# Generated by Django 3.0.4 on 2020-05-05 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0052_auto_20200505_1218'),
    ]

    operations = [
        migrations.AddField(
            model_name='humanorgan',
            name='photo',
            field=models.FileField(default=None, upload_to='organs'),
            preserve_default=False,
        ),
    ]
