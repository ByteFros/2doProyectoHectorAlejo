"""
Vistas para gestión de mensajería (conversaciones entre usuarios)
"""
import os
import mimetypes
from typing import Optional

from django.db.models import Prefetch
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Conversacion, ConversacionLectura, CustomUser, Mensaje, EmpresaProfile, EmpleadoProfile
from users.serializers import ConversacionSerializer, MensajeSerializer
from users.common.exceptions import UnauthorizedAccessError, EmpresaProfileNotFoundError, EmpleadoProfileNotFoundError
from users.common.services import get_user_empresa, get_user_empleado
from users.common.files import compress_if_image
from .utils import (
    get_target_user_or_400,
    get_existing_conversation,
    create_conversation,
    mark_conversation_as_read,
)


def puede_participar_conversacion(usuario: CustomUser, conversacion: Conversacion) -> bool:
    """Verifica si un usuario participa en la conversación"""
    return conversacion.participantes.filter(id=usuario.id).exists()


def enviar_mensaje(
    conversacion: Conversacion,
    autor: CustomUser,
    contenido: str,
    archivo=None
) -> Mensaje:
    """Crea un mensaje dentro de una conversación"""
    if (not contenido or not contenido.strip()) and not archivo:
        raise ValueError("El contenido no puede estar vacío")

    return Mensaje.objects.create(
        conversacion=conversacion,
        autor=autor,
        contenido=contenido,
        archivo=archivo
    )


def obtener_conversaciones_usuario(usuario: CustomUser):
    return Conversacion.objects.filter(participantes=usuario)


def obtener_mensajes_conversacion(conversacion: Conversacion):
    return conversacion.mensajes.order_by('fecha_creacion')


class ContactListView(APIView):
    """Devuelve la lista jerárquica de contactos permitidos para el usuario autenticado"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.user.role

        if role == "MASTER":
            data = self._build_master_contacts(request.user)
        elif role == "EMPRESA":
            data = self._build_empresa_contacts(request.user)
        elif role == "EMPLEADO":
            data = self._build_empleado_contacts(request.user)
        else:
            return Response({"error": "Rol no soportado para contactos"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_200_OK)

    def _format_user(self, user: CustomUser, display_name: Optional[str] = None, extra: Optional[dict] = None):
        full_name = (user.get_full_name() or "").strip()
        display = display_name or full_name or user.username
        payload = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": display,
            "role": user.role,
        }
        if extra:
            payload.update(extra)
        return payload

    def _format_empresa(self, empresa: EmpresaProfile):
        return {
            "empresa_id": empresa.id,
            "nombre": empresa.nombre_empresa,
            "user": self._format_user(
                empresa.user,
                display_name=empresa.nombre_empresa or empresa.user.username
            )
        }

    def _format_empleado(self, empleado: EmpleadoProfile):
        display = " ".join(filter(None, [empleado.nombre, empleado.apellido])).strip()
        return self._format_user(
            empleado.user,
            display_name=display or empleado.user.username,
            extra={
                "empleado_id": empleado.id,
                "empresa_id": empleado.empresa_id,
            }
        )

    def _build_master_contacts(self, current_user: CustomUser):
        empleados_prefetch = Prefetch(
            'empleados',
            queryset=EmpleadoProfile.objects.select_related('user').filter(user__is_active=True).order_by('nombre', 'apellido', 'user__username')
        )
        empresas = (
            EmpresaProfile.objects
            .select_related('user')
            .filter(user__is_active=True)
            .prefetch_related(empleados_prefetch)
            .order_by('nombre_empresa')
        )

        companies = []
        for empresa in empresas:
            employees = [self._format_empleado(emp) for emp in empresa.empleados.all()]
            companies.append({
                **self._format_empresa(empresa),
                "employees": employees
            })

        masters = []
        master_qs = CustomUser.objects.filter(role="MASTER", is_active=True).exclude(pk=current_user.id).order_by('username')
        for admin in master_qs:
            full_name = (admin.get_full_name() or "").strip()
            masters.append(self._format_user(admin, display_name=full_name or admin.username))

        return {
            "role": "MASTER",
            "masters": masters,
            "companies": companies
        }

    def _build_empresa_contacts(self, user: CustomUser):
        empresa = get_user_empresa(user)
        if not empresa:
            raise EmpresaProfileNotFoundError()

        empresa = EmpresaProfile.objects.select_related('user').prefetch_related(
            Prefetch(
                'empleados',
                queryset=EmpleadoProfile.objects.select_related('user').filter(user__is_active=True).order_by('nombre', 'apellido', 'user__username')
            )
        ).get(pk=empresa.id)

        masters = []
        for admin in CustomUser.objects.filter(role="MASTER", is_active=True).order_by('username'):
            full_name = (admin.get_full_name() or "").strip()
            masters.append(self._format_user(admin, display_name=full_name or admin.username))

        employees = [self._format_empleado(emp) for emp in empresa.empleados.all()]

        return {
            "role": "EMPRESA",
            "masters": masters,
            "companies": [{
                **self._format_empresa(empresa),
                "employees": employees
            }]
        }

    def _build_empleado_contacts(self, user: CustomUser):
        empleado = get_user_empleado(user)
        if not empleado:
            raise EmpleadoProfileNotFoundError()

        empleado = EmpleadoProfile.objects.select_related('empresa__user').get(pk=empleado.id)
        empresa = empleado.empresa

        coworkers_qs = EmpleadoProfile.objects.select_related('user').filter(
            empresa=empresa,
            user__is_active=True
        ).exclude(pk=empleado.id).order_by('nombre', 'apellido', 'user__username')

        coworkers = [self._format_empleado(emp) for emp in coworkers_qs]

        masters = []
        for admin in CustomUser.objects.filter(role="MASTER", is_active=True).order_by('username'):
            full_name = (admin.get_full_name() or "").strip()
            masters.append(self._format_user(admin, display_name=full_name or admin.username))

        return {
            "role": "EMPLEADO",
            "masters": masters,
            "companies": [{
                **self._format_empresa(empresa),
                "employees": coworkers
            }]
        }


class AdminContactView(APIView):
    """Entrega el listado de usuarios con rol MASTER para iniciar conversaciones"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ["EMPRESA", "EMPLEADO"]:
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        admins = CustomUser.objects.filter(role="MASTER", is_active=True).order_by('id')
        data = [
            {
                "user_id": admin.id,
                "username": admin.username,
                "display_name": (admin.get_full_name() or "").strip() or admin.username
            }
            for admin in admins
        ]

        return Response({"admins": data}, status=status.HTTP_200_OK)


