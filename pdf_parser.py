"""
pdf_parser.py — PDF 解析模块

职责:
  1. 使用 PyMuPDF (fitz) 读取 PDF 文本
  2. 判断 PDF 是否为扫描件（文本长度 < 阈值）
  3. 为 OCR 模块提供 PDF 路径信息

依赖:
  pip install pymupdf
"""

import fitz  # PyMuPDF
import logging
from pathlib import Path

# ============================================================
# 配置
# ============================================================
TEXT_LENGTH_THRESHOLD = 100  # 提取文本少于该字符数 → 判定为扫描件

# ============================================================
# 日志
# ============================================================
logger = logging.getLogger(__name__)


def check_encrypted(pdf_path: str | Path) -> tuple[bool, bool, str | None]:
    """
    检查 PDF 是否加密/受密码保护。

    Args:
        pdf_path: PDF 文件路径

    Returns:
        (is_encrypted, needs_password, message)
        - is_encrypted:    是否加密
        - needs_password:  是否需要密码才能打开
        - message:         描述信息
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    try:
        doc = fitz.open(str(pdf_path))
        needs = doc.needs_pass
        is_enc = needs or doc.is_encrypted
        doc.close()
        if needs:
            return (True, True, "PDF 已加密，需要密码才能打开")
        elif is_enc:
            return (True, False, "PDF 有加密标记但已可访问")
        return (False, False, "PDF 未加密")
    except Exception as e:
        logger.warning(f"检查加密状态失败: {e}")
        return (False, False, f"无法检查加密状态: {e}")


def try_decrypt(pdf_path: str | Path, password: str = "") -> bool:
    """
    尝试用密码解密 PDF。

    Args:
        pdf_path:  PDF 文件路径
        password:  尝试的密码（空字符串＝无密码尝试）

    Returns:
        True=解密成功, False=解密失败
    """
    pdf_path = Path(pdf_path)
    try:
        doc = fitz.open(str(pdf_path))
        if not doc.needs_pass:
            doc.close()
            return True
        success = doc.authenticate(password)
        doc.close()
        return bool(success)
    except Exception as e:
        logger.warning(f"解密失败: {e}")
        return False


def extract_text(pdf_path: str | Path, password: str | None = None) -> str:
    """
    使用 PyMuPDF 从 PDF 提取所有文本。

    自动检测加密状态：
      - 无加密 → 正常提取
      - 有加密但提供了密码 → 尝试解密
      - 有加密无密码 → 抛出 ValueError

    Args:
        pdf_path:  PDF 文件路径
        password:  可选密码（用于解密受保护 PDF）

    Returns:
        提取到的文本内容（可能为空字符串）

    Raises:
        FileNotFoundError: 文件不存在
        ValueError:        PDF 加密且无法解密
        RuntimeError:      解析失败
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    doc = None
    try:
        doc = fitz.open(str(pdf_path))
        logger.info(f"已打开 PDF: {pdf_path.name} ({doc.page_count} 页)")

        # 检测加密
        if doc.needs_pass:
            if password is not None:
                auth = doc.authenticate(password)
                if not auth:
                    msg = (
                        f"PDF 需要密码，但提供的密码不正确: {pdf_path.name}\n"
                        f"尝试: python main.py --input \"{pdf_path}\" --password \"你的密码\""
                    )
                    raise ValueError(msg)
                logger.info(f"PDF 已用密码解密: {pdf_path.name}")
            else:
                msg = (
                    f"PDF 已加密，无法读取: {pdf_path.name}\n"
                    f"这是常见情况：非免费文献经常有密码保护。\n"
                    f"如已知密码，用 --password 参数传入:\n"
                    f"  python main.py --input \"{pdf_path}\" --password \"你的密码\""
                )
                raise ValueError(msg)

        # 逐页提取文本
        text_pages = []
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text()
            if page_text.strip():
                text_pages.append(page_text)
            logger.debug(f"  第 {page_num} 页: {len(page_text)} 字符")

        full_text = "\n".join(text_pages)
        logger.info(f"提取文本总长度: {len(full_text)} 字符")
        return full_text

    except ValueError:
        raise  # 原样抛出密码相关的错误
    except Exception as e:
        logger.error(f"读取 PDF 失败 [{pdf_path.name}]: {e}")
        raise RuntimeError(f"PDF 解析失败: {e}")
    finally:
        if doc:
            doc.close()


def is_scanned_pdf(pdf_path: str | Path, password: str | None = None) -> bool:
    """
    判断 PDF 是否为扫描件（不可复制文本）。

    策略: 提取全部文本，如果字符数 < TEXT_LENGTH_THRESHOLD
    则认为是扫描图片型 PDF。

    Args:
        pdf_path:  PDF 文件路径
        password:  密码（加密 PDF 需要）

    Returns:
        True = 扫描件（需要 OCR），False = 可直接提取

    Raises:
        ValueError: PDF 加密且无法解密，需先提供密码
    """
    try:
        text = extract_text(pdf_path, password=password)
        is_scanned = len(text.strip()) < TEXT_LENGTH_THRESHOLD
        if is_scanned:
            logger.info(f"判定为扫描件 (文本仅 {len(text.strip())} 字符)")
        else:
            logger.info(f"判定为可复制文本 ({len(text.strip())} 字符)")
        return is_scanned
    except ValueError:
        raise  # 加密 PDF 直接向上抛，让调用方处理
    except Exception as e:
        logger.warning(f"PDF 解析异常，按扫描件处理: {e}")
        return True


def get_page_count(pdf_path: str | Path) -> int:
    """快速获取 PDF 页数"""
    try:
        doc = fitz.open(str(pdf_path))
        count = doc.page_count
        doc.close()
        return count
    except Exception:
        return 0


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    test_path = input("输入 PDF 路径测试: ").strip()
    if Path(test_path).exists():
        result = extract_text(test_path)
        print(f"\n提取结果预览 ({len(result)} 字符):")
        print(result[:500])
        print(f"\n是否为扫描件: {is_scanned_pdf(test_path)}")
    else:
        print("文件不存在")
