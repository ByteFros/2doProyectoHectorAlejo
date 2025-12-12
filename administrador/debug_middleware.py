# debug_middleware.py - Versión mejorada
import json
import logging

logger = logging.getLogger(__name__)

class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log TODAS las peticiones a /api/users/empresas/
        if '/api/users/empresas/' in request.path:
            print("🔧 [MIDDLEWARE] ===== REQUEST START =====")
            print(f"🔧 [MIDDLEWARE] Path: {request.path}")
            print(f"🔧 [MIDDLEWARE] Method: {request.method}")
            print(f"🔧 [MIDDLEWARE] Content-Type: {request.content_type}")
            print(f"🔧 [MIDDLEWARE] Headers: {dict(request.headers)}")
            
            if request.method == 'POST':
                print(f"🔧 [MIDDLEWARE] Body: {request.body}")
                # Verifica si el body puede ser parseado como JSON
                try:
                    if request.body:
                        parsed = json.loads(request.body)
                        print(f"🔧 [MIDDLEWARE] Body parsed as JSON: {parsed}")
                except Exception as e:
                    print(f"🔧 [MIDDLEWARE] Error parsing body: {e}")
        
        response = self.get_response(request)
        
        if '/api/users/empresas/' in request.path:
            print(f"🔧 [MIDDLEWARE] Response status: {response.status_code}")
            if hasattr(response, 'content'):
                try:
                    content = response.content.decode('utf-8')
                    if len(content) < 500:  # Solo para respuestas cortas
                        print(f"🔧 [MIDDLEWARE] Response content: {content}")
                except UnicodeDecodeError:
                    # Algunas respuestas pueden no ser texto; ignoramos el contenido en ese caso.
                    pass
            print("🔧 [MIDDLEWARE] ===== REQUEST END =====")
        
        return response
