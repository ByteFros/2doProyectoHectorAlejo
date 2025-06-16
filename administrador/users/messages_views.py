"""messages_views.py"""
import os

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import generics, permissions, parsers
from rest_framework.response import Response
from users.models import Gasto, MensajeJustificante, EmpresaProfile, Conversacion, CustomUser, Mensaje, Viaje
from users.serializers import MensajeJustificanteSerializer, ConversacionSerializer, MensajeSerializer
import mimetypes



class SolicitarJustificanteView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, gasto_id):
        motivo = request.data.get("motivo", "").strip()
        if not motivo:
            return Response({"error": "Debes explicar por qué solicitas el justificante"}, status=400)

        user = request.user

        try:
            gasto = Gasto.objects.get(id=gasto_id)

            if user.role == "EMPRESA":
                empresa = EmpresaProfile.objects.filter(user=user).first()
                if not empresa or gasto.empresa != empresa:
                    return Response({"error": "No autorizado para este gasto"}, status=403)
            elif user.role != "MASTER":
                return Response({"error": "No tienes permisos para solicitar justificante"}, status=403)

            if gasto.comprobante:
                return Response({"error": "Este gasto ya tiene un justificante"}, status=400)

            # Ya existe un mensaje sin respuesta para este gasto
            if MensajeJustificante.objects.filter(gasto=gasto, respuesta__isnull=True).exists():
                return Response({"error": "Ya se ha solicitado un justificante para este gasto."}, status=400)

            MensajeJustificante.objects.create(
                gasto=gasto,
                autor=user,
                motivo=motivo
            )

            gasto.estado = "JUSTIFICAR"
            gasto.save()

            return Response({"message": "Justificante solicitado correctamente"}, status=200)

        except Gasto.DoesNotExist:
            return Response({"error": "Gasto no encontrado"}, status=404)


class ListarMensajesView(generics.ListAPIView):
    serializer_class = MensajeJustificanteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'MASTER':
            return MensajeJustificante.objects.all()
        elif user.role == 'EMPRESA':
            return MensajeJustificante.objects.filter(gasto__empresa__user=user)
        elif user.role == 'EMPLEADO':
            return MensajeJustificante.objects.filter(gasto__empleado__user=user)
        return MensajeJustificante.objects.none()

class ListarMensajesByIdView(generics.ListAPIView):
    """
    Lista todos los mensajes de una conversación (por conversacion_id en la URL).
    """
    serializer_class = MensajeSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conv_id = self.kwargs.get('conversacion_id')
        conversacion = get_object_or_404(Conversacion, id=conv_id)
        # Validar que el usuario esté en la conversación
        if self.request.user not in conversacion.participantes.all():
            return Mensaje.objects.none()
        return conversacion.mensajes.order_by('fecha_creacion')

class EnviarMensajeView(APIView):
    """
    Envía un nuevo mensaje en una conversación existente.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        conv_id  = request.data.get("conversacion_id")
        contenido = request.data.get("contenido", "").strip()
        gasto_id = request.data.get("gasto_id")    # NUEVO
        archivo  = request.FILES.get("archivo")

        if not conv_id or not contenido:
            return Response({"error":"Faltan conversacion_id o contenido"}, status=400)

        conversacion = get_object_or_404(Conversacion, id=conv_id)
        if request.user not in conversacion.participantes.all():
            return Response({"error":"No en este hilo"}, status=403)

        # Si es mensaje justificante, asociamos gasto y cambiamos su estado
        gasto = None
        if gasto_id:
            gasto = get_object_or_404(Gasto, id=gasto_id)
            # sólo MASTER/EMPRESA piden justificantes
            if request.user.role in ["MASTER", "EMPRESA"]:
                gasto.estado = "JUSTIFICAR"
                gasto.save()
            # si es empleado respondiendo con archivo justificante:
            elif request.user.role == "EMPLEADO" and archivo:
                gasto.comprobante = archivo
                gasto.estado = "PENDIENTE"
                gasto.save()

        mensaje = Mensaje.objects.create(
            conversacion=conversacion,
            autor=request.user,
            contenido=contenido,
            archivo=archivo,
            gasto=gasto
        )

        return Response(MensajeSerializer(mensaje).data, status=201)


class ResponderMensajeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request, mensaje_id):
        try:
            mensaje = MensajeJustificante.objects.get(id=mensaje_id)
        except MensajeJustificante.DoesNotExist:
            return Response({"error": "Mensaje no encontrado"}, status=404)

        # ✅ Solo el empleado puede responder
        if request.user.role != "EMPLEADO":
            return Response({"error": "Solo los empleados pueden responder mensajes"}, status=403)

        if mensaje.gasto.empleado.user != request.user:
            return Response({"error": "No tienes permiso para responder este mensaje"}, status=403)

        # ✅ Si ya respondió, no permitir otra respuesta
        if mensaje.respuesta:
            return Response({"error": "Este mensaje ya ha sido respondido"}, status=400)

        respuesta = request.data.get("respuesta", "").strip()
        archivo = request.FILES.get("archivo")

        if not respuesta:
            return Response({"error": "La respuesta no puede estar vacía"}, status=400)

        mensaje.respuesta = respuesta
        mensaje.estado = "pendiente"

        if archivo:
            mensaje.archivo_justificante = archivo
            mensaje.gasto.comprobante = archivo

        mensaje.save()
        mensaje.gasto.save()

        return Response({"message": "Respuesta guardada correctamente"}, status=200)

class CrearConversacionView(APIView):
    """
    Crea una conversación nueva, ligada opcionalmente a un gasto o a un empleado específico.
    MASTER o EMPRESA pueden iniciar:
      - Conversación por gasto: enviar gasto_id
      - Conversación libre: enviar empleado_id
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        viaje_id = request.data.get("viaje_id")
        empleado_id = request.data.get("empleado_id")

        # Sólo MASTER/EMPRESA
        if user.role not in ["MASTER", "EMPRESA"]:
            return Response({"error": "No autorizado"}, status=403)

        # Caso viaje: lista TODOS los empleados que participaron, o solo uno?
        # Aquí asumo 1 empleado por viaje:
        if viaje_id:
            viaje = get_object_or_404(Viaje, id=viaje_id)
            conversacion = Conversacion.objects.create(viaje=viaje)
            conversacion.participantes.add(user, viaje.empleado.user)

        elif empleado_id:
            # como antes, conversación libre
            empleado = get_object_or_404(CustomUser, id=empleado_id, role="EMPLEADO")
            conversacion = Conversacion.objects.create()
            conversacion.participantes.add(user, empleado)

        else:
            return Response({"error": "Envía viaje_id o empleado_id"}, status=400)

        serializer = ConversacionSerializer(conversacion)
        return Response(serializer.data, status=201)

