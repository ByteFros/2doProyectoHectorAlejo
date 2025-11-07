"""
Tests para los query parameters 'include' en ViewSets de empresas y empleados.
Prueba la funcionalidad de carga anidada (nested loading) de datos relacionados.
"""
from datetime import date, timedelta
from django.test import TestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient

from users.models import CustomUser, EmpresaProfile, EmpleadoProfile, Viaje

# Base URL para todos los endpoints
API_BASE_URL = '/api/users'


class IncludeParameterTestCase(TestCase):
    """Tests para query parameter 'include' en empresas y empleados"""

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
        self.master_token = self._token(self.master_user)

        # Crear empresa con usuario EMPRESA
        self.empresa_user = CustomUser.objects.create_user(
            username="empresa1",
            email="empresa1@test.com",
            password="password123",
            role="EMPRESA"
        )
        self.empresa_token = self._token(self.empresa_user)
        self.empresa = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa="Empresa Test",
            nif="B12345678",
            correo_contacto="empresa1@test.com",
            permisos=True
        )

        # Crear empleados
        self.empleado1_user = CustomUser.objects.create_user(
            username="empleado1",
            email="empleado1@test.com",
            password="password123",
            role="EMPLEADO"
        )
        self.empleado1 = EmpleadoProfile.objects.create(
            user=self.empleado1_user,
            empresa=self.empresa,
            nombre="Juan",
            apellido="Pérez",
            dni="12345678A",
            salario=30000
        )

        self.empleado2_user = CustomUser.objects.create_user(
            username="empleado2",
            email="empleado2@test.com",
            password="password123",
            role="EMPLEADO"
        )
        self.empleado2 = EmpleadoProfile.objects.create(
            user=self.empleado2_user,
            empresa=self.empresa,
            nombre="María",
            apellido="García",
            dni="87654321B",
            salario=28000
        )

        # Crear viajes para empleado1
        self.viaje1 = Viaje.objects.create(
            empleado=self.empleado1,
            empresa=self.empresa,
            destino="Madrid, España",
            ciudad="Madrid",
            pais="España",
            es_internacional=False,
            fecha_inicio=date.today(),
            fecha_fin=date.today(),
            dias_viajados=1,
            estado="EN_REVISION",
            motivo="Reunión con cliente"
        )

        self.viaje2 = Viaje.objects.create(
            empleado=self.empleado1,
            empresa=self.empresa,
            destino="Barcelona, España",
            ciudad="Barcelona",
            pais="España",
            es_internacional=False,
            fecha_inicio=date.today() + timedelta(days=7),
            fecha_fin=date.today() + timedelta(days=9),
            dias_viajados=3,
            estado="EN_REVISION",
            motivo="Visita a oficina"
        )

        # Crear viaje para empleado2
        self.viaje3 = Viaje.objects.create(
            empleado=self.empleado2,
            empresa=self.empresa,
            destino="París, Francia",
            ciudad="París",
            pais="Francia",
            es_internacional=True,
            fecha_inicio=date.today() + timedelta(days=14),
            fecha_fin=date.today() + timedelta(days=16),
            dias_viajados=3,
            estado="REVISADO",
            motivo="Conferencia internacional"
        )

    def _token(self, user):
        return str(RefreshToken.for_user(user).access_token)


