# Generated by Django 5.1.5 on 2025-02-28 10:44

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_viaje_coste'),
    ]

    operations = [
        migrations.AddField(
            model_name='passwordresettoken',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2025, 2, 28, 11, 44, 18, 969411, tzinfo=datetime.timezone.utc)),
        ),
    ]
