from src.translation_providers import DeepLBatchProvider, MicrosoftBatchProvider


def test_deepl_batch(monkeypatch):
    def fake_request(url, headers, payload):
        assert payload["text"] == ["uno", "dos"]
        return {"translations": [{"text": "one"}, {"text": "two"}]}

    monkeypatch.setattr(
        DeepLBatchProvider,
        "_request",
        staticmethod(fake_request),
    )
    result = DeepLBatchProvider("es", "en", "key").translate_batch(["uno", "dos"])
    assert result == ["one", "two"]


def test_microsoft_batch(monkeypatch):
    def fake_request(url, headers, payload):
        assert len(payload) == 2
        assert headers["Ocp-Apim-Subscription-Region"] == "westeurope"
        return [
            {"translations": [{"text": "one"}]},
            {"translations": [{"text": "two"}]},
        ]

    monkeypatch.setattr(
        MicrosoftBatchProvider,
        "_request",
        staticmethod(fake_request),
    )
    result = MicrosoftBatchProvider("es", "en", "key", "westeurope").translate_batch(["uno", "dos"])
    assert result == ["one", "two"]
