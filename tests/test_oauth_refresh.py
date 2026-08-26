def test_google_preflight_refreshes_silently(monkeypatch, tmp_path):
    import src.auth.unattended as unattended
    from config.settings import AppSettings

    class FakeCredentials:
        refresh_token = "test-refresh-token"

    class FakeGoogle:
        def __init__(self, credentials_file, token_file):
            self.token_file = token_file

        def refresh_silently(self):
            return FakeCredentials(), True

    monkeypatch.setattr(unattended, "GoogleOAuthManager", FakeGoogle)
    settings = AppSettings(
        provider="google_drive",
        source="gdrive://input",
        target="gdrive://output",
        google_credentials_file=tmp_path / "credentials.json",
        google_token_file=tmp_path / "token.json",
    )
    result = unattended.check_unattended(settings, ensure_rclone_binary=False)
    assert result.ready is True
    assert result.checks["google_token_refreshed"] is True


def test_google_preflight_is_not_interactive_when_refresh_fails(monkeypatch, tmp_path):
    import src.auth.unattended as unattended
    from config.settings import AppSettings

    class FakeGoogle:
        def __init__(self, credentials_file, token_file):
            pass

        def refresh_silently(self):
            raise RuntimeError("Google refresh token is no longer valid")

    monkeypatch.setattr(unattended, "GoogleOAuthManager", FakeGoogle)
    settings = AppSettings(
        provider="google_drive",
        source="gdrive://input",
        target="gdrive://output",
        google_credentials_file=tmp_path / "credentials.json",
        google_token_file=tmp_path / "token.json",
    )
    result = unattended.check_unattended(settings, ensure_rclone_binary=False)
    assert result.ready is False
    assert "refresh token" in result.errors[0].lower()
