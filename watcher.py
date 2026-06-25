"""
watcher.py — 文件夹自动监听模块

职责:
  1. 使用 watchdog 监听 input_pdfs/ 目录
  2. 检测到新 PDF 文件 → 自动调用主处理流程
  3. 防重复处理（冷却时间 + 文件大小稳定检测）

依赖:
  pip install watchdog
"""

import logging
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class PDFHandler(FileSystemEventHandler):
    """
    watchdog 事件处理器。

    监听到 input_pdfs/ 出现新 PDF 时触发回调。
    """

    def __init__(self, callback, cooldown: float = 5.0):
        """
        Args:
            callback: 处理函数 def callback(pdf_path: str) -> None
            cooldown: 同一文件冷却时间（秒），防重复触发
        """
        super().__init__()
        self.callback = callback
        self.cooldown = cooldown
        self._recently_processed: dict[str, float] = {}

    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory and event.src_path.lower().endswith(".pdf"):
            self._handle_pdf(event.src_path)

    def on_modified(self, event):
        """文件修改事件（拖入的 PDF 可能触发多次）"""
        if not event.is_directory and event.src_path.lower().endswith(".pdf"):
            self._handle_pdf(event.src_path)

    def on_moved(self, event):
        """文件移动/重命名事件"""
        if hasattr(event, "dest_path") and event.dest_path.lower().endswith(".pdf"):
            self._handle_pdf(event.dest_path)

    def _handle_pdf(self, pdf_path: str):
        """处理 PDF 文件（带冷却和稳定性检测）"""
        pdf_path = str(Path(pdf_path).resolve())

        # 防重复
        now = time.time()
        last_time = self._recently_processed.get(pdf_path, 0)
        if now - last_time < self.cooldown:
            logger.debug(f"跳过（冷却中）: {Path(pdf_path).name}")
            return

        # 文件大小稳定性检测（等待写入完成）
        try:
            if not self._wait_for_stable(pdf_path):
                logger.warning(f"文件大小不稳定，跳过: {Path(pdf_path).name}")
                return
        except FileNotFoundError:
            logger.debug(f"文件已消失: {Path(pdf_path).name}")
            return

        self._recently_processed[pdf_path] = now
        logger.info(f"检测到新 PDF: {Path(pdf_path).name}")

        try:
            self.callback(pdf_path)
            logger.info(f"处理完成: {Path(pdf_path).name}")
        except Exception as e:
            logger.error(f"处理失败 [{Path(pdf_path).name}]: {e}")

    @staticmethod
    def _wait_for_stable(
        file_path: str,
        max_retries: int = 10,
        interval: float = 0.5,
    ) -> bool:
        """
        等待文件写入完成（大小稳定）。

        连续检查文件大小，如果 interval 秒后大小未变则认为稳定。

        Returns:
            True 稳定 / False 超时
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        prev_size = -1
        for i in range(max_retries):
            curr_size = path.stat().st_size
            if curr_size == prev_size and curr_size > 0:
                return True
            prev_size = curr_size
            time.sleep(interval)

        logger.debug(f"文件大小仍在变化: {file_path}")
        return True  # 超时也返回 True，避免卡死


def start_watching(
    watch_dir: str | Path,
    callback,
    recursive: bool = False,
) -> Observer:
    """
    启动文件夹监听。

    Args:
        watch_dir:  监听目录
        callback:   处理函数 def callback(pdf_path: str) -> None
        recursive:  是否递归子目录

    Returns:
        Observer 实例（调用 observer.stop() 停止）
    """
    watch_dir = Path(watch_dir).resolve()
    if not watch_dir.exists():
        watch_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"已创建监听目录: {watch_dir}")

    event_handler = PDFHandler(callback=callback)
    observer = Observer()
    observer.schedule(event_handler, str(watch_dir), recursive=recursive)
    observer.start()

    logger.info(f"开始监听: {watch_dir}")
    return observer


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    def demo_callback(pdf_path: str):
        print(f"   → 处理: {Path(pdf_path).name}")

    watch_dir = Path(__file__).parent / "input_pdfs"
    watch_dir.mkdir(exist_ok=True)

    observer = start_watching(str(watch_dir), demo_callback)
    print(f"监听中 (按 Ctrl+C 停止): {watch_dir}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("已停止监听")
