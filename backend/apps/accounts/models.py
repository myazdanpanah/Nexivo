from django.contrib.auth.models import AbstractUser
from django.db import models
from .role_filters import RoleFilter  # noqa: F401 — registered via role_filters.py


class Company(models.Model):
    """Top-level organization (e.g., a holding company or brand)."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    logo = models.ImageField(upload_to="companies/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Division(models.Model):
    """A division within a company (e.g., Sales Division, Finance Division)."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="divisions")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    # The manager of this division
    manager = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_divisions",
        help_text="Manager responsible for this division",
    )
    # Parent division for nested hierarchy (optional)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subdivisions",
        help_text="Parent division (for sub-divisions)",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["company__name", "name"]
        verbose_name_plural = "divisions"

    def __str__(self):
        return f"{self.company.name} → {self.name}"


class Team(models.Model):
    """A team within a division (e.g., Sales Team North, Finance Team Auditing)."""
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    # The team lead / manager
    manager = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_teams",
        help_text="Team lead responsible for this team",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["division__company__name", "division__name", "name"]

    def __str__(self):
        return f"{self.division.company.name} → {self.division.name} → {self.name}"


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

    # Org hierarchy links
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        help_text="Company this user belongs to",
    )
    division = models.ForeignKey(
        Division,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        help_text="Division this user belongs to",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
        help_text="Team this user belongs to",
    )
    # Direct manager (for org chart / reporting lines)
    reports_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direct_reports",
        help_text="Direct manager this user reports to",
    )

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
