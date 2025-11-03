"""
Tests para el módulo de gestión de contraseñas
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from datetime import timedelta
from users.models import CustomUser, PasswordResetToken


class PasswordManagementTestCase(TestCase):
    """Tests para gestión de contraseñas"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()

        # Crear usuario de prueba
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword123',
            role='EMPLEADO'
        )
        self.user.must_change_password = True
        self.user.save()

        # Crear usuario MASTER
        self.master = CustomUser.objects.create_user(
            username='master',
            email='master@example.com',
            password='masterpass123',
            role='MASTER'
        )
        self.master.must_change_password = False
        self.master.save()

    def test_password_reset_request_valid_email(self):
        """Test: Solicitud de reset con email válido"""
        url = reverse('password_reset_request')
        data = {'email': 'test@example.com'}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Verificar que se creó el token
        token_exists = PasswordResetToken.objects.filter(user=self.user).exists()
        self.assertTrue(token_exists)

    def test_password_reset_request_invalid_email(self):
        """Test: Solicitud de reset con email que no existe"""
        url = reverse('password_reset_request')
        data = {'email': 'noexiste@example.com'}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_password_reset_request_missing_email(self):
        """Test: Solicitud de reset sin email"""
        url = reverse('password_reset_request')
        data = {}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_valid_token(self):
        """Test: Confirmar reset con token válido"""
        # Crear token
        reset_token = PasswordResetToken.objects.create(user=self.user)

        url = reverse('password_reset_confirm')
        data = {
            'token': str(reset_token.token),
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Verificar que la contraseña cambió
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))

        # Verificar que el token fue eliminado
        token_exists = PasswordResetToken.objects.filter(token=reset_token.token).exists()
        self.assertFalse(token_exists)

    def test_password_reset_confirm_invalid_token(self):
        """Test: Confirmar reset con token inválido"""
        url = reverse('password_reset_confirm')
        data = {
            'token': '00000000-0000-0000-0000-000000000000',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_password_reset_confirm_expired_token(self):
        """Test: Confirmar reset con token expirado"""
        # Crear token expirado
        reset_token = PasswordResetToken.objects.create(user=self.user)
        reset_token.expires_at = timezone.now() - timedelta(hours=2)
        reset_token.save()

        url = reverse('password_reset_confirm')
        data = {
            'token': str(reset_token.token),
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('expirado', response.data['error'].lower())

    def test_password_reset_confirm_short_password(self):
        """Test: Confirmar reset con contraseña muy corta"""
        reset_token = PasswordResetToken.objects.create(user=self.user)

        url = reverse('password_reset_confirm')
        data = {
            'token': str(reset_token.token),
            'new_password': 'short',  # Menos de 8 caracteres
            'confirm_password': 'short'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_successful(self):
        """Test: Cambio de contraseña exitoso"""
        # Login
        login_url = reverse('login')
        login_response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'oldpassword123'
        })
        token = login_response.data['token']

        # Cambiar contraseña
        url = reverse('change_password')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertFalse(response.data['must_change_password'])

        # Verificar que la contraseña cambió
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
        self.assertFalse(self.user.must_change_password)

    def test_change_password_wrong_old_password(self):
        """Test: Cambio de contraseña con contraseña actual incorrecta"""
        # Login
        login_url = reverse('login')
        login_response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'oldpassword123'
        })
        token = login_response.data['token']

        # Intentar cambiar con contraseña incorrecta
        url = reverse('change_password')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_change_password_same_as_old(self):
        """Test: Cambio de contraseña igual a la anterior"""
        # Login
        login_url = reverse('login')
        login_response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'oldpassword123'
        })
        token = login_response.data['token']

        # Intentar cambiar a la misma contraseña
        url = reverse('change_password')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'oldpassword123',
            'confirm_password': 'oldpassword123'
        }
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # El serializer devuelve errores por campo
        self.assertTrue('new_password' in response.data or 'error' in response.data)

    def test_change_password_master_allowed(self):
        """Test: Usuario MASTER puede cambiar su contraseña"""
        # Login como master
        login_url = reverse('login')
        login_response = self.client.post(login_url, {
            'username': 'master',
            'password': 'masterpass123'
        })
        token = login_response.data['token']

        # Intentar cambiar contraseña
        url = reverse('change_password')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        data = {
            'old_password': 'masterpass123',
            'new_password': 'newmasterpass123',
            'confirm_password': 'newmasterpass123'
        }
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        # Verificar cambio de contraseña
        self.master.refresh_from_db()
        self.assertTrue(self.master.check_password('newmasterpass123'))
        self.assertFalse(self.master.must_change_password)

    def test_change_password_without_authentication(self):
        """Test: Cambio de contraseña sin autenticación"""
        url = reverse('change_password')
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        response = self.client.put(url, data)

        # DRF puede devolver 401 o 403 dependiendo de la configuración
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_change_password_short_new_password(self):
        """Test: Cambio con nueva contraseña muy corta"""
        # Login
        login_url = reverse('login')
        login_response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'oldpassword123'
        })
        token = login_response.data['token']

        # Intentar cambiar con contraseña corta
        url = reverse('change_password')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'short',  # Menos de 8 caracteres
            'confirm_password': 'short'
        }
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_missing_fields(self):
        """Test: Cambio de contraseña sin campos requeridos"""
        # Login
        login_url = reverse('login')
        login_response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'oldpassword123'
        })
        token = login_response.data['token']

        # Intentar cambiar sin campos
        url = reverse('change_password')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        data = {}
        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
