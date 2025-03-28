from rest_framework import serializers
from .models import CustomUser, EmpresaProfile, EmpleadoProfile, Gasto, Viaje, Notificacion, Notas


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializador unificado para usuarios"""

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'must_change_password']
        extra_kwargs = {'password': {'write_only': True}}


class EmpresaProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaProfile
        fields = ['id', 'nombre_empresa', 'nif', 'address', 'city', 'postal_code', 'correo_contacto', 'permisos']


class EmpleadoProfileSerializer(serializers.ModelSerializer):
    empresa = serializers.StringRelatedField(source="empresa.nombre_empresa", read_only=True)
    email = serializers.StringRelatedField(source="user.email", read_only=True)

    class Meta:
        model = EmpleadoProfile
        fields = ['id', 'nombre', 'apellido', 'dni', 'email', 'empresa']


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

            # 🔹 Verificar si ya existe una empresa con ese NIF
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


class GastoSerializer(serializers.ModelSerializer):
    """Serializador de Gastos con info detallada y soporte de entrada para viaje_id"""

    empleado_id = serializers.IntegerField(write_only=True)
    empresa_id = serializers.IntegerField(write_only=True)
    viaje_id = serializers.IntegerField(write_only=True)

    empresa = EmpresaProfileSerializer(read_only=True)
    empleado = EmpleadoProfileSerializer(read_only=True)
    viaje = serializers.SerializerMethodField()

    class Meta:
        model = Gasto
        fields = [
            "id", "concepto", "monto", "estado", "fecha_solicitud", "comprobante",
            "empleado", "empresa", "empleado_id", "empresa_id",
            "viaje", "viaje_id"
        ]

    def get_viaje(self, obj):
        if obj.viaje:
            return {
                "id": obj.viaje.id,
                "destino": obj.viaje.destino,
                "fecha_inicio": obj.viaje.fecha_inicio,
                "fecha_fin": obj.viaje.fecha_fin,
                "estado": obj.viaje.estado,
            }
        return None

    def create(self, validated_data):
        # Extraemos y asignamos manualmente el viaje
        viaje_id = validated_data.pop("viaje_id")
        validated_data["viaje"] = Viaje.objects.get(id=viaje_id)
        return super().create(validated_data)

class ViajeSerializer(serializers.ModelSerializer):
    """Serializador para manejar viajes"""

    empleado_id = serializers.IntegerField(write_only=True)
    empresa_id = serializers.IntegerField(write_only=True)
    empresa = EmpresaProfileSerializer(read_only=True)
    empleado = EmpleadoProfileSerializer(read_only=True)

    class Meta:
        model = Viaje
        fields = ["id", "empleado", "empresa", "destino", "fecha_inicio", "fecha_fin", "estado", "fecha_solicitud",
                  "empleado_id", "empresa_id","empresa_visitada","motivo","dias_viajados"]

    def create(self, validated_data):
        """Crear un viaje asegurando que los IDs sean convertidos en instancias y evitando duplicados"""

        empleado_id = validated_data.pop("empleado_id", None)
        empresa_id = validated_data.pop("empresa_id", None)
        dias_viajados = validated_data.pop("dias_viajados", 1)

        # 🔹 Verificar si el empleado y la empresa existen
        try:
            empleado = EmpleadoProfile.objects.get(id=empleado_id)
            empresa = EmpresaProfile.objects.get(id=empresa_id)
        except EmpleadoProfile.DoesNotExist:
            raise serializers.ValidationError({"empleado_id": "Empleado no encontrado"})
        except EmpresaProfile.DoesNotExist:
            raise serializers.ValidationError({"empresa_id": "Empresa no encontrada"})

        # 🔹 Validar el motivo del viaje
        motivo = validated_data.get("motivo", "")
        if len(motivo) > 500:
            raise serializers.ValidationError({"motivo": "El motivo no puede superar los 500 caracteres"})

        # 🔹 Verificar si YA existe un viaje en estado "PENDIENTE" para la empresa en las mismas fechas y destino
        viaje_existente = Viaje.objects.filter(
            empresa=empresa,
            destino=validated_data.get("destino"),
            fecha_inicio=validated_data.get("fecha_inicio"),
            fecha_fin=validated_data.get("fecha_fin"),
            estado="PENDIENTE"
        ).exists()

        if viaje_existente:
            raise serializers.ValidationError(
                {"error": "Ya existe un viaje pendiente a este destino en estas fechas para la empresa."}
            )

        # 🔹 Si no hay duplicados, crear el viaje
        viaje = Viaje.objects.create(empleado=empleado,
                                     empresa=empresa,
                                        dias_viajados=dias_viajados,
                                     **validated_data)

        return viaje


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ["id", "tipo", "mensaje", "fecha_creacion", "leida"]


# serializers.py

class NotaViajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notas
        fields = ['id', 'viaje', 'empleado', 'contenido', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion', 'empleado']
