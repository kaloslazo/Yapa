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

## Iteración 28 · Admin de zona: beneficios, referidos y su panel (17/10/2026)

- Spec: `28-admin-zona-beneficios.md` (S-158..S-165). Envío gratis y 5 % las primeras 4 semanas para el admin de zona, código de referido `NOMBRE+número`, premio de S/ 3.00 + S/ 3.00 al liquidar el primer pedido del invitado, y el panel del admin de zona en `/api/mi-zona` (avance del grupo, vecinos que ya pidieron, zonas cercanas para unir, beneficios y código).
- Costo de cada beneficio en la spec, para que el equipo decida con números (lección L2 de los antecedentes).
- Error encontrado al implementar (AZ-09): `pilot_store()` compartía las mismas zonas entre repositorios. Primero la spec, luego la prueba en rojo, luego la corrección.
- Resultado: 324 pruebas en verde.

## Iteración 29 · Frontend de Kalos conectado al motor: vecino, admin de zona y admin de Yapa (17/10/2026)

- Spec: `29-frontend-tres-roles.md` (S-166..S-169). La tienda de Kalos ya no calcula reglas: todo viene de la API. Se agregaron el panel del admin de zona y el centro de operaciones completo, y el pago sin escribir códigos.
- Se retiró Appwrite y la copia en TypeScript de las reglas (S-168); quedan en el historial.
- Errores de la spec corregidos antes del código: FE-E (55.95, no 56.00) y FE-09 (faltaba la ruta para guardar la ubicación).
- Resultado: 325 pruebas del motor y 6 del frontend en verde; typecheck y build sin errores.

## Iteración 30 · Auditoría módulo por módulo y endurecimiento (17/10/2026)

- Spec: `30-auditoria-endurecimiento.md` (S-170, S-171). Se sondearon todos los módulos con entradas hostiles y con una simulación de 600 semanas al azar que comprueba la conciliación en cada paso. **El dinero resistió las 600 semanas** (diferencia 0, ningún saldo negativo, guardar y cargar sin pérdidas).
- Huecos corregidos: verificar el pago de un pedido cancelado metía plata a la caja sin dueño; una zona creada con coordenadas en texto rompía la unión de vecinos y el panel; `1e999` tumbaba pedido, reclamo y colchón; la API caía con PIN, celular o lista como número, o con listas donde iba texto; las caídas respondían texto en vez de JSON; el admin podía consultar semanas que no existen.
- Queda para decisión del equipo: devolver el pago externo de un pedido cancelado antes de verificarse (S-20), limpiar sesiones, cookie `Secure` al publicar con HTTPS, y el bloqueo de cuenta por fuerza bruta.
- Resultado: 340 pruebas del motor en verde (15 nuevas), 6 del frontend sin cambios.

## Iteración 31 · Pulido de la tienda: dinero con confirmación y compra en el celular (18/10/2026)

- Spec: `31-pulido-vecino-dinero.md` (S-172..S-174). Sale de la auditoría de diseño del 18/10 por tipo de usuario (vecino, admin de zona, admin de Yapa) con revisión de código y recorrido en navegador a 390 px.
- Cancelar un pedido y devolver el saldo a Yape o Plin ahora piden confirmar y dicen el plazo con palabras. En el celular hay una barra fija con el total y lo que falta para el mínimo, botones de al menos 44 px y el menú con pista de que se desliza.
- Queda para la iteración 32: ver la foto del reclamo (hace falta un endpoint solo para el admin), confirmaciones del admin de zona y de Yapa. Accesibilidad (foco, grises, enlace de salto) en una iteración propia.
- Resultado: 13 pruebas del frontend en verde (antes 6), typecheck y build sin errores; el motor no cambió.

## Iteración 32 · Accesibilidad y lenguaje claro de la tienda (18/10/2026)

- Spec: `32-accesibilidad-lenguaje.md` (S-175..S-178). Sale de la auditoría del 18/10: foco invisible en listas y subida de foto, gris de apoyo con contraste 3.5 a 4.2, enlace de salto roto fuera del catálogo, aviso de conexión con comando de Python, avisos de 3 segundos.
- Cambios: foco visible en todos los campos, gris `#526059` (mínimo 4.88:1 sobre cualquier fondo), anillo de foco de 3 px en acento oscuro, enlace de salto que funciona en toda página, filtro de categorías con botones, aviso "No pudimos conectar con Yapa" con Reintentar, avisos de 6 s (9 s las advertencias), y textos sin códigos en el admin.
- Las pruebas de accesibilidad leen la hoja de estilos y comprueban contraste y foco: si alguien oscurece o aclara un color por error, falla.
- Queda: foto del reclamo y confirmaciones del admin (iteración 33), kickers sobre los títulos, bordes de campos y fotos reales de productos.
- Resultado: 27 pruebas del frontend en verde (antes 13), typecheck y build sin errores; el motor no cambió.

