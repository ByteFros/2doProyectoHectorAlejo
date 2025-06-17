import { vitePlugin as remix } from '@remix-run/dev';
import { defineConfig } from 'vite';
import tsconfigPaths from 'vite-tsconfig-paths';
import path from 'node:path';

export default defineConfig({
  plugins: [
    remix({
      ignoredRouteFiles: ['**/*.module.scss'],
    }),
    tsconfigPaths(),
    // ❌ netlifyPlugin se elimina si no usas Netlify
  ],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'crowe.bronixia.es',
    ],
  },
  resolve: {
    alias: {
      '@styles': path.resolve(__dirname, './src/styles/'),
    },
  },
  build: {
    outDir: 'public', // ✅ Importante: generar en 'public' para servir como SPA
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
});
