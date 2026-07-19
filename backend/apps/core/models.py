"""
Enterprise ERP Base Models — Shared mixins for all business models.

Per DATABASE_SCHEMA.md §3: Every business table must include audit fields.
Per DJANGO_BACKEND.md §19: Soft delete policy — business documents are never
physically deleted.
Per DJANGO_BACKEND.md §11: Company and Branch isolation.
"""

import uuid
from django.db import models
from django.conf import settings


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted records by default."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteMixin(models.Model):
    """
    Soft delete mixin — business documents are never physically deleted.

    Adds: is_deleted, deleted_at, deleted_by, delete_reason
    Per DATABASE_SCHEMA.md: deleted_at, deleted_by, delete_reason
    """

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(class)s_deleted",
    )
    delete_reason = models.CharField(max_length=500, blank=True, default="")

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self, user=None, reason: str = ""):
        """Soft-delete this record instead of hard-deleting."""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.delete_reason = reason
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "delete_reason"])

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.delete_reason = ""
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "delete_reason"])


class AuditFieldsMixin(models.Model):
    """
    Audit trail fields — every entity tracks who created and updated it.

    Per DJANGO_BACKEND.md §18: Audit Trail.
    Per DATABASE_SCHEMA.md §3: Common Audit Fields.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="%(class)s_updated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CompanyIsolationMixin(models.Model):
    """
    Multi-company isolation — every record belongs to one company.

    Per DJANGO_BACKEND.md §11: Multi-Company Architecture.
    Per MASTER_ARCHITECTURE.md §6: Multi Company Architecture.
    """

    company = models.ForeignKey(
        "accounts.Company",
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
    )

    class Meta:
        abstract = True


class BaseModel(CompanyIsolationMixin, AuditFieldsMixin, SoftDeleteMixin):
    """
    Base model for all business entities in the ERP.

    Includes: company isolation, audit fields, soft delete.
    """

    class Meta:
        abstract = True
