# Generated by Django 3.0.4 on 2020-04-26 06:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0034_auto_20200426_1159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patientpersonalreccord',
            name='deceased',
            field=models.BooleanField(default=False),
        ),
    ]
