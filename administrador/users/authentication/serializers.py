"""
Serializers para el módulo de autenticación
"""
from django.db import transaction
import re
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from users.models import CustomUser, EmpresaProfile, EmpleadoProfile
from .services import build_auth_response


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializador unificado para usuarios"""

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'must_change_password']
        extra_kwargs = {'password': {'write_only': True}}


class RegisterUserSerializer(serializers.ModelSerializer):
    """Serializador para registrar usuarios con perfiles específicos"""

    nombre_empresa = serializers.CharField(required=False)
    nif = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    postal_code = serializers.CharField(required=False)
    correo_contacto = serializers.EmailField(required=False)
    permisos = serializers.BooleanField(required=False, default=False, write_only=True)
    permisos_autogestion = serializers.BooleanField(required=False, write_only=True)

    nombre = serializers.CharField(required=False)
    apellido = serializers.CharField(required=False)
    empresa_id = serializers.IntegerField(required=False)
    dni = serializers.CharField(required=False, allow_blank=True)
    salario = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'password',
                  'nombre_empresa', 'nif', 'address', 'city', 'postal_code', 'correo_contacto',
                  'permisos', 'permisos_autogestion',
                  'nombre', 'apellido', 'empresa_id', 'dni', 'salario']
        extra_kwargs = {'password': {'write_only': True, 'required': False}}

    def create(self, validated_data):
        role = validated_data.get('role')
        permisos_autogestion = validated_data.pop('permisos_autogestion', None)
        permisos = validated_data.pop('permisos', False)
        if permisos_autogestion is not None:
            permisos = permisos_autogestion

        if role == 'EMPRESA':
            nif = validated_data.get('nif')
            if not nif:
                raise serializers.ValidationError({"nif": "Debe proporcionar un NIF para registrar la empresa."})
            if EmpresaProfile.objects.filter(nif=nif).exists():
                raise serializers.ValidationError({"nif": "Ya existe una empresa con este NIF."})
            empresa = None
            dni = None

        elif role == 'EMPLEADO':
            empresa_id = validated_data.get('empresa_id')
            if not empresa_id:
                raise serializers.ValidationError({"empresa_id": "Debe especificar la empresa del empleado."})
            try:
                empresa = EmpresaProfile.objects.get(id=empresa_id)
            except EmpresaProfile.DoesNotExist:
                raise serializers.ValidationError({"empresa_id": f"No existe una empresa con id {empresa_id}."})
            dni = validated_data.get('dni')
            if dni and EmpleadoProfile.objects.filter(dni=dni).exists():
                raise serializers.ValidationError({"dni": "El DNI/NIE ya está asociado a otro empleado."})
            salario = validated_data.get('salario')
            if salario is not None and salario < 0:
                raise serializers.ValidationError({"salario": "El salario debe ser un número positivo."})
        else:
            empresa = None
            dni = None
            salario = None

        password = validated_data.pop('password', None)
        must_change = False
        if role == 'EMPLEADO':
            password = password or 'empleado'
            must_change = True
        elif role == 'EMPRESA':
            password = password or 'empresa'
            must_change = True
        elif not password:
            raise serializers.ValidationError({"password": "Debe proporcionar una contraseña."})

        username = validated_data.get('username') or validated_data['email']
        correo_contacto = validated_data.get('correo_contacto') or validated_data['email']
        if role == 'EMPRESA' and validated_data.get('nif'):
            validated_data['nif'] = re.sub(r'[^0-9A-Za-z]', '', validated_data['nif']).upper()

        with transaction.atomic():
            user = CustomUser.objects.create(
                username=username,
                email=validated_data['email'],
                role=role,
                must_change_password=must_change
            )
            user.set_password(password)
            user.save()

            if role == 'EMPRESA':
                EmpresaProfile.objects.create(
                    user=user,
                    nombre_empresa=validated_data['nombre_empresa'],
                    nif=validated_data['nif'],
                    address=validated_data.get('address', ''),
                    city=validated_data.get('city', ''),
                    postal_code=validated_data.get('postal_code', ''),
                    correo_contacto=correo_contacto,
                    permisos=permisos
                )
            elif role == 'EMPLEADO':
                EmpleadoProfile.objects.create(
                    user=user,
                    empresa=empresa,
                    nombre=validated_data['nombre'],
                    apellido=validated_data['apellido'],
                    dni=dni or None,
                    salario=salario
                )

        return RegisterUserSerializer(user).data


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extiende el serializer JWT para incluir datos del perfil en la respuesta."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data.update(build_auth_response(self.user))
        return data
