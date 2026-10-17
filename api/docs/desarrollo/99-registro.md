# Registro de iteraciones de desarrollo

## Iteración 3 · Billetera de saldo (24/09/2026)

- Spec: `03-billetera-saldo.md`. Se agregan los supuestos S-13..S-17, que el equipo debe validar.
- Pruebas antes del código: `docs/evidencia/desarrollo/03-billetera-rojo.txt`.
- Diseño: `Order` pasa a tener una lista de pagos (saldo + Yape/Plin), se crea el módulo `wallet.py`, y la liquidación abona saldo y registra reembolsos.
- En la revisión apareció una regla nueva, **BS-15 "todo o nada"**: la liquidación aplicaba efectos (estados) antes de validar el reporte de faltantes. Se reordenó para validar primero y aplicar después.
- Resultado: 61 pruebas en verde. Las de la iteración 2 siguen pasando sin cambios.
- Nota: las líneas de código citadas en `docs/sdd/06-trazabilidad.md` corresponden al checkpoint del Lab 4 (tag `checkpoint-lab4`).

## Iteración 4 · Cancelar y editar (24/09/2026)

- Spec: `04-cancelar-editar.md`, con los supuestos S-18..S-24.
- Pruebas antes del código: `docs/evidencia/desarrollo/04-cancelar-editar-rojo.txt`.
- **Hallazgo de seguridad al diseñar:** editar un pedido a la baja habría convertido en saldo real un pago **sin verificar**, lo que permitía cobrar con un código de operación falso. Se especificó S-24/CE-12, se agregó la prueba CE-H y recién después se implementó.
- Implementación: módulo `order_changes.py`. "Un pedido por ciclo" pasa a significar "un pedido **activo**" (`store.find_order`), y la liquidación ignora los pedidos cancelados por el cliente.
- Resultado: 79 pruebas en verde.

## Iteración 5 · Zonas de vecinos (24/09/2026)

- Spec: `05-zonas-vecinos.md`, con los supuestos S-25..S-32 (radio de 300 m, unión a 500 m sin cadenas, activación por portería o encargado).
- Pruebas antes del código: `docs/evidencia/desarrollo/05-zonas-rojo.txt`.
- Al revisar las pruebas se corrigió un dato del ZA-07: el vecino quedaba a exactamente 300 m de la otra zona, así que la prueba dependía de un redondeo. Se movió a 150 m y 250 m.
- Implementación: módulo `zones.py`. `Zone` ahora tiene coordenadas, admin y datos de recepción, y `Customer` tiene ubicación opcional.
- Resultado: 94 pruebas en verde.

## Iteración 6 · Catálogo semanal del proveedor aliado (24/09/2026)

- Spec: `06-catalogo-semanal.md`, con los supuestos S-33..S-37, S-38 (orden de los errores al publicar) y S-39 (editar con un producto desactivado), todos a validar por el equipo.
- Pruebas antes del código: `docs/evidencia/desarrollo/06-catalogo-rojo.txt` (9 errores: el módulo no existía y las reservas no tenían ciclo).
- Implementación: módulo `catalog.py` (`publish_catalog`, `deactivate_product`). El store guarda un catálogo por ciclo, los administradores y los proveedores; las reservas pasan a ser por ciclo, lo que corrige la limitación anotada en la iteración 3. `Product` tiene `supplier_id` opcional y `cycle.opens_at` da el lunes 00:00 del ciclo.
- Se anotaron en la spec cuatro huecos para el equipo (editar un pedido con un producto desactivado, desactivar en el catálogo base, unidad y paso sin validar, proveedor que deja de ser aliado).
- Resultado: 106 pruebas en verde (`docs/evidencia/desarrollo/06-catalogo-verde.txt`).
- **Revisión:** editar un pedido con un producto desactivado rechazaba toda la edición. Se especificó S-39/CT-11 (la línea desactivada se mantiene con la misma cantidad o menos), se agregó la prueba CT-M en rojo (`06-catalogo-edicion-rojo.txt`) y después el código. Resultado: 107 pruebas en verde.

## Iteración 7 · Armado, entrega en portería, reclamos por artículo y colchón (24/09/2026)

