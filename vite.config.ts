import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';

// S-153: en desarrollo, /api va al motor de Yapa (api/, puerto 8000) y comparte origen con la tienda
declare const process: { env: Record<string, string | undefined> }; // Node lo da al compilar; la app no lo usa

// DA-08: la página lleva, sin mostrarse, qué commit está desplegado (<meta name="yapa-build">); en GitHub, GITHUB_SHA lo da el propio flujo
const build = (process.env.GITHUB_SHA ?? 'local').slice(0, 7);
const buildTag: Plugin = {
  name: 'yapa-build',
  transformIndexHtml: (html) => html.replace('</head>', `    <meta name="yapa-build" content="${build}" />
  </head>`),
};

export default defineConfig({
  plugins: [react(), buildTag],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  preview: { proxy: { '/api': 'http://127.0.0.1:8000' } },
});
