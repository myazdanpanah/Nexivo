# Generated migration for enabled_modules field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_customrole"),
    ]

    operations = [
        migrations.AddField(
            model_name="company",
            name="enabled_modules",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='List of enabled module slugs, e.g. ["bi_dashboard", "datasets"]',
            ),
        ),
    ]
