# Generated by Django 3.0.4 on 2020-04-19 05:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0022_staffreport_remark_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffreport',
            name='stop_editing',
            field=models.BooleanField(default=False, verbose_name='stop editing of this report'),
        ),
    ]
