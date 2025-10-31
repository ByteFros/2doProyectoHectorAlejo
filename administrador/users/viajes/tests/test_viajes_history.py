from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from users.models import CustomUser, EmpresaProfile, EmpleadoProfile, Viaje, Gasto


class ViajesHistoryIncludeGastosTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.empresa_user = CustomUser.objects.create_user(
            username='empresa',
            email='empresa@test.com',
            password='pass',
            role='EMPRESA'
        )
        self.empresa_profile = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa='Empresa Test',
            nif='B12345678',
            correo_contacto='empresa@test.com'
        )

        self.empleado_user = CustomUser.objects.create_user(
            username='empleado',
            email='empleado@test.com',
            password='pass',
            role='EMPLEADO'
        )
        self.empleado_profile = EmpleadoProfile.objects.create(
            user=self.empleado_user,
            empresa=self.empresa_profile,
            nombre='Juan',
            apellido='Pérez',
            dni='12345678A'
        )

        self.empleado_token = Token.objects.create(user=self.empleado_user).key

        self.viaje = Viaje.objects.create(
            empleado=self.empleado_profile,
            empresa=self.empresa_profile,
            destino='Madrid',
            ciudad='Madrid',
            pais='España',
            es_internacional=False,
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=date(2024, 1, 3),
            estado='REVISADO',
            dias_viajados=3
        )

        Gasto.objects.create(
            empleado=self.empleado_profile,
            empresa=self.empresa_profile,
            viaje=self.viaje,
            concepto='Hotel',
            monto=100,
            estado='APROBADO',
            fecha_gasto=date(2024, 1, 1)
        )
        Gasto.objects.create(
            empleado=self.empleado_profile,
            empresa=self.empresa_profile,
            viaje=self.viaje,
            concepto='Comidas',
            monto=50,
            estado='RECHAZADO',
            fecha_gasto=date(2024, 1, 2)
        )

    def authenticate(self, token=None):
        if token:
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        else:
            self.client.credentials()

    def test_historial_includes_gastos_when_requested(self):
        self.authenticate(self.empleado_token)
        url = reverse('viajes_todos')
        response = self.client.get(f'{url}?include=gastos')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('employee', response.data)
        self.assertIn('company', response.data)
        self.assertIn('trips', response.data)
        self.assertEqual(len(response.data['trips']), 1)
        viaje = response.data['trips'][0]
        self.assertIn('gastos', viaje)
        self.assertEqual(len(viaje['gastos']), 2)
        conceptos = {g['concepto'] for g in viaje['gastos']}
        self.assertSetEqual(conceptos, {'Hotel', 'Comidas'})
        for gasto in viaje['gastos']:
            self.assertIn('comprobante', gasto)
            self.assertIn('comprobante_url', gasto)

    def test_historial_without_include_excludes_gastos(self):
        self.authenticate(self.empleado_token)
        url = reverse('viajes_todos')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('trips', response.data)
        self.assertEqual(len(response.data['trips']), 1)
        self.assertNotIn('gastos', response.data['trips'][0])
