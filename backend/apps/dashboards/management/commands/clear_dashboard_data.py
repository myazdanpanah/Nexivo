"""
Management command to delete all dashboard data (dashboards, pages, widgets).
Use: python manage.py clear_dashboard_data
"""
from django.core.management.base import BaseCommand
from apps.dashboards.models import Dashboard, DashboardPage, Widget
from apps.datasets.models import Dataset


class Command(BaseCommand):
    help = "Delete all dashboards, pages, widgets, and optionally datasets"

    def add_arguments(self, parser):
        parser.add_argument(
            "--include-datasets",
            action="store_true",
            help="Also delete all datasets",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip confirmation prompt",
        )

    def handle(self, *args, **options):
        widget_count = Widget.objects.count()
        page_count = DashboardPage.objects.count()
        dashboard_count = Dashboard.objects.count()
        dataset_count = Dataset.objects.count() if options["include_datasets"] else 0

        total = widget_count + page_count + dashboard_count + dataset_count

        if total == 0:
            self.stdout.write(self.style.SUCCESS("No data to delete. Already clean!"))
            return

        self.stdout.write(f"Found: {dashboard_count} dashboards, {page_count} pages, {widget_count} widgets")
        if options["include_datasets"]:
            self.stdout.write(f"  + {dataset_count} datasets")

        if not options["yes"]:
            confirm = input(f"\nAre you sure you want to delete ALL {total} records? (yes/no): ")
            if confirm.lower() != "yes":
                self.stdout.write(self.style.WARNING("Aborted."))
                return

        Widget.objects.all().delete()
        DashboardPage.objects.all().delete()
        Dashboard.objects.all().delete()

        if options["include_datasets"]:
            Dataset.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(
            f"Deleted {dashboard_count} dashboards, {page_count} pages, {widget_count} widgets"
            + (f", {dataset_count} datasets" if options["include_datasets"] else "")
        ))
