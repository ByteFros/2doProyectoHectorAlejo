import csv
import io

from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser

from .models import EmpleadoProfile, EmpresaProfile, CustomUser
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import EmpresaProfileSerializer, EmpleadoProfileSerializer
from django.db import IntegrityError, transaction


class RegisterEmpresaView(APIView):
    """Endpoint para registrar una nueva empresa con un usuario asociado"""
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden crear empresas

    def post(self, request):
        data = request.data  # 🔹 Recibe los datos del formulario

        try:
            # 🔹 Verificamos si ya existe un usuario con ese correo o NIF
            if CustomUser.objects.filter(email=data["correo_contacto"]).exists():
                return Response({"error": "Ya existe una empresa con este correo"}, status=status.HTTP_400_BAD_REQUEST)
            if EmpresaProfile.objects.filter(nif=data["nif"]).exists():
                return Response({"error": "El NIF ya está registrado en la BBDD"}, status=status.HTTP_400_BAD_REQUEST)

            # 🔹 Creamos el usuario con el rol EMPRESA y asignamos la contraseña "empresa"
            user = CustomUser.objects.create(
                username=data["nombre_empresa"],  # Se usa el nombre de la empresa como username
                email=data["correo_contacto"],
                role="EMPRESA"
            )
            user.set_password("empresa")  # ✅ Se asigna la contraseña por defecto
            user.save()

            # 🔹 Creamos el perfil de la empresa asociado al usuario recién creado
            empresa = EmpresaProfile.objects.create(
                user=user,
                nombre_empresa=data["nombre_empresa"],
                nif=data["nif"],
                address=data.get("address", ""),  # 🔹 Si no existe, asigna cadena vacía
                city=data.get("city", ""),
                postal_code=data.get("postal_code", ""),
                correo_contacto=data["correo_contacto"],
                permisos=data.get("permisos", False)
            )

            return Response(EmpresaProfileSerializer(empresa).data, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response({"error": "Error de integridad: NIF o email ya registrado"},
                            status=status.HTTP_400_BAD_REQUEST)

        except KeyError as e:
            return Response({"error": f"Falta el campo {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class EliminarEmpleadoView(APIView):
    """Permite a una EMPRESA eliminar a sus empleados"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, empleado_id):
        """La EMPRESA puede eliminar a un empleado de su empresa"""
        if request.user.role != "EMPRESA":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        try:
            empleado = EmpleadoProfile.objects.get(id=empleado_id, empresa__user=request.user)
            empleado.user.delete()  # Elimina también el usuario relacionado
            empleado.delete()
            return Response({"message": "Empleado eliminado correctamente."}, status=status.HTTP_204_NO_CONTENT)
        except EmpleadoProfile.DoesNotExist:
            return Response({"error": "Empleado no encontrado o no pertenece a tu empresa."},
                            status=status.HTTP_404_NOT_FOUND)

class RegisterEmployeeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Registrar empleado a la empresa asociada"""
        if request.user.role != "EMPRESA":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        empresa = EmpresaProfile.objects.filter(user=request.user).first()

        if not empresa:
            return Response({"error": "No tienes un perfil de empresa registrado"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        nombre = data.get("nombre", "").strip()
        apellido = data.get("apellido", "").strip()
        dni = data.get("dni", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()  # 🔹 Si no se proporciona, usa "empleado"

        if not password:
            password = "empleado"

        if not nombre or not apellido or not dni:
            return Response({"error": "Nombre, Apellido y DNI son obligatorios"}, status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(username=dni).exists():
            return Response({"error": "El DNI ya está registrado"}, status=status.HTTP_400_BAD_REQUEST)

        if not email:
            nombre_empresa = empresa.nombre_empresa.lower().replace(" ", "")
            email = f"{nombre.lower()}.{apellido.lower()}@{nombre_empresa}.com"

        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "El email ya está registrado"}, status=status.HTTP_400_BAD_REQUEST)

        # 🔹 Crear usuario asegurando que la contraseña se encripta correctamente
        user = CustomUser(
            username=f"{nombre}{apellido}",
            email=email,
            role="EMPLEADO"
        )
        user.set_password(password)  # ✅ Encripta la contraseña correctamente
        user.save()

        empleado = EmpleadoProfile.objects.create(
            user=user,
            empresa=empresa,
            nombre=nombre,
            apellido=apellido,
            dni=dni
        )

        return Response(EmpleadoProfileSerializer(empleado).data, status=status.HTTP_201_CREATED)

class BatchRegisterEmployeesView(APIView):
    """Permite a una empresa registrar empleados en lote desde un archivo CSV"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)  # Soporta archivos

    def post(self, request):
        """Procesa el archivo CSV y registra empleados"""
        if request.user.role != "EMPRESA":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        empresa = EmpresaProfile.objects.filter(user=request.user).first()
        if not empresa:
            return Response({"error": "No tienes un perfil de empresa registrado"}, status=status.HTTP_404_NOT_FOUND)

        if "file" not in request.FILES:
            return Response({"error": "Debe proporcionar un archivo"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES["file"]
        decoded_file = file.read().decode("utf-8").splitlines()
        reader = csv.reader(decoded_file)

        empleados_registrados = []
        empleados_omitidos = []
        errores = []

        next(reader, None)  # ✅ Omite la primera fila (Encabezados)

        with transaction.atomic():  # ✅ Usa rollback en caso de error
            for row in reader:
                try:
                    nombre, apellido, dni, email = row  # 🔹 Eliminamos la contraseña del CSV

                    if not nombre or not apellido or not dni:
                        errores.append({"dni": dni, "error": "Nombre, Apellido y DNI son obligatorios"})
                        continue

                    username = f"{nombre}{apellido}".replace(" ", "").lower()

                    # ✅ Verificar si el empleado ya está en la empresa
                    if EmpleadoProfile.objects.filter(empresa=empresa, dni=dni).exists():
                        empleados_omitidos.append({"dni": dni, "mensaje": "Ya registrado en la empresa"})
                        continue  # 🔹 Saltar la creación de este usuario

                    if not email:
                        nombre_empresa = empresa.nombre_empresa.lower().replace(" ", "")
                        email = f"{nombre.lower()}.{apellido.lower()}@{nombre_empresa}.com"

                    if CustomUser.objects.filter(email=email).exists():
                        errores.append({"dni": dni, "error": "El email ya está registrado"})
                        continue

                    if CustomUser.objects.filter(username=username).exists():
                        errores.append({"dni": dni, "error": "El username ya está registrado"})
                        continue

                    # 🔹 Crear usuario con contraseña fija
                    default_password = "empleado"  # ✅ Contraseña por defecto
                    user = CustomUser.objects.create(
                        username=username,
                        email=email,
                        role="EMPLEADO",
                    )
                    user.set_password(default_password)
                    user.is_active = True  # ✅ Asegurar que el usuario esté activo
                    user.save()

                    empleado = EmpleadoProfile.objects.create(
                        user=user,
                        empresa=empresa,
                        nombre=nombre,
                        apellido=apellido,
                        dni=dni
                    )

                    empleados_registrados.append(EmpleadoProfileSerializer(empleado).data)

                except Exception as e:
                    errores.append({"dni": dni, "error": str(e)})

        return Response({
            "empleados_registrados": empleados_registrados,
            "empleados_omitidos": empleados_omitidos,
            "errores": errores
        }, status=201)

class EmpresaManagementView(APIView):
    """Gestiona empresas: listar, modificar permisos, eliminar"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """MASTER: Listar todas las empresas"""
        if request.user.role != "MASTER":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        empresas = EmpresaProfile.objects.all()
        serializer = EmpresaProfileSerializer(empresas, many=True)
        return Response(serializer.data, status=200)

    def put(self, request, empresa_id):
        """MASTER: Actualizar permisos de autogestión"""
        if request.user.role != "MASTER":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        try:
            empresa = EmpresaProfile.objects.get(id=empresa_id)
            permisos = request.data.get("permisos")

            if permisos is None:
                return Response({"error": "El campo 'permisos' es requerido."}, status=400)

            empresa.permisos = permisos
            empresa.save()

            return Response({"message": "Permisos actualizados correctamente."}, status=200)
        except EmpresaProfile.DoesNotExist:
            return Response({"error": "Empresa no encontrada."}, status=404)

    def delete(self, request, empresa_id):
        """MASTER: Eliminar empresa"""
        if request.user.role != "MASTER":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        try:
            empresa = EmpresaProfile.objects.get(id=empresa_id)

            user = empresa.user
            empresa.delete()

            if user and user.id:
                user.delete()

            return Response({"message": "Empresa eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)

        except EmpresaProfile.DoesNotExist:
            return Response({"error": "Empresa no encontrada."}, status=status.HTTP_404_NOT_FOUND)
