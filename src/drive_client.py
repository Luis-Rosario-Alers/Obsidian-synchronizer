import io
import logging
import os
import time
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]
_RETRYABLE_STATUSES = {429, 500, 503}


class DriveClientError(Exception):
    pass


def _escape_drive_query(value: str) -> str:
    """Escape single quotes for Drive API query strings."""
    return value.replace("'", "\\'")


class DriveClient:
    def __init__(self, credentials_path: str, token_path: str) -> None:
        self._credentials_path = credentials_path
        self._token_path = token_path
        self._service = None
        self.authenticate()

    def authenticate(self) -> None:
        creds: Credentials | None = None

        if os.path.exists(self._token_path):
            creds = Credentials.from_authorized_user_file(self._token_path, SCOPES)

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("OAuth token refreshed.")
            except Exception as exc:
                raise DriveClientError(f"Failed to refresh token: {exc}") from exc
        elif not creds or not creds.valid:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            except Exception as exc:
                raise DriveClientError(f"OAuth flow failed: {exc}") from exc

        with open(self._token_path, "w") as token_file:
            token_file.write(creds.to_json())

        self._service = build("drive", "v3", credentials=creds)
        logger.info("Authenticated with Google Drive successfully.")

    def get_or_create_folder(self, name: str, parent_id: str) -> str:
        safe_name = _escape_drive_query(name)
        query = (
            f"name='{safe_name}' and '{parent_id}' in parents"
            " and mimeType='application/vnd.google-apps.folder'"
            " and trashed=false"
        )
        try:
            request = self._service.files().list(
                q=query, fields="files(id)", spaces="drive"
            )
            result = self._execute_with_retry(request)
        except DriveClientError:
            raise
        except Exception as exc:
            raise DriveClientError(f"Failed to query folder '{name}': {exc}") from exc

        files = result.get("files", [])
        if files:
            return files[0]["id"]

        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        try:
            request = self._service.files().create(
                body=metadata, fields="id"
            )
            result = self._execute_with_retry(request)
        except DriveClientError:
            raise
        except Exception as exc:
            raise DriveClientError(f"Failed to create folder '{name}': {exc}") from exc

        folder_id: str = result["id"]
        logger.info("Created Drive folder '%s' (id=%s).", name, folder_id)
        return folder_id

    def upload_file(self, local_path: str, drive_folder_id: str) -> str:
        file_name = os.path.basename(local_path)
        safe_name = _escape_drive_query(file_name)
        query = (
            f"name='{safe_name}' and '{drive_folder_id}' in parents"
            " and trashed=false"
        )
        try:
            request = self._service.files().list(
                q=query, fields="files(id)", spaces="drive"
            )
            result = self._execute_with_retry(request)
        except DriveClientError:
            raise
        except Exception as exc:
            raise DriveClientError(
                f"Failed to query file '{file_name}': {exc}"
            ) from exc

        media = MediaFileUpload(local_path, resumable=True)
        existing = result.get("files", [])

        try:
            if existing:
                file_id: str = existing[0]["id"]
                request = self._service.files().update(
                    fileId=file_id, media_body=media, fields="id"
                )
                self._execute_with_retry(request)
                logger.info("Updated Drive file '%s' (id=%s).", file_name, file_id)
            else:
                metadata = {"name": file_name, "parents": [drive_folder_id]}
                request = self._service.files().create(
                    body=metadata, media_body=media, fields="id"
                )
                result = self._execute_with_retry(request)
                file_id = result["id"]
                logger.info("Uploaded Drive file '%s' (id=%s).", file_name, file_id)
        except DriveClientError:
            raise
        except Exception as exc:
            raise DriveClientError(
                f"Failed to upload file '{file_name}': {exc}"
            ) from exc

        return file_id

    def list_remote_files(self, drive_folder_id: str) -> list[dict]:
        results: list[dict] = []
        self._list_folder_recursive(drive_folder_id, "", results)
        return results

    def _list_folder_recursive(
        self, folder_id: str, prefix: str, results: list[dict]
    ) -> None:
        page_token: str | None = None

        while True:
            try:
                request = self._service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                    spaces="drive",
                    pageToken=page_token,
                )
                response = self._execute_with_retry(request)
            except DriveClientError:
                raise
            except Exception as exc:
                raise DriveClientError(
                    f"Failed to list folder id='{folder_id}': {exc}"
                ) from exc

            for item in response.get("files", []):
                relative_path = f"{prefix}{item['name']}" if not prefix else f"{prefix}/{item['name']}"
                if item["mimeType"] == "application/vnd.google-apps.folder":
                    self._list_folder_recursive(item["id"], relative_path, results)
                else:
                    results.append(
                        {
                            "id": item["id"],
                            "name": item["name"],
                            "relative_path": relative_path,
                            "modified_time": item.get("modifiedTime", ""),
                        }
                    )

            page_token = response.get("nextPageToken")
            if not page_token:
                break

    def download_file(self, drive_file_id: str, local_path: str) -> None:
        parent_dir = os.path.dirname(local_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        try:
            request = self._service.files().get_media(fileId=drive_file_id)
        except Exception as exc:
            raise DriveClientError(
                f"Failed to build download request for id='{drive_file_id}': {exc}"
            ) from exc

        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        try:
            done = False
            while not done:
                _, done = downloader.next_chunk()
        except Exception as exc:
            raise DriveClientError(
                f"Failed to download file id='{drive_file_id}': {exc}"
            ) from exc

        with open(local_path, "wb") as f:
            f.write(buffer.getvalue())

    def _execute_with_retry(self, request: Any) -> Any:
        last_exc: Exception | None = None

        for attempt in range(3):
            try:
                return request.execute()
            except HttpError as exc:
                if exc.resp.status in _RETRYABLE_STATUSES:
                    delay = 2 ** attempt
                    logger.warning(
                        "Retryable HTTP %s error (attempt %d/3). Retrying in %ds.",
                        exc.resp.status,
                        attempt + 1,
                        delay,
                    )
                    time.sleep(delay)
                    last_exc = exc
                else:
                    raise DriveClientError(str(exc)) from exc
            except Exception as exc:
                raise DriveClientError(str(exc)) from exc

        logger.error("All 3 retry attempts exhausted. Last error: %s", last_exc)
        raise DriveClientError(f"Request failed after 3 retries: {last_exc}") from last_exc
