from django.utils import timezone
from rest_framework import serializers
import re
from .models import CustomUser, EmpresaProfile, EmpleadoProfile, Gasto, Viaje, Notificacion, Notas, MensajeJustificante, \
    DiaViaje, Conversacion, Mensaje, ViajeReviewSnapshot, GastoReviewSnapshot


class CustomUserSerializer(serializers.ModelSerializer):
    """Serializador unificado para usuarios"""

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'must_change_password']
        extra_kwargs = {'password': {'write_only': True}}


class EmpresaProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = EmpresaProfile
        fields = [
            'id',
            'user_id',
            'nombre_empresa',
            'nif',
            'address',
            'city',
            'postal_code',
            'correo_contacto',
            'permisos',
            'periodicity',
            'last_release_at',
            'next_release_at',
            'manual_release_at',
            'force_release',
            'has_pending_review_changes',
            'role'
        ]
        read_only_fields = [
            'last_release_at',
            'next_release_at',
            'force_release',
            'has_pending_review_changes',
            'role',
            'user_id',
        ]
        extra_kwargs = {
            'manual_release_at': {'allow_null': True, 'required': False},
            'periodicity': {'required': False},
        }


EMAIL_UNICODE_REGEX = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', re.UNICODE)


class EmpleadoProfileSerializer(serializers.ModelSerializer):
    empresa = serializers.StringRelatedField(source="empresa.nombre_empresa", read_only=True)
    empresa_id = serializers.IntegerField(source="empresa.id", read_only=True)
    email = serializers.CharField(source="user.email", required=False)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = EmpleadoProfile
        fields = ['id', 'nombre', 'apellido', 'dni', 'email', 'empresa', 'empresa_id', 'user_id', 'username', 'role', 'salario']

    def validate_email(self, value):
        if value is None:
            return value

        email_normalized = value.strip()
        if not EMAIL_UNICODE_REGEX.match(email_normalized):
            raise serializers.ValidationError("El email no tiene un formato válido")

        queryset = CustomUser.objects.filter(email__iexact=email_normalized)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.user_id)

        if queryset.exists():
            raise serializers.ValidationError("El email ya está registrado")

        return email_normalized

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        new_email = user_data.get('email')

        if new_email is not None:
            new_email = new_email.strip()
            user = instance.user
            if user.email != new_email or user.username != new_email:
                user.email = new_email
                user.username = new_email
                user.save(update_fields=['email', 'username'])

        instance = super().update(instance, validated_data)
        return instance


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

        if fecha < viaje.fecha_inicio or fecha > viaje.fecha_fin:
            raise serializers.ValidationError({
                "fecha_gasto": f"La fecha debe estar entre {viaje.fecha_inicio} y {viaje.fecha_fin}"
            })

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

    def update(self, instance, validated_data):
        viaje = instance.viaje
        if viaje and viaje.estado == "REABIERTO":
            # Ignorar identificadores que puedan venir desde el cliente
            for field in ('viaje_id', 'empresa_id', 'empleado_id'):
                validated_data.pop(field, None)
            allowed_fields = {"comprobante"}
            invalid_fields = [field for field in validated_data.keys() if field not in allowed_fields]
            if invalid_fields:
                raise serializers.ValidationError({
                    field: "No se puede modificar este campo mientras el viaje está reabierto."
                    for field in invalid_fields
                })
        return super().update(instance, validated_data)


class GastoNestedSerializer(serializers.ModelSerializer):
    """Serializer compacto de gastos para anidar en viajes"""
    comprobante_url = serializers.SerializerMethodField()

    class Meta:
        model = Gasto
        fields = [
            "id",
            "concepto",
            "monto",
            "fecha_gasto",
            "estado",
            "fecha_solicitud",
            "comprobante",
            "comprobante_url",
        ]
        read_only_fields = fields

    def get_comprobante_url(self, obj):
        request = self.context.get('request') if hasattr(self, 'context') else None
        if obj.comprobante:
            if request:
                return request.build_absolute_uri(obj.comprobante.url)
            return obj.comprobante.url
        return None


