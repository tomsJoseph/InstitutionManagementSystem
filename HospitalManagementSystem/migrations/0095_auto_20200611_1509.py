# Generated by Django 3.0.4 on 2020-06-11 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0094_bill_surgery_refund'),
    ]

    operations = [
        migrations.AlterField(
            model_name='disease',
            name='causes',
            field=models.ManyToManyField(blank=True, to='HospitalManagementSystem.CauseOfDisease'),
        ),
    ]
