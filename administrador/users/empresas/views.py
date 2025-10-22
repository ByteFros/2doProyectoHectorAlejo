"""
Vistas para gestión de empresas y empleados
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import EmpresaProfile, EmpleadoProfile
from users.serializers import EmpresaProfileSerializer, EmpleadoProfileSerializer, EmpresaPendingSerializer
from users.common.services import get_user_empresa
from users.common.exceptions import EmpresaProfileNotFoundError, UnauthorizedAccessError

from .serializers import (
    EmpresaCreateSerializer,
    EmpleadoCreateSerializer,
    BatchEmployeeUploadSerializer,
    EmpresaUpdatePermissionsSerializer
)
from .services import (
    create_empresa,
    update_empresa_permissions,
    delete_empresa,
    create_empleado,
    delete_empleado,
    process_employee_csv,
    get_companies_with_pending_reviews,
    get_employees_with_pending_reviews
)


class RegisterEmpresaView(APIView):
    """
    Registra una nueva empresa con su usuario asociado.
    Solo usuarios autenticados (generalmente MASTER) pueden crear empresas.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request):
        serializer = EmpresaCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            empresa = create_empresa(serializer.validated_data)
            return Response(
                EmpresaProfileSerializer(empresa).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RegisterEmployeeView(APIView):
    """
    Registra un empleado individual asociado a la empresa del usuario autenticado.
    Solo usuarios con rol EMPRESA pueden registrar empleados.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Validar rol
        if request.user.role != "EMPRESA":
            raise UnauthorizedAccessError("Solo empresas pueden registrar empleados")

        # Obtener empresa del usuario
        empresa = get_user_empresa(request.user)
        if not empresa:
            raise EmpresaProfileNotFoundError()

        # Validar datos
        serializer = EmpleadoCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Crear empleado
        try:
            empleado = create_empleado(
                empresa=empresa,
                **serializer.validated_data
            )
            return Response(
                EmpleadoProfileSerializer(empleado).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BatchRegisterEmployeesView(APIView):
    """
    Registra empleados en lote desde un archivo CSV.
    Solo usuarios con rol EMPRESA pueden usar esta funcionalidad.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        # Validar rol
        if request.user.role != "EMPRESA":
            raise UnauthorizedAccessError("Solo empresas pueden registrar empleados")

        # Obtener empresa
        empresa = get_user_empresa(request.user)
        if not empresa:
            raise EmpresaProfileNotFoundError()

        # Validar archivo
        serializer = BatchEmployeeUploadSerializer(data=request.FILES)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Procesar CSV
        csv_file = serializer.validated_data['file']
        resultado = process_employee_csv(empresa, csv_file)

        # Serializar empleados registrados
        empleados_data = [
            EmpleadoProfileSerializer(emp).data
            for emp in resultado['empleados_registrados']
        ]

        return Response({
            "empleados_registrados": empleados_data,
            "empleados_omitidos": resultado['empleados_omitidos'],
            "errores": resultado['errores']
        }, status=status.HTTP_201_CREATED)


class EliminarEmpleadoView(APIView):
    """
    Elimina un empleado de la empresa del usuario autenticado.
    Solo usuarios con rol EMPRESA pueden eliminar sus propios empleados.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, empleado_id):
        # Validar rol
        if request.user.role != "EMPRESA":
            raise UnauthorizedAccessError("Solo empresas pueden eliminar empleados")

        # Obtener y validar empleado
        try:
            empleado = EmpleadoProfile.objects.get(
                id=empleado_id,
                empresa__user=request.user
            )
        except EmpleadoProfile.DoesNotExist:
            return Response(
                {"error": "Empleado no encontrado o no pertenece a tu empresa"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Eliminar empleado
        delete_empleado(empleado)
        return Response(
            {"message": "Empleado eliminado correctamente"},
            status=status.HTTP_204_NO_CONTENT
        )


class EmpresaManagementView(APIView):
    """
    Gestión de empresas: listar, actualizar permisos y eliminar.
    Solo usuarios con rol MASTER pueden usar estas operaciones.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Lista todas las empresas (solo MASTER)"""
        if request.user.role != "MASTER":
            raise UnauthorizedAccessError("Solo MASTER puede listar empresas")

        empresas = EmpresaProfile.objects.all()
        serializer = EmpresaProfileSerializer(empresas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, empresa_id):
        """Actualiza permisos de una empresa (solo MASTER)"""
        if request.user.role != "MASTER":
            raise UnauthorizedAccessError("Solo MASTER puede actualizar permisos")

        empresa = get_object_or_404(EmpresaProfile, id=empresa_id)

        serializer = EmpresaUpdatePermissionsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        update_empresa_permissions(empresa, serializer.validated_data['permisos'])

        return Response(
            {"message": "Permisos actualizados correctamente"},
            status=status.HTTP_200_OK
        )

    def delete(self, request, empresa_id):
        """Elimina una empresa (solo MASTER)"""
        if request.user.role != "MASTER":
            raise UnauthorizedAccessError("Solo MASTER puede eliminar empresas")

        empresa = get_object_or_404(EmpresaProfile, id=empresa_id)
        delete_empresa(empresa)

        return Response(
            {"message": "Empresa eliminada correctamente"},
            status=status.HTTP_204_NO_CONTENT
        )


class PendingCompaniesView(APIView):
    """
    Lista empresas que tienen empleados con viajes en estado EN_REVISION.
    - MASTER: ve todas
    - EMPRESA con permisos: ve solo su empresa (si aplica)
    - EMPLEADO: no autorizado
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # EMPLEADO no puede ver
        if user.role == 'EMPLEADO':
            raise UnauthorizedAccessError("Los empleados no pueden ver esta información")

        # Obtener empresas con viajes pendientes
        empresas = get_companies_with_pending_reviews()

        # EMPRESA: solo ve la suya si tiene permisos
        if user.role == 'EMPRESA':
            mi_empresa = get_user_empresa(user)
            if not mi_empresa:
                raise EmpresaProfileNotFoundError()

            if not mi_empresa.permisos:
                raise UnauthorizedAccessError("No tienes permisos para gestionar revisiones")

            empresas = empresas.filter(id=mi_empresa.id)

        # MASTER ve todas (sin filtro adicional)

        serializer = EmpresaPendingSerializer(empresas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PendingEmployeesByCompanyView(APIView):
    """
    Lista empleados de una empresa que tienen viajes en estado EN_REVISION.
    - MASTER: ve todos
    - EMPRESA: solo ve sus empleados
    - EMPLEADO: no autorizado
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, empresa_id):
        empresa = get_object_or_404(EmpresaProfile, id=empresa_id)

        # EMPLEADO no autorizado
        if request.user.role == 'EMPLEADO':
            raise UnauthorizedAccessError("Los empleados no pueden ver esta información")

        # EMPRESA: solo sus propios empleados
        if request.user.role == 'EMPRESA':
            mi_empresa = get_user_empresa(request.user)
            if not mi_empresa or mi_empresa.id != empresa.id:
                raise UnauthorizedAccessError("No puedes ver empleados de otras empresas")

        # MASTER: sin restricciones

        # Obtener empleados con viajes pendientes
        empleados = get_employees_with_pending_reviews(empresa)
        serializer = EmpleadoProfileSerializer(empleados, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
