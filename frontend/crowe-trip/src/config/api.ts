// Configuración centralizada de la API
const getApiBaseUrl = (): string => {
  // En desarrollo, usar la variable de entorno o fallback a localhost
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
  }
  
  // En producción, usar la variable de entorno o fallback al dominio actual
  return import.meta.env.VITE_API_BASE_URL || 'https://crowe.bronixia.es';
};

export const API_BASE_URL = getApiBaseUrl();

// Helper para construir URLs de API completas
export const buildApiUrl = (endpoint: string): string => {
  // Asegurar que el endpoint comience con /
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${API_BASE_URL}/api${cleanEndpoint}`;
};

// Configuración de fetch con defaults
export const apiRequest = async (
  endpoint: string, 
  options: RequestInit = {}
): Promise<Response> => {
  const url = buildApiUrl(endpoint);
  
  // Crear headers usando Headers API para evitar problemas de spread
  const headers = new Headers();
  headers.set('Content-Type', 'application/json');
  
  // Agregar headers del options DESPUÉS del Content-Type por defecto
  if (options.headers) {
    if (options.headers instanceof Headers) {
      options.headers.forEach((value, key) => {
        headers.set(key, value);
      });
    } else {
      Object.entries(options.headers).forEach(([key, value]) => {
        if (value !== undefined) {
          headers.set(key, value.toString());
        }
      });
    }
  }

  // Si el body es FormData, quitar Content-Type (el navegador lo hace automáticamente)
  if (options.body instanceof FormData) {
    headers.delete('Content-Type');
  }
  
  const defaultOptions: RequestInit = {
    ...options,
    headers,
    credentials: 'include',
  };

  // Debug temporal - Log ANTES de la petición
  console.log('🔧 API Request BEFORE:', {
    url,
    method: options.method || 'GET',
    headers: [...headers.entries()],
    bodyType: options.body ? (options.body instanceof FormData ? 'FormData' : typeof options.body) : 'none',
    bodyContent: options.body
  });

  const response = fetch(url, defaultOptions);
  
  // Debug temporal - Log DESPUÉS de iniciar la petición
  console.log('🔧 API Request STARTED for:', url);
  
  return response;
};

// Debug helper - se puede eliminar en producción
export const logApiConfig = () => {
  console.log('🔧 API Configuration:', {
    baseUrl: API_BASE_URL,
    environment: import.meta.env.VITE_ENVIRONMENT,
    isDev: import.meta.env.DEV,
  });
};

// Función alternativa para debug que fuerza application/json
export const apiRequestDebug = async (
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> => {
  const url = buildApiUrl(endpoint);
  
  console.log('🔧 DEBUG apiRequestDebug called with:', { endpoint, options });
  
  // Crear headers más explícitamente
  const headers = new Headers();
  headers.set('Content-Type', 'application/json');
  
  // Agregar otros headers
  if (options.headers) {
    if (options.headers instanceof Headers) {
      options.headers.forEach((value, key) => {
        if (key !== 'Content-Type') {
          headers.set(key, value);
        }
      });
    } else {
      Object.entries(options.headers).forEach(([key, value]) => {
        if (key !== 'Content-Type' && value !== undefined) {
          headers.set(key, value.toString());
        }
      });
    }
  }
  
  console.log('🔧 DEBUG Final headers:', [...headers.entries()]);
  
  const fetchOptions: RequestInit = {
    ...options,
    headers,
    credentials: 'include'
  };
  
  console.log('🔧 DEBUG Final fetch options:', fetchOptions);
  
  return fetch(url, fetchOptions);
};
