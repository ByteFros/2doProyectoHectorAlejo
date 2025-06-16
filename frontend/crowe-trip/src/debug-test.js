// Script temporal para diagnosticar el problema
console.log('🔧 Probando conectividad con el endpoint de debug...');

const testData = {
  nombre_empresa: "Test Company",
  nif: "B12345678",
  address: "Test Address",
  city: "",
  postal_code: "",
  correo_contacto: "test@test.com",
  permisos: false
};

// Test 1: Usando fetch directo
fetch('http://127.0.0.1:8000/api/users/empresas/debug/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Token 3226f5c51969a47e25b2d2f15dca6d83006cb03e'
  },
  body: JSON.stringify(testData)
})
.then(response => {
  console.log('🔧 Response status:', response.status);
  return response.json();
})
.then(data => {
  console.log('🔧 Response data:', data);
})
.catch(error => {
  console.error('🔧 Error:', error);
});

// Test 2: Usando el apiRequest
import { apiRequest } from '../../config/api';

setTimeout(() => {
  console.log('🔧 Probando con apiRequest...');
  
  apiRequest('/users/empresas/debug/', {
    method: 'POST',
    headers: {
      'Authorization': 'Token 3226f5c51969a47e25b2d2f15dca6d83006cb03e'
    },
    body: JSON.stringify(testData)
  })
  .then(response => {
    console.log('🔧 apiRequest status:', response.status);
    return response.json();
  })
  .then(data => {
    console.log('🔧 apiRequest data:', data);
  })
  .catch(error => {
    console.error('🔧 apiRequest error:', error);
  });
}, 2000);