class DiaViajeGastoSerializer(serializers.ModelSerializer):
    """Gasto simplificado para uso dentro de DiaViajeSerializer"""

    class Meta:
        model = Gasto
        fields = [
            "id",
            "concepto",
            "monto",
            "fecha_gasto",
            "estado",
            "fecha_solicitud",
            "comprobante",
        ]
        read_only_fields = fields


class DiaViajeSerializer(serializers.ModelSerializer):
    """Serializador para representar cada día de viaje junto con sus gastos"""
    dia_id = serializers.IntegerField(source='id', read_only=True)
    gastos = DiaViajeGastoSerializer(many=True, read_only=True)

    class Meta:
        model = DiaViaje
        fields = [
            'dia_id',
            'fecha',
            'exento',
            'revisado',
            'gastos',
        ]
        read_only_fields = ['dia_id', 'fecha', 'gastos']

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
            estado__in=['EN_REVISION', 'REABIERTO']
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
    empleado_id = serializers.IntegerField(write_only=True, required=False)
    empresa_id = serializers.IntegerField(write_only=True, required=False)
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
        # 1) Sacamos los IDs (si están presentes, sino serán asignados por la vista)
        empleado_id = validated_data.pop('empleado_id', None)
        empresa_id = validated_data.pop('empresa_id', None)
        
        if empleado_id and empresa_id:
            empleado = EmpleadoProfile.objects.get(id=empleado_id)
            empresa = EmpresaProfile.objects.get(id=empresa_id)
        else:
            # Los IDs serán asignados por la vista antes de llegar aquí
            raise serializers.ValidationError("empleado_id y empresa_id son requeridos")

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
                estado__in=['EN_REVISION', 'REABIERTO']
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


class ViajeWithGastosSerializer(ViajeSerializer):
    """Extiende el serializer de viajes para incluir los gastos asociados."""

    gastos = GastoNestedSerializer(many=True, read_only=True, source='gasto_set')

    class Meta(ViajeSerializer.Meta):
        fields = ViajeSerializer.Meta.fields + ['gastos']
        read_only_fields = ViajeSerializer.Meta.read_only_fields + ['gastos']


class ViajeSnapshotSerializer(serializers.Serializer):
    """Serializa snapshots publicados de viajes revisados."""

    id = serializers.IntegerField(source='viaje_id')
    empleado = serializers.SerializerMethodField()
    empresa = serializers.SerializerMethodField()
    destino = serializers.CharField()
    ciudad = serializers.CharField(allow_null=True)
    pais = serializers.CharField(allow_null=True)
    es_internacional = serializers.BooleanField()
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    estado = serializers.CharField()
    fecha_solicitud = serializers.SerializerMethodField()
    empresa_visitada = serializers.CharField(allow_null=True)
    motivo = serializers.CharField(allow_null=True)
    dias_viajados = serializers.IntegerField()
    notas = serializers.SerializerMethodField()
    gastos = serializers.SerializerMethodField()

    def _get_request_context(self):
        return self.context.get('request') if isinstance(self.context, dict) else None

    def get_empleado(self, obj):
        if not obj.empleado_id:
            return None
        return EmpleadoProfileSerializer(obj.empleado, context=self.context).data

    def get_empresa(self, obj):
        if not obj.empresa_id:
            return None
        return EmpresaProfileSerializer(obj.empresa, context=self.context).data

    def get_fecha_solicitud(self, obj):
        if obj.viaje_id and obj.viaje:
            return obj.viaje.fecha_solicitud
        return None

    def get_notas(self, obj):
        viaje = getattr(obj, "viaje", None)
        if not viaje:
            return []
        notas_qs = viaje.notas.all()
        return NotaViajeSerializer(notas_qs, many=True, context=self.context).data

    def get_gastos(self, obj):
        if not self.context.get('include_gastos'):
            return []

        serializer = GastoSnapshotSerializer(
            obj.gastos_snapshot.all(),
            many=True,
            context={'request': self._get_request_context()}
        )
        return serializer.data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self.context.get('include_gastos'):
            data.pop('gastos', None)
        return data


