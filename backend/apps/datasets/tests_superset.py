"""
Tests for Superset health check and sync endpoints.
"""

from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Company
from .models import Dataset, DataFilter

User = get_user_model()


class SupersetHealthTests(TestCase):
    """Tests for the superset_health endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(
            name="Test Company",
            enabled_modules=["bi_dashboard", "finance", "crm", "db_manager", "datasets", "llm", "settings"],
        )
        self.admin = User.objects.create_user(
            username="admin", password="testpass123", role="admin", is_staff=True, company=self.company
        )
        self.ceo = User.objects.create_user(
            username="ceo", password="testpass123", role="ceo", company=self.company
        )
        self.regular = User.objects.create_user(
            username="regular", password="testpass123", role="sales", company=self.company
        )
        self.dataset = Dataset.objects.create(
            name="Test DS",
            table_name="test_table",
            status="ready",
            column_names=["col1"],
            allowed_roles=["ceo"],
            owner=self.admin,
        )
        self.url = reverse("superset-health")

    def test_admin_can_access(self):
        """Admin users can access the health endpoint."""
        self.client.force_authenticate(user=self.admin)
        with patch("apps.datasets.superset.superset_client") as mock_client:
            mock_client.get_datasets.return_value = [
                {"table_name": "test_table", "id": 42}
            ]
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "ok")

    def test_ceo_can_access(self):
        """CEO users can access the health endpoint."""
        self.client.force_authenticate(user=self.ceo)
        with patch("apps.datasets.superset.superset_client") as mock_client:
            mock_client.get_datasets.return_value = []
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_denied(self):
        """Regular users get 403."""
        self.client.force_authenticate(user=self.regular)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_health_reports_sync_status(self):
        """Health endpoint correctly reports which datasets are synced."""
        self.client.force_authenticate(user=self.admin)
        with patch("apps.datasets.superset.superset_client") as mock_client:
            mock_client.get_datasets.return_value = [
                {"table_name": "test_table", "id": 42}
            ]
            response = self.client.get(self.url)
            self.assertEqual(response.data["status"], "ok")
            self.assertEqual(len(response.data["datasets"]), 1)
            ds = response.data["datasets"][0]
            # synced = remote_id is not None (Superset has this table)
            self.assertTrue(ds["synced"])
            self.assertEqual(ds["remote_superset_id"], 42)
            # local superset_dataset_id is still None (not yet synced locally)
            self.assertIsNone(ds["superset_dataset_id"])

    def test_health_handles_superset_down(self):
        """When Superset is unreachable, status is 'error'."""
        self.client.force_authenticate(user=self.admin)
        with patch("apps.datasets.superset.superset_client") as mock_client:
            mock_client.get_datasets.side_effect = ConnectionError("refused")
            response = self.client.get(self.url)
            self.assertEqual(response.data["status"], "error")
            self.assertIn("error", response.data)


class SupersetSyncDatasetTests(TestCase):
    """Tests for the superset_sync_dataset endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(
            name="Test Company",
            enabled_modules=["bi_dashboard", "finance", "crm", "db_manager", "datasets", "llm", "settings"],
        )
        self.admin = User.objects.create_user(
            username="admin", password="testpass123", role="admin", is_staff=True, company=self.company
        )
        self.regular = User.objects.create_user(
            username="regular", password="testpass123", role="sales", company=self.company
        )
        self.dataset = Dataset.objects.create(
            name="Test DS",
            table_name="test_table",
            status="ready",
            column_names=["col1"],
            allowed_roles=["ceo"],
            owner=self.admin,
        )
        self.url = reverse("superset-sync-dataset", args=[self.dataset.pk])

    def test_sync_unsynced_dataset(self):
        """Syncing an unsynced dataset registers it in Superset."""
        self.client.force_authenticate(user=self.admin)
        with patch("apps.datasets.superset.superset_client") as mock_client:
            mock_client.register_dataset.return_value = 99
            response = self.client.post(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], "synced")
            self.assertEqual(response.data["superset_dataset_id"], 99)
            self.dataset.refresh_from_db()
            self.assertEqual(self.dataset.superset_dataset_id, 99)

    def test_sync_already_synced(self):
        """Syncing an already-synced dataset returns 'already_synced'."""
        self.dataset.superset_dataset_id = 42
        self.dataset.save()
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "already_synced")

    def test_regular_user_denied(self):
        """Regular users cannot sync."""
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_dataset_returns_404(self):
        """Syncing a non-existent dataset returns 404."""
        self.client.force_authenticate(user=self.admin)
        url = reverse("superset-sync-dataset", args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_superset_failure_returns_502(self):
        """When Superset rejects the registration, return 502."""
        self.client.force_authenticate(user=self.admin)
        with patch("apps.datasets.superset.superset_client") as mock_client:
            mock_client.register_dataset.side_effect = Exception("Superset rejected")
            response = self.client.post(self.url)
            self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)