## Iteración 33 · El admin ve la foto del reclamo y confirma lo que mueve dinero o zonas (18/10/2026)

- Spec: `33-admin-foto-confirmaciones.md` (S-179..S-181). El admin de Yapa decidía reclamos sin ver la foto, porque la API guardaba las fotos pero no las entregaba.
- Nuevo `GET /api/admin/foto?ruta=...`: solo admin, solo rutas con la forma exacta que escribe el motor (nada de `..`, rutas absolutas ni otros tipos), con `nosniff` y sin caché. Nueve rutas hostiles probadas.
- En pantalla: miniatura de la foto en cada reclamo y confirmación corta al aprobar o rechazar (dice el efecto), al verificar un pago (muestra monto y código) y al pedir unión o separar la zona.
- Pregunta para el equipo: las fotos de reclamos fallidos quedan guardadas (huérfanas).
- Resultado: 346 pruebas del motor (6 nuevas) y 32 del frontend (5 nuevas), typecheck y build sin errores.

## Iteración 34 · Recorrido visual del admin en el celular (18/10/2026)

- Spec: `34-admin-celular.md`. Sin supuestos nuevos. Recorrido a 390 px de las 9 secciones del admin y de las pantallas del vecino.
- Encontrado y corregido: el menú del admin mostraba una sola sección (cada opción medía 335 px), el botón Salir quedaba oculto en el celular, dos tablas (Conciliación y Revisados) se cortaban por la derecha, y "Desactivar", "Nuevo PIN", los textos de enlace y los resúmenes de pedido medían 21 a 25 px de alto.
- Resultado: 35 pruebas del frontend (3 nuevas), typecheck y build sin errores. El motor no cambió.

## Iteración 35 · Contadores en el menú del admin y búsqueda de vecinos (18/10/2026)

- Spec: `35-admin-contadores-busqueda.md`. Sin supuestos nuevos.
- Menú del admin: número de pagos por verificar, reclamos pendientes y devoluciones por hacer, que se actualiza tras cada acción.
- Padrón: buscador por nombre, número o celular, sin distinguir tildes ni mayúsculas.
- También se recorrió el admin de zona (Ana) a 390 px: sin desbordes ni botones chicos, y la confirmación de "Separar mi zona" se ve bien.
- Resultado: 40 pruebas del frontend (5 nuevas), typecheck y build sin errores. El motor no cambió.

## Iteración 36 · Menos etiquetas sobre los títulos (18/10/2026)

- Spec: `36-kickers.md`. Se quitaron las etiquetas decorativas y se dejaron las que dan un dato (semana, regla, paso).
- Resultado: 40 pruebas del frontend, typecheck sin errores. Solo cambia la pantalla.

## Iteración 37 · Análisis por zona y propuestas del sistema (18/10/2026)

- Spec: `37-analisis-zonas-propuestas.md` (S-182..S-189, a validar). Nuevo `GET /api/admin/analisis`: por zona, pedidos, avance, adopción y margen; los pares de zonas que se pueden unir (con el motivo si hoy no) y propuestas del sistema: unir, recordar, invitar, revisar costo y reactivar.
- `merge_blocker` reutiliza las reglas de pedir y aceptar la unión, sin duplicarlas.
- La demo suma el Edificio Arenales con su admin (Marta, cliente 116) a 391 m de Los Álamos, para ver la unión con acuerdo de los dos admins.
- Resultado: 364 pruebas del motor (18 nuevas). Solo lee: no mueve dinero ni zonas.

## Iteración 38 · Mapa real de zonas, sección Zonas del admin y unión visible (18/10/2026)

