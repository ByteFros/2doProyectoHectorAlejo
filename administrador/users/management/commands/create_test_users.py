from django.core.management.base import BaseCommand
from users.models import CustomUser, EmpresaProfile, EmpleadoProfile


class Command(BaseCommand):
    help = "Crea usuarios de prueba: 1 MASTER, 1 EMPRESA y 1 EMPLEADO relacionado a la empresa"

    def handle(self, *args, **kwargs):
        # Crear usuario MASTER
        master_username = "master_user"
        if not CustomUser.objects.filter(username=master_username).exists():
            master_user = CustomUser.objects.create_superuser(
                username=master_username,
                email="master@example.com",
                password="master123",
                first_name="Master",
                last_name="Admin",
                role="MASTER"
            )
            self.stdout.write(self.style.SUCCESS(f"✓ Usuario MASTER '{master_username}' creado exitosamente."))
        else:
            self.stdout.write(self.style.WARNING(f"⚠ El usuario MASTER '{master_username}' ya existe."))

        # Crear usuario EMPRESA
        empresa_username = "empresa_test"
        if not CustomUser.objects.filter(username=empresa_username).exists():
            empresa_user = CustomUser.objects.create_user(
                username=empresa_username,
                email="empresa@example.com",
                password="empresa123",
                first_name="Empresa",
                last_name="Test",
                role="EMPRESA"
            )

            # Crear perfil de empresa
            EmpresaProfile.objects.create(
                user=empresa_user,
                nombre_empresa="Empresa de Prueba S.A.",
                nif="B12345678",
                address="Calle Principal 123",
                city="Madrid",
                postal_code="28001",
                correo_contacto="contacto@empresatest.com",
                permisos=True
            )

            self.stdout.write(self.style.SUCCESS(f"✓ Usuario EMPRESA '{empresa_username}' y perfil creados exitosamente."))
        else:
            self.stdout.write(self.style.WARNING(f"⚠ El usuario EMPRESA '{empresa_username}' ya existe."))
            empresa_user = CustomUser.objects.get(username=empresa_username)

        # Crear usuario EMPLEADO
        empleado_username = "empleado_test"
        if not CustomUser.objects.filter(username=empleado_username).exists():
            empleado_user = CustomUser.objects.create_user(
                username=empleado_username,
                email="empleado@example.com",
                password="empleado123",
                first_name="Juan",
                last_name="Pérez",
                role="EMPLEADO"
            )

            # Obtener el perfil de la empresa para relacionarlo
            try:
                empresa_profile = EmpresaProfile.objects.get(user__username=empresa_username)

                # Crear perfil de empleado relacionado a la empresa
                EmpleadoProfile.objects.create(
                    user=empleado_user,
                    empresa=empresa_profile,
                    nombre="Juan",
                    apellido="Pérez",
                    dni="12345678A"
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
        self.stdout.write(f"MASTER   → username: {master_username}   | password: master123")
        self.stdout.write(f"EMPRESA  → username: {empresa_username}  | password: empresa123")
        self.stdout.write(f"EMPLEADO → username: {empleado_username} | password: empleado123")
        self.stdout.write(self.style.SUCCESS("="*60))
