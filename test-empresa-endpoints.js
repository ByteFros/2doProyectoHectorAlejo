// test-empresa-endpoints.js
// Script para probar los endpoints desde la consola del navegador

const testData = {
  nombre_empresa: "Test Company",
  nif: "B12345678",
  address: "Test Address",
  city: "",
  postal_code: "",
  correo_contacto: "test@test.com",
  permisos: false
};

const token = localStorage.getItem('token');

console.log('🔧 Token:', token);
console.log('🔧 Test data:', testData);

// Test 1: Endpoint de debug (sin autenticación)
fetch('http://127.0.0.1:8000/api/users/empresas/debug/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(testData)
})
.then(response => {
  console.log('🔧 Debug endpoint status:', response.status);
  return response.json();
})
.then(data => {
  console.log('🔧 Debug endpoint response:', data);
})
.catch(error => {
  console.error('🔧 Debug endpoint error:', error);
});

// Test 2: Endpoint simple (sin autenticación)
fetch('http://127.0.0.1:8000/api/users/empresas/simple/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(testData)
})
.then(response => {
  console.log('🔧 Simple endpoint status:', response.status);
  return response.json();
})
.then(data => {
  console.log('🔧 Simple endpoint response:', data);
})
.catch(error => {
  console.error('🔧 Simple endpoint error:', error);
});

// Test 3: Endpoint original DRF (con autenticación)
if (token) {
  fetch('http://127.0.0.1:8000/api/users/empresas/new/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`
    },
    body: JSON.stringify(testData)
  })
  .then(response => {
    console.log('🔧 Original DRF endpoint status:', response.status);
    return response.json();
  })
  .then(data => {
    console.log('🔧 Original DRF endpoint response:', data);
  })
  .catch(error => {
    console.error('🔧 Original DRF endpoint error:', error);
  });
} else {
  console.log('🔧 No token found, skipping authenticated test');
}
