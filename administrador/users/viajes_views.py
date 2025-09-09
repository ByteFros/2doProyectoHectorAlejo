import logging
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404

from .models import EmpleadoProfile, Viaje, EmpresaProfile, Notificacion, DiaViaje, Conversacion, Mensaje
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from datetime import datetime, date, timedelta
from .serializers import ViajeSerializer, DiaViajeSerializer, PendingTripSerializer

logger = logging.getLogger(__name__)


class CrearViajeView(APIView):
    """ Permitimos a los empleados crear un nuevo viaje """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "EMPLEADO":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        try:
            empleado = EmpleadoProfile.objects.get(user=request.user)
            data = request.data.copy()
            data["empleado_id"] = empleado.id
            data["empresa_id"] = empleado.empresa.id

            # 🔄 Validar y convertir fechas
            fecha_inicio_str = data.get("fecha_inicio")
            fecha_fin_str = data.get("fecha_fin")

            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
                fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return Response({"error": "Formato de fecha inválido. Usa YYYY-MM-DD."},
                                status=status.HTTP_400_BAD_REQUEST)

            # 🔒 Validar que fecha_fin >= fecha_inicio
            if fecha_fin < fecha_inicio:
                return Response({"error": "La fecha de fin no puede ser anterior a la fecha de inicio."},
                                status=status.HTTP_400_BAD_REQUEST)

            # 🔁 Determinar estado inicial del viaje
            hoy = date.today()
            if fecha_fin < hoy:
                # Viaje ya terminó (fechas pasadas)
                data["estado"] = "FINALIZADO"
            elif fecha_inicio == hoy:
                # Viaje comienza hoy
                data["estado"] = "EN_CURSO"
            elif fecha_inicio > hoy:
                # Viaje futuro
                data["estado"] = "PENDIENTE"
            else:
                # Viaje comenzó en el pasado pero aún no terminó
                data["estado"] = "EN_CURSO"

            # 🔍 Verificar conflicto con otros viajes
            conflicto_viajes = Viaje.objects.filter(
                empleado=empleado,
                fecha_inicio__lte=fecha_fin,
                fecha_fin__gte=fecha_inicio,
                estado__in=["PENDIENTE", "EN_CURSO"]
            ).exists()

            if conflicto_viajes:
                return Response({"error": "Ya tienes un viaje programado en esas fechas."},
                                status=status.HTTP_400_BAD_REQUEST)

            # ✅ Crear viaje
            serializer = ViajeSerializer(data=data)
            if serializer.is_valid():
                viaje = serializer.save()

                # 🔔 Notificar a la empresa
                if empleado.empresa:
                    empresa_usuario = empleado.empresa.user
                    nombre_empleado = f"{empleado.nombre} {empleado.apellido}".strip()

                    Notificacion.objects.create(
                        tipo="VIAJE_SOLICITADO",
                        mensaje=f"{nombre_empleado} ha solicitado un viaje a {viaje.destino}.",
                        usuario_destino=empresa_usuario
                    )

                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except EmpleadoProfile.DoesNotExist:
            return Response({"error": "El usuario no tiene perfil de empleado"}, status=status.HTTP_400_BAD_REQUEST)


class VerificarViajeEnCursoView(APIView):
    """ Verifica si un usuario tiene un viaje en curso """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "EMPLEADO":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        try:
            empleado = EmpleadoProfile.objects.get(user=request.user)
            viaje_en_curso = Viaje.objects.filter(empleado=empleado, estado="EN_CURSO").exists()
            return Response({"tiene_viaje_en_curso": viaje_en_curso}, status=status.HTTP_200_OK)

        except EmpleadoProfile.DoesNotExist:
            return Response({"error": "El usuario no tiene perfil de empleado"}, status=status.HTTP_400_BAD_REQUEST)


# ... el resto del código de las otras views no fue alterado ...


class AprobarRechazarViajeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, viaje_id):
        try:
            viaje = Viaje.objects.get(id=viaje_id)
            empresa = EmpresaProfile.objects.get(user=request.user)

            if viaje.empresa != empresa:
                return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

            nuevo_estado = request.data.get("estado")  # "APROBADO" o "RECHAZADO"
            if nuevo_estado not in ["APROBADO", "RECHAZADO"]:
                return Response({"error": "Estado inválido"}, status=status.HTTP_400_BAD_REQUEST)

            viaje.estado = nuevo_estado
            viaje.save()

            mensaje = f"Tu viaje a {viaje.destino} ha sido {nuevo_estado.lower()}."
            if nuevo_estado == "RECHAZADO":
                motivo = request.data.get("motivo", "Sin motivo especificado")
                mensaje += f" Motivo: {motivo}"

            # 🔹 Crear notificación para el empleado
            notificacion = Notificacion.objects.create(
                tipo=f"VIAJE_{nuevo_estado}",
                mensaje=mensaje,
                usuario_destino=viaje.empleado.user
            )

            return Response({"message": f"Viaje {nuevo_estado.lower()} correctamente."}, status=status.HTTP_200_OK)

        except Viaje.DoesNotExist:
            return Response({"error": "El viaje no existe"}, status=status.HTTP_404_NOT_FOUND)
        except EmpresaProfile.DoesNotExist:
            return Response({"error": "No tienes perfil de empresa"}, status=status.HTTP_403_FORBIDDEN)


class IniciarViajeView(APIView):
    """Permite a un empleado iniciar un viaje aprobado cuando llega la fecha de inicio"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, viaje_id):
        if request.user.role != "EMPLEADO":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        try:
            viaje = Viaje.objects.get(id=viaje_id, empleado__user=request.user)

            """
            # 🔹 Verificar que el viaje está APROBADO
            if viaje.estado != "APROBADO":
                return Response({"error": "Solo puedes iniciar un viaje aprobado"}, status=status.HTTP_400_BAD_REQUEST)
            """

            # 🔹 Verificar que la fecha actual sea mayor o igual a la fecha de inicio

            if date.today() < viaje.fecha_inicio:
                return Response({"error": "Aún no puedes iniciar este viaje, la fecha de inicio no ha llegado"},
                                status=status.HTTP_400_BAD_REQUEST)

            # 🔹 Cambiar estado del viaje a EN_CURSO
            viaje.estado = "EN_CURSO"
            viaje.save()
            return Response({"message": "Viaje iniciado correctamente"}, status=status.HTTP_200_OK)

        except Viaje.DoesNotExist:
            return Response({"error": "Viaje no encontrado o no autorizado"}, status=status.HTTP_404_NOT_FOUND)


class FinalizarViajeView(APIView):
    """Permite al empleado finalizar su viaje y pasar a estado de revisión"""
    permission_classes = [IsAuthenticated]

    def put(self, request, viaje_id):
        # Solo empleados pueden finalizar
        if request.user.role != 'EMPLEADO':
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        viaje = get_object_or_404(Viaje, id=viaje_id, empleado__user=request.user)

        if viaje.estado != 'EN_CURSO':
            return Response({'error': 'Solo puedes finalizar un viaje en curso.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Cambiar a revisión
        viaje.estado = 'EN_REVISION'
        viaje.save()

        # Crear objetos DiaViaje para cada jornada si no existen
        start = viaje.fecha_inicio
        end = viaje.fecha_fin
        delta = (end - start).days
        for i in range(delta + 1):
            fecha = start + timedelta(days=i)
            DiaViaje.objects.get_or_create(viaje=viaje, fecha=fecha)

        return Response({'message': 'Viaje en revisión. Un supervisor procederá a validar los días.'},
                        status=status.HTTP_200_OK)

    class RevisionViajeView(APIView):
        """Permite a usuarios superiores revisar y exentar/aprobar días del viaje"""
        permission_classes = [IsAuthenticated]

        def get(self, request, viaje_id):
            # Solo EMPRESA o MASTER pueden revisar
            if request.user.role not in ('EMPRESA', 'MASTER'):
                return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

            viaje = get_object_or_404(Viaje, id=viaje_id, estado='EN_REVISION')
            dias = viaje.dias.prefetch_related('gastos')
            serializer = DiaViajeSerializer(dias, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        def put(self, request, viaje_id):
            if request.user.role not in ('EMPRESA', 'MASTER'):
                return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

            viaje = get_object_or_404(Viaje, id=viaje_id, estado='EN_REVISION')
            datos = request.data.get('dias', [])

            for dia_data in datos:
                dia = get_object_or_404(DiaViaje, id=dia_data.get('id'), viaje=viaje)
                exento = dia_data.get('exento', False)

                dia.exento = exento
                dia.revisado = True
                dia.save()

                # Actualizar estado de gastos asociados
                estado_nuevo = 'RECHAZADO' if exento else 'APROBADO'
                dia.gastos.update(estado=estado_nuevo)

            # Si todos los días ya revisados, finalizar el viaje
            if viaje.dias.filter(revisado=False).count() == 0:
                viaje.estado = 'FINALIZADO'
                viaje.save()

            return Response({'message': 'Días revisados correctamente.'}, status=status.HTTP_200_OK)


class CancelarViajeView(APIView):
    """Permite a un empleado cancelar un viaje antes de que comience"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, viaje_id):
        if request.user.role != "EMPLEADO":
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        try:
            viaje = Viaje.objects.get(id=viaje_id, empleado__user=request.user)

            # 🔹 Solo se pueden cancelar viajes en estado PENDIENTE
            if viaje.estado != "PENDIENTE":
                return Response({"error": "Solo puedes cancelar un viaje que aún está pendiente"},
                                status=status.HTTP_400_BAD_REQUEST)

            viaje.estado = "CANCELADO"
            viaje.save()

            return Response({"message": "Viaje cancelado correctamente."}, status=status.HTTP_200_OK)

        except Viaje.DoesNotExist:
            return Response({"error": "Viaje no encontrado o no autorizado"}, status=status.HTTP_404_NOT_FOUND)


