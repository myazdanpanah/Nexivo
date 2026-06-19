"""
Management command to create a superuser and sample data for local development.
This command is idempotent: it always resets passwords on every run,
so you can safely run it multiple times.

Usage: python manage.py create_dev_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


DEV_USERS = [
    {
        "username": "admin",
        "email": "admin@nexivo.local",
        "password": "admin12345",
        "role": "admin",
        "department": "IT",
        "first_name": "Admin",
        "last_name": "User",
        "is_superuser": True,
        "is_staff": True,
    },
    {
        "username": "ceo",
        "email": "ceo@nexivo.local",
        "password": "ceo123456",
        "role": "ceo",
        "department": "Executive",
        "first_name": "CEO",
        "last_name": "User",
    },
    {
        "username": "finance",
        "email": "finance@nexivo.local",
        "password": "finance123",
        "role": "finance",
        "department": "Finance",
        "first_name": "Finance",
        "last_name": "User",
    },
    {
        "username": "sales",
        "email": "sales@nexivo.local",
        "password": "sales12345",
        "role": "sales",
        "department": "Sales",
        "first_name": "Sales",
        "last_name": "User",
    },
]


class Command(BaseCommand):
    help = "Create (or reset) superuser and sample users for local development"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Reset ALL dev users even if they already exist (passwords always reset)",
        )

    def handle(self, *args, **options):
        force = options["force"]

        for data in DEV_USERS:
            username = data["username"]
            password = data["password"]
            is_superuser = data.get("is_superuser", False)
            is_staff = data.get("is_staff", False)

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": data["email"],
                    "role": data["role"],
                    "department": data.get("department", ""),
                    "first_name": data.get("first_name", ""),
                    "last_name": data.get("last_name", ""),
                    "is_superuser": is_superuser,
                    "is_staff": is_staff,
                },
            )

            # Always reset password and role (idempotent)
            user.set_password(password)
            user.role = data["role"]
            user.email = data["email"]
            user.department = data.get("department", "")
            user.first_name = data.get("first_name", "")
            user.last_name = data.get("last_name", "")
            if is_superuser:
                user.is_superuser = True
                user.is_staff = True
            user.save()

            status = "created" if created else "updated (password reset)"
            self.stdout.write(self.style.SUCCESS(f'  {username:10s} {status}'))

        self.stdout.write(self.style.SUCCESS("\nAll dev users ready!"))
        self.stdout.write("Login credentials:")
        self.stdout.write("  admin   / admin12345")
        self.stdout.write("  ceo     / ceo123456")
        self.stdout.write("  finance / finance123")
        self.stdout.write("  sales   / sales12345")
