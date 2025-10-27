from django.db import migrations, models


def normalize_viaje_states(apps, schema_editor):
    Viaje = apps.get_model('users', 'Viaje')
    # Estados que desaparecen -> EN_REVISION
    Viaje.objects.filter(estado__in=['PENDIENTE', 'APROBADO', 'EN_CURSO', 'CANCELADO']).update(estado='EN_REVISION')
    # FINALIZADO pasa a REVISADO
    Viaje.objects.filter(estado='FINALIZADO').update(estado='REVISADO')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0031_alter_empleadoprofile_dni_and_more'),
    ]

    operations = [
        migrations.RunPython(normalize_viaje_states, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='viaje',
            name='estado',
            field=models.CharField(choices=[('EN_REVISION', 'En revision'), ('REVISADO', 'Revisado')], default='EN_REVISION', max_length=15),
        ),
    ]
