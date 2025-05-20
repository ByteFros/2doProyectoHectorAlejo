from django.utils import timezone
from rest_framework import serializers
from .models import CustomUser, EmpresaProfile, EmpleadoProfile, Gasto, Viaje, Notificacion, Notas, MensajeJustificante, \
    DiaViaje, Conversacion, Mensaje


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
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.StringRelatedField(source="user.username", read_only=True)  # 🆕 Añadido

    class Meta:
        model = EmpleadoProfile
        fields = ['id', 'nombre', 'apellido', 'dni', 'email', 'empresa', 'user_id', 'username']


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
    fecha_gasto = serializers.DateField(allow_null=True, required=False, help_text="Fecha en que ocurrio el gasto")

    empresa = EmpresaProfileSerializer(read_only=True)
    empleado = EmpleadoProfileSerializer(read_only=True)
    viaje = serializers.SerializerMethodField()

    class Meta:
        model = Gasto
        fields = [
            "id", "concepto", "monto", "fecha_gasto", "estado", "fecha_solicitud", "comprobante",
            "empleado", "empresa", "empleado_id", "empresa_id",
            "viaje", "viaje_id"
        ]
        read_only_fields = ["id", "estado", "fecha_solicitud", "viaje"]

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

        # 3) Obtenemos/creamos el DiaViaje
        dia, _ = DiaViaje.objects.get_or_create(viaje=viaje, fecha=fecha)

        # 4) Sacamos empleado_id y empresa_id
        empleado_id = validated_data.pop("empleado_id")
        empresa_id = validated_data.pop("empresa_id")

        # 5) Creamos el gasto **incluyendo** fecha_gasto
        gasto = Gasto.objects.create(
            viaje=viaje,
            dia=dia,
            fecha_gasto=fecha,
            empleado_id=empleado_id,
            empresa_id=empresa_id,
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


class NotaViajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notas
        fields = ['id','viaje','empleado', 'contenido', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion', 'empleado']
"""

este es un serializer viejo que funciona, lo guardo para no perderlo
class NotaViajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notas
        fields = ['id', 'viaje', 'empleado', 'contenido', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion', 'empleado']


"""


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



"""2do serializer para manejar viajes y cálculo automático de días con destino y país"""
class ViajeSerializer(serializers.ModelSerializer):
    empleado_id = serializers.IntegerField(write_only=True)
    empresa_id = serializers.IntegerField(write_only=True)
    empleado = EmpleadoProfileSerializer(read_only=True)
    empresa = EmpresaProfileSerializer(read_only=True)
    destino = serializers.CharField()
    ciudad = serializers.CharField(read_only=True)
    pais = serializers.CharField(read_only=True)
    es_internacional = serializers.BooleanField(read_only=True)
    dias_viajados = serializers.IntegerField(read_only=True)
    notas = NotaViajeSerializer(many=True,read_only=True)

    class Meta:
        model = Viaje
        fields = [
            'id', 'empleado', 'empresa',
            'destino', 'ciudad', 'pais', 'es_internacional',
            'fecha_inicio', 'fecha_fin', 'estado', 'fecha_solicitud',
            'empleado_id', 'empresa_id', 'empresa_visitada', 'motivo',
            'dias_viajados','notas'
        ]
        read_only_fields = [
            'id', 'empleado', 'empresa',
            'fecha_solicitud',
            'ciudad', 'pais', 'es_internacional',
            'dias_viajados'
        ]

    def create(self, validated_data):
        # 1) Sacamos los IDs
        empleado = EmpleadoProfile.objects.get(id=validated_data.pop('empleado_id'))
        empresa = EmpresaProfile.objects.get(id=validated_data.pop('empresa_id'))

        # 2) Sacamos y eliminamos destino de validated_data
        destino = validated_data.pop('destino', '').strip()

        # 3) Extraemos ciudad y país
        parts = [p.strip() for p in destino.split(',', 1)]
        if len(parts) == 2:
            ciudad, pais = parts
        else:
            ciudad, pais = parts[0], ''

        # Normalize country for Spanish aliases
        pais_norm = pais.strip().lower()
        nacional_aliases = ('españa', 'espana', 'spain')
        es_int = not (pais_norm in nacional_aliases)

        # 5) Días de viaje
        fecha_inicio = validated_data['fecha_inicio']
        fecha_fin = validated_data['fecha_fin']
        dias = (fecha_fin - fecha_inicio).days + 1

        # 6) Validaciones (motivo, duplicados…)
        motivo = validated_data.get('motivo', '')
        if motivo and len(motivo) > 500:
            raise serializers.ValidationError({'motivo': 'El motivo no puede superar los 500 caracteres'})

        if Viaje.objects.filter(
                empresa=empresa,
                destino=destino,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado='PENDIENTE'
        ).exists():
            raise serializers.ValidationError(
                {'error': 'Ya existe un viaje pendiente a este destino en estas fechas para la empresa.'}
            )

        # 7) Creamos el viaje
        viaje = Viaje.objects.create(
            empleado=empleado,
            empresa=empresa,
            destino=destino,
            ciudad=ciudad,
            pais=pais,
            es_internacional=es_int,
            dias_viajados=dias,
            **validated_data
        )
        return viaje


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ["id", "tipo", "mensaje", "fecha_creacion", "leida"]





class MensajeJustificanteSerializer(serializers.ModelSerializer):
    autor = serializers.StringRelatedField(read_only=True)
    archivo_justificante_url = serializers.SerializerMethodField()
    gasto_id = serializers.IntegerField(source='gasto.id', read_only=True)
    remitente = serializers.SerializerMethodField()

    class Meta:
        model = MensajeJustificante
        fields = ["id", "gasto","destinatario", "autor", "motivo", "respuesta", "estado", "archivo_justificante_url", "fecha_creacion",
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

    def validate(self, data):
        if not data.get("gasto") and not data.get("destinatario"):
            raise serializers.ValidationError(
                "Debes indicar un gasto _o_ un destinatario"
            )
        return data

class ConversacionSerializer(serializers.ModelSerializer):
    participantes = serializers.StringRelatedField(many=True)
    class Meta:
        model = Conversacion
        fields = ['id', 'gasto', 'participantes', 'fecha_creacion']

class MensajeSerializer(serializers.ModelSerializer):
    autor = serializers.StringRelatedField()
    archivo = serializers.FileField(read_only=True)
    class Meta:
        model = Mensaje
        fields = ['id', 'conversacion', 'autor', 'contenido', 'archivo', 'fecha_creacion']

class CompanyTripsSummarySerializer(serializers.Serializer):
    empresa_id = serializers.IntegerField()
    empresa = serializers.CharField()
    trips = serializers.IntegerField()
    days = serializers.IntegerField()
    nonExemptDays = serializers.IntegerField()


class TripsPerMonthSerializer(serializers.Serializer):
    month = serializers.CharField()     # ej. '2025-03'
    totalDays = serializers.IntegerField()

class TripsTypeSerializer(serializers.Serializer):
    national = serializers.IntegerField()
    international = serializers.IntegerField()
    total = serializers.IntegerField()
    total_days = serializers.IntegerField()

class ExemptDaysSerializer(serializers.Serializer):
    exempt = serializers.IntegerField()
    nonExempt = serializers.IntegerField()

class GeneralInfoSerializer(serializers.Serializer):
    companies            = serializers.IntegerField()
    employees            = serializers.IntegerField()
    international_trips  = serializers.IntegerField()
    national_trips       = serializers.IntegerField()

"""es un nuevo serializador que estoy probando para ver si funciona mejor"""
class PendingTripSerializer(serializers.ModelSerializer):
    tripDates   = serializers.SerializerMethodField()
    destination = serializers.CharField(source='destino')
    info        = serializers.CharField(source='motivo')
    notes       = serializers.SerializerMethodField()
    employeeName = serializers.SerializerMethodField()
    companyVisited = serializers.CharField(source='empresa_visitada')

    class Meta:
        model = Viaje
        fields = ['id', 'tripDates', 'destination', 'info', 'notes', 'employeeName','companyVisited']

    def get_tripDates(self, obj):
        # devolvemos [fecha_inicio, fecha_fin] en ISO
        return [obj.fecha_inicio.isoformat(), obj.fecha_fin.isoformat()]

    def get_notes(self, obj):
        # si usas tu modelo Notas:
        return [n.contenido for n in obj.notas.all()]

    def get_employeeName(self, obj):
        # Asegúrate de que el viaje tenga prefetched empleado
        return f"{obj.empleado.nombre} {obj.empleado.apellido}"


class EmpresaPendingSerializer(serializers.ModelSerializer):
    """Solo campos esenciales para la lista de empresas con viajes pendientes."""
    class Meta:
        model = EmpresaProfile
        fields = ['id', 'nombre_empresa']