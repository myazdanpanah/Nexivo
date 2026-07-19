"""
LLM API Key Encryption — Fernet symmetric encryption using Django SECRET_KEY.
"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings


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


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string. Returns empty string for empty input."""
    if not plaintext:
        return ""
    fernet = _get_fernet()
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt_value(token: str) -> str:
    """Decrypt an encrypted string. Returns the raw value for non-encrypted input."""
    if not token:
        return ""
    try:
        fernet = _get_fernet()
        return fernet.decrypt(token.encode()).decode()
    except Exception:
        return token
