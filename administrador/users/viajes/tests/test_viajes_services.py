"""
Tests para los servicios de viajes con la nueva lógica de DiaViaje.
Verifica que los DiaViaje se crean correctamente en cada etapa del flujo.
"""
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model

from users.models import CustomUser, EmpresaProfile, EmpleadoProfile, Viaje, DiaViaje, Gasto
from users.viajes.services import (
    crear_viaje,
    iniciar_viaje,
    finalizar_viaje,
    crear_dias_viaje,
    inicializar_dias_viaje_finalizado,
    procesar_revision_viaje
)

User = get_user_model()


class ViajesServicesTestCase(TestCase):
    """Base para tests de servicios de viajes"""

    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear empresa
        self.empresa_user = User.objects.create_user(
            username="empresa_test",
            email="empresa@test.com",
            password="test123",
            role="EMPRESA"
        )
        self.empresa = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa="Test Company",
            nif="B12345678",
            correo_contacto="empresa@test.com",
            permisos=True
        )

        # Crear empleado
        self.empleado_user = User.objects.create_user(
            username="empleado_test",
            email="empleado@test.com",
            password="test123",
            role="EMPLEADO"
        )
        self.empleado = EmpleadoProfile.objects.create(
            user=self.empleado_user,
            empresa=self.empresa,
            nombre="Juan",
            apellido="Pérez",
            dni="12345678A"
        )


class CrearDiasViajeTest(ViajesServicesTestCase):
    """Tests para crear_dias_viaje()"""

    def test_crear_dias_viaje_basico(self):
        """Debe crear DiaViaje para cada día del viaje"""
        # Viaje de 3 días
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Madrid, España",
            fecha_inicio=date(2025, 1, 15),
            fecha_fin=date(2025, 1, 17),
            dias_viajados=3,
            estado="PENDIENTE"
        )

        # Crear días
        dias = crear_dias_viaje(viaje)

        # Verificaciones
        self.assertEqual(len(dias), 3)
        self.assertEqual(viaje.dias.count(), 3)

        # Verificar fechas
        fechas_esperadas = [
            date(2025, 1, 15),
            date(2025, 1, 16),
            date(2025, 1, 17)
        ]
        fechas_creadas = [dia.fecha for dia in dias]
        self.assertEqual(fechas_creadas, fechas_esperadas)

    def test_crear_dias_viaje_un_dia(self):
        """Debe funcionar para viajes de un solo día"""
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Barcelona, España",
            fecha_inicio=date(2025, 2, 1),
            fecha_fin=date(2025, 2, 1),
            dias_viajados=1,
            estado="PENDIENTE"
        )

        dias = crear_dias_viaje(viaje)

        self.assertEqual(len(dias), 1)
        self.assertEqual(dias[0].fecha, date(2025, 2, 1))

    def test_crear_dias_viaje_idempotente(self):
        """Llamar múltiples veces no debe duplicar días"""
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Valencia, España",
            fecha_inicio=date(2025, 3, 1),
            fecha_fin=date(2025, 3, 3),
            dias_viajados=3,
            estado="PENDIENTE"
        )

        # Crear días dos veces
        crear_dias_viaje(viaje)
        crear_dias_viaje(viaje)

        # Solo deben existir 3 días (no 6)
        self.assertEqual(viaje.dias.count(), 3)


