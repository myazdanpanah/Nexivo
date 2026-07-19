"""
Auto-seed bi_dashboard for existing companies that have no modules enabled.

This data migration runs after 0004_company_enabled_modules and ensures
that companies created before the module management feature are not left
with empty enabled_modules lists.
"""

from django.db import migrations


def seed_modules(apps, schema_editor):
    Company = apps.get_model("accounts", "Company")
    for company in Company.objects.filter(enabled_modules=[]):
        company.enabled_modules = ["bi_dashboard"]
        company.save(update_fields=["enabled_modules"])


def reverse_seed(apps, schema_editor):
    Company = apps.get_model("accounts", "Company")
    Company.objects.filter(enabled_modules=["bi_dashboard"]).update(enabled_modules=[])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_company_enabled_modules"),
    ]

    operations = [
        migrations.RunPython(seed_modules, reverse_seed),
    ]
