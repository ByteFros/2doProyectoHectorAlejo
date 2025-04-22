from datetime import date, timezone

from rest_framework import serializers
from .models import CustomUser, EmpresaProfile, EmpleadoProfile, Gasto, Viaje, Notificacion, Notas, MensajeJustificante, \
    DiaViaje


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
    fecha_gasto = serializers.DateField(allow_null= True, required = False, help_text="Fecha en que ocurrio el gasto")

    empresa = EmpresaProfileSerializer(read_only=True)
    empleado = EmpleadoProfileSerializer(read_only=True)
    viaje = serializers.SerializerMethodField()

    class Meta:
        model = Gasto
        fields = [
            "id", "concepto", "monto","fecha_gasto", "estado", "fecha_solicitud", "comprobante",
            "empleado", "empresa", "empleado_id", "empresa_id",
            "viaje", "viaje_id"
        ]
        read_only_fields = ["id", "estado", "fecha_solicitud","viaje"]

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
        # 1) Extraemos el viaje
        viaje = Viaje.objects.get(id=validated_data.pop("viaje_id"))

        # 2) Sacamos fecha_gasto si vino, o tomamos la fecha local de hoy
        fecha = validated_data.pop("fecha_gasto", None)
        if fecha is None:
            fecha = timezone.localdate()

        # 3) Obtenemos o creamos el DíaViaje correspondiente
        dia, _ = DiaViaje.objects.get_or_create(viaje=viaje, fecha=fecha)

        # 4) Creamos el gasto asociando viaje, día y resto de campos
        gasto = Gasto.objects.create(
            viaje=viaje,
            dia=dia,
            **validated_data
        )
        return gasto
class DiaViajeSerializer(serializers.ModelSerializer):
    """Serializador para representar cada día de viaje junto con sus gastos"""
    gastos = GastoSerializer(many=True, read_only=True)

    class Meta:
        model = DiaViaje
        fields = [
            'id',
            'fecha',
            'exento',
            'revisado',
            'gastos',
        ]
        read_only_fields = ['id', 'fecha', 'gastos']

    def update(self, instance, validated_data):
        # Solo actualizar los flags exento y revisado
        instance.exento = validated_data.get('exento', instance.exento)
        instance.revisado = validated_data.get('revisado', instance.revisado)
        instance.save()
        return instance


class ViajeSerializer(serializers.ModelSerializer):
    """Serializador para manejar viajes y cálculo automático de días"""

    empleado_id = serializers.IntegerField(write_only=True)
    empresa_id = serializers.IntegerField(write_only=True)
    empresa = EmpresaProfileSerializer(read_only=True)
    empleado = EmpleadoProfileSerializer(read_only=True)
    dias_viajados = serializers.IntegerField(read_only=True)

    class Meta:
        model = Viaje
        fields = [
            'id', 'empleado', 'empresa', 'destino',
            'fecha_inicio', 'fecha_fin', 'estado', 'fecha_solicitud',
            'empleado_id', 'empresa_id', 'empresa_visitada', 'motivo',
            'dias_viajados'
        ]

    def create(self, validated_data):
        empleado_id = validated_data.pop('empleado_id')
        empresa_id = validated_data.pop('empresa_id')

        empleado = EmpleadoProfile.objects.get(id=empleado_id)
        empresa = EmpresaProfile.objects.get(id=empresa_id)

        # Calcular días de viaje inclusivos
        fecha_inicio = validated_data.get('fecha_inicio')
        fecha_fin = validated_data.get('fecha_fin')
        dias = (fecha_fin - fecha_inicio).days + 1

        # Verificación de duplicados y validaciones de motivo
        motivo = validated_data.get('motivo', '')
        if motivo and len(motivo) > 500:
            raise serializers.ValidationError({'motivo': 'El motivo no puede superar los 500 caracteres'})

        existe = Viaje.objects.filter(
            empresa=empresa,
            destino=validated_data.get('destino'),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado='PENDIENTE'
        ).exists()
        if existe:
            raise serializers.ValidationError(
                {'error': 'Ya existe un viaje pendiente a este destino en estas fechas para la empresa.'}
            )

        viaje = Viaje.objects.create(
            empleado=empleado,
            empresa=empresa,
            dias_viajados=dias,
            **validated_data
        )
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


class MensajeJustificanteSerializer(serializers.ModelSerializer):
    autor = serializers.StringRelatedField(read_only=True)
    archivo_justificante_url = serializers.SerializerMethodField()
    gasto_id = serializers.IntegerField(source='gasto.id', read_only=True)
    remitente = serializers.SerializerMethodField()

    class Meta:
        model = MensajeJustificante
        fields = ["id", "gasto", "autor", "motivo", "respuesta", "estado", "archivo_justificante_url", "fecha_creacion",
                  "gasto_id", "remitente"]
        read_only_fields = ["id", "fecha_creacion", "autor", "archivo_justificante_url", "gasto_id"]

    def get_remitente(self, obj):
        if obj.respuesta and obj.gasto.empleado:
            return obj.gasto.empleado.user.username
        return None

    def get_archivo_justificante_url(self, obj):
        if obj.archivo_justificante:
            return obj.archivo_justificante.url
        return None