- Spec: `07-armado-entrega-reclamos.md`, con los supuestos S-40..S-46, a validar por el equipo (personal = administradores, entrega por zona todo o nada, plazo de 24 h, aprobación con el ciclo liquidado, colchón de S/ 500 solo con limpieza).
- Pruebas antes del código: `docs/evidencia/desarrollo/07-armado-entrega-rojo.txt`.
- Implementación: módulos `fulfillment.py` (bolsas y entrega), `claims.py` (reclamo y revisión) y `buffer.py` (colchón). La liquidación guarda su resultado en `store.settlements` para que el reclamo aprobado use el precio final del artículo.
- **Decisión de diseño para no devolver dos veces:** un faltante que ya se descontó en la liquidación no se puede aprobar otra vez como reclamo (RV-04, criterio RV-E).
- Se anotaron cinco huecos para el equipo en la spec.
- Resultado: 132 pruebas en verde (`docs/evidencia/desarrollo/07-armado-entrega-verde.txt`).

## Iteración 8 · Métricas del piloto (24/09/2026)

- Spec: `08-metricas-piloto.md`, con los supuestos S-47..S-52, a validar por el equipo (qué cuenta como compra, cohorte por primera compra con meta del 50 %, margen de contribución sin costos operativos, ahorro sin faltantes ni reclamos).
- Pruebas antes del código: `docs/evidencia/desarrollo/08-metricas-rojo.txt`.
- Implementación: módulo `metrics.py`, que solo lee la liquidación guardada, los pedidos y los reclamos. `cycle.add_weeks` calcula el ciclo N + 3.
- Hallazgo: con una parada de S/ 100 y 8 pedidos, el tope de envío de S/ 5 deja cada pedido con margen negativo (−S/ 1.86). El mínimo de 8 pedidos (S-06) solo cubre paradas de hasta S/ 40.
- Se anotaron cuatro huecos para el equipo en la spec.
- Resultado: 140 pruebas en verde (`docs/evidencia/desarrollo/08-metricas-verde.txt`).


## Iteración 9 · Interfaz web (24/09/2026, rama `carlos/web`)

- Spec: `09-interfaz-web.md`, con los supuestos S-60..S-63 (sin inicio de sesión todavía, admin solo local, datos en memoria, hora fija para la demo).
- Pruebas antes del código: `docs/evidencia/desarrollo/09-web-rojo.txt`. Hay 13 pruebas que llaman a la aplicación WSGI sin levantar el servidor.
- La web es solo un adaptador (`src/yapa_sdd/web/`): no tiene reglas de negocio propias, llama a los casos de uso de las iteraciones 2 a 6.
- **Revisión visual:** una captura a 390 px parecía mostrar la página desbordada. Se investigó y resultó ser un límite de la herramienta: Chrome sin interfaz no dibuja por debajo de 512 px y recortaba la imagen. A 512 px se ve bien. Igual se dejó el ajuste de CSS (`min-width:0` en la fila), que ayuda en pantallas más angostas.
- Resultado: la suite completa en verde.

## Iteración 10 · Acceso con PIN, sesión y CSRF (24/09/2026, rama `carlos/web`)

- Spec: `10-acceso.md` (S-64..S-71). Reemplaza a S-60 y S-61 de la iteración 9: ya no se entra con solo escribir un número de cliente, y el admin tiene contraseña.
- Las pruebas de la iteración 9 se adaptaron **antes** del código. WA-07, WA-11 y WA-12 cambiaron según la spec 10.
- Implementación: `auth.py` (PIN con hash PBKDF2 y sal, bloqueo tras 5 fallos, mismo error si el usuario no existe). En `web/app.py`: sesión en el servidor con cookie `HttpOnly`/`SameSite=Lax`, rol por ruta, token CSRF en cada POST, entrar, salir y cambiar PIN.
- La suite tardaba 24 s por el hash lento. Se resolvió bajando las iteraciones solo en las pruebas, y AA-11 fija el valor de producción.
- Resultado: 130 pruebas en verde en la rama.

## Iteración 11 · Persistencia en SQLite (24/09/2026)

