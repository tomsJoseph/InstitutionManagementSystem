# Generated by Django 3.0.4 on 2020-04-10 06:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0004_remove_shift_next_turn'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='next_turn',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='HospitalManagementSystem.Shift'),
        ),
    ]
