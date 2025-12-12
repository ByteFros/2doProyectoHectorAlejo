"""
URLs del módulo de gestión de contraseñas
"""
from django.urls import path

from .views import ChangePasswordView, PasswordResetConfirmView, PasswordResetRequestView

urlpatterns = [
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]
