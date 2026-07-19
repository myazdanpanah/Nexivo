"""
Tests for dataset_query endpoint - SQL injection prevention and column validation.
"""

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Company
from .models import Dataset, DataFilter

User = get_user_model()


class DatasetQueryTests(TestCase):
    """Tests for the dataset_query endpoint's SQL injection protection."""

    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(
            name="Test Company",
            enabled_modules=["bi_dashboard", "finance", "crm", "db_manager", "datasets", "llm", "settings"],
        )
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", role="finance", company=self.company
        )
        self.ceo_user = User.objects.create_user(
            username="ceouser", password="testpass123", role="ceo", company=self.company
        )

        # Create a test table in PostgreSQL
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_query_data (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    amount DOUBLE PRECISION,
                    region TEXT
                )
            """)
            cursor.execute(
                "INSERT INTO test_query_data (name, amount, region) VALUES (%s, %s, %s)",
                ["Alice", 100.0, "North"],
            )
            cursor.execute(
                "INSERT INTO test_query_data (name, amount, region) VALUES (%s, %s, %s)",
                ["Bob", 200.0, "South"],
            )

        self.dataset = Dataset.objects.create(
            name="Test Data",
            table_name="test_query_data",
            status="ready",
            column_names=["id", "name", "amount", "region"],
            column_types={"id": "BIGINT", "name": "TEXT", "amount": "DOUBLE PRECISION", "region": "TEXT"},
            allowed_roles=["finance", "ceo"],
            owner=self.user,
        )
        self.query_url = reverse("dataset-query", args=[self.dataset.pk])

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS test_query_data")

    def test_query_valid_columns(self):
        """Querying valid columns returns correct data."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {"columns": ["name", "amount"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["row_count"], 2)
        self.assertIn("name", response.data["columns"])
        self.assertIn("amount", response.data["columns"])

    def test_query_all_columns_default(self):
        """Querying without specifying columns returns all dataset columns."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.query_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["row_count"], 2)

    def test_sql_injection_via_column_name(self):
        """SQL injection attempt via column name is rejected."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {"columns": ["id; DROP TABLE test_query_data; --"]},
            format="json",
        )
        # Should return 400 because the injected column name is not in valid columns
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No valid columns requested", response.data["error"])

        # Verify the table still exists (not dropped)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='test_query_data')"
            )
            self.assertTrue(cursor.fetchone()[0])

    def test_sql_injection_via_filter_column(self):
        """SQL injection attempt via filter column name is rejected."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["name"],
                "filters": [
                    {"col": "1=1; DROP TABLE test_query_data; --", "op": "eq", "val": "x"}
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid filter column", response.data["error"])

    def test_mixed_valid_and_invalid_columns(self):
        """Mix of valid and invalid columns: only valid ones are queried."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {"columns": ["name", "nonexistent_col", "amount"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("name", response.data["columns"])
        self.assertIn("amount", response.data["columns"])
        self.assertNotIn("nonexistent_col", response.data["columns"])

    def test_all_invalid_columns_returns_400(self):
        """When all requested columns are invalid, return 400."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {"columns": ["fake1", "fake2"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_eq_filter_works(self):
        """Equality filter correctly filters data."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["name", "region"],
                "filters": [{"col": "region", "op": "eq", "val": "North"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["row_count"], 1)
        self.assertEqual(response.data["data"][0]["region"], "North")

    def test_in_filter_works(self):
        """IN filter correctly filters data."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["name"],
                "filters": [
                    {"col": "region", "op": "in", "val": ["North", "East"]}
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["row_count"], 1)

    def test_contains_filter_works(self):
        """Contains filter correctly filters data."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {
                "columns": ["name"],
                "filters": [{"col": "name", "op": "contains", "val": "li"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["row_count"], 1)
        self.assertEqual(response.data["data"][0]["name"], "Alice")

    def test_role_based_filters_applied(self):
        """DataFilter records are automatically applied for the user's role."""
        DataFilter.objects.create(
            dataset=self.dataset,
            role="finance",
            column_name="region",
            operator="eq",
            value="North",
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.query_url,
            {"columns": ["name", "region"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["row_count"], 1)
        self.assertEqual(response.data["data"][0]["region"], "North")
        self.assertTrue(
            any("region" in f for f in response.data["filters_applied"]) or 
            any("region" in str(f) for f in response.data["filters_applied"]),
            f"Expected 'region' in filters_applied, got {response.data['filters_applied']}"
        )

    def test_nonexistent_dataset_returns_404(self):
        """Querying a non-existent dataset returns 404."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("dataset-query", args=[99999]),
            {"columns": ["name"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_ceo_user_sees_all_data(self):
        """CEO user can query any dataset without role-based filters."""
        self.client.force_authenticate(user=self.ceo_user)
        response = self.client.post(
            self.query_url,
            {"columns": ["name"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["row_count"], 2)
