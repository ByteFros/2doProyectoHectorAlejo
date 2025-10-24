"""
Comando de Django para crear gastos de prueba en viajes existentes.
Genera gastos realistas distribuidos en los días de cada viaje.
"""
import random
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import EmpleadoProfile, Viaje, DiaViaje, Gasto
from users.viajes.services import inicializar_dias_viaje_finalizado


class Command(BaseCommand):
    help = "Crea gastos de prueba realistas para viajes existentes"

    # Categorías de gastos con montos realistas (en EUR)
    GASTOS_CONFIG = {
        'alojamiento': {
            'conceptos': [
                'Hotel - Habitación individual',
                'Hotel - Suite ejecutiva',
                'Apartamento turístico',
                'Hostel',
                'Airbnb',
            ],
            'monto_min': 50,
            'monto_max': 250,
            'por_dia': True,  # Un gasto de alojamiento por día
            'probabilidad': 0.9,  # 90% de días tienen alojamiento
        },
        'transporte': {
            'conceptos': [
                'Vuelo',
                'Tren AVE',
                'Taxi al aeropuerto',
                'Taxi desde hotel',
                'Uber',
                'Alquiler de coche',
                'Gasolina',
                'Peaje autopista',
                'Parking',
                'Metro/Autobús',
            ],
            'monto_min': 5,
            'monto_max': 350,
            'por_dia': False,  # Varios gastos de transporte posibles
            'probabilidad': 0.7,
        },
        'comida': {
            'conceptos': [
                'Desayuno',
                'Almuerzo con cliente',
                'Cena de trabajo',
                'Comida rápida',
                'Restaurante',
                'Cafetería',
            ],
            'monto_min': 8,
            'monto_max': 85,
            'por_dia': False,  # 2-3 comidas por día
            'probabilidad': 0.95,
        },
        'otros': {
            'conceptos': [
                'Material de oficina',
                'Tarjeta SIM internacional',
                'Internet móvil',
                'Lavandería',
                'Propinas',
                'Fotocopia de documentos',
            ],
            'monto_min': 3,
            'monto_max': 40,
            'por_dia': False,
            'probabilidad': 0.3,
        },
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--viajes-con-gastos',
            type=int,
            default=10,
            help='Número de viajes FINALIZADOS a los que añadir gastos (default: 10)',
        )
        parser.add_argument(
            '--viajes-en-revision',
            type=int,
            default=5,
            help='Número de nuevos viajes EN_REVISION a crear con gastos (default: 5)',
        )
        parser.add_argument(
            '--gastos-por-dia-min',
            type=int,
            default=2,
            help='Mínimo de gastos por día (default: 2)',
        )
        parser.add_argument(
            '--gastos-por-dia-max',
            type=int,
            default=6,
            help='Máximo de gastos por día (default: 6)',
        )
        parser.add_argument(
            '--clear-gastos',
            action='store_true',
            help='Elimina todos los gastos existentes antes de crear nuevos',
        )

    def handle(self, *args, **options):
        viajes_con_gastos = options['viajes_con_gastos']
        viajes_en_revision = options['viajes_en_revision']
        gastos_min = options['gastos_por_dia_min']
        gastos_max = options['gastos_por_dia_max']

        if options['clear_gastos']:
            self.stdout.write(self.style.WARNING('\n⚠️  Limpiando gastos existentes...'))
            deleted_count = Gasto.objects.all().delete()[0]
            self.stdout.write(self.style.SUCCESS(f'✓ {deleted_count} gastos eliminados\n'))

        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('GENERANDO GASTOS DE PRUEBA'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # 1. Añadir gastos a viajes finalizados existentes
        gastos_creados_finalizados = self._add_gastos_to_existing_trips(
            viajes_con_gastos,
            gastos_min,
            gastos_max
        )

        # 2. Crear nuevos viajes EN_REVISION con gastos
        gastos_creados_revision = self._create_trips_en_revision(
            viajes_en_revision,
            gastos_min,
            gastos_max
        )

        # Resumen final
        self._print_summary(
            gastos_creados_finalizados,
            gastos_creados_revision,
            viajes_con_gastos,
            viajes_en_revision
        )

    @transaction.atomic
    def _add_gastos_to_existing_trips(self, count, gastos_min, gastos_max):
        """Añade gastos a viajes FINALIZADOS existentes"""
        self.stdout.write(f'\n📋 Añadiendo gastos a {count} viajes FINALIZADOS...\n')

        # Obtener viajes finalizados sin gastos (o con pocos gastos)
        viajes = (
            Viaje.objects
            .filter(estado='FINALIZADO')
            .prefetch_related('dias', 'dias__gastos')
            .select_related('empleado', 'empresa')
            .order_by('?')[:count]
        )

        if not viajes.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  No se encontraron viajes FINALIZADOS')
            )
            return 0

        total_gastos = 0
        for idx, viaje in enumerate(viajes, 1):
            # Asegurar que tiene DiaViaje
            if viaje.dias.count() == 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠️  Viaje {viaje.id} sin días, creando...'
                    )
                )
                inicializar_dias_viaje_finalizado(viaje, exentos=True)

            gastos = self._create_gastos_for_trip(viaje, gastos_min, gastos_max)
            total_gastos += gastos

            self.stdout.write(
                f'  ✓ [{idx}/{count}] Viaje {viaje.id} '
                f'({viaje.empleado.nombre} → {viaje.ciudad}): '
                f'{gastos} gastos creados'
            )

        return total_gastos

    @transaction.atomic
    def _create_trips_en_revision(self, count, gastos_min, gastos_max):
        """Crea nuevos viajes EN_REVISION con gastos completos"""
        self.stdout.write(f'\n📋 Creando {count} viajes EN_REVISION con gastos...\n')

        # Obtener empleados aleatorios
        empleados = list(EmpleadoProfile.objects.select_related('empresa', 'user').all())

        if not empleados:
            self.stdout.write(
                self.style.ERROR('❌ No se encontraron empleados')
            )
            return 0

        # Destinos para viajes recientes
        destinos = [
            {'ciudad': 'Madrid', 'pais': 'España', 'internacional': False},
            {'ciudad': 'Barcelona', 'pais': 'España', 'internacional': False},
            {'ciudad': 'Valencia', 'pais': 'España', 'internacional': False},
            {'ciudad': 'París', 'pais': 'Francia', 'internacional': True},
            {'ciudad': 'Lisboa', 'pais': 'Portugal', 'internacional': True},
            {'ciudad': 'Londres', 'pais': 'Reino Unido', 'internacional': True},
        ]

        motivos = [
            'Reunión trimestral con equipo',
            'Visita a cliente importante',
            'Formación técnica especializada',
            'Conferencia del sector',
            'Auditoría de calidad',
        ]

        total_gastos = 0
        viajes_creados = 0

        for idx in range(count):
            empleado = random.choice(empleados)
            destino = random.choice(destinos)

            # Fechas: viajes que terminaron hace 1-7 días (listos para revisar)
            fecha_fin = date.today() - timedelta(days=random.randint(1, 7))
            duracion = random.choice([2, 3, 4, 5])
            fecha_inicio = fecha_fin - timedelta(days=duracion - 1)

            try:
                # Crear viaje EN_REVISION
                viaje = Viaje.objects.create(
                    empleado=empleado,
                    empresa=empleado.empresa,
                    destino=f"{destino['ciudad']}, {destino['pais']}",
                    ciudad=destino['ciudad'],
                    pais=destino['pais'],
                    es_internacional=destino['internacional'],
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    dias_viajados=duracion,
                    estado='EN_REVISION',
                    empresa_visitada=f'Cliente {random.choice(["Alpha", "Beta", "Gamma", "Delta"])}',
                    motivo=random.choice(motivos)
                )

                # Crear días (sin marcar como revisados, están en revisión)
                from users.viajes.services import crear_dias_viaje
                crear_dias_viaje(viaje)

                # Crear gastos
                gastos = self._create_gastos_for_trip(viaje, gastos_min, gastos_max)
                total_gastos += gastos
                viajes_creados += 1

                simbolo = '✈️' if destino['internacional'] else '🚄'
                self.stdout.write(
                    f'  {simbolo} [{idx+1}/{count}] {empleado.nombre} → {destino["ciudad"]} '
                    f'({duracion}d, {gastos} gastos)'
                )

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Error al crear viaje {idx+1}: {str(e)}')
                )

        return total_gastos

    def _create_gastos_for_trip(self, viaje, gastos_min, gastos_max):
        """Crea gastos realistas para un viaje específico"""
        dias = list(viaje.dias.all())
        total_gastos = 0

        # Decidir qué días tendrán gastos (algunos días pueden estar exentos sin gastos)
        dias_con_gastos = random.sample(
            dias,
            k=random.randint(max(1, len(dias) - 1), len(dias))
        )

        for dia in dias_con_gastos:
            num_gastos = random.randint(gastos_min, gastos_max)
            gastos_dia = 0

            # Generar gastos según categorías
            categorias_dia = self._select_categorias_for_day()

            for _ in range(num_gastos):
                if not categorias_dia:
                    break

                categoria = random.choice(list(categorias_dia.keys()))
                config = self.GASTOS_CONFIG[categoria]

                # Generar gasto
                concepto = random.choice(config['conceptos'])
                monto = round(random.uniform(config['monto_min'], config['monto_max']), 2)

                # Decidir estado del gasto (mayoría pendientes, algunos aprobados)
                estado = random.choices(
                    ['PENDIENTE', 'APROBADO', 'RECHAZADO'],
                    weights=[70, 25, 5],
                    k=1
                )[0]

                try:
                    Gasto.objects.create(
                        empleado=viaje.empleado,
                        empresa=viaje.empresa,
                        viaje=viaje,
                        dia=dia,
                        concepto=concepto,
                        monto=Decimal(str(monto)),
                        fecha_gasto=dia.fecha,
                        estado=estado
                    )
                    gastos_dia += 1
                    total_gastos += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'    ⚠️  Error al crear gasto: {str(e)}')
                    )

                # Remover categoría si es "por día" (solo un gasto de ese tipo por día)
                if config['por_dia']:
                    categorias_dia.pop(categoria, None)

        return total_gastos

    def _select_categorias_for_day(self):
        """Selecciona qué categorías de gastos tendrá un día"""
        categorias_seleccionadas = {}

        for categoria, config in self.GASTOS_CONFIG.items():
            if random.random() < config['probabilidad']:
                categorias_seleccionadas[categoria] = config

        return categorias_seleccionadas

    def _print_summary(self, gastos_finalizados, gastos_revision, viajes_finalizados, viajes_revision):
        """Imprime resumen de los gastos creados"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE GASTOS GENERADOS'))
        self.stdout.write('='*70)

        total_gastos = gastos_finalizados + gastos_revision

        self.stdout.write(f'\n💰 Total de gastos creados: {total_gastos}')
        self.stdout.write(f'   • Gastos en viajes FINALIZADOS: {gastos_finalizados}')
        self.stdout.write(f'   • Gastos en viajes EN_REVISION: {gastos_revision}')

        # Estadísticas por categoría
        self.stdout.write('\n📊 Distribución por categoría:')
        for categoria in ['alojamiento', 'transporte', 'comida', 'otros']:
            count = Gasto.objects.filter(concepto__icontains=categoria.split('_')[0]).count()
            if count > 0:
                porcentaje = (count / total_gastos * 100) if total_gastos > 0 else 0
                self.stdout.write(f'   • {categoria.capitalize()}: {count} ({porcentaje:.1f}%)')

        # Estadísticas por estado
        self.stdout.write('\n📈 Distribución por estado:')
        for estado in ['PENDIENTE', 'APROBADO', 'RECHAZADO', 'JUSTIFICAR']:
            count = Gasto.objects.filter(estado=estado).count()
            if count > 0:
                porcentaje = (count / total_gastos * 100) if total_gastos > 0 else 0
                self.stdout.write(f'   • {estado}: {count} ({porcentaje:.1f}%)')

        # Monto total
        from django.db.models import Sum
        monto_total = Gasto.objects.aggregate(Sum('monto'))['monto__sum'] or 0
        self.stdout.write(f'\n💵 Monto total de gastos: {monto_total:,.2f} EUR')

        # Viajes EN_REVISION
        viajes_en_revision_count = Viaje.objects.filter(estado='EN_REVISION').count()
        self.stdout.write(f'\n🔍 Viajes EN_REVISION: {viajes_en_revision_count}')
        self.stdout.write(f'   ({viajes_revision} creados por este comando)')

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✓ Gastos generados exitosamente'))
        self.stdout.write('='*70 + '\n')

        self.stdout.write(self.style.WARNING('💡 PRÓXIMOS PASOS:'))
        self.stdout.write('   • Los viajes EN_REVISION están listos para procesar')
        self.stdout.write('   • Usa el endpoint de revisión para aprobar/rechazar días')
        self.stdout.write('   • Los gastos están distribuidos realísticamente en los días')
        self.stdout.write('   • Mayoría de gastos en estado PENDIENTE\n')
