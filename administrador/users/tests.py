from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import CustomUser, EmpresaProfile, Notificacion


class NotificacionesViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.master = CustomUser.objects.create_user(
            username="master",
            email="master@test.com",
            password="pass",
            role="MASTER"
        )

        empresa_user = CustomUser.objects.create_user(
            username="empresa",
            email="empresa@test.com",
            password="pass",
            role="EMPRESA"
        )
        self.empresa = EmpresaProfile.objects.create(
            user=empresa_user,
            nombre_empresa="Empresa Test",
            nif="B12345678",
            correo_contacto="empresa@test.com"
        )

        self.notificacion = Notificacion.objects.create(
            tipo=Notificacion.TIPO_REVISION_FECHA_LIMITE,
            mensaje="La próxima revisión es el 2025-07-10",
            usuario_destino=empresa_user
        )

    def _authenticate(self, user):
        access = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_master_puede_listar_notificaciones_de_empresa(self):
        self._authenticate(self.master)

        response = self.client.get(
            "/api/users/notificaciones/",
            {"empresa_id": self.empresa.id},
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["mensaje"], self.notificacion.mensaje)

    def test_master_puede_ver_todas_las_notificaciones(self):
        self._authenticate(self.master)

        response = self.client.get("/api/users/notificaciones/", format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["mensaje"], self.notificacion.mensaje)

    def test_no_master_no_puede_listar_otras_notificaciones(self):
        self._authenticate(self.empresa.user)

        response = self.client.get(
            "/api/users/notificaciones/",
            {"user_id": self.master.id},
            format='json'
        )

        self.assertEqual(response.status_code, 403)