- Spec: `11-persistencia.md` (S-90..S-94). Se guarda el estado completo después de cada POST exitoso, en una transacción.
- Pruebas antes del código: `docs/evidencia/desarrollo/11-persistencia-rojo.txt`. La prueba PA-04 se corrigió antes de programar, porque la falla simulada ocurría en el primer dato y no probaba el "todo o nada".
- Seguridad: al cargar solo se reconstruyen clases del propio paquete. Una base alterada se rechaza sin ejecutar nada.
- **Hallazgo al probar con el servidor real:** con una base nueva nadie podía entrar (no hay PINs). Se agregó S-94 (credenciales de demo solo si no hay ninguna).
- Resultado: 174 pruebas en verde y prueba manual de punta a punta con HTTP real.

## Iteración 12 · Pantallas web de operación (24/09/2026)
- **Spec:** `12-web-operacion.md`, con los supuestos S-72..S-80, a validar por el equipo. Los principales:
  - la foto es una referencia de texto y subir archivos queda fuera de alcance;
  - las acciones de zona las hace el vecino admin de la zona;
  - la web solo controla el formato de los datos;
  - el tablero de métricas es por ciclo.
- **Pruebas antes del código:** `docs/evidencia/desarrollo/12-web-operacion-rojo.txt`. Son 15 pruebas nuevas (OA-01..OA-15) contra la aplicación WSGI, con una hora del servidor que avanza del miércoles al domingo.
- **Implementación en la web (`web/app.py` y `web/views.py`), sin reglas de negocio propias:**
  - el vecino tiene `/zona`, `/reclamos` y la devolución de saldo en `/cuenta`;
  - el administrador tiene `/admin/armado` (bolsas y entregas), `/admin/reclamos`, `/admin/colchon` y `/admin/metricas`;
  - cada ruta llama al caso de uso con el actor de la sesión.
- **Único cambio fuera de la web (S-75):** unirse a una zona sin ubicación, o unirla a un grupo, fallaba con un error interno. Ahora responde `LOCATION_REQUIRED`.
- **Revisión:**
  - Las fotos se muestran como texto y no como enlace, para que una referencia `javascript:` no se pueda usar para atacar.
  - Un monto como `abc` o `0.001` hacía fallar el pedido de devolución. La web ahora lo rechaza con `INVALID_INPUT` (S-76).
- Se anotaron nueve huecos para el equipo en la spec. El más visible: no hay cómo registrar la ubicación del vecino, así que en la demo nadie puede crear una zona.
- **Resultado:** 182 pruebas en verde (`docs/evidencia/desarrollo/12-web-operacion-verde.txt`).

## Iteración 13 · Margen neto con costos operativos (24/09/2026)

- Spec: `13-margen-neto.md` (S-95..S-97). Atiende el hallazgo urgente n.º 1: el margen de contribución de S/ 5.64 no incluía armado, cobro ni atención.
- **Resultado con los costos documentados** (escenario MT-A, 8 pedidos): optimista **+S/ 3.31** por pedido; pesimista **−S/ 1.82** por pedido (los 8 pierden). La diferencia la hacen el cobro (Yape Empresa 2.95 % frente a Plin 0 %) y que el proveedor entregue o no.
- No se decidió qué escenario es el real: eso lo decide el equipo. El código deja los escenarios como datos.
- Resultado: la suite completa en verde.

## Iteración 14 · Simulador de escenarios (24/09/2026)

- Spec: `14-simulador-escenarios.md` (S-98, S-99). El simulador usa las reglas reales sobre un repositorio aparte.
- **La prueba SA-02 desmintió una suposición de la propia spec** ("más pedidos, mejor margen"). En realidad el margen de Yapa baja con el volumen, porque todo el ahorro vuelve al cliente y la comisión es un % del precio final. Se corrigió la spec (commit `docs:`) y la prueba se reescribió según el comportamiento verdadero, sin debilitarla. Es un ejemplo claro de cómo SDD y las pruebas detectan un error de razonamiento de negocio antes de lanzar.
- Hallazgos para el equipo:
  - En el escenario pesimista no alcanza ni con 15 % de comisión.
  - Con una parada de S/ 100, el mínimo optimista es 13 pedidos, no 8.

  Se agregaron a las decisiones urgentes.
- Resultado: la suite completa en verde.

## Iteración 15 · Parte del ahorro que retiene Yapa (24/09/2026)

- Spec: `15-reparto-ahorro.md` (S-100, S-101). Un parámetro de la liquidación, que por defecto es 0 %: el modelo actual no cambia.
- Resultado del simulador: retener el 25 % deja el peor escenario en −S/ 0.06 por pedido (antes −S/ 2.52), y el cliente sigue recuperando S/ 10.39 (antes S/ 12.86). Queda como dato para la decisión urgente n.º 5.
- Resultado: 189 pruebas en verde.

