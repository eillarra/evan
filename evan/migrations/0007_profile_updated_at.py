# Generated by Django 2.2 on 2019-04-01 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evan', '0006_event_ingenico_salt'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]