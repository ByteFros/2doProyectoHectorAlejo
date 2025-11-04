from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from users.models import CustomUser, EmpresaProfile, EmpleadoProfile, Viaje


class TripsPerMonthReportTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.master = CustomUser.objects.create_user(
            username='master',
            email='master@example.com',
            password='pass',
            role='MASTER'
        )
        self.master_token = Token.objects.create(user=self.master).key

        empresa_user = CustomUser.objects.create_user(
            username='empresa',
            email='empresa@example.com',
            password='pass',
            role='EMPRESA'
        )
        self.empresa_profile = EmpresaProfile.objects.create(
            user=empresa_user,
            nombre_empresa='Empresa Test',
            nif='B12345678',
            correo_contacto='empresa@example.com'
        )

        empleado_user = CustomUser.objects.create_user(
            username='empleado',
            email='empleado@example.com',
            password='pass',
            role='EMPLEADO'
        )
        self.empleado_profile = EmpleadoProfile.objects.create(
            user=empleado_user,
            empresa=self.empresa_profile,
            nombre='Juan',
            apellido='Pérez',
            dni='12345678A'
        )

        # Enero: 1 pendiente, 1 revisado
        Viaje.objects.create(
            empleado=self.empleado_profile,
            empresa=self.empresa_profile,
            destino='Madrid',
            fecha_inicio=date(2025, 1, 10),
            fecha_fin=date(2025, 1, 12),
            estado='EN_REVISION'
        )
        Viaje.objects.create(
            empleado=self.empleado_profile,
            empresa=self.empresa_profile,
            destino='Barcelona',
            fecha_inicio=date(2025, 1, 15),
            fecha_fin=date(2025, 1, 16),
            estado='REVISADO'
        )

        # Febrero: 1 revisado
        Viaje.objects.create(
            empleado=self.empleado_profile,
            empresa=self.empresa_profile,
            destino='Valencia',
            fecha_inicio=date(2025, 2, 5),
            fecha_fin=date(2025, 2, 7),
            estado='REVISADO'
        )

        # Marzo: 1 reabierto (pendiente)
        Viaje.objects.create(
            empleado=self.empleado_profile,
            empresa=self.empresa_profile,
            destino='Sevilla',
            fecha_inicio=date(2025, 3, 1),
            fecha_fin=date(2025, 3, 3),
            estado='REABIERTO'
        )

    def authenticate(self, token=None):
        if token:
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        else:
            self.client.credentials()

    def test_report_returns_pending_and_reviewed_counts(self):
        self.authenticate(self.master_token)
        url = reverse('trips-per-month')
        response = self.client.get(url, {'year': '2025'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['year'], '2025')

        data_by_month = {item['month']: item for item in response.data['data']}

        january = data_by_month['2025-01']
        self.assertEqual(january['totalTrips'], 2)
        self.assertEqual(january['pendingTrips'], 1)
        self.assertEqual(january['reviewedTrips'], 1)

        february = data_by_month['2025-02']
        self.assertEqual(february['totalTrips'], 1)
        self.assertEqual(february['pendingTrips'], 0)
        self.assertEqual(february['reviewedTrips'], 1)

        march = data_by_month['2025-03']
        self.assertEqual(march['totalTrips'], 1)
        self.assertEqual(march['pendingTrips'], 1)
        self.assertEqual(march['reviewedTrips'], 0)
