# Generated by Django 3.0.4 on 2020-06-17 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0104_remove_patienthealthreccord_op_time_stamp_change'),
    ]

    operations = [
        migrations.AddField(
            model_name='patienthealthreccord',
            name='op_time_stamp_change',
            field=models.IntegerField(default=1),
        ),
    ]
