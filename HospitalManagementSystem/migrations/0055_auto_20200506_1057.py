# Generated by Django 3.0.4 on 2020-05-06 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0054_humanorgan_related_organs'),
    ]

    operations = [
        migrations.AlterField(
            model_name='humanorgan',
            name='photo',
            field=models.FileField(blank=True, default=None, null=True, upload_to='organs'),
        ),
        migrations.AlterField(
            model_name='humanorgan',
            name='related_organs',
            field=models.ManyToManyField(blank=True, to='HospitalManagementSystem.HumanOrgan'),
        ),
    ]
