# Generated by Django 5.1.5 on 2025-03-20 09:45

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_alter_passwordresettoken_expires_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='viaje',
            name='empresa_visitada',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='viaje',
            name='motivo',
            field=models.TextField(default='No se ha declarado el motivo por parte del empleado', max_length=500),
        ),
        migrations.AlterField(
            model_name='passwordresettoken',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2025, 3, 20, 10, 45, 45, 740170, tzinfo=datetime.timezone.utc)),
        ),
    ]
