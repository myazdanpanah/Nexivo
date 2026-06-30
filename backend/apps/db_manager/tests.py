"""
Tests for Database Manager module — permissions, CRUD, encryption, file import.
"""

import io
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import ExternalDatabase, DatabasePermission, GoogleSheetsSync
from .encryption import encrypt_value, decrypt_value

User = get_user_model()


class EncryptionTests(TestCase):
    """Test Fernet encryption helpers."""

    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "super_secret_password_123"
        token = encrypt_value(plaintext)
        self.assertNotEqual(token, plaintext)
        self.assertEqual(decrypt_value(token), plaintext)

    def test_encrypt_empty_string(self):
        self.assertEqual(encrypt_value(""), "")

    def test_decrypt_empty_string(self):
        self.assertEqual(decrypt_value(""), "")

    def test_decrypt_backward_compat(self):
        """Unencrypted values should pass through unchanged."""
        self.assertEqual(decrypt_value("raw_password"), "raw_password")


class ExternalDatabaseModelTests(TestCase):
    """Test ExternalDatabase model encryption properties."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="admin1", password="pass123", role="admin"
        )

    def test_username_password_encrypted_at_rest(self):
        db = ExternalDatabase.objects.create(
            name="Test DB",
            host="localhost",
            port=5432,
            database="testdb",
            owner=self.user,
        )
        db.username = "my_user"
        db.password = "my_pass"
        db.save()

        # Raw DB value should be encrypted
        raw = ExternalDatabase.objects.get(pk=db.pk)
        self.assertNotEqual(raw._username, "my_user")
        self.assertNotEqual(raw._password, "my_pass")

        # Property should decrypt
        self.assertEqual(raw.username, "my_user")
        self.assertEqual(raw.password, "my_pass")

    def test_get_connection_params(self):
        db = ExternalDatabase.objects.create(
            name="Test DB",
            host="db.example.com",
            port=5433,
            database="mydb",
            owner=self.user,
        )
        db.username = "admin"
        db.password = "secret"
        db.save()

        params = db.get_connection_params()
        self.assertEqual(params["host"], "db.example.com")
        self.assertEqual(params["port"], 5433)
        self.assertEqual(params["dbname"], "mydb")
        self.assertEqual(params["user"], "admin")
        self.assertEqual(params["password"], "secret")


class DatabasePermissionTests(TestCase):
    """Test DatabasePermission model."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin1", password="pass123", role="admin"
        )
        self.updater = User.objects.create_user(
            username="updater1", password="pass123", role="updater"
        )

    def test_create_permission(self):
        perm = DatabasePermission.objects.create(
            user=self.updater,
            database_source="local",
            table_name="sales_data",
            can_edit=True,
        )
        self.assertTrue(perm.can_edit)
        self.assertEqual(perm.table_name, "sales_data")

    def test_wildcard_permission(self):
        perm = DatabasePermission.objects.create(
            user=self.updater,
            database_source="local",
            table_name="*",
            can_edit=True,
        )
        self.assertEqual(perm.table_name, "*")


