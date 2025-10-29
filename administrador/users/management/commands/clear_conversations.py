"""Comando para eliminar conversaciones de prueba."""
from django.core.management.base import BaseCommand
from django.db.models import Count

from users.models import Conversacion


class Command(BaseCommand):
    help = "Elimina conversaciones y mensajes asociados"

    def add_arguments(self, parser):
        parser.add_argument(
            '--yes', action='store_true',
            help='Confirma la eliminación sin pedir confirmación.'
        )
        parser.add_argument(
            '--only-empty', action='store_true',
            help='Limita la eliminación a conversaciones sin mensajes.'
        )

    def handle(self, *args, **options):
        queryset = Conversacion.objects.all()

        if options['only_empty']:
            queryset = queryset.annotate(total=Count('mensajes')).filter(total=0)

        total = queryset.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('No se encontraron conversaciones para eliminar.'))
            return

        if not options['yes']:
            self.stdout.write(
                self.style.WARNING(
                    f'Se eliminarían {total} conversaciones. Ejecuta el comando con --yes para confirmar.'
                )
            )
            return

        deleted, _ = queryset.delete()
        self.stdout.write(self.style.SUCCESS(f'Eliminadas {total} conversaciones (registros afectados: {deleted}).'))
