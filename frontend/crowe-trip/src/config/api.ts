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
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include',
    ...options,
  };

  return fetch(url, defaultOptions);
};

// Debug helper - se puede eliminar en producción
export const logApiConfig = () => {
  console.log('🔧 API Configuration:', {
    baseUrl: API_BASE_URL,
    environment: import.meta.env.VITE_ENVIRONMENT,
    isDev: import.meta.env.DEV,
  });
};
