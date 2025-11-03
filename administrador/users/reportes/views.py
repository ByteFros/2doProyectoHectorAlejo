"""
Vistas para reportes y analytics de viajes
"""
from django.db.models import (
    OuterRef, Subquery, Count, Sum, IntegerField, Value, Q
)
from django.db.models.functions import Coalesce, TruncMonth
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import (
    EmpresaProfile,
    Viaje,
    DiaViaje,
    EmpleadoProfile,
    ViajeReviewSnapshot,
    DiaViajeReviewSnapshot,
)
from users.serializers import (
    CompanyTripsSummarySerializer,
    TripsPerMonthSerializer,
    TripsTypeSerializer,
    ExemptDaysSerializer,
    GeneralInfoSerializer
)
from users.common.services import (
    get_user_empresa,
    get_user_empleado,
    get_visible_viajes_queryset,
    get_visible_dias_queryset,
)
from users.common.exceptions import (
    EmpresaProfileNotFoundError,
    EmpleadoProfileNotFoundError,
    UnauthorizedAccessError
)


class CompanyTripsSummaryView(APIView):
    """
    Devuelve resumen de viajes por empresa: viajes, días y días no exentos (ambos estados (EN_REVISION y REVISADO))

    Query Parameters:
    - ?include=empleados : Incluye desglose de empleados para cada empresa

    TODO: Optimizar con Prefetch para reducir queries cuando include=empleados
          Actualmente: 1 query para empresas + N queries para empleados (una por empresa)
          Objetivo: Reducir a 2 queries totales usando Prefetch con anotaciones
          Beneficio: Significativo cuando hay 50+ empresas con empleados
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        include_empleados = 'empleados' in request.query_params.get('include', '')

        if request.user.role == 'MASTER':
            data = self._get_master_summary(include_empleados)
        elif request.user.role == 'EMPRESA':
            empresa = get_user_empresa(request.user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
            visible_viajes = get_visible_viajes_queryset(request.user)
            data = self._get_empresa_summary(empresa, visible_viajes, include_empleados)
        else:
            raise UnauthorizedAccessError("No autorizado para ver resúmenes de empresas")

        serializer = CompanyTripsSummarySerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_master_summary(self, include_empleados: bool):
        """
        Construye el resumen usando los modelos en vivo (acceso MASTER).
        """
        viajes = Viaje.objects.filter(
            empleado__empresa=OuterRef('pk'),
            estado__in=('EN_REVISION', 'REVISADO', 'REABIERTO')
        )

        trips_sq = (
            viajes
            .order_by()
            .values('empleado__empresa')
            .annotate(count=Count('pk'))
            .values('count')
        )

        days_sq = (
            viajes
            .order_by()
            .values('empleado__empresa')
            .annotate(total=Sum('dias_viajados'))
            .values('total')
        )

        exempt_sq = (
            DiaViaje.objects
            .filter(
                viaje__empleado__empresa=OuterRef('pk'),
                exento=True
            )
            .order_by()
            .values('viaje__empleado__empresa')
            .annotate(count=Count('pk'))
            .values('count')
        )

        nonexempt_sq = (
            DiaViaje.objects
            .filter(
                viaje__empleado__empresa=OuterRef('pk'),
                exento=False
            )
            .order_by()
            .values('viaje__empleado__empresa')
            .annotate(count=Count('pk'))
            .values('count')
        )

        empresas = EmpresaProfile.objects.annotate(
            trips=Coalesce(
                Subquery(trips_sq, output_field=IntegerField()),
                Value(0)
            ),
            days=Coalesce(
                Subquery(days_sq, output_field=IntegerField()),
                Value(0)
            ),
            exemptDays=Coalesce(
                Subquery(exempt_sq, output_field=IntegerField()),
                Value(0)
            ),
            nonExemptDays=Coalesce(
                Subquery(nonexempt_sq, output_field=IntegerField()),
                Value(0)
            ),
        )

        data = []
        for empresa in empresas:
            payload = {
                'empresa_id': empresa.id,
                'empresa': empresa.nombre_empresa,
                'trips': empresa.trips,
                'days': empresa.days,
                'exemptDays': empresa.exemptDays,
                'nonExemptDays': empresa.nonExemptDays,
            }
            if include_empleados:
                payload['empleados'] = self._get_master_empleados_stats(empresa)
            data.append(payload)
        return data

    def _get_master_empleados_stats(self, empresa):
        """
        Obtiene estadísticas de empleados para una empresa específica
        utilizando los modelos en vivo (flujo MASTER).
        """
        # Subqueries para cada empleado (ambos estados (EN_REVISION y REVISADO))
        viajes_qs = Viaje.objects.filter(
            empleado=OuterRef('pk')
        )

        dias_qs = DiaViaje.objects.filter(
            viaje__empleado=OuterRef('pk')
        )

        non_exentos_qs = dias_qs.filter(exento=False)
        exentos_qs = dias_qs.filter(exento=True)

        empleados = EmpleadoProfile.objects.filter(empresa=empresa).annotate(
            trips=Coalesce(Subquery(
                viajes_qs.values('empleado')
                .annotate(count=Count('pk'))
                .values('count'),
                output_field=IntegerField()
            ), Value(0)),
            days=Coalesce(Subquery(
                viajes_qs.values('empleado')
                .annotate(total=Sum('dias_viajados'))
                .values('total'),
                output_field=IntegerField()
            ), Value(0)),
            nonExemptDays=Coalesce(Subquery(
                non_exentos_qs.values('viaje__empleado')
                .annotate(count=Count('pk'))
                .values('count'),
                output_field=IntegerField()
            ), Value(0)),
            exemptDays=Coalesce(Subquery(
                exentos_qs.values('viaje__empleado')
                .annotate(count=Count('pk'))
                .values('count'),
                output_field=IntegerField()
            ), Value(0)),
        ).filter(
            Q(trips__gt=0) |
            Q(days__gt=0) |
            Q(nonExemptDays__gt=0) |
            Q(exemptDays__gt=0)
        )

        return [{
            'empleado_id': emp.id,
            'nombre': emp.nombre,
            'apellido': emp.apellido,
            'email': emp.user.email,
            'trips': emp.trips,
            'travelDays': emp.days,
            'exemptDays': emp.exemptDays,
            'nonExemptDays': emp.nonExemptDays,
        } for emp in empleados]

    def _get_empresa_summary(self, empresa, visible_viajes, include_empleados: bool):
        """
        Construye el resumen usando snapshots publicados para EMPRESA.
        """
        snapshots = visible_viajes.queryset.filter(empresa=empresa)

        trips = snapshots.count()
        days = snapshots.aggregate(
            total=Coalesce(Sum('dias_viajados'), Value(0))
        )['total'] or 0

        dias_qs = get_visible_dias_queryset(visible_viajes).filter(
            viaje_snapshot__empresa=empresa
        )
        exempt_days = dias_qs.filter(exento=True).count()
        non_exempt_days = dias_qs.filter(exento=False).count()

        empresa_data = {
            'empresa_id': empresa.id,
            'empresa': empresa.nombre_empresa,
            'trips': trips,
            'days': days,
            'exemptDays': exempt_days,
            'nonExemptDays': non_exempt_days,
        }

        if include_empleados:
            empresa_data['empleados'] = self._get_empresa_empleados_stats(
                empresa,
                snapshots,
                dias_qs
            )

        return [empresa_data]

    def _get_empresa_empleados_stats(self, empresa, snapshots, dias_qs):
        """
        Calcula métricas de empleados a partir de snapshots publicados.
        """
        empleado_ids = list(
            snapshots.values_list('empleado_id', flat=True).distinct()
        )
        if not empleado_ids:
            return []

        empleados = EmpleadoProfile.objects.filter(
            id__in=empleado_ids,
            empresa=empresa
        ).select_related('user')

        trips_agg = {
            row['empleado_id']: row['trips']
            for row in snapshots.values('empleado_id').annotate(
                trips=Count('id')
            )
        }
        days_agg = {
            row['empleado_id']: row['days']
            for row in snapshots.values('empleado_id').annotate(
                days=Coalesce(Sum('dias_viajados'), Value(0))
            )
        }

        exempt_agg = {
            row['viaje_snapshot__empleado_id']: row['total']
            for row in dias_qs.filter(exento=True).values(
                'viaje_snapshot__empleado_id'
            ).annotate(total=Count('id'))
        }
        non_exempt_agg = {
            row['viaje_snapshot__empleado_id']: row['total']
            for row in dias_qs.filter(exento=False).values(
                'viaje_snapshot__empleado_id'
            ).annotate(total=Count('id'))
        }

        data = []
        for empleado in empleados:
            trips = trips_agg.get(empleado.id, 0)
            days = days_agg.get(empleado.id, 0)
            exempt = exempt_agg.get(empleado.id, 0)
            non_exempt = non_exempt_agg.get(empleado.id, 0)

            # Evitar incluir empleados sin métricas relevantes
            if not any([trips, days, exempt, non_exempt]):
                continue

            data.append({
                'empleado_id': empleado.id,
                'nombre': empleado.nombre,
                'apellido': empleado.apellido,
                'email': empleado.user.email,
                'trips': trips,
                'travelDays': days,
                'exemptDays': exempt,
                'nonExemptDays': non_exempt,
            })

        return data


class TripsPerMonthView(APIView):
    """
    Número de viajes iniciados por mes (ambos estados (EN_REVISION y REVISADO)), filtrado según el rol

    Query Parameters:
    - ?year=2024 : Filtra viajes por año específico (ej: 2024, 2025)
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == "EMPRESA":
            empresa = get_user_empresa(user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
        elif user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            if not empleado:
                raise EmpleadoProfileNotFoundError()
        elif user.role != "MASTER":
            raise UnauthorizedAccessError("Rol de usuario no reconocido")

        try:
            visible_viajes = get_visible_viajes_queryset(user)
        except ValueError as exc:
            raise UnauthorizedAccessError(str(exc))

        viajes = visible_viajes.queryset

        # Filtrado por año (opcional)
        year_param = request.query_params.get('year')
        if year_param:
            try:
                year = int(year_param)
                viajes = viajes.filter(fecha_inicio__year=year)
            except ValueError:
                return Response(
                    {"error": f"El parámetro 'year' debe ser un número válido. Recibido: {year_param}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Agrupación por mes y conteo de viajes
        viajes_agrupados = (
            viajes.annotate(month=TruncMonth('fecha_inicio'))
            .values('month')
            .annotate(totalTrips=Count('pk'))
            .order_by('month')
        )

        # Verificar si hay resultados
        if not viajes_agrupados:
            year_msg = f" para el año {year_param}" if year_param else ""
            return Response(
                {
                    "message": f"No se encontraron viajes{year_msg}.",
                    "data": []
                },
                status=status.HTTP_200_OK
            )

        # Serialización de los datos
        data = [
            {'month': v['month'].strftime('%Y-%m'), 'totalTrips': v['totalTrips']}
            for v in viajes_agrupados
        ]

        return Response({
            "year": year_param if year_param else "todos",
            "data": data
        }, status=status.HTTP_200_OK)


class TripsTypeView(APIView):
    """Devuelve el conteo de viajes nacionales vs internacionales, filtrado por rol"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == "EMPRESA":
            empresa = get_user_empresa(user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
        elif user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            if not empleado:
                raise EmpleadoProfileNotFoundError()
        elif user.role != "MASTER":
            raise UnauthorizedAccessError("Rol de usuario no reconocido")

        try:
            visible_viajes = get_visible_viajes_queryset(user)
        except ValueError as exc:
            raise UnauthorizedAccessError(str(exc))

        viajes = visible_viajes.queryset.filter(estado='REVISADO')

        national = viajes.filter(es_internacional=False).count()
        international = viajes.filter(es_internacional=True).count()
        total_days = viajes.aggregate(total=Coalesce(Sum('dias_viajados'), Value(0)))['total'] or 0

        total = national + international

        data = {
            'national': national,
            'international': international,
            'total': total,
            'total_days': total_days
        }

        serializer = TripsTypeSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExemptDaysView(APIView):
    """Devuelve conteo de días exentos vs no exentos (viajes REVISADOS), filtrado por rol"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == "EMPRESA":
            empresa = get_user_empresa(user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
        elif user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            if not empleado:
                raise EmpleadoProfileNotFoundError()
        elif user.role != "MASTER":
            raise UnauthorizedAccessError("Rol de usuario no reconocido")

        try:
            visible_viajes = get_visible_viajes_queryset(user)
        except ValueError as exc:
            raise UnauthorizedAccessError(str(exc))

        dias_qs = get_visible_dias_queryset(visible_viajes)

        if visible_viajes.uses_snapshot:
            exempt_count = dias_qs.filter(exento=True).count()
            non_exempt_count = dias_qs.filter(exento=False).count()
        else:
            dias_qs = dias_qs.filter(viaje__estado='REVISADO')
            exempt_count = dias_qs.filter(exento=True).count()
            non_exempt_count = dias_qs.filter(exento=False).count()

        data = {
            'exempt': exempt_count,
            'nonExempt': non_exempt_count,
        }

        serializer = ExemptDaysSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GeneralInfoView(APIView):
    """Devuelve totales de empresas, empleados y viajes nacionales/internacionales,
       filtrados según el rol del usuario"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # MASTER: todo el sistema
        if user.role == "MASTER":
            companies = EmpresaProfile.objects.count()
            employees = EmpleadoProfile.objects.count()
            viajes_qs = Viaje.objects.filter(estado='REVISADO')

        # EMPRESA: sólo su empresa
        elif user.role == "EMPRESA":
            empresa = get_user_empresa(user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
            companies = 1
            employees = EmpleadoProfile.objects.filter(empresa=empresa).count()
            try:
                visible_viajes = get_visible_viajes_queryset(user)
            except ValueError as exc:
                raise UnauthorizedAccessError(str(exc))
            viajes_qs = visible_viajes.queryset.filter(estado='REVISADO')

        # EMPLEADO: sólo él
        elif user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            if not empleado:
                raise EmpleadoProfileNotFoundError()
            companies = 1
            employees = 1
            try:
                visible_viajes = get_visible_viajes_queryset(user)
            except ValueError as exc:
                raise UnauthorizedAccessError(str(exc))
            viajes_qs = visible_viajes.queryset.filter(estado='REVISADO')

        else:
            raise UnauthorizedAccessError("No autorizado")

        # Ahora contamos nacionales e internacionales
        national = viajes_qs.filter(es_internacional=False).count()
        international = viajes_qs.filter(es_internacional=True).count()

        data = {
            'companies': companies,
            'employees': employees,
            'international_trips': international,
            'national_trips': national,
        }

        serializer = GeneralInfoSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeTripsSummaryView(APIView):
    """Resumen por empleado:

    - EMPRESA: mantiene el listado de empleados con métricas agregadas.
    - EMPLEADO: devuelve resumen personal (viajes revisados, en revisión y días exentos/no exentos).
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            if not empleado:
                raise EmpleadoProfileNotFoundError()

            reviewed_qs = Viaje.objects.filter(empleado=empleado, estado='REVISADO')
            pending_qs = Viaje.objects.filter(
                empleado=empleado,
                estado__in=['EN_REVISION', 'REABIERTO']
            )

            dias_qs = DiaViaje.objects.filter(
                viaje__empleado=empleado,
                viaje__estado='REVISADO'
            )

            nombre_completo = " ".join(filter(None, [empleado.nombre, empleado.apellido])).strip()
            data = {
                "role": "EMPLEADO",
                "employee": {
                    "id": empleado.id,
                    "name": nombre_completo or empleado.user.username,
                    "company": empleado.empresa.nombre_empresa if empleado.empresa else None,
                },
                "summary": {
                    "reviewedTrips": reviewed_qs.count(),
                    "pendingTrips": pending_qs.count(),
                    "exemptDays": dias_qs.filter(exento=True).count(),
                    "nonExemptDays": dias_qs.filter(exento=False).count(),
                }
            }

            return Response(data, status=status.HTTP_200_OK)

        if user.role != "EMPRESA":
            raise UnauthorizedAccessError("Solo EMPRESA o EMPLEADO pueden ver este reporte")

        empresa = get_user_empresa(user)
        if not empresa:
            raise EmpresaProfileNotFoundError()

        # Subqueries para cada empleado (ambos estados (EN_REVISION y REVISADO))
        viajes_qs = Viaje.objects.filter(
            empleado=OuterRef('pk')
        )

        dias_qs = DiaViaje.objects.filter(
            viaje__empleado=OuterRef('pk')
        )

        non_exentos_qs = dias_qs.filter(exento=False)
        exentos_qs = dias_qs.filter(exento=True)

        empleados = EmpleadoProfile.objects.filter(empresa=empresa).annotate(
            trips=Coalesce(Subquery(
                viajes_qs.values('empleado')
                .annotate(count=Count('pk'))
                .values('count'),
                output_field=IntegerField()
            ), Value(0)),
            days=Coalesce(Subquery(
                viajes_qs.values('empleado')
                .annotate(total=Sum('dias_viajados'))
                .values('total'),
                output_field=IntegerField()
            ), Value(0)),
            nonExemptDays=Coalesce(Subquery(
                non_exentos_qs.values('viaje__empleado')
                .annotate(count=Count('pk'))
                .values('count'),
                output_field=IntegerField()
            ), Value(0)),
            exemptDays=Coalesce(Subquery(
                exentos_qs.values('viaje__empleado')
                .annotate(count=Count('pk'))
                .values('count'),
                output_field=IntegerField()
            ), Value(0)),
        ).filter(
            Q(trips__gt=0) |
            Q(days__gt=0) |
            Q(nonExemptDays__gt=0) |
            Q(exemptDays__gt=0)
        )

        data = [{
            'name': f"{e.nombre} {e.apellido}",
            'trips': e.trips,
            'travelDays': e.days,
            'exemptDays': e.exemptDays,
            'nonExemptDays': e.nonExemptDays,
        } for e in empleados]

        return Response(data, status=status.HTTP_200_OK)


class MasterCompanyEmployeesView(APIView):
    """Permite a un usuario MASTER ver los viajes de empleados de una empresa específica (ambos estados (EN_REVISION y REVISADO))"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, empresa_id):
        user = request.user

        if user.role != "MASTER":
            raise UnauthorizedAccessError("Solo MASTER puede acceder a este reporte")

        empresa = get_object_or_404(EmpresaProfile, pk=empresa_id)

        viajes_qs = Viaje.objects.filter(
            empleado=OuterRef('pk')
        )

        dias_qs = DiaViaje.objects.filter(
            viaje__empleado=OuterRef('pk')
        )

        non_exentos_qs = dias_qs.filter(exento=False)
        exentos_qs = dias_qs.filter(exento=True)

        empleados = EmpleadoProfile.objects.filter(empresa=empresa).annotate(
            trips=Coalesce(Subquery(
                viajes_qs.values('empleado')
                    .annotate(count=Count('pk'))
                    .values('count'),
                output_field=IntegerField()
            ), Value(0)),
            days=Coalesce(Subquery(
                viajes_qs.values('empleado')
                    .annotate(total=Sum('dias_viajados'))
                    .values('total'),
                output_field=IntegerField()
            ), Value(0)),
            nonExemptDays=Coalesce(Subquery(
                non_exentos_qs.values('viaje__empleado')
                    .annotate(count=Count('pk'))
                    .values('count'),
                output_field=IntegerField()
            ), Value(0)),
            exemptDays=Coalesce(Subquery(
                exentos_qs.values('viaje__empleado')
                    .annotate(count=Count('pk'))
                    .values('count'),
                output_field=IntegerField()
            ), Value(0)),
        ).filter(
            Q(trips__gt=0) |
            Q(days__gt=0) |
            Q(nonExemptDays__gt=0) |
            Q(exemptDays__gt=0)
        )

        data = [{
            'name': f"{e.nombre} {e.apellido}",
            'trips': e.trips,
            'travelDays': e.days,
            'exemptDays': e.exemptDays,
            'nonExemptDays': e.nonExemptDays,
        } for e in empleados]

        return Response(data, status=status.HTTP_200_OK)