class IniciarViajeTest(ViajesServicesTestCase):
    """Tests para iniciar_viaje() con creación de DiaViaje"""

    def test_iniciar_viaje_crea_dias(self):
        """iniciar_viaje() debe crear todos los DiaViaje"""
        # Crear viaje futuro
        fecha_hoy = date.today()
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Sevilla, España",
            fecha_inicio=fecha_hoy,
            fecha_fin=fecha_hoy + timedelta(days=4),
            dias_viajados=5,
            estado="PENDIENTE"
        )

        # Verificar que no hay días antes de iniciar
        self.assertEqual(viaje.dias.count(), 0)

        # Iniciar viaje
        viaje_iniciado = iniciar_viaje(viaje)

        # Verificaciones
        self.assertEqual(viaje_iniciado.estado, "EN_CURSO")
        self.assertEqual(viaje_iniciado.dias.count(), 5)

        # Verificar que todos los días están sin revisar
        for dia in viaje_iniciado.dias.all():
            self.assertFalse(dia.revisado)
            self.assertTrue(dia.exento)  # Default

    def test_iniciar_viaje_fecha_futura_error(self):
        """No se puede iniciar un viaje si la fecha no ha llegado"""
        fecha_futura = date.today() + timedelta(days=30)
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Lisboa, Portugal",
            fecha_inicio=fecha_futura,
            fecha_fin=fecha_futura + timedelta(days=2),
            dias_viajados=3,
            estado="PENDIENTE"
        )

        with self.assertRaises(ValueError) as context:
            iniciar_viaje(viaje)

        self.assertIn("Aún no puedes iniciar", str(context.exception))
        self.assertEqual(viaje.dias.count(), 0)


class FinalizarViajeTest(ViajesServicesTestCase):
    """Tests para finalizar_viaje() con verificación de DiaViaje"""

    def test_finalizar_viaje_con_dias_existentes(self):
        """Debe finalizar si los DiaViaje ya existen"""
        fecha_hoy = date.today()
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Málaga, España",
            fecha_inicio=fecha_hoy,
            fecha_fin=fecha_hoy + timedelta(days=2),
            dias_viajados=3,
            estado="PENDIENTE"
        )

        # Iniciar (crea días)
        viaje = iniciar_viaje(viaje)
        self.assertEqual(viaje.dias.count(), 3)

        # Finalizar
        viaje_finalizado = finalizar_viaje(viaje)

        self.assertEqual(viaje_finalizado.estado, "EN_REVISION")
        self.assertEqual(viaje_finalizado.dias.count(), 3)

    def test_finalizar_viaje_sin_dias_crea_fallback(self):
        """Si faltan días, los crea como fallback (viajes antiguos)"""
        # Simular viaje antiguo sin días (creado antes del cambio)
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Bilbao, España",
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=date(2024, 1, 3),
            dias_viajados=3,
            estado="EN_CURSO"
        )

        # No tiene días
        self.assertEqual(viaje.dias.count(), 0)

        # Finalizar (debe crear días como fallback)
        viaje_finalizado = finalizar_viaje(viaje)

        self.assertEqual(viaje_finalizado.estado, "EN_REVISION")
        self.assertEqual(viaje_finalizado.dias.count(), 3)

    def test_finalizar_viaje_no_en_curso_error(self):
        """Solo se puede finalizar un viaje EN_CURSO"""
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Zaragoza, España",
            fecha_inicio=date.today() + timedelta(days=1),
            fecha_fin=date.today() + timedelta(days=3),
            dias_viajados=3,
            estado="PENDIENTE"
        )

        with self.assertRaises(ValueError) as context:
            finalizar_viaje(viaje)

        self.assertIn("Solo puedes finalizar un viaje en curso", str(context.exception))


