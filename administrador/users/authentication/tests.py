"""
Tests para el módulo de autenticación
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import CustomUser, EmpresaProfile, EmpleadoProfile


class AuthenticationTestCase(TestCase):
    """Tests para autenticación de usuarios"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()

        # Crear usuario MASTER
        self.master_user = CustomUser.objects.create_user(
            username='master',
            email='master@test.com',
            password='masterpass123',
            role='MASTER'
        )
        self.master_user.must_change_password = False
        self.master_user.save()

        # Crear usuario EMPRESA con perfil
        self.empresa_user = CustomUser.objects.create_user(
            username='empresa_test',
            email='empresa@test.com',
            password='empresapass123',
            role='EMPRESA'
        )
        self.empresa_profile = EmpresaProfile.objects.create(
            user=self.empresa_user,
            nombre_empresa='Empresa Test',
            nif='B12345678',
            correo_contacto='empresa@test.com'
        )

        # Crear usuario EMPLEADO con perfil
        self.empleado_user = CustomUser.objects.create_user(
            username='empleado_test',
            email='empleado@test.com',
            password='empleadopass123',
            role='EMPLEADO'
        )
        self.empleado_user.must_change_password = True
        self.empleado_user.save()

        self.empleado_profile = EmpleadoProfile.objects.create(
            user=self.empleado_user,
            empresa=self.empresa_profile,
            nombre='Juan',
            apellido='Pérez',
            dni='12345678A'
        )

    def test_login_successful_master(self):
        """Test: Login exitoso de usuario MASTER"""
        url = reverse('login')
        data = {
            'username': 'master',
            'password': 'masterpass123'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['role'], 'MASTER')
        self.assertEqual(response.data['user_id'], self.master_user.id)
        self.assertFalse(response.data['must_change_password'])

    def test_login_successful_empresa(self):
        """Test: Login exitoso de usuario EMPRESA"""
        url = reverse('login')
        data = {
            'username': 'empresa_test',
            'password': 'empresapass123'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['role'], 'EMPRESA')
        self.assertEqual(response.data['empresa_id'], self.empresa_profile.id)

    def test_login_successful_empleado(self):
        """Test: Login exitoso de usuario EMPLEADO"""
        url = reverse('login')
        data = {
            'username': 'empleado_test',
            'password': 'empleadopass123'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['role'], 'EMPLEADO')
        self.assertEqual(response.data['empleado_id'], self.empleado_profile.id)
        self.assertTrue(response.data['must_change_password'])

    def test_login_invalid_credentials(self):
        """Test: Login con credenciales inválidas"""
        url = reverse('login')
        data = {
            'username': 'master',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_logout_successful(self):
        """Test: Logout exitoso elimina el token"""
        # Primero hacer login
        login_url = reverse('login')
        login_data = {
            'username': 'master',
            'password': 'masterpass123'
        }
        login_response = self.client.post(login_url, login_data)
        token = login_response.data['token']

        # Ahora hacer logout
        logout_url = reverse('logout')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.post(logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Verificar que el token fue eliminado
        session_url = reverse('session')
        session_response = self.client.get(session_url)
        self.assertEqual(session_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_authentication(self):
        """Test: Logout sin autenticación falla"""
        url = reverse('logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_authenticated_user(self):
        """Test: Session devuelve datos del usuario autenticado"""
        # Login
        login_url = reverse('login')
        login_data = {
            'username': 'master',
            'password': 'masterpass123'
        }
        login_response = self.client.post(login_url, login_data)
        token = login_response.data['token']

        # Obtener sesión
        session_url = reverse('session')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.get(session_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'master')
        self.assertEqual(response.data['role'], 'MASTER')
        self.assertIn('token', response.data)

    def test_session_without_authentication(self):
        """Test: Session sin autenticación falla"""
        url = reverse('session')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_user_empresa(self):
        """Test: Registro de usuario tipo EMPRESA"""
        url = reverse('register')
        data = {
            'username': 'nueva_empresa',
            'email': 'nueva@empresa.com',
            'password': 'password123',
            'role': 'EMPRESA',
            'nombre_empresa': 'Nueva Empresa',
            'nif': 'B98765432',
            'address': 'Calle Test 123',
            'city': 'Madrid',
            'postal_code': '28001',
            'correo_contacto': 'nueva@empresa.com'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verificar que se creó el usuario
        user_exists = CustomUser.objects.filter(username='nueva_empresa').exists()
        self.assertTrue(user_exists)

        # Verificar que se creó el perfil de empresa
        empresa_exists = EmpresaProfile.objects.filter(nif='B98765432').exists()
        self.assertTrue(empresa_exists)

    def test_register_user_duplicate_email(self):
        """Test: Registro con email duplicado falla"""
        url = reverse('register')
        data = {
            'username': 'otro_usuario',
            'email': 'master@test.com',  # Email ya existe
            'password': 'password123',
            'role': 'MASTER'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_empresa_duplicate_nif(self):
        """Test: Registro de empresa con NIF duplicado falla"""
        url = reverse('register')
        data = {
            'username': 'empresa2',
            'email': 'empresa2@test.com',
            'password': 'password123',
            'role': 'EMPRESA',
            'nombre_empresa': 'Empresa 2',
            'nif': 'B12345678',  # NIF ya existe
            'address': 'Calle Test 456',
            'city': 'Barcelona',
            'postal_code': '08001',
            'correo_contacto': 'empresa2@test.com'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
