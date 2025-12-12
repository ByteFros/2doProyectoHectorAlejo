import shutil
import tempfile
from datetime import date
from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import CustomUser, EmpleadoProfile, EmpresaProfile, Gasto, Viaje

API_BASE = "/api/users"


class GastoAttachmentCompressionTest(TestCase):
    def setUp(self):
        self.temp_media = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.temp_media)
        self.override.enable()
        super().setUp()

        self.client = APIClient()

        self.empresa_user = CustomUser.objects.create_user(
            username="empresa_gastos",
            email="empresa_gastos@test.com",
            password="pass",
            role="EMPRESA",
        )
        self.empresa = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa="Empresa Gastos",
            nif="B76543210",
            correo_contacto="empresa_gastos@test.com",
        )

        self.empleado_user = CustomUser.objects.create_user(
            username="empleado_gastos",
            email="empleado_gastos@test.com",
            password="pass",
            role="EMPLEADO",
        )
        self.empleado = EmpleadoProfile.objects.create(
            user=self.empleado_user,
            empresa=self.empresa,
            nombre="Carlos",
            apellido="Sánchez",
            dni="11223344Z",
        )

        self.token = self._token(self.empleado_user)

        self.viaje = Viaje.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            destino="Barcelona",
            fecha_inicio=date(2025, 1, 10),
            fecha_fin=date(2025, 1, 12),
            dias_viajados=3,
            estado="EN_REVISION",
        )

    def tearDown(self):
        super().tearDown()
        self.override.disable()
        shutil.rmtree(self.temp_media, ignore_errors=True)

    def _token(self, user):
        return str(RefreshToken.for_user(user).access_token)

    def _image_upload(self, size=(3200, 2400), name="ticket.jpg"):
        buffer = BytesIO()
        Image.new("RGB", size, (50, 80, 120)).save(buffer, format="JPEG", quality=95)
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")

    def test_crear_gasto_comprime_comprobante(self):
        upload = self._image_upload()
        original_size = upload.size

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.post(
            f"{API_BASE}/gastos/new/",
            {
                "viaje_id": str(self.viaje.id),
                "concepto": "Taxi aeropuerto",
                "monto": "45.10",
                "fecha_gasto": str(self.viaje.fecha_inicio),
                "comprobante": upload,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        gasto = Gasto.objects.get(id=response.data["id"])
        self.assertTrue(gasto.comprobante.name.endswith(".webp"))
        self.assertLess(gasto.comprobante.size, original_size)

    def test_actualizar_gasto_reemplaza_con_compresion(self):
        gasto = Gasto.objects.create(
            empleado=self.empleado,
            empresa=self.empresa,
            viaje=self.viaje,
            concepto="Cena",
            monto=Decimal("30.00"),
            estado="PENDIENTE",
        )

        upload = self._image_upload(name="nuevo.png")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.patch(
            f"{API_BASE}/gastos/edit/{gasto.id}/",
            {"comprobante": upload},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        gasto.refresh_from_db()
        self.assertTrue(gasto.comprobante.name.endswith(".webp"))

    def test_rechaza_archivos_mayores_a_limite(self):
        big_payload = SimpleUploadedFile(
            "huge.jpg",
            b"a" * (10 * 1024 * 1024 + 1),
            content_type="image/jpeg",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.post(
            f"{API_BASE}/gastos/new/",
            {
                "viaje_id": str(self.viaje.id),
                "concepto": "Hotel",
                "monto": "120.00",
                "fecha_gasto": str(self.viaje.fecha_inicio),
                "comprobante": big_payload,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("comprobante", response.data)
        self.assertIn("10 MB", response.data["comprobante"][0])
