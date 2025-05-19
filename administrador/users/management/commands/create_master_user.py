from django.core.management.base import BaseCommand
from users.models import CustomUser

class Command(BaseCommand):
    help = "Crea un usuario MASTER por defecto"

    def handle(self, *args, **kwargs):
        if not CustomUser.objects.filter(username="admin").exists():
            CustomUser.objects.create_superuser(
                username="admin",
                email="admin@admin.com",
                password="admin123",
                first_name="Admin",
                last_name="Master",
                role="MASTER"
            )
            self.stdout.write(self.style.SUCCESS("Usuario MASTER creado exitosamente."))
        else:
            self.stdout.write(self.style.WARNING("El usuario MASTER ya existe."))