from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="DeviceSession",
            new_name="Session",
        ),
        migrations.AlterModelTable(
            name="session",
            table="accounts_session",
        ),
        migrations.AlterField(
            model_name="session",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sessions",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
