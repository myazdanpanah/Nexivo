"""
LLM Gateway Service — Unified interface for all LLM providers.

Supports:
- Ollama (local, Gemma 4 / any model)
- OpenAI (GPT-4o, GPT-4o-mini, etc.)
- Google Gemini (gemini-2.0-flash, gemini-1.5-pro, etc.)
- Anthropic (Claude 3.5 Sonnet, etc.)
- DeepSeek

All calls go through this service for:
- Consistent API across providers
- Usage tracking
- Error handling
- Fallback logic
"""

import time
import logging
import json
import requests

logger = logging.getLogger(__name__)

# ─── Provider implementations ────────────────────────────────────


class OllamaProvider:
    """Ollama local LLM provider."""

    def __init__(self, base_url: str, model: str, **kwargs):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 4096)

    def chat(self, messages: list[dict], **kwargs) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": float(self.temperature),
                "num_predict": self.max_tokens,
            },
        }
        resp = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "content": data.get("message", {}).get("content", ""),
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "model": self.model,
        }

    def health_check(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


class OpenAIProvider:
    """OpenAI API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str = "", **kwargs):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 4096)

    def chat(self, messages: list[dict], **kwargs) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": float(self.temperature),
            "max_tokens": self.max_tokens,
        }
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage", {})
        return {
            "content": data["choices"][0]["message"]["content"],
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "model": self.model,
        }

    def health_check(self) -> bool:
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.get(f"{self.base_url}/models", headers=headers, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


class GeminiProvider:
    """Google Gemini API provider."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", **kwargs):
        self.api_key = api_key
        self.model = model
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 4096)

    def chat(self, messages: list[dict], **kwargs) -> dict:
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": float(self.temperature),
                "maxOutputTokens": self.max_tokens,
            },
        }
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        return {
            "content": content,
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
            "model": self.model,
        }

    def health_check(self) -> bool:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
            resp = requests.get(url, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


class AnthropicProvider:
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", **kwargs):
        self.api_key = api_key
        self.model = model
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 4096)

    def chat(self, messages: list[dict], **kwargs) -> dict:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        # Anthropic requires system message separate
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append({"role": msg["role"], "content": msg["content"]})

        payload = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": self.max_tokens,
            "temperature": float(self.temperature),
        }
        if system_msg:
            payload["system"] = system_msg

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage", {})
        return {
            "content": data["content"][0]["text"],
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
            "model": self.model,
        }

    def health_check(self) -> bool:
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            }
            resp = requests.get("https://api.anthropic.com/v1/models", headers=headers, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


# ─── Gateway ─────────────────────────────────────────────────────

PROVIDER_MAP = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "anthropic": AnthropicProvider,
}


def get_provider(provider_config) -> object:
    """Instantiate the right provider from a LLMProvider model instance."""
    cls = PROVIDER_MAP.get(provider_config.provider_type)
    if not cls:
        raise ValueError(f"Unknown provider type: {provider_config.provider_type}")

    kwargs = {
        "temperature": float(provider_config.temperature),
        "max_tokens": provider_config.max_tokens,
    }

    if provider_config.provider_type == "ollama":
        return cls(
            base_url=provider_config.api_base_url or "http://localhost:11434",
            model=provider_config.model_name,
            **kwargs,
        )
    elif provider_config.provider_type in ("openai", "anthropic"):
        return cls(
            api_key=provider_config.api_key,
            model=provider_config.model_name,
            **kwargs,
        )
    elif provider_config.provider_type == "gemini":
        return cls(
            api_key=provider_config.api_key,
            model=provider_config.model_name,
            **kwargs,
        )
    else:
        return cls(api_key=provider_config.api_key, model=provider_config.model_name, **kwargs)


def chat_completion(company, messages: list[dict], feature: str = "chat", user=None) -> dict:
    """
    Main gateway function: sends messages to the company's active LLM provider.
    Returns: {"content": str, "prompt_tokens": int, "completion_tokens": int, "model": str, "duration_ms": int}
    """
    from .models import LLMProvider, LLMUsageLog

    provider = LLMProvider.objects.filter(company=company, is_active=True).first()
    if not provider:
        raise ValueError("No active LLM provider configured for this company")

    llm = get_provider(provider)

    start = time.time()
    try:
        result = llm.chat(messages)
    except Exception as e:
        logger.error("LLM provider %s failed: %s", provider.name, e)
        raise

    duration_ms = int((time.time() - start) * 1000)
    total_tokens = result.get("prompt_tokens", 0) + result.get("completion_tokens", 0)

    # Log usage
    LLMUsageLog.objects.create(
        company=company,
        provider=provider,
        user=user,
        feature=feature,
        prompt_tokens=result.get("prompt_tokens", 0),
        completion_tokens=result.get("completion_tokens", 0),
        total_tokens=total_tokens,
        duration_ms=duration_ms,
    )

    result["duration_ms"] = duration_ms
    return result
