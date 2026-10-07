from django.db import migrations
from django.utils import timezone


def seed_deepseek_flash(apps, schema_editor):
    ModelPrice = apps.get_model("telemetry", "ModelPrice")
    ModelPrice.objects.get_or_create(
        model="deepseek-flash",
        version="v1",
        defaults={
            "input_per_1k_micros": 140,
            "output_per_1k_micros": 280,
            "currency": "USD",
            "effective_at": timezone.now(),
        },
    )


def unseed_deepseek_flash(apps, schema_editor):
    ModelPrice = apps.get_model("telemetry", "ModelPrice")
    ModelPrice.objects.filter(model="deepseek-flash", version="v1").delete()


class Migration(migrations.Migration):
    dependencies = [("telemetry", "0001_initial")]

    operations = [
        migrations.RunPython(seed_deepseek_flash, unseed_deepseek_flash),
    ]
