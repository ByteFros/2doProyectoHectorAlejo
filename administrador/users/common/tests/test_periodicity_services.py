"""
Tests para servicios de publicación diferida de viajes/gastos.
"""
from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.utils.formats import date_format

from users.common.services import (
    get_periodicity_delta,
    mark_company_review_pending,
    sync_company_review_snapshots,
    ensure_company_is_up_to_date,
    sync_company_review_notification,
)
from users.models import (
    CustomUser,
    EmpresaProfile,
    EmpleadoProfile,
    Viaje,
    DiaViaje,
    Gasto,
    ViajeReviewSnapshot,
    GastoReviewSnapshot,
    Notificacion,
)


class PeriodicityServicesTestCase(TestCase):
    def setUp(self):
        self.empresa_user = CustomUser.objects.create_user(
            username="empresa1",
            email="empresa1@example.com",
            password="pass",
            role="EMPRESA",
        )
        self.empresa = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa="Empresa Uno",
            nif="B12345678",
            correo_contacto="contacto@empresa1.com",
            permisos=True,
        )

        self.empleado_user = CustomUser.objects.create_user(
            username="empleado1",
            email="empleado1@example.com",
            password="pass",
            role="EMPLEADO",
        )
        self.empleado = EmpleadoProfile.objects.create(
            user=self.empleado_user,
            empresa=self.empresa,
            nombre="Empleado",
            apellido="Uno",
            dni="12345678Z",
        )

        self.viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Madrid",
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date() + timedelta(days=1),
            estado="REVISADO",
            motivo="Reunión",
            dias_viajados=2,
        )

        DiaViaje.objects.create(
            viaje=self.viaje,
            fecha=self.viaje.fecha_inicio,
            exento=True,
            revisado=True,
        )
        DiaViaje.objects.create(
            viaje=self.viaje,
            fecha=self.viaje.fecha_fin,
            exento=False,
            revisado=True,
        )

        self.gasto_aprobado = Gasto.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            viaje=self.viaje,
            concepto="Hotel",
            monto=Decimal("120.50"),
            estado="APROBADO",
            fecha_gasto=self.viaje.fecha_inicio,
        )
        self.gasto_pendiente = Gasto.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            viaje=self.viaje,
            concepto="Comida",
            monto=Decimal("30.00"),
            estado="PENDIENTE",
            fecha_gasto=self.viaje.fecha_inicio,
        )

    def test_get_periodicity_delta(self):
        delta = get_periodicity_delta(self.empresa)
        self.assertEqual(delta, timedelta(days=90))

        self.empresa.periodicity = EmpresaProfile.PERIODICITY_SEMESTRAL
        delta_semestral = get_periodicity_delta(self.empresa)
        self.assertEqual(delta_semestral, timedelta(days=180))

    def test_mark_company_review_pending_sets_flag_once(self):
        self.assertFalse(self.empresa.has_pending_review_changes)
        mark_company_review_pending(self.empresa, save=False)
        self.assertTrue(self.empresa.has_pending_review_changes)

        # No guardado adicional si ya estaba marcado
        mark_company_review_pending(self.empresa, save=False)
        self.assertTrue(self.empresa.has_pending_review_changes)

    def test_sync_company_review_snapshots_creates_records(self):
        self.empresa.has_pending_review_changes = True
        self.empresa.save(update_fields=["has_pending_review_changes"])

        sync_company_review_snapshots(self.empresa, current_time=timezone.now())

        snapshot = ViajeReviewSnapshot.objects.get(viaje=self.viaje)
        self.assertEqual(snapshot.empresa, self.empresa)
        self.assertEqual(snapshot.empleado, self.empleado)
        self.assertEqual(snapshot.estado, "REVISADO")
        self.assertEqual(snapshot.dias_snapshot.count(), 2)

        gastos_snapshot = GastoReviewSnapshot.objects.filter(viaje_snapshot=snapshot)
        self.assertEqual(gastos_snapshot.count(), 1)
        self.assertEqual(gastos_snapshot.first().gasto, self.gasto_aprobado)
        self.assertFalse(EmpresaProfile.objects.get(pk=self.empresa.pk).has_pending_review_changes)

    def test_ensure_company_is_up_to_date_triggers_sync_and_notification(self):
        past = timezone.now() - timedelta(days=1)
        self.empresa.next_release_at = past
        self.empresa.has_pending_review_changes = True
        self.empresa.save(update_fields=["next_release_at", "has_pending_review_changes"])

        updated = ensure_company_is_up_to_date(self.empresa, current_time=timezone.now())
        self.assertTrue(updated)

        empresa_refreshed = EmpresaProfile.objects.get(pk=self.empresa.pk)
        self.assertIsNotNone(empresa_refreshed.last_release_at)
        self.assertGreater(empresa_refreshed.next_release_at, timezone.now())
        self.assertFalse(empresa_refreshed.force_release)
        self.assertIsNone(empresa_refreshed.manual_release_at)

        notifications = Notificacion.objects.filter(
            usuario_destino=self.empresa_user,
            tipo=Notificacion.TIPO_REVISION_FECHA_LIMITE,
        )
        self.assertEqual(notifications.count(), 1)
        expected_text = date_format(empresa_refreshed.next_release_at, "DATE_FORMAT")
        self.assertIn(expected_text, notifications.first().mensaje)

    def test_sync_company_review_notification_replaces_existing(self):
        limit = timezone.now() + timedelta(days=30)
        first = sync_company_review_notification(self.empresa, limit_datetime=limit)
        self.assertIsNotNone(first)
        self.assertEqual(
            Notificacion.objects.filter(
                usuario_destino=self.empresa_user,
                tipo=Notificacion.TIPO_REVISION_FECHA_LIMITE,
            ).count(),
            1,
        )

        new_limit = limit + timedelta(days=15)
        sync_company_review_notification(self.empresa, limit_datetime=new_limit)
        notifications = Notificacion.objects.filter(
            usuario_destino=self.empresa_user,
            tipo=Notificacion.TIPO_REVISION_FECHA_LIMITE,
        )
        self.assertEqual(notifications.count(), 1)
        self.assertIn(date_format(new_limit, "DATE_FORMAT"), notifications.first().mensaje)
