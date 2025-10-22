#!/bin/bash

echo "🔧 Probando endpoint de debug con curl..."

curl -X POST http://127.0.0.1:8000/api/users/empresas/debug/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token 3226f5c51969a47e25b2d2f15dca6d83006cb03e" \
  -d '{
    "nombre_empresa": "Test Company",
    "nif": "B12345678", 
    "address": "Test Address",
    "city": "",
    "postal_code": "",
    "correo_contacto": "test@test.com",
    "permisos": false
  }' \
  -v

echo -e "\n\n🔧 Probando endpoint real con curl..."

curl -X POST http://127.0.0.1:8000/api/users/empresas/new/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token 3226f5c51969a47e25b2d2f15dca6d83006cb03e" \
  -d '{
    "nombre_empresa": "Test Company 2",
    "nif": "B87654321",
    "address": "Test Address 2", 
    "city": "",
    "postal_code": "",
    "correo_contacto": "test2@test.com",
    "permisos": false
  }' \
  -v
