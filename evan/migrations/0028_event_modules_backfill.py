"""Backfill existing events to the all-modules-on mapping.

Events that predate the module system must behave exactly as before, so every
existing event is mapped to all modules enabled, the public registration
audience, and a listed listing status. Reversing restores the same mapping.
"""

from django.db import migrations


MODULE_KEYS = ("payments", "content", "program", "papers", "communications")


def backfill_existing_events(apps, schema_editor):
    """Map every existing event to all modules on, public audience, listed.

    :param apps: A registry of historical models provided by Django.
    :param schema_editor: The schema editor for the current database.
    """
    Event = apps.get_model("evan", "Event")
    for event in Event.objects.all():
        config = dict(event.config or {})
        config["modules"] = {key: True for key in MODULE_KEYS}
        event.config = config
        event.registration_audience = "public"
        event.listing_status = "listed"
        event.save()


class Migration(migrations.Migration):
    dependencies = [
        ("evan", "0027_alter_user_managers_event_decline_reason_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_existing_events, backfill_existing_events),
    ]
