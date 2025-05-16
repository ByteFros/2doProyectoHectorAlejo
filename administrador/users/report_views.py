# views/report_views.py
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.db.models import (
    OuterRef, Subquery,
    Count, Sum, IntegerField, Value, Q
)
from django.db.models.functions import Coalesce

from .models import EmpresaProfile, Viaje, DiaViaje, EmpleadoProfile
from .serializers import CompanyTripsSummarySerializer, TripsPerMonthSerializer, TripsTypeSerializer, \
    ExemptDaysSerializer, GeneralInfoSerializer


class CompanyTripsSummaryView(APIView):
    """Devuelve resumen de viajes por empresa: viajes, días y días no exentos."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Sólo MASTER o EMPRESA
        if request.user.role not in ('MASTER', 'EMPRESA'):
            return Response({'error': 'No autorizado'}, status=403)

        # Base de viajes FINALIZADOS por empresa
        viajes = Viaje.objects.filter(
            empleado__empresa=OuterRef('pk'),
            estado='FINALIZADO'
        )

        # Subquery para trips (número de viajes finalizados)
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

        # Subquery para nonExemptDays (día_viaje no exentos)
        nonexempt_sq = (
            DiaViaje.objects
            .filter(
                viaje__empleado__empresa=OuterRef('pk'),
                viaje__estado='FINALIZADO',
                exento=False
            )
            .order_by()
            .values('viaje__empleado__empresa')
            .annotate(count=Count('pk'))
            .values('count')
        )


        # Annotate la QS principal
        qs = EmpresaProfile.objects.annotate(
            trips=Coalesce(
                Subquery(trips_sq, output_field=IntegerField()),
                Value(0)
            ),
            days=Coalesce(
                Subquery(days_sq, output_field=IntegerField()),
                Value(0)
            ),
            nonExemptDays=Coalesce(
                Subquery(nonexempt_sq, output_field=IntegerField()),
                Value(0)
            ),
        )

        # Serializar la respuesta
        data = [{
            'empresa_id': e.id,  # ✅ Correcto
            'empresa': e.nombre_empresa,
            'trips': e.trips,
            'days': e.days,
            'nonExemptDays': e.nonExemptDays,
        } for e in qs]

        serializer = CompanyTripsSummarySerializer(data, many=True)
        return Response(serializer.data)


class TripsPerMonthView(APIView):
    """Total de días viajados por mes (solo FINALIZADOS), filtrado según el rol."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        viajes = Viaje.objects.filter(estado='FINALIZADO')

        # 🔹 Filtrado por rol
        if user.role == "EMPRESA":
            try:
                empresa = EmpresaProfile.objects.get(user=user)
                viajes = viajes.filter(empleado__empresa=empresa)
            except EmpresaProfile.DoesNotExist:
                return Response({"error": "No tienes un perfil de empresa asociado"}, status=403)

        elif user.role == "EMPLEADO":
            try:
                empleado = EmpleadoProfile.objects.get(user=user)
                viajes = viajes.filter(empleado=empleado)
            except EmpleadoProfile.DoesNotExist:
                return Response({"error": "No tienes un perfil de empleado asociado"}, status=403)

        elif user.role != "MASTER":
            return Response({"error": "Rol de usuario no reconocido"}, status=403)

        # Agrupación por mes y suma de días
        viajes = (
            viajes.annotate(month=TruncMonth('fecha_inicio'))
            .values('month')
            .annotate(totalDays=Sum('dias_viajados'))
            .order_by('month')
        )

        # Serialización de los datos (sin usar serializer ya que es simple)
        data = [
            {'month': v['month'].strftime('%Y-%m'), 'totalDays': v['totalDays'] or 0}
            for v in viajes
        ]
        return Response(data, status=200)


