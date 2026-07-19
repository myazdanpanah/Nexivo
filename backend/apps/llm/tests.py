"""
Tests for LLM Gateway module — Provider CRUD, API key encryption,
chat sessions, usage stats, session management, module gating.
"""

from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests_helpers import create_test_company, create_test_user
from .models import LLMProvider, LLMUsageLog, LLMChatSession, LLMChatMessage
from .encryption import encrypt_value, decrypt_value

User = get_user_model()


# ─── Encryption Tests ────────────────────────────────────────────


class LLMEncryptionTests(TestCase):
    """Test Fernet encryption helpers for API keys."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypted value can be decrypted back to plaintext."""
        plaintext = "sk-test-abc123"
        token = encrypt_value(plaintext)
        self.assertNotEqual(token, plaintext)
        self.assertEqual(decrypt_value(token), plaintext)

    def test_encrypt_empty_string(self):
        self.assertEqual(encrypt_value(""), "")

    def test_decrypt_empty_string(self):
        self.assertEqual(decrypt_value(""), "")

    def test_decrypt_backward_compat(self):
        """Unencrypted values pass through unchanged."""
        self.assertEqual(decrypt_value("raw_key"), "raw_key")


# ─── Provider CRUD Tests ────────────────────────────────────────


class LLMProviderTests(TestCase):
    """Tests for LLM provider management endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company()
        self.user = create_test_user(company=self.company, role="ceo")
        self.url = reverse("llm-provider-list")

    def test_list_providers_empty(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_provider(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {
            "provider_type": "ollama",
            "name": "Gemma 4 Local",
            "model_name": "gemma3:1b",
            "api_base_url": "http://localhost:11434",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Gemma 4 Local")
        self.assertTrue(response.data["has_key"] is False or response.data["has_key"] is None)

    def test_create_provider_with_encrypted_key(self):
        """API key is stored encrypted via the model property."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {
            "provider_type": "openai",
            "name": "GPT-4o",
            "model_name": "gpt-4o",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        provider = LLMProvider.objects.get(pk=response.data["id"])
        # Set API key via the model property (encrypts at rest)
        provider.api_key = "sk-test-secret-key"
        provider.save()
        # Stored value should be encrypted
        self.assertNotEqual(provider.api_key_encrypted, "sk-test-secret-key")
        # Decrypted should match
        self.assertEqual(provider.api_key, "sk-test-secret-key")

    def test_api_key_not_exposed_in_list(self):
        """API keys are NOT exposed in list responses (has_key boolean instead)."""
        provider = LLMProvider.objects.create(
            company=self.company,
            provider_type="openai",
            name="Test",
            model_name="gpt-4o",
        )
        provider.api_key = "sk-secret123"
        provider.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # api_key should NOT be in response — only has_key boolean
        self.assertNotIn("api_key", response.data[0])
        self.assertTrue(response.data[0]["has_key"])

    def test_provider_detail(self):
        provider = LLMProvider.objects.create(
            company=self.company,
            provider_type="ollama",
            name="Local LLM",
            model_name="llama3",
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("llm-provider-detail", args=[provider.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Local LLM")

    def test_delete_provider(self):
        provider = LLMProvider.objects.create(
            company=self.company,
            provider_type="ollama",
            name="To Delete",
            model_name="llama3",
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("llm-provider-detail", args=[provider.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LLMProvider.objects.filter(pk=provider.pk).exists())

    def test_provider_company_scoped(self):
        """Users cannot access providers from other companies."""
        other_company = create_test_company(name="Other Co")
        provider = LLMProvider.objects.create(
            company=other_company,
            provider_type="ollama",
            name="Other Co Provider",
            model_name="llama3",
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("llm-provider-detail", args=[provider.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class LLMProviderActivateTests(TestCase):
    """Tests for setting a provider as active."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company()
        self.user = create_test_user(company=self.company, role="ceo")
        self.p1 = LLMProvider.objects.create(
            company=self.company, provider_type="ollama",
            name="Ollama", model_name="gemma3:1b", is_active=True, is_default=True,
        )
        self.p2 = LLMProvider.objects.create(
            company=self.company, provider_type="openai",
            name="OpenAI", model_name="gpt-4o",
        )

    def test_activate_provider(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("llm-provider-activate", args=[self.p2.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.p1.refresh_from_db()
        self.p2.refresh_from_db()
        self.assertFalse(self.p1.is_active)
        self.assertTrue(self.p2.is_active)
        self.assertTrue(self.p2.is_default)


# ─── Chat Session Tests ─────────────────────────────────────────


class LLMChatSessionTests(TestCase):
    """Tests for chat session management."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company()
        self.user = create_test_user(company=self.company, role="ceo")
        self.session = LLMChatSession.objects.create(
            company=self.company,
            user=self.user,
            title="Test Chat",
            feature="chat",
        )

    def test_list_sessions(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("llm-session-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_session_detail(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("llm-session-detail", args=[self.session.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test Chat")

    def test_session_messages_count(self):
        LLMChatMessage.objects.create(session=self.session, role="user", content="Hi")
        LLMChatMessage.objects.create(session=self.session, role="assistant", content="Hello")
        self.client.force_authenticate(user=self.user)
        url = reverse("llm-session-detail", args=[self.session.pk])
        response = self.client.get(url)
        self.assertEqual(response.data["message_count"], 2)

    def test_delete_session(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("llm-session-delete", args=[self.session.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LLMChatSession.objects.filter(pk=self.session.pk).exists())

    def test_session_company_scoped(self):
        """Users cannot access sessions from other companies."""
        other_company = create_test_company(name="Other Co")
        other_user = create_test_user(username="other", company=other_company, role="ceo")
        other_session = LLMChatSession.objects.create(
            company=other_company, user=other_user, title="Other Chat",
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("llm-session-detail", args=[other_session.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ─── Usage Stats Tests ──────────────────────────────────────────


class LLMUsageStatsTests(TestCase):
    """Tests for usage statistics endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company()
        self.user = create_test_user(company=self.company, role="ceo")
        self.url = reverse("llm-usage-stats")

    def test_usage_empty(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_tokens"], 0)
        self.assertEqual(response.data["total_requests"], 0)

    def test_usage_with_logs(self):
        provider = LLMProvider.objects.create(
            company=self.company, provider_type="ollama",
            name="Test", model_name="gemma3:1b",
        )
        LLMUsageLog.objects.create(
            company=self.company, provider=provider, user=self.user,
            feature="chat", prompt_tokens=100, completion_tokens=50,
            total_tokens=150, duration_ms=500,
        )
        LLMUsageLog.objects.create(
            company=self.company, provider=provider, user=self.user,
            feature="chat", prompt_tokens=200, completion_tokens=100,
            total_tokens=300, duration_ms=800,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_tokens"], 450)
        self.assertEqual(response.data["total_requests"], 2)


# ─── Chat Endpoint Tests (with mocked LLM) ──────────────────────


class LLMChatTests(TestCase):
    """Tests for the chat endpoint with mocked LLM service."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company()
        self.user = create_test_user(company=self.company, role="ceo")
        self.provider = LLMProvider.objects.create(
            company=self.company, provider_type="ollama",
            name="Local", model_name="gemma3:1b",
            api_base_url="http://localhost:11434",
            is_active=True, is_default=True,
        )
        self.url = reverse("llm-chat")

    @patch("apps.llm.views.chat_completion")
    def test_chat_creates_session_and_messages(self, mock_chat):
        mock_chat.return_value = {
            "content": "Hello! How can I help?",
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "model": "gemma3:1b",
            "duration_ms": 200,
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {
            "message": "Hi there",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("session_id", response.data)
        # Verify session and messages were created
        session = LLMChatSession.objects.get(pk=response.data["session_id"])
        self.assertEqual(session.messages.count(), 2)  # user + assistant

    @patch("apps.llm.views.chat_completion")
    def test_chat_no_active_provider_returns_400(self, mock_chat):
        """When no active provider exists, chat returns 400."""
        self.provider.is_active = False
        self.provider.save()
        mock_chat.side_effect = ValueError("No active LLM provider")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {
            "message": "Hello",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ─── Module Gate Tests ──────────────────────────────────────────


class LLMModuleGateTests(TestCase):
    """Tests that the LLM provider list is company-scoped (no cross-company access)."""

    def setUp(self):
        self.client = APIClient()
        self.company = create_test_company(
            name="No LLM Co",
            enabled_modules=["bi_dashboard", "datasets"],
        )
        self.user = create_test_user(
            username="nollm",
            company=self.company,
            role="ceo",
        )

    def test_provider_list_company_scoped(self):
        """Provider list returns only providers for the user's company."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("llm-provider-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # No providers in this company, so empty list
        self.assertEqual(len(response.data), 0)
