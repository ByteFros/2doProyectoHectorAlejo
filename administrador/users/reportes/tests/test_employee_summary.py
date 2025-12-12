from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import CustomUser, DiaViaje, EmpleadoProfile, EmpresaProfile, Viaje


class EmployeeSummaryReportTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.master = CustomUser.objects.create_user(
            username='master',
            email='master@example.com',
            password='pass',
            role='MASTER'
        )
        self.master_token = str(RefreshToken.for_user(self.master).access_token)

        self.empresa_user = CustomUser.objects.create_user(
            username='empresa',
            email='empresa@example.com',
            password='pass',
            role='EMPRESA'
        )
        self.empresa_profile = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa='Empresa Test',
            nif='B12345678',
            correo_contacto='empresa@example.com'
        )
        self.empresa_token = str(RefreshToken.for_user(self.empresa_user).access_token)

        self.employee_user = CustomUser.objects.create_user(
            username='empleado',
            email='empleado@example.com',
            password='pass',
            role='EMPLEADO'
        )
        self.employee_profile = EmpleadoProfile.objects.create(
            user=self.employee_user,
            empresa=self.empresa_profile,
            nombre='Juan',
            apellido='Pérez',
            dni='12345678A'
        )
        self.employee_token = str(RefreshToken.for_user(self.employee_user).access_token)

        # Crear viajes y días para el empleado
        today = timezone.now().date()
        reviewed_trip = Viaje.objects.create(
            empleado=self.employee_profile,
            empresa=self.empresa_profile,
            destino='Madrid',
            fecha_inicio=today - timedelta(days=5),
            fecha_fin=today - timedelta(days=3),
            estado='REVISADO'
        )
        DiaViaje.objects.create(viaje=reviewed_trip, fecha=today - timedelta(days=5), exento=True)
        DiaViaje.objects.create(viaje=reviewed_trip, fecha=today - timedelta(days=4), exento=False)

        Viaje.objects.create(
            empleado=self.employee_profile,
            empresa=self.empresa_profile,
            destino='Barcelona',
            fecha_inicio=today + timedelta(days=1),
            fecha_fin=today + timedelta(days=3),
            estado='EN_REVISION'
        )

    def authenticate(self, token=None):
        if token:
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        else:
            self.client.credentials()

    def test_employee_summary_endpoint_for_employee(self):
        self.authenticate(self.employee_token)
        url = reverse('employee-trips-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'EMPLEADO')
        self.assertEqual(response.data['summary']['reviewedTrips'], 1)
        self.assertEqual(response.data['summary']['pendingTrips'], 1)
        self.assertEqual(response.data['summary']['exemptDays'], 1)
        self.assertEqual(response.data['summary']['nonExemptDays'], 1)

    def test_employee_summary_endpoint_for_empresa(self):
        self.authenticate(self.empresa_token)
        url = reverse('employee-trips-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['trips'], 2)
        self.assertEqual(response.data[0]['exemptDays'], 1)
        self.assertEqual(response.data[0]['nonExemptDays'], 1)

    def test_employee_summary_endpoint_forbidden_for_master(self):
        self.authenticate(self.master_token)
        url = reverse('employee-trips-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
