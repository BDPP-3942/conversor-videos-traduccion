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


class TranslationRateLimitError(RuntimeError):
    """Provider temporarily rejected a request because of rate limiting."""


class TranslationConfigurationError(RuntimeError):
    """Provider cannot run because its configuration is invalid or incomplete."""


class TranslationResourceError(RuntimeError):
    """Provider cannot run because a required local resource is unavailable or invalid."""


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
        if urllib.parse.urlsplit(url).scheme != "https":
            raise ValueError("Translation provider URL must use HTTPS")
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code in {402, 403, 456}:
                raise TranslationQuotaError(
                    f"translation provider quota/authorization response {exc.code}: {detail}"
                ) from exc
            if exc.code == 429:
                raise TranslationRateLimitError(
                    f"translation provider rate limit response 429: {detail}"
                ) from exc
            raise RuntimeError(f"translation provider HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"translation provider connection failed: {exc}") from exc


class MistralBatchProvider(_HttpBatchProvider):
    """Mistral chat API provider using structured JSON output for segment batches."""

    URL = "https://api.mistral.ai/v1/chat/completions"
    DEFAULT_MODEL = "mistral-small-latest"
    MAX_ITEMS = 50
    MAX_CHARS = 20_000

    def __init__(self, source: str, target: str, api_key: str, model: str = "") -> None:
        super().__init__(source.lower(), target.lower())
        self.api_key = api_key
        self.model = model.strip() or self.DEFAULT_MODEL

    def translate_batch(self, texts: list[str]) -> list[str]:
        if not texts:
            return []
        if len(texts) > self.MAX_ITEMS or sum(len(text) for text in texts) > self.MAX_CHARS:
            raise ValueError("Mistral batch exceeds the configured request size limit")
        items = [{"id": index, "text": text} for index, text in enumerate(texts)]
        system_prompt = (
            f"Translate each input from {self.source} to {self.target}. "
            "Return JSON only as an object with a 'translations' array. "
            "The array must contain exactly one string for every input, in the same order. "
            "Do not merge, split, omit, explain, or add commentary. "
            "Preserve names, numbers and formatting."
        )
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(items, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
        }
        result = self._request(
            self.URL,
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            payload,
        )
        try:
            content = result["choices"][0]["message"]["content"]
            parsed = json.loads(content) if isinstance(content, str) else content
            translations = parsed["translations"]
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise RuntimeError("Mistral returned an invalid structured translation response") from exc
        if not isinstance(translations, list) or len(translations) != len(texts):
            count = len(translations) if isinstance(translations, list) else "invalid"
            raise RuntimeError(f"Mistral returned {count} translations for {len(texts)} inputs")
        return [str(item) for item in translations]


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
        result = self._request(
            f"{self.url}?{params}",
            {"Content-Type": "application/json"},
            {"q": texts, "source": self.source, "target": self.target, "format": "text"},
        )
        try:
            translations = result["data"]["translations"]
        except (KeyError, TypeError) as exc:
            raise RuntimeError("Google Cloud returned an invalid translation response") from exc
        if len(translations) != len(texts):
            raise RuntimeError(f"Google returned {len(translations)} translations for {len(texts)} inputs")
        return [str(item.get("translatedText", "")) for item in translations]


class DeepLBatchProvider(_HttpBatchProvider):
    """Direct DeepL API client using the official HTTP API."""

    MAX_ITEMS = 50
    MAX_CHARS = 30_000

    def __init__(self, source: str, target: str, api_key: str) -> None:
        super().__init__(source.upper(), target.upper())
        self.api_key = api_key
        self.base_url = "https://api-free.deepl.com/v2"

    def translate_batch(self, texts: list[str]) -> list[str]:
        if not texts:
            return []
        if len(texts) > self.MAX_ITEMS or sum(len(text) for text in texts) > self.MAX_CHARS:
            raise ValueError("DeepL batch exceeds the configured request size limit")
        result = self._request(
            f"{self.base_url}/translate",
            {
                "Authorization": f"DeepL-Auth-Key {self.api_key}",
                "Content-Type": "application/json",
            },
            {"text": texts, "source_lang": self.source, "target_lang": self.target},
        )
        translations = result.get("translations", []) if isinstance(result, dict) else []
        if len(translations) != len(texts):
            raise RuntimeError(f"DeepL returned {len(translations)} translations for {len(texts)} inputs")
        return [str(item.get("text", "")) for item in translations]


class MicrosoftBatchProvider(_HttpBatchProvider):
    """Direct Azure Translator v3 client retained for backwards compatibility."""

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
        result = self._request(
            f"{self.base_url}&{params}",
            headers,
            [{"Text": text} for text in texts],
        )
        if not isinstance(result, list) or len(result) != len(texts):
            count = len(result) if isinstance(result, list) else "invalid"
            raise RuntimeError(f"Microsoft returned {count} translations for {len(texts)} inputs")
        outputs: list[str] = []
        for item in result:
            translations = item.get("translations", [])
            outputs.append(str(translations[0].get("text", "")) if translations else "")
        return outputs


class MyMemoryBatchProvider(_HttpBatchProvider):
    """Direct MyMemory client; supports optional registered-email quota."""

    MAX_CHARS_PER_REQUEST = 500

    def __init__(self, source: str, target: str, email: str = "") -> None:
        super().__init__(source, target)
        self.url = "https://api.mymemory.translated.net/get"
        self.email = email.strip()

    def translate_batch(self, texts: list[str]) -> list[str]:
        outputs: list[str] = []
        for text in texts:
            if len(text) > self.MAX_CHARS_PER_REQUEST:
                raise ValueError("MyMemory request text exceeds the configured 500-character limit")
            params = {"q": text, "langpair": f"{self.source}|{self.target}"}
            if self.email:
                params["de"] = self.email
            request = urllib.request.Request(
                f"{self.url}?{urllib.parse.urlencode(params)}", method="GET"
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
                    result = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if exc.code in {402, 403, 456}:
                    raise TranslationQuotaError(
                        f"MyMemory quota/authorization response {exc.code}: {detail}"
                    ) from exc
                if exc.code == 429:
                    raise TranslationRateLimitError(
                        f"MyMemory rate limit response 429: {detail}"
                    ) from exc
                raise RuntimeError(f"MyMemory HTTP {exc.code}: {detail}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                raise RuntimeError(f"MyMemory connection failed: {exc}") from exc
            if result.get("quotaFinished"):
                raise TranslationQuotaError("MyMemory reported that its free quota is exhausted")
            response_data = result.get("responseData", {})
            output = str(response_data.get("translatedText", ""))
            if not output:
                raise RuntimeError(f"MyMemory returned no translation: {result.get('responseDetails', '')}")
            outputs.append(output)
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
    """Build a provider using official HTTP APIs and the optional offline local model."""
    provider = name.strip().lower().replace("-", "_")
    source = _language_code(settings.source_lang)
    target = _language_code(settings.target_lang)
    if provider in {"local", "local_model", "ct2", "opus_mt"}:
        if source != "es" or target != "en":
            raise TranslationConfigurationError(
                "The bundled local translation model currently supports only es→en"
            )
        from src.local_translation import LocalTranslationProvider

        try:
            return LocalTranslationProvider(settings)
        except TranslationConfigurationError:
            raise
        except ValueError as exc:
            raise TranslationConfigurationError(str(exc)) from exc
        except Exception as exc:
            raise TranslationResourceError(
                f"Local translation resource/runtime is unavailable: {exc}"
            ) from exc
    if provider == "mistral":
        api_key = os.getenv("MISTRAL_API_KEY", "").strip()
        if not api_key:
            raise TranslationConfigurationError("Mistral provider requires MISTRAL_API_KEY")
        return MistralBatchProvider(source, target, api_key, os.getenv("MISTRAL_MODEL", ""))
    if provider == "google":
        api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY", "").strip()
        if not api_key:
            raise TranslationConfigurationError("Google provider requires GOOGLE_TRANSLATE_API_KEY")
        return GoogleCloudBatchProvider(source, target, api_key)
    if provider == "deepl":
        api_key = os.getenv("DEEPL_API_KEY", "").strip()
        if not api_key:
            raise TranslationConfigurationError("DeepL provider requires DEEPL_API_KEY")
        return DeepLBatchProvider(source, target, api_key)
    if provider == "microsoft":
        api_key = os.getenv("MICROSOFT_TRANSLATOR_API_KEY", "").strip()
        if not api_key:
            raise TranslationConfigurationError("Microsoft provider requires MICROSOFT_TRANSLATOR_API_KEY")
        return MicrosoftBatchProvider(source, target, api_key, os.getenv("MICROSOFT_TRANSLATOR_REGION", ""))
    if provider in {"mymemory", "my_memory"}:
        return MyMemoryBatchProvider(source, target, os.getenv("MYMEMORY_EMAIL", ""))
    raise TranslationConfigurationError(f"Unsupported translation provider: {name}")
