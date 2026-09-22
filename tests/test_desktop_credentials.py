from __future__ import annotations

import os

from src.desktop import DesktopApp


class _FakeVariable:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value) -> None:
        self.value = value


def test_gui_credentials_are_scoped_to_operation(monkeypatch) -> None:
    app = DesktopApp.__new__(DesktopApp)
    app.credential_vars = {
        "MISTRAL_API_KEY": _FakeVariable("secret-value"),
        "DEEPL_API_KEY": _FakeVariable(""),
    }
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    observed = []

    def operation():
        observed.append(os.environ.get("MISTRAL_API_KEY"))
        return "ok"

    assert app._with_credentials(operation) == "ok"
    assert observed == ["secret-value"]
    assert "MISTRAL_API_KEY" not in os.environ
