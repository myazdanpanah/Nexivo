"""
Shared test fixtures for Nexivo test suites.

Provides reusable helpers for creating Company and User objects with
proper module gating setup. Use these in all test files to avoid
duplicating Company.objects.create() blocks.
"""

from django.contrib.auth import get_user_model

from .models import Company, ALL_MODULE_IDS

User = get_user_model()


def create_test_company(name="Test Company", enabled_modules=None, **kwargs):
    """
    Create a Company with all (or specified) modules enabled.

    Args:
        name: Company name (default: "Test Company")
        enabled_modules: List of module slugs. Defaults to ALL_MODULE_IDS.
        **kwargs: Extra fields passed to Company.objects.create()

    Returns:
        Company instance
    """
    if enabled_modules is None:
        enabled_modules = list(ALL_MODULE_IDS)
    return Company.objects.create(
        name=name,
        enabled_modules=enabled_modules,
        **kwargs,
    )


def create_test_user(
    username="testuser",
    password="testpass123",
    role="finance",
    company=None,
    is_staff=False,
    **kwargs,
):
    """
    Create a User assigned to a Company (for module gate testing).

    Args:
        username: Username (default: "testuser")
        password: Password (default: "testpass123")
        role: User role — finance, sales, ceo, admin (default: "finance")
        company: Company instance. If None, creates one via create_test_company().
        is_staff: Whether the user is a Django staff user (bypasses RequireModule).
        **kwargs: Extra fields passed to User.objects.create_user()

    Returns:
        User instance
    """
    if company is None:
        company = create_test_company()
    return User.objects.create_user(
        username=username,
        password=password,
        role=role,
        company=company,
        is_staff=is_staff,
        **kwargs,
    )