- Spec: `38-mapa-zonas-fusion.md` (S-190..S-193, a validar). Mapa real con Leaflet y mosaicos de OpenStreetMap: cada zona es un círculo de 300 m del color de su grupo, las uniones posibles son líneas verdes con su distancia y las bloqueadas, grises con el motivo en palabras.
- Admin de Yapa: sección **Zonas** con el mapa, las propuestas del sistema y la tabla por zona (vecinos, pedidos, verificados, adopción y margen). El menú muestra cuántas propuestas hay.
- Admin de zona: el mapa esquemático se reemplazó por el real. Cada zona cercana dice si hoy se puede pedir la unión; una unión pedida muestra "Esperando a su admin" con Retirar; la zona que la recibe ve "Te pidió unirse" y acepta.
- Motor (iteración 37, completada aquí): `motivo` en las cercanas, `enviadas`, `POST /api/solicitudes/<id>/retirar`, propuestas solo para el piloto, singular y plural correctos.
- Recorrido en el navegador con la demo: Marta (Edificio Arenales) pide unirse a Los Álamos, Ana acepta y las tres zonas quedan unidas con el mismo color.
- Errores propios corregidos en el camino: el mapa dejaba la app en blanco por usar `getBounds` de un círculo antes de tener vista (ahora se calcula directo y un fallo del mapa no tumba la pantalla); mis datos de prueba no contaban los 3 vecinos que ya trae el piloto; la spec decía 403 donde el motor responde 422.
- Resultado: 372 pruebas del motor (26 nuevas) y 55 del frontend (15 nuevas), typecheck y build sin errores.

## Iteración 39 · Fotos sin dueño y "Olvidé mi PIN" (18/10/2026)

- Spec: `39-fotos-huerfanas-pin.md` (S-194..S-200, a validar).
- Fotos: antes la foto se guardaba antes de validar la acción, así que un reclamo rechazado dejaba un archivo sin dueño. Ahora, si la acción falla, el archivo de esa petición se borra (solo ese archivo).
- Olvidé mi PIN **sin bot ni correo**: el vecino pide ayuda con su número de cliente y recibe siempre el mismo mensaje, exista o no el número. El admin ve la cola en Vecinos (con número en el menú) y la atiende con "Nuevo PIN y escribir", que abre WhatsApp al celular registrado; o la descarta. El PIN nunca se muestra a quien lo pide.
- Un bot de WhatsApp o correo se retoman cuando el volumen lo pida; piden decisiones del equipo (número de empresa, plantillas, costo, guardar correos).
- Resultado: 383 pruebas del motor (11 nuevas) y 55 del frontend, typecheck y build sin errores.

## Iteración 40 · Correo obligatorio y recuperar el PIN con un código (18/10/2026)

- Spec: `40-correo-y-recuperar-pin.md` (S-201..S-209, a validar). Decisión del equipo: correo y celular obligatorios, y recuperación sin depender de una persona.
- El alta pide el correo (único, en minúsculas). Un vecino con sesión lo agrega o cambia y lo verifica con un código de 6 dígitos (vale 10 minutos, 5 intentos, un reenvío por minuto, 5 por hora). Solo un correo verificado sirve para recuperar.
- "Olvidé mi PIN": con correo verificado manda un código; sin él, sigue la cola del equipo (iteración 39). Con el código el vecino elige su PIN nuevo, que también quita el bloqueo. Las respuestas son iguales exista o no el número.
- El envío es un componente intercambiable: sin credenciales imprime el código en la consola del motor; con una cuenta Gmail de Yapa (contraseña de aplicación en variables de entorno) manda correos reales. No hace falta ninguna API key.
- Se probó en el navegador con la demo y se comprobó con mutaciones que las pruebas detectan un código aceptado sin revisar, sin tope de intentos y sin vencimiento.
- Resultado: 412 pruebas del motor (29 nuevas) y 55 del frontend, typecheck y build sin errores.

## Iteración 41 · Entrar con Google (18/10/2026)

- Spec: `41-entrar-con-google.md` (S-210..S-215, a validar). Opcional y complementa al PIN y al código por correo: se activa con el Client ID público de Google Cloud; sin él no aparece nada.
- El vecino entra al menos una vez con su PIN y vincula su cuenta de Google. Después entra con un toque. Se guarda el identificador estable de Google, no el correo. Si no tenía correo verificado, el de Google (ya verificado por Google) pasa a serlo.
- El motor verifica el token con PyJWT: firma RS256 con las llaves públicas de Google, audiencia, emisor, vencimiento y correo verificado. Es una dependencia **opcional**: el resto del motor sigue usando solo la biblioteca estándar.
- Las pruebas firman tokens de verdad con una llave propia (incluidos los ataques típicos: sin firma y confusión de algoritmo) y se comprobó con mutaciones que muerden.
- No se pudo probar el inicio de sesión real con la ventana de Google: falta el Client ID del equipo.
- Resultado: 431 pruebas del motor (19 nuevas) y 55 del frontend, typecheck y build sin errores.

## Iteración 42 · Avisos dentro de la app y por correo (19/10/2026)

