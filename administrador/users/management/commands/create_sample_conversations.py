"""Comando para generar conversaciones de ejemplo."""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from users.models import Conversacion, Mensaje, CustomUser, Viaje, Gasto


class Command(BaseCommand):
    help = "Crea conversaciones de prueba con mensajes iniciales"

    def add_arguments(self, parser):
        parser.add_argument(
            '--conversations', type=int, default=10,
            help='Número de conversaciones a crear (default: 10)'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        total = options['conversations']

        master = CustomUser.objects.filter(role='MASTER').first()
        empresa_users = list(CustomUser.objects.filter(role='EMPRESA'))
        empleados = list(CustomUser.objects.filter(role='EMPLEADO'))

        if not master:
            self.stdout.write(self.style.ERROR('❌ No existe usuario MASTER.'))
            return
        if not empresa_users:
            self.stdout.write(self.style.ERROR('❌ No existen usuarios EMPRESA.'))
            return
        if len(empleados) < 2:
            self.stdout.write(self.style.ERROR('❌ Se requieren al menos dos empleados.'))
            return

        viajes = list(Viaje.objects.all())
        gastos = list(Gasto.objects.all())

        created = 0
        for idx in range(total):
            modo = idx % 4

            if modo == 0 and viajes:
                viaje = viajes[idx % len(viajes)]
                creador = master if idx % 2 == 0 else empresa_users[idx % len(empresa_users)]
                conversacion = Conversacion.objects.create(viaje=viaje)
                conversacion.participantes.add(creador, viaje.empleado.user)
                mensaje_inicial = f"Hola {viaje.empleado.user.username}, revisemos el viaje a {viaje.destino}."
                Mensaje.objects.create(
                    conversacion=conversacion,
                    autor=creador,
                    contenido=mensaje_inicial,
                    fecha_creacion=timezone.now() + timezone.timedelta(minutes=idx)
                )
                created += 1
                continue

            if modo == 1:
                empresa = empresa_users[idx % len(empresa_users)]
                empleado = empleados[idx % len(empleados)]
                conversacion = Conversacion.objects.create()
                conversacion.participantes.add(empresa, empleado)
                Mensaje.objects.create(
                    conversacion=conversacion,
                    autor=empresa,
                    contenido=f"Hola {empleado.username}, revisemos documentación pendiente.",
                    fecha_creacion=timezone.now() + timezone.timedelta(minutes=idx)
                )
                Mensaje.objects.create(
                    conversacion=conversacion,
                    autor=empleado,
                    contenido="Gracias, adjunto los archivos solicitados.",
                    fecha_creacion=timezone.now() + timezone.timedelta(minutes=idx + 1)
                )
                created += 1
                continue

            if modo == 2 and gastos:
                gasto = gastos[idx % len(gastos)]
                conversacion, _ = Conversacion.objects.get_or_create(gasto=gasto)
                conversacion.participantes.add(master, gasto.empleado.user)
                Mensaje.objects.create(
                    conversacion=conversacion,
                    autor=master,
                    contenido=f"Revisemos el justificante del gasto {gasto.id} ({gasto.concepto}).",
                    fecha_creacion=timezone.now() + timezone.timedelta(minutes=idx)
                )
                created += 1
                continue

            conversacion = Conversacion.objects.create()
            autor = master
            receptor = empleados[idx % len(empleados)]
            conversacion.participantes.add(autor, receptor)
            Mensaje.objects.create(
                conversacion=conversacion,
                autor=autor,
                contenido="Conversación libre de coordinación.",
                fecha_creacion=timezone.now() + timezone.timedelta(minutes=idx)
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'✅ {created} conversaciones creadas.'))
