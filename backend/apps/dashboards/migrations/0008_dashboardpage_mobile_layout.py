from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0007_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='dashboardpage',
            name='mobile_layout',
            field=models.JSONField(blank=True, default=list, verbose_name='Mobile layout grid'),
        ),
    ]
