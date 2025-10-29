"""
Tests de integración para ViewSets de empresas y empleados
Actualizado para usar endpoints RESTful con DRF Router
"""
import io
from decimal import Decimal
from datetime import date
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from users.models import CustomUser, EmpresaProfile, EmpleadoProfile, Viaje, Gasto

# Base URL para todos los endpoints
API_BASE_URL = '/api/users'


class EmpresaViewSetIntegrationTest(TestCase):
    """Tests de integración para EmpresaViewSet"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()

        # Crear usuario MASTER
        self.master_user = CustomUser.objects.create_user(
            username="master",
            email="master@test.com",
            password="password123",
            role="MASTER"
        )
        self.master_token = Token.objects.create(user=self.master_user)

    def test_create_empresa_con_nif_valido(self):
        """Test POST /empresas/ - Crear empresa con NIF válido"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.master_token.key}')

        data = {
            "nombre_empresa": "Test SA",
            "nif": "B12345678",
            "correo_contacto": "test@empresa.com",
            "address": "Calle Test 123",
            "city": "Madrid",
            "postal_code": "28001",
            "permisos": False
        }

        response = self.client.post(f'{API_BASE_URL}/empresas/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(EmpresaProfile.objects.filter(nif="B12345678").exists())
        self.assertIn('nombre_empresa', response.data)

    def test_create_empresa_con_nif_invalido(self):
        """Test POST /empresas/ - Crear empresa con NIF inválido"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.master_token.key}')

        data = {
            "nombre_empresa": "Test SA",
            "nif": "INVALID",
            "correo_contacto": "test@empresa.com"
        }

        response = self.client.post(f'{API_BASE_URL}/empresas/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nif', response.data)

    def test_create_empresa_con_nif_duplicado(self):
        """Test POST /empresas/ - NIF duplicado"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.master_token.key}')

        # Crear primera empresa
        data1 = {
            "nombre_empresa": "Primera Empresa",
            "nif": "B12345678",
            "correo_contacto": "empresa1@test.com"
        }
        self.client.post(f'{API_BASE_URL}/empresas/', data1, format='json')

        # Intentar crear segunda con mismo NIF
        data2 = {
            "nombre_empresa": "Segunda Empresa",
            "nif": "B12345678",
            "correo_contacto": "empresa2@test.com"
        }
        response = self.client.post(f'{API_BASE_URL}/empresas/', data2, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nif', response.data)

    def test_list_empresas_solo_master(self):
        """Test GET /empresas/ - Solo MASTER puede listar"""
        # Crear empresa
        empresa_user = CustomUser.objects.create_user(
            username="empresa1",
            email="empresa1@test.com",
            password="pass",
            role="EMPRESA"
        )
        EmpresaProfile.objects.create(
            user=empresa_user,
            nombre_empresa="Test SA",
            nif="B12345678",
            correo_contacto="empresa1@test.com"
        )

        # MASTER puede listar
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.master_token.key}')
        response = self.client.get(f'{API_BASE_URL}/empresas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_empresa(self):
        """Test GET /empresas/{id}/ - Obtener detalle de empresa"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.master_token.key}')

        # Crear empresa
        empresa_user = CustomUser.objects.create_user(
            username="empresa1",
            email="empresa1@test.com",
            password="pass",
            role="EMPRESA"
        )
        empresa = EmpresaProfile.objects.create(
            user=empresa_user,
            nombre_empresa="Test SA",
            nif="B12345678",
            correo_contacto="empresa1@test.com"
        )

        response = self.client.get(f'{API_BASE_URL}/empresas/{empresa.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre_empresa'], "Test SA")

    def test_partial_update_empresa_permisos(self):
        """Test PATCH /empresas/{id}/ - Actualizar permisos de empresa"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.master_token.key}')

        # Crear empresa
        empresa_user = CustomUser.objects.create_user(
            username="empresa1",
            email="empresa1@test.com",
            password="pass",
            role="EMPRESA"
        )
        empresa = EmpresaProfile.objects.create(
            user=empresa_user,
            nombre_empresa="Test SA",
            nif="B12345678",
            correo_contacto="empresa1@test.com",
            permisos=False
        )

        # Actualizar permisos
        response = self.client.patch(f'{API_BASE_URL}/empresas/{empresa.id}/', {'permisos': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar cambio
        empresa.refresh_from_db()
        self.assertTrue(empresa.permisos)

    def test_delete_empresa(self):
        """Test DELETE /empresas/{id}/ - Eliminar empresa"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.master_token.key}')

        # Crear empresa
        empresa_user = CustomUser.objects.create_user(
            username="empresa1",
            email="empresa1@test.com",
            password="pass",
            role="EMPRESA"
        )
        empresa = EmpresaProfile.objects.create(
            user=empresa_user,
            nombre_empresa="Test SA",
            nif="B12345678",
            correo_contacto="empresa1@test.com"
        )

        response = self.client.delete(f'{API_BASE_URL}/empresas/{empresa.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(EmpresaProfile.objects.filter(id=empresa.id).exists())


class EmpleadoViewSetIntegrationTest(TestCase):
    """Tests de integración para EmpleadoViewSet"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()

        # Crear empresa
        self.empresa_user = CustomUser.objects.create_user(
            username="empresa_test",
            email="empresa@test.com",
            password="password123",
            role="EMPRESA"
        )
        self.empresa_profile = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa="Test SA",
            nif="B12345678",
            correo_contacto="empresa@test.com"
        )
        self.empresa_token = Token.objects.create(user=self.empresa_user)

    def test_create_empleado_con_dni_valido(self):
        """Test POST /empleados/ - Crear empleado con DNI válido"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.empresa_token.key}')

        data = {
            "nombre": "Juan",
            "apellido": "Perez",
            "dni": "12345678Z",
            "email": "juan.perez@test.com",
            "salario": "25000.50"
        }

        response = self.client.post(f'{API_BASE_URL}/empleados/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(EmpleadoProfile.objects.filter(dni="12345678Z").exists())
        self.assertEqual(response.data['salario'], '25000.50')

    def test_create_empleado_con_dni_invalido(self):
        """Test POST /empleados/ - DNI inválido"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.empresa_token.key}')

        data = {
            "nombre": "Juan",
            "apellido": "Perez",
            "dni": "12345678A",  # Letra incorrecta
            "email": "juan.perez@test.com"
        }

        response = self.client.post(f'{API_BASE_URL}/empleados/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('dni', response.data)

    def test_create_empleado_sin_email(self):
        """Test POST /empleados/ - Email ahora obligatorio"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.empresa_token.key}')

        data = {
            "nombre": "Juan",
            "apellido": "Perez",
            "dni": "12345678Z"
        }

        response = self.client.post(f'{API_BASE_URL}/empleados/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_create_empleado_con_nie_valido(self):
        """Test POST /empleados/ - Crear con NIE válido"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.empresa_token.key}')

        data = {
            "nombre": "Pedro",
            "apellido": "Lopez",
            "dni": "X1234567L",  # NIE válido: X + 1234567 -> 01234567 % 23 = 11 -> L
            "email": "pedro.lopez@test.com"
        }

        response = self.client.post(f'{API_BASE_URL}/empleados/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(EmpleadoProfile.objects.filter(dni="X1234567L").exists())

    def test_list_empleados(self):
        """Test GET /empleados/ - Listar empleados"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.empresa_token.key}')

        # Crear empleado
        EmpleadoProfile.objects.create(
            user=CustomUser.objects.create_user(
                username="empleado1",
                email="empleado1@test.com",
                password="pass",
                role="EMPLEADO"
            ),
            empresa=self.empresa_profile,
            nombre="Juan",
            apellido="Perez",
            dni="12345678Z"
        )

        response = self.client.get(f'{API_BASE_URL}/empleados/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn('salario', response.data[0])
        self.assertIsNone(response.data[0]['salario'])

    def test_retrieve_empleado(self):
        """Test GET /empleados/{id}/ - Obtener detalle de empleado"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.empresa_token.key}')

        # Crear empleado
        empleado = EmpleadoProfile.objects.create(
            user=CustomUser.objects.create_user(
                username="empleado1",
                email="empleado1@test.com",
                password="pass",
                role="EMPLEADO"
            ),
            empresa=self.empresa_profile,
            nombre="Juan",
            apellido="Perez",
            dni="12345678Z"
        )

        response = self.client.get(f'{API_BASE_URL}/empleados/{empleado.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], "Juan")
        self.assertIn('salario', response.data)

    def test_delete_empleado(self):
        """Test DELETE /empleados/{id}/ - Eliminar empleado"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.empresa_token.key}')

        # Crear empleado
        empleado = EmpleadoProfile.objects.create(
            user=CustomUser.objects.create_user(
                username="empleado1",
                email="empleado1@test.com",
                password="pass",
                role="EMPLEADO"
            ),
            empresa=self.empresa_profile,
            nombre="Juan",
            apellido="Perez",
            dni="12345678Z"
        )

        response = self.client.delete(f'{API_BASE_URL}/empleados/{empleado.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(EmpleadoProfile.objects.filter(id=empleado.id).exists())


class BatchEmployeeUploadIntegrationTest(TestCase):
    """Tests para carga masiva de empleados"""

    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()

        self.master_user = CustomUser.objects.create_user(
            username="master_batch",
            email="master_batch@test.com",
            password="password123",
            role="MASTER"
        )
        self.master_token = Token.objects.create(user=self.master_user)

        # Crear empresa
        self.empresa_user = CustomUser.objects.create_user(
            username="empresa_test",
            email="empresa@test.com",
            password="password123",
            role="EMPRESA"
        )
        self.empresa_profile = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa="Test SA",
            nif="B12345678",
            correo_contacto="empresa@test.com"
        )
        self.empresa_token = Token.objects.create(user=self.empresa_user)

    def test_batch_upload_csv_valido(self):
        """Test POST /empleados/batch-upload/ - CSV válido"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.empresa_token.key}')

        csv_content = """nombre,apellido,dni,email,salario
Juan,Perez,55495559D,juan.perez@test.com,28000
Maria,Garcia,12345678Z,maria.garcia@test.com,30500.50"""

        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'empleados.csv'

        response = self.client.post(f'{API_BASE_URL}/empleados/batch-upload/', {'file': csv_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['empleados_registrados']), 2)
        self.assertEqual(len(response.data['errores']), 0)
        salarios = {emp['dni']: emp['salario'] for emp in response.data['empleados_registrados']}
        self.assertEqual(salarios['55495559D'], '28000.00')
        self.assertEqual(salarios['12345678Z'], '30500.50')

    def test_batch_upload_dni_invalido(self):
        """Test POST /empleados/batch-upload/ - DNI inválido"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.empresa_token.key}')

        csv_content = """nombre,apellido,dni,email,salario
Juan,Perez,55495559A,juan.perez@test.com,25000"""  # Letra incorrecta (debería ser D)

        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'empleados.csv'

        response = self.client.post(f'{API_BASE_URL}/empleados/batch-upload/', {'file': csv_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['empleados_registrados']), 0)
        self.assertGreater(len(response.data['errores']), 0)

    def test_batch_upload_master_con_empresa_id(self):
        """MASTER puede cargar empleados indicando empresa_id"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.master_token.key}')

        csv_content = """nombre,apellido,dni,email,salario
Ana,López,44556677L,ana.lopez@test.com,31000
Luis,Ruiz,55667788Z,luis.ruiz@test.com,33000"""

        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'empleados.csv'

        response = self.client.post(
            f'{API_BASE_URL}/empleados/batch-upload/',
            {'file': csv_file, 'empresa_id': self.empresa_profile.id},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['empleados_registrados']), 2)
        empleados = EmpleadoProfile.objects.filter(empresa=self.empresa_profile)
        self.assertEqual(empleados.count(), 2)

    def test_batch_upload_master_sin_empresa_id(self):
        """MASTER sin empresa_id recibe error 400"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.master_token.key}')

        csv_content = "nombre,apellido,dni,email\nAna,López,44556677B,ana.lopez@test.com"
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'empleados.csv'

        response = self.client.post(
            f'{API_BASE_URL}/empleados/batch-upload/',
            {'file': csv_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PendingReviewsIntegrationTest(TestCase):
    """Tests para endpoint consolidado de viajes pendientes"""

    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()

        # Crear MASTER
        self.master_user = CustomUser.objects.create_user(
            username="master",
            email="master@test.com",
            password="pass",
            role="MASTER"
        )
        self.master_token = Token.objects.create(user=self.master_user)

        # Crear empresa CON permisos
        self.empresa_user = CustomUser.objects.create_user(
            username="empresa",
            email="empresa@test.com",
            password="pass",
            role="EMPRESA"
        )
        self.empresa_profile = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa="Test SA",
            nif="B12345678",
            correo_contacto="empresa@test.com",
            permisos=True  # Tiene permisos
        )
        self.empresa_token = Token.objects.create(user=self.empresa_user)

        # Crear empresa SIN permisos
        self.empresa_sin_permisos_user = CustomUser.objects.create_user(
            username="empresa2",
            email="empresa2@test.com",
            password="pass",
            role="EMPRESA"
        )
        self.empresa_sin_permisos = EmpresaProfile.objects.create(
            user=self.empresa_sin_permisos_user,
            nombre_empresa="Test SA 2",
            nif="B87654321",
            correo_contacto="empresa2@test.com",
            permisos=False  # NO tiene permisos
        )
        self.empresa_sin_permisos_token = Token.objects.create(user=self.empresa_sin_permisos_user)

        # Crear empleado con viaje EN_REVISION
        self.empleado = EmpleadoProfile.objects.create(
            user=CustomUser.objects.create_user(
                username="empleado1",
                email="empleado1@test.com",
                password="pass",
                role="EMPLEADO"
            ),
            empresa=self.empresa_profile,
            nombre="Juan",
            apellido="Perez",
            dni="12345678Z"
        )

        # Crear viaje EN_REVISION
        self.viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa_profile,
            destino="Madrid",
            ciudad="Madrid",
            pais="España",
            fecha_inicio=date(2024, 1, 15),
            fecha_fin=date(2024, 1, 20),
            estado="EN_REVISION",
            dias_viajados=5,
            empresa_visitada="Cliente ABC",
            motivo="Reunión comercial"
        )
        Gasto.objects.create(
            empleado=self.empleado,
            empresa=self.empresa_profile,
            viaje=self.viaje,
            concepto="Hotel",
            monto=Decimal("150.00"),
            estado="APROBADO"
        )
        Gasto.objects.create(
            empleado=self.empleado,
            empresa=self.empresa_profile,
            viaje=self.viaje,
            concepto="Taxi",
            monto=Decimal("30.00"),
            estado="RECHAZADO"
        )

        self.viaje_extra = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa_profile,
            destino="Barcelona",
            ciudad="Barcelona",
            pais="España",
            fecha_inicio=date(2024, 2, 10),
            fecha_fin=date(2024, 2, 12),
            estado="EN_REVISION",
            dias_viajados=3,
            empresa_visitada="Cliente DEF",
            motivo="Seguimiento"
        )
        Gasto.objects.create(
            empleado=self.empleado,
            empresa=self.empresa_profile,
            viaje=self.viaje_extra,
            concepto="Comidas",
            monto=Decimal("80.50"),
            estado="APROBADO"
        )

        self.viaje_revisado = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa_profile,
            destino="Lisboa",
            ciudad="Lisboa",
            pais="Portugal",
            fecha_inicio=date(2023, 11, 5),
            fecha_fin=date(2023, 11, 7),
            estado="REVISADO",
            dias_viajados=3,
            empresa_visitada="Cliente Lisboa",
            motivo="Cierre de proyecto"
        )
        Gasto.objects.create(
            empleado=self.empleado,
            empresa=self.empresa_profile,
            viaje=self.viaje_revisado,
            concepto="Alojamiento",
            monto=Decimal("200.00"),
            estado="APROBADO"
        )

        # Empresa adicional con viaje en revisión para validar filtro por empresa
        self.otra_empresa_user = CustomUser.objects.create_user(
            username="otra_empresa",
            email="otra@empresa.com",
            password="pass",
            role="EMPRESA"
        )
        self.otra_empresa_profile = EmpresaProfile.objects.create(
            user=self.otra_empresa_user,
            nombre_empresa="Otra SA",
            nif="B98765432",
            correo_contacto="otra@empresa.com",
            permisos=True
        )
        otro_empleado = EmpleadoProfile.objects.create(
            user=CustomUser.objects.create_user(
                username="empleado_otro",
                email="empleado_otro@test.com",
                password="pass",
                role="EMPLEADO"
            ),
            empresa=self.otra_empresa_profile,
            nombre="Luis",
            apellido="Lopez",
            dni="98765432Z"
        )
        Viaje.objects.create(
            empleado=otro_empleado,
            empresa=self.otra_empresa_profile,
            destino="Sevilla",
            ciudad="Sevilla",
            pais="España",
            fecha_inicio=date(2024, 3, 1),
            fecha_fin=date(2024, 3, 4),
            estado="EN_REVISION",
            dias_viajados=4,
            empresa_visitada="Cliente GHI",
            motivo="Instalación"
        )

    def test_pending_master_puede_ver(self):
        """Test GET /empleados/pending/ - MASTER puede ver todos"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.master_token.key}')

        response = self.client.get(f'{API_BASE_URL}/empleados/pending/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        nombres = {item['nombre'] for item in response.data}
        self.assertIn("Juan", nombres)
        self.assertIn("Luis", nombres)

    def test_pending_empresa_con_permisos_puede_ver(self):
        """Test GET /empleados/pending/ - EMPRESA con permisos=True puede ver"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.empresa_token.key}')

        response = self.client.get(f'{API_BASE_URL}/empleados/pending/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_pending_empresa_sin_permisos_no_puede_ver(self):
        """Test GET /empleados/pending/ - EMPRESA sin permisos=False no puede ver"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.empresa_sin_permisos_token.key}')

        response = self.client.get(f'{API_BASE_URL}/empleados/pending/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pending_incluye_datos_viaje(self):
        """Test GET /empleados/pending/ - Respuesta incluye datos del viaje"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.master_token.key}')

        response = self.client.get(f'{API_BASE_URL}/empleados/pending/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Buscar al empleado Juan y validar sus dos viajes
        juan = next((item for item in response.data if item['nombre'] == 'Juan'), None)
        self.assertIsNotNone(juan)
        self.assertEqual(len(juan['viajes_pendientes']), 3)

        destinos = {v['destino'] for v in juan['viajes_pendientes']}
        self.assertEqual(destinos, {"Madrid", "Barcelona", "Lisboa"})

        self.assertEqual(juan['descuento_viajes'], '430.50')
        montos_por_destino = {v['destino']: v['descuento_viajes'] for v in juan['viajes_pendientes']}
        self.assertEqual(montos_por_destino['Madrid'], '150.00')
        self.assertEqual(montos_por_destino['Barcelona'], '80.50')
        self.assertEqual(montos_por_destino['Lisboa'], '200.00')

    def test_pending_master_filtra_por_empresa(self):
        """Test GET /empleados/pending/?empresa=ID - filtra por empresa"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.master_token.key}')

        response = self.client.get(f'{API_BASE_URL}/empleados/pending/?empresa={self.empresa_profile.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Asegurar que solo se incluyen viajes de la empresa solicitada
        destinos = {viaje['destino'] for viaje in response.data[0]['viajes_pendientes']}
        self.assertEqual(destinos, {"Madrid", "Barcelona", "Lisboa"})
        self.assertEqual(response.data[0]['descuento_viajes'], '430.50')

        # Al pedir otra empresa, debe devolver los viajes correspondientes
        response_otro = self.client.get(f'{API_BASE_URL}/empleados/pending/?empresa={self.otra_empresa_profile.id}')
        self.assertEqual(response_otro.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_otro.data), 1)
        self.assertEqual(response_otro.data[0]['viajes_pendientes'][0]['destino'], "Sevilla")
        self.assertEqual(response_otro.data[0]['descuento_viajes'], '0.00')


class AuthorizationIntegrationTest(TestCase):
    """Tests de autorización"""

    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()

        # Crear usuario EMPLEADO
        self.empleado_user = CustomUser.objects.create_user(
            username="empleado",
            email="empleado@test.com",
            password="password123",
            role="EMPLEADO"
        )
        self.empleado_token = Token.objects.create(user=self.empleado_user)

    def test_empleado_no_puede_crear_empleados(self):
        """Test POST /empleados/ - EMPLEADO no puede crear"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.empleado_token.key}')

        data = {
            "nombre": "Juan",
            "apellido": "Perez",
            "dni": "12345678Z",
            "email": "juan@test.com"
        }

        response = self.client.post(f'{API_BASE_URL}/empleados/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sin_autenticacion(self):
        """Test POST /empleados/ - Sin autenticación"""
        data = {
            "nombre": "Juan",
            "apellido": "Perez",
            "dni": "12345678Z",
            "email": "juan@test.com"
        }

        response = self.client.post(f'{API_BASE_URL}/empleados/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
