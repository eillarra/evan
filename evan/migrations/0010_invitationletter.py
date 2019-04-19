# Generated by Django 2.2 on 2019-04-19 09:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('evan', '0009_auto_20190402_1106'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvitationLetter',
            fields=[
                ('registration', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='letter', serialize=False, to='evan.Registration')),
                ('name', models.CharField(max_length=190)),
                ('passport_number', models.CharField(max_length=60)),
                ('nationality', models.CharField(max_length=190)),
                ('address', models.TextField()),
                ('submitted_paper', models.TextField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
            ],
        ),
    ]