- Spec: `42-avisos.md` (S-216..S-221, a validar). Ocho hechos generan un aviso para la persona concerniente: pago verificado, pedido liquidado, zona entregada, entrega fallida, reclamo revisado, devolución pagada, y la solicitud de unión de zonas y su respuesta.
- Dentro de la app: una campana en la barra con el número de avisos sin leer, un panel con la lista (cada aviso lleva a "Mis pedidos" o a "Mi zona"), "Marcar todo como leído" y el interruptor del correo. Se refresca cada minuto y al volver a la pestaña. Se guardan los últimos 50 por vecino.
- Por correo: solo lo importante (dinero, entrega, reclamo, devolución y pedido de unión), solo a un correo verificado y solo si el vecino no lo apagó. Sale en segundo plano y se intenta una sola vez; si el correo falla, la acción termina igual y el aviso queda en la app. Nunca lleva códigos ni PIN.
- Un aviso nunca rompe la acción que lo causa. Los avisos se guardan en la base como el resto del estado.
- Se comprobó con 15 mutaciones que las pruebas detectan un correo sin filtro de verificación o de preferencia, avisos ajenos, el tope y un aviso que rompe la acción. Una mutación sobrevivió al principio y reveló un error de la spec sobre qué pedidos entran en la liquidación; se corrigió.
- Se probó en el navegador (con un proxy local de prueba, ver la spec), incluido el correo y el ancho de 390 px.
- Resultado: 465 pruebas del motor (34 nuevas) y 67 del frontend (12 nuevas), typecheck y build sin errores.

## Iteración 43 · Correos con diseño (19/10/2026)

- Spec: `43-correo-html.md` (S-222..S-225, a validar). Los correos reales llevan dos versiones, texto plano y HTML, armadas desde el mismo texto: encabezado con la marca, título, el código de 6 dígitos en una caja destacada, los párrafos y un pie con la línea para apagar los avisos.
- Se ve como la app (S-227): encabezado claro con el logo de la bolsa y "yapa" en minúsculas, tarjeta de 16 px, botón en píldora terracota. El logo viaja incrustado en el correo (S-226); nada se carga de internet, sin scripts ni seguimiento. Todo texto que viene de datos se escapa (un nombre con etiquetas se ve como texto). Un botón "Abrir Yapa" aparece solo si se define `YAPA_PUBLIC_URL` con `http(s)://`.
- La API, los avisos y la consola del motor no cambian; solo cambia el correo que sale por SMTP.
- Con el dominio `holayapa.app` verificado en Resend, se envió de verdad: llegaron a la bandeja principal el código de verificación y un aviso de unión de zonas. Aprendizaje: `YAPA_SMTP_FROM` va solo con la dirección (el código agrega "Yapa").
- Se comprobó con 7 mutaciones que las pruebas detectan HTML sin escapar, una dirección de botón insegura, la ausencia de la parte HTML y el código sin su caja.
- Primera versión con encabezado oscuro y marca en mayúscula, inventada y distinta de la app; el dueño pidió uniformar y se rehízo con la marca real (se revisó la barra de la app). Mutaciones del ajuste: 7 de 7 detectadas.
- Resultado: 480 pruebas del motor (15 nuevas); el frontend no cambió (67).

## Iteración 44 · Lista para producción (20/10/2026)

- Spec: `44-produccion.md` (S-228..S-235, a validar). En modo servidor (`--base`) no se crean credenciales de demo; el administrador sale de `YAPA_ADMIN_USUARIO` y `YAPA_ADMIN_CLAVE` y, si falta y la base no tiene uno, el motor no arranca. Escuchar fuera de la propia máquina (`--escuchar`) exige `--base`.
- La cookie de sesión lleva `Secure` si `YAPA_PUBLIC_URL` empieza con `https://`. `GET /salud` dice que el motor está vivo sin dar datos. `--estaticos` hace que el motor sirva la web construida (`dist`) con las rutas de la web, sin salirse de la carpeta y con cabeceras de seguridad.
- El servidor atiende cada conexión en su hilo pero el motor ejecuta una petición a la vez (cerrojo global), porque el almacén no es seguro entre hilos.
- Se comprobó con 8 mutaciones: dos sobrevivieron al inicio (el chequeo de `..` y un archivo inexistente con extensión), se ampliaron la spec y las pruebas y las 8 quedaron detectadas. Además se arrancó el motor de verdad en modo servidor y se probaron las negativas y el login.
- Lo que sigue pendiente para abrir Yapa a internet: HTTPS (lo pone un servidor delante), que las solicitudes de unión y de PIN sobrevivan a un reinicio y un límite de intentos de PIN por IP.
- Resultado: 496 pruebas del motor (16 nuevas); el frontend no cambió (67).

## Iteración 45 · Registro por invitación (20/10/2026)

