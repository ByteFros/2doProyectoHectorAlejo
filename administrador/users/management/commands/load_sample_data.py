"""
Comando de Django para cargar datos de prueba en la base de datos.
Crea 2 empresas con 10 empleados cada una.
"""
import random
from django.core.management.base import BaseCommand

from users.models import CustomUser, EmpresaProfile
from users.empresas.services import create_empresa, create_empleado


class Command(BaseCommand):
    help = "Carga datos de prueba: 2 empresas con 10 empleados cada una"

    # Contador global para generar DNIs únicos
    dni_counter = 10000000

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina todos los datos existentes antes de cargar los nuevos',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('\n⚠️  Limpiando datos existentes...'))
            self._clear_data()
            self.stdout.write(self.style.SUCCESS('✓ Datos eliminados correctamente\n'))

        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('CARGANDO DATOS DE PRUEBA'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # Crear empresas
        empresas = self._create_empresas()

        # Crear empleados para cada empresa
        total_empleados = 0
        for empresa in empresas:
            empleados_creados = self._create_empleados(empresa, count=10)
            total_empleados += empleados_creados

        # Resumen final
        self._print_summary(empresas, total_empleados)

    def _clear_data(self):
        """Elimina todos los datos de empresas y empleados (excepto MASTER)"""
        from users.models import EmpleadoProfile

        # Eliminar empleados
        EmpleadoProfile.objects.all().delete()

        # Eliminar usuarios EMPLEADO
        CustomUser.objects.filter(role='EMPLEADO').delete()

        # Eliminar empresas
        EmpresaProfile.objects.all().delete()

        # Eliminar usuarios EMPRESA
        CustomUser.objects.filter(role='EMPRESA').delete()

    def _create_empresas(self):
        """Crea 2 empresas de prueba"""
        empresas_data = [
            {
                'nombre_empresa': 'TechNova Solutions S.L.',
                'nif': 'B12345678',
                'correo_contacto': 'contacto@technova.com',
                'address': 'Calle Serrano 45',
                'city': 'Madrid',
                'postal_code': '28001',
                'permisos': True
            },
            {
                'nombre_empresa': 'InnovaDigital Consulting S.A.',
                'nif': 'A87654321',
                'correo_contacto': 'info@innovadigital.com',
                'address': 'Paseo de Gracia 123',
                'city': 'Barcelona',
                'postal_code': '08008',
                'permisos': True
            }
        ]

        empresas = []
        for data in empresas_data:
            try:
                empresa = create_empresa(data)
                empresas.append(empresa)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Empresa creada: {data["nombre_empresa"]} (NIF: {data["nif"]})'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error al crear empresa {data["nombre_empresa"]}: {str(e)}'
                    )
                )

        return empresas

    def _generate_valid_dni(self):
        """Genera un DNI válido calculando la letra correctamente"""
        DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

        # Incrementar contador para obtener un número único
        numero = self.dni_counter
        self.dni_counter += 1

        # Calcular letra
        letra = DNI_LETTERS[numero % 23]

        return f"{numero:08d}{letra}"

    def _create_empleados(self, empresa, count=10):
        """Crea empleados para una empresa"""
        self.stdout.write(f'\n📋 Creando {count} empleados para {empresa.nombre_empresa}...')

        # Lista de nombres y apellidos españoles
        nombres = [
            'Carlos', 'María', 'Juan', 'Ana', 'Pedro', 'Laura', 'Miguel', 'Carmen',
            'José', 'Isabel', 'Francisco', 'Marta', 'Antonio', 'Lucía', 'Manuel',
            'Elena', 'Javier', 'Sara', 'David', 'Patricia'
        ]

        apellidos = [
            'García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez',
            'Sánchez', 'Pérez', 'Gómez', 'Martín', 'Jiménez', 'Ruiz', 'Hernández',
            'Díaz', 'Moreno', 'Muñoz', 'Álvarez', 'Romero', 'Alonso', 'Gutiérrez'
        ]

        empleados_creados = 0
        for i in range(count):
            nombre = random.choice(nombres)
            apellido1 = random.choice(apellidos)
            apellido2 = random.choice(apellidos)

            # Generar DNI válido único
            dni = self._generate_valid_dni()

            # Generar email único
            email = f'{nombre.lower()}.{apellido1.lower()}{i}@{empresa.nombre_empresa.split()[0].lower()}.com'

            empleado_data = {
                'nombre': nombre,
                'apellido': f'{apellido1} {apellido2}',
                'dni': dni,
                'email': email,
                'username': f'{nombre.lower()}.{apellido1.lower()}{i}',
                'password': 'empleado123',
                'salario': random.randint(18000, 48000)
            }

            try:
                empleado = create_empleado(empresa=empresa, **empleado_data)
                empleados_creados += 1
                self.stdout.write(
                    f'  ✓ {empleados_creados}/10 - {nombre} {apellido1} {apellido2} (DNI: {dni})'
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠️  Error al crear empleado {nombre} {apellido1}: {str(e)}'
                    )
                )

        return empleados_creados

    def _print_summary(self, empresas, total_empleados):
        """Imprime un resumen de los datos cargados"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE DATOS CARGADOS'))
        self.stdout.write('='*70)

        self.stdout.write(f'\n📊 Total de empresas creadas: {len(empresas)}')
        for empresa in empresas:
            self.stdout.write(f'   • {empresa.nombre_empresa}')
            self.stdout.write(f'     - Usuario: {empresa.user.username}')
            self.stdout.write(f'     - Email: {empresa.correo_contacto}')
            self.stdout.write(f'     - Password: empresa123')

        self.stdout.write(f'\n👥 Total de empleados creados: {total_empleados}')
        self.stdout.write('   - Password para todos: empleado123')

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✓ Datos cargados exitosamente'))
        self.stdout.write('='*70 + '\n')

        self.stdout.write(self.style.WARNING('\n💡 CREDENCIALES DE ACCESO:'))
        self.stdout.write('   Empresas: username del email (ej: contacto@technova.com)')
        self.stdout.write('   Password: empresa123')
        self.stdout.write('   Empleados: nombre.apellido{N} (ej: carlos.garcia0)')
        self.stdout.write('   Password: empleado123\n')
