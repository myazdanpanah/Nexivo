"""
Tests for the create_dev_data management command.
"""

from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

User = get_user_model()


class CreateDevDataTests(TestCase):
    """Tests for the create_dev_data management command."""

    def _run_command(self, **kwargs):
        out = StringIO()
        call_command("create_dev_data", stdout=out, **kwargs)
        return out.getvalue()

    def test_creates_all_users(self):
        """First run creates all 4 dev users."""
        output = self._run_command()
        self.assertEqual(User.objects.count(), 4)
        self.assertIn("created", output)

    def test_creates_admin_as_superuser(self):
        """Admin user is created as a superuser with is_staff=True."""
        self._run_command()
        admin = User.objects.get(username="admin")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.role, "admin")

    def test_creates_correct_roles(self):
        """Each user gets the correct role."""
        self._run_command()
        self.assertEqual(User.objects.get(username="admin").role, "admin")
        self.assertEqual(User.objects.get(username="ceo").role, "ceo")
        self.assertEqual(User.objects.get(username="finance").role, "finance")
        self.assertEqual(User.objects.get(username="sales").role, "sales")

    def test_idempotent_creates_no_duplicates(self):
        """Running twice doesn't create duplicate users."""
        self._run_command()
        self.assertEqual(User.objects.count(), 4)
        self._run_command()
        self.assertEqual(User.objects.count(), 4)

    def test_idempotent_resets_passwords(self):
        """Running twice still works and passwords are reset each time."""
        self._run_command()
        # Manually change admin password
        admin = User.objects.get(username="admin")
        admin.set_password("hacked_password")
        admin.save()
        self.assertFalse(admin.check_password("admin12345"))

        # Re-run command - should reset password back
        self._run_command()
        admin.refresh_from_db()
        self.assertTrue(admin.check_password("admin12345"))

    def test_idempotent_resets_roles(self):
        """Running twice resets roles that may have been changed."""
        self._run_command()
        # Manually change role
        ceo = User.objects.get(username="ceo")
        ceo.role = "sales"
        ceo.save()

        self._run_command()
        ceo.refresh_from_db()
        self.assertEqual(ceo.role, "ceo")

    def test_output_shows_updated_for_existing_users(self):
        """Second run shows 'updated (password reset)' for existing users."""
        self._run_command()
        output = self._run_command()
        self.assertIn("updated (password reset)", output)

    def test_dev_users_can_authenticate(self):
        """All created dev users can authenticate with their passwords."""
        self._run_command()
        from django.contrib.auth import authenticate

        self.assertIsNotNone(authenticate(username="admin", password="admin12345"))
        self.assertIsNotNone(authenticate(username="ceo", password="ceo123456"))
        self.assertIsNotNone(authenticate(username="finance", password="finance123"))
        self.assertIsNotNone(authenticate(username="sales", password="sales12345"))

    def test_admin_email_set_correctly(self):
        """Admin user has the correct email."""
        self._run_command()
        admin = User.objects.get(username="admin")
        self.assertEqual(admin.email, "admin@nexivo.local")

    def test_output_shows_credentials(self):
        """Output includes login credentials for reference."""
        output = self._run_command()
        self.assertIn("admin   / admin12345", output)
        self.assertIn("ceo     / ceo123456", output)
        self.assertIn("finance / finance123", output)
        self.assertIn("sales   / sales12345", output)
