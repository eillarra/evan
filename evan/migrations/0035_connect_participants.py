from django.db import migrations


def connect_participants(apps, schema_editor):
    Profile = apps.get_model("evan", "Profile")

    for p in Profile.objects.all():
        p.custom_data = {**p.custom_data, **{"connect": True, "special_needs": None}}
        p.save()


class Migration(migrations.Migration):

    dependencies = [
        ("evan", "0035_auto_20210626_1604"),
    ]

    operations = [
        # -----------
        migrations.RunPython(connect_participants),
        # -----------
    ]
