# Generated by Django 3.0.4 on 2020-06-04 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0084_complaintsfeedback_authority_remark'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complaintsfeedback',
            name='authority_remark',
            field=models.TextField(max_length=200, null=True),
        ),
    ]
