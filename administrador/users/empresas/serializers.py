"""
Serializers para el módulo de empresas y empleados
"""
from rest_framework import serializers
from users.models import EmpresaProfile, EmpleadoProfile, CustomUser, Viaje
from users.common.validators import validate_dni_nie_nif_serializer, validate_nif_serializer


# ==================== SERIALIZERS ANIDADOS PARA 'include' ====================

class ViajeNestedSerializer(serializers.ModelSerializer):
    """Serializer simplificado de viajes para anidar en empleados"""
    class Meta:
        model = Viaje
        fields = [
            'id', 'destino', 'ciudad', 'pais', 'es_internacional',
            'fecha_inicio', 'fecha_fin', 'estado',
            'dias_viajados', 'empresa_visitada', 'motivo', 'fecha_solicitud'
        ]
        read_only_fields = fields


class EmpleadoNestedSerializer(serializers.ModelSerializer):
    """Serializer simplificado de empleados para anidar en empresas"""
    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = EmpleadoProfile
        fields = ['id', 'nombre', 'apellido', 'dni', 'email', 'username']
        read_only_fields = fields


class EmpresaNestedSerializer(serializers.ModelSerializer):
    """Serializer completo de empresa para anidar en empleados"""
    class Meta:
        model = EmpresaProfile
        fields = ['id', 'nombre_empresa', 'nif', 'address', 'city', 'postal_code', 'correo_contacto', 'permisos']
        read_only_fields = fields


# ==================== SERIALIZERS DINÁMICOS ====================

class EmpresaWithEmpleadosSerializer(serializers.ModelSerializer):
    """Serializer de empresa con empleados anidados (include=empleados)"""
    empleados = EmpleadoNestedSerializer(many=True, read_only=True)
    empleados_count = serializers.SerializerMethodField()

    class Meta:
        model = EmpresaProfile
        fields = ['id', 'nombre_empresa', 'nif', 'address', 'city', 'postal_code',
                  'correo_contacto', 'permisos', 'empleados', 'empleados_count']
        read_only_fields = fields

    def get_empleados_count(self, obj):
        return obj.empleados.count()


class EmpleadoWithViajesSerializer(serializers.ModelSerializer):
    """Serializer de empleado con viajes anidados (include=viajes)"""
    empresa = EmpresaNestedSerializer(read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    viajes = ViajeNestedSerializer(many=True, read_only=True, source='viaje_set')
    viajes_count = serializers.SerializerMethodField()

    class Meta:
        model = EmpleadoProfile
        fields = ['id', 'nombre', 'apellido', 'dni', 'email', 'username',
                  'empresa', 'viajes', 'viajes_count']
        read_only_fields = fields

    def get_viajes_count(self, obj):
        return obj.viaje_set.count()


# ==================== SERIALIZERS ORIGINALES ====================

class EmpresaCreateSerializer(serializers.Serializer):
    """Serializer para crear empresa"""
    nombre_empresa = serializers.CharField(max_length=255, required=True)
    nif = serializers.CharField(max_length=50, required=True, validators=[validate_nif_serializer])
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=10, required=False, allow_blank=True)
    correo_contacto = serializers.EmailField(required=True)
    permisos = serializers.BooleanField(default=False, required=False)

    def validate_nif(self, value):
        """Validar que el NIF no esté duplicado"""
        # Normalizar para comparación (el validator ya lo normaliza)
        value_normalized = value.upper().strip()
        if EmpresaProfile.objects.filter(nif=value_normalized).exists():
            raise serializers.ValidationError("El NIF ya está registrado en la BBDD")
        return value_normalized

    def validate_correo_contacto(self, value):
        """Validar que el email no esté duplicado"""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe una empresa con este correo")
        return value


class EmpleadoCreateSerializer(serializers.Serializer):
    """Serializer para crear empleado individual"""
    nombre = serializers.CharField(max_length=255, required=True)
    apellido = serializers.CharField(max_length=255, required=True)
    dni = serializers.CharField(max_length=20, required=True, validators=[validate_dni_nie_nif_serializer])
    email = serializers.EmailField(required=True)  # Ahora es obligatorio
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, default="empleado")

    def validate_dni(self, value):
        """Validar que el DNI/NIE/NIF no esté duplicado"""
        # Normalizar para comparación (el validator ya lo normaliza)
        value_normalized = value.upper().strip()
        if EmpleadoProfile.objects.filter(dni=value_normalized).exists():
            raise serializers.ValidationError("El DNI/NIE ya está asociado a un empleado")
        return value_normalized

    def validate_email(self, value):
        """Validar que el email no esté duplicado"""
        if CustomUser.objects.filter(email=value).exists():
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
