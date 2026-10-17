# Yapa · repositorio general del proyecto

Repositorio base para continuar el proyecto completo de Yapa: una plataforma web que organiza compras mayoristas consolidadas por zona en Lima.

La app web local ya está disponible en `src/`: permite explorar el catálogo de
esta semana, armar una canasta, registrar una dirección de entrega con mapa
simulado y consultar el historial de pedidos. La app soporta dos modos: Appwrite Cloud
para persistencia real de usuarios, catálogo, pedidos y roles; y un modo local de
demo para probar el flujo sin credenciales. Los pagos siguen simulados.

```bash
npm install
npm run dev
```

Este repositorio conserva el mapa funcional y el contexto del proyecto. La implementación de la exposición académica se mantiene separada en [sdd-2026-exposicion](https://github.com/kaloslazo/sdd-2026-exposicion), donde solo se trabaja la vertical SDD de `CUN-02 Registrar pedido semanal`.

## Contexto académico

- Curso: EL3304 Diseño de Software.
- Sección: 1.
- Docente: Jaime Moshe Farfán Madariaga.
- Integrantes: Carlos Bravo, Aaron Gonzales y Kalos Lazo.
- Estado: modelo de negocio y alcance funcional documentados; implementación integral pendiente.

## Mapa funcional

| Código | Módulo | Estado en este repositorio |
|---|---|---|
| CUN-01 | Actualizar catálogo y precios | Catálogo + panel admin con precio y stock persistidos |
| CUN-02 | Registrar pedido semanal | Flujo con usuario, dirección, mapa simulado, pedido e historial persistidos |
| CUN-03 | Procesar pago | Medios de pago simulados; integración real pendiente |
| CUN-04 | Consolidar por zona | Roadmap |
| CUN-05 | Reponer compra consolidada | Roadmap |
| CUN-06 | Preparar pedidos | Roadmap |
| CUN-07 | Planificar y ejecutar entrega | Roadmap |
| CUN-08 | Resolver incidencia | Roadmap |

## Estructura

- `docs/project-context.md`: lore funcional, actores, entidades y reglas de negocio.
- `docs/module-roadmap.md`: módulos, dependencias y siguientes incrementos.
- `docs/decisions.md`: decisiones de diseño y límites del alcance.
- `docs/reference/`: documento fuente del modelado de negocio.
- `src/`: app React, servicios locales y reglas de dominio testeables.
- `scripts/setup-appwrite.mjs`: crea la base, tablas, permisos, catálogo y admin de Appwrite.
- `supabase/schema.sql`: esquema legado de la primera alternativa; ya no lo usa la app.
- `tests/`: espacio reservado para pruebas del proyecto completo.

## Producto piloto

La primera operación se plantea para Lince, Jesús María y La Victoria. Los pedidos se reciben de lunes 00:00 a miércoles 20:00 y se entregan los sábados en ventanas de 09:00–12:00, 12:00–15:00 y 15:00–18:00, sujetas a capacidad.

## Conectar Appwrite Cloud

1. Crea un proyecto en Appwrite Cloud y registra `localhost` y `127.0.0.1` como Web platforms.
2. Crea una API key con permisos de configuración de Databases/Tables y Users. Solo se usa localmente.
3. Copia `.env.example` a `.env.local` y agrega `APPWRITE_PROJECT_ID`, `APPWRITE_API_KEY` y, opcionalmente, `APPWRITE_ADMIN_USER_ID`.
4. Ejecuta `npm run appwrite:setup`. El script crea la base `yapa`, las tablas con permisos por usuario/etiqueta, siembra el catálogo y marca el admin.
5. Agrega `VITE_APPWRITE_PROJECT_ID` en `.env.local` y vuelve a ejecutar `npm run dev`.

La API key de configuración nunca se expone en el navegador: solo se lee desde el
script Node. El cliente usa el Web SDK de Appwrite con el Project ID público. La
etiqueta `admin` controla el panel y el acceso de operaciones; el rol del perfil
se mantiene para la UI. En modo local, el usuario de prueba del panel admin es
`admin@yapa.pe` con contraseña `admin123`.

Para recuperar contraseñas, agrega también la URL local del proyecto como plataforma
Web; Appwrite enviará el enlace de recuperación al correo del usuario.

## Verificación local

```bash
npm run typecheck
npm run test
npm run build
```

El repositorio mantiene el sistema completo como roadmap. Cada módulo debe entrar
con su propio alcance, decisiones, criterios de aceptación, código y evidencia; no
se debe presentar como implementado aquello que aún es diseño.