class ListarConversacionesView(generics.ListAPIView):
    """
    Lista todas las conversaciones en las que participa el usuario.
    """
    serializer_class = ConversacionSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversacion.objects.filter(participantes=self.request.user)




class CambiarEstadoJustificacionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, mensaje_id):
        estado = request.data.get("estado")
        if estado not in ["aprobado", "rechazado"]:
            return Response({"error": "Estado inválido"}, status=400)

        try:
            mensaje = MensajeJustificante.objects.get(id=mensaje_id)
        except MensajeJustificante.DoesNotExist:
            return Response({"error": "Mensaje no encontrado"}, status=404)

        if request.user.role == "EMPRESA" and mensaje.gasto.empresa.user != request.user:
            return Response({"error": "No autorizado"}, status=403)

        mensaje.estado = estado
        mensaje.save()

        if estado == "aprobado":
            mensaje.gasto.estado = "APROBADO"
        elif estado == "rechazado":
            mensaje.gasto.estado = "RECHAZADO"
        mensaje.gasto.save()

        return Response({"message": f"Justificante {estado}"}, status=200)


class DescargarArchivoMensajeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, mensaje_id):
        try:
            mensaje = MensajeJustificante.objects.get(id=mensaje_id)
        except MensajeJustificante.DoesNotExist:
            return Response({"error": "Mensaje no encontrado"}, status=404)

        if not mensaje.archivo_justificante:
            return Response({"error": "Este mensaje no tiene justificante adjunto"}, status=404)

        archivo = mensaje.archivo_justificante
        mime_type, _ = mimetypes.guess_type(archivo.name)
        content_type = mime_type or 'application/octet-stream'

        response = FileResponse(archivo.open(), content_type=content_type)
        response['Content-Disposition'] = f"inline; filename=\"{archivo.name.split('/')[-1]}\""

        return response


class DescargarAdjuntoMensajeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, mensaje_id):
        print(f"🔧 [DescargarAdjuntoMensajeView] Request received for mensaje_id: {mensaje_id}")
        print(f"🔧 [DescargarAdjuntoMensajeView] User: {request.user}")
        print(f"🔧 [DescargarAdjuntoMensajeView] Path: {request.path}")
        
        mensaje = get_object_or_404(Mensaje, id=mensaje_id)
        print(f"🔧 [DescargarAdjuntoMensajeView] Mensaje found: {mensaje}")
        print(f"🔧 [DescargarAdjuntoMensajeView] Mensaje.archivo: {mensaje.archivo}")
        
        # Validar que el usuario participe en la conversación:
        if request.user not in mensaje.conversacion.participantes.all():
            print(f"🔧 [DescargarAdjuntoMensajeView] User not authorized")
            return Response({"error": "No autorizado"}, status=403)

        if not mensaje.archivo:
            print(f"🔧 [DescargarAdjuntoMensajeView] No archivo found")
            return Response({"error": "No hay archivo adjunto"}, status=404)

        archivo = mensaje.archivo
        print(f"🔧 [DescargarAdjuntoMensajeView] Archivo path: {archivo.path}")
        print(f"🔧 [DescargarAdjuntoMensajeView] Archivo name: {archivo.name}")
        
        mime_type, _ = mimetypes.guess_type(archivo.name)
        response = FileResponse(archivo.open(), content_type=mime_type or 'application/octet-stream')
        filename = os.path.basename(archivo.name)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        print(f"🔧 [DescargarAdjuntoMensajeView] Returning file response")
        return response