class ViajeEnCursoView(APIView):
    """Devuelve el viaje actual en curso del empleado autenticado"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "EMPLEADO":
            return Response({"error": "Solo los empleados pueden acceder a esta vista."},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            empleado = EmpleadoProfile.objects.get(user=request.user)
        except EmpleadoProfile.DoesNotExist:
            return Response({"error": "El usuario no tiene perfil de empleado."},
                            status=status.HTTP_400_BAD_REQUEST)

        viaje_en_curso = Viaje.objects.filter(
            empleado=empleado,
            estado="EN_CURSO"
        ).order_by("-fecha_inicio").first()

        if not viaje_en_curso:
            return Response({"message": "No hay viajes en curso."}, status=status.HTTP_204_NO_CONTENT)

        serializer = ViajeSerializer(viaje_en_curso)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ListarViajesFinalizadosView(APIView):
    """Lista los viajes finalizados según el rol del usuario"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 🔹 MASTER: ve todos los viajes finalizados
        if user.role == "MASTER":
            viajes = Viaje.objects.filter(estado="FINALIZADO").exclude(estado="CANCELADO")

        # 🔹 EMPRESA: ve los viajes de sus empleados
        elif user.role == "EMPRESA":
            try:
                empresa = EmpresaProfile.objects.get(user=user)
                viajes = Viaje.objects.filter(empleado__empresa=empresa, estado="FINALIZADO").exclude(estado="CANCELADO")
            except EmpresaProfile.DoesNotExist:
                return Response({"error": "No tienes un perfil de empresa asociado"}, status=403)

        # 🔹 EMPLEADO: solo sus propios viajes
        elif user.role == "EMPLEADO":
            try:
                empleado = EmpleadoProfile.objects.get(user=user)
                viajes = Viaje.objects.filter(empleado=empleado, estado="FINALIZADO").exclude(estado="CANCELADO")
            except EmpleadoProfile.DoesNotExist:
                return Response({"error": "No tienes un perfil de empleado asociado"}, status=403)

        else:
            return Response({"error": "Rol de usuario no reconocido"}, status=403)

        serializer = ViajeSerializer(viajes, many=True)
        return Response(serializer.data, status=200)


