import logging
import os
import queue
import threading

from src.drive_client import DriveClient, DriveClientError


class Uploader:
    def __init__(
        self,
        upload_queue: queue.Queue,
        drive_client: DriveClient,
        drive_folder_id: str,
        vault_path: str,
    ) -> None:
        self.upload_queue = upload_queue
        self.drive_client = drive_client
        self.drive_folder_id = drive_folder_id
        self.vault_path = vault_path
        self._stop_event = threading.Event()
        self._folder_cache: dict[str, str] = {}
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logging.info("Uploader started.")

    def stop(self) -> None:
        if self._thread is None:
            return
        # Waits for all tasks to be processed before stopping the thread.
        self.upload_queue.join()
        self._stop_event.set()
        self._thread.join()
        logging.info("Uploader stopped.")

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                path = self.upload_queue.get(timeout=1)
                try:
                    self._upload(path)
                except Exception as e:
                    logging.error(f"Unexpected error uploading '{path}': {e}")
                finally:
                    self.upload_queue.task_done()
            except queue.Empty:
                continue

    def _resolve_drive_folder(self, path: str) -> str:
        relative = os.path.relpath(path, self.vault_path)
        parts = relative.replace("\\", "/").split("/")
        folder_segments = parts[:-1]
        current_folder_id = self.drive_folder_id
        try:
            for segment in folder_segments:
                cache_key = f"{current_folder_id}/{segment}"
                if cache_key not in self._folder_cache:
                    self._folder_cache[cache_key] = self.drive_client.get_or_create_folder(
                        segment, current_folder_id
                    )
                current_folder_id = self._folder_cache[cache_key]
        except DriveClientError as exc:
            raise DriveClientError(
                f"Failed to resolve folder for '{path}': {exc}"
            ) from exc
        return current_folder_id

    def _upload(self, path: str) -> None:
        try:
            folder_id = self._resolve_drive_folder(path)
            self.drive_client.upload_file(path, folder_id)
            logging.info(f"Uploaded: {path}")
        except DriveClientError as e:
            logging.error(f"Failed to upload {path}: {e}")
