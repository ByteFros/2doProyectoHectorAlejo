"""
Serializers para el módulo de empresas y empleados
"""
from rest_framework import serializers
from users.models import EmpresaProfile, EmpleadoProfile, CustomUser


class EmpresaCreateSerializer(serializers.Serializer):
    """Serializer para crear empresa"""
    nombre_empresa = serializers.CharField(max_length=255, required=True)
    nif = serializers.CharField(max_length=50, required=True)
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    correo_contacto = serializers.EmailField(required=True)
    permisos = serializers.BooleanField(default=False, required=False)

    def validate_nif(self, value):
        """Validar que el NIF no esté duplicado"""
        if EmpresaProfile.objects.filter(nif=value).exists():
            raise serializers.ValidationError("El NIF ya está registrado en la BBDD")
        return value

    def validate_correo_contacto(self, value):
        """Validar que el email no esté duplicado"""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe una empresa con este correo")
        return value


class EmpleadoCreateSerializer(serializers.Serializer):
    """Serializer para crear empleado individual"""
    nombre = serializers.CharField(max_length=255, required=True)
    apellido = serializers.CharField(max_length=255, required=True)
    dni = serializers.CharField(max_length=20, required=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, default="empleado")

    def validate_dni(self, value):
        """Validar que el DNI no esté duplicado"""
        if EmpleadoProfile.objects.filter(dni=value).exists():
            raise serializers.ValidationError("El DNI ya está asociado a un empleado")
        return value

    def validate_email(self, value):
        """Validar que el email no esté duplicado (si se proporciona)"""
        if value and CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("El email ya está registrado")
        return value

    def validate_username(self, value):
        """Validar que el username no esté duplicado (si se proporciona)"""
        if value and CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("El nombre de usuario ya existe")
        return value


class BatchEmployeeUploadSerializer(serializers.Serializer):
    """Serializer para validar archivo CSV"""
    file = serializers.FileField(required=True)

    def validate_file(self, value):
        """Validar que sea un archivo CSV"""
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("El archivo debe ser un CSV")
        return value


class EmpresaUpdatePermissionsSerializer(serializers.Serializer):
    """Serializer para actualizar permisos de empresa"""
    permisos = serializers.BooleanField(required=True)
