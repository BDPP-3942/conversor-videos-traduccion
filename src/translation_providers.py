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
    def __init__(self, source: str, target: str, api_key: str) -> None:
        self.source = source
        self.target = target
        self.api_key = api_key

    def translate(self, text: str) -> str:
        return self.translate_batch([text])[0]

    @staticmethod
    def _request(url: str, headers: dict[str, str], payload: object) -> object:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
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


class DeepLBatchProvider(_HttpBatchProvider):
    """Direct DeepL API client using the current POST/auth-header API."""

    def __init__(self, source: str, target: str, api_key: str) -> None:
        super().__init__(source.upper(), target.upper(), api_key)
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
        super().__init__(source, target, api_key)
        self.region = region.strip()
        self.base_url = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0"

    def translate_batch(self, texts: list[str]) -> list[str]:
        if not texts:
            return []
        if len(texts) > self.MAX_ITEMS or sum(len(text) for text in texts) > self.MAX_CHARS:
            raise ValueError(
                "Microsoft batch exceeds the 25-item/5000-character request limit"
            )
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


def _mymemory_language(language: str, languages: dict[str, str]) -> str:
    value = str(language).strip()
    if value == "auto":
        return value
    if value in languages.values():
        return value
    if value in languages:
        return languages[value]
    prefix = f"{value.lower()}-"
    for code in languages.values():
        if str(code).lower().startswith(prefix):
            return code
    raise ValueError(f"MyMemory does not support configured language {language!r}")


def build_translation_provider(name: str, settings: AppSettings) -> TranslationProvider:
    """Build the configured provider without adding a service or local daemon."""
    provider = name.strip().lower().replace("-", "_")
    try:
        from deep_translator import GoogleTranslator, MyMemoryTranslator
    except ImportError as exc:
        raise RuntimeError("Translation support requires the deep-translator package") from exc

    if provider == "google":
        return GoogleTranslator(source=settings.source_lang, target=settings.target_lang)
    if provider == "deepl":
        api_key = os.getenv("DEEPL_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("DeepL provider requires DEEPL_API_KEY")
        return DeepLBatchProvider(settings.source_lang, settings.target_lang, api_key)
    if provider == "microsoft":
        api_key = os.getenv("MICROSOFT_TRANSLATOR_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Microsoft provider requires MICROSOFT_TRANSLATOR_API_KEY")
        return MicrosoftBatchProvider(
            settings.source_lang,
            settings.target_lang,
            api_key,
            os.getenv("MICROSOFT_TRANSLATOR_REGION", ""),
        )
    if provider in {"mymemory", "my_memory"}:
        try:
            from deep_translator.constants import MY_MEMORY_LANGUAGES_TO_CODES
        except ImportError as exc:
            raise RuntimeError("Installed deep-translator lacks MyMemory language metadata") from exc
        source = _mymemory_language(settings.source_lang, MY_MEMORY_LANGUAGES_TO_CODES)
        target = _mymemory_language(settings.target_lang, MY_MEMORY_LANGUAGES_TO_CODES)
        return MyMemoryTranslator(source=source, target=target)
    raise ValueError(f"Unsupported translation provider: {name}")
