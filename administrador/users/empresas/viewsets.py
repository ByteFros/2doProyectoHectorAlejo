"""
ViewSets para gestión de empresas y empleados con DRF.
Usa lógica de negocio de common/services y permissions personalizados.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Prefetch

from users.models import EmpresaProfile, EmpleadoProfile, Viaje
from users.serializers import EmpresaProfileSerializer, EmpleadoProfileSerializer
from users.common.services import filter_queryset_by_empresa, get_user_empresa
from users.common.exceptions import EmpresaProfileNotFoundError

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
    process_employee_csv
)
from .permissions import (
    IsMaster,
    IsMasterOrEmpresa,
    CanAccessEmpresa,
    CanAccessEmpleado,
    CanManageEmpleados,
    CanViewPendingReviews
)


class EmpresaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de empresas.

    Acciones disponibles:
    - list: GET /empresas/ - Lista todas las empresas (solo MASTER)
    - create: POST /empresas/ - Crea una empresa (solo MASTER)
    - retrieve: GET /empresas/{id}/ - Detalle de empresa
    - update: PUT /empresas/{id}/ - Actualiza empresa completa (solo MASTER)
    - partial_update: PATCH /empresas/{id}/ - Actualiza campos específicos (permisos)
    - destroy: DELETE /empresas/{id}/ - Elimina empresa (solo MASTER)

    Permisos:
    - MASTER: Acceso total a todas las operaciones
    - EMPRESA: Solo puede ver y actualizar su propia empresa
    - EMPLEADO: No tiene acceso
    """
    queryset = EmpresaProfile.objects.select_related('user').all()
    serializer_class = EmpresaProfileSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, CanAccessEmpresa]

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'create':
            return EmpresaCreateSerializer
        elif self.action == 'partial_update' and 'permisos' in self.request.data:
            return EmpresaUpdatePermissionsSerializer
        return EmpresaProfileSerializer

    def get_permissions(self):
        """Define permisos específicos por acción"""
        if self.action in ['create', 'destroy']:
            # Solo MASTER puede crear y eliminar empresas
            return [IsAuthenticated(), IsMaster()]
        elif self.action == 'list':
            # Solo MASTER puede listar todas las empresas
            return [IsAuthenticated(), IsMaster()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Crea una nueva empresa"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            empresa = create_empresa(serializer.validated_data)
            output_serializer = EmpresaProfileSerializer(empresa)
            return Response(
                output_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def partial_update(self, request, *args, **kwargs):
        """
        Actualización parcial de empresa.
        Principalmente para actualizar el campo 'permisos'.
        """
        instance = self.get_object()

        # Si solo se está actualizando permisos
        if 'permisos' in request.data and len(request.data) == 1:
            serializer = EmpresaUpdatePermissionsSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            update_empresa_permissions(instance, serializer.validated_data['permisos'])
            return Response(
                {"message": "Permisos actualizados correctamente"},
                status=status.HTTP_200_OK
            )

        # Actualización parcial normal
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Elimina una empresa y todos sus empleados"""
        instance = self.get_object()
        delete_empresa(instance)
        return Response(
            {"message": "Empresa eliminada correctamente"},
            status=status.HTTP_204_NO_CONTENT
        )


class EmpleadoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de empleados.

    Acciones disponibles:
    - list: GET /empleados/ - Lista empleados (filtrados por empresa)
    - create: POST /empleados/ - Crea un empleado
    - retrieve: GET /empleados/{id}/ - Detalle de empleado
    - update: PUT /empleados/{id}/ - Actualiza empleado completo
    - partial_update: PATCH /empleados/{id}/ - Actualiza campos específicos
    - destroy: DELETE /empleados/{id}/ - Elimina empleado
    - batch_upload: POST /empleados/batch-upload/ - Carga masiva CSV
    - pending: GET /empleados/pending/ - Empleados con viajes EN_REVISION

    Permisos:
    - MASTER: Acceso total a todos los empleados
    - EMPRESA: Solo puede gestionar empleados de su empresa
    - EMPLEADO: Solo puede ver su propio perfil

    Filtros disponibles:
    - ?empresa=1 - Filtrar por empresa (solo MASTER)
    - ?dni=12345678Z - Buscar por DNI
    - ?search=nombre - Buscar por nombre/apellido
    """
    queryset = EmpleadoProfile.objects.select_related('user', 'empresa').all()
    serializer_class = EmpleadoProfileSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, CanAccessEmpleado]
    filterset_fields = ['empresa', 'dni']
    search_fields = ['nombre', 'apellido', 'dni', 'user__email']

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'create':
            return EmpleadoCreateSerializer
        return EmpleadoProfileSerializer

    def get_permissions(self):
        """Define permisos específicos por acción"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageEmpleados()]
        # batch_upload y pending usan sus propios permission_classes en el decorador @action
        return super().get_permissions()

    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario.
        Usa la lógica de common.services.filter_queryset_by_empresa
        """
        queryset = super().get_queryset()
        # Reutilizar la lógica de filtrado de common
        return filter_queryset_by_empresa(self.request.user, queryset)

    def create(self, request, *args, **kwargs):
        """Crea un nuevo empleado asociado a la empresa del usuario"""
        # Validar que el usuario es EMPRESA
        if request.user.role == "EMPRESA":
            empresa = get_user_empresa(request.user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
        elif request.user.role == "MASTER":
            # MASTER debe especificar la empresa
            empresa_id = request.data.get('empresa_id')
            if not empresa_id:
                return Response(
                    {"error": "MASTER debe especificar empresa_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                empresa = EmpresaProfile.objects.get(id=empresa_id)
            except EmpresaProfile.DoesNotExist:
                return Response(
                    {"error": "Empresa no encontrada"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {"error": "No autorizado"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            empleado = create_empleado(
                empresa=empresa,
                **serializer.validated_data
            )
            output_serializer = EmpleadoProfileSerializer(empleado)
            return Response(
                output_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Elimina un empleado y su usuario asociado"""
        instance = self.get_object()
        delete_empleado(instance)
        return Response(
            {"message": "Empleado eliminado correctamente"},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=['post'],
        url_path='batch-upload',
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[IsAuthenticated, CanManageEmpleados]
    )
    def batch_upload(self, request):
        """
        Carga masiva de empleados desde archivo CSV.

        Formato CSV esperado:
        nombre,apellido,dni,email
        Juan,Perez,12345678Z,juan@empresa.com

        Returns:
            {
                "empleados_registrados": [...],
                "empleados_omitidos": [...],
                "errores": [...]
            }
        """
        # Obtener empresa
        if request.user.role == "EMPRESA":
            empresa = get_user_empresa(request.user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
        else:
            return Response(
                {"error": "Solo usuarios EMPRESA pueden usar carga masiva"},
                status=status.HTTP_403_FORBIDDEN
            )

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

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, CanViewPendingReviews]
    )
    def pending(self, request):
        """
        Lista empleados que tienen viajes en estado EN_REVISION.

        Respuesta incluye información del viaje anidada.

        Filtros opcionales:
        - ?empresa=1 - Filtrar por empresa (solo MASTER)

        Returns:
            [
                {
                    "id": 1,
                    "nombre": "Juan",
                    "viajes_pendientes": [
                        {
                            "id": 5,
                            "destino": "Madrid",
                            "estado": "EN_REVISION",
                            ...
                        }
                    ],
                    "total_viajes_pendientes": 1
                }
            ]
        """
        # Base queryset: empleados con viajes EN_REVISION
        queryset = EmpleadoProfile.objects.filter(
            viaje__estado='EN_REVISION'
        ).select_related('user', 'empresa').prefetch_related(
            Prefetch(
                'viaje_set',
                queryset=Viaje.objects.filter(estado='EN_REVISION'),
                to_attr='viajes_pendientes'
            )
        ).distinct()

        # Filtrar por rol
        if request.user.role == "EMPRESA":
            empresa = get_user_empresa(request.user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
            queryset = queryset.filter(empresa=empresa)
        # MASTER ve todos (sin filtro adicional)

        # Serializar con viajes anidados
        data = []
        for empleado in queryset:
            empleado_data = EmpleadoProfileSerializer(empleado).data

            # Agregar viajes pendientes
            viajes_data = []
            for viaje in empleado.viajes_pendientes:
                viajes_data.append({
                    "id": viaje.id,
                    "destino": viaje.destino,
                    "ciudad": viaje.ciudad,
                    "pais": viaje.pais,
                    "fecha_inicio": viaje.fecha_inicio,
                    "fecha_fin": viaje.fecha_fin,
                    "estado": viaje.estado,
                    "dias_viajados": viaje.dias_viajados,
                    "empresa_visitada": viaje.empresa_visitada,
                    "motivo": viaje.motivo,
                    "fecha_solicitud": viaje.fecha_solicitud,
                })

            empleado_data['viajes_pendientes'] = viajes_data
            empleado_data['total_viajes_pendientes'] = len(viajes_data)
            data.append(empleado_data)

        return Response(data, status=status.HTTP_200_OK)