class EmpresaIncludeEmpleadosTest(IncludeParameterTestCase):
    """Tests para GET /empresas/?include=empleados"""

    def test_empresas_sin_include(self):
        """GET /empresas/ sin include - NO debe traer empleados anidados"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        response = self.client.get(f'{API_BASE_URL}/empresas/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)

        # Verificar que NO tiene empleados anidados
        empresa_data = response.data[0]
        self.assertNotIn('empleados', empresa_data)
        self.assertNotIn('empleados_count', empresa_data)

    def test_empresas_con_include_empleados(self):
        """GET /empresas/?include=empleados - DEBE traer empleados anidados"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        response = self.client.get(f'{API_BASE_URL}/empresas/?include=empleados')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)

        # Verificar que SÍ tiene empleados anidados
        empresa_data = response.data[0]
        self.assertIn('empleados', empresa_data)
        self.assertIn('empleados_count', empresa_data)
        self.assertIsInstance(empresa_data['empleados'], list)
        self.assertEqual(empresa_data['empleados_count'], 2)  # 2 empleados creados

        # Verificar estructura de empleado anidado
        if len(empresa_data['empleados']) > 0:
            empleado = empresa_data['empleados'][0]
            self.assertIn('id', empleado)
            self.assertIn('nombre', empleado)
            self.assertIn('apellido', empleado)
            self.assertIn('dni', empleado)
            self.assertIn('email', empleado)
            self.assertIn('username', empleado)
            self.assertIn('salario', empleado)
            # NO debe tener viajes (no se pidió include=empleados.viajes)
            self.assertNotIn('viajes', empleado)

    def test_empresa_detalle_con_include_empleados(self):
        """GET /empresas/{id}/?include=empleados - Detalle con empleados"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        response = self.client.get(
            f'{API_BASE_URL}/empresas/{self.empresa.id}/?include=empleados'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('empleados', response.data)
        self.assertIn('empleados_count', response.data)
        self.assertEqual(response.data['empleados_count'], 2)

        # Verificar que los empleados están en el orden correcto
        empleados = response.data['empleados']
        nombres = [e['nombre'] for e in empleados]
        self.assertIn('Juan', nombres)
        self.assertIn('María', nombres)

    def test_empresa_sin_permisos_include_empleados(self):
        """EMPRESA no puede listar todas las empresas (ni con include)"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.empresa_token}')

        response = self.client.get(f'{API_BASE_URL}/empresas/?include=empleados')

        # EMPRESA no tiene permiso para listar todas las empresas
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class EmpleadoIncludeViajesTest(IncludeParameterTestCase):
    """Tests para GET /empleados/?include=viajes"""

    def test_empleados_sin_include(self):
        """GET /empleados/ sin include - NO debe traer viajes anidados"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        response = self.client.get(f'{API_BASE_URL}/empleados/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)

        # Verificar que NO tiene viajes anidados
        empleado_data = response.data[0]
        self.assertIn('salario', empleado_data)
        self.assertNotIn('viajes', empleado_data)
        self.assertNotIn('viajes_count', empleado_data)

    def test_empleados_con_include_viajes(self):
        """GET /empleados/?include=viajes - DEBE traer viajes anidados"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        response = self.client.get(f'{API_BASE_URL}/empleados/?include=viajes')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)

        # Buscar empleado1 que tiene 2 viajes
        empleado1_data = next(
            (e for e in response.data if e['nombre'] == 'Juan'),
            None
        )
        self.assertIsNotNone(empleado1_data)

        # Verificar que SÍ tiene viajes anidados
        self.assertIn('salario', empleado1_data)
        self.assertEqual(empleado1_data['salario'], '30000.00')
        self.assertIn('viajes', empleado1_data)
        self.assertIn('viajes_count', empleado1_data)
        self.assertIsInstance(empleado1_data['viajes'], list)
        self.assertEqual(empleado1_data['viajes_count'], 2)  # 2 viajes para empleado1

        # Verificar estructura de viaje anidado
        viaje = empleado1_data['viajes'][0]
        self.assertIn('id', viaje)
        self.assertIn('destino', viaje)
        self.assertIn('ciudad', viaje)
        self.assertIn('pais', viaje)
        self.assertIn('es_internacional', viaje)
        self.assertIn('fecha_inicio', viaje)
        self.assertIn('fecha_fin', viaje)
        self.assertIn('estado', viaje)
        self.assertIn('dias_viajados', viaje)
        self.assertIn('motivo', viaje)

    def test_empleado_detalle_con_include_viajes(self):
        """GET /empleados/{id}/?include=viajes - Detalle con viajes"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        response = self.client.get(
            f'{API_BASE_URL}/empleados/{self.empleado1.id}/?include=viajes'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('viajes', response.data)
        self.assertIn('viajes_count', response.data)
        self.assertIn('empresa', response.data)  # Empresa completa anidada
        self.assertEqual(response.data['viajes_count'], 2)

        # Verificar información de empresa anidada
        empresa = response.data['empresa']
        self.assertEqual(empresa['nombre_empresa'], 'Empresa Test')
        self.assertEqual(empresa['nif'], 'B12345678')

        # Verificar viajes
        viajes = response.data['viajes']
        destinos = [v['destino'] for v in viajes]
        self.assertIn('Madrid, España', destinos)
        self.assertIn('Barcelona, España', destinos)

    def test_empleado_sin_viajes_include(self):
        """Empleado sin viajes debe tener lista vacía con include=viajes"""
        # Crear empleado sin viajes
        empleado_sin_viajes_user = CustomUser.objects.create_user(
            username="empleado_sin_viajes",
            email="sin_viajes@test.com",
            password="password123",
            role="EMPLEADO"
        )
        empleado_sin_viajes = EmpleadoProfile.objects.create(
            user=empleado_sin_viajes_user,
            empresa=self.empresa,
            nombre="Pedro",
            apellido="López",
            dni="11111111C"
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        response = self.client.get(
            f'{API_BASE_URL}/empleados/{empleado_sin_viajes.id}/?include=viajes'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('viajes', response.data)
        self.assertIn('viajes_count', response.data)
        self.assertEqual(response.data['viajes_count'], 0)
        self.assertEqual(len(response.data['viajes']), 0)

    def test_empresa_ve_solo_sus_empleados_con_viajes(self):
        """EMPRESA solo ve empleados de su empresa con include=viajes"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.empresa_token}')

        response = self.client.get(f'{API_BASE_URL}/empleados/?include=viajes')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)  # Solo 2 empleados de su empresa

        # Todos deben pertenecer a su empresa
        for empleado in response.data:
            self.assertEqual(empleado['empresa']['id'], self.empresa.id)


