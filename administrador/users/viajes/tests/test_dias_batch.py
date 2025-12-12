from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import CustomUser, DiaViaje, EmpleadoProfile, EmpresaProfile, Gasto
from users.viajes.services import crear_viaje


class DiaViajeBatchReviewAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.master = CustomUser.objects.create_user(
            username='master', email='master@test.com', password='pass', role='MASTER'
        )
        self.master_token = str(RefreshToken.for_user(self.master).access_token)

        self.empresa_user = CustomUser.objects.create_user(
            username='empresa', email='empresa@test.com', password='pass', role='EMPRESA'
        )
        self.empresa_profile = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa='Empresa Test',
            nif='B12345678',
            correo_contacto='empresa@test.com'
        )

        self.empleado_user = CustomUser.objects.create_user(
            username='empleado', email='empleado@test.com', password='pass', role='EMPLEADO'
        )
        self.empleado = EmpleadoProfile.objects.create(
            user=self.empleado_user,
            empresa=self.empresa_profile,
            nombre='Juan',
            apellido='Pérez',
            dni='12345678A'
        )

        self.viaje = crear_viaje(
            empleado=self.empleado,
            destino='Madrid',
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 1, 5),
            motivo='Reunión'
        )
        self.dias = list(DiaViaje.objects.filter(viaje=self.viaje))

    def authenticate(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_master_actualiza_varios_dias(self):
        self.authenticate(self.master_token)
        target_ids = [self.dias[0].id, self.dias[1].id]
        # Crear un gasto ligado al primer día para validar actualización
        Gasto.objects.create(
            empleado=self.empleado,
            empresa=self.empresa_profile,
            viaje=self.viaje,
            dia=self.dias[0],
            concepto='Hotel',
            monto=100,
            estado='PENDIENTE'
        )

        url = reverse('dias-review-batch')
        payload = {'dia_ids': target_ids, 'exento': False}
        response = self.client.put(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        updated = DiaViaje.objects.filter(id__in=target_ids)
        self.assertTrue(all(d.revisado for d in updated))
        self.assertTrue(all(d.exento is False for d in updated))
        gasto = Gasto.objects.get(dia=self.dias[0])
        self.assertEqual(gasto.estado, 'RECHAZADO')

    def test_empresa_no_puede_modificar_dias_de_otra_empresa(self):
        otra_empresa_user = CustomUser.objects.create_user(
            username='empresa2', email='empresa2@test.com', password='pass', role='EMPRESA'
        )
        EmpresaProfile.objects.create(
            user=otra_empresa_user,
            nombre_empresa='Otra',
            nif='B99999999',
            correo_contacto='otra@test.com'
        )
        token = str(RefreshToken.for_user(otra_empresa_user).access_token)
        self.authenticate(token)

        url = reverse('dias-review-batch')
        payload = {'dia_ids': [self.dias[0].id], 'exento': True}
        response = self.client.put(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_batch_rejects_invalid_ids(self):
        self.authenticate(self.master_token)
        url = reverse('dias-review-batch')
        payload = {'dia_ids': [99999], 'exento': True}
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
