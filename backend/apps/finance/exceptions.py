"""
Finance Module Exceptions — Shared business exceptions.

Per API_SPECIFICATION.md §8: Business exceptions return 422 (Unprocessable Entity).
Per DJANGO_BACKEND.md §27: Exception Architecture — all exceptions inherit from ERPException.

This module exists to break the circular import between services.py and validators.py.
Both modules import ValidationError from here.
"""


class ValidationError(Exception):
    """Business validation error — returned as 422 to the client.

    Per API_SPECIFICATION.md §8:
    - 422 = Business Rule Violation
    """
    def __init__(self, message: str, code: str = "validation_error"):
        self.message = message
        self.code = code
        super().__init__(message)