- Spec: `45-registro-por-invitacion.md` (S-236..S-243, a validar). El registro propio existe solo con el enlace de un vecino. Cada vecino tiene un enlace con código al azar (el código de referido `ANA101` se puede adivinar y no sirve como llave), que puede renovar.
- Quien entra con el enlace queda en la zona de quien lo invitó y como su referido (premio de siempre). Se registra con correo (código de 6 dígitos y PIN elegido) o con Google (nombre y correo de Google, sin PIN). Celular y consentimiento obligatorios; el celular no se verifica por SMS.
- Topes: 20 registros por enlace al día y 200 registros a medio hacer. Quien invita y el admin de la zona reciben un aviso en la app.
- Pantalla: `/unete/<código>`, el enlace con WhatsApp, copiar y renovar en Mi cuenta y en Invita y gana.
- Se comprobó con 13 mutaciones (todas detectadas) y con un registro real contra el motor local. Chrome no respondía en esa sesión, así que la pantalla se probó en un DOM simulado.
- Se corrigió un dato que se había dicho mal: las solicitudes de unión y de PIN sí se guardan en la base; al reiniciar solo se pierden las sesiones.
- Resultado: 518 pruebas del motor (22 nuevas) y 77 del frontend (10 nuevas), typecheck y build sin errores.

## Iteración 46 · Entrar con correo o celular (21/10/2026)

- Spec: `46-entrar-con-correo-o-celular.md` (S-244..S-248, a validar). El vecino entra con su correo, su celular o su número de cliente más el PIN; lo que no existe da el mismo error que una clave mala. "Olvidé mi PIN" acepta lo mismo. Quien nació con Google no tiene PIN: entra con Google y, si quiere, crea su PIN desde Mi cuenta (`POST /api/pin/crear`, sin PIN actual).
- Salió de la prueba del dueño con el registro por Google: "para iniciar sesión manualmente te tienes que saber tu número de cliente, y además te pide contraseña si te vinculaste con Google".
- Se comprobó con 8 mutaciones (todas detectadas, tras reforzar una prueba) y en producción con el vecino de prueba.
- Se corrigió un fallo viejo: los campos del código y del PIN nuevo dejaban escribir letras por un `/D/g` mal escrito.
- Resultado: 532 pruebas del motor (14 nuevas) y 85 del frontend (2 nuevas).

## Iteración 47 · Pulido de lanzamiento (21/10/2026)

- Spec: `47-pulido-de-lanzamiento.md` (S-249..S-252, a validar). Revisión de la web contra una guía de interfaz: la parte mecánica estaba bien; lo flojo era el peso de las imágenes (3,6 MB, ahora 261 KB en WebP), el favicon que faltaba (404 en cada visita), la ausencia de vista previa al compartir el enlace por WhatsApp (ahora el enlace de invitación se ve con el nombre de quien invita y la zona) y que los archivos con huella se guardaban solo una hora (ahora un año).
- Página `/privacidad` en borrador y enlazada desde el registro: el equipo debe revisar el texto, sobre todo el medio de contacto y los plazos.
- La invitación pone el cursor en el primer campo al cambiar de paso y ajusta el título de la pestaña.
- Se comprobó con 5 mutaciones (todas detectadas).
- Resultado: 537 pruebas del motor (5 nuevas) y 92 del frontend (7 nuevas), tipos y compilación sin errores.

## Iteración 48 · Datos de demostración y cuentas de depuración (21/10/2026)

- Spec: `48-demostracion-y-depuracion.md` (S-253..S-258, a validar). La web desplegada es la demostración para el profesor, así que la base real se siembra con la semana de demostración corrida a la semana actual (`--sembrar-demo`): la anterior entregada y liquidada, y la actual abierta con pedidos. La base guarda su propio "ahora" (miércoles 10:00) para que la semana siempre esté abierta; lo de seguridad (bloqueo, sesiones) usa la hora real.
- Cuentas de prueba con claves propias (fuera del repositorio): admin de zona (Ana y Marta), vecina (Carmen), admin de Yapa y un admin global de depuración (`debug-global`) que puede "ver como" cualquier vecino o admin de zona, con aviso fijo, botón para volver, sin poder cambiar PIN, correo ni Google, y con registro de cada uso.
- Se comprobó con 9 mutaciones (8 detectadas y una equivalente) y en producción.
- Se discutió y quedó anotado como iteración 49: registro abierto con ubicación (el navegador pide permiso, solo zonas a menos de 300 m) y aprobación del admin de zona, con la invitación como atajo que da beneficios a quien invita; reemplaza el supuesto S-236.
- Resultado: 557 pruebas del motor (20 nuevas) y 93 del frontend (1 nueva).

