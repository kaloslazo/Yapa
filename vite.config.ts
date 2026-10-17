import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// S-153: en desarrollo, /api va al motor de Yapa (api/, puerto 8000) y comparte origen con la tienda
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  preview: { proxy: { '/api': 'http://127.0.0.1:8000' } },
});
