from django.contrib.auth.models import AbstractUser
from django.db import models
from .role_filters import RoleFilter  # noqa: F401 — registered via role_filters.py


class User(AbstractUser):
    """
    Custom user model with role-based access for Nexivo.
    Roles: finance, sales, ceo, admin
    """

    ROLE_CHOICES = [
        ("finance", "Finance"),
        ("sales", "Sales"),
        ("ceo", "CEO"),
        ("admin", "Admin"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="sales")
    department = models.CharField(max_length=100, blank=True, default="")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_ceo(self):
        return self.role == "ceo"

    @property
    def is_finance(self):
        return self.role == "finance"

    @property
    def is_sales(self):
        return self.role == "sales"

    @property
    def is_admin_user(self):
        return self.role == "admin" or self.is_staff
