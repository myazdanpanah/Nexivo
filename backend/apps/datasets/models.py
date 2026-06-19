from django.db import models
from django.conf import settings


class Dataset(models.Model):
    """
    Represents an uploaded dataset (e.g., from Excel file).
    The original file is preserved, and a PostgreSQL table is created
    from the data for querying via Superset.
    """

    STATUS_CHOICES = [
        ("uploading", "Uploading"),
        ("processing", "Processing"),
        ("ready", "Ready"),
        ("error", "Error"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    original_file = models.FileField(upload_to="datasets/originals/")
    table_name = models.CharField(
        max_length=100,
        unique=True,
        help_text="PostgreSQL table name created from the uploaded data",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="uploading")
    row_count = models.PositiveIntegerField(default=0)
    column_count = models.PositiveIntegerField(default=0)
    column_names = models.JSONField(default=list, blank=True)
    column_types = models.JSONField(default=dict, blank=True)

    # Superset integration
    superset_dataset_id = models.PositiveIntegerField(
        null=True, blank=True, help_text="ID of the corresponding dataset in Superset"
    )

    # Access control
    allowed_roles = models.JSONField(
        default=list,
        blank=True,
        help_text='Roles that can access this dataset, e.g. ["finance", "ceo"]',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_datasets",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class DataFilter(models.Model):
    """
    Role-based data filters applied to datasets.
    These filters are sent to Superset as RLS rules when querying.
    """

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="filters")
    role = models.CharField(max_length=20)
    column_name = models.CharField(max_length=200)
    operator = models.CharField(
        max_length=20,
        choices=[
            ("eq", "Equals"),
            ("in", "In List"),
            ("contains", "Contains"),
            ("gt", "Greater Than"),
            ("lt", "Less Than"),
        ],
        default="eq",
    )
    value = models.JSONField(
        help_text='Filter value. For "in" operator, use a list like ["A", "B"]'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["dataset", "role"]

    def __str__(self):
        return f"{self.dataset.name} - {self.role}: {self.column_name} {self.operator} {self.value}"
