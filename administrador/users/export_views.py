import csv
import os
import zipfile
from io import BytesIO, StringIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from users.models import Viaje, EmpresaProfile, EmpleadoProfile, Gasto


class ExportMasterCSVView(APIView):
    """Exporta los viajes de empleados de todas las empresas (MASTER only)."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "MASTER":
            return HttpResponse("No autorizado", status=403)

        viajes = Viaje.objects.filter(estado="FINALIZADO").select_related(
            "empresa", "empleado"
        )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="viajes_todas_empresas.csv"'
        )

        writer = csv.writer(response, delimiter=";")
        writer.writerow(
            [
                "Empresa",
                "Empleado",
                "Destino",
                "Fecha Inicio",
                "Fecha Fin",
                "Días Exentos",
                "Días No Exentos",
                "Motivo",
            ]
        )

        for viaje in viajes:
            dias = viaje.dias.all()
            writer.writerow(
                [
                    viaje.empresa.nombre_empresa,
                    f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                    viaje.destino,
                    viaje.fecha_inicio.strftime("%Y-%m-%d"),
                    viaje.fecha_fin.strftime("%Y-%m-%d"),
                    dias.filter(exento=True).count(),
                    dias.filter(exento=False).count(),
                    viaje.motivo.replace("\n", " ").strip(),
                ]
            )

        return response


class ExportEmpresaCSVView(APIView):
    """Exporta los viajes de empleados de la empresa logueada en formato CSV."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "EMPRESA":
            return HttpResponse("No autorizado", status=403)

        try:
            empresa = EmpresaProfile.objects.get(user=request.user)
        except EmpresaProfile.DoesNotExist:
            return HttpResponse("No tienes perfil de empresa asociado", status=403)

        viajes = Viaje.objects.filter(
            empresa=empresa, estado="FINALIZADO"
        ).select_related("empleado")

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{empresa.nombre_empresa}_viajes.csv"'
        )

        writer = csv.writer(response, delimiter=";")
        writer.writerow(
            [
                "Empleado",
                "Destino",
                "Fecha Inicio",
                "Fecha Fin",
                "Días Exentos",
                "Días No Exentos",
                "Motivo",
            ]
        )

        for viaje in viajes:
            dias = viaje.dias.all()
            writer.writerow(
                [
                    f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                    viaje.destino,
                    viaje.fecha_inicio.strftime("%Y-%m-%d"),
                    viaje.fecha_fin.strftime("%Y-%m-%d"),
                    dias.filter(exento=True).count(),
                    dias.filter(exento=False).count(),
                    viaje.motivo.replace("\n", " ").strip(),
                ]
            )

        return response


class ExportViajesGastosView(APIView):
    """Exporta viajes con sus gastos asociados según el rol del usuario"""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Determinar qué viajes puede ver según el rol
        if user.role == "MASTER":
            viajes = (
                Viaje.objects.exclude(estado="CANCELADO")
                .select_related("empresa", "empleado")
                .prefetch_related("dias__gastos")
            )
            filename = "todos_los_viajes_con_gastos.csv"

        elif user.role == "EMPRESA":
            try:
                empresa = EmpresaProfile.objects.get(user=user)
                viajes = (
                    Viaje.objects.filter(empresa=empresa)
                    .exclude(estado="CANCELADO")
                    .select_related("empleado")
                    .prefetch_related("dias__gastos")
                )
                filename = f"{empresa.nombre_empresa}_viajes_con_gastos.csv"
            except EmpresaProfile.DoesNotExist:
                return HttpResponse("No tienes perfil de empresa asociado", status=403)

        elif user.role == "EMPLEADO":
            try:
                empleado = EmpleadoProfile.objects.get(user=user)
                viajes = (
                    Viaje.objects.filter(empleado=empleado)
                    .exclude(estado="CANCELADO")
                    .prefetch_related("dias__gastos")
                )
                filename = (
                    f"{empleado.nombre}_{empleado.apellido}_viajes_con_gastos.csv"
                )
            except EmpleadoProfile.DoesNotExist:
                return HttpResponse("No tienes perfil de empleado asociado", status=403)
        else:
            return HttpResponse("No autorizado", status=403)

        # Crear respuesta CSV
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response, delimiter=";")

        # Headers del CSV
        writer.writerow(
            [
                "Empresa",
                "Empleado",
                "DNI",
                "Destino",
                "País",
                "Ciudad",
                "Fecha Inicio",
                "Fecha Fin",
                "Estado Viaje",
                "Días Totales",
                "Días Exentos",
                "Días No Exentos",
                "Concepto Gasto",
                "Monto",
                "Fecha Gasto",
                "Estado Gasto",
                "Tiene Comprobante",
            ]
        )

        # Procesar cada viaje
        for viaje in viajes:
            dias_totales = viaje.dias_viajados or (
                (viaje.fecha_fin - viaje.fecha_inicio).days + 1
            )
            dias = viaje.dias.all()
            dias_exentos = dias.filter(exento=True).count()
            dias_no_exentos = dias.filter(exento=False).count()

            # Obtener todos los gastos del viaje
            gastos = Gasto.objects.filter(viaje=viaje)

            if gastos.exists():
                # Si hay gastos, crear una fila por cada gasto
                for gasto in gastos:
                    writer.writerow(
                        [
                            viaje.empresa.nombre_empresa,
                            f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                            viaje.empleado.dni,
                            viaje.destino,
                            viaje.pais or "",
                            viaje.ciudad or "",
                            viaje.fecha_inicio.strftime("%Y-%m-%d"),
                            viaje.fecha_fin.strftime("%Y-%m-%d"),
                            viaje.estado,
                            dias_totales,
                            dias_exentos,
                            dias_no_exentos,
                            gasto.concepto,
                            f"{gasto.monto:.2f}",
                            gasto.fecha_gasto.strftime("%Y-%m-%d")
                            if gasto.fecha_gasto
                            else "",
                            gasto.estado,
                            "Sí" if gasto.comprobante else "No",
                        ]
                    )
            else:
                # Si no hay gastos, crear una fila sin información de gastos
                writer.writerow(
                    [
                        viaje.empresa.nombre_empresa,
                        f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                        viaje.empleado.dni,
                        viaje.destino,
                        viaje.pais or "",
                        viaje.ciudad or "",
                        viaje.fecha_inicio.strftime("%Y-%m-%d"),
                        viaje.fecha_fin.strftime("%Y-%m-%d"),
                        viaje.estado,
                        dias_totales,
                        dias_exentos,
                        dias_no_exentos,
                        "Sin gastos registrados",
                        "0.00",
                        "",
                        "N/A",
                        "No",
                    ]
                )

        return response


