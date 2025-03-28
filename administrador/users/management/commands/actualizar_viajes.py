from django.core.management.base import BaseCommand
from django.utils.timezone import now

from users.models import Viaje


class Command(BaseCommand):
    help = "Actualiza viajes aprobados a 'EN_CURSO' si la fecha de inicio ha llegado"

    def handle(self, *args, **kwargs):
        hoy = now().date()
        viajes_a_actualizar = Viaje.objects.filter(estado="PENDIENTE", fecha_inicio__lte=hoy)

        total = viajes_a_actualizar.update(estado="EN_CURSO")

        self.stdout.write(self.style.SUCCESS(f"[OK]{total} viaje(s) actualizados a 'EN_CURSO'"))
