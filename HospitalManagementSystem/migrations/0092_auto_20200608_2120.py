# Generated by Django 3.0.4 on 2020-06-08 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0091_auto_20200608_1524'),
    ]

    operations = [
        migrations.AlterField(
            model_name='test',
            name='test_abbr',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='test',
            name='test_description',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='test',
            name='test_name',
            field=models.CharField(max_length=30),
        ),
    ]
