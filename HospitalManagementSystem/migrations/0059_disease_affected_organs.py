# Generated by Django 3.0.4 on 2020-05-06 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0058_humanorgan_related_organs'),
    ]

    operations = [
        migrations.AddField(
            model_name='disease',
            name='affected_organs',
            field=models.ManyToManyField(to='HospitalManagementSystem.HumanOrgan'),
        ),
    ]
