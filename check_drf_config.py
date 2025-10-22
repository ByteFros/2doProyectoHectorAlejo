#!/usr/bin/env python3

# Script para verificar la configuración de DRF
import os
import sys
import django

# Configurar Django
sys.path.append('C:\\Users\\alejo\\Desktop\\repositorios\\7p\\2doProyectoHectorAlejo\\administrador')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'administrador.settings')
django.setup()

from django.conf import settings
from rest_framework.settings import api_settings

print("🔧 Django REST Framework Configuration:")
print(f"DEFAULT_PARSER_CLASSES: {api_settings.DEFAULT_PARSER_CLASSES}")
print(f"DEFAULT_AUTHENTICATION_CLASSES: {api_settings.DEFAULT_AUTHENTICATION_CLASSES}")
print(f"DEFAULT_PERMISSION_CLASSES: {api_settings.DEFAULT_PERMISSION_CLASSES}")

print("\n🔧 Raw settings from settings.py:")
if hasattr(settings, 'REST_FRAMEWORK'):
    for key, value in settings.REST_FRAMEWORK.items():
        print(f"{key}: {value}")
else:
    print("REST_FRAMEWORK not found in settings!")
