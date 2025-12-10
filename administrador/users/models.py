from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
import uuid
from django.utils.timezone import now
from datetime import timedelta
from django.conf import settings


def password_reset_token_expiration_default():
    """Retorna la expiración por defecto (ahora + 1h)."""
    return now() + timedelta(hours=1)


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('MASTER', 'Master'),
        ('EMPRESA', 'Empresa'),
        ('EMPLEADO', 'Empleado'),
    ]
    email = models.EmailField(unique=True, blank=False, null=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='EMPLEADO')
    must_change_password = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        """Si es un nuevo usuario EMPLEADO se debe forzar a cambiar la contraseña"""
        if self.role == "EMPLEADO" and not self.pk :
            self.must_change_password = True

        super().save(*args,**kwargs)

    def __str__(self):
        return f"{self.username} - {self.role}"


class EmpresaProfile(models.Model):
    """Perfil para usuarios con rol EMPRESA"""
    PERIODICITY_TRIMESTRAL = "TRIMESTRAL"
    PERIODICITY_SEMESTRAL = "SEMESTRAL"
    PERIODICITY_CHOICES = [
        (PERIODICITY_TRIMESTRAL, "Trimestral"),
        (PERIODICITY_SEMESTRAL, "Semestral"),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="empresa_profile")
    nombre_empresa = models.CharField(max_length=255)
    nif = models.CharField(max_length=50, unique=True)  # Identificación Fiscal
    address = models.CharField(max_length=255, null=True, blank=True)  # ✅ Dirección
    city = models.CharField(max_length=100, null=True, blank=True)  # ✅ Ciudad
    postal_code = models.CharField(max_length=10, null=True, blank=True)  # ✅ Código Postal
    correo_contacto = models.EmailField()
    permisos = models.BooleanField(default=False)  # ✅ Permisos
    periodicity = models.CharField(
        max_length=20,
        choices=PERIODICITY_CHOICES,
        default=PERIODICITY_TRIMESTRAL,
    )
    last_release_at = models.DateTimeField(null=True, blank=True)
    next_release_at = models.DateTimeField(null=True, blank=True)
    manual_release_at = models.DateTimeField(null=True, blank=True)
    force_release = models.BooleanField(default=False)
    has_pending_review_changes = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        """Si se elimina una empresa tambien se debe eliminar a sus empleados"""
        empleados = EmpleadoProfile.objects.filter(empresa=self)

        for empleado in empleados:
            empleado.user.delete()

        empleados.delete()

        self.user.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Empresa: {self.nombre_empresa} ({self.user.username})"

    """Perfil para usuarios con rol EMPLEADO"""


class EmpleadoProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="empleado_profile")
    empresa = models.ForeignKey(EmpresaProfile, on_delete=models.CASCADE, related_name="empleados", null=False)
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    dni = models.CharField(max_length=20, unique=True, null=True, blank=True, default=None)  # 🔹 DNI único opcional
    salario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)

    def clean(self):
        """Un empleado no puede pertenecer a más de una empresa"""
        if EmpleadoProfile.objects.filter(user=self.user).exclude(id=self.id).exists():
            raise ValidationError("Este empleado ya está registrado en otra empresa")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Empleado: {self.nombre} {self.apellido} ({self.user.username})"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)  # Genera un token único
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=password_reset_token_expiration_default)

    def save(self,*args, **kwargs):
        """este token tendra 1 hora de validez"""
        if not self.expires_at:
            self.expires_at = password_reset_token_expiration_default()
        super().save(*args, **kwargs)

    def is_valid(self):
        """verificamos si el token es valido"""
        return now() < self.expires_at

class Viaje(models.Model):
    """Modelo para manejar los viajes solicitados por empleados"""

    ESTADO_CHOICES = [
        ("EN_REVISION", "En revision"),
        ("REABIERTO", "Reabierto"),
        ("REVISADO", "Revisado"),
    ]

    empleado = models.ForeignKey(EmpleadoProfile, on_delete=models.CASCADE)
    empresa = models.ForeignKey(EmpresaProfile, on_delete=models.CASCADE)
    ciudad = models.CharField(max_length=255, null=True, blank=True)
    pais = models.CharField(max_length=255, null=True, blank=True)
    es_internacional = models.BooleanField(default=False,help_text="True si el país es distinto de 'España'")
    destino = models.CharField(max_length=255)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default="EN_REVISION")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    dias_viajados = models.PositiveIntegerField(default = 1)  # 🔹 Días de viaje
    empresa_visitada = models.CharField(max_length=255, null=True, blank=True)  # 🔹 Empresa visitada
    motivo = models.TextField(max_length=500, default="No se ha declarado el motivo por parte del empleado")  # 🔹 Motivo del viaje

    def __str__(self):
        return f"{self.empleado.nombre} viaja a {self.destino} ({self.estado})"

