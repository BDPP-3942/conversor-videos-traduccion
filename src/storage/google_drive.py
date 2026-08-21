from __future__ import annotations

from pathlib import Path

from src.file_naming import normalize_component, normalize_filename
from src.storage.base import StorageFile, StorageProvider


class GoogleDriveStorageProvider(StorageProvider):
    def __init__(
        self,
        credentials_file: Path,
        token_file: Path,
        archive_folder_id: str = "",
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
        self._archive_folder_id = archive_folder_id
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
                "Run the one-time interactive setup command on the deployment machine "
                "and keep the generated token.json available to the scheduled task account."
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
        try:
            self._token_file.chmod(0o600)
        except OSError:
            pass

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

    def folder_exists(self, parent: str, name: str) -> bool:
        escaped = name.replace("'", "\\'")
        query = (
            f"'{parent}' in parents and trashed = false "
            "and mimeType = 'application/vnd.google-apps.folder' "
            f"and name = '{escaped}'"
        )
        result = self._service.files().list(
            q=query, spaces="drive", fields="files(id)", pageSize=1
        ).execute()
        return bool(result.get("files"))

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


    def file_exists(self, parent: str, name: str) -> bool:
        escaped = name.replace("'", "\\'")
        query = (
            f"'{parent}' in parents and trashed = false "
            "and mimeType != 'application/vnd.google-apps.folder' "
            f"and name = '{escaped}'"
        )
        result = self._service.files().list(
            q=query, spaces="drive", fields="files(id)", pageSize=1
        ).execute()
        return bool(result.get("files"))

    def _list_children(self, parent: str) -> list[dict]:
        query = f"'{parent}' in parents and trashed = false"
        files = []
        page_token = None
        while True:
            response = (
                self._service.files().list(
                    q=query, spaces="drive",
                    fields="nextPageToken, files(id,name,mimeType)",
                    pageSize=1000, pageToken=page_token,
                ).execute()
            )
            files.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                return files

    def normalize_existing_output_names(
        self, target: str, original_transcript_subdir: str
    ) -> dict[str, str]:
        renamed: dict[str, str] = {}
        for item in self._list_children(target):
            if item["mimeType"] != "application/vnd.google-apps.folder":
                continue
            old = item["name"]
            new = normalize_component(old)
            folder_id = item["id"]
            if new != old:
                # Only rename when the normalized name is not already occupied.
                if not self.folder_exists(target, new):
                    self._service.files().update(
                        fileId=folder_id, body={"name": new}, fields="id,name"
                    ).execute()
                    renamed[old] = new
                    old = new
            for child in self._list_children(folder_id):
                child_name = child["name"]
                if child["mimeType"] == "application/vnd.google-apps.folder":
                    child_folder_id = child["id"]
                    if child_name != original_transcript_subdir:
                        normalized_dir = normalize_component(child_name)
                        if normalized_dir != child_name:
                            self._service.files().update(
                                fileId=child_folder_id, body={"name": normalized_dir}, fields="id,name"
                            ).execute()
                            child_name = normalized_dir
                    for nested in self._list_children(child_folder_id):
                        if nested["mimeType"] == "application/vnd.google-apps.folder":
                            continue
                        normalized_nested = normalize_filename(nested["name"])
                        if normalized_nested != nested["name"] and not self.file_exists(child_folder_id, normalized_nested):
                            self._service.files().update(
                                fileId=nested["id"], body={"name": normalized_nested}, fields="id,name"
                            ).execute()
                    continue
                normalized_file = normalize_filename(child_name)
                if normalized_file != child_name and not self.file_exists(folder_id, normalized_file):
                    self._service.files().update(
                        fileId=child["id"], body={"name": normalized_file}, fields="id,name"
                    ).execute()
        return renamed

    def finalize_source(self, file: StorageFile, status: str, output_folders: list[str] | None = None) -> None:
        if status != "success":
            return
        # Archive the cloud source instead of deleting it, so scheduled runs do not process it again.
        # The archive folder is injected by the provider factory through _archive_folder_id.
        archive_folder_id = getattr(self, "_archive_folder_id", "")
        if not archive_folder_id:
            raise RuntimeError(
                "Google Drive archive folder is not configured. Set google_drive.archive_folder_id "
                "or GDRIVE_ARCHIVE_FOLDER_ID before running unattended cloud mode."
            )
        try:
            self._service.files().update(
                fileId=file.id,
                addParents=archive_folder_id,
                removeParents=self._find_parent_ids(file.id),
                fields="id,name,parents",
            ).execute()
        except Exception:
            # Keep the original error so pipeline reports a cloud finalization problem.
            raise

    def _find_parent_ids(self, file_id: str) -> str:
        meta = self._service.files().get(fileId=file_id, fields="parents").execute()
        return ",".join(meta.get("parents", []))

    def close(self) -> None:
        self._service.close()
