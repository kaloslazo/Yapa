import { defineConfig } from 'vitest/config';

export default defineConfig({
  define: { __BUILD__: '"prueba"' },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts', 'scripts/**/*.test.ts'], // scripts/: revisan archivos del proyecto con Node (no entran en el tsc de la app)
    css: { include: [/styles.css/] }, // las pruebas de accesibilidad leen la hoja de estilos
  },
});
