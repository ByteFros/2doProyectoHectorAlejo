// test-from-browser-console.js
// Copia y pega esto en la consola del navegador mientras estás en la app

console.log('🔧 Testing from browser console...');

const token = localStorage.getItem('token');
console.log('🔧 Token found:', !!token);

const testData = {
  nombre_empresa: "Browser Test Company",
  nif: "B99999999",
  address: "Browser Test Address",
  city: "",
  postal_code: "",
  correo_contacto: "browsertest@test.com",
  permisos: false
};

console.log('🔧 Test data:', testData);
console.log('🔧 JSON string:', JSON.stringify(testData));

// Test directo con fetch
fetch('http://127.0.0.1:8000/api/users/empresas/new/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Token ${token}`
  },
  body: JSON.stringify(testData)
})
.then(response => {
  console.log('🔧 Direct fetch status:', response.status);
  console.log('🔧 Direct fetch headers:', [...response.headers.entries()]);
  return response.json();
})
.then(data => {
  console.log('🔧 Direct fetch response:', data);
})
.catch(error => {
  console.error('🔧 Direct fetch error:', error);
});

// Test con apiRequest importado (si está disponible)
if (typeof window !== 'undefined' && window.apiRequest) {
  console.log('🔧 Testing with window.apiRequest...');
  window.apiRequest('/users/empresas/new/', {
    method: 'POST',
    headers: {
      'Authorization': `Token ${token}`
    },
    body: JSON.stringify(testData)
  })
  .then(response => {
    console.log('🔧 apiRequest status:', response.status);
    return response.json();
  })
  .then(data => {
    console.log('🔧 apiRequest response:', data);
  })
  .catch(error => {
    console.error('🔧 apiRequest error:', error);
  });
} else {
  console.log('🔧 window.apiRequest not available');
}
