# Generated by Django 2.1.7 on 2019-03-26 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evan", "0005_registration_extra_fees"),
    ]

    operations = [
        migrations.AddField(
            model_name="event", name="ingenico_salt", field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
