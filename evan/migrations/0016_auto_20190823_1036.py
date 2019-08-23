# Generated by Django 2.2.4 on 2019-08-23 08:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('evan', '0015_auto_20190822_1016'),
    ]

    operations = [
        migrations.AddField(
            model_name='content',
            name='notes',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.FileField(blank=True, null=True, upload_to='public/images', verbose_name='Image')),
                ('position', models.PositiveSmallIntegerField(default=0)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['content_type', 'object_id', 'position'],
            },
        ),
    ]
