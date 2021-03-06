# Generated by Django 2.2 on 2019-04-02 09:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("evan", "0008_auto_20190402_1052"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="dietary",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"type": "meal_preference"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="profile_meal_preference",
                to="evan.Metadata",
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="gender",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"type": "gender"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="profile_gender",
                to="evan.Metadata",
            ),
        ),
    ]