class IncludeParameterEdgeCasesTest(IncludeParameterTestCase):
    """Tests de casos borde para query parameter 'include'"""

    def test_include_invalido_ignorado(self):
        """Include con valor inválido debe ignorarse y devolver datos básicos"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        response = self.client.get(f'{API_BASE_URL}/empresas/?include=invalid')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Debe devolver el serializer básico (sin empleados)
        if len(response.data) > 0:
            self.assertNotIn('empleados', response.data[0])

    def test_include_vacio_igual_sin_include(self):
        """include= (vacío) debe comportarse igual que sin include"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        response_sin_include = self.client.get(f'{API_BASE_URL}/empresas/')
        response_con_vacio = self.client.get(f'{API_BASE_URL}/empresas/?include=')

        self.assertEqual(response_sin_include.status_code, status.HTTP_200_OK)
        self.assertEqual(response_con_vacio.status_code, status.HTTP_200_OK)

        # Deben tener la misma estructura
        if len(response_sin_include.data) > 0 and len(response_con_vacio.data) > 0:
            self.assertEqual(
                set(response_sin_include.data[0].keys()),
                set(response_con_vacio.data[0].keys())
            )

    def test_multiple_includes_no_soportados(self):
        """include con múltiples valores separados por coma (futuro)"""
        # Por ahora, solo verificamos que no causa error
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        response = self.client.get(f'{API_BASE_URL}/empresas/?include=empleados,otro')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Como 'empleados' está en el string, debería incluirlo
        if len(response.data) > 0:
            self.assertIn('empleados', response.data[0])

    def test_filtro_empresa_con_include_viajes(self):
        """Combinar filtros con include debe funcionar correctamente"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        response = self.client.get(
            f'{API_BASE_URL}/empleados/?empresa={self.empresa.id}&include=viajes'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

        # Todos deben tener viajes incluidos
        for empleado in response.data:
            self.assertIn('viajes', empleado)
            self.assertIn('viajes_count', empleado)

    def test_search_con_include(self):
        """Buscar empleados con include=viajes debe funcionar"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        response = self.client.get(
            f'{API_BASE_URL}/empleados/?search=Juan&include=viajes'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

        # Debe encontrar a Juan con sus viajes
        juan = response.data[0]
        self.assertEqual(juan['nombre'], 'Juan')
        self.assertIn('viajes', juan)
        self.assertEqual(juan['viajes_count'], 2)


class IncludeParameterPerformanceTest(IncludeParameterTestCase):
    """Tests para verificar optimización de queries con prefetch_related"""

    def test_numero_queries_sin_include(self):
        """Verificar que sin include no se hacen queries extras"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        # Django's assertNumQueries context manager
        from django.test.utils import override_settings
        from django.db import connection
        from django.conf import settings

        with self.settings(DEBUG=True):
            connection.queries_log.clear()
            response = self.client.get(f'{API_BASE_URL}/empresas/')
            num_queries_sin_include = len(connection.queries)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Debe ser un número razonable de queries (1-3 típicamente)
        self.assertLessEqual(num_queries_sin_include, 5)

    def test_numero_queries_con_include(self):
        """Verificar que include usa prefetch_related correctamente"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        from django.db import connection
        from django.conf import settings

        with self.settings(DEBUG=True):
            connection.queries_log.clear()
            response = self.client.get(f'{API_BASE_URL}/empresas/?include=empleados')
            num_queries_con_include = len(connection.queries)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Con prefetch_related debe ser +1 o +2 queries adicionales (no N+1)
        # Típicamente: 1 query empresas + 1 query empleados + 1 query auth
        self.assertLessEqual(num_queries_con_include, 8)
