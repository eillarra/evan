# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-22 14:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('toucon', '0005_auto_20171120_1653'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='registration',
            name='toucon_regi_code_056dea_idx',
        ),
        migrations.RenameField(
            model_name='registration',
            old_name='code',
            new_name='uuid',
        ),
        migrations.AddIndex(
            model_name='registration',
            index=models.Index(fields=['uuid'], name='toucon_regi_uuid_ee4ad7_idx'),
        ),
    ]
