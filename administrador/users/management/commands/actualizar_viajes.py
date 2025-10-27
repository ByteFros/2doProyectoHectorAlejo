from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Comando legacy sin efecto tras la simplificación de estados de viajes."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Sin cambios: los viajes ya no se actualizan automáticamente por fecha."))
