# Generated by Django 3.0.4 on 2020-06-15 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0101_emessage_sender_dept'),
    ]

    operations = [
        migrations.AlterField(
            model_name='disciplinaryaction',
            name='start_date',
            field=models.DateTimeField(null=True),
        ),
    ]
