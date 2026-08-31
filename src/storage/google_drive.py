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
                "Google Drive support requires google-api-python-client, google-auth-httplib2 and google-auth-oauthlib"
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
            credentials = self._Credentials.from_authorized_user_file(str(self._token_file), scopes)
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
            raise FileNotFoundError(f"Google OAuth credentials not found: {self._credentials_file}")
        flow = self._InstalledAppFlow.from_client_secrets_file(str(self._credentials_file), scopes)
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
        query = f"'{location}' in parents and trashed = false and mimeType = 'application/zip'"
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
            files.extend(StorageFile(id=item["id"], name=item["name"]) for item in response.get("files", []))
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

    def upload_file(self, local_path: Path, location: str, mime_type: str | None = None) -> StorageFile:
        if not local_path.is_file():
            raise FileNotFoundError(f"Local output not found: {local_path}")
        escaped_name = local_path.name.replace(chr(39), chr(92) + chr(39))
        query = f"'{location}' in parents and trashed = false and name = '{escaped_name}'"
        found = (
            self._service.files()
            .list(q=query, spaces="drive", fields="files(id,name)", pageSize=10)
            .execute()
            .get("files", [])
        )
        media = self._MediaFileUpload(str(local_path), mime_type=mime_type, resumable=True)
        if found:
            file_id = found[0]["id"]
            result = self._service.files().update(fileId=file_id, media_body=media, fields="id,name").execute()
        else:
            metadata = {"name": local_path.name, "parents": [location]}
            result = self._service.files().create(body=metadata, media_body=media, fields="id,name").execute()
        return StorageFile(id=result["id"], name=result["name"])

    def folder_exists(self, parent: str, name: str) -> bool:
        escaped = name.replace("'", "\\'")
        query = (
            f"'{parent}' in parents and trashed = false and "
            "mimeType = 'application/vnd.google-apps.folder' and "
            f"name = '{escaped}'"
        )
        result = self._service.files().list(q=query, spaces="drive", fields="files(id)", pageSize=1).execute()
        return bool(result.get("files"))

    def ensure_folder(self, parent: str, name: str) -> str:
        escaped = name.replace("'", "\\'")
        query = (
            f"'{parent}' in parents and trashed = false and "
            "mimeType = 'application/vnd.google-apps.folder' and "
            f"name = '{escaped}'"
        )
        result = self._service.files().list(q=query, spaces="drive", fields="files(id)", pageSize=10).execute()
        if result.get("files"):
            return result["files"][0]["id"]
        metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent]}
        created = self._service.files().create(body=metadata, fields="id").execute()
        return created["id"]

    def file_exists(self, parent: str, name: str) -> bool:
        escaped = name.replace("'", "\\'")
        query = (
            f"'{parent}' in parents and trashed = false and "
            "mimeType != 'application/vnd.google-apps.folder' and "
            f"name = '{escaped}'"
        )
        result = self._service.files().list(q=query, spaces="drive", fields="files(id)", pageSize=1).execute()
        return bool(result.get("files"))

    def list_children(self, parent: str) -> list[StorageFile]:
        return [
            StorageFile(
                id=item["id"], name=item["name"], is_directory=item["mimeType"] == "application/vnd.google-apps.folder"
            )
            for item in self._list_children(parent)
        ]

    def _list_children(self, parent: str) -> list[dict]:
        query = f"'{parent}' in parents and trashed = false"
        files = []
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
            files.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                return files

    def _delete_folder_tree(self, folder_id: str) -> None:
        for child in self._list_children(folder_id):
            if child["mimeType"] == "application/vnd.google-apps.folder":
                self._delete_folder_tree(child["id"])
            else:
                self._service.files().delete(fileId=child["id"]).execute()
        self._service.files().delete(fileId=folder_id).execute()

    def delete_folder(self, parent: str, name: str) -> None:
        folders = [
            item
            for item in self._list_children(parent)
            if item["name"] == name and item["mimeType"] == "application/vnd.google-apps.folder"
        ]
        if not folders:
            return
        self._delete_folder_tree(folders[0]["id"])

    def rename_output_folder(
        self, target: str, old_name: str, new_name: str, original_transcript_subdir: str
    ) -> dict[str, str]:
        if old_name == new_name:
            return {}
        old_items = [
            item
            for item in self._list_children(target)
            if item["name"] == old_name and item["mimeType"] == "application/vnd.google-apps.folder"
        ]
        if not old_items:
            return {}
        if self.folder_exists(target, new_name):
            raise FileExistsError(f"Output target already exists: {new_name}")
        folder_id = old_items[0]["id"]
        self._service.files().update(fileId=folder_id, body={"name": new_name}, fields="id,name").execute()
        for child in self._list_children(folder_id):
            if child["mimeType"] == "application/vnd.google-apps.folder":
                if child["name"] != original_transcript_subdir:
                    continue
                for nested in self._list_children(child["id"]):
                    new_nested = self._rename_artifact_name(nested["name"], old_name, new_name)
                    if new_nested != nested["name"] and not self.file_exists(child["id"], new_nested):
                        self._service.files().update(
                            fileId=nested["id"], body={"name": new_nested}, fields="id,name"
                        ).execute()
                continue
            new_child = self._rename_artifact_name(child["name"], old_name, new_name)
            if new_child != child["name"] and not self.file_exists(folder_id, new_child):
                self._service.files().update(fileId=child["id"], body={"name": new_child}, fields="id,name").execute()
        return {old_name: new_name}

    @staticmethod
    def _rename_artifact_name(old_name: str, old_stem: str, new_stem: str) -> str:
        path = Path(old_name)
        stem = path.stem
        if stem.startswith(old_stem):
            stem = new_stem + stem[len(old_stem) :]
        else:
            stem = normalize_component(stem)
        return f"{stem}{path.suffix.lower()}"

    def normalize_existing_output_names(self, target: str, original_transcript_subdir: str) -> dict[str, str]:
        renamed: dict[str, str] = {}
        for item in self._list_children(target):
            if item["mimeType"] != "application/vnd.google-apps.folder":
                continue
            old = item["name"]
            new = normalize_component(old)
            folder_id = item["id"]
            if new != old and not self.folder_exists(target, new):
                self._service.files().update(fileId=folder_id, body={"name": new}, fields="id,name").execute()
                renamed[old] = new
                old = new
            for child in self._list_children(folder_id):
                if child["mimeType"] == "application/vnd.google-apps.folder":
                    child_folder_id = child["id"]
                    if child["name"] != original_transcript_subdir:
                        normalized_dir = normalize_component(child["name"])
                        if normalized_dir != child["name"]:
                            self._service.files().update(
                                fileId=child_folder_id, body={"name": normalized_dir}, fields="id,name"
                            ).execute()
                    for nested in self._list_children(child_folder_id):
                        if nested["mimeType"] == "application/vnd.google-apps.folder":
                            continue
                        normalized_nested = normalize_filename(nested["name"])
                        if normalized_nested != nested["name"] and not self.file_exists(
                            child_folder_id, normalized_nested
                        ):
                            self._service.files().update(
                                fileId=nested["id"], body={"name": normalized_nested}, fields="id,name"
                            ).execute()
                    continue
                normalized_file = normalize_filename(child["name"])
                if normalized_file != child["name"] and not self.file_exists(folder_id, normalized_file):
                    self._service.files().update(
                        fileId=child["id"], body={"name": normalized_file}, fields="id,name"
                    ).execute()
        return renamed

    def finalize_source(self, file: StorageFile, status: str, output_folders: list[str] | None = None) -> None:
        if status != "success":
            return
        archive_folder_id = self._archive_folder_id
        if not archive_folder_id:
            raise RuntimeError(
                "Google Drive archive folder is not configured. "
                "Set google_drive.archive_folder_id or GDRIVE_ARCHIVE_FOLDER_ID "
                "before running unattended cloud mode."
            )
        self._service.files().update(
            fileId=file.id,
            addParents=archive_folder_id,
            removeParents=self._find_parent_ids(file.id),
            fields="id,name,parents",
        ).execute()

    def _find_parent_ids(self, file_id: str) -> str:
        meta = self._service.files().get(fileId=file_id, fields="parents").execute()
        return ",".join(meta.get("parents", []))

    def close(self) -> None:
        self._service.close()
