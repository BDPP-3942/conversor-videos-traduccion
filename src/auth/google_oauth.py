from __future__ import annotations

from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/drive"]


class GoogleOAuthManager:
    def __init__(self, credentials_file: Path, token_file: Path) -> None:
        self.credentials_file = credentials_file
        self.token_file = token_file

    def authorize(self, *, open_browser: bool = True):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as exc:
            raise RuntimeError(
                "Google OAuth requires google-auth-oauthlib"
            ) from exc

        credentials = None
        if self.token_file.is_file():
            credentials = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
        if credentials and credentials.valid:
            return credentials
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self.save(credentials)
            return credentials

        if not self.credentials_file.is_file():
            raise FileNotFoundError(
                f"Google OAuth client credentials not found: {self.credentials_file}"
            )
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_file), SCOPES)
        credentials = flow.run_local_server(port=0, open_browser=open_browser)
        self.save(credentials)
        return credentials

    def refresh_silently(self) -> tuple[object, bool]:
        """Validate/refresh a stored Google credential without ever opening a browser.

        Returns (credentials, refreshed). Missing credentials or a non-refreshable
        credential are treated as not ready for unattended execution.
        """
        try:
            from google.auth.exceptions import RefreshError
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
        except ImportError as exc:
            raise RuntimeError(
                "Google OAuth requires google-auth-oauthlib"
            ) from exc

        if not self.token_file.is_file():
            raise RuntimeError("Google token.json is missing; run the one-time interactive setup.")

        credentials = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
        if credentials.valid:
            return credentials, False
        if not credentials.refresh_token:
            raise RuntimeError("Google credential has no refresh token; interactive authorization is required.")
        try:
            credentials.refresh(Request())
        except RefreshError as exc:
            raise RuntimeError(
                "Google refresh token is no longer valid; run the one-time interactive setup again."
            ) from exc
        self.save(credentials)
        return credentials, True

    def status(self) -> dict[str, object]:
        if not self.token_file.is_file():
            return {"authorized": False, "token_file": str(self.token_file)}
        try:
            from google.oauth2.credentials import Credentials
            credentials = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
            return {
                "authorized": bool(credentials.valid or credentials.refresh_token),
                "valid": bool(credentials.valid),
                "refreshable": bool(credentials.refresh_token),
                "token_file": str(self.token_file),
            }
        except Exception as exc:
            return {"authorized": False, "token_file": str(self.token_file), "error": str(exc)}

    def save(self, credentials) -> None:
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.token_file.write_text(credentials.to_json(), encoding="utf-8")
        try:
            self.token_file.chmod(0o600)
        except OSError:
            pass
