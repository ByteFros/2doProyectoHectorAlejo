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

    server: {
        host: '0.0.0.0',
        port: 5173,
        // Permitir conexiones desde crowe.bronixia.es
        allowedHosts: [
            'localhost',
            '127.0.0.1',
            'crowe.bronixia.es',
            '.bronixia.es' // wildcard para subdominios
        ],
        proxy: {
            // Solo usar proxy en desarrollo
            '/api': {
                target: process.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, '/api'),
            }
        }
    },

    preview: {
        host: '0.0.0.0',
        port: 4173,
        // También permitir hosts en preview mode
        allowedHosts: [
            'localhost',
            '127.0.0.1', 
            'crowe.bronixia.es',
            '.bronixia.es'
        ]
    },
    resolve: {
        alias: {
            '@styles': path.resolve(__dirname, './src/styles/'),
            '@config': path.resolve(__dirname, './src/config/'),
        },
    },
});