## Iteración 50 · Endurecimiento antes de abrir (21/10/2026)

- Spec: `50-endurecimiento-antes-de-abrir.md` (S-259..S-262, a validar). Sale de la revisión de seguridad de la rama `carlos/motor-y-roles` antes de abrir `holayapa.app`. La 49 queda reservada para el registro abierto con ubicación.
- Cualquiera, sin sesión, podía dejar un archivo en la carpeta de fotos mandándolo a una ruta que no usa fotos; ahora solo se guardan en el reclamo, la bolsa, la entrega y la entrega fallida, después de sesión y CSRF, y solo si el contenido es una imagen (la extensión sale del contenido).
- El cuerpo se leía sin tope dentro del cerrojo: ahora el servidor rechaza más de 9 MB sin leerlos (413) y lee el cuerpo antes del cerrojo.
- Una credencial nueva (cambiar, recuperar, crear o reiniciar el PIN) cierra las demás sesiones de esa persona, en la API y en la web HTML.
- "Ver como" ya no puede pedir la devolución del saldo, cancelar pedidos ni ceder una zona.
- El CI estaba en `api/.github` y GitHub nunca lo corría; pasa a la raíz, instala PyJWT (las pruebas de Google ya no se saltan) y suma tipos, pruebas y compilación de la web.
- La prueba de "crear el PIN" simulaba la entrada con Google borrando la credencial después del login; ahora entra con Google de verdad (las aserciones no cambian).
- Resultado: 571 pruebas del motor (14 nuevas, sin pruebas saltadas) y 93 del frontend.

## Iteración 51 · Cierre de huecos para pasar a main (21/10/2026)

- Spec: `51-cierre-de-huecos-para-main.md` (S-263..S-269, a validar). Cierra lo que la iteración 50 dejó anotado, para pasar la rama a `main`.
- Límites por dirección (la real detrás de Caddy): 30 entradas fallidas en 15 minutos y 10 correos con código por hora; 10 códigos por hora por enlace de invitación. Antes se podía probar un PIN común contra todas las cuentas y mandar cientos de códigos desde el Gmail de Yapa.
- `/api/zonas` ya no muestra el contacto de recepción ni el admin a quien no es del equipo, y a quien no entró le da la ubicación aproximada.
- En el servidor sin SMTP los códigos ya no van a la consola (ni a los registros): no sale el correo y se avisa al arrancar.
- Toda respuesta lleva CSP, `nosniff`, `X-Frame-Options` y, con https, HSTS. Las sesiones vencidas se borran; "volver" de "ver como" no reabre una sesión cuya clave cambió.
- Web: "semana del 28 sep" en vez de `2026-W40` para el vecino, el ingreso dice que vale el correo o el celular, la insignia de ahorro dice cuándo se vio el precio, el panel del equipo y el mapa se bajan solo al abrirse (639 KB → 447 KB), y una respuesta que no es JSON ya no rompe la pantalla. `npm audit fix` en las dependencias de desarrollo.
- Dos pruebas de la iteración 45 cambian de escenario (no de aserciones) porque los nuevos topes no dejan mandar 20 o 200 códigos en minutos desde un solo enlace.
- Se comprobó en el navegador con la web construida y la CSP real (portada, mapa y centro de operaciones sin errores).
- Resultado: 584 pruebas del motor (13 nuevas, ninguna saltada) y 99 del frontend (6 nuevas); tipos, compilación sin aviso de tamaño y 0 vulnerabilidades.

## Iteración 52 · Despliegue automático (21/10/2026)

- Spec: `52-despliegue-automatico.md` (S-270..S-276, a validar). Kalos propuso un runner de GitHub en la VPS. Se comprobó que **sí arranca** en Windows Server 2012 R2 y que Node 20 corre; Node 24 no, así que el trabajo de la VPS usa solo comandos de PowerShell.
- Cada subida corre las pruebas y arma el paquete en los servidores de GitHub; **solo una subida a `main` despliega**, en el runner de la VPS: baja el paquete con un token temporal del trabajo (no queda ninguna credencial de GitHub en la VPS), respalda la base, guarda la versión anterior, pone la nueva y **vuelve a la anterior si el motor nuevo no responde `/salud` en 40 segundos**.
- El flujo se combinó con el de Kalos (`tests`, trabajos `motor` y `web`) en el mismo `ci.yml`. Los scripts de la VPS están en `deploy/vps/` como copia de referencia.
- Se probó: validador de flujos, pruebas en GitHub, despliegue normal, marcha atrás con un motor roto, paquetes inválidos y la bajada real desde GitHub. El trayecto completo (DA-H) se probó el 21/10: se registró el runner (token generado por Kalos) y un push a `main` desplegó solo en 12 segundos, con la etiqueta del commit en el pie de la web como prueba.
- Resultado: 584 pruebas del motor y 99 de la web en verde sobre el árbol integrado con lo de Kalos.