class CrearConversacionView(APIView):
    """Crea una conversación entre el usuario autenticado y otro usuario"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        target_user_id = request.data.get("user_id")
        if not target_user_id:
            return Response({"error": "Debes indicar user_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = get_target_user_or_400(user, int(target_user_id))
        except UnauthorizedAccessError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError:
            return Response({"error": "user_id inválido"}, status=status.HTTP_400_BAD_REQUEST)

        existing = get_existing_conversation(user, target_user)
        if existing:
            return Response(
                {"error": "Ya existe una conversación con este usuario"},
                status=status.HTTP_400_BAD_REQUEST
            )

        conversacion = create_conversation(user, target_user)

        serializer = ConversacionSerializer(conversacion, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ListarConversacionesView(generics.ListAPIView):
    """Lista todas las conversaciones en las que participa el usuario"""
    serializer_class = ConversacionSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user
        lecturas_prefetch = Prefetch(
            'lecturas',
            queryset=ConversacionLectura.objects.filter(usuario=usuario)
        )
        return obtener_conversaciones_usuario(usuario).prefetch_related(
            'mensajes',
            'participantes',
            lecturas_prefetch
        )


class ListarMensajesByIdView(generics.ListAPIView):
    """Lista todos los mensajes de una conversación"""
    serializer_class = MensajeSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conv_id = self.kwargs.get('conversacion_id')
        conversacion = get_object_or_404(Conversacion, id=conv_id)

        # Validar que el usuario esté en la conversación
        if not puede_participar_conversacion(self.request.user, conversacion):
            return Mensaje.objects.none()

        mensajes_qs = obtener_mensajes_conversacion(conversacion)
        last_message = mensajes_qs.order_by('-fecha_creacion').first()
        if last_message:
            mark_conversation_as_read(conversacion, self.request.user, last_message.fecha_creacion)

        return mensajes_qs


class EnviarMensajeView(APIView):
    """Envía un mensaje creando la conversación si es necesario"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        contenido = request.data.get("contenido", "")
        contenido = contenido.strip() if isinstance(contenido, str) else ""
        archivo = request.FILES.get("archivo")
        conv_id = request.data.get("conversacion_id")
        to_user_id = request.data.get("to_user_id")

        # Validar datos mínimos
        if not conv_id and not to_user_id:
            return Response({"error": "Debes indicar conversacion_id o to_user_id"}, status=status.HTTP_400_BAD_REQUEST)

        if not archivo and not contenido:
            return Response({"error": "El mensaje debe incluir contenido o un archivo."}, status=status.HTTP_400_BAD_REQUEST)

        if archivo:
            if archivo.size > getattr(settings, "FILE_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024):
                return Response(
                    {"error": "El archivo supera el límite permitido (10 MB)."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            compression_result = compress_if_image(archivo)
            archivo = compression_result.file

        conversacion = None

        if conv_id:
            conversacion = get_object_or_404(Conversacion, id=conv_id)
            if not puede_participar_conversacion(request.user, conversacion):
                raise UnauthorizedAccessError("No participas en esta conversación")
        else:
            try:
                target_user = get_target_user_or_400(request.user, int(to_user_id))
            except UnauthorizedAccessError as exc:
                return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
            except (ValueError, TypeError):
                return Response({"error": "to_user_id inválido"}, status=status.HTTP_400_BAD_REQUEST)

            conversacion = get_existing_conversation(request.user, target_user)
            if not conversacion:
                conversacion = create_conversation(request.user, target_user)

        # Enviar mensaje
        try:
            mensaje = enviar_mensaje(conversacion, request.user, contenido, archivo)
            mark_conversation_as_read(conversacion, request.user, mensaje.fecha_creacion)
            payload = MensajeSerializer(mensaje).data
            payload["conversation_id"] = conversacion.id
            return Response(payload, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DescargarAdjuntoMensajeView(APIView):
    """Descarga el archivo adjunto de un mensaje de conversación"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, mensaje_id):
        mensaje = get_object_or_404(Mensaje, id=mensaje_id)

        # Validar permisos
        if not puede_participar_conversacion(request.user, mensaje.conversacion):
            raise UnauthorizedAccessError("No autorizado")

        if not mensaje.archivo:
            return Response(
                {"error": "No hay archivo adjunto"},
                status=status.HTTP_404_NOT_FOUND
            )

        archivo = mensaje.archivo
        mime_type, _ = mimetypes.guess_type(archivo.name)
        response = FileResponse(
            archivo.open(),
            content_type=mime_type or 'application/octet-stream'
        )
        filename = os.path.basename(archivo.name)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
