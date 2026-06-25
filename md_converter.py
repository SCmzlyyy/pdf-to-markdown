"""
md_converter.py — MarkItDown 转换模块

职责:
  1. 封装 Microsoft MarkItDown 转换功能
  2. 优先使用 CLI 调用，回退到 Python API
  3. 支持文本→Markdown 和 PDF→Markdown

依赖:
  pip install markitdown
  (或从 https://github.com/microsoft/markitdown 克隆)
"""

import logging
import subprocess
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================
# MarkItDown 路径自动检测
# ============================================================

# 已知的 markitdown CLI 入口候选路径
# 优先通过 PATH 查找，无需硬编码
MARKITDOWN_CLI_CANDIDATES = [
    "markitdown",
]


def _find_markitdown_cli() -> str | None:
    """查找 markitdown CLI 工具路径。"""
    import shutil

    # 1) PATH
    which = shutil.which("markitdown")
    if which:
        logger.info(f"MarkItDown CLI 已在 PATH 中找到: {which}")
        return which

    # 2) 候选路径
    for cand in MARKITDOWN_CLI_CANDIDATES:
        if Path(cand).exists():
            logger.info(f"MarkItDown CLI 在候选路径中找到: {cand}")
            return cand

    return None


def _find_markitdown_python() -> bool:
    """检查是否能导入 markitdown Python 包。"""
    try:
        import markitdown  # noqa
        logger.info("MarkItDown Python API 可用")
        return True
    except ImportError:
        logger.warning("MarkItDown Python API 不可用")
        return False


def is_available() -> bool:
    """检查 MarkItDown 是否可用。"""
    return _find_markitdown_cli() is not None or _find_markitdown_python()


# ============================================================
# 核心转换函数
# ============================================================


def _convert_via_cli(text: str, filename_hint: str = "document") -> str:
    """
    通过 MarkItDown CLI 将文本转换为 Markdown。

    先将文本写入临时文件，调用 CLI 转换，然后读取结果。

    Args:
        text:          待转换的文本
        filename_hint: 临时文件名提示（用于扩展名判断）

    Returns:
        Markdown 格式文本
    """
    # 使用 .txt 扩展名，因为 markitdown CLI 接受纯文本
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(text)
        tmp_path = f.name

    cli_path = _find_markitdown_cli()
    if not cli_path:
        raise RuntimeError("MarkItDown CLI 不可用")

    try:
        logger.info(f"通过 CLI 转换: {tmp_path}")
        result = subprocess.run(
            [cli_path, tmp_path],
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
        )
        if result.returncode != 0:
            logger.warning(f"CLI 返回非零: {result.returncode}, stderr: {result.stderr[:200]}")
            # 即使非零也可能有部分输出
        output = result.stdout
        logger.info(f"CLI 转换完成，输出 {len(output)} 字符")
        return output
    except subprocess.TimeoutExpired:
        logger.error("CLI 转换超时 (120s)")
        raise
    except Exception as e:
        logger.error(f"CLI 转换失败: {e}")
        raise
    finally:
        # 清理临时文件
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


def _convert_via_api(text: str, filename_hint: str = "document") -> str:
    """
    通过 MarkItDown Python API 将文本转换为 Markdown。

    注意：markitdown 库通常接受文件路径，所以先写临时文件。

    Args:
        text:          待转换的文本
        filename_hint: 临时文件名提示

    Returns:
        Markdown 格式文本
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(text)
        tmp_path = f.name

    try:
        from markitdown import MarkItDown

        logger.info("通过 Python API 转换")
        md = MarkItDown()
        result = md.convert(tmp_path)
        output = result.text_content if hasattr(result, "text_content") else str(result)
        logger.info(f"API 转换完成，输出 {len(output)} 字符")
        return output
    except ImportError as e:
        logger.error(f"无法导入 MarkItDown: {e}")
        raise RuntimeError(
            "MarkItDown 未安装。请运行: pip install markitdown\n"
            "或从 https://github.com/microsoft/markitdown 克隆"
        )
    except Exception as e:
        logger.error(f"API 转换失败: {e}")
        raise
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


def convert_text_to_markdown(
    text: str,
    filename_hint: str = "document",
    prefer_cli: bool = True,
) -> str:
    """
    将纯文本转换为 Markdown 格式。

    转换策略:
      - 优先 MarkItDown CLI (prefer_cli=True)
      - 回退 MarkItDown Python API
      - 如果都不可用，返回原始文本（无需转换）

    Args:
        text:          输入文本（OCR 或 PDF 提取结果）
        filename_hint: 文件名提示（用于日志）
        prefer_cli:    是否优先使用 CLI

    Returns:
        Markdown 格式文本
    """
    if not text or not text.strip():
        logger.warning("输入文本为空，返回空字符串")
        return ""

    cli_path = _find_markitdown_cli() if prefer_cli else None

    try:
        if cli_path:
            return _convert_via_cli(text, filename_hint)
        elif _find_markitdown_python():
            return _convert_via_api(text, filename_hint)
        else:
            logger.warning("MarkItDown 不可用，返回原始文本（仅简单包装）")
            return _fallback_convert(text)
    except Exception as e:
        logger.error(f"MarkItDown 转换失败，使用回退方案: {e}")
        return _fallback_convert(text)


def _fallback_convert(text: str) -> str:
    """
    当 MarkItDown 不可用时的回退方案：
    将文本包装为基本 Markdown 格式。
    """
    lines = text.split("\n")
    md_lines = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        # 检测可能的标题行（全大写短行）
        if stripped and len(stripped) < 80 and stripped.isupper():
            md_lines.append(f"\n## {stripped}\n")
            continue

        # 检测引用行
        if stripped.startswith("Reference") or stripped.startswith("REFERENCES"):
            md_lines.append(f"\n### {stripped}\n")
            continue

        # 检测 DOI / URL
        if stripped.startswith("DOI:"):
            md_lines.append(f"- **DOI:** {stripped[4:].strip()}")
            continue

        md_lines.append(line)

    return "\n".join(md_lines)


def convert_pdf_to_markdown(
    pdf_path: str | Path,
    text: str,
    filename_hint: str | None = None,
) -> str:
    """
    方便的 PDF 全文转 Markdown 入口。

    Args:
        pdf_path:      PDF 路径（用于提取文件名 hint）
        text:          PDF 提取的文本
        filename_hint: 自定义文件名（可选）

    Returns:
        Markdown 格式文本
    """
    pdf_path = Path(pdf_path)
    hint = filename_hint or pdf_path.stem
    return convert_text_to_markdown(text, filename_hint=hint)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(f"MarkItDown 可用: {is_available()}")

    test_text = """
    Introduction
    This is a test document about UK Biobank research.
    The study analyzed 500,000 participants.
    Results show significant correlation.
    DOI: 10.1038/s41586-020-1234-5
    References
    1. Smith et al., Nature 2020
    """
    md = convert_text_to_markdown(test_text)
    print("\n转换结果:")
    print(md)
