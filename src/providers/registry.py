from __future__ import annotations

from config.settings import resolve_project_path
from src.auth.google_oauth import GoogleOAuthManager
from src.auth.rclone_manager import RcloneManager


class ProviderRegistry:
    """Keeps provider profiles separate from the processing pipeline."""

    def __init__(self, settings) -> None:
        self.settings = settings
        self.profile_dir = resolve_project_path(settings.provider_profile_dir)
        self.google_dir = self.profile_dir / "google"
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.rclone = RcloneManager(
            resolve_project_path(settings.rclone_binary_file),
            resolve_project_path(settings.rclone_config_file),
        )

    def google_auth(self, profile: str) -> dict:
        if not _safe_profile(profile):
            raise ValueError("Invalid Google profile name")
        profile_dir = self.google_dir / profile
        manager = GoogleOAuthManager(profile_dir / "credentials.json", profile_dir / "token.json")
        credentials = manager.authorize()
        return {"profile": profile, "token_file": str(manager.token_file), "valid": credentials.valid}

    def google_status(self, profile: str) -> dict:
        manager = GoogleOAuthManager(
            self.google_dir / profile / "credentials.json",
            self.google_dir / profile / "token.json",
        )
        return manager.status()

    def verify_rclone(self, remote: str, location: str = "") -> dict:
        if remote not in self.rclone.list_remotes():
            raise RuntimeError(f"rclone remote '{remote}' does not exist")
        return self.rclone.healthcheck(remote, location)

    def update_rclone_if_enabled(self) -> dict:
        if not self.settings.auto_update_rclone:
            return {"enabled": False}
        before = self.rclone.version()
        output = self.rclone.self_update()
        after = self.rclone.version()
        return {"enabled": True, "before": before, "after": after, "output": output}

    def list_profiles(self) -> dict:
        google = []
        if self.google_dir.exists():
            google = sorted(item.name for item in self.google_dir.iterdir() if item.is_dir())
        rclone = self.rclone.list_remotes()
        return {"google": google, "rclone": rclone}

    def remove_google(self, profile: str) -> None:
        import shutil
        if not _safe_profile(profile):
            raise ValueError("Invalid Google profile name")
        target = self.google_dir / profile
        if target.exists():
            shutil.rmtree(target)


def _safe_profile(name: str) -> bool:
    return bool(name) and name not in {".", ".."} and all(ch.isalnum() or ch in "-_." for ch in name)
