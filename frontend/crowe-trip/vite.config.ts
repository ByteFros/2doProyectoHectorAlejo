import { vitePlugin as remix } from '@remix-run/dev';
import { defineConfig } from 'vite';
import tsconfigPaths from 'vite-tsconfig-paths';
import path from 'node:path';
import { netlifyPlugin } from '@netlify/remix-adapter/plugin';

export default defineConfig({
    plugins: [
        remix({
            ignoredRouteFiles: ['**/*.module.scss'],
        }),
        tsconfigPaths(),
        netlifyPlugin(),
    ],

    // probaremos esto despues de crear el contenedor 
    server: {
        host: '0.0.0.0',
        port: 5173,
        proxy: {
            // Interceptar todas las peticiones a 127.0.0.1:8000 y redirigirlas al backend
            'http://127.0.0.1:8000': {
                target: 'http://backend:8000',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^http:\/\/127\.0\.0\.1:8000/, ''),
            },
            // Alternativa: si prefieres usar rutas relativas
            '/api': {
                target: 'http://backend:8000',
                changeOrigin: true,
            }
        }
    },
    resolve: {
        alias: {
            '@styles': path.resolve(__dirname, './src/styles/'),
        },
    },
});