## Iteración 53 · La sesión no se pierde por cookies de otros servicios (22/10/2026)

- Spec: `53-cookies-de-otros-sitios.md` (S-277, a validar). En producción, después de verse el botón de Google, cada recarga sacaba al usuario: la cookie `g_state` de Google trae un JSON y `SimpleCookie` dejaba de leer la cabecera antes de llegar a la cookie de Yapa.
- Ahora la API y la web HTML buscan su cookie por nombre y las ajenas se ignoran. Se comprobó con `curl` contra holayapa.app antes del arreglo (401 con `g_state` antes, 200 sin ella).
- Resultado: 588 pruebas del motor (4 nuevas, ninguna saltada).

## Iteración 54 · Cuentas para proveedores y transportistas (28/10/2026)

- Spec: `54-proveedores-y-transportistas.md`, con los supuestos S-278..S-288, a validar por el equipo (el admin crea las cuentas, el transportista solo entrega y no ve datos de vecinos, el proveedor propone y el admin publica, al aprobar se reemplazan solo sus productos).
- Pruebas antes del código: `docs/evidencia/desarrollo/54-proveedores-transportistas-rojo.txt`.
- Implementación: módulos `partners.py` (cuentas) y `supplier_offers.py` (lista propuesta y pedido consolidado); `fulfillment.check_courier` deja entregar al transportista activo; la API suma los tipos de sesión `transportista` y `proveedor` con rutas propias. En la web, el acceso del equipo elige Equipo · Reparto · Proveedor y cada uno ve su pantalla.
- Resultado: 607 pruebas del motor (37 nuevas) y 103 del frontend en verde; typecheck y build sin errores (`54-proveedores-transportistas-verde.txt`).

## Iteración 55 · Cuentas para compras, armado, atención y portería (06/11/2026)

- Spec: `55-personal-por-rol.md`, con los supuestos S-289..S-294 a validar por el equipo:
  - el admin crea las cuatro cuentas;
  - cada rol hace solo su trabajo, sin ver montos que no le tocan;
  - la portería pertenece a una zona;
  - confirman la recepción la portería o el admin de zona.
- Pruebas antes del código: `docs/evidencia/desarrollo/55-personal-por-rol-rojo.txt`.
- Implementación en el motor:
  - `partners.create_staff` y `partners.can`;
  - `fulfillment.check_role` reemplaza a `check_staff` en el armado, el colchón y los reclamos;
  - `customers` deja que atención atienda los PIN;
  - el módulo nuevo `reception.py` y el aviso `notices.in_building`.
- Implementación en la API: las rutas aceptan una tupla de roles; se suman `/api/compras*`, `/api/porteria*` y `/api/zona/recepcion*`.
- Implementación en la web:
  - un selector con siete roles en el acceso del equipo;
  - el panel del equipo con secciones según el rol, incluidas "Compra de la semana" y "Pedidos de PIN";
  - la pantalla de portería;
  - la tarjeta de recepción en el panel del admin de zona;
  - "Cuentas del equipo" para crear los seis tipos de cuenta.
- Hallazgos al probar:
  - la lista de armado mostraba los pagos al armador;
  - con el ciclo abierto y sin pedidos, compras decía "Cerrado".
  - Los dos se especificaron y se probaron antes de corregirlos.
- Resultado: 638 pruebas del motor (31 nuevas) y 110 del frontend (7 nuevas) en verde; typecheck y build sin errores (`55-personal-por-rol-verde.txt`). La demo se probó en el navegador: compras con la W39, y la portería confirmando Los Álamos con el aviso al vecino 101.

## Acceso en páginas propias (06/11/2026)

- Solo cambia la web; el motor no se tocó y no hay reglas ni supuestos nuevos.
- El modal de acceso se reemplazó por páginas completas:
  - `/entrar` para los vecinos;
  - `/equipo` para el personal, y `/equipo?rol=porteria` llega con ese rol ya elegido;
  - "Mi cuenta" (`#cuenta`) como una vista más de la tienda.
- Después de entrar se vuelve a donde se estaba (canasta, pedidos, zona) y Atrás no reabre el acceso. `volver` solo acepta vistas de la tienda (`src/utils/authRoutes.ts`), así un link no puede mandar a otro sitio.
- Pruebas: `src/utils/authRoutes.test.ts`. Revisado en el navegador en escritorio y en celular.

