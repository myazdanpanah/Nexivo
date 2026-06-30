import re

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from .encryption import encrypt_value, decrypt_value


class ExternalDatabase(models.Model):
    """Stores connection credentials for external PostgreSQL databases."""

    name = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    port = models.IntegerField(default=5432)
    database = models.CharField(max_length=255)
    _username = models.CharField(max_length=512, db_column="username")
    _password = models.CharField(max_length=512, db_column="password")
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="external_databases",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.host}:{self.port}/{self.database})"

    @property
    def username(self):
        """Decrypt username on read."""
        return decrypt_value(self._username)

    @username.setter
    def username(self, value):
        """Encrypt username on write."""
        self._username = encrypt_value(value)

    @property
    def password(self):
        """Decrypt password on read."""
        return decrypt_value(self._password)

    @password.setter
    def password(self, value):
        """Encrypt password on write."""
        self._password = encrypt_value(value)

    def get_connection_params(self):
        """Return psycopg2 connection parameters dict."""
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.username,
            "password": self.password,
        }


class DatabasePermission(models.Model):
    """Grants updater-role users access to specific tables."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="db_permissions",
    )
    database_source = models.CharField(
        max_length=100,
        help_text="'local' for Nexivo DB or 'external_<id>' for external DBs",
    )
    table_name = models.CharField(
        max_length=255,
        help_text="Table name or '*' for all tables",
    )
    can_edit = models.BooleanField(default=True)
    can_schema = models.BooleanField(default=False)
    can_import = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user", "database_source", "table_name"]
        unique_together = ["user", "database_source", "table_name"]

    def __str__(self):
        return f"{self.user.username} → {self.database_source}/{self.table_name}"

    def clean(self):
        if self.database_source != "local" and not self.database_source.startswith("external_"):
            raise ValidationError(
                "database_source must be 'local' or 'external_<id>'"
            )


class GoogleSheetsSync(models.Model):
    """Google Sheets scheduled sync configuration."""

    SYNC_MODE_CHOICES = [
        ("replace", "Replace"),
        ("upsert", "Upsert"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("error", "Error"),
    ]

    name = models.CharField(max_length=255)
    spreadsheet_id = models.CharField(max_length=100)
    sheet_name = models.CharField(max_length=255)
    database_source = models.CharField(max_length=100)
    table_name = models.CharField(max_length=255)
    sync_mode = models.CharField(max_length=20, choices=SYNC_MODE_CHOICES, default="replace")
    key_column = models.CharField(max_length=255, blank=True, default="")
    schedule = models.CharField(
        max_length=100,
        help_text="Celery cron expression, e.g. '0 */6 * * *'",
    )
    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    last_error = models.TextField(blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sheets_syncs",
    )
    _credentials_json = models.JSONField(
        default=dict,
        blank=True,
        db_column="credentials_json",
        help_text="Google Service Account credentials (JSON, Fernet-encrypted)",
    )

    @property
    def credentials_json(self):
        """Decrypt credentials on read."""
        val = self._credentials_json
        if isinstance(val, dict) and val.get("_encrypted"):
            try:
                return {k: decrypt_value(v) if isinstance(v, str) else v
                        for k, v in val.items() if k != "_encrypted"}
            except Exception:
                return val
        return val

    @credentials_json.setter
    def credentials_json(self, value):
        """Encrypt credentials on write."""
        if isinstance(value, dict) and value:
            encrypted = {k: encrypt_value(v) if isinstance(v, str) else v
                         for k, v in value.items()}
            encrypted["_encrypted"] = True
            self._credentials_json = encrypted
        else:
            self._credentials_json = value
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} → {self.database_source}/{self.table_name}"
