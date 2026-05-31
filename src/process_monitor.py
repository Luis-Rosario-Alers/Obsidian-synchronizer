import logging
import threading
import time

import psutil


class ProcessMonitor:
    def __init__(self, shutdown_event: threading.Event, poll_interval: float = 5.0) -> None:
        self.shutdown_event = shutdown_event
        self.poll_interval = poll_interval
        self._thread: threading.Thread | None = None

    def _is_obsidian_running(self) -> bool:
        for p in psutil.process_iter(["name"]):
            try:
                if "obsidian" in p.name().lower():
                    return True
            except psutil.NoSuchProcess:
                continue
        return False
    
    def _wait_for_obsidian(self, timeout: int = 30) -> bool:
        logging.info("Waiting for Obsidian to start...")
        for _ in range(timeout):
            if self._is_obsidian_running():
                return True
            time.sleep(1)
        return False

    def _run(self) -> None:
        logging.info("Process monitor started.")
        while not self.shutdown_event.is_set():
            if not self._is_obsidian_running():
                logging.info("Obsidian process not found. Triggering shutdown.")
                self.shutdown_event.set()
                break
            time.sleep(self.poll_interval)

    def start(self) -> None:
        if not self._wait_for_obsidian():
            logging.warning("Obsidian did not start within the expected time. Shutting Down.")
            self.shutdown_event.set()
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        self.shutdown_event.set()
        self._thread.join()
        logging.info("Process monitor stopped.")