## Iteración 16 · Entrega fallida y cierre del ciclo (24/09/2026)

- Spec: `16-entrega-fallida-cierre.md` (S-102..S-106). Responde la decisión urgente n.º 3 con las recomendaciones del cuestionario (sin reintento; se devuelve todo menos el envío real, como saldo). Queda para que el equipo lo valide.
- Nuevo `close_cycle`: el ciclo solo se liquida cuando cada zona atendida se entregó o falló. Cierra el hueco 2 de la iteración 7. `settle_cycle` sigue siendo el cálculo puro.
- Hueco abierto: la merma de los frescos de una zona fallida todavía no aparece como pérdida en las métricas.
- Resultado: 196 pruebas en verde.

## Iteración 17 · Pérdida de una zona fallida en el margen (24/09/2026)

- Spec: `17-perdida-zona-fallida.md` (S-107, S-108). Una zona fallida muestra una pérdida de −S/ 47.00 por pedido en el escenario base y los pedidos aparecen en las alertas.
- Resultado: 199 pruebas en verde.

## Iteración 18 · Cierre de huecos de robustez (24/09/2026)

- Spec: `18-cierre-huecos.md` (S-109..S-112). Cierra los huecos 1 a 7 y 9 que reportó la iteración 12, y el que apareció al integrar la iteración 16 (la web liquidaba sin exigir entregas).
- Ahora la demo sirve de punta a punta: el vecino registra su ubicación y las zonas del piloto tienen coordenadas, así que se pueden crear zonas y unirse a ellas.
- Cambió el ejemplo de OA-03/OA-04 y el resultado esperado de WA-10. Se documentó en la spec y las pruebas se actualizaron **antes** del código.
- Resultado: 226 pruebas en verde.

## Iteración 19 · Conciliación del dinero y semana completa (24/09/2026)

- Spec: `19-conciliacion-punta-a-punta.md` (S-113..S-115). Se agrega un registro de caja y la cuenta **recibido = en curso + retenido + deuda con clientes + devoluciones pagadas**. El admin la ve en `/admin/conciliacion`.
- Hueco encontrado al diseñar: al editar un pedido a la baja, se perdía cuánto se había cobrado de verdad. Ahora lo guarda el registro de caja.
- Nueva prueba de punta a punta: una semana completa por la web (pedidos, verificación, cancelación, armado, entrega, liquidación, reclamo, devolución). La diferencia es 0 después de cada paso.
- Se corrigió el escenario de la prueba, no el código. El vecino pedía devolver S/ 10, pero solo tenía S/ 5.38, y el sistema lo rechazó como debía. Primero se cambió la spec y después la prueba.
- Resultado: 230 pruebas en verde.

## Iteración 20 · Catálogo semanal desde la web (24/09/2026)

- Spec: `20-catalogo-web.md` (S-116..S-120). El admin pega la lista del proveedor, separada por comas, en `/admin/catalogo`. La pantalla abre con el ciclo siguiente y la lista actual ya cargada, y permite desactivar un producto.
- Cambio de regla (S-118): antes no se podía desactivar un producto en una semana que usaba el catálogo base. Ahora se guarda una copia para esa semana.
- Error encontrado al revisar: un paso de 0 dividía por cero. Se agregó S-120 a la spec, luego la prueba CW-I en rojo y después la corrección.
- Resultado: 244 pruebas en verde.

## Iteración 21 · Huecos del armado, el colchón y el catálogo (25/09/2026)

- Spec: `21-huecos-armado-colchon.md` (S-121..S-124). Cierra los huecos 3 y 4 de la iteración 6 y los huecos 3 y 4 de la iteración 7 (este último, en parte).
- Cambio de firma: `use_buffer` ahora pide el pedido y la hora. Se actualizaron CO-D, CO-E y OA-11 en un commit `test:`, y los números que verifican no cambiaron.
- Datos del escenario corregidos antes del código: dos pedidos no respetaban el mínimo de S/ 50 ni el máximo de 10 kg por producto.
- Resultado: 253 pruebas en verde.

