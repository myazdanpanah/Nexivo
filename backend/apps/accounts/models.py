from django.contrib.auth.models import AbstractUser
from django.db import models
from .role_filters import RoleFilter  # noqa: F401 — registered via role_filters.py


# ─── Module Registry ──────────────────────────────────────────────
# Each module that Nexivo can host is declared here.  The key is the
# stable slug used in enabled_modules JSON and route guards.
MODULE_CHOICES = [
    ("bi_dashboard", "BI Dashboard"),
    ("finance",       "Finance"),
    ("crm",           "CRM"),
    ("db_manager",    "Database Manager"),
    ("datasets",      "Data Upload"),
    ("llm",           "LLM Gateway"),
    ("settings",      "Settings"),
]

ALL_MODULE_IDS = [m[0] for m in MODULE_CHOICES]


class Company(models.Model):
    """Top-level organization (e.g., a holding company or brand)."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    logo = models.ImageField(upload_to="companies/", blank=True, null=True)

    # Which Nexivo modules this company has subscribed to / enabled.
    # Stored as a JSON list of module slugs, e.g. ["bi_dashboard", "datasets"].
    # A superuser bypasses this; a normal user only sees modules that are:
    #   1. present in their company's enabled_modules, AND
    #   2. permitted by their role (see permissions.py).
    enabled_modules = models.JSONField(
        default=list,
        blank=True,
        help_text='List of enabled module slugs, e.g. ["bi_dashboard", "datasets"]',
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def has_module(self, module_id: str) -> bool:
        """Return True if *module_id* is in this company's enabled list."""
        return module_id in (self.enabled_modules or [])

    def enable_module(self, module_id: str) -> None:
        """Add a module to the enabled list (idempotent)."""
        current = self.enabled_modules or []
        if module_id not in current:
            current.append(module_id)
            self.enabled_modules = current
            self.save(update_fields=["enabled_modules"])

    def disable_module(self, module_id: str) -> None:
        """Remove a module from the enabled list (idempotent)."""
        current = self.enabled_modules or []
        if module_id in current:
            current.remove(module_id)
            self.enabled_modules = current
            self.save(update_fields=["enabled_modules"])


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


class CustomRole(models.Model):
    """Custom role created by admins for fine-grained access control."""
    value = models.CharField(max_length=50, unique=True, help_text="Unique identifier (e.g. 'marketing')")
    label = models.CharField(max_length=100, help_text="Display name (e.g. 'بازاریابی')")
    color = models.CharField(max_length=50, default='bg-gray-100 text-gray-700', help_text="Tailwind color classes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['label']

    def __str__(self):
        return f"{self.label} ({self.value})"


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
