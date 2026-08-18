from django.db import migrations


def rename_ingenico_salt_forward(apps, schema_editor) -> None:
    """Rename the ``ingenico_salt`` config key to ``salt`` for UGent-bridge events."""

    Event = apps.get_model("evan", "Event")

    for event in Event.objects.all():
        payments = (event.config or {}).get("payments") or {}
        if payments.get("type") == "ugent" and "ingenico_salt" in payments:
            payments["salt"] = payments.pop("ingenico_salt")
            event.config["payments"] = payments
            event.save(update_fields=["config"])


def rename_ingenico_salt_reverse(apps, schema_editor) -> None:
    """Rename the ``salt`` config key back to ``ingenico_salt`` for UGent-bridge events."""

    Event = apps.get_model("evan", "Event")

    for event in Event.objects.all():
        payments = (event.config or {}).get("payments") or {}
        if payments.get("type") == "ugent" and "salt" in payments:
            payments["ingenico_salt"] = payments.pop("salt")
            event.config["payments"] = payments
            event.save(update_fields=["config"])


class Migration(migrations.Migration):
    dependencies = [
        ("evan", "0024_alter_registrationpaymentattempt_options_and_more"),
    ]

    operations = [
        migrations.RunPython(rename_ingenico_salt_forward, rename_ingenico_salt_reverse),
    ]
