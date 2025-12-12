from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from users.common.services import ensure_company_is_up_to_date
from users.models import (
    CustomUser,
    DiaViaje,
    EmpleadoProfile,
    EmpresaProfile,
    Gasto,
    Viaje,
)


class CompanyTripsVisibilityTestCase(APITestCase):
    def setUp(self):
        self.empresa_user = CustomUser.objects.create_user(
            username="empresa_snap",
            email="empresa_snap@example.com",
            password="test1234",
            role="EMPRESA",
        )
        self.empresa = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa="Empresa Snapshot",
            nif="B00000001",
            correo_contacto="contacto@snapshot.com",
            permisos=True,
        )

        empleado_user = CustomUser.objects.create_user(
            username="empleado_snap",
            email="empleado_snap@example.com",
            password="test1234",
            role="EMPLEADO",
        )
        self.empleado = EmpleadoProfile.objects.create(
            user=empleado_user,
            empresa=self.empresa,
            nombre="Empleado",
            apellido="Snapshot",
            dni="12345678Z",
        )

        fecha_inicio = date.today()
        fecha_fin = fecha_inicio + timedelta(days=1)

        self.viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Madrid",
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado="REVISADO",
            motivo="Pruebas",
            dias_viajados=2,
        )

        dia_inicio = DiaViaje.objects.create(
            viaje=self.viaje,
            fecha=fecha_inicio,
            exento=True,
            revisado=True,
        )
        DiaViaje.objects.create(
            viaje=self.viaje,
            fecha=fecha_fin,
            exento=False,
            revisado=True,
        )

        self.gasto = Gasto.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            viaje=self.viaje,
            dia=dia_inicio,
            concepto="Hotel",
            monto=Decimal("120.50"),
            estado="APROBADO",
            fecha_gasto=fecha_inicio,
        )

        # Generar snapshots iniciales
        ensure_company_is_up_to_date(self.empresa, current_time=timezone.now())

        # Alterar datos reales después de generar snapshots para simular cambios pendientes
        self.viaje.dias_viajados = 5
        self.viaje.save(update_fields=["dias_viajados"])

        self.gasto.estado = "RECHAZADO"
        self.gasto.save(update_fields=["estado"])

        self.pending_trip = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Barcelona",
            fecha_inicio=fecha_fin + timedelta(days=7),
            fecha_fin=fecha_fin + timedelta(days=9),
            estado="EN_REVISION",
            motivo="Pruebas pendientes",
            dias_viajados=3,
        )

        for dia in self.viaje.dias.all():
            dia.exento = False
            dia.save(update_fields=["exento"])

    def test_company_summary_uses_snapshots_for_empresa(self):
        self.client.force_authenticate(user=self.empresa_user)
        url = reverse('company-trips-summary') + '?include=empleados'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)

        summary = response.data[0]
        self.assertEqual(summary['empresa'], self.empresa.nombre_empresa)
        self.assertEqual(summary['days'], 2)  # Valor original antes del cambio
        self.assertEqual(summary['exemptDays'], 1)
        self.assertEqual(summary['nonExemptDays'], 1)

        empleados = summary.get('empleados', [])
        self.assertEqual(len(empleados), 1)
        empleado_stats = empleados[0]
        self.assertEqual(empleado_stats['travelDays'], 2)
        self.assertEqual(empleado_stats['exemptDays'], 1)
        self.assertEqual(empleado_stats['nonExemptDays'], 1)

    def test_viajes_all_uses_snapshots_and_live_data(self):
        self.client.force_authenticate(user=self.empresa_user)
        url = reverse('viajes_todos')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        trips = response.data
        self.assertEqual(len(trips), 2)

        revisado = next(trip for trip in trips if trip['id'] == self.viaje.id)
        self.assertEqual(int(revisado['dias_viajados']), 2)

        pendiente = next(trip for trip in trips if trip['id'] == self.pending_trip.id)
        self.assertEqual(pendiente['estado'], 'EN_REVISION')

    def test_viajes_all_include_gastos_snapshot_data(self):
        self.client.force_authenticate(user=self.empresa_user)
        url = reverse('viajes_todos') + '?include=gastos'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        trips = response.data
        revisado = next(trip for trip in trips if trip['id'] == self.viaje.id)
        gastos = revisado.get('gastos', [])
        self.assertEqual(len(gastos), 1)
        self.assertEqual(gastos[0]['estado'], 'APROBADO')

    def test_gastos_list_uses_snapshots(self):
        self.client.force_authenticate(user=self.empresa_user)
        url = reverse('lista_gastos')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.data), 1)
        gasto = response.data[0]
        self.assertEqual(gasto['id'], self.gasto.id)
        self.assertEqual(gasto['estado'], 'APROBADO')
