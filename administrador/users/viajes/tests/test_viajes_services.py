"""
Tests actualizados para la lógica de viajes con los nuevos estados.
"""
import shutil
import tempfile
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import (
    EmpleadoProfile,
    EmpresaProfile,
    Gasto,
    Viaje,
)
from users.viajes.services import (
    crear_dias_viaje,
    crear_viaje,
    inicializar_dias_viaje_finalizado,
    procesar_revision_viaje,
)

User = get_user_model()


def get_access_token(user):
    return str(RefreshToken.for_user(user).access_token)


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
            usuario=self.empresa.user,
        )

        viaje.refresh_from_db()
        dia_obj.refresh_from_db()
        gasto = Gasto.objects.get(viaje=viaje)
        self.empresa.refresh_from_db()

        self.assertEqual(viaje.estado, "REVISADO")
        self.assertTrue(dia_obj.revisado)
        self.assertFalse(dia_obj.exento)
        self.assertEqual(gasto.estado, "RECHAZADO")
        self.assertEqual(resultado["dias_procesados"], 3)
        self.assertTrue(self.empresa.has_pending_review_changes)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CambiarEstadoViajeViewTest(TestCase):
    """Pruebas para transiciones de estado de viajes (revisión y reapertura)"""

    def setUp(self):
        self.client = APIClient()

        self.master_user = User.objects.create_user(
            username="master",
            email="master@test.com",
            password="pass",
            role="MASTER"
        )
        self.master_token = get_access_token(self.master_user)

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
        self.empleado_token = get_access_token(self.empleado_user)

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

        self.transition_url = f"/api/users/viajes/{self.viaje.id}/transition/"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_master_puede_finalizar_revision(self):
        self.viaje.estado = "EN_REVISION"
        self.viaje.save(update_fields=['estado'])

        self.dia.exento = False
        self.dia.revisado = True
        self.dia.save(update_fields=['exento', 'revisado'])

        self.gasto.estado = "RECHAZADO"
        self.gasto.save(update_fields=['estado'])

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.master_token}")
        response = self.client.post(
            self.transition_url,
            {
                "target_state": "REVISADO",
            },
            format='json'
        )
        self.assertEqual(response.status_code, 200)

        self.viaje.refresh_from_db()
        self.dia.refresh_from_db()
        self.gasto.refresh_from_db()
        self.empresa.refresh_from_db()

        self.assertEqual(self.viaje.estado, "REVISADO")
        self.assertTrue(self.dia.revisado)
        self.assertFalse(self.dia.exento)
        self.assertEqual(self.gasto.estado, "RECHAZADO")
        self.assertEqual(response.data["resultado"]["dias_no_exentos"], 1)
        self.assertTrue(self.empresa.has_pending_review_changes)

    def test_no_puede_finalizar_con_dias_pendientes(self):
        self.viaje.estado = "EN_REVISION"
        self.viaje.save(update_fields=['estado'])

        self.dia.revisado = False
        self.dia.save(update_fields=['revisado'])

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.master_token}")
        response = self.client.post(
            self.transition_url,
            {"target_state": "REVISADO"},
            format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(self.dia.fecha.isoformat(), response.data.get("error", ""))

    def _reabrir_viaje(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.master_token}")

        response = self.client.post(
            self.transition_url,
            {"target_state": "REABIERTO"},
            format='json'
        )

        self.viaje.refresh_from_db()
        self.dia.refresh_from_db()
        self.gasto.refresh_from_db()
        self.empresa.refresh_from_db()
        self.client.credentials()
        return response

    def test_master_puede_reabrir_viaje(self):
        response = self._reabrir_viaje()

        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.viaje.estado, "REABIERTO")
        self.assertFalse(self.viaje.dias.filter(revisado=True).exists())
        self.assertEqual(self.gasto.estado, "PENDIENTE")
        self.assertTrue(self.empresa.has_pending_review_changes)

    def test_no_reabre_si_no_esta_revisado(self):
        self.viaje.estado = "EN_REVISION"
        self.viaje.save(update_fields=['estado'])

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.master_token}")
        response = self.client.post(
            f"/api/users/viajes/{self.viaje.id}/transition/",
            {"target_state": "REABIERTO"},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_empleado_puede_crear_gasto_en_reabierto(self):
        self._reabrir_viaje()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.empleado_token}")
        response = self.client.post(
            "/api/users/gastos/new/",
            {
                "viaje_id": str(self.viaje.id),
                "concepto": "Taxi",
                "monto": "30.00",
                "fecha_gasto": str(self.dia.fecha),
            },
            format='multipart'
        )
        self.assertEqual(response.status_code, 201)

    def test_empleado_puede_modificar_monto_en_reabierto(self):
        self._reabrir_viaje()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.empleado_token}")
        response = self.client.patch(
            f"/api/users/gastos/edit/{self.gasto.id}/",
            {"monto": "150.00"},
            format='multipart'
        )
        self.assertEqual(response.status_code, 200)
        self.gasto.refresh_from_db()
        self.assertEqual(str(self.gasto.monto), '150.00')

    def test_empleado_puede_adjuntar_comprobante_en_reabierto(self):
        self._reabrir_viaje()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.empleado_token}")
        archivo = SimpleUploadedFile("ticket.pdf", b"fake pdf content", content_type="application/pdf")
        response = self.client.patch(
            f"/api/users/gastos/edit/{self.gasto.id}/",
            {"comprobante": archivo},
            format='multipart'
        )
        self.assertEqual(response.status_code, 200)
        self.gasto.refresh_from_db()
        self.assertTrue(self.gasto.comprobante.name.endswith("ticket.pdf"))

    def test_aprobar_gasto_marca_pendiente(self):
        self.empresa.has_pending_review_changes = False
        self.empresa.save(update_fields=["has_pending_review_changes"])

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.master_token}")
        response = self.client.put(
            f"/api/users/gastos/{self.gasto.id}/",
            {"estado": "RECHAZADO"},
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.empresa.refresh_from_db()
        self.assertTrue(self.empresa.has_pending_review_changes)


class EliminarViajeViewTest(TestCase):
    """Pruebas para eliminación de viajes"""

    def setUp(self):
        self.client = APIClient()

        self.master_user = User.objects.create_user(
            username="master_del",
            email="master_del@test.com",
            password="pass",
            role="MASTER"
        )
        self.master_token = get_access_token(self.master_user)

        self.empresa_user = User.objects.create_user(
            username="empresa_del",
            email="empresa_del@test.com",
            password="pass",
            role="EMPRESA"
        )
        self.empresa = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa="Empresa Delete",
            nif="B99999999",
            correo_contacto="empresa_del@test.com",
        )
        self.empresa_token = get_access_token(self.empresa_user)

        self.empleado_user = User.objects.create_user(
            username="empleado_del",
            email="empleado_del@test.com",
            password="pass",
            role="EMPLEADO"
        )
        self.empleado = EmpleadoProfile.objects.create(
            user=self.empleado_user,
            empresa=self.empresa,
            nombre="Luis",
            apellido="García",
            dni="55555555A",
        )
        self.empleado_token = get_access_token(self.empleado_user)

        self.viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Madrid, España",
            fecha_inicio=date(2025, 2, 1),
            fecha_fin=date(2025, 2, 3),
            dias_viajados=3,
            estado="EN_REVISION",
        )

    def _delete(self, token, viaje_id=None):
        viaje_id = viaje_id or self.viaje.id
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return self.client.delete(f"/api/users/viajes/{viaje_id}/")

    def test_empleado_elimina_viaje_en_revision(self):
        response = self._delete(self.empleado_token)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Viaje.objects.filter(id=self.viaje.id).exists())

    def test_empleado_no_puede_eliminar_viaje_revisado(self):
        self.viaje.estado = "REVISADO"
        self.viaje.save(update_fields=['estado'])

        response = self._delete(self.empleado_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Viaje.objects.filter(id=self.viaje.id).exists())

    def test_empleado_no_puede_eliminar_viaje_de_otro(self):
        otro_user = User.objects.create_user(
            username="empleado_otro",
            email="empleado_otro@test.com",
            password="pass",
            role="EMPLEADO"
        )
        EmpleadoProfile.objects.create(
            user=otro_user,
            empresa=self.empresa,
            nombre="Ana",
            apellido="López",
            dni="55555555B",
        )
        otro_token = get_access_token(otro_user)

        response = self._delete(otro_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Viaje.objects.filter(id=self.viaje.id).exists())

    def test_master_puede_eliminar_viaje_revisado(self):
        self.viaje.estado = "REVISADO"
        self.viaje.save(update_fields=['estado'])

        response = self._delete(self.master_token)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Viaje.objects.filter(id=self.viaje.id).exists())

    def test_empresa_elimina_viaje_en_revision(self):
        response = self._delete(self.empresa_token)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Viaje.objects.filter(id=self.viaje.id).exists())
