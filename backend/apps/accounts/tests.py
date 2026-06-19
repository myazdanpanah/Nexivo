"""
Tests for login, register, and JWT authentication endpoints.
"""

import jwt
from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class LoginViewTests(TestCase):
    """Tests for the login endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("login")
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            role="finance",
            department="Finance",
        )

    def test_login_success(self):
        """Valid credentials return a JWT token and user data."""
        response = self.client.post(
            self.url,
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "testuser")
        self.assertEqual(response.data["user"]["role"], "finance")

    def test_login_wrong_password(self):
        """Wrong password returns 401."""
        response = self.client.post(
            self.url,
            {"username": "testuser", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_login_nonexistent_user(self):
        """Non-existent username returns 401."""
        response = self.client.post(
            self.url,
            {"username": "nobody", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_fields(self):
        """Missing username or password returns 400."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_password(self):
        """Missing password returns 400."""
        response = self.client.post(
            self.url, {"username": "testuser"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user(self):
        """Inactive user cannot log in."""
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            self.url,
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_returns_valid_jwt(self):
        """The returned JWT can be decoded and contains correct claims."""
        response = self.client.post(
            self.url,
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        token = response.data["token"]
        from django.conf import settings

        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        self.assertEqual(payload["user_id"], self.user.id)
        self.assertEqual(payload["username"], "testuser")
        self.assertEqual(payload["role"], "finance")
        self.assertIn("exp", payload)
        self.assertIn("iat", payload)


class RegisterViewTests(TestCase):
    """Tests for the register endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("register")

    def test_register_success(self):
        """Valid registration returns token and user data."""
        response = self.client.post(
            self.url,
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "securepass123",
                "role": "sales",
                "department": "Sales",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "newuser")
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_duplicate_username(self):
        """Duplicate username returns 400."""
        User.objects.create_user(
            username="existing", password="pass12345", role="sales"
        )
        response = self.client.post(
            self.url,
            {
                "username": "existing",
                "email": "new@example.com",
                "password": "securepass123",
                "role": "sales",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password(self):
        """Password shorter than 8 chars returns 400."""
        response = self.client.post(
            self.url,
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "short",
                "role": "sales",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        """Missing required fields returns 400."""
        response = self.client.post(
            self.url, {"username": "newuser"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JWTAuthenticationTests(TestCase):
    """Tests for the JWT authentication middleware."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            role="ceo",
        )
        self.profile_url = reverse("profile")

    def _get_token(self):
        """Helper to get a valid JWT token."""
        from apps.accounts.authentication import JWTAuthentication

        return JWTAuthentication.generate_token(self.user)

    def test_authenticated_request(self):
        """Valid token allows access to protected endpoints."""
        token = self._get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

    def test_no_token_returns_401_or_403(self):
        """Missing token returns 401 or 403 (DRF default)."""
        response = self.client.get(self.profile_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_invalid_token_returns_401_or_403(self):
        """Invalid token returns 401 or 403."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.here")
        response = self.client.get(self.profile_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_expired_token_returns_401_or_403(self):
        """Expired token returns 401 or 403."""
        from django.conf import settings

        payload = {
            "user_id": self.user.id,
            "username": self.user.username,
            "role": self.user.role,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        expired_token = jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {expired_token}")
        response = self.client.get(self.profile_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_disabled_user_token_rejected(self):
        """Token for a disabled user is rejected."""
        self.user.is_active = False
        self.user.save()
        token = self._get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(self.profile_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_malformed_auth_header(self):
        """Malformed Authorization header is rejected."""
        self.client.credentials(HTTP_AUTHORIZATION="Token somevalue")
        response = self.client.get(self.profile_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
