# Generated by Django 3.0.4 on 2020-04-28 10:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0038_auto_20200428_1044'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patienthealthreccord',
            name='accident',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='HospitalManagementSystem.Accident'),
        ),
        migrations.AlterField(
            model_name='surgery',
            name='surgery_report',
            field=models.TextField(default='Surgery not over', max_length=400, verbose_name='report'),
        ),
        migrations.DeleteModel(
            name='Autopsy',
        ),
    ]
