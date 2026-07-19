"""
Management command to seed default enabled_modules for existing companies.

Companies created before the module management feature will have an empty
enabled_modules list.  This command adds 'bi_dashboard' as a sensible
default so existing tenants aren't left with no accessible modules.

Usage:
    python manage.py seed_default_modules          # only companies with empty list
    python manage.py seed_default_modules --all    # force re-seed all companies
"""

from django.core.management.base import BaseCommand
from apps.accounts.models import Company


DEFAULT_MODULE = "bi_dashboard"


class Command(BaseCommand):
    help = "Seed default enabled_modules for companies that have none."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            dest="force_all",
            help="Add the default module to ALL companies, even those with existing modules.",
        )

    def handle(self, *args, **options):
        force = options["force_all"]

        if force:
            companies = Company.objects.all()
        else:
            companies = Company.objects.filter(enabled_modules=[])

        updated = 0
        for company in companies:
            modules = company.enabled_modules or []
            if DEFAULT_MODULE not in modules:
                modules.append(DEFAULT_MODULE)
                company.enabled_modules = modules
                company.save(update_fields=["enabled_modules"])
                updated += 1
                self.stdout.write(
                    f"  ✓ {company.name}: enabled_modules → {modules}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {updated} company(ies) updated with default module '{DEFAULT_MODULE}'."
            )
        )
