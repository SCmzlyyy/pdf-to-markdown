"""
ocr_engine.py — OCR 识别模块

职责:
  1. 将 PDF 每页转图片 (pdf2image)
  2. 调用 pytesseract 进行文字识别
  3. 拼接所有页文本

依赖:
  pip install pytesseract pdf2image pillow
  + Tesseract-OCR 引擎 (系统级安装)
"""

import logging
import shutil
import subprocess
from pathlib import Path

from pdf2image import convert_from_path
from PIL import Image

# ============================================================
# 日志
# ============================================================
logger = logging.getLogger(__name__)

# ============================================================
# Tesseract 可执行文件路径自动检测
# ============================================================
TESSERACT_CANDIDATE_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    # WSL / Git Bash 下可能通过 PATH 找到
    "tesseract",
]


def _auto_find_tesseract() -> str | None:
    """自动定位 tesseract.exe，返回路径或 None。"""
    # 1) 检查系统 PATH
    which = shutil.which("tesseract")
    if which:
        logger.info(f"通过 PATH 找到 tesseract: {which}")
        return which

    # 2) 检查常见安装位置
    for candidate in TESSERACT_CANDIDATE_PATHS:
        if candidate == "tesseract":
            continue  # 已在上一步检查过
        p = Path(candidate)
        if p.exists():
            logger.info(f"在 {p} 找到 tesseract")
            return str(p)

    # 3) 尝试通过注册表查找 (Windows)
    try:
        result = subprocess.run(
            [
                "reg",
                "query",
                r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\tesseract.exe",
                "/ve",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.splitlines():
            if "REG_SZ" in line or "REG_EXPAND_SZ" in line:
                parts = line.strip().split()
                exe_path = parts[-1]
                if Path(exe_path).exists():
                    logger.info(f"通过注册表找到 tesseract: {exe_path}")
                    return exe_path
    except Exception:
        pass

    logger.warning("未找到 tesseract，OCR 将不可用")
    return None


def _configure_tesseract(tesseract_path: str) -> None:
    """配置 pytesseract 使用指定路径的 tesseract。"""
    import pytesseract as pts

    pts.pytesseract.tesseract_cmd = tesseract_path
    logger.debug(f"tesseract 路径已设为: {tesseract_path}")


def auto_setup() -> bool:
    """
    自动检测并配置 Tesseract。

    Returns:
        True 表示配置成功，False 表示未找到。
    """
    path = _auto_find_tesseract()
    if path:
        _configure_tesseract(path)
        return True
    return False


def ocr_pdf(
    pdf_path: str | Path,
    output_dir: str | Path | None = None,
    lang: str = "eng",
    dpi: int = 300,
) -> str:
    """
    对 PDF 进行 OCR 识别。

    Args:
        pdf_path:    PDF 文件路径
        output_dir:  中间图片存放目录（None = 不存盘）
        lang:        Tesseract 语言包 (eng=英文, chi_sim=简体中文)
        dpi:         导出图片分辨率

    Returns:
        识别到的全部文本
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    # 确保 tesseract 可用
    if not auto_setup():
        raise RuntimeError(
            "Tesseract-OCR 未安装！请从以下位置安装:\n"
            "  https://github.com/UB-Mannheim/tesseract/wiki\n"
            "并确保安装路径在系统 PATH 中。"
        )

    import pytesseract as pts

    logger.info(f"开始 OCR: {pdf_path.name} (dpi={dpi}, lang={lang})")

    all_text = []
    # pdf2image: 将 PDF 每页转换为 PIL Image
    images: list[Image.Image] = convert_from_path(
        str(pdf_path), dpi=dpi, fmt="png"
    )

    total_pages = len(images)
    logger.info(f"PDF 共 {total_pages} 页，开始逐页 OCR")

    for page_num, img in enumerate(images, start=1):
        logger.info(f"  OCR 第 {page_num}/{total_pages} 页...")

        # 可选：将图片保存到临时目录
        if output_dir:
            output_path = Path(output_dir) / f"{pdf_path.stem}_page_{page_num:04d}.png"
            img.save(str(output_path))
            logger.debug(f"    图片已保存: {output_path.name}")

        # OCR 识别
        try:
            page_text = pts.image_to_string(img, lang=lang)
            all_text.append(page_text)
            logger.debug(f"    识别到 {len(page_text)} 字符")
        except Exception as e:
            logger.error(f"    第 {page_num} 页 OCR 失败: {e}")
            all_text.append(f"\n[OCR 第 {page_num} 页失败: {e}]\n")

    full_text = "\n".join(all_text)
    logger.info(f"OCR 完成，总文本长度: {len(full_text)} 字符")
    return full_text


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    auto_setup()
    test_path = input("输入 PDF 路径测试 OCR: ").strip()
    if Path(test_path).exists():
        text = ocr_pdf(test_path)
        print(f"\nOCR 结果预览 ({len(text)} 字符):")
        print(text[:800])
    else:
        print("文件不存在")
