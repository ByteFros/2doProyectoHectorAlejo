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
from decimal import Decimal
from django.db.models import Prefetch
from django.utils import timezone

from users.models import EmpresaProfile, EmpleadoProfile, Viaje, Gasto
from users.serializers import EmpresaProfileSerializer, EmpleadoProfileSerializer
from users.common.services import (
    filter_queryset_by_empresa,
    get_user_empresa,
    get_periodicity_delta,
    sync_company_review_notification,
    ensure_company_is_up_to_date,
)
from users.common.exceptions import EmpresaProfileNotFoundError

from .serializers import (
    EmpresaCreateSerializer,
    EmpleadoCreateSerializer,
    BatchEmployeeUploadSerializer,
    EmpresaUpdatePermissionsSerializer,
    EmpresaWithEmpleadosSerializer,
    EmpleadoWithViajesSerializer
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
        """Retorna el serializer apropiado según la acción y query params"""
        if self.action == 'create':
            return EmpresaCreateSerializer
        elif self.action == 'partial_update' and 'permisos' in self.request.data and len(self.request.data) == 1:
            return EmpresaUpdatePermissionsSerializer

        # Detectar parámetro 'include' para respuestas anidadas
        if self.action in ['list', 'retrieve']:
            include = self.request.query_params.get('include', '')
            if 'empleados' in include:
                return EmpresaWithEmpleadosSerializer

        return EmpresaProfileSerializer

    def get_queryset(self):
        """Optimiza queries según parámetro 'include'"""
        queryset = super().get_queryset()

        # Optimizar queries según lo que se incluya
        include = self.request.query_params.get('include', '')
        if 'empleados' in include:
            # Prefetch empleados con sus usuarios
            # Nota: el related_name es 'empleados' (ver models.py)
            queryset = queryset.prefetch_related(
                'empleados',
                'empleados__user'
            )

        return queryset

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

        data = request.data.copy()
        manual_value = data.get('manual_release_at')
        if manual_value == '' or manual_value is None:
            data['manual_release_at'] = None

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)

        empresa = serializer.save()

        updated_fields = []
        notification_limit = None

        if 'periodicity' in serializer.validated_data:
            base_dt = empresa.last_release_at or timezone.now()
            empresa.next_release_at = base_dt + get_periodicity_delta(empresa)
            updated_fields.append('next_release_at')

        if 'manual_release_at' in serializer.validated_data:
            # El serializer ya persistió manual_release_at, pero registramos cambio
            notification_limit = empresa.manual_release_at

        if updated_fields:
            empresa.save(update_fields=updated_fields)

        if {'periodicity', 'manual_release_at'} & set(serializer.validated_data.keys()):
            limit = notification_limit or empresa.manual_release_at or empresa.next_release_at
            sync_company_review_notification(empresa, limit_datetime=limit)

        empresa.refresh_from_db()
        response_serializer = self.get_serializer(empresa)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Elimina una empresa y todos sus empleados"""
        instance = self.get_object()
        delete_empresa(instance)
        return Response(
            {"message": "Empresa eliminada correctamente"},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='publish',
        permission_classes=[IsAuthenticated, IsMaster]
    )
    def publish(self, request, pk=None):
        """Permite a MASTER publicar los datos revisados de una empresa inmediatamente."""
        empresa = self.get_object()
        empresa.force_release = True
        empresa.save(update_fields=['force_release'])

        updated = ensure_company_is_up_to_date(empresa)
        empresa.refresh_from_db()

        response_serializer = self.get_serializer(empresa)
        message = "Datos publicados correctamente"
        if not updated:
            message = "No había cambios pendientes para publicar"

        return Response(
            {
                "message": message,
                "empresa": response_serializer.data
            },
            status=status.HTTP_200_OK
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
        """Retorna el serializer apropiado según la acción y query params"""
        if self.action == 'create':
            return EmpleadoCreateSerializer

        # Detectar parámetro 'include' para respuestas anidadas
        if self.action in ['list', 'retrieve']:
            include = self.request.query_params.get('include', '')
            if 'viajes' in include:
                return EmpleadoWithViajesSerializer

        return EmpleadoProfileSerializer

    def get_permissions(self):
        """Define permisos específicos por acción"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageEmpleados()]
        # batch_upload y pending usan sus propios permission_classes en el decorador @action
        return super().get_permissions()

    def get_queryset(self):
        """
        Filtra el queryset según el rol del usuario y optimiza según 'include'.
        Usa la lógica de common.services.filter_queryset_by_empresa
        """
        queryset = super().get_queryset()

        # Optimizar queries según lo que se incluya
        include = self.request.query_params.get('include', '')
        if 'viajes' in include:
            # Prefetch viajes del empleado
            queryset = queryset.prefetch_related('viaje_set')

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
        target_empresa = None
        require_empresa_id = False

        if request.user.role == "EMPRESA":
            target_empresa = get_user_empresa(request.user)
            if not target_empresa:
                raise EmpresaProfileNotFoundError()
        elif request.user.role == "MASTER":
            require_empresa_id = True
        else:
            return Response(
                {"error": "Solo usuarios MASTER o EMPRESA pueden usar carga masiva"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BatchEmployeeUploadSerializer(
            data=request.data,
            require_empresa_id=require_empresa_id
        )
        serializer.is_valid(raise_exception=True)

        if request.user.role == "MASTER":
            empresa_id = serializer.validated_data.get('empresa_id')
            try:
                target_empresa = EmpresaProfile.objects.get(id=empresa_id)
            except EmpresaProfile.DoesNotExist:
                return Response(
                    {"empresa_id": "La empresa especificada no existe"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        csv_file = serializer.validated_data['file']
        resultado = process_employee_csv(target_empresa, csv_file)

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
        Lista empleados que tienen viajes en estado EN_REVISION, REABIERTO o REVISADO.

        Respuesta incluye información del viaje anidada y el total de gastos aprobados (`descuento_viajes`).

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
                        },
                        {
                            "id": 6,
                            "destino": "Lisboa",
                            "estado": "REVISADO",
                            ...
                        }
                    ],
                    "total_viajes_pendientes": 1
                }
            ]
        """
        empresa_filter = None
        empresa_param = request.query_params.get('empresa')

        if request.user.role == "EMPRESA":
            empresa = get_user_empresa(request.user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
            empresa_filter = empresa
        elif request.user.role == "MASTER" and empresa_param:
            try:
                empresa_filter = EmpresaProfile.objects.get(id=empresa_param)
            except EmpresaProfile.DoesNotExist:
                return Response(
                    {"error": f"La empresa con id {empresa_param} no existe"},
                    status=status.HTTP_404_NOT_FOUND
                )

        gastos_aprobados_prefetch = Prefetch(
            'gasto_set',
            queryset=Gasto.objects.filter(estado='APROBADO'),
            to_attr='gastos_aprobados'
        )

        viajes_queryset = (
            Viaje.objects
            .filter(estado__in=['EN_REVISION', 'REABIERTO', 'REVISADO'])
            .prefetch_related(gastos_aprobados_prefetch)
            .order_by('fecha_inicio')
        )
        if empresa_filter:
            viajes_queryset = viajes_queryset.filter(empresa=empresa_filter)

        queryset = (
            EmpleadoProfile.objects.filter(viaje__estado__in=['EN_REVISION', 'REABIERTO', 'REVISADO'])
            .select_related('user', 'empresa')
            .prefetch_related(
            Prefetch(
                'viaje_set',
                queryset=viajes_queryset.order_by('fecha_inicio'),
                to_attr='viajes_pendientes'
            )
            )
            .distinct()
        )

        if empresa_filter:
            queryset = queryset.filter(empresa=empresa_filter)

        # Serializar con viajes anidados
        data = []
        empleados_vistos = set()
        for empleado in queryset.order_by('empresa__nombre_empresa', 'nombre', 'apellido'):
            if empleado.id in empleados_vistos:
                continue
            empleados_vistos.add(empleado.id)

            empleado_data = EmpleadoProfileSerializer(empleado).data

            viajes_data = []
            descuento_total = Decimal('0.00')
            for viaje in getattr(empleado, 'viajes_pendientes', []):
                gastos_aprobados = getattr(viaje, 'gastos_aprobados', [])
                descuento = sum((g.monto for g in gastos_aprobados), Decimal('0.00'))
                descuento = descuento.quantize(Decimal('0.01'))
                descuento_total += descuento

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
                    "descuento_viajes": str(descuento)
                })

            empleado_data['viajes_pendientes'] = viajes_data
            empleado_data['total_viajes_pendientes'] = len(viajes_data)
            empleado_data['descuento_viajes'] = str(descuento_total.quantize(Decimal('0.01')))
            data.append(empleado_data)

        return Response(data, status=status.HTTP_200_OK)
