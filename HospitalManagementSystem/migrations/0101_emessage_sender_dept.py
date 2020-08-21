# Generated by Django 3.0.4 on 2020-06-15 09:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('HospitalManagementSystem', '0100_emessage_reciever_dept'),
    ]

    operations = [
        migrations.AddField(
            model_name='emessage',
            name='sender_dept',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages_from_dept', to='HospitalManagementSystem.Department'),
        ),
    ]
