from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_viaje_estado_transicion'),
    ]

    operations = [
        migrations.AddField(
            model_name='empleadoprofile',
            name='salario',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True),
        ),
    ]