class GastoSnapshotSerializer(serializers.Serializer):
    """Serializa snapshot de gasto usando valores congelados."""

    def to_representation(self, snapshot: GastoReviewSnapshot):
        gasto = getattr(snapshot, 'gasto', None)
        request = self.context.get('request') if isinstance(self.context, dict) else None

        if gasto:
            data = GastoSerializer(gasto, context={'request': request}).data
        else:
            # construir estructura básica si el gasto fue borrado
            data = {
                'id': snapshot.gasto_id,
                'concepto': snapshot.concepto,
                'monto': str(snapshot.monto),
                'fecha_gasto': snapshot.fecha_gasto,
                'estado': snapshot.estado,
                'fecha_solicitud': None,
                'comprobante': None,
                'empleado': EmpleadoProfileSerializer(snapshot.empleado).data if snapshot.empleado_id else None,
                'empresa': EmpresaProfileSerializer(snapshot.empresa).data if snapshot.empresa_id else None,
                'empleado_id': snapshot.empleado_id,
                'empresa_id': snapshot.empresa_id,
                'viaje': None,
                'viaje_id': snapshot.viaje_snapshot.viaje_id if snapshot.viaje_snapshot else None,
            }

        # Sobrescribir campos congelados
        data['concepto'] = snapshot.concepto
        data['monto'] = str(snapshot.monto)
        data['estado'] = snapshot.estado
        data['fecha_gasto'] = snapshot.fecha_gasto.isoformat() if snapshot.fecha_gasto else None
        data['id'] = snapshot.gasto_id
        data['viaje_id'] = snapshot.viaje_snapshot.viaje_id if snapshot.viaje_snapshot else data.get('viaje_id')

        if 'viaje' in data and data['viaje'] and snapshot.viaje_snapshot:
            viaje = snapshot.viaje_snapshot
            data['viaje'] = {
                'id': viaje.viaje_id,
                'destino': viaje.destino,
                'fecha_inicio': viaje.fecha_inicio,
                'fecha_fin': viaje.fecha_fin,
                'estado': viaje.estado,
            }

        return data


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
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversacion
        fields = ['id', 'participantes', 'fecha_creacion', 'last_message']

    def get_last_message(self, obj):
        last_message = obj.mensajes.order_by('-fecha_creacion').first()
        if not last_message:
            return None

        request = self.context.get('request') if hasattr(self, 'context') else None
        archivo_url = None
        if last_message.archivo:
            if request:
                archivo_url = request.build_absolute_uri(last_message.archivo.url)
            else:
                archivo_url = last_message.archivo.url

        return {
            "id": last_message.id,
            "autor": last_message.autor.username,
            "contenido": last_message.contenido,
            "archivo": archivo_url,
            "fecha_creacion": last_message.fecha_creacion,
        }

class MensajeSerializer(serializers.ModelSerializer):
    autor = serializers.StringRelatedField()
    autor_id = serializers.IntegerField(source='autor.id', read_only=True)
    archivo = serializers.FileField(read_only=True)

    class Meta:
        model = Mensaje
        fields = ['id', 'conversacion', 'autor', 'autor_id', 'contenido', 'archivo', 'fecha_creacion']

class CompanyTripsSummarySerializer(serializers.Serializer):
    empresa_id = serializers.IntegerField()
    empresa = serializers.CharField()
    trips = serializers.IntegerField()
    days = serializers.IntegerField()
    exemptDays = serializers.IntegerField()
    nonExemptDays = serializers.IntegerField()
    empleados = serializers.ListField(required=False)  # Campo opcional para el desglose


class TripsPerMonthSerializer(serializers.Serializer):
    month = serializers.CharField()     # ej. '2025-03'
    totalTrips = serializers.IntegerField()  # Número de viajes iniciados en el mes

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