class PendingTripsByEmployeeView(APIView):
    """
    MASTER puede ver cualquier empleado;
    EMPRESA sólo los de su empresa;
    EMPLEADO ve sólo sus propios viajes.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, empleado_id):
        empleado = get_object_or_404(EmpleadoProfile, id=empleado_id)

        # --- Permisos ---
        if request.user.role == 'EMPRESA':
            # Una empresa sólo ve a sus propios empleados
            mi_empresa = getattr(request.user, 'empresa_profile', None)
            if not mi_empresa or empleado.empresa_id != mi_empresa.id:
                return Response({'error': 'No autorizado'}, status=403)

        elif request.user.role == 'EMPLEADO':
            # Un empleado sólo ve SUS propios viajes
            if empleado.user != request.user:
                return Response({'error': 'No autorizado'}, status=403)

        # MASTER pasa sin restricciones

        # --- Lectura de los viajes en revisión ---
        viajes = Viaje.objects.filter(empleado=empleado, estado='EN_REVISION').exclude(estado='CANCELADO')
        serializer = PendingTripSerializer(viajes, many=True)
        return Response(serializer.data, status=200)


class ListarTodosLosViajesView(APIView):
    """Lista todos los viajes según el rol del usuario"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == "MASTER":
            viajes = Viaje.objects.exclude(estado="CANCELADO")

        elif user.role == "EMPRESA":
            try:
                empresa = EmpresaProfile.objects.get(user=user)
                viajes = Viaje.objects.filter(empleado__empresa=empresa).exclude(estado="CANCELADO")
            except EmpresaProfile.DoesNotExist:
                return Response({"error": "No tienes un perfil de empresa asociado"}, status=403)

        elif user.role == "EMPLEADO":
            try:
                empleado = EmpleadoProfile.objects.get(user=user)
                viajes = Viaje.objects.filter(empleado=empleado).exclude(estado="CANCELADO")
            except EmpleadoProfile.DoesNotExist:
                return Response({"error": "No tienes un perfil de empleado asociado"}, status=403)

        else:
            return Response({"error": "Rol de usuario no reconocido"}, status=403)

        serializer = ViajeSerializer(viajes, many=True)
        return Response(serializer.data, status=200)


# users/views.py

