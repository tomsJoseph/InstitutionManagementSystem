# Generated by Django 3.0.4 on 2020-04-21 05:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0027_auto_20200420_2132'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffreport',
            name='dismissed',
            field=models.BooleanField(default=False, verbose_name='dismiss this report from list'),
        ),
    ]
