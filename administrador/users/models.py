from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
import uuid
from django.utils.timezone import now
from datetime import timedelta
from django.conf import settings


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
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="empresa_profile")
    nombre_empresa = models.CharField(max_length=255)
    nif = models.CharField(max_length=50, unique=True)  # Identificación Fiscal
    address = models.CharField(max_length=255, null=True, blank=True)  # ✅ Dirección
    city = models.CharField(max_length=100, null=True, blank=True)  # ✅ Ciudad
    postal_code = models.CharField(max_length=10, null=True, blank=True)  # ✅ Código Postal
    correo_contacto = models.EmailField()
    permisos = models.BooleanField(default=False)  # ✅ Permisos

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
    dni = models.CharField(max_length=20, unique=True, default="PENDIENTE")  # 🔹 DNI único

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
    expires_at = models.DateTimeField(default= now() + timedelta(hours=1))

    def save(self,*args, **kwargs):
        """este token tendra 1 hora de validez"""
        if not self.expires_at:
            self.expires_at = now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    def is_valid(self):
        """verificamos si el token es valido"""
        return now() < self.expires_at

class Viaje(models.Model):
    """Modelo para manejar los viajes solicitados por empleados"""

    ESTADO_CHOICES = [
        ("PENDIENTE", "Pendiente"),
        ("EN_CURSO", "En curso"),
        ("FINALIZADO", "Finalizado"),
        ("CANCELADO", "Cancelado"),
    ]

    empleado = models.ForeignKey(EmpleadoProfile, on_delete=models.CASCADE)
    empresa = models.ForeignKey(EmpresaProfile, on_delete=models.CASCADE)
    destino = models.CharField(max_length=255)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default="PENDIENTE")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    dias_viajados = models.PositiveIntegerField(default = 1)  # 🔹 Días de viaje
    empresa_visitada = models.CharField(max_length=255, null=True, blank=True)  # 🔹 Empresa visitada
    motivo = models.TextField(max_length=500, default="No se ha declarado el motivo por parte del empleado")  # 🔹 Motivo del viaje

    def __str__(self):
        return f"{self.empleado.nombre} viaja a {self.destino} ({self.estado})"

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
    viaje = models.ForeignKey(Viaje, on_delete=models.CASCADE, null =True, blank= True)  # 🔹 Ahora es obligatorio asociarlo a un viaje
    concepto = models.TextField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default="PENDIENTE")
    comprobante = models.FileField(upload_to="comprobantes/", null=True, blank=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.concepto} - {self.estado}"


class Notificacion(models.Model):
    TIPOS_NOTIFICACION = [
        ("VIAJE_SOLICITADO", "Viaje solicitado"),
        ("VIAJE_APROBADO", "Viaje aprobado"),
        ("GASTO_REGISTRADO", "Gasto registrado"),
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
    gasto = models.ForeignKey("Gasto", on_delete=models.CASCADE, related_name="mensajes_justificante")
    autor = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    motivo = models.TextField(max_length=500)
    respuesta = models.TextField(max_length=500, blank=True, null=True)
    archivo_justificante = models.FileField(upload_to="respuestas_justificantes/", null=True, blank=True)
    estado = models.CharField(max_length=20, choices=[("pendiente", "Pendiente"), ("aprobado", "Aprobado"), ("rechazado", "Rechazado")], default="pendiente")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mensaje para Gasto {self.gasto.id} - {self.fecha_creacion.strftime('%Y-%m-%d')}"
