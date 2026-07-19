"""
LLM Gateway Models — Multi-provider AI configuration for Nexivo.

Each company can configure multiple LLM providers (Ollama/Gemma 4 local,
OpenAI GPT-4o, Google Gemini, Anthropic Claude, etc.).
One provider is marked as the active default for the company.
"""

import base64
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


PROVIDER_CHOICES = [
    ("ollama", "Ollama (Local)"),
    ("openai", "OpenAI"),
    ("gemini", "Google Gemini"),
    ("anthropic", "Anthropic Claude"),
    ("deepseek", "DeepSeek"),
]


def _get_fernet():
    """Get Fernet encryption instance using Django secret key."""
    secret = settings.SECRET_KEY.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'nexivo-llm-salt-v1',
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret))
    return Fernet(key)


class LLMProvider(models.Model):
    company = models.ForeignKey(
        "accounts.Company", on_delete=models.CASCADE, related_name="llm_providers"
    )
    provider_type = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    name = models.CharField(max_length=100, help_text="Friendly name, e.g. 'Gemma 4 Local'")
    model_name = models.CharField(
        max_length=100,
        help_text="Model ID, e.g. 'gemma3:1b', 'gpt-4o', 'gemini-2.0-flash'",
    )
    api_base_url = models.URLField(
        blank=True, default="",
        help_text="API base URL. For Ollama: http://host:11434.",
    )
    # Encrypted API key (renamed from _api_key_encrypted for Django compatibility)
    api_key_encrypted = models.TextField(
        blank=True, default="",
        help_text="Encrypted API key (not needed for Ollama local).",
    )
    temperature = models.DecimalField(max_digits=3, decimal_places=2, default=0.7)
    max_tokens = models.IntegerField(default=4096)
    is_active = models.BooleanField(default=False, help_text="Only one provider per company should be active")
    is_default = models.BooleanField(default=False, help_text="Default provider for this company")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("company", "name")]
        ordering = ["-is_default", "-is_active", "name"]

    def __str__(self):
        return f"{self.name} ({self.provider_type}/{self.model_name})"

    @property
    def api_key(self):
        """Decrypt and return the API key."""
        if not self.api_key_encrypted:
            return ""
        try:
            fernet = _get_fernet()
            return fernet.decrypt(self.api_key_encrypted.encode()).decode()
        except Exception:
            return ""

    @api_key.setter
    def api_key(self, value):
        """Encrypt and store the API key."""
        if not value:
            self.api_key_encrypted = ""
        else:
            fernet = _get_fernet()
            self.api_key_encrypted = fernet.encrypt(value.encode()).decode()

    @property
    def has_key(self):
        """Check if an API key is configured."""
        return bool(self.api_key_encrypted)


class LLMUsageLog(models.Model):
    company = models.ForeignKey(
        "accounts.Company", on_delete=models.CASCADE, related_name="llm_usage_logs"
    )
    provider = models.ForeignKey(LLMProvider, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    feature = models.CharField(
        max_length=50,
        choices=[
            ("text_to_sql", "Text-to-SQL"),
            ("ocr", "Invoice OCR"),
            ("insights", "Data Insights"),
            ("chat", "General Chat"),
            ("summarize", "Summarization"),
        ],
        default="chat",
    )
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    duration_ms = models.IntegerField(default=0, help_text="Response time in milliseconds")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.feature} — {self.total_tokens} tokens"


class LLMChatSession(models.Model):
    company = models.ForeignKey(
        "accounts.Company", on_delete=models.CASCADE, related_name="llm_chat_sessions"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True, default="")
    feature = models.CharField(max_length=50, default="chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title or f"Session {self.pk}"


class LLMChatMessage(models.Model):
    session = models.ForeignKey(LLMChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=[("system", "System"), ("user", "User"), ("assistant", "Assistant")])
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True, help_text="Extra data: SQL generated, charts, etc.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:80]}"
