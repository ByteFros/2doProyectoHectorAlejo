// Middleware para manejar rutas SPA
export function spaFallbackMiddleware() {
  return {
    name: 'spa-fallback',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        // Si es una ruta de la API, continuar
        if (req.url.startsWith('/api')) {
          return next();
        }
        
        // Si es un archivo estático, continuar
        if (req.url.includes('.')) {
          return next();
        }
        
        // Para todas las demás rutas, servir index.html
        if (req.method === 'GET' && !req.url.startsWith('/@')) {
          req.url = '/';
        }
        
        next();
      });
    },
  };
}
