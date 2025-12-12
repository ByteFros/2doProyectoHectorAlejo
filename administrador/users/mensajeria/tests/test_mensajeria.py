import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import Conversacion, CustomUser, EmpleadoProfile, EmpresaProfile, Mensaje

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
        self.master_token = self._token(self.master_user)

        self.master_user_2 = CustomUser.objects.create_user(
            username='master2',
            email='master2@test.com',
            password='pass',
            role='MASTER'
        )

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
        self.empresa_token = self._token(self.empresa_user)

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
        self.empleado_token = self._token(self.empleado_user)

    def _token(self, user):
        return str(RefreshToken.for_user(user).access_token)

    def test_master_crea_conversacion_con_empleado(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

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
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.empleado_token}')

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

    def test_empleado_contacta_master(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.empleado_token}')

        payload_master = {"user_id": self.master_user.id}
        response = self.client.post(f'{API_BASE}/conversaciones/crear/', payload_master, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Conversacion.objects.count(), 1)

        # no debe permitir duplicado
        response_dup = self.client.post(f'{API_BASE}/conversaciones/crear/', payload_master, format='json')
        self.assertEqual(response_dup.status_code, 400)
        self.assertEqual(Conversacion.objects.count(), 1)

    def test_master_contacta_otro_master(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        payload = {"user_id": self.master_user_2.id}
        response = self.client.post(f'{API_BASE}/conversaciones/crear/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Conversacion.objects.count(), 1)

        # evitar duplicados
        response_dup = self.client.post(f'{API_BASE}/conversaciones/crear/', payload, format='json')
        self.assertEqual(response_dup.status_code, 400)
        self.assertEqual(Conversacion.objects.count(), 1)

    def test_contact_list_for_master(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')

        response = self.client.get(f'{API_BASE}/contacts/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['role'], 'MASTER')
        self.assertIn('masters', response.data)
        self.assertEqual(len(response.data['masters']), 1)
        self.assertEqual(response.data['masters'][0]['user_id'], self.master_user_2.id)
        self.assertIn('companies', response.data)
        self.assertEqual(len(response.data['companies']), 1)

        company = response.data['companies'][0]
        self.assertEqual(company['user']['user_id'], self.empresa_user.id)
        self.assertEqual(len(company['employees']), 1)
        self.assertEqual(company['employees'][0]['user_id'], self.empleado_user.id)

    def test_contact_list_for_empresa(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.empresa_token}')

        response = self.client.get(f'{API_BASE}/contacts/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['role'], 'EMPRESA')
        self.assertEqual(len(response.data['masters']), 2)
        master_ids = {m['user_id'] for m in response.data['masters']}
        self.assertSetEqual(master_ids, {self.master_user.id, self.master_user_2.id})

        companies = response.data['companies']
        self.assertEqual(len(companies), 1)
        self.assertEqual(companies[0]['user']['user_id'], self.empresa_user.id)
        self.assertEqual(len(companies[0]['employees']), 1)
        self.assertEqual(companies[0]['employees'][0]['user_id'], self.empleado_user.id)

    def test_contact_list_for_empleado(self):
        # crear compañero adicional
        coworker_user = CustomUser.objects.create_user(
            username='empleado_coworker',
            email='empleado_coworker@test.com',
            password='pass',
            role='EMPLEADO'
        )
        EmpleadoProfile.objects.create(
            user=coworker_user,
            empresa=self.empresa_profile,
            nombre='Ana',
            apellido='López',
            dni='99999999X'
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.empleado_token}')

        response = self.client.get(f'{API_BASE}/contacts/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['role'], 'EMPLEADO')
        self.assertEqual(len(response.data['masters']), 2)
        master_ids = {m['user_id'] for m in response.data['masters']}
        self.assertSetEqual(master_ids, {self.master_user.id, self.master_user_2.id})
        self.assertEqual(len(response.data['companies']), 1)

        company = response.data['companies'][0]
        self.assertEqual(company['user']['user_id'], self.empresa_user.id)
        coworkers = company['employees']
        self.assertEqual(len(coworkers), 1)
        self.assertEqual(coworkers[0]['user_id'], coworker_user.id)

    def test_unread_flag_is_updated(self):
        conversacion = Conversacion.objects.create()
        conversacion.participantes.add(self.master_user, self.empleado_user)
        Mensaje.objects.create(
            conversacion=conversacion,
            autor=self.master_user,
            contenido="Hola"
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.empleado_token}')

        response = self.client.get(f'{API_BASE}/conversaciones/')
        self.assertEqual(response.status_code, 200)
        convo = next(item for item in response.data if item['id'] == conversacion.id)
        self.assertTrue(convo['has_unread'])

        response_msgs = self.client.get(f'{API_BASE}/conversaciones/{conversacion.id}/mensajes/')
        self.assertEqual(response_msgs.status_code, 200)

        response = self.client.get(f'{API_BASE}/conversaciones/')
        convo = next(item for item in response.data if item['id'] == conversacion.id)
        self.assertFalse(convo['has_unread'])

        payload = {"conversacion_id": conversacion.id, "contenido": "Respuesta"}
        send_resp = self.client.post(f'{API_BASE}/mensajes/enviar/', payload, format='json')
        self.assertEqual(send_resp.status_code, 201)

        response = self.client.get(f'{API_BASE}/conversaciones/')
        convo = next(item for item in response.data if item['id'] == conversacion.id)
        self.assertFalse(convo['has_unread'])

        # Master envía un nuevo mensaje
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.master_token}')
        payload = {"conversacion_id": conversacion.id, "contenido": "Nuevo"}
        master_send = self.client.post(f'{API_BASE}/mensajes/enviar/', payload, format='json')
        self.assertEqual(master_send.status_code, 201)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.empleado_token}')
        response = self.client.get(f'{API_BASE}/conversaciones/')
        convo = next(item for item in response.data if item['id'] == conversacion.id)
        self.assertTrue(convo['has_unread'])


class EnviarMensajeCompressionTest(TestCase):
    def setUp(self):
        self.temp_media = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.temp_media)
        self.override.enable()
        super().setUp()

        self.client = APIClient()

        self.user_a = CustomUser.objects.create_user(
            username='user_a',
            email='user_a@test.com',
            password='pass',
            role='MASTER'
        )
        self.user_b = CustomUser.objects.create_user(
            username='user_b',
            email='user_b@test.com',
            password='pass',
            role='EMPRESA'
        )
        self.token_a = self._token(self.user_a)

        self.conversacion = Conversacion.objects.create()
        self.conversacion.participantes.add(self.user_a, self.user_b)

    def tearDown(self):
        super().tearDown()
        self.override.disable()
        shutil.rmtree(self.temp_media, ignore_errors=True)

    def _token(self, user):
        return str(RefreshToken.for_user(user).access_token)

    def _image_upload(self, size=(3200, 2400), name="photo.jpg"):
        buffer = BytesIO()
        Image.new("RGB", size, (120, 10, 10)).save(buffer, format="JPEG", quality=95)
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")

    def test_envio_con_imagen_se_comprime(self):
        upload = self._image_upload()
        original_size = upload.size

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_a}')
        response = self.client.post(
            f'{API_BASE}/mensajes/enviar/',
            {
                "conversacion_id": self.conversacion.id,
                "contenido": "",
                "archivo": upload
            },
            format='multipart'
        )

        self.assertEqual(response.status_code, 201)
        mensaje = Mensaje.objects.get(id=response.data['id'])
        self.assertTrue(mensaje.archivo.name.endswith('.webp'))
        self.assertLess(mensaje.archivo.size, original_size)

        with Image.open(mensaje.archivo.path) as optimized:
            self.assertLessEqual(max(optimized.size), 1920)

    def test_envio_con_archivo_no_imagen_no_modifica(self):
        payload = SimpleUploadedFile("doc.txt", b"just text", content_type="text/plain")

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_a}')
        response = self.client.post(
            f'{API_BASE}/mensajes/enviar/',
            {
                "conversacion_id": self.conversacion.id,
                "contenido": "",
                "archivo": payload
            },
            format='multipart'
        )

        self.assertEqual(response.status_code, 201)
        mensaje = Mensaje.objects.get(id=response.data['id'])
        self.assertTrue(mensaje.archivo.name.endswith('doc.txt'))
        self.assertEqual(mensaje.archivo.size, payload.size)