## Iteración 56 · Compra real, dañados, rótulos, bloqueo del despacho e incidencias (09/11/2026)

- Spec: `56-compra-real-y-armado.md` (S-295..S-300). Kalos decidió el 09/11 cómo tocan el dinero el faltante del proveedor y el dañado al armar: primero el colchón y, si no alcanza, se descuenta a los últimos pedidos registrados y vuelve como saldo en la liquidación.
- Pruebas antes del código (`56-57-motor-rojo.txt`, `56-57-web-rojo.txt`).
- El bloqueo del despacho (S-299) obligó a que las pruebas que entregan registren la compra en su preparación. El chequeo va **al final** de la entrega, así que ningún error que ya se verificaba cambió.
- Implementación: módulos `purchase.py` e `incidents.py`; `bag_labels` y el bloqueo en `fulfillment.py`; `close_cycle` suma los faltantes que no cubrió el colchón. Web: "Lo que llegó" en Compras, rótulos y "Algo llegó dañado" en Armado, y la sección Incidencias para atención.
- Queda fuera "ver la app como un vecino desde atención" (decisión de privacidad).

## Iteración 57 · 25 % del ahorro y retiro del consentimiento (09/11/2026)

- Spec: `57-ahorro-retenido-y-retiro-de-datos.md` (S-301..S-304). Cierra las decisiones urgentes 49 (Yapa retiene el 25 %) y 67 (retiro del consentimiento: se anonimiza).
- El 25 % se aplica en la liquidación operativa (`close_cycle`); `settle_cycle` sigue en 0 % como cálculo puro, así las specs anteriores conservan sus ejemplos. Solo cambió la semana completa (AU-C): el vecino 801 termina con S/ 4,62 en vez de S/ 5,38, y la conciliación sigue en 0.
- La portada dice el reparto: 75 % al vecino y 25 % para la operación (Ley 29571).
- Resultado: 660 pruebas del motor (22 nuevas) y 117 del frontend (7 nuevas) en verde; typecheck y build sin errores (`56-57-motor-verde.txt`, `56-57-web-verde.txt`).

## Iteración 58 · Logística propia (09/11/2026)

- Spec: `58-logistica-propia.md` (S-305..S-309). Kalos decidió, con fuentes (Interbank, Yape, BCRP, Makro, EMMSA y fletes de Lima), cobrar por Plin negocios sin comisión y que Yapa contrate y pague el flete y maneje todo el reparto.
- Pruebas antes del código (`58-logistica-rojo.txt`, `58-logistica-web-rojo.txt`).
- Implementación: módulo `logistics.py` (flete, margen real, salida a reparto y seguimiento). Web: el vecino ve 7 pasos de su pedido y a qué Plin pagar; el transportista marca "Salí hacia esta zona"; compras registra el flete; métricas muestra el margen real.
- Hallazgo: el margen real llega a 0 con 24 pedidos por semana si el flete cuesta S/ 120, con 35 si cuesta S/ 180 y con 60 si cuesta S/ 320. La demo (9 pedidos) pierde S/ 9,57 por pedido.
- Resultado: 671 pruebas del motor (11 nuevas) y 119 del frontend (2 nuevas) en verde; typecheck y build sin errores.
- Ajuste del mismo día: Yapa es un proyecto académico sin empresa constituida, así que el Plin de cobro es una **cuenta simulada** por defecto, también en el servidor (S-305). El flete y los montos que se registran también son de simulación.

## Despliegue en AWS (09/11/2026)

- Yapa pasa de la VPS con runner propio (iteración 52, desconectado) a **AWS Lightsail** en la cuenta estudiantil: un servidor nano en Ohio (`us-east-2`, la única región que permite la cuenta) por unos USD 5 al mes con la IP fija incluida. Los USD 100 de crédito alcanzan para unos 20 meses.
- Caddy da HTTPS con Let's Encrypt para `holayapa.app` y `www`. Los subdominios `lab*` siguen apuntando a la máquina del laboratorio.
- GitHub sigue corriendo las pruebas. El despliegue ahora sube el paquete por SSH y `deploy/aws/desplegar.sh` respalda la base, cambia la versión y vuelve atrás si `/salud` no responde. A diferencia del runner de la VPS, el servicio arranca solo si la máquina se reinicia.
- La cuenta estudiantil no deja que AWS cree llaves SSH ni usar EC2 fuera de Ohio: la llave se genera en la máquina de quien despliega y se importa la parte pública (`deploy/aws/README.md`).
- Medido en el servidor: el motor usa unos 32 MB de RAM.

