# Generated by Django 3.0.4 on 2020-06-06 05:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0086_auto_20200605_2100'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patienthealthreccord',
            name='department',
        ),
    ]
