"""
Tests actualizados para la lógica de viajes con los nuevos estados.
"""
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from users.models import (
    EmpresaProfile,
    EmpleadoProfile,
    Viaje,
    DiaViaje,
    Gasto,
)
from users.viajes.services import (
    crear_viaje,
    crear_dias_viaje,
    inicializar_dias_viaje_finalizado,
    procesar_revision_viaje,
)

User = get_user_model()


class ViajesServicesBase(TestCase):
    """Configura empresa y empleado de prueba"""

    def setUp(self):
        empresa_user = User.objects.create_user(
            username="empresa_test",
            email="empresa@test.com",
            password="test123",
            role="EMPRESA",
        )
        self.empresa = EmpresaProfile.objects.create(
            user=empresa_user,
            nombre_empresa="Empresa Test",
            nif="B12345678",
            correo_contacto="empresa@test.com",
        )

        empleado_user = User.objects.create_user(
            username="empleado_test",
            email="empleado@test.com",
            password="test123",
            role="EMPLEADO",
        )
        self.empleado = EmpleadoProfile.objects.create(
            user=empleado_user,
            empresa=self.empresa,
            nombre="Juan",
            apellido="Pérez",
            dni="12345678A",
        )


class CrearViajeServiceTest(ViajesServicesBase):
    """Verifica creación básica de viajes"""

    def test_crear_viaje_establece_en_revision(self):
        inicio = date.today() - timedelta(days=3)
        fin = date.today() - timedelta(days=1)

        viaje = crear_viaje(
            empleado=self.empleado,
            destino="Madrid, España",
            fecha_inicio=inicio,
            fecha_fin=fin,
            motivo="Reunión con cliente",
            empresa_visitada="Cliente Madrid",
            ciudad="Madrid",
            pais="España",
            es_internacional=False,
        )

        self.assertEqual(viaje.estado, "EN_REVISION")
        self.assertEqual(viaje.dias_viajados, 3)
        self.assertEqual(viaje.empresa, self.empresa)


class CrearDiasViajeServiceTest(ViajesServicesBase):
    """Verifica generación de días asociados a un viaje"""

    def test_crear_dias_viaje_generates_expected_dates(self):
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Barcelona, España",
            fecha_inicio=date(2025, 1, 10),
            fecha_fin=date(2025, 1, 12),
            dias_viajados=3,
            estado="EN_REVISION",
        )

        dias = crear_dias_viaje(viaje)

        self.assertEqual(len(dias), 3)
        fechas = [dia.fecha for dia in dias]
        self.assertEqual(
            fechas,
            [date(2025, 1, 10), date(2025, 1, 11), date(2025, 1, 12)],
        )
        self.assertTrue(all(dia.revisado is False for dia in dias))


class InicializarDiasRevisadosTest(ViajesServicesBase):
    """Valida la inicialización masiva para viajes históricos"""

    def test_inicializar_dias_para_viaje_revisado(self):
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Sevilla, España",
            fecha_inicio=date(2024, 5, 1),
            fecha_fin=date(2024, 5, 3),
            dias_viajados=3,
            estado="REVISADO",
        )

        dias = inicializar_dias_viaje_finalizado(viaje, exentos=True)

        self.assertEqual(len(dias), 3)
        self.assertTrue(all(dia.revisado for dia in dias))
        self.assertTrue(all(dia.exento for dia in dias))


class ProcesarRevisionServiceTest(ViajesServicesBase):
    """Cubre la finalización de la revisión de un viaje"""

    def test_procesar_revision_actualiza_estado_y_gastos(self):
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Valencia, España",
            fecha_inicio=date(2024, 6, 1),
            fecha_fin=date(2024, 6, 3),
            dias_viajados=3,
            estado="EN_REVISION",
        )

        dias = crear_dias_viaje(viaje)
        dia_obj = dias[0]

        Gasto.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            viaje=viaje,
            dia=dia_obj,
            concepto="Hotel",
            monto=150.00,
            estado="PENDIENTE",
        )

        resultado = procesar_revision_viaje(
            viaje,
            dias_data=[{"id": dia_obj.id, "exento": False}],
            motivo="Día no exento por exceso de dietas",
            usuario=self.empresa.user,
        )

        viaje.refresh_from_db()
        dia_obj.refresh_from_db()
        gasto = Gasto.objects.get(viaje=viaje)

        self.assertEqual(viaje.estado, "REVISADO")
        self.assertTrue(dia_obj.revisado)
        self.assertFalse(dia_obj.exento)
        self.assertEqual(gasto.estado, "RECHAZADO")
        self.assertEqual(resultado["dias_procesados"], 3)


class ReabrirViajeViewTest(TestCase):
    """Pruebas para reabrir viajes ya revisados"""

    def setUp(self):
        self.client = APIClient()

        self.master_user = User.objects.create_user(
            username="master",
            email="master@test.com",
            password="pass",
            role="MASTER"
        )
        self.master_token = Token.objects.create(user=self.master_user)

        self.empresa_user = User.objects.create_user(
            username="empresa",
            email="empresa@test.com",
            password="pass",
            role="EMPRESA"
        )
        self.empresa = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa="Empresa Test",
            nif="B98765432",
            correo_contacto="empresa@test.com",
            permisos=True
        )

        self.empleado_user = User.objects.create_user(
            username="empleado",
            email="empleado@test.com",
            password="pass",
            role="EMPLEADO"
        )
        self.empleado = EmpleadoProfile.objects.create(
            user=self.empleado_user,
            empresa=self.empresa,
            nombre="Laura",
            apellido="Revisada",
            dni="22334455L"
        )

        self.viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Bilbao, España",
            fecha_inicio=date(2024, 5, 1),
            fecha_fin=date(2024, 5, 3),
            dias_viajados=3,
            estado="REVISADO"
        )

        dias = crear_dias_viaje(self.viaje)
        for dia in dias:
            dia.revisado = True
            dia.save(update_fields=["revisado"])

        self.dia = dias[0]

        self.gasto = Gasto.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            viaje=self.viaje,
            dia=self.dia,
            concepto="Hotel",
            monto=Decimal("120.00"),
            fecha_gasto=self.dia.fecha,
            estado="APROBADO"
        )

        self.reabrir_url = f"/api/users/viajes/{self.viaje.id}/reabrir/"

    def test_master_puede_reabrir_viaje(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.master_token.key}")

        response = self.client.patch(self.reabrir_url)

        self.assertEqual(response.status_code, 200)
        self.viaje.refresh_from_db()
        self.dia.refresh_from_db()
        self.gasto.refresh_from_db()

        self.assertEqual(self.viaje.estado, "EN_REVISION")
        self.assertFalse(self.viaje.dias.filter(revisado=True).exists())
        self.assertEqual(self.gasto.estado, "PENDIENTE")

    def test_no_reabre_si_no_esta_revisado(self):
        self.viaje.estado = "EN_REVISION"
        self.viaje.save(update_fields=['estado'])

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.master_token.key}")
        response = self.client.patch(self.reabrir_url)
        self.assertEqual(response.status_code, 400)
