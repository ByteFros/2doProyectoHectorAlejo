from django.http import FileResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import generics, permissions, parsers
from rest_framework.response import Response
from users.models import Gasto, MensajeJustificante, EmpresaProfile
from users.serializers import MensajeJustificanteSerializer
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
