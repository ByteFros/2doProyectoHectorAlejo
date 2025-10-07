"""
Serializers para el módulo de autenticación
"""
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
    pais = serializers.CharField(required=False)
    codigo_postal = serializers.CharField(required=False)
    correo_contacto = serializers.EmailField(required=False)

    nombre = serializers.CharField(required=False)
    apellido = serializers.CharField(required=False)
    empresa_id = serializers.IntegerField(required=False)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'password',
                  'nombre_empresa', 'nif', 'pais', 'codigo_postal', 'correo_contacto',
                  'nombre', 'apellido', 'empresa_id']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        role = validated_data.get('role')

        user = CustomUser.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            role=role
        )
        user.set_password(validated_data['password'])
        user.save()

        if role == 'EMPRESA':
            nif = validated_data.get('nif')

            # Verificar si ya existe una empresa con ese NIF
            if EmpresaProfile.objects.filter(nif=nif).exists():
                raise serializers.ValidationError({"nif": "Ya existe una empresa con este NIF."})

            EmpresaProfile.objects.create(
                user=user,
                nombre_empresa=validated_data['nombre_empresa'],
                nif=nif,
                pais=validated_data['pais'],
                codigo_postal=validated_data['codigo_postal'],
                correo_contacto=validated_data['correo_contacto']
            )

        elif role == 'EMPLEADO':
            empresa_id = validated_data.get('empresa_id')
            if not empresa_id:
                raise serializers.ValidationError({"empresa_id": "Debe especificar una empresa para el empleado."})

            try:
                empresa = EmpresaProfile.objects.get(id=empresa_id)
            except EmpresaProfile.DoesNotExist:
                raise serializers.ValidationError({"empresa_id": "La empresa especificada no existe."})

            EmpleadoProfile.objects.create(
                user=user,
                empresa=empresa,
                nombre=validated_data['nombre'],
                apellido=validated_data['apellido']
            )

        return RegisterUserSerializer(user).data
