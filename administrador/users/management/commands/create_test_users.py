import os

from django.core.management.base import BaseCommand
from users.models import CustomUser, EmpresaProfile, EmpleadoProfile


class Command(BaseCommand):
    help = "Crea usuarios de prueba: 1 MASTER, 1 EMPRESA y 1 EMPLEADO relacionado a la empresa"

    def handle(self, *args, **kwargs):
        # Configuración mediante variables de entorno con valores por defecto
        master_username = os.getenv("SEED_MASTER_USERNAME", "master_user")
        master_password = os.getenv("SEED_MASTER_PASSWORD", "master123")
        master_email = os.getenv("SEED_MASTER_EMAIL", "master@example.com")

        empresa_username = os.getenv("SEED_EMPRESA_USERNAME", "empresa_test")
        empresa_password = os.getenv("SEED_EMPRESA_PASSWORD", "empresa123")
        empresa_email = os.getenv("SEED_EMPRESA_EMAIL", "empresa@example.com")
        empresa_nombre = os.getenv("SEED_EMPRESA_NAME", "Empresa de Prueba S.A.")
        empresa_nif = os.getenv("SEED_EMPRESA_NIF", "B12345678")
        empresa_address = os.getenv("SEED_EMPRESA_ADDRESS", "Calle Principal 123")
        empresa_city = os.getenv("SEED_EMPRESA_CITY", "Madrid")
        empresa_postal_code = os.getenv("SEED_EMPRESA_POSTAL_CODE", "28001")
        empresa_contact_email = os.getenv("SEED_EMPRESA_CONTACT_EMAIL", "contacto@empresatest.com")
        empresa_periodicity = os.getenv("SEED_EMPRESA_PERIODICITY", EmpresaProfile.PERIODICITY_TRIMESTRAL)

        empleado_username = os.getenv("SEED_EMPLEADO_USERNAME", "empleado_test")
        empleado_password = os.getenv("SEED_EMPLEADO_PASSWORD", "empleado123")
        empleado_email = os.getenv("SEED_EMPLEADO_EMAIL", "empleado@example.com")
        empleado_nombre = os.getenv("SEED_EMPLEADO_NOMBRE", "Juan")
        empleado_apellido = os.getenv("SEED_EMPLEADO_APELLIDO", "Pérez")
        empleado_dni = os.getenv("SEED_EMPLEADO_DNI", "12345678A")

        # Crear usuario MASTER
        if not CustomUser.objects.filter(username=master_username).exists():
            CustomUser.objects.create_superuser(
                username=master_username,
                email=master_email,
                password=master_password,
                first_name="Master",
                last_name="Admin",
                role="MASTER"
            )
            self.stdout.write(self.style.SUCCESS(f"✓ Usuario MASTER '{master_username}' creado exitosamente."))
        else:
            self.stdout.write(self.style.WARNING(f"⚠ El usuario MASTER '{master_username}' ya existe."))

        # Crear usuario EMPRESA
        if not CustomUser.objects.filter(username=empresa_username).exists():
            empresa_user = CustomUser.objects.create_user(
                username=empresa_username,
                email=empresa_email,
                password=empresa_password,
                first_name="Empresa",
                last_name="Test",
                role="EMPRESA"
            )

            # Crear perfil de empresa
            EmpresaProfile.objects.create(
                user=empresa_user,
                nombre_empresa=empresa_nombre,
                nif=empresa_nif,
                address=empresa_address,
                city=empresa_city,
                postal_code=empresa_postal_code,
                correo_contacto=empresa_contact_email,
                permisos=True,
                periodicity=empresa_periodicity,
            )

            self.stdout.write(self.style.SUCCESS(f"✓ Usuario EMPRESA '{empresa_username}' y perfil creados exitosamente."))
        else:
            self.stdout.write(self.style.WARNING(f"⚠ El usuario EMPRESA '{empresa_username}' ya existe."))
            empresa_user = CustomUser.objects.get(username=empresa_username)

        # Crear usuario EMPLEADO
        if not CustomUser.objects.filter(username=empleado_username).exists():
            empleado_user = CustomUser.objects.create_user(
                username=empleado_username,
                email=empleado_email,
                password=empleado_password,
                first_name=empleado_nombre,
                last_name=empleado_apellido,
                role="EMPLEADO"
            )

            # Obtener el perfil de la empresa para relacionarlo
            try:
                empresa_profile = EmpresaProfile.objects.get(user__username=empresa_username)

                # Crear perfil de empleado relacionado a la empresa
                EmpleadoProfile.objects.create(
                    user=empleado_user,
                    empresa=empresa_profile,
                    nombre=empleado_nombre,
                    apellido=empleado_apellido,
                    dni=empleado_dni
                )

                self.stdout.write(self.style.SUCCESS(
                    f"✓ Usuario EMPLEADO '{empleado_username}' creado y relacionado con '{empresa_profile.nombre_empresa}'."
                ))
            except EmpresaProfile.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    "✗ No se pudo encontrar el perfil de empresa para relacionar el empleado."
                ))
                empleado_user.delete()
        else:
            self.stdout.write(self.style.WARNING(f"⚠ El usuario EMPLEADO '{empleado_username}' ya existe."))

        # Resumen final
        self.stdout.write(self.style.SUCCESS("\n" + "="*60))
        self.stdout.write(self.style.SUCCESS("RESUMEN DE USUARIOS CREADOS:"))
        self.stdout.write(self.style.SUCCESS("="*60))
        self.stdout.write(f"MASTER   → username: {master_username}   | password: {master_password}")
        self.stdout.write(f"EMPRESA  → username: {empresa_username}  | password: {empresa_password}")
        self.stdout.write(f"EMPLEADO → username: {empleado_username} | password: {empleado_password}")
        self.stdout.write(self.style.SUCCESS("="*60))