class PendingTripsDetailView(APIView):
    """Devuelve count + lista de viajes 'EN_REVISION', opcionalmente filtrado por empleado."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        empleado_id = request.query_params.get('empleado')

        # Si piden por empleado y tengo permiso, lo filtro
        if empleado_id:
            # Sólo EMPRESA/MASTER pueden filtrar otros; EMPLEADO sólo el suyo
            if user.role == "EMPLEADO" and int(empleado_id) != user.empleado_profile.id:
                return Response({"error": "No autorizado"}, status=403)
            viajes_qs = Viaje.objects.filter(empleado_id=empleado_id, estado="EN_REVISION").exclude(estado="CANCELADO")

        else:
            # Sin filtro, cae en la lógica global
            if user.role == "MASTER":
                viajes_qs = Viaje.objects.filter(estado="EN_REVISION").exclude(estado="CANCELADO")
            elif user.role == "EMPRESA":
                empresa = get_object_or_404(EmpresaProfile, user=user)
                viajes_qs = Viaje.objects.filter(empleado__empresa=empresa, estado="EN_REVISION").exclude(estado="CANCELADO")
            else:  # EMPLEADO
                empleado = get_object_or_404(EmpleadoProfile, user=user)
                viajes_qs = Viaje.objects.filter(empleado=empleado, estado="EN_REVISION").exclude(estado="CANCELADO")

        serializer = PendingTripSerializer(viajes_qs, many=True)
        return Response({
            "count": viajes_qs.count(),
            "trips": serializer.data
        }, status=200)


class FinalizarRevisionViajeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, viaje_id):
        user = request.user
        motivo = request.data.get("motivo", "").strip()
        dias_data = request.data.get("dias", [])

        if not isinstance(dias_data, list) or not all('id' in d and 'exento' in d for d in dias_data):
            return Response({"error": "Formato de días inválido"}, status=400)

        viaje = get_object_or_404(Viaje, id=viaje_id, estado='EN_REVISION')

        # Validación de permisos
        if user.role == 'EMPRESA':
            empresa = get_object_or_404(EmpresaProfile, user=user)
            if viaje.empresa != empresa:
                return Response({'error': 'No autorizado'}, status=403)
        elif user.role != 'MASTER':
            return Response({'error': 'No autorizado'}, status=403)

        # Mapear días enviados
        id_a_exento = {d['id']: d['exento'] for d in dias_data}
        dias_viaje = viaje.dias.all()
        ids_validos = set(d.id for d in dias_viaje)

        # Validación de que todos los días pertenezcan al viaje
        if not set(id_a_exento.keys()).issubset(ids_validos):
            return Response({"error": "Uno o más días no pertenecen al viaje"}, status=400)

        # Procesar cada día
        dias_no_exentos = []
        for dia in dias_viaje:
            exento = id_a_exento.get(dia.id, dia.exento)
            dia.exento = exento
            dia.revisado = True
            dia.save()

            estado_gasto = "RECHAZADO" if not exento else "APROBADO"
            dia.gastos.update(estado=estado_gasto)

            if not exento:
                dias_no_exentos.append(dia)

        # Crear conversación si hay días no exentos
        if dias_no_exentos and motivo:
            conversacion = Conversacion.objects.create(viaje=viaje)
            conversacion.participantes.add(user, viaje.empleado.user)

            mensaje = Mensaje.objects.create(
                conversacion=conversacion,
                autor=user,
                contenido=motivo
            )

        # Marcar viaje como finalizado
        viaje.estado = "FINALIZADO"
        viaje.save()

        return Response({"message": "Revisión finalizada. Conversación creada si fue necesario."}, status=200)



class EmployeeCityStatsView(APIView):
    """Devuelve estadísticas de ciudades visitadas por un empleado (viajes finalizados)."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != 'EMPLEADO':
            return Response({"error": "No autorizado"}, status=403)

        try:
            empleado = EmpleadoProfile.objects.get(user=user)
        except EmpleadoProfile.DoesNotExist:
            return Response({"error": "Perfil de empleado no encontrado"}, status=404)

        # Traer todos los viajes finalizados del empleado
        viajes = Viaje.objects.filter(empleado=empleado, estado='FINALIZADO').exclude(estado='CANCELADO')

        # Agrupación manual por ciudad
        city_stats = {}

        for viaje in viajes:
            ciudad = viaje.ciudad or viaje.destino.split(',')[0].strip()
            dias = viaje.dias_viajados or 1

            # Calcular días exentos y no exentos
            dias_relacionados = DiaViaje.objects.filter(viaje=viaje)
            exentos = dias_relacionados.filter(exento=True).count()
            no_exentos = dias_relacionados.filter(exento=False).count()

            if ciudad not in city_stats:
                city_stats[ciudad] = {
                    'city': ciudad,
                    'trips': 1,
                    'days': dias,
                    'nonExemptDays': no_exentos,
                    'exemptDays': exentos,
                }
            else:
                city_stats[ciudad]['trips'] += 1
                city_stats[ciudad]['days'] += dias
                city_stats[ciudad]['nonExemptDays'] += no_exentos
                city_stats[ciudad]['exemptDays'] += exentos

        return Response(list(city_stats.values()), status=200)
