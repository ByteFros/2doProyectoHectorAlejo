"""
Comando de Django para crear viajes de prueba para empleados existentes.
Genera viajes en estado EN_REVISION con destinos reales (sin gastos).
"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand

from users.models import EmpleadoProfile, Viaje
from users.viajes.services import crear_dias_viaje


class Command(BaseCommand):
    help = "Crea viajes de prueba para empleados existentes con destinos reales"

    # Destinos reales con información completa
    DESTINOS_NACIONALES = [
        {
            'ciudad': 'Madrid',
            'pais': 'España',
            'empresas': ['Cliente Tecnológico Madrid', 'Banco Central', 'Consultora Ibérica', 'Retail Solutions'],
        },
        {
            'ciudad': 'Barcelona',
            'pais': 'España',
            'empresas': ['Startup Barcelona Tech', 'Port de Barcelona', 'Mobile World Congress', 'Design Studio BCN'],
        },
        {
            'ciudad': 'Valencia',
            'pais': 'España',
            'empresas': ['Puerto de Valencia', 'Ceramics Industry', 'Tourism Valencia', 'Agriculture Tech'],
        },
        {
            'ciudad': 'Sevilla',
            'pais': 'España',
            'empresas': ['Turismo Sevilla', 'Construcción del Sur', 'Agro Andalucía', 'Logistics Sevilla'],
        },
        {
            'ciudad': 'Bilbao',
            'pais': 'España',
            'empresas': ['Industrias del Norte', 'Guggenheim Foundation', 'Naval Engineering', 'Banco Bilbao'],
        },
        {
            'ciudad': 'Málaga',
            'pais': 'España',
            'empresas': ['Tech Park Málaga', 'Costa del Sol Tourism', 'Port Authority', 'Andalusia Tech'],
        },
        {
            'ciudad': 'Zaragoza',
            'pais': 'España',
            'empresas': ['Logistics Hub Aragón', 'Opel España', 'Agriculture Coop', 'Tech Innovation Zaragoza'],
        },
        {
            'ciudad': 'Alicante',
            'pais': 'España',
            'empresas': ['Puerto de Alicante', 'Tourism Costa Blanca', 'Wine Industry', 'Mediterranean Trade'],
        },
    ]

    DESTINOS_INTERNACIONALES = [
        {
            'ciudad': 'París',
            'pais': 'Francia',
            'empresas': ['Air France', 'L\'Oréal', 'Renault Group', 'Orange Telecom'],
        },
        {
            'ciudad': 'Londres',
            'pais': 'Reino Unido',
            'empresas': ['Financial Services UK', 'Tech London', 'British Airways', 'Consulting London'],
        },
        {
            'ciudad': 'Berlín',
            'pais': 'Alemania',
            'empresas': ['Siemens', 'Deutsche Telekom', 'Berlin Startup Hub', 'Manufacturing Solutions'],
        },
        {
            'ciudad': 'Roma',
            'pais': 'Italia',
            'empresas': ['Leonardo SpA', 'Fashion Milano', 'Tourism Italia', 'Food Industry Roma'],
        },
        {
            'ciudad': 'Ámsterdam',
            'pais': 'Países Bajos',
            'empresas': ['ING Bank', 'Philips', 'Port of Amsterdam', 'Dutch Tech'],
        },
        {
            'ciudad': 'Bruselas',
            'pais': 'Bélgica',
            'empresas': ['European Commission', 'NATO Headquarters', 'Belgian Consulting', 'EU Parliament'],
        },
        {
            'ciudad': 'Lisboa',
            'pais': 'Portugal',
            'empresas': ['Web Summit', 'Port of Lisbon', 'Portuguese Tourism', 'Tech Lisboa'],
        },
        {
            'ciudad': 'Dublín',
            'pais': 'Irlanda',
            'empresas': ['Google EMEA', 'Facebook Europe', 'Irish Tech Hub', 'Finance Dublin'],
        },
        {
            'ciudad': 'Milán',
            'pais': 'Italia',
            'empresas': ['Fashion Week Milano', 'Banca Intesa', 'Design Milano', 'Automotive Italia'],
        },
        {
            'ciudad': 'Múnich',
            'pais': 'Alemania',
            'empresas': ['BMW Group', 'Siemens Munich', 'Oktoberfest Organization', 'Tech Munich'],
        },
        {
            'ciudad': 'Zúrich',
            'pais': 'Suiza',
            'empresas': ['Credit Suisse', 'UBS', 'Swiss Finance', 'Pharma Zurich'],
        },
        {
            'ciudad': 'Viena',
            'pais': 'Austria',
            'empresas': ['OPEC Headquarters', 'Vienna Insurance', 'Cultural Vienna', 'Austrian Tech'],
        },
    ]

    MOTIVOS = [
        'Reunión con cliente para cierre de proyecto',
        'Conferencia anual del sector',
        'Visita a instalaciones de proveedor',
        'Presentación de nueva propuesta comercial',
        'Training técnico especializado',
        'Auditoría de calidad en sede cliente',
        'Negociación de contrato marco',
        'Workshop de innovación tecnológica',
        'Reunión de coordinación con equipo remoto',
        'Feria comercial del sector',
        'Due diligence de posible adquisición',
        'Kick-off de nuevo proyecto',
        'Reunión de seguimiento trimestral',
        'Presentación de resultados anuales',
        'Sesión de formación para cliente',
        'Evaluación de nueva oficina',
        'Congreso internacional',
        'Reunión con stakeholders clave',
        'Visita técnica a planta de producción',
        'Evento de networking empresarial',
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--trips-per-employee',
            type=int,
            default=5,
            help='Número de viajes a crear por empleado (default: 5)',
        )
        parser.add_argument(
            '--months-back',
            type=int,
            default=12,
            help='Meses hacia atrás para generar viajes (default: 12)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina todos los viajes existentes antes de crear nuevos',
        )

    def handle(self, *args, **options):
        trips_per_employee = options['trips_per_employee']
        months_back = options['months_back']

        if options['clear']:
            self.stdout.write(self.style.WARNING('\n⚠️  Limpiando viajes existentes...'))
            deleted_count = Viaje.objects.all().delete()[0]
            self.stdout.write(self.style.SUCCESS(f'✓ {deleted_count} viajes eliminados\n'))

        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('GENERANDO VIAJES DE PRUEBA'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # Obtener todos los empleados
        empleados = EmpleadoProfile.objects.select_related('empresa', 'user').all()

        if not empleados.exists():
            self.stdout.write(
                self.style.ERROR('❌ No se encontraron empleados en la base de datos.')
            )
            self.stdout.write(
                self.style.WARNING('   Ejecuta primero: python manage.py load_sample_data')
            )
            return

        total_empleados = empleados.count()
        self.stdout.write(f'📊 Se encontraron {total_empleados} empleados')
        self.stdout.write(f'📅 Generando {trips_per_employee} viajes por empleado')
        self.stdout.write(f'🗓️  Rango de fechas: últimos {months_back} meses\n')

        # Generar viajes
        viajes_creados = 0
        for idx, empleado in enumerate(empleados, 1):
            self.stdout.write(
                f'👤 [{idx}/{total_empleados}] Generando viajes para '
                f'{empleado.nombre} {empleado.apellido} ({empleado.empresa.nombre_empresa})'
            )

            viajes_empleado = self._create_trips_for_employee(
                empleado,
                trips_per_employee,
                months_back
            )
            viajes_creados += viajes_empleado

        # Resumen final
        self._print_summary(total_empleados, viajes_creados, trips_per_employee)

    def _create_trips_for_employee(self, empleado, count, months_back):
        """Crea viajes aleatorios para un empleado"""
        viajes_creados = 0

        for i in range(count):
            # Decidir si es nacional o internacional (70% nacional, 30% internacional)
            es_internacional = random.random() > 0.7

            if es_internacional:
                destino_info = random.choice(self.DESTINOS_INTERNACIONALES)
            else:
                destino_info = random.choice(self.DESTINOS_NACIONALES)

            # Generar fechas en el pasado
            fecha_inicio, fecha_fin, dias = self._generate_random_dates(months_back)

            # Seleccionar empresa visitada y motivo
            empresa_visitada = random.choice(destino_info['empresas'])
            motivo = random.choice(self.MOTIVOS)

            # Estado del viaje
            estado = 'EN_REVISION'

            # Construir destino
            destino = f"{destino_info['ciudad']}, {destino_info['pais']}"

            try:
                viaje = Viaje.objects.create(
                    empleado=empleado,
                    empresa=empleado.empresa,
                    destino=destino,
                    ciudad=destino_info['ciudad'],
                    pais=destino_info['pais'],
                    es_internacional=es_internacional,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    dias_viajados=dias,
                    estado=estado,
                    empresa_visitada=empresa_visitada,
                    motivo=motivo
                )

                # Crear DiaViaje para viajes revisados o en revisión
                dias_creados = crear_dias_viaje(viaje)
                # Algunos días se marcarán como no exentos para generar variedad
                for dia in dias_creados:
                    if random.random() < 0.3:
                        dia.exento = False
                        dia.save(update_fields=["exento"])

                viajes_creados += 1

                # Símbolo según tipo de viaje
                simbolo = '✈️' if es_internacional else '🚄'

                self.stdout.write(
                    f'  {simbolo} {i+1}/{count} - {destino} '
                    f'({fecha_inicio} → {fecha_fin}, {dias}d) - {estado}'
                )

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠️  Error al crear viaje {i+1}: {str(e)}'
                    )
                )

        return viajes_creados

    def _generate_random_dates(self, months_back):
        """Genera fechas aleatorias de viaje en el pasado"""
        today = date.today()

        # Fecha de inicio aleatoria en los últimos N meses
        days_back = random.randint(30, months_back * 30)
        fecha_inicio = today - timedelta(days=days_back)

        # Duración del viaje (1-7 días, con peso hacia duraciones cortas)
        duracion_options = [1, 1, 2, 2, 2, 3, 3, 4, 5, 7]
        dias = random.choice(duracion_options)
        fecha_fin = fecha_inicio + timedelta(days=dias - 1)

        return fecha_inicio, fecha_fin, dias

    def _get_random_estado(self):
        """Retorna un estado aleatorio con pesos"""
        # 80% revisados, 20% en revisión
        return 'EN_REVISION'

    def _print_summary(self, total_empleados, viajes_creados, trips_per_employee):
        """Imprime resumen de los viajes creados"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE VIAJES GENERADOS'))
        self.stdout.write('='*70)

        self.stdout.write(f'\n👥 Empleados procesados: {total_empleados}')
        self.stdout.write(f'✈️  Total de viajes creados: {viajes_creados}')
        self.stdout.write(f'📊 Promedio por empleado: {viajes_creados / total_empleados:.1f}')

        # Estadísticas por estado
        estados_stats = {}
        for estado, _ in Viaje.ESTADO_CHOICES:
            count = Viaje.objects.filter(estado=estado).count()
            if count > 0:
                estados_stats[estado] = count

        self.stdout.write('\n📈 Distribución por estado:')
        for estado, count in estados_stats.items():
            porcentaje = (count / viajes_creados * 100) if viajes_creados > 0 else 0
            self.stdout.write(f'   • {estado}: {count} ({porcentaje:.1f}%)')

        # Estadísticas nacionales vs internacionales
        nacionales = Viaje.objects.filter(es_internacional=False).count()
        internacionales = Viaje.objects.filter(es_internacional=True).count()

        self.stdout.write('\n🌍 Distribución geográfica:')
        if viajes_creados > 0:
            self.stdout.write(f'   • Viajes nacionales: {nacionales} ({nacionales/viajes_creados*100:.1f}%)')
            self.stdout.write(f'   • Viajes internacionales: {internacionales} ({internacionales/viajes_creados*100:.1f}%)')
        else:
            self.stdout.write('   • Sin viajes generados')

        # Top 5 destinos más visitados
        from django.db.models import Count
        top_destinos = (
            Viaje.objects
            .values('ciudad', 'pais')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        self.stdout.write('\n🏆 Top 5 destinos más visitados:')
        for idx, destino in enumerate(top_destinos, 1):
            self.stdout.write(
                f'   {idx}. {destino["ciudad"]}, {destino["pais"]} - {destino["count"]} viajes'
            )

        # Estadísticas de días
        from users.models import DiaViaje
        total_dias = DiaViaje.objects.count()
        dias_exentos = DiaViaje.objects.filter(exento=True).count()
        dias_no_exentos = DiaViaje.objects.filter(exento=False).count()

        self.stdout.write('\n📅 Estadísticas de días de viaje:')
        self.stdout.write(f'   • Total de días creados: {total_dias}')
        if total_dias > 0:
            self.stdout.write(f'   • Días exentos: {dias_exentos} ({dias_exentos/total_dias*100:.1f}%)')
            self.stdout.write(f'   • Días no exentos: {dias_no_exentos} ({dias_no_exentos/total_dias*100:.1f}%)')
        else:
            self.stdout.write('   • No se han generado días de viaje')

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✓ Viajes generados exitosamente'))
        self.stdout.write('='*70 + '\n')

        self.stdout.write(self.style.WARNING('💡 NOTAS:'))
        self.stdout.write('   • Los DiaViaje han sido creados e inicializados')
        self.stdout.write('   • Los viajes NO tienen gastos asociados todavía')
        self.stdout.write('   • Para agregar gastos, ejecuta: python manage.py create_sample_expenses')
        self.stdout.write('   • La mayoría de viajes están en estado REVISADO')
        self.stdout.write('   • 70% de viajes con días exentos, 30% con días no exentos')
        self.stdout.write('   • Fechas generadas en los últimos 12 meses por defecto\n')