class InicializarDiasViajeFinalizadoTest(ViajesServicesTestCase):
    """Tests para inicializar_dias_viaje_finalizado() - nuevo método para scripts"""

    def test_inicializar_dias_finalizado_exentos(self):
        """Debe crear días marcados como exentos y revisados"""
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="París, Francia",
            fecha_inicio=date(2024, 12, 1),
            fecha_fin=date(2024, 12, 5),
            dias_viajados=5,
            estado="FINALIZADO"
        )

        dias = inicializar_dias_viaje_finalizado(viaje, exentos=True)

        self.assertEqual(len(dias), 5)
        for dia in dias:
            self.assertTrue(dia.exento)
            self.assertTrue(dia.revisado)

    def test_inicializar_dias_finalizado_no_exentos(self):
        """Debe crear días marcados como no exentos y revisados"""
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Londres, Reino Unido",
            fecha_inicio=date(2024, 11, 15),
            fecha_fin=date(2024, 11, 18),
            dias_viajados=4,
            estado="FINALIZADO"
        )

        dias = inicializar_dias_viaje_finalizado(viaje, exentos=False)

        self.assertEqual(len(dias), 4)
        for dia in dias:
            self.assertFalse(dia.exento)
            self.assertTrue(dia.revisado)

    def test_inicializar_dias_en_revision(self):
        """Debe funcionar también con viajes EN_REVISION"""
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Berlín, Alemania",
            fecha_inicio=date(2024, 10, 1),
            fecha_fin=date(2024, 10, 3),
            dias_viajados=3,
            estado="EN_REVISION"
        )

        dias = inicializar_dias_viaje_finalizado(viaje)

        self.assertEqual(len(dias), 3)
        self.assertEqual(viaje.dias.count(), 3)

    def test_inicializar_dias_estado_invalido_error(self):
        """Solo funciona con FINALIZADO o EN_REVISION"""
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Roma, Italia",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=2),
            dias_viajados=3,
            estado="PENDIENTE"
        )

        with self.assertRaises(ValueError) as context:
            inicializar_dias_viaje_finalizado(viaje)

        self.assertIn("FINALIZADOS o EN_REVISION", str(context.exception))


class ProcesarRevisionViajeTest(ViajesServicesTestCase):
    """Tests para procesar_revision_viaje() con nuevas validaciones"""

    def test_procesar_revision_valida_dias_completos(self):
        """Debe validar que existen todos los DiaViaje esperados"""
        # Crear viaje con días incompletos (simular error)
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Ámsterdam, Países Bajos",
            fecha_inicio=date(2024, 9, 1),
            fecha_fin=date(2024, 9, 5),
            dias_viajados=5,
            estado="EN_REVISION"
        )

        # Crear solo 2 de 5 días (simular inconsistencia)
        DiaViaje.objects.create(viaje=viaje, fecha=date(2024, 9, 1))
        DiaViaje.objects.create(viaje=viaje, fecha=date(2024, 9, 2))

        dias_data = [
            {'id': viaje.dias.first().id, 'exento': True}
        ]

        # Debe fallar porque faltan días
        with self.assertRaises(ValueError) as context:
            procesar_revision_viaje(
                viaje=viaje,
                dias_data=dias_data,
                motivo="Test",
                usuario=self.empresa_user
            )

        self.assertIn("Faltan días por crear", str(context.exception))
        self.assertIn("Esperados: 5", str(context.exception))
        self.assertIn("Encontrados: 2", str(context.exception))

    def test_procesar_revision_exitosa(self):
        """Debe procesar correctamente con todos los días"""
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Bruselas, Bélgica",
            fecha_inicio=date(2024, 8, 1),
            fecha_fin=date(2024, 8, 3),
            dias_viajados=3,
            estado="EN_REVISION"
        )

        # Crear todos los días
        dias = crear_dias_viaje(viaje)

        # Preparar datos de revisión
        dias_data = [
            {'id': dias[0].id, 'exento': True},
            {'id': dias[1].id, 'exento': False},
            {'id': dias[2].id, 'exento': True}
        ]

        # Procesar revisión
        resultado = procesar_revision_viaje(
            viaje=viaje,
            dias_data=dias_data,
            motivo="Día 2 no justificado",
            usuario=self.empresa_user
        )

        # Verificaciones
        self.assertEqual(resultado['dias_procesados'], 3)
        self.assertEqual(resultado['dias_no_exentos'], 1)
        self.assertTrue(resultado['conversacion_creada'])

        # Verificar estado final
        viaje.refresh_from_db()
        self.assertEqual(viaje.estado, "FINALIZADO")

        # Verificar días marcados como revisados
        for dia in viaje.dias.all():
            self.assertTrue(dia.revisado)


