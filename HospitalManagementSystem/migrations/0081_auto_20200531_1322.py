# Generated by Django 3.0.4 on 2020-05-31 07:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0080_auto_20200521_1453'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complaintsfeedback',
            name='concerned_department',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='HospitalManagementSystem.Department'),
        ),
        migrations.AlterField(
            model_name='patienthealthreccord',
            name='op_time_stamp',
            field=models.DateTimeField(blank=True),
        ),
    ]
