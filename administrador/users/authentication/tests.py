"""
Tests para el módulo de autenticación
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

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

        self.master_access, self.master_refresh = self._generate_tokens(self.master_user)
        self.empresa_access, self.empresa_refresh = self._generate_tokens(self.empresa_user)
        self.empleado_access, self.empleado_refresh = self._generate_tokens(self.empleado_user)
        self.master_token = self.master_access
        self.empresa_token = self.empresa_access
        self.empleado_token = self.empleado_access

    def authenticate(self, token=None):
        """Helper para establecer credenciales del cliente API"""
        if token:
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        else:
            self.client.credentials()

    def _generate_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token), str(refresh)

    def test_login_successful_master(self):
        """Test: Login exitoso de usuario MASTER"""
        url = reverse('login')
        data = {
            'username': 'master',
            'password': 'masterpass123'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
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
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
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
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
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
        self.assertIn('detail', response.data)

    def test_logout_successful(self):
        """Test: Logout exitoso elimina el token"""
        # Primero hacer login
        login_url = reverse('login')
        login_data = {
            'username': 'master',
            'password': 'masterpass123'
        }
        login_response = self.client.post(login_url, login_data)
        refresh = login_response.data['refresh']
        access = login_response.data['access']

        # Logout con el refresh recibido
        logout_url = reverse('logout')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        response = self.client.post(logout_url, {'refresh': refresh})

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertIn('message', response.data)

        # Intentar usar el refresh token otra vez debe fallar
        refresh_url = reverse('token_refresh')
        refresh_response = self.client.post(refresh_url, {'refresh': refresh})
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_authentication(self):
        """Test: Logout sin autenticación falla"""
        url = reverse('logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_authenticated_user(self):
        """Test: Session devuelve datos del usuario autenticado"""
        login_url = reverse('login')
        login_data = {
            'username': 'master',
            'password': 'masterpass123'
        }
        login_response = self.client.post(login_url, login_data)
        access = login_response.data['access']

        session_url = reverse('session')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        response = self.client.get(session_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'master')
        self.assertEqual(response.data['role'], 'MASTER')

    def test_session_without_authentication(self):
        """Test: Session sin autenticación falla"""
        url = reverse('session')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_user_empresa(self):
        """Test: Registro de usuario tipo EMPRESA"""
        self.authenticate(self.master_access)
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
        empresa = EmpresaProfile.objects.filter(nif='B98765432').first()
        self.assertIsNotNone(empresa)
        self.assertFalse(empresa.permisos)

        self.authenticate()

    def test_register_empresa_without_password_uses_default(self):
        self.authenticate(self.master_access)
        url = reverse('register')
        data = {
            'username': 'empresa_sin_pass',
            'email': 'sinpass@empresa.com',
            'role': 'EMPRESA',
            'nombre_empresa': 'Empresa Sin Pass',
            'nif': 'B55555555',
            'address': 'Calle 1',
            'city': 'Madrid',
            'postal_code': '28001',
            'correo_contacto': 'sinpass@empresa.com'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = CustomUser.objects.get(username='empresa_sin_pass')
        self.assertTrue(user.must_change_password)
        self.assertTrue(user.check_password('empresa'))

        login_resp = self.client.post(reverse('login'), {
            'username': 'empresa_sin_pass',
            'password': 'empresa'
        })
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        self.authenticate()

    def test_register_empresa_autofills_username_and_contact_email(self):
        self.authenticate(self.master_access)
        url = reverse('register')
        data = {
            'email': 'autofill@empresa.com',
            'role': 'EMPRESA',
            'nombre_empresa': 'Empresa Autofill',
            'nif': 'B66666666'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = CustomUser.objects.get(email='autofill@empresa.com')
        self.assertEqual(user.username, 'autofill@empresa.com')
        empresa = user.empresa_profile
        self.assertEqual(empresa.correo_contacto, 'autofill@empresa.com')

    def test_register_empresa_rejects_duplicate_nif(self):
        self.authenticate(self.master_access)
        url = reverse('register')
        base_payload = {
            'email': 'primera@empresa.com',
            'role': 'EMPRESA',
            'nombre_empresa': 'Empresa Uno',
            'nif': 'B00000001'
        }
        self.client.post(url, base_payload)

        payload = {
            'email': 'segunda@empresa.com',
            'role': 'EMPRESA',
            'nombre_empresa': 'Empresa Dos',
            'nif': 'b-00000001'
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nif', response.data)

    def test_register_user_empresa_with_autogestion_permissions(self):
        """Test: Registro de empresa con permisos de autogestión"""
        self.authenticate(self.master_access)
        url = reverse('register')
        data = {
            'username': 'empresa_autogestion',
            'email': 'autogestion@empresa.com',
            'password': 'password123',
            'role': 'EMPRESA',
            'nombre_empresa': 'Empresa Autogestion',
            'nif': 'B11223344',
            'address': 'Calle Autogestión 1',
            'city': 'Valencia',
            'postal_code': '46001',
            'correo_contacto': 'autogestion@empresa.com',
            'permisos_autogestion': True
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        empresa = EmpresaProfile.objects.filter(nif='B11223344').first()
        self.assertIsNotNone(empresa)
        self.assertTrue(empresa.permisos)
        self.authenticate()

    def test_register_user_empleado_with_salary(self):
        """Test: Registro de empleado permite asignar salario"""
        self.authenticate(self.master_access)
        url = reverse('register')
        data = {
            'username': 'empleado_salario',
            'email': 'empleado.salario@test.com',
            'password': 'password123',
            'role': 'EMPLEADO',
            'nombre': 'Empleado',
            'apellido': 'Salario',
            'empresa_id': self.empresa_profile.id,
            'dni': '22334455K',
            'salario': '34500.75'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        empleado = EmpleadoProfile.objects.filter(dni='22334455K').first()
        self.assertIsNotNone(empleado)
        self.assertEqual(str(empleado.salario), '34500.75')
        self.authenticate()

    def test_register_user_empleado_with_invalid_empresa(self):
        """Test: Registro de empleado con empresa inválida falla"""
        self.authenticate(self.master_access)
        url = reverse('register')
        data = {
            'username': 'empleado_invalido',
            'email': 'empleado.invalido@test.com',
            'password': 'password123',
            'role': 'EMPLEADO',
            'nombre': 'Empleado',
            'apellido': 'Invalido',
            'empresa_id': 9999,
            'dni': '11223344P'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('empresa_id', response.data)
        self.authenticate()

    def test_register_user_empleado_with_negative_salary(self):
        """Test: Registro de empleado con salario negativo lanza error"""
        self.authenticate(self.master_access)
        url = reverse('register')
        data = {
            'username': 'empleado_negativo',
            'email': 'empleado.negativo@test.com',
            'password': 'password123',
            'role': 'EMPLEADO',
            'nombre': 'Empleado',
            'apellido': 'Negativo',
            'empresa_id': self.empresa_profile.id,
            'dni': '33445566L',
            'salario': '-1000'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('salario', response.data)
        self.authenticate()

    def test_register_user_empleado_without_password_uses_default(self):
        """Test: Registro de empleado sin password usa contraseña por defecto"""
        self.authenticate(self.master_access)
        url = reverse('register')
        data = {
            'username': 'empleado_sin_password',
            'email': 'empleado.sinpass@test.com',
            'role': 'EMPLEADO',
            'nombre': 'Empleado',
            'apellido': 'SinPass',
            'empresa_id': self.empresa_profile.id,
            'dni': '55667788M'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = CustomUser.objects.get(username='empleado_sin_password')
        self.assertTrue(user.check_password('empleado'))
        self.authenticate()

    def test_register_user_duplicate_email(self):
        """Test: Registro con email duplicado falla"""
        self.authenticate(self.master_access)
        url = reverse('register')
        data = {
            'username': 'otro_usuario',
            'email': 'master@test.com',  # Email ya existe
            'password': 'password123',
            'role': 'MASTER'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.authenticate()

    def test_register_empresa_duplicate_nif(self):
        """Test: Registro de empresa con NIF duplicado falla"""
        self.authenticate(self.master_access)
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
        self.authenticate()

    def test_register_requires_authentication(self):
        """Test: Registro sin token devuelve 401"""
        self.authenticate()
        url = reverse('register')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_master_can_register_master_user(self):
        """Test: MASTER puede crear otro MASTER"""
        self.authenticate(self.master_token)
        url = reverse('register')
        data = {
            'username': 'nuevo_master',
            'email': 'nuevo.master@test.com',
            'password': 'password123',
            'role': 'MASTER'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = CustomUser.objects.get(username='nuevo_master')
        self.assertEqual(user.role, 'MASTER')
        self.authenticate()

    def test_empresa_registers_employee_for_own_company(self):
        """Test: Empresa solo puede crear empleados ligados a su empresa"""
        self.authenticate(self.empresa_access)
        url = reverse('register')
        data = {
            'username': 'empleado_empresa',
            'email': 'empleado.empresa@test.com',
            'password': 'password123',
            'role': 'MASTER',  # Será forzado a EMPLEADO
            'nombre': 'Empleado',
            'apellido': 'Empresa',
            'dni': '99887766J'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = CustomUser.objects.get(username='empleado_empresa')
        self.assertEqual(created.role, 'EMPLEADO')
        empleado_profile = created.empleado_profile
        self.assertEqual(empleado_profile.empresa_id, self.empresa_profile.id)
        self.authenticate()

    def test_empleado_cannot_access_register(self):
        """Test: Empleado autenticado recibe 403 al registrar"""
        self.authenticate(self.empleado_access)
        url = reverse('register')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.authenticate()
