# Generated by Django 3.0.4 on 2020-04-30 04:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0046_auto_20200430_1009'),
    ]

    operations = [
        migrations.AddField(
            model_name='morgue',
            name='dismissed',
            field=models.BooleanField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='morgue',
            name='start_date',
            field=models.DateField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='morgue',
            name='start_time',
            field=models.TimeField(auto_now_add=True),
        ),
    ]