class IntegracionFlujosViajeTest(ViajesServicesTestCase):
    """Tests de integración del flujo completo de viaje"""

    def test_flujo_completo_viaje(self):
        """Test del flujo completo: crear → iniciar → finalizar → revisar"""
        # 1. Crear viaje
        fecha_hoy = date.today()
        viaje = crear_viaje(
            empleado=self.empleado,
            destino="Múnich, Alemania",
            fecha_inicio=fecha_hoy,
            fecha_fin=fecha_hoy + timedelta(days=2),
            motivo="Conferencia",
            ciudad="Múnich",
            pais="Alemania",
            es_internacional=True
        )

        self.assertEqual(viaje.estado, "EN_CURSO")  # Se inicia automáticamente si es hoy
        self.assertEqual(viaje.dias.count(), 0)  # Aún no tiene días

        # 2. Iniciar viaje (crea días)
        viaje = iniciar_viaje(viaje)

        self.assertEqual(viaje.estado, "EN_CURSO")
        self.assertEqual(viaje.dias.count(), 3)

        # 3. Finalizar viaje (pasa a revisión)
        viaje = finalizar_viaje(viaje)

        self.assertEqual(viaje.estado, "EN_REVISION")
        self.assertEqual(viaje.dias.count(), 3)

        # 4. Procesar revisión
        dias = list(viaje.dias.all())
        dias_data = [
            {'id': dias[0].id, 'exento': True},
            {'id': dias[1].id, 'exento': True},
            {'id': dias[2].id, 'exento': True}
        ]

        resultado = procesar_revision_viaje(
            viaje=viaje,
            dias_data=dias_data,
            motivo="Todo correcto",
            usuario=self.empresa_user
        )

        # Verificaciones finales
        viaje.refresh_from_db()
        self.assertEqual(viaje.estado, "FINALIZADO")
        self.assertEqual(resultado['dias_procesados'], 3)
        self.assertEqual(resultado['dias_no_exentos'], 0)

    def test_flujo_viaje_con_gastos(self):
        """Test de flujo con gastos en días específicos"""
        fecha_hoy = date.today()
        viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Zúrich, Suiza",
            fecha_inicio=fecha_hoy,
            fecha_fin=fecha_hoy + timedelta(days=1),
            dias_viajados=2,
            estado="PENDIENTE"
        )

        # Iniciar viaje
        viaje = iniciar_viaje(viaje)
        dias = list(viaje.dias.all())

        # Crear gastos en días específicos
        Gasto.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            viaje=viaje,
            dia=dias[0],
            concepto="Hotel",
            monto=150.00,
            fecha_gasto=dias[0].fecha
        )

        Gasto.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            viaje=viaje,
            dia=dias[1],
            concepto="Comida",
            monto=45.00,
            fecha_gasto=dias[1].fecha
        )

        # Verificar que los gastos están asociados a los días
        self.assertEqual(dias[0].gastos.count(), 1)
        self.assertEqual(dias[1].gastos.count(), 1)

        # Finalizar y revisar
        viaje = finalizar_viaje(viaje)

        dias_data = [
            {'id': dias[0].id, 'exento': True},
            {'id': dias[1].id, 'exento': False}  # Día con gasto rechazado
        ]

        procesar_revision_viaje(
            viaje=viaje,
            dias_data=dias_data,
            motivo="Gasto de comida no justificado",
            usuario=self.empresa_user
        )

        # Verificar estados de gastos
        dias[0].refresh_from_db()
        dias[1].refresh_from_db()

        gasto_aprobado = dias[0].gastos.first()
        gasto_rechazado = dias[1].gastos.first()

        self.assertEqual(gasto_aprobado.estado, "APROBADO")
        self.assertEqual(gasto_rechazado.estado, "RECHAZADO")
