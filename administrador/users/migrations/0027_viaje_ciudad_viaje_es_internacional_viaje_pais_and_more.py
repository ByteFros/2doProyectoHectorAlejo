# Generated by Django 5.1.5 on 2025-04-24 07:50

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0026_gasto_fecha_gasto_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='viaje',
            name='ciudad',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='viaje',
            name='es_internacional',
            field=models.BooleanField(default=False, help_text="True si el país es distinto de 'España'"),
        ),
        migrations.AddField(
            model_name='viaje',
            name='pais',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='passwordresettoken',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2025, 4, 24, 8, 50, 44, 722091, tzinfo=datetime.timezone.utc)),
        ),
    ]
