"""
URLs del módulo de autenticación
"""
from django.urls import path
from .views import LoginView, LogoutView, RegisterUserView, SessionView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('session/', SessionView.as_view(), name='session'),
]