class DiaViaje(models.Model):
    """Modelo para manejar los días de viaje"""

    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, related_name="dias")
    fecha = models.DateField()
    """TODO
     se ha de corregir el estado de los dias exentos y no exentos para la puñetera empresa """
    exento = models.BooleanField(default=True)
    revisado = models.BooleanField(default=False)


class ViajeReviewSnapshot(models.Model):
    """Snapshot publicado de viajes revisados"""

    viaje = models.OneToOneField("Viaje", on_delete=models.CASCADE, related_name="review_snapshot")
    empresa = models.ForeignKey("EmpresaProfile", on_delete=models.CASCADE, related_name="viaje_snapshots")
    empleado = models.ForeignKey("EmpleadoProfile", on_delete=models.CASCADE, related_name="viaje_snapshots")
    estado = models.CharField(max_length=15, choices=Viaje.ESTADO_CHOICES)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    ciudad = models.CharField(max_length=255, null=True, blank=True)
    pais = models.CharField(max_length=255, null=True, blank=True)
    es_internacional = models.BooleanField(default=False)
    destino = models.CharField(max_length=255)
    dias_viajados = models.PositiveIntegerField(default=1)
    empresa_visitada = models.CharField(max_length=255, null=True, blank=True)
    motivo = models.TextField(max_length=500, null=True, blank=True)
    published_at = models.DateTimeField(auto_now_add=True)
    source_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Snapshot Viaje {self.viaje_id} ({self.estado})"


class DiaViajeReviewSnapshot(models.Model):
    """Snapshot publicado de días asociados a viajes revisados"""

    dia = models.OneToOneField("DiaViaje", on_delete=models.CASCADE, related_name="review_snapshot")
    viaje_snapshot = models.ForeignKey(
        "ViajeReviewSnapshot",
        on_delete=models.CASCADE,
        related_name="dias_snapshot"
    )
    fecha = models.DateField()
    exento = models.BooleanField(default=True)
    revisado = models.BooleanField(default=False)
    published_at = models.DateTimeField(auto_now_add=True)
    source_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Snapshot Día {self.dia_id} (exento={self.exento})"


class Gasto(models.Model):
    """Modelo de gastos asociados a viajes"""

    ESTADO_CHOICES = [
        ("PENDIENTE", "Pendiente"),
        ("APROBADO", "Aprobado"),
        ("RECHAZADO", "Rechazado"),
        ("JUSTIFICAR", "Justificante solicitado")

    ]

    empleado = models.ForeignKey(EmpleadoProfile, on_delete=models.CASCADE)
    empresa = models.ForeignKey(EmpresaProfile, on_delete=models.CASCADE)
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, null=True, blank=True)
    dia = models.ForeignKey(DiaViaje, on_delete=models.CASCADE,null=True,blank=True, related_name="gastos")
    concepto = models.TextField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default="PENDIENTE")
    comprobante = models.FileField(upload_to="comprobantes/", null=True, blank=True)
    fecha_gasto = models.DateField(null=True, blank=True , help_text="Fecha del gasto")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.concepto} - {self.estado}"


class GastoReviewSnapshot(models.Model):
    """Snapshot publicado de gastos revisados"""

    gasto = models.OneToOneField("Gasto", on_delete=models.CASCADE, related_name="review_snapshot")
    viaje_snapshot = models.ForeignKey(
        "ViajeReviewSnapshot",
        on_delete=models.CASCADE,
        related_name="gastos_snapshot",
        null=True,
        blank=True
    )
    empresa = models.ForeignKey("EmpresaProfile", on_delete=models.CASCADE, related_name="gasto_snapshots")
    empleado = models.ForeignKey("EmpleadoProfile", on_delete=models.CASCADE, related_name="gasto_snapshots")
    concepto = models.TextField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=10, choices=Gasto.ESTADO_CHOICES)
    fecha_gasto = models.DateField(null=True, blank=True, help_text="Fecha del gasto")
    published_at = models.DateTimeField(auto_now_add=True)
    source_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Snapshot Gasto {self.gasto_id} ({self.estado})"


class Notificacion(models.Model):
    TIPO_VIAJE_SOLICITADO = "VIAJE_SOLICITADO"
    TIPO_VIAJE_APROBADO = "VIAJE_APROBADO"
    TIPO_GASTO_REGISTRADO = "GASTO_REGISTRADO"
    TIPO_REVISION_FECHA_LIMITE = "REVISION_FECHA_LIMITE"

    TIPOS_NOTIFICACION = [
        (TIPO_VIAJE_SOLICITADO, "Viaje solicitado"),
        (TIPO_VIAJE_APROBADO, "Viaje aprobado"),
        (TIPO_GASTO_REGISTRADO, "Gasto registrado"),
        (TIPO_REVISION_FECHA_LIMITE, "Fecha límite de revisión"),
    ]

    tipo = models.CharField(max_length=50, choices=TIPOS_NOTIFICACION)
    mensaje = models.TextField()
    usuario_destino = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notificaciones")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.tipo} - {self.usuario_destino}"



class Notas(models.Model):
    viaje = models.ForeignKey("Viaje", on_delete=models.CASCADE, related_name="notas")
    empleado = models.ForeignKey("EmpleadoProfile", on_delete=models.CASCADE)
    contenido = models.TextField(max_length=500)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nota para viaje {self.viaje.id} - {self.fecha_creacion.strftime('%Y-%m-%d')}"


class MensajeJustificante(models.Model):
    gasto = models.ForeignKey("Gasto", on_delete=models.CASCADE, related_name="mensajes_justificante",null = True, blank=True)
    autor = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    motivo = models.TextField(max_length=500)
    respuesta = models.TextField(max_length=500, blank=True, null=True)
    archivo_justificante = models.FileField(upload_to="respuestas_justificantes/", null=True, blank=True)
    estado = models.CharField(max_length=20, choices=[("pendiente", "Pendiente"), ("aprobado", "Aprobado"), ("rechazado", "Rechazado")], default="pendiente")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    destinatario = models.ForeignKey("CustomUser", on_delete=models.CASCADE, related_name="mensajes_recibidos", null=True, blank=True, help_text="Usuario que recibe el mensaje")

    def __str__(self):
        return f"Mensaje para Gasto {self.gasto.id} - {self.fecha_creacion.strftime('%Y-%m-%d')}"


class Conversacion(models.Model):
    viaje = models.ForeignKey(
        "Viaje",
        on_delete=models.CASCADE,
        related_name="conversaciones",
        null=True, blank=True,
    )
    gasto = models.ForeignKey(
        "Gasto",
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="conversaciones"
    )
    participantes = models.ManyToManyField(
        "CustomUser",
        related_name="conversaciones"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversación {self.id} ({self.gasto or 'Libre'})"

class Mensaje(models.Model):
    conversacion = models.ForeignKey(
        "Conversacion",
        on_delete=models.CASCADE,
        related_name="mensajes"
    )
    autor = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE
    )
    contenido = models.TextField(max_length=1000)
    archivo = models.FileField(
        upload_to="mensajes_adjuntos/",
        null=True, blank=True
    )
    gasto = models.ForeignKey(
        "Gasto",
        on_delete=models.CASCADE,
        null=True, blank=True,
        help_text="Sólo para mensajes de solicitud/entrega de justificante"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.autor.username} @ {self.fecha_creacion:%Y-%m-%d %H:%M}"


class ConversacionLectura(models.Model):
    """Almacena el último instante en que un usuario leyó una conversación."""

    conversacion = models.ForeignKey(
        "Conversacion",
        on_delete=models.CASCADE,
        related_name="lecturas"
    )
    usuario = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        related_name="lecturas_conversacion"
    )
    last_read_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("conversacion", "usuario")
        verbose_name = "Lectura de conversación"
        verbose_name_plural = "Lecturas de conversación"

    def __str__(self):
        return f"Lectura conversacion {self.conversacion_id} - {self.usuario_id}"
