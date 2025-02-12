from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model, authenticate
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

User = get_user_model()

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Obtener datos del usuario autenticado."""
        user = request.user
        return Response({"username": user.username, "role": user.role})


    def put(self, request):
        """Actualizar los datos del usuario autenticado."""
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)  # `partial=True` permite actualizar solo algunos campos
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Eliminar el usuario autenticado."""
        user = request.user
        user.delete()
        return Response({"message": "Usuario eliminado exitosamente."}, status=status.HTTP_204_NO_CONTENT)


class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class LoginView(APIView):
    permission_classes = [AllowAny]  # Permite que cualquiera haga login

    def post(self, request):
        """Autentica un usuario y devuelve su token"""
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "role": user.role}, status=status.HTTP_200_OK)

        return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Cerrar sesión eliminando el token del usuario."""
        try:
            request.user.auth_token.delete()  # Elimina el token del usuario autenticado
            return Response({"message": "Sesión cerrada correctamente"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)