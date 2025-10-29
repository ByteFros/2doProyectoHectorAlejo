from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from users.models import CustomUser, EmpresaProfile, EmpleadoProfile, Conversacion


API_BASE = '/api/users'


class ConversacionCreationTest(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.master_user = CustomUser.objects.create_user(
            username='master',
            email='master@test.com',
            password='pass',
            role='MASTER'
        )
        self.master_token = Token.objects.create(user=self.master_user)

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
            correo_contacto='contacto@empresa.com',
            permisos=True
        )
        self.empresa_token = Token.objects.create(user=self.empresa_user)

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
        self.empleado_token = Token.objects.create(user=self.empleado_user)

    def test_master_crea_conversacion_con_empleado(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.master_token.key}')

        payload = {"user_id": self.empleado_user.id}
        response = self.client.post(f'{API_BASE}/conversaciones/crear/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Conversacion.objects.count(), 1)

        # segundo intento debe fallar
        response2 = self.client.post(f'{API_BASE}/conversaciones/crear/', payload, format='json')
        self.assertEqual(response2.status_code, 400)
        self.assertEqual(Conversacion.objects.count(), 1)
        self.assertIn('Ya existe una conversación', response2.data.get('error', ''))

    def test_empleado_contacta_empresa_y_compañero(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.empleado_token.key}')

        # conversación con empresa
        payload_empresa = {"user_id": self.empresa_user.id}
        resp_empresa = self.client.post(f'{API_BASE}/conversaciones/crear/', payload_empresa, format='json')
        self.assertEqual(resp_empresa.status_code, 201)
        self.assertEqual(Conversacion.objects.count(), 1)

        # conversación con compañero
        companero_user = CustomUser.objects.create_user(
            username='empleado2',
            email='empleado2@test.com',
            password='pass',
            role='EMPLEADO'
        )
        EmpleadoProfile.objects.create(
            user=companero_user,
            empresa=self.empresa_profile,
            nombre='Ana',
            apellido='López',
            dni='87654321Z'
        )

        payload_companero = {"user_id": companero_user.id}
        resp_comp = self.client.post(f'{API_BASE}/conversaciones/crear/', payload_companero, format='json')
        self.assertEqual(resp_comp.status_code, 201)
        self.assertEqual(Conversacion.objects.count(), 2)

        # intentar duplicar conversación con compañero debe fallar
        resp_dup = self.client.post(f'{API_BASE}/conversaciones/crear/', payload_companero, format='json')
        self.assertEqual(resp_dup.status_code, 400)
        self.assertEqual(Conversacion.objects.count(), 2)