class ExportEmpleadoIndividualView(APIView):
    """Exporta los viajes con gastos de un empleado específico"""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, empleado_id):
        user = request.user
        empleado = get_object_or_404(EmpleadoProfile, id=empleado_id)

        # Validar permisos
        if user.role == "EMPLEADO":
            # Un empleado solo puede ver sus propios datos
            if empleado.user != user:
                return HttpResponse("No autorizado", status=403)

        elif user.role == "EMPRESA":
            # Una empresa solo puede ver a sus empleados
            try:
                empresa = EmpresaProfile.objects.get(user=user)
                if empleado.empresa != empresa:
                    return HttpResponse("No autorizado", status=403)
            except EmpresaProfile.DoesNotExist:
                return HttpResponse("No tienes perfil de empresa asociado", status=403)

        # MASTER puede ver cualquier empleado

        # Obtener viajes del empleado
        viajes = (
            Viaje.objects.filter(empleado=empleado)
            .exclude(estado="CANCELADO")
            .prefetch_related("dias__gastos")
        )

        # Crear respuesta CSV
        response = HttpResponse(content_type="text/csv")
        filename = f"{empleado.nombre}_{empleado.apellido}_viajes_detallados.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        writer = csv.writer(response, delimiter=";")

        # Headers del CSV
        writer.writerow(
            [
                "Empresa",
                "Empleado",
                "DNI",
                "Destino",
                "País",
                "Ciudad",
                "Fecha Inicio",
                "Fecha Fin",
                "Estado Viaje",
                "Días Totales",
                "Días Exentos",
                "Días No Exentos",
                "Concepto Gasto",
                "Monto",
                "Fecha Gasto",
                "Estado Gasto",
                "Tiene Comprobante",
            ]
        )

        # Procesar cada viaje (mismo código que la vista anterior)
        for viaje in viajes:
            dias_totales = viaje.dias_viajados or (
                (viaje.fecha_fin - viaje.fecha_inicio).days + 1
            )
            dias = viaje.dias.all()
            dias_exentos = dias.filter(exento=True).count()
            dias_no_exentos = dias.filter(exento=False).count()

            gastos = Gasto.objects.filter(viaje=viaje)

            if gastos.exists():
                for gasto in gastos:
                    writer.writerow(
                        [
                            viaje.empresa.nombre_empresa,
                            f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                            viaje.empleado.dni,
                            viaje.destino,
                            viaje.pais or "",
                            viaje.ciudad or "",
                            viaje.fecha_inicio.strftime("%Y-%m-%d"),
                            viaje.fecha_fin.strftime("%Y-%m-%d"),
                            viaje.estado,
                            dias_totales,
                            dias_exentos,
                            dias_no_exentos,
                            gasto.concepto,
                            f"{gasto.monto:.2f}",
                            gasto.fecha_gasto.strftime("%Y-%m-%d")
                            if gasto.fecha_gasto
                            else "",
                            gasto.estado,
                            "Sí" if gasto.comprobante else "No",
                        ]
                    )
            else:
                writer.writerow(
                    [
                        viaje.empresa.nombre_empresa,
                        f"{viaje.empleado.nombre} {viaje.empleado.apellido}",
                        viaje.empleado.dni,
                        viaje.destino,
                        viaje.pais or "",
                        viaje.ciudad or "",
                        viaje.fecha_inicio.strftime("%Y-%m-%d"),
                        viaje.fecha_fin.strftime("%Y-%m-%d"),
                        viaje.estado,
                        dias_totales,
                        dias_exentos,
                        dias_no_exentos,
                        "Sin gastos registrados",
                        "0.00",
                        "",
                        "N/A",
                        "No",
                    ]
                )

        return response