## Iteración 22 · Precio de referencia y ahorro frente al mercado (25/09/2026)

- Spec: `22-precio-referencia.md` (S-125..S-129). El admin registra precios del mercado de barrio y del supermercado, con fuente y fecha. El vecino los ve en el catálogo mientras estén vigentes (14 días), y las métricas muestran el ahorro real del ciclo.
- Con los precios de ejemplo, la canasta de prueba ahorra 43.9 % frente al supermercado, pero solo **7.8 %** frente al mercado (con precios de mercado inventados). La papa amarilla queda en 10.4 %, debajo de la meta de 15 %. Coincide con lo que ya advertía el análisis económico: el competidor real es el mercado, no el supermercado.
- Error encontrado al revisar: la base SQLite no guardaba fechas sin hora. Se agregó RF-I a la spec, luego la prueba en rojo y después la corrección.
- Resultado: 266 pruebas en verde.

## Iteración 23 · "Te devolvemos" y el ahorro en Mi cuenta (25/09/2026)

- Spec: `23-mi-ahorro.md` (S-130..S-132). Cada pedido liquidado muestra lo que se pagó, lo que costó, lo que se devolvió y a dónde, y cuánto costaba en el mercado y en el supermercado. Arriba, el total devuelto.
- Se unificó el cálculo por canasta de la iteración 22 (`_basket_reference`) y se corrigió el empate entre dos precios con la misma fecha: ahora gana el último registrado.
- Resultado: 272 pruebas en verde.

## Iteración 24 · Alta de vecinos y reinicio del PIN (25/09/2026)

- Spec: `24-alta-vecinos.md` (S-133..S-138). El admin da de alta a un vecino en `/admin/vecinos` con nombre, celular, zona y consentimiento (Ley 29733). El sistema genera el PIN y lo muestra una sola vez. Si el vecino olvida el PIN, el admin genera uno nuevo, y eso también desbloquea la cuenta.
- Cierra el hueco de S-65: el PIN inicial lo asignaba el admin "al dar de alta", pero no había alta.
- Resultado: 282 pruebas en verde.


## Iteración 25 · Presentación de la web y semana de demo (17/10/2026)

- Spec: `25-presentacion-web.md` (S-139..S-143). Portada con "Cómo funciona" y la promesa del precio máximo, barra de avance hacia el siguiente tramo, distintivo "N % menos que en Plaza Vea", saldo destacado en Mi cuenta y panel del admin con accesos. Sin recursos de otros sitios.
- `python -m yapa_sdd.web --demo` arranca con la semana 2026-W39 entregada y liquidada y la 2026-W40 abierta. Se arma solo con los casos de uso, y la conciliación da 0.
- Error encontrado en la spec: PW-D decía 49.6 % porque se calculó con el precio redondeado. Se corrigió la spec, luego la prueba y después el código.
- Resultado: 292 pruebas en verde.

## Iteración 26 · Experiencia de compra (17/10/2026)

- Spec: `26-experiencia-compra.md` (S-144..S-152). Catálogo con botones − y + y carrito fijo con el mínimo y el ahorro aproximado; página "Tu carrito"; confirmación con lo que sigue; Mi cuenta con tarjetas por pedido, avance, botones para cancelar y "Ahorraste S/ X frente al supermercado"; panel del admin con resumen de la semana.
- Revisión del equipo: escribir lo menos posible. Ciclos, pedidos, zonas y vecinos se eligen de listas; las fotos se suben desde la cámara; la ubicación se toma con un botón.
- Decisión de Carlos (S-150): el vecino ya no escribe el código de operación. Yapa genera un código de pago y le dice cuánto yapear.
- Se ajustaron WA-05 y WA-08 (estados en palabras, S-146) en un commit `test:` antes del código.
- Resultado: 305 pruebas en verde.

## Iteración 27 · API JSON para el frontend (17/10/2026)

- Decisión del equipo: la app React de Kalos (`kaloslazo/Yapa`) es el frontend y este motor es el backend. El motor entró al repo de Kalos en `api/` con su historial (`git subtree`), en la rama `carlos/motor-y-roles`.
- Spec: `27-api-json.md` (S-153..S-157). `/api/...` con sesión, CSRF por cabecera, errores en JSON y roles `vecino`, `admin_zona` y `admin`.
- Resultado: 314 pruebas en verde.

