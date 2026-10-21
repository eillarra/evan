from django.db import migrations, models


def private_to_attendees(apps, schema_editor):
    """Map the old binary flag onto the new visibility tiers.

    The old ``private`` tier granted access to the owning object's managers and
    to accepted attendees of the owning event, which is exactly the new
    ``attendees`` tier. ``public`` files stay public.
    """
    File = apps.get_model("evan", "File")
    File.objects.filter(visibility="private").update(visibility="attendees")


def attendees_to_private(apps, schema_editor):
    """Restore the old binary flag; organizer-tier files fall back to private."""
    File = apps.get_model("evan", "File")
    File.objects.filter(visibility__in=["attendees", "organizers"]).update(visibility="private")


class Migration(migrations.Migration):
    dependencies = [
        ("evan", "0028_event_modules_backfill"),
    ]

    operations = [
        migrations.RenameField(
            model_name="file",
            old_name="type",
            new_name="visibility",
        ),
        migrations.AlterField(
            model_name="file",
            name="visibility",
            field=models.CharField(
                choices=[("public", "Public"), ("attendees", "Attendees"), ("organizers", "Organizers")],
                default="attendees",
                max_length=16,
            ),
        ),
        migrations.RunPython(private_to_attendees, attendees_to_private),
    ]
