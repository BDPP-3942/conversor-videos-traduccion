from __future__ import annotations

from pathlib import Path

from src.storage.base import StorageFile, StorageProvider


class GoogleDriveStorageProvider(StorageProvider):
    def __init__(
        self,
        credentials_file: Path,
        token_file: Path,
        allow_interactive_auth: bool = False,
    ) -> None:
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
        except ImportError as exc:
            raise RuntimeError(
                "Google Drive support requires google-api-python-client, "
                "google-auth-httplib2 and google-auth-oauthlib"
            ) from exc

        self._Request = Request
        self._Credentials = Credentials
        self._InstalledAppFlow = InstalledAppFlow
        self._MediaFileUpload = MediaFileUpload
        self._MediaIoBaseDownload = MediaIoBaseDownload
        self._credentials_file = credentials_file
        self._token_file = token_file
        self._allow_interactive_auth = allow_interactive_auth
        self._service = build("drive", "v3", credentials=self._load_credentials())

    def _load_credentials(self):
        scopes = ["https://www.googleapis.com/auth/drive"]
        credentials = None
        if self._token_file.is_file():
            credentials = self._Credentials.from_authorized_user_file(
                str(self._token_file), scopes
            )
        if credentials and credentials.valid:
            return credentials
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(self._Request())
            self._save_token(credentials)
            return credentials
        if not self._allow_interactive_auth:
            raise RuntimeError(
                "Google Drive is not authorized for unattended execution. "
                "Run 'python main.py auth google' once on an interactive machine "
                "and keep secrets/google/token.json available to the scheduled task."
            )
        if not self._credentials_file.is_file():
            raise FileNotFoundError(
                f"Google OAuth credentials not found: {self._credentials_file}"
            )
        flow = self._InstalledAppFlow.from_client_secrets_file(
            str(self._credentials_file), scopes
        )
        credentials = flow.run_local_server(port=0)
        self._save_token(credentials)
        return credentials

    def _save_token(self, credentials) -> None:
        self._token_file.parent.mkdir(parents=True, exist_ok=True)
        self._token_file.write_text(credentials.to_json(), encoding="utf-8")

    def list_zip_files(self, location: str) -> list[StorageFile]:
        query = (
            f"'{location}' in parents and trashed = false "
            "and mimeType = 'application/zip'"
        )
        files: list[StorageFile] = []
        page_token = None
        while True:
            response = (
                self._service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="nextPageToken, files(id,name,mimeType)",
                    pageSize=1000,
                    pageToken=page_token,
                )
                .execute()
            )
            files.extend(
                StorageFile(id=item["id"], name=item["name"])
                for item in response.get("files", [])
            )
            page_token = response.get("nextPageToken")
            if not page_token:
                return sorted(files, key=lambda item: item.name.lower())

    def download_file(self, file: StorageFile, destination: Path) -> None:
        request = self._service.files().get_media(fileId=file.id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as handle:
            downloader = self._MediaIoBaseDownload(handle, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

    def upload_file(
        self,
        local_path: Path,
        location: str,
        mime_type: str | None = None,
    ) -> StorageFile:
        if not local_path.is_file():
            raise FileNotFoundError(f"Local output not found: {local_path}")
        query = (
            f"'{location}' in parents and trashed = false "
            f"and name = '{local_path.name.replace(chr(39), chr(92)+chr(39))}'"
        )
        found = self._service.files().list(
            q=query, spaces="drive", fields="files(id,name)", pageSize=10
        ).execute().get("files", [])
        media = self._MediaFileUpload(
            str(local_path), mime_type=mime_type, resumable=True
        )
        if found:
            file_id = found[0]["id"]
            result = self._service.files().update(
                fileId=file_id, media_body=media, fields="id,name"
            ).execute()
        else:
            metadata = {"name": local_path.name, "parents": [location]}
            result = self._service.files().create(
                body=metadata, media_body=media, fields="id,name"
            ).execute()
        return StorageFile(id=result["id"], name=result["name"])

    def ensure_folder(self, parent: str, name: str) -> str:
        escaped = name.replace("'", "\\'")
        query = (
            f"'{parent}' in parents and trashed = false "
            "and mimeType = 'application/vnd.google-apps.folder' "
            f"and name = '{escaped}'"
        )
        result = self._service.files().list(
            q=query, spaces="drive", fields="files(id)", pageSize=10
        ).execute()
        if result.get("files"):
            return result["files"][0]["id"]
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent],
        }
        created = self._service.files().create(body=metadata, fields="id").execute()
        return created["id"]

    def close(self) -> None:
        self._service.close()
