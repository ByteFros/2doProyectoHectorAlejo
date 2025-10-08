"""
Serializers para el módulo de autenticación
"""
from django.db import transaction
from rest_framework import serializers
from users.models import CustomUser, EmpresaProfile, EmpleadoProfile


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

    nombre = serializers.CharField(required=False)
    apellido = serializers.CharField(required=False)
    empresa_id = serializers.IntegerField(required=False)
    dni = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'password',
                  'nombre_empresa', 'nif', 'address', 'city', 'postal_code', 'correo_contacto',
                  'nombre', 'apellido', 'empresa_id', 'dni']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        role = validated_data.get('role')

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
                raise serializers.ValidationError({"empresa_id": "Debe especificar una empresa para el empleado."})
            try:
                empresa = EmpresaProfile.objects.get(id=empresa_id)
            except EmpresaProfile.DoesNotExist:
                raise serializers.ValidationError({"empresa_id": "La empresa especificada no existe."})
            dni = validated_data.get('dni')
            if dni and EmpleadoProfile.objects.filter(dni=dni).exists():
                raise serializers.ValidationError({"dni": "Ya existe un empleado registrado con este DNI."})
        else:
            empresa = None
            dni = None

        with transaction.atomic():
            user = CustomUser.objects.create(
                username=validated_data['username'],
                email=validated_data['email'],
                role=role
            )
            user.set_password(validated_data['password'])
            user.save()

            if role == 'EMPRESA':
                EmpresaProfile.objects.create(
                    user=user,
                    nombre_empresa=validated_data['nombre_empresa'],
                    nif=validated_data['nif'],
                    address=validated_data.get('address', ''),
                    city=validated_data.get('city', ''),
                    postal_code=validated_data.get('postal_code', ''),
                    correo_contacto=validated_data['correo_contacto']
                )
            elif role == 'EMPLEADO':
                EmpleadoProfile.objects.create(
                    user=user,
                    empresa=empresa,
                    nombre=validated_data['nombre'],
                    apellido=validated_data['apellido'],
                    dni=dni or None
                )

        return RegisterUserSerializer(user).data
