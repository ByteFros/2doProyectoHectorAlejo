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

from users.models import EmpresaProfile, Viaje, DiaViaje, EmpleadoProfile
from users.serializers import (
    CompanyTripsSummarySerializer,
    TripsPerMonthSerializer,
    TripsTypeSerializer,
    ExemptDaysSerializer,
    GeneralInfoSerializer
)
from users.common.services import get_user_empresa, get_user_empleado
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
        # Solo MASTER o EMPRESA
        if request.user.role not in ('MASTER', 'EMPRESA'):
            raise UnauthorizedAccessError("No autorizado para ver resúmenes de empresas")

        # Detectar si se solicita incluir empleados
        include_empleados = 'empleados' in request.query_params.get('include', '')

        # TODO: Implementar Prefetch aquí cuando include_empleados=True

        # Base de empresas permitidas según el rol
        qs = EmpresaProfile.objects.all()
        if request.user.role == 'EMPRESA':
            empresa = get_user_empresa(request.user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
            qs = qs.filter(pk=empresa.pk)

        # Base de viajes (ambos estados (EN_REVISION y REVISADO)) por empresa
        viajes = Viaje.objects.filter(
            empleado__empresa=OuterRef('pk')
        )

        # Subquery para trips (número de viajes, ambos estados (EN_REVISION y REVISADO))
        trips_sq = (
            viajes
            .order_by()
            .values('empleado__empresa')
            .annotate(count=Count('pk'))
            .values('count')
        )

        # Subquery para days (suma de dias_viajados)
        days_sq = (
            viajes
            .order_by()
            .values('empleado__empresa')
            .annotate(total=Sum('dias_viajados'))
            .values('total')
        )

        # Subquery para exemptDays (días exentos)
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

        # Subquery para nonExemptDays (días no exentos)
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

        # Annotate la QS principal
        qs = qs.annotate(
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

        # Serializar la respuesta
        data = []
        for e in qs:
            empresa_data = {
                'empresa_id': e.id,
                'empresa': e.nombre_empresa,
                'trips': e.trips,
                'days': e.days,
                'exemptDays': e.exemptDays,
                'nonExemptDays': e.nonExemptDays,
            }

            # Si se solicita, agregar desglose de empleados
            if include_empleados:
                empresa_data['empleados'] = self._get_empleados_stats(e)

            data.append(empresa_data)

        serializer = CompanyTripsSummarySerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_empleados_stats(self, empresa):
        """
        Obtiene estadísticas de empleados para una empresa específica
        Reutiliza la lógica de EmployeeTripsSummaryView
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
        viajes = Viaje.objects.all()

        # Filtrado por rol
        if user.role == "EMPRESA":
            empresa = get_user_empresa(user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
            viajes = viajes.filter(empleado__empresa=empresa)

        elif user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            if not empleado:
                raise EmpleadoProfileNotFoundError()
            viajes = viajes.filter(empleado=empleado)

        elif user.role != "MASTER":
            raise UnauthorizedAccessError("Rol de usuario no reconocido")

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

        # Base queryset
        viajes = Viaje.objects.filter(estado='REVISADO')

        # Filtrado por rol
        if user.role == "EMPRESA":
            empresa = get_user_empresa(user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
            viajes = viajes.filter(empleado__empresa=empresa)

        elif user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            if not empleado:
                raise EmpleadoProfileNotFoundError()
            viajes = viajes.filter(empleado=empleado)

        elif user.role != "MASTER":
            raise UnauthorizedAccessError("Rol de usuario no reconocido")

        # Conteo nacional vs internacional
        national = viajes.filter(es_internacional=False).count()
        international = viajes.filter(es_internacional=True).count()
        total_days = viajes.aggregate(total=Coalesce(Sum('dias_viajados'), Value(0)))['total']

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
        qs = DiaViaje.objects.filter(viaje__estado='REVISADO')

        # Filtrado por rol
        if user.role == "EMPRESA":
            empresa = get_user_empresa(user)
            if not empresa:
                raise EmpresaProfileNotFoundError()
            qs = qs.filter(viaje__empleado__empresa=empresa)

        elif user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            if not empleado:
                raise EmpleadoProfileNotFoundError()
            qs = qs.filter(viaje__empleado=empleado)

        elif user.role != "MASTER":
            raise UnauthorizedAccessError("Rol de usuario no reconocido")

        exempt_count = qs.filter(exento=True).count()
        non_exempt_count = qs.filter(exento=False).count()

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
            viajes_qs = Viaje.objects.filter(
                estado='REVISADO',
                empleado__empresa=empresa
            )

        # EMPLEADO: sólo él
        elif user.role == "EMPLEADO":
            empleado = get_user_empleado(user)
            if not empleado:
                raise EmpleadoProfileNotFoundError()
            companies = 1
            employees = 1
            viajes_qs = Viaje.objects.filter(
                estado='REVISADO',
                empleado=empleado
            )

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
