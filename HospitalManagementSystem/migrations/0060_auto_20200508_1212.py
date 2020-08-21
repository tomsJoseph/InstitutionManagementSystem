# Generated by Django 3.0.4 on 2020-05-08 06:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0059_disease_affected_organs'),
    ]

    operations = [
        migrations.AddField(
            model_name='surgery',
            name='team_leader',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='surgeries_led', to='HospitalManagementSystem.AppUser'),
        ),
        migrations.AlterField(
            model_name='disease',
            name='causes',
            field=models.ManyToManyField(blank=True, to='HospitalManagementSystem.CauseOfDisease'),
        ),
    ]
