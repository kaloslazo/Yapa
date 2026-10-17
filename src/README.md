# Implementación web

La primera superficie ejecutable del repositorio general es una app web local en
React + TypeScript sobre Vite para explorar el catálogo vigente y registrar un
pedido semanal de demostración.

## Ejecutar

```bash
npm install
npm run dev
```

También se puede validar el build de producción con `npm run build`.

## Alcance actual

- CUN-01: catálogo estático con categorías, búsqueda y precios por unidad.
- CUN-02: canasta local y formulario de pedido con distrito, dirección, mapa simulado, ventana y medio de pago.
- Reglas visibles: cobertura piloto, mínimo de S/ 50, delivery de S/ 7.90,
  delivery gratis desde S/ 120 y ventanas del sábado.
- Cuenta con roles `customer/admin`, adaptador local y conexión a Appwrite Cloud vía `.env`.
- Catálogo, direcciones, pedidos, detalles de pedido y panel admin con persistencia
  conectada; los permisos de tablas y filas limitan el acceso por usuario y etiqueta `admin`.
- Pruebas unitarias de reglas de autenticación, checkout, delivery y códigos de pedido.

Los pagos siguen simulados. Sin credenciales de Appwrite, la app usa persistencia
local para permitir pruebas de extremo a extremo; cuando se configuran las variables
de entorno y se ejecuta `npm run appwrite:setup`, usuarios, catálogo y pedidos pasan a
la base real sin cambiar la UI.

## Estructura

- `src/App.tsx`: composición de la superficie y estado de la experiencia.
- `src/components/`: catálogo, canasta, checkout, iconos y arte de producto.
- `src/data/catalog.ts`: datos iniciales del catálogo y opciones operativas.
- `src/types.ts`: contratos TypeScript del dominio frontend.
- `src/services/`: adaptadores de autenticación y persistencia.
- `src/utils/domain.ts`: reglas de negocio reutilizables y testeables.
- `public/images/products/`: recortes visuales generados para cada producto.

## Verificación

```bash
npm run typecheck
npm run test
npm run build
```
