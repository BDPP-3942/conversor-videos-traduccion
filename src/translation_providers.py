from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Protocol

from config.settings import AppSettings


class TranslationProvider(Protocol):
    """Minimal interface required by the translation pipeline."""

    def translate_batch(self, texts: list[str]) -> list[str]: ...

    def translate(self, text: str) -> str: ...


class TranslationQuotaError(RuntimeError):
    """Provider reported that its remote quota or free allowance is exhausted."""


class _HttpBatchProvider:
    def __init__(self, source: str, target: str) -> None:
        self.source = source
        self.target = target

    def translate(self, text: str) -> str:
        return self.translate_batch([text])[0]

    @staticmethod
    def _request(
        url: str,
        headers: dict[str, str],
        payload: object,
        method: str = "POST",
    ) -> object:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code in {402, 403, 429, 456}:
                raise TranslationQuotaError(
                    f"translation provider quota/authorization response {exc.code}: {detail}"
                ) from exc
            raise RuntimeError(f"translation provider HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"translation provider connection failed: {exc}") from exc


class GoogleCloudBatchProvider(_HttpBatchProvider):
    """Official Google Cloud Translation v2 client; no third-party wrapper."""

    MAX_ITEMS = 100
    MAX_CHARS = 25_000

    def __init__(self, source: str, target: str, api_key: str) -> None:
        super().__init__(source.lower(), target.lower())
        self.api_key = api_key
        self.url = "https://translation.googleapis.com/language/translate/v2"

    def translate_batch(self, texts: list[str]) -> list[str]:
        if not texts:
            return []
        if len(texts) > self.MAX_ITEMS or sum(len(text) for text in texts) > self.MAX_CHARS:
            raise ValueError("Google batch exceeds the configured request size limit")
        params = urllib.parse.urlencode({"key": self.api_key})
        payload = {
            "q": texts,
            "source": self.source,
            "target": self.target,
            "format": "text",
        }
        result = self._request(
            f"{self.url}?{params}",
            {"Content-Type": "application/json"},
            payload,
        )
        try:
            translations = result["data"]["translations"]
        except (KeyError, TypeError) as exc:
            raise RuntimeError("Google Cloud returned an invalid translation response") from exc
        if len(translations) != len(texts):
            raise RuntimeError(
                f"Google returned {len(translations)} translations for {len(texts)} inputs"
            )
        return [str(item.get("translatedText", "")) for item in translations]


class DeepLBatchProvider(_HttpBatchProvider):
    """Direct DeepL API client using the official HTTP API."""

    def __init__(self, source: str, target: str, api_key: str) -> None:
        super().__init__(source.upper(), target.upper())
        self.api_key = api_key
        self.base_url = "https://api-free.deepl.com/v2"

    def translate_batch(self, texts: list[str]) -> list[str]:
        if not texts:
            return []
        payload = {"text": texts, "source_lang": self.source, "target_lang": self.target}
        result = self._request(
            f"{self.base_url}/translate",
            {
                "Authorization": f"DeepL-Auth-Key {self.api_key}",
                "Content-Type": "application/json",
            },
            payload,
        )
        translations = result.get("translations", []) if isinstance(result, dict) else []
        if len(translations) != len(texts):
            raise RuntimeError(
                f"DeepL returned {len(translations)} translations for {len(texts)} inputs"
            )
        return [str(item.get("text", "")) for item in translations]


class MicrosoftBatchProvider(_HttpBatchProvider):
    """Direct Azure Translator v3 client with real multi-text requests."""

    MAX_ITEMS = 25
    MAX_CHARS = 5_000

    def __init__(self, source: str, target: str, api_key: str, region: str = "") -> None:
        super().__init__(source, target)
        self.api_key = api_key
        self.region = region.strip()
        self.base_url = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0"

    def translate_batch(self, texts: list[str]) -> list[str]:
        if not texts:
            return []
        if len(texts) > self.MAX_ITEMS or sum(len(text) for text in texts) > self.MAX_CHARS:
            raise ValueError("Microsoft batch exceeds the 25-item/5000-character request limit")
        params = urllib.parse.urlencode({"from": self.source, "to": self.target})
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json",
        }
        if self.region:
            headers["Ocp-Apim-Subscription-Region"] = self.region
        payload = [{"Text": text} for text in texts]
        result = self._request(f"{self.base_url}&{params}", headers, payload)
        if not isinstance(result, list) or len(result) != len(texts):
            count = len(result) if isinstance(result, list) else "invalid"
            raise RuntimeError(f"Microsoft returned {count} translations for {len(texts)} inputs")
        outputs: list[str] = []
        for item in result:
            translations = item.get("translations", [])
            outputs.append(str(translations[0].get("text", "")) if translations else "")
        return outputs


class MyMemoryBatchProvider(_HttpBatchProvider):
    """Direct MyMemory client; kept as the lowest-priority free fallback."""

    def __init__(self, source: str, target: str) -> None:
        super().__init__(source, target)
        self.url = "https://api.mymemory.translated.net/get"

    def translate_batch(self, texts: list[str]) -> list[str]:
        outputs: list[str] = []
        for text in texts:
            query = urllib.parse.urlencode(
                {"q": text, "langpair": f"{self.source}|{self.target}"}
            )
            request = urllib.request.Request(f"{self.url}?{query}", method="GET")
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    result = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if exc.code in {402, 403, 429}:
                    raise TranslationQuotaError(
                        f"MyMemory quota/authorization response {exc.code}: {detail}"
                    ) from exc
                raise RuntimeError(f"MyMemory HTTP {exc.code}: {detail}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                raise RuntimeError(f"MyMemory connection failed: {exc}") from exc
            response_data = result.get("responseData", {})
            translated = str(response_data.get("translatedText", ""))
            outputs.append(translated)
        return outputs


def _language_code(language: str) -> str:
    normalized = language.strip().lower()
    aliases = {
        "spanish": "es",
        "es-es": "es",
        "english": "en",
        "en-gb": "en",
        "en-us": "en",
    }
    return aliases.get(normalized, normalized.split("-", 1)[0])


def build_translation_provider(name: str, settings: AppSettings) -> TranslationProvider:
    """Build a provider using official HTTP APIs and standard-library networking."""
    provider = name.strip().lower().replace("-", "_")
    source = _language_code(settings.source_lang)
    target = _language_code(settings.target_lang)

    if provider == "google":
        api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Google provider requires GOOGLE_TRANSLATE_API_KEY")
        return GoogleCloudBatchProvider(source, target, api_key)
    if provider == "deepl":
        api_key = os.getenv("DEEPL_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("DeepL provider requires DEEPL_API_KEY")
        return DeepLBatchProvider(source, target, api_key)
    if provider == "microsoft":
        api_key = os.getenv("MICROSOFT_TRANSLATOR_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Microsoft provider requires MICROSOFT_TRANSLATOR_API_KEY")
        return MicrosoftBatchProvider(
            source,
            target,
            api_key,
            os.getenv("MICROSOFT_TRANSLATOR_REGION", ""),
        )
    if provider in {"mymemory", "my_memory"}:
        return MyMemoryBatchProvider(source, target)
    raise ValueError(f"Unsupported translation provider: {name}")
