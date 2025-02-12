from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('MASTER', 'Master'),
        ('EMPRESA', 'Empresa'),
        ('EMPLEADO', 'Empleado'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='EMPLEADO')

    # Si el usuario es EMPRESA, este será su nombre de empresa
    company_name = models.CharField(max_length=255, blank=True, null=True)

    # Si el usuario es EMPLEADO, este campo almacenará su empresa
    company = models.ForeignKey(
        'self',  # Relación con el mismo modelo (Empresa es también un usuario)
        on_delete=models.CASCADE,  # Si la Empresa se elimina, los empleados también
        limit_choices_to={'role': 'EMPRESA'},  # Solo usuarios con rol EMPRESA pueden ser asignados
        blank=True,
        null=True
    )

    def clean(self):
        """Evita que un empleado pertenezca a más de una empresa."""
        if self.role == 'EMPLEADO' and self.company:
            already_exists = CustomUser.objects.filter(role='EMPLEADO', company=self.company, username=self.username).exclude(id=self.id)
            if already_exists.exists():
                raise ValidationError("Este empleado ya está registrado en otra empresa.")

    def save(self, *args, **kwargs):
        """Ejecuta la validación antes de guardar."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} - {self.role}"
