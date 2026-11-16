# Desarrollo de Yapa después del Lab 4

Iteración 64 validada localmente (13/11/2026), pendiente de revisión: `64-bolsas-con-selector.md`. Selector de bolsas nuevas con una foto por bolsa, confirmación y reintento parcial; 175 pruebas frontend, TypeScript y build aprobados.

Esta copia parte del checkpoint entregado en el Lab 4 (tag `checkpoint-lab4`, rama `carlos/iteracion-2-sdd`, PR #1). El checkpoint no se toca. Aquí se sigue desarrollando en la rama `main` de `Raith726/yapa-desarrollo`.

## Método (el mismo del Lab 4)

Cada iteración sigue el orden SDD y se commitea en ese orden:

1. `docs:` especificación de la iteración (`docs/desarrollo/NN-*.md`): requisito, reglas, errores, criterios de aceptación y supuestos nuevos.
2. `test:` pruebas de aceptación antes del código. Se guarda la ejecución en rojo.
3. `feat:` implementación mínima que cumple la spec.
4. `docs:` trazabilidad y registro de la iteración.

Se respetan las decisiones C-01..C-12 y los supuestos S-01..S-12 de `docs/sdd/10-clarificaciones-v2.md`. Lo nuevo que no esté decidido por el equipo entra como **supuesto a validar** (S-13 en adelante).

## Iteraciones planificadas

| # | Iteración | Origen (decisión del equipo) | Estado |
|---|---|---|---|
| 3 | **Billetera de saldo**: el saldo de la liquidación se guarda, se usa en la siguiente compra (combinado con Yape o Plin), no vence y se puede pedir de vuelta al medio de pago (hasta 30 días) | C-05, C-02 | completa, ver `03-billetera-saldo.md` |
| 4 | **Cancelar y editar el pedido antes del cierre**: devolución completa si todavía no se compró | Carlos 24/09 (cancelación con devolución antes de la compra) | completa, ver `04-cancelar-editar.md` |
| 5 | **Zonas de vecinos**: crear zona con punto de recepción, radio máximo, unir zonas cercanas con dos admins, transferir el rol de admin | C-07 | completa, ver `05-zonas-vecinos.md` |
| 6 | **Catálogo semanal del proveedor aliado (CUN-01)**: lista con tramos, stock máximo y marca única; solo el administrador publica | C-11, C-12, RN-16 | completa, ver `06-catalogo-semanal.md` |
| 7 | **Armado, entrega e incidencias por artículo**: foto por bolsa, foto de entrega en portería, reclamo por artículo en 24 h, colchón de reposición con tope | C-10, decisiones del 24/09 | completa, ver `07-armado-entrega-reclamos.md` |
| 8 | **Métricas del piloto**: recompra en la semana 4, margen por pedido, ahorro entregado | lecciones de los antecedentes | completa, ver `08-metricas-piloto.md` |
| 9 | **Interfaz web** (vecino y admin), responsiva y solo con biblioteca estándar | Entregable 1 §4.1 (app web responsiva) | completa, ver `09-interfaz-web.md` |
| 10 | **Acceso con PIN, sesión y CSRF** | necesario para que el saldo (plata del cliente) esté protegido | completa, ver `10-acceso.md` |
| 11 | **Persistencia en SQLite**: que los datos sobrevivan a reiniciar el servidor | S-62 (hoy todo vive en memoria) | completa, ver `11-persistencia.md` |
| 12 | **Web para lo que falta**: zonas, armado y entrega con foto, reclamos, devolución de saldo, métricas | iteraciones 5, 7 y 8 ya tienen reglas y pruebas, falta la pantalla | completa, ver `12-web-operacion.md` |
| 13 | **Margen neto con costos operativos** por escenario (optimista y pesimista) | hallazgo de la iteración 8 | completa, ver `13-margen-neto.md` (falta que el equipo elija el escenario real) |
| 14 | **Simulador de escenarios** (comisión, pedidos por zona, costo de parada) | decisiones urgentes 1, 2 y 5 | completa, ver `14-simulador-escenarios.md` |
| 15 | **Parte del ahorro que retiene Yapa** (parámetro, 0 % por defecto) | decisión urgente n.º 5 (opción A) | completa, ver `15-reparto-ahorro.md` |
| 16 | **Entrega fallida y cierre del ciclo** (sin reintento; vuelve todo menos el envío real) | decisión urgente n.º 3, hueco 2 de la iteración 7 | completa, ver `16-entrega-fallida-cierre.md` |
| 17 | **Pérdida de una zona fallida en el margen** | hueco de la iteración 16 | completa, ver `17-perdida-zona-fallida.md` |
| 18 | **Cierre de huecos de robustez** (ubicación del vecino, coordenadas, solicitudes de unión, montos, ciclo válido, devoluciones y entrega fallida desde la web) | revisiones de las iteraciones 12 y 16 | completa, ver `18-cierre-huecos.md` |
| 19 | **Conciliación del dinero y semana completa por la web** (registro de caja, `/admin/conciliacion`) | confianza en el saldo (C-05), integración de todas las iteraciones | completa, ver `19-conciliacion-punta-a-punta.md` |
| 20 | **Catálogo semanal desde la web** (pegar la lista del proveedor, desactivar productos) | operación semanal (C-12), iteración 6 | completa, ver `20-catalogo-web.md` |
| 21 | **Huecos del armado, el colchón y el catálogo** (sin bolsas tras cerrar la zona, reposición con pedido, unidad válida, proveedor que deja de ser aliado) | huecos de las iteraciones 6 y 7 | completa, ver `21-huecos-armado-colchon.md` |
| 22 | **Precio de referencia y ahorro frente al mercado** (fuente y fecha, vigencia de 14 días, métrica por canasta) | hueco 2 de la iteración 8, kit de campo, Ley 29571 | completa, ver `22-precio-referencia.md` |
| 23 | **"Te devolvemos" y el ahorro en Mi cuenta** (lo pagado, lo que costó, lo devuelto y la comparación por pedido) | C-05, recompra de la semana 4 (iteración 8) | completa, ver `23-mi-ahorro.md` |
| 24 | **Alta de vecinos y reinicio del PIN** (celular, zona, consentimiento, PIN generado) | S-65 (iteración 10), Ley 29733 | completa, ver `24-alta-vecinos.md` |
| 25 | **Presentación de la web y semana de demo** (portada, avance del tramo, ahorro frente al supermercado, `--demo`) | C-01, C-02, pregunta 64 | completa, ver `25-presentacion-web.md` |
| 26 | **Experiencia de compra** (carrito, pedidos con botones, código de pago generado, listas en vez de escribir, fotos desde la cámara) | revisión del equipo del 17/10, S-150 | completa, ver `26-experiencia-compra.md` |
| 27 | **API JSON para el frontend React** (`/api`, sesión, CSRF, roles) | decisión del equipo del 17/10 | completa, ver `27-api-json.md` |
| 28 | **Admin de zona: beneficios, referidos y su panel** | pedido de Carlos del 17/10, doc 07 | completa, ver `28-admin-zona-beneficios.md` (beneficios a validar con su costo) |
| 29 | **Frontend de Kalos conectado al motor** (vecino, admin de zona, admin de Yapa) | decisión del equipo del 17/10 | completa, ver `29-frontend-tres-roles.md` |
| 30 | **Auditoría módulo por módulo y endurecimiento** (pedido cancelado, coordenadas, cantidades enormes, entradas de la API) | auditoría del 17/10 | completa, ver `30-auditoria-endurecimiento.md` |
| 31 | **Pulido de la tienda** (confirmación al devolver dinero, barra de canasta en el celular, botones de 44 px) | auditoría de diseño del 18/10 | completa, ver `31-pulido-vecino-dinero.md` |
| 32 | **Accesibilidad y lenguaje claro** (foco, contraste, enlace de salto, aviso de conexión) | auditoría de diseño del 18/10 | completa, ver `32-accesibilidad-lenguaje.md` |
| 33 | **Foto del reclamo y confirmaciones del admin** (`GET /api/admin/foto`, confirmar pago, reclamo, unión y separación) | auditoría de diseño del 18/10 | completa, ver `33-admin-foto-confirmaciones.md` |
| 34 | **El admin en el celular** (menú, Salir, tablas, áreas de toque) | recorrido visual del 18/10 | completa, ver `34-admin-celular.md` |
| 35 | **Contadores y búsqueda del admin** (pendientes en el menú, buscador de vecinos) | recorrido visual del 18/10 | completa, ver `35-admin-contadores-busqueda.md` |
| 36 | **Menos etiquetas sobre los títulos** | auditoría de diseño del 18/10 | completa, ver `36-kickers.md` |
| 37 | **Análisis por zona y propuestas del sistema** (`GET /api/admin/analisis`, uniones posibles, demo con dos admins) | pedido del equipo 18/10 | completa, ver `37-analisis-zonas-propuestas.md` |
| 38 | **Mapa real de zonas, sección Zonas y unión visible** (Leaflet, propuestas, Esperando/Te pidió unirse/Retirar) | pedido del equipo 18/10 | completa, ver `38-mapa-zonas-fusion.md` |
| 39 | **Fotos sin dueño y Olvidé mi PIN** (sin bot; cola para el admin) | auditoría de la iteración 33 y pedido del equipo | completa, ver `39-fotos-huerfanas-pin.md` |
| 40 | **Correo obligatorio y recuperar el PIN con un código** (verificación por correo, envío intercambiable) | decisión del equipo 18/10 | completa, ver `40-correo-y-recuperar-pin.md` |
| 41 | **Entrar con Google** (vincular cuenta, verificación del token en el motor, opcional) | decisión del equipo 18/10 | completa, ver `41-entrar-con-google.md` |
| 42 | **Avisos dentro de la app y por correo** (campana, ocho hechos, correo de lo importante) | decisión del equipo 18/10 | completa, ver `42-avisos.md` |
| 43 | **Correos con diseño** (HTML con la marca, código destacado, texto plano de respaldo) | pedido del dueño 19/10 | completa, ver `43-correo-html.md` |
| 44 | **Lista para producción** (administrador real por entorno, sin credenciales de demo, cookie segura, `/salud`, web servida por el motor, servidor con hilos y cerrojo) | despliegue en servidor para el proyecto final | completa, ver `44-produccion.md` |
| 45 | **Registro por invitación** (enlace propio de cada vecino, registro con correo o Google, la zona y el referido de quien invita, topes y avisos; página `/unete`) | pedido del dueño 20/10 | completa, ver `45-registro-por-invitacion.md` |
| 46 | **Entrar con correo o celular** (ya no se pide el número de cliente; quien nació con Google puede crear su PIN, opcional) | prueba del dueño 21/10 | completa, ver `46-entrar-con-correo-o-celular.md` |
| 47 | **Pulido de lanzamiento** (imágenes WebP, favicon, vista previa al compartir, caché de archivos con huella, privacidad en borrador) | revisión del 21/10 | completa, ver `47-pulido-de-lanzamiento.md` |
| 48 | **Datos de demostración y cuentas de depuración** (semana actual en la base real, reloj de demostración, cuentas de prueba, admin global que ve como cualquiera) | pedido del dueño 21/10 | completa, ver `48-demostracion-y-depuracion.md` |
| 49 | **Registro abierto con ubicación** y aprobación del admin de zona | idea del dueño 21/10 | pendiente (reservada) |
| 52 | **Despliegue automático** (flujo de GitHub, runner en la VPS, paquete con token temporal, marcha atrás si el motor nuevo no responde) | pedido de Kalos 21/10 | completa y probada de punta a punta (un push a `main` cambió solo la web), ver `52-despliegue-automatico.md` |
| 53 | **La sesión no se pierde por cookies de otros servicios** (la cookie de Google sacaba al usuario al recargar) | hallado en producción 22/10 | completa, ver `53-cookies-de-otros-sitios.md` |
| 54 | **Cuentas para proveedores y transportistas** (el admin las crea; el transportista ve su reparto y registra la entrega con foto; el proveedor propone su lista semanal y ve lo que le compramos) | pedido del equipo 26/10 | completa, ver `54-proveedores-y-transportistas.md` |
| 55 | **Cuentas para compras, armado, atención y portería** (Tabla 3 del Informe PC3: cada rol con su cuenta y solo sus secciones; la portería o el admin de zona confirman la recepción y se avisa a cada vecino) | pedido del equipo 06/11 | completa, ver `55-personal-por-rol.md` |
| 56 | **Compra real, dañados, rótulos, bloqueo del despacho e incidencias** (faltante del proveedor y dañado: colchón primero y luego saldo a los últimos pedidos; la zona no sale sin compra registrada) | Tabla 3 del Informe PC3; decisión de Kalos 09/11 | completa, ver `56-compra-real-y-armado.md` |
| 57 | **Yapa retiene el 25 % del ahorro y el vecino puede retirar su consentimiento** (anonimización, Ley 29733) | decisiones urgentes 49 y 67, Kalos 09/11 | completa, ver `57-ahorro-retenido-y-retiro-de-datos.md` |
| 58 | **Logística propia** (cobro por Plin sin comisión, flete de compra pagado por Yapa, salida a reparto con aviso, seguimiento de 7 pasos y margen real) | decisión de Kalos 09/11, con fuentes | completa, ver `58-logistica-propia.md` |
| 59 | **Seguimiento del pedido** (estado en una frase, pasos verticales con hora y detalle, fotos del propio pedido, a qué Plin pagar) | revisión de la pantalla del vecino 09/11 | completa, ver `59-seguimiento-del-pedido.md` |
| 60 | **"Arma mi canasta" con IA** (Groq, con GitHub Models de respaldo; la IA sugiere y el motor valida) | pedido de Kalos 09/11 | completa, ver `60-arma-mi-canasta-ia.md` |
| 61 | **Ayuda de IA para atención** (categoría, prioridad y borrador; no cambia estados) | pedido de Kalos 09/11 | completa, ver `61-atencion-con-ia.md` |
| 62 | **Avance del grupo para el vecino** (pedidos verificados frente a 8 en la tarjeta de la semana; solo el conteo) | estructura nueva de la tienda 10/11 | completa, ver `62-avance-del-grupo-para-el-vecino.md` |
| 63 | **Paneles y Explorar más claros** (fechas y zonas en armado, completados en atención, seguimiento en portería, editor del proveedor) | pedido de Aaron 11/11 | completa, ver `63-paneles-y-explorar.md` |
| 64 | **La operación en el celular** (tablas como tarjetas, nombres y fotos en vez de claves, elegir en vez de escribir, armado con cámara) | recomendación del profesor en la demo, 12/11 | completa, ver `64-operacion-en-el-celular.md` |
| 65 | **Pedidos y reclamos del vecino como un carrito** (fotos de cada producto, reclamar tocando, solo lo reclamable en 24 horas, tus reclamos con su estado) | revisión de la demo, 12/11 | completa, ver `65-reclamos-como-un-carrito.md` |
| 66 | **Ver la foto que se toma** (vista previa antes de enviar, miniaturas de las bolsas en el armado) | revisión del 12/11 | completa, ver `66-ver-la-foto.md` |
| 67 | **Cantidades con su unidad** (5 kg o 2 unidades en armado, pedido y reclamos) | revisión del 12/11 | completa, ver `67-cantidades-con-unidad.md` |
| 68 | **Predicción de demanda** (regresión sobre 8 semanas por zona, estimado y aviso para cotizar con el mayorista) | propuesta de IA del curso, 16/11 | completa, ver `68-prediccion-de-demanda.md` |
| 50 | **Endurecimiento antes de abrir** (tope del cuerpo fuera del cerrojo, fotos solo donde se usan y con tipo real, cambiar el PIN cierra las sesiones, "ver como" sin sacar dinero, CI en la raíz) | revisión de seguridad 21/10 | completa, ver `50-endurecimiento-antes-de-abrir.md` |
| 51 | **Cierre de huecos para pasar a `main`** (límites por dirección, zonas públicas sin contacto, correo apagado sin SMTP en servidor, CSP y HSTS, sesiones vencidas, semana en palabras, panel y mapa bajo demanda) | revisión de seguridad 21/10 | completa, ver `51-cierre-de-huecos-para-main.md` |
| — | **Costos operativos en el margen** (armado, cobro, atención) | hallazgo de la iteración 8: el margen sin estos costos puede ser engañoso | necesita decisión del equipo |

## Registro

Iteración 63: **Paneles y Explorar más claros**, completa localmente (11/11/2026), pendiente de revisión del equipo. Ver `63-paneles-y-explorar.md`: fechas y zonas en Armado, Completados en Atención, seguimiento de Portería, editor de Proveedor y contenido plegable en Explorar. Compras y Reparto conservados.

Ver `docs/desarrollo/99-registro.md`.