class TableOperationsTests(TestCase):
    """Test table listing, schema, data browsing."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin1", password="pass123", role="admin"
        )
        self.regular = User.objects.create_user(
            username="regular1", password="pass123", role="finance"
        )

        # Create a test table
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dbm_test_table (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    value DOUBLE PRECISION
                )
            """)
            cursor.execute(
                "INSERT INTO dbm_test_table (name, value) VALUES (%s, %s)",
                ["Alice", 100.0],
            )
            cursor.execute(
                "INSERT INTO dbm_test_table (name, value) VALUES (%s, %s)",
                ["Bob", 200.0],
            )

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS dbm_test_table")

    def test_table_list_local(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("table-list", args=["local"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # table_list returns a list of table name strings
        self.assertIsInstance(response.data, list)
        self.assertIn("dbm_test_table", response.data)

    def test_table_schema(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            reverse("table-schema", args=["local", "dbm_test_table"])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        col_names = [c["name"] for c in response.data]
        self.assertIn("id", col_names)
        self.assertIn("name", col_names)
        self.assertIn("value", col_names)

    def test_table_data(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            reverse("table-data", args=["local", "dbm_test_table"])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # table_data returns columns, rows, total_count, offset, limit
        self.assertIn("columns", response.data)
        self.assertIn("rows", response.data)
        self.assertEqual(len(response.data["rows"]), 2)

    def test_table_count(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            reverse("table-count", args=["local", "dbm_test_table"])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)


class CellEditingTests(TestCase):
    """Test cell update, batch update, row insert, row delete."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin1", password="pass123", role="admin"
        )
        self.regular = User.objects.create_user(
            username="regular1", password="pass123", role="finance"
        )

        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dbm_cell_test (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    amount DOUBLE PRECISION
                )
            """)
            cursor.execute(
                "INSERT INTO dbm_cell_test (name, amount) VALUES (%s, %s)",
                ["Alice", 100.0],
            )

    def tearDown(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS dbm_cell_test")

    def test_cell_update_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            reverse("cell-update", args=["local", "dbm_cell_test"]),
            {
                "pk_column": "id",
                "pk_value": 1,
                "column": "name",
                "value": "Alice Updated",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rows_affected"], 1)

    def test_cell_update_regular_user_denied(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.patch(
            reverse("cell-update", args=["local", "dbm_cell_test"]),
            {
                "pk_column": "id",
                "pk_value": 1,
                "column": "name",
                "value": "Hacked",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cell_update_updater_with_permission(self):
        updater = User.objects.create_user(
            username="updater1", password="pass123", role="updater"
        )
        DatabasePermission.objects.create(
            user=updater,
            database_source="local",
            table_name="dbm_cell_test",
            can_edit=True,
        )
        self.client.force_authenticate(user=updater)
        response = self.client.patch(
            reverse("cell-update", args=["local", "dbm_cell_test"]),
            {
                "pk_column": "id",
                "pk_value": 1,
                "column": "amount",
                "value": 999.0,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cell_update_updater_no_permission(self):
        updater = User.objects.create_user(
            username="updater2", password="pass123", role="updater"
        )
        self.client.force_authenticate(user=updater)
        response = self.client.patch(
            reverse("cell-update", args=["local", "dbm_cell_test"]),
            {
                "pk_column": "id",
                "pk_value": 1,
                "column": "name",
                "value": "Hacked",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_row_insert(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("row-insert", args=["local", "dbm_cell_test"]),
            {"name": "Charlie", "amount": 300.0},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_row_delete(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
            reverse("row-delete", args=["local", "dbm_cell_test"]),
            {"pk_column": "id", "pk_values": [1]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rows_affected"], 1)


class PermissionManagementTests(TestCase):
    """Test permission CRUD endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin1", password="pass123", role="admin"
        )
        self.updater = User.objects.create_user(
            username="updater1", password="pass123", role="updater"
        )

    def test_admin_can_create_permission(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("permission-list"),
            {
                "user": self.updater.pk,
                "database_source": "local",
                "table_name": "sales_data",
                "can_edit": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_regular_user_cannot_create_permission(self):
        regular = User.objects.create_user(
            username="regular1", password="pass123", role="finance"
        )
        self.client.force_authenticate(user=regular)
        response = self.client.post(
            reverse("permission-list"),
            {
                "user": self.updater.pk,
                "database_source": "local",
                "table_name": "sales_data",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_permission(self):
        perm = DatabasePermission.objects.create(
            user=self.updater,
            database_source="local",
            table_name="*",
            can_edit=True,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
            reverse("permission-detail", args=[perm.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class SQLExecutorTests(TestCase):
    """Test SQL editor endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin1", password="pass123", role="admin"
        )
        self.regular = User.objects.create_user(
            username="regular1", password="pass123", role="finance"
        )

    def test_admin_can_execute_sql(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("sql-execute"),
            {"source": "local", "sql": "SELECT 1 AS num"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_execute_sql(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            reverse("sql-execute"),
            {"source": "local", "sql": "SELECT 1 AS num"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dangerous_sql_blocked(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("sql-execute"),
            {"source": "local", "sql": "DROP TABLE important_data"},
            format="json",
        )
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
        ])


class GoogleSheetsSyncTests(TestCase):
    """Test sync config CRUD (without actual Google API calls)."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin1", password="pass123", role="admin"
        )

    def test_create_sync_config(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("sync-list"),
            {
                "name": "Sales Sync",
                "spreadsheet_id": "abc123",
                "sheet_name": "Sheet1",
                "database_source": "local",
                "table_name": "synced_data",
                "sync_mode": "replace",
                "schedule": "0 */6 * * *",
                "credentials_json": {"type": "service_account", "project_id": "test"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_syncs(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("sync-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_credentials_not_exposed_in_read(self):
        """credentials_json should NOT appear in the read serializer response."""
        sync = GoogleSheetsSync.objects.create(
            name="Test Sync",
            spreadsheet_id="abc123",
            sheet_name="Sheet1",
            database_source="local",
            table_name="test_table",
            sync_mode="replace",
            schedule="0 */6 * * *",
            owner=self.admin,
        )
        sync.credentials_json = {"type": "service_account", "key": "secret"}
        sync.save()

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("sync-detail", args=[sync.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # credentials_json should NOT be in the response
        self.assertNotIn("credentials_json", response.data)


class DatabaseManagementTests(TestCase):
    """Test external database CRUD."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin1", password="pass123", role="admin"
        )
        self.regular = User.objects.create_user(
            username="regular1", password="pass123", role="finance"
        )

    def test_admin_can_create_database(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("db-list"),
            {
                "name": "Ext DB",
                "host": "db.example.com",
                "port": 5432,
                "database": "mydb",
                "username": "admin",
                "password": "secret",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Password should be masked
        self.assertEqual(response.data["password"], "***")

    def test_regular_user_cannot_create_database(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.post(
            reverse("db-list"),
            {
                "name": "Ext DB",
                "host": "db.example.com",
                "port": 5432,
                "database": "mydb",
                "username": "admin",
                "password": "secret",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_password_masked_in_response(self):
        db = ExternalDatabase.objects.create(
            name="Test DB",
            host="localhost",
            port=5432,
            database="testdb",
            owner=self.admin,
        )
        db.username = "user"
        db.password = "secret_pass"
        db.save()

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("db-detail", args=[db.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["password"], "***")
        self.assertEqual(response.data["username"], "user")

    def test_admin_can_delete_database(self):
        db = ExternalDatabase.objects.create(
            name="To Delete",
            host="localhost",
            port=5432,
            database="testdb",
            owner=self.admin,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(reverse("db-detail", args=[db.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
