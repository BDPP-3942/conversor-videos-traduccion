from __future__ import annotations

from src.desktop import DesktopApp


class _FakeVariable:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value) -> None:
        self.value = value


class _FakeWidget:
    def __init__(self) -> None:
        self.configured: dict[str, object] = {}

    def configure(self, **kwargs: object) -> None:
        self.configured.update(kwargs)


def _app_for_toggle_test() -> DesktopApp:
    app = DesktopApp.__new__(DesktopApp)
    app.webm = _FakeVariable(False)
    app.tts = _FakeVariable(False)
    app.tts_required = _FakeVariable(True)
    app.webm_toggle = _FakeWidget()
    app.tts_toggle = _FakeWidget()
    app.tts_required_check = _FakeWidget()
    return app


def test_webm_toggle_changes_boolean_state() -> None:
    app = _app_for_toggle_test()

    app._toggle_webm()
    assert app.webm.get() is True
    assert app.webm_toggle.configured["text"] == "WebM: ACTIVADO"

    app._toggle_webm()
    assert app.webm.get() is False
    assert app.webm_toggle.configured["text"] == "WebM: DESACTIVADO"


def test_tts_toggle_is_optional_and_clears_required_when_disabled() -> None:
    app = _app_for_toggle_test()

    app._refresh_feature_toggles()
    assert app.tts.get() is False
    assert app.tts_required.get() is False
    assert app.tts_required_check.configured["state"] == "disabled"

    app._toggle_tts()
    assert app.tts.get() is True
    assert app.tts_toggle.configured["text"] == "TTS: ACTIVADO"
    assert app.tts_required_check.configured["state"] == "normal"

    app.tts_required.set(True)
    app._toggle_tts()
    assert app.tts.get() is False
    assert app.tts_required.get() is False
    assert app.tts_required_check.configured["state"] == "disabled"
