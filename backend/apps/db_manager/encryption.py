"""Database Manager — Fernet encryption helpers for credentials at rest."""

from cryptography.fernet import Fernet
from django.conf import settings
import base64
import hashlib


def _derive_key(secret_key: str) -> bytes:
    """Derive a Fernet-compatible key from Django's SECRET_KEY."""
    digest = hashlib.sha256(secret_key.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string using Fernet. Returns a token string."""
    if not plaintext:
        return ""
    key = _derive_key(settings.SECRET_KEY)
    f = Fernet(key)
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(token: str) -> str:
    """Decrypt a Fernet token back to plaintext string.
    Falls back to returning the raw value for backward compatibility
    with unencrypted data.
    """
    if not token:
        return ""
    try:
        key = _derive_key(settings.SECRET_KEY)
        f = Fernet(key)
        return f.decrypt(token.encode()).decode()
    except Exception:
        # Backward compatibility: return raw value if not encrypted
        return token
