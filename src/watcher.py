import logging
import queue
import time
import threading
import os

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class VaultEventHandler(FileSystemEventHandler):
    def __init__(self, upload_queue: queue.Queue, debounce_seconds: float) -> None:
        self.upload_queue = upload_queue
        self.debounce_seconds = debounce_seconds
        self._last_enqueued: dict[str, float] = {}
        self._lock = threading.Lock()

    def _enqueue(self, path: str) -> None:
        parts = path.replace("\\", "/").split("/")
        if any(part in {".obsidian", ".smart-env", ".trash"} for part in parts):
            logging.debug("Ignored (vault metadata): %s", path)
            return
        
        now = time.time()
        with self._lock:
            if not os.path.exists(path):
                logging.debug(f"Ignored (no longer exists): {path}")
                return
            if now - self._last_enqueued.get(path, 0) >= self.debounce_seconds:
                self._last_enqueued[path] = now
                self.upload_queue.put(path)
                logging.info(f"Enqueued: {path}")
            else:
                logging.debug(f"Debounced (skipped): {path}")

    def on_created(self, event) -> None:
        if not event.is_directory:
            self._enqueue(event.src_path)

    def on_modified(self, event) -> None:
        if not event.is_directory:
            self._enqueue(event.src_path)

    def on_moved(self, event) -> None:
        if not event.is_directory:
            with self._lock:
                self._last_enqueued.pop(event.src_path, None)
            self._enqueue(event.dest_path)
    

def start_watcher(vault_path: str, upload_queue: queue.Queue, debounce_seconds: float, shutdown_event: threading.Event) -> None:
    event_handler = VaultEventHandler(upload_queue, debounce_seconds)
    observer = Observer()
    observer.schedule(event_handler, path=vault_path, recursive=True)
    observer.start()
    logging.info(f"Watching vault at: {vault_path}")

    try:
        while not shutdown_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Shutting down watcher.")
    finally:
        observer.stop()
        observer.join()
        logging.info("Watcher stopped.")


def placeholder_consumer(upload_queue: queue.Queue) -> None:
    """Temporary stand-in for uploader.py — remove once uploader.py is connected."""
    while True:
        path = upload_queue.get()
        print(f"[QUEUE] Would upload: {path}", flush=True)
        upload_queue.task_done()
