import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
    css: { include: [/styles.css/] }, // las pruebas de accesibilidad leen la hoja de estilos
  },
});
