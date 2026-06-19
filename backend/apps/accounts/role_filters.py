from django.db import models
from django.conf import settings


class RoleFilter(models.Model):
    """
    Defines data access filters per role.
    Maps a role to a set of SQL conditions that are applied
    when querying datasets, without modifying the source data.
    """

    role = models.CharField(max_length=20)
    filter_name = models.CharField(max_length=100)
    filter_column = models.CharField(max_length=200, help_text="Column to filter on, e.g. department")
    filter_values = models.JSONField(
        default=list,
        help_text='List of allowed values, e.g. ["finance", "accounting"]',
    )
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["role", "filter_name"]

    def __str__(self):
        return f"{self.role}: {self.filter_name} ({self.filter_column} IN {self.filter_values})"