class SupersetSyncAllTests(TestCase):
    """Tests for the superset_sync_all bulk endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(
            name="Test Company",
            enabled_modules=["bi_dashboard", "finance", "crm", "db_manager", "datasets", "llm", "settings"],
        )
        self.admin = User.objects.create_user(
            username="admin", password="testpass123", role="admin", is_staff=True, company=self.company
        )
        self.url = reverse("superset-sync-all")
        self.ds1 = Dataset.objects.create(
            name="DS1", table_name="t1", status="ready", column_names=[], owner=self.admin
        )
        self.ds2 = Dataset.objects.create(
            name="DS2", table_name="t2", status="ready", column_names=[], owner=self.admin
        )
        # Already synced
        self.ds3 = Dataset.objects.create(
            name="DS3", table_name="t3", status="ready", column_names=[],
            superset_dataset_id=10, owner=self.admin
        )

    def test_bulk_sync_registers_unsynced(self):
        """Bulk sync registers all unsynced datasets."""
        self.client.force_authenticate(user=self.admin)
        with patch("apps.datasets.superset.superset_client") as mock_client:
            mock_client.register_dataset.side_effect = [101, 102]
            response = self.client.post(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["synced"], 2)
            self.ds1.refresh_from_db()
            self.ds2.refresh_from_db()
            # Default ordering is -created_at, so ds2 (newer) iterates before ds1
            self.assertIn(self.ds1.superset_dataset_id, [101, 102])
            self.assertIn(self.ds2.superset_dataset_id, [101, 102])
            self.assertNotEqual(self.ds1.superset_dataset_id, self.ds2.superset_dataset_id)

    def test_bulk_sync_skips_already_synced(self):
        """Already-synced datasets are NOT re-registered."""
        self.client.force_authenticate(user=self.admin)
        with patch("apps.datasets.superset.superset_client") as mock_client:
            mock_client.register_dataset.side_effect = [101, 102]
            response = self.client.post(self.url)
            # ds3 already has superset_dataset_id=10, so register_dataset is called
            # only for ds1 and ds2 (2 calls, not 3)
            self.assertEqual(mock_client.register_dataset.call_count, 2)
            # After sync, all 3 are now synced
            self.assertEqual(response.data["synced"], 2)
            self.assertEqual(response.data["skipped"], 3)

    def test_bulk_sync_handles_partial_failure(self):
        """If one dataset fails, others still sync."""
        self.client.force_authenticate(user=self.admin)
        with patch("apps.datasets.superset.superset_client") as mock_client:
            mock_client.register_dataset.side_effect = [101, Exception("bad table")]
            response = self.client.post(self.url)
            self.assertEqual(response.data["synced"], 1)
            self.assertEqual(len(response.data["errors"]), 1)
            # Default ordering is -created_at, so ds2 fails (second in iteration)
            self.assertIn(response.data["errors"][0]["name"], ["DS1", "DS2"])


class DataFilterSyncTests(TestCase):
    """Tests for DataFilter.save() auto-sync to Superset RLS."""

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            enabled_modules=["bi_dashboard", "finance", "crm", "db_manager", "datasets", "llm", "settings"],
        )
        self.admin = User.objects.create_user(
            username="admin", password="testpass123", role="admin", is_staff=True, company=self.company
        )
        self.dataset = Dataset.objects.create(
            name="Test DS", table_name="test_table", status="ready",
            column_names=["region", "amount"], superset_dataset_id=42, owner=self.admin,
        )
        self.unsynced_dataset = Dataset.objects.create(
            name="Unsynced DS", table_name="unsynced_table", status="ready",
            column_names=["region"], superset_dataset_id=None, owner=self.admin,
        )

    def test_save_triggers_rls_sync_when_synced(self):
        """Saving a DataFilter on a synced dataset calls sync_rls."""
        with patch("apps.datasets.superset.superset_client") as mock_client:
            f = DataFilter(
                dataset=self.dataset, role="sales", column_name="region",
                operator="eq", value="north",
            )
            f.save()
            mock_client.sync_rls.assert_called_once_with(
                42, [{"clause": "region = 'north'"}],
            )

    def test_save_skips_sync_when_not_synced(self):
        """Saving a DataFilter on an unsynced dataset skips sync."""
        with patch("apps.datasets.superset.superset_client") as mock_client:
            f = DataFilter(
                dataset=self.unsynced_dataset, role="sales", column_name="region",
                operator="eq", value="south",
            )
            f.save()
            mock_client.sync_rls.assert_not_called()

    def test_save_syncs_multiple_active_filters(self):
        """sync_to_superset collects all active filters for the dataset."""
        DataFilter.objects.create(
            dataset=self.dataset, role="sales", column_name="region",
            operator="eq", value="north", is_active=True,
        )
        DataFilter.objects.create(
            dataset=self.dataset, role="finance", column_name="amount",
            operator="gt", value=1000, is_active=True,
        )
        DataFilter.objects.create(
            dataset=self.dataset, role="sales", column_name="old_col",
            operator="eq", value="x", is_active=False,  # inactive — should be excluded
        )
        with patch("apps.datasets.superset.superset_client") as mock_client:
            f = DataFilter(
                dataset=self.dataset, role="ceo", column_name="region",
                operator="in", value=["east", "west"],
            )
            f.save()
            mock_client.sync_rls.assert_called_once()
            rls_rules = mock_client.sync_rls.call_args[0][1]
            # Should have 3 active filters (2 existing + 1 new)
            self.assertEqual(len(rls_rules), 3)
            clauses = [r["clause"] for r in rls_rules]
            self.assertIn("region = 'north'", clauses)
            self.assertIn("amount > '1000'", clauses)
            self.assertIn("region IN ('east', 'west')", clauses)

    def test_save_gracefully_handles_superset_error(self):
        """If sync_rls raises, save() still succeeds."""
        with patch("apps.datasets.superset.superset_client") as mock_client:
            mock_client.sync_rls.side_effect = ConnectionError("refused")
            f = DataFilter(
                dataset=self.dataset, role="sales", column_name="region",
                operator="eq", value="north",
            )
            # Should not raise
            f.save()
            self.assertIsNotNone(f.pk)

    def test_build_rls_clause_eq(self):
        """_build_rls_clause for eq operator."""
        f = DataFilter(
            dataset=self.dataset, role="sales", column_name="col",
            operator="eq", value="A",
        )
        self.assertEqual(f._build_rls_clause(), "col = 'A'")

    def test_build_rls_clause_in(self):
        """_build_rls_clause for in operator."""
        f = DataFilter(
            dataset=self.dataset, role="sales", column_name="col",
            operator="in", value=["A", "B", "C"],
        )
        self.assertEqual(f._build_rls_clause(), "col IN ('A', 'B', 'C')")

    def test_build_rls_clause_contains(self):
        """_build_rls_clause for contains operator."""
        f = DataFilter(
            dataset=self.dataset, role="sales", column_name="col",
            operator="contains", value="test",
        )
        self.assertEqual(f._build_rls_clause(), "col ILIKE '%test%'")

    def test_build_rls_clause_gt(self):
        """_build_rls_clause for gt operator."""
        f = DataFilter(
            dataset=self.dataset, role="sales", column_name="col",
            operator="gt", value=100,
        )
        self.assertEqual(f._build_rls_clause(), "col > '100'")
