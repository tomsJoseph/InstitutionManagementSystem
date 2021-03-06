# Generated by Django 3.0.4 on 2020-05-10 09:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0064_fatality_updated_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='surgery',
            name='initiated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='surgeries_initiated', to='HospitalManagementSystem.AppUser'),
        ),
    ]
