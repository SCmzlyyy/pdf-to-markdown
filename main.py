"""
main.py — pdf-to-markdown 主入口

核心流程:
  PDF → 判断扫描件 → (OCR / 直接提取) → MarkItDown → Markdown(.md)

支持两种运行模式:
  1. 单次批处理: python main.py
  2. 持续监听:   python main.py --watch

用法:
  python main.py                    # 处理 input_pdfs/ 下所有 PDF
  python main.py --watch            # 持续监听 input_pdfs/
  python main.py --input my.pdf     # 处理指定 PDF
  python main.py --output ./my_md   # 自定义输出目录
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# ============================================================
# 项目内部模块
# ============================================================
from pdf_parser import extract_text, is_scanned_pdf, get_page_count
from ocr_engine import ocr_pdf, auto_setup as ocr_auto_setup
from md_converter import convert_text_to_markdown, is_available as md_available
from watcher import start_watching

# ============================================================
# 日志配置
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pdf-to-markdown")


# ============================================================
# 路径配置
# ============================================================
PROJECT_DIR = Path(__file__).parent
INPUT_DIR = PROJECT_DIR / "input_pdfs"
TEMP_DIR = PROJECT_DIR / "temp"
OUTPUT_DIR = PROJECT_DIR / "output_md"


# ============================================================
# 核心处理函数
# ============================================================


def process_single_pdf(
    pdf_path: str | Path,
    output_dir: str | Path | None = None,
    temp_dir: str | Path | None = None,
    ocr_lang: str = "eng",
    ocr_dpi: int = 300,
    password: str | None = None,
) -> str | None:
    """
    处理单个 PDF 文件：PDF → 文本提取/OCR → Markdown

    Args:
        pdf_path:   PDF 文件路径
        output_dir: 输出目录 (None = 使用默认)
        temp_dir:   临时目录 (None = 使用默认)
        ocr_lang:   Tesseract 语言
        ocr_dpi:    OCR 分辨率
        password:   PDF 密码（加密文献需要）

    Returns:
        输出 md 文件路径，失败返回 None
    """
    pdf_path = Path(pdf_path)
    if output_dir is None:
        output_dir = Path(__file__).parent / "output_md"
    if temp_dir is None:
        temp_dir = Path(__file__).parent / "temp"

    output_dir = Path(output_dir)
    temp_dir = Path(temp_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    output_md = output_dir / f"{pdf_path.stem}.md"

    # ---- Step 1: 已存在则跳过 ----
    if output_md.exists():
        logger.info(f"已存在，跳过: {output_md.name}")
        return str(output_md)

    logger.info(f"{'='*50}")
    logger.info(f"开始处理: {pdf_path.name}")
    logger.info(f"{'='*50}")

    try:
        # ---- Step 2: 判断 PDF 类型 ----
        pages = get_page_count(pdf_path)
        logger.info(f"页数: {pages}")

        try:
            scanned = is_scanned_pdf(pdf_path, password=password)
        except ValueError as e:
            logger.error(str(e))
            return None

        # ---- Step 3: 提取文本 ----
        if scanned:
            logger.info("→ 扫描件，启动 OCR...")
            raw_text = ocr_pdf(
                pdf_path,
                output_dir=temp_dir,
                lang=ocr_lang,
                dpi=ocr_dpi,
            )
        else:
            logger.info("→ 可复制文本，直接提取...")
            raw_text = extract_text(pdf_path, password=password)

        if not raw_text.strip():
            logger.warning("提取文本为空，跳过")
            return None

        logger.info(f"原始文本长度: {len(raw_text)} 字符")

        # ---- Step 4: MarkItDown 转换 ----
        logger.info("→ 转换为 Markdown...")
        md_content = convert_text_to_markdown(
            raw_text,
            filename_hint=pdf_path.stem,
        )

        # ---- Step 5: 写入输出 ----
        # 添加文件头元信息
        header = (
            f"---\n"
            f"title: {pdf_path.stem}\n"
            f"source: {pdf_path.name}\n"
            f"pages: {pages}\n"
            f"ocr: {scanned}\n"
            f"processed: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"---\n\n"
        )

        output_md.write_text(header + md_content, encoding="utf-8")
        logger.info(f"✓ 已保存: {output_md}")

        return str(output_md)

    except Exception as e:
        logger.error(f"✗ 处理失败 [{pdf_path.name}]: {e}", exc_info=True)
        return None


def process_batch(
    input_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    temp_dir: str | Path | None = None,
    ocr_lang: str = "eng",
    ocr_dpi: int = 300,
    password: str | None = None,
) -> list[str]:
    """
    批量处理整个文件夹的 PDF。

    Returns:
        成功输出的 md 文件路径列表
    """
    if input_dir is None:
        input_dir = INPUT_DIR
    input_dir = Path(input_dir)

    if not input_dir.exists():
        logger.info(f"输入目录不存在，已创建: {input_dir}")
        input_dir.mkdir(parents=True, exist_ok=True)
        return []

    # 查找所有 PDF
    pdf_files = sorted(input_dir.glob("*.pdf")) + sorted(input_dir.glob("*.PDF"))
    if not pdf_files:
        logger.info(f"输入目录中没有 PDF 文件: {input_dir}")
        return []

    logger.info(f"找到 {len(pdf_files)} 个 PDF 文件，开始批处理")

    successful = []
    for i, pdf_path in enumerate(pdf_files, start=1):
        logger.info(f"\n[{i}/{len(pdf_files)}]")
        result = process_single_pdf(
            pdf_path,
            output_dir=output_dir,
            temp_dir=temp_dir,
            ocr_lang=ocr_lang,
            ocr_dpi=ocr_dpi,
            password=password,
        )
        if result:
            successful.append(result)

    logger.info(f"\n批处理完成！成功: {len(successful)}/{len(pdf_files)}")
    return successful


# ============================================================
# 环境检查
# ============================================================


def check_environment() -> bool:
    """检查运行环境，报告缺失项。"""
    all_ok = True

    print("\n" + "=" * 50)
    print("  pdf-to-markdown — 环境检查")
    print("=" * 50)

    # Python 版本
    py_ver = sys.version_info
    print(f"\n  Python:   {sys.version.split()[0]}", end="")
    if py_ver.major >= 3 and py_ver.minor >= 10:
        print(" [OK]")
    else:
        print(" [MISS] (need 3.10+)")
        all_ok = False

    # PyMuPDF
    try:
        import fitz  # noqa
        print("  PyMuPDF:  installed [OK]")
    except ImportError:
        print("  PyMuPDF:  missing [MISS] -> pip install pymupdf")
        all_ok = False

    # Pillow
    try:
        from PIL import Image  # noqa
        print("  Pillow:   installed [OK]")
    except ImportError:
        print("  Pillow:   missing [MISS] -> pip install pillow")
        all_ok = False

    # pytesseract
    try:
        import pytesseract  # noqa
        print("  pytesseract: installed [OK]")
    except ImportError:
        print("  pytesseract: missing [MISS] -> pip install pytesseract")
        all_ok = False

    # pdf2image
    try:
        import pdf2image  # noqa
        print("  pdf2image: installed [OK]")
    except ImportError:
        print("  pdf2image: missing [MISS] -> pip install pdf2image")
        all_ok = False

    # watchdog
    try:
        import watchdog  # noqa
        print("  watchdog:  installed [OK]")
    except ImportError:
        print("  watchdog:  missing [MISS] -> pip install watchdog")
        all_ok = False

    # MarkItDown
    if md_available():
        print("  MarkItDown: available [OK]")
    else:
        print("  MarkItDown: missing [MISS] -> pip install markitdown")
        all_ok = False

    # Tesseract-OCR 引擎
    if ocr_auto_setup():
        print("  Tesseract-OCR: configured [OK]")
    else:
        print("  Tesseract-OCR: not found [MISS] -> manual install needed")
        print("    download: https://github.com/UB-Mannheim/tesseract/wiki")
        all_ok = False

    # 目录
    for d in [INPUT_DIR, OUTPUT_DIR, TEMP_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        ok_str = "[OK]" if d.exists() else "[MISS]"
        print(f"  {d.name}/: {ok_str}")

    print("\n" + "=" * 50)
    if all_ok:
        print("  All checks passed! [OK]")
    else:
        print("  Some components missing -- see above.")
    print("=" * 50 + "\n")

    return all_ok


# ============================================================
# 命令行入口
# ============================================================


def main():
    parser = argparse.ArgumentParser(
        description="pdf-to-markdown — 各类PDF 转 Markdown 自动化流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                  # 批处理 input_pdfs/ 下所有 PDF
  python main.py --watch          # 持续监听模式（拖放 PDF 自动处理）
  python main.py --input paper.pdf
  python main.py --check          # 仅检查环境
        """,
    )

    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="输入 PDF 文件或目录 (默认:./input_pdfs/)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="输出目录 (默认:./output_md/)",
    )
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="持续监听模式（拖放 PDF 自动处理）",
    )
    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="仅检查环境，不处理文件",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="eng",
        help="OCR 语言 (eng=英文, chi_sim=简体中文, 默认:eng)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="OCR 图片分辨率 (默认:300)",
    )
    parser.add_argument(
        "--password", "-p",
        type=str,
        default=None,
        help="PDF 密码（加密文献需要）",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细日志输出",
    )

    args = parser.parse_args()

    # 日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # ---- --check 模式 ----
    if args.check:
        check_environment()
        return

    # ---- 确保目录存在 ----
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # 解析输入路径
    input_path = Path(args.input) if args.input else INPUT_DIR
    output_dir = Path(args.output) if args.output else OUTPUT_DIR

    # ---- --watch 模式 ----
    if args.watch:
        watch_dir = input_path if input_path.is_dir() else INPUT_DIR
        logger.info(f"启动监听模式: {watch_dir}")
        logger.info("将 PDF 文件拖入该文件夹即可自动处理")
        logger.info("按 Ctrl+C 停止\n")

        def callback(pdf_path: str):
            process_single_pdf(
                pdf_path,
                output_dir=output_dir,
                ocr_lang=args.lang,
                ocr_dpi=args.dpi,
                password=args.password,
            )

        observer = start_watching(str(watch_dir), callback)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n收到停止信号...")
            observer.stop()
        observer.join()
        logger.info("监听已停止")
        return

    # ---- 单文件模式 ----
    if input_path.is_file():
        if input_path.suffix.lower() == ".pdf":
            process_single_pdf(
                input_path,
                output_dir=output_dir,
                ocr_lang=args.lang,
                ocr_dpi=args.dpi,
                password=args.password,
            )
        else:
            logger.error(f"不支持的文件格式: {input_path.suffix}")
        return

    # ---- 批处理模式 ----
    if not any(input_path.glob("*.pdf")) and not any(input_path.glob("*.PDF")):
        logger.info(f"input_pdfs/ 为空。请将 PDF 放入: {INPUT_DIR}")
        logger.info("提示: 使用 --watch 模式可自动监听文件拖放")
        return

    process_batch(
        input_dir=input_path,
        output_dir=output_dir,
        ocr_lang=args.lang,
        ocr_dpi=args.dpi,
        password=args.password,
    )


if __name__ == "__main__":
    main()