class TripsTypeView(APIView):
    """Devuelve el conteo de viajes nacionales vs internacionales, filtrado por rol."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Base queryset
        viajes = Viaje.objects.filter(estado='FINALIZADO')

        # 🔹 Filtrado por rol
        if user.role == "EMPRESA":
            try:
                empresa = EmpresaProfile.objects.get(user=user)
                viajes = viajes.filter(empleado__empresa=empresa)
            except EmpresaProfile.DoesNotExist:
                return Response({"error": "No tienes un perfil de empresa asociado"}, status=403)

        elif user.role == "EMPLEADO":
            try:
                empleado = EmpleadoProfile.objects.get(user=user)
                viajes = viajes.filter(empleado=empleado)
            except EmpleadoProfile.DoesNotExist:
                return Response({"error": "No tienes un perfil de empleado asociado"}, status=403)

        elif user.role != "MASTER":
            return Response({"error": "Rol de usuario no reconocido"}, status=403)

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
        return Response(serializer.data)


class ExemptDaysView(APIView):
    """Devuelve conteo de días exentos vs no exentos (viajes FINALIZADOS), filtrado por rol."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = DiaViaje.objects.filter(viaje__estado='FINALIZADO')

        if user.role == "EMPRESA":
            try:
                empresa = EmpresaProfile.objects.get(user=user)
                qs = qs.filter(viaje__empleado__empresa=empresa)
            except EmpresaProfile.DoesNotExist:
                return Response({"error": "No tienes un perfil de empresa asociado"}, status=403)

        elif user.role == "EMPLEADO":
            try:
                empleado = EmpleadoProfile.objects.get(user=user)
                qs = qs.filter(viaje__empleado=empleado)
            except EmpleadoProfile.DoesNotExist:
                return Response({"error": "No tienes un perfil de empleado asociado"}, status=403)

        elif user.role != "MASTER":
            return Response({"error": "Rol de usuario no reconocido"}, status=403)

        exempt_count = qs.filter(exento=True).count()
        non_exempt_count = qs.filter(exento=False).count()

        data = {
            'exempt': exempt_count,
            'nonExempt': non_exempt_count,
        }

        serializer = ExemptDaysSerializer(data)
        return Response(serializer.data)


class GeneralInfoView(APIView):
    """Devuelve totales de empresas, empleados y viajes nacionales/internacionales,
       filtrados según el rol del usuario."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # MASTER: todo el sistema
        if user.role == "MASTER":
            companies = EmpresaProfile.objects.count()
            employees = EmpleadoProfile.objects.count()
            viajes_qs = Viaje.objects.filter(estado='FINALIZADO')

        # EMPRESA: sólo su empresa
        elif user.role == "EMPRESA":
            try:
                empresa = EmpresaProfile.objects.get(user=user)
            except EmpresaProfile.DoesNotExist:
                return Response(
                    {"error": "No tienes un perfil de empresa asociado"},
                    status=403
                )
            companies = 1
            employees = EmpleadoProfile.objects.filter(empresa=empresa).count()
            viajes_qs = Viaje.objects.filter(
                estado='FINALIZADO',
                empleado__empresa=empresa
            )

        # EMPLEADO: sólo él
        elif user.role == "EMPLEADO":
            try:
                empleado = EmpleadoProfile.objects.get(user=user)
            except EmpleadoProfile.DoesNotExist:
                return Response(
                    {"error": "No tienes un perfil de empleado asociado"},
                    status=403
                )
            companies = 1
            employees = 1
            viajes_qs = Viaje.objects.filter(
                estado='FINALIZADO',
                empleado=empleado
            )

        else:
            return Response(
                {"error": "No autorizado"},
                status=403
            )

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
        return Response(serializer.data, status=200)


class EmployeeTripsSummaryView(APIView):
    """Resumen por empleado: viajes, días y días no exentos (solo para EMPRESA)"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != "EMPRESA":
            return Response({'error': 'No autorizado'}, status=403)

        try:
            empresa = EmpresaProfile.objects.get(user=user)
        except EmpresaProfile.DoesNotExist:
            return Response({'error': 'No tienes un perfil de empresa asociado'}, status=403)

        # Subqueries para cada empleado
        viajes_qs = Viaje.objects.filter(
            empleado=OuterRef('pk'),
            estado='FINALIZADO'
        )

        dias_qs = DiaViaje.objects.filter(
            viaje__empleado=OuterRef('pk'),
            viaje__estado='FINALIZADO'
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

        return Response(data, status=200)


class MasterCompanyEmployeesView(APIView):
    """Permite a un usuario MASTER ver los viajes de empleados de una empresa específica"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, empresa_id):
        user = request.user

        if user.role != "MASTER":
            return Response({'error': 'No autorizado'}, status=403)

        try:
            empresa = EmpresaProfile.objects.get(pk=empresa_id)
        except EmpresaProfile.DoesNotExist:
            return Response({'error': 'Empresa no encontrada'}, status=404)

        viajes_qs = Viaje.objects.filter(
            empleado=OuterRef('pk'),
            estado='FINALIZADO'
        )

        dias_qs = DiaViaje.objects.filter(
            viaje__empleado=OuterRef('pk'),
            viaje__estado='FINALIZADO'
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

        return Response(data, status=200)
