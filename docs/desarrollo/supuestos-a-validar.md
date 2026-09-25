# Supuestos para que el equipo valide

Estas son las decisiones que se tomaron **por defecto** para poder especificar y programar. Ninguna es definitiva: si Kalos o Aaron no están de acuerdo con alguna, se cambia primero aquí y en la spec, y después en las pruebas y el código (así funciona SDD).

Cómo usar esta lista: marca ✅ si estás de acuerdo o escribe tu propuesta en la columna "Otra idea". Entre paréntesis va el código del supuesto, para buscarlo en las specs.

---

## ⚠️ Decisiones urgentes (salieron al programar)

1. **¿Nos alcanza el margen?** En el escenario base, cada pedido deja **S/ 5.64** antes de costos operativos (`08-metricas-piloto.md`, MT-A). Pero armar, cobrar y atender cuesta entre **S/ 3.22 y S/ 12.69 por pedido** (`docs/analisis/08_validacion_economica.md`). Con Yape Empresa (2.95 %) y armado pagado, el margen puede quedar **negativo**. Hay que decidir:
   - si subimos la comisión;
   - si usamos Plin negocios (0 %) en vez de Yape Empresa;
   - qué costo por pedido se descuenta en las métricas.
2. **Zonas lejanas.** Una zona con parada de S/ 100 y 8 pedidos pierde S/ 1.86 por pedido (MT-B), porque el envío cobrado tiene tope de S/ 5. **El mínimo de 8 pedidos solo alcanza si la parada cuesta hasta S/ 40.** ¿El mínimo debería depender del costo de la parada?
3. **Portería que no recibe.** *Implementado con la recomendación por defecto* (`16-entrega-fallida-cierre.md`): sin reintento, al vecino le vuelve todo menos el envío real (como saldo) y los frescos son merma de Yapa. **Falta que el equipo lo confirme** o proponga otra cosa (¿reintento el domingo?, ¿dejar las bolsas con el admin de la zona?).
5. **Crecer no mejora el margen (simulador, iteración 14).** Como todo el ahorro por volumen vuelve al cliente y la comisión es un % del precio final, **Yapa gana menos por pedido mientras más compra el grupo**: de S/ 3.31 con 8 pedidos a S/ 2.52 con 30 (optimista). ¿Yapa se queda con parte del ahorro, cobra un fee fijo o solo baja costos? Ver `14-simulador-escenarios.md`. **Dato:** reteniendo el 25 % del ahorro por volumen, el peor escenario queda en equilibrio (−S/ 0.06) y el vecino sigue ahorrando S/ 10.39 por pedido (`15-reparto-ahorro.md`).
4. **Reclamo por un artículo dañado:** ¿la plata vuelve a saldo (como está hoy) o directo al Yape/Plin?

## A. Dinero y pagos (los más importantes)

| # | Pregunta | Se decidió por defecto | Kalos | Aaron | Otra idea |
|---|---|---|---|---|---|
| 1 | ¿Cuánto cobramos de comisión? | 12 % en frescos y 9 % en limpieza (S-07). Los datos de precios reales lo respaldan en frescos. | | | |
| 2 | ¿Cuánto es el envío máximo que se cobra? | S/ 5 por pedido; lo que sobre vuelve como saldo (S-05). | | | |
| 3 | ¿Cuántos pedidos necesita una zona para que el camión vaya? | 8 pedidos con pago confirmado, y las zonas unidas suman (S-06). | | | |
| 4 | ¿Cuánto es lo mínimo que puede pedir una persona? | S/ 50, sin redondear (S-04). | | | |
| 5 | ¿Un pedido se puede pagar mitad con saldo y mitad con Yape? | Sí, con un pago de saldo y uno de Yape/Plin (S-13). | | | |
| 6 | Si el saldo alcanza para todo, ¿hace falta código de Yape? | No, y se confirma al instante (S-14). | | | |
| 7 | ¿En cuánto tiempo devolvemos plata al Yape/Plin del cliente? | Hasta 30 días; el administrador registra el pago con su código (S-15). | | | |
| 8 | Si alguien cancela, ¿a dónde vuelve su plata? | El cliente elige: a su Yape/Plin o a su saldo. Por defecto, a su Yape/Plin (S-19). | | | |
| 9 | Si alguien baja su pedido, ¿a dónde vuelve la diferencia? | A su saldo, que puede pedir de vuelta cuando quiera (S-22). | | | |
| 10 | Si alguien sube su pedido, ¿qué pasa? | Paga la diferencia con un código nuevo, y el pedido espera confirmación otra vez (S-23). | | | |
| 11 | Si el administrador no confirmó el Yape y el cliente cancela, ¿se le devuelve? | No automáticamente: atención al cliente revisa si la plata llegó (S-20). | | | |
| 12 | Redondeos | Siempre a favor del cliente, al céntimo (S-09, Ley 29571). | | | |

## B. Tiempos del ciclo

| # | Pregunta | Se decidió por defecto | Kalos | Aaron | Otra idea |
|---|---|---|---|---|---|
| 13 | ¿Hasta qué hora se reciben pedidos? | Hasta antes del miércoles a las 20:00, hora de Lima; a las 20:00 en punto ya está cerrado (S-02). | | | |
| 14 | ¿Hasta cuándo se puede cancelar o cambiar el pedido? | Hasta el mismo cierre del miércoles a las 20:00, no hasta la hora de compra (S-18). | | | |
| 15 | ¿Cuántos pedidos por persona por semana? | Uno activo; si lo cancela, puede hacer otro (S-03). | | | |
| 16 | ¿Quién elige la ventana de entrega? | Yapa la asigna a cada zona, porque recibe la portería (S-10). | | | |

## C. Zonas y vecinos

| # | Pregunta | Se decidió por defecto | Kalos | Aaron | Otra idea |
|---|---|---|---|---|---|
| 17 | ¿Qué tan lejos del punto de recepción puede vivir un vecino? | 300 m, unas 3 cuadras (S-25). | | | |
| 18 | ¿Qué tan cerca deben estar dos zonas para unirse? | 500 m entre todas las zonas del grupo, para que no se forme una cadena larga (S-26). | | | |
| 19 | ¿Cuándo empieza a recibir pedidos una zona nueva? | Cuando el admin registra quién recibe: portería, encargado o él mismo (S-28). | | | |
| 20 | ¿Una persona puede ser admin de varias zonas? | No, de una sola, y vive en ella (S-29). | | | |
| 21 | ¿Un vecino puede cambiarse de zona en cualquier momento? | No si tiene un pedido en curso (S-30). | | | |
| 22 | ¿Cuándo se pueden unir o separar zonas? | Solo con el ciclo abierto (S-31). | | | |
| 23 | ¿Cuánto cuesta la parada de una zona? | S/ 40 en el piloto; lo fija Yapa (S-32). | | | |

## D. Catálogo y proveedores

| # | Pregunta | Se decidió por defecto | Kalos | Aaron | Otra idea |
|---|---|---|---|---|---|
| 24 | ¿Se pueden cambiar los precios a mitad de semana? | No: el catálogo se publica antes del lunes y queda fijo. Solo se puede desactivar un producto (S-33, S-36). | | | |
| 25 | ¿El precio puede subir si se compra más volumen? | Nunca: los tramos solo bajan el precio (S-34). | | | |
| 26 | ¿Cuánto se puede pedir por línea? | Hasta 10 kg o 6 unidades; frescos en pasos de 1 kg (ajo de 250 g) (S-08). | | | |
| 27 | ¿Los precios del piloto son reales? | Son de ejemplo, sacados del mayorista del 23–24/09. Hay que cambiarlos por la lista real del proveedor aliado (S-12). | | | |

## E2. Iteraciones 6 a 8 (catálogo, armado, reclamos, métricas)

| # | Pregunta | Se decidió por defecto | Kalos | Aaron | Otra idea |
|---|---|---|---|---|---|
| 28 | Si Yapa desactiva un producto a mitad de semana, ¿el vecino que ya lo pidió puede editar su pedido? | Sí, puede mantener o bajar esa cantidad, pero no subirla (S-39). | | | |
| 29 | ¿Quién arma y entrega? | Por ahora, los administradores; no hay rol separado de armador o repartidor (S-40). | | | |
| 30 | ¿Cómo se prueba que se armó bien? | Una foto por bolsa, al terminar de armarla (S-41). | | | |
| 31 | ¿Cómo se prueba que se entregó? | Foto de la entrega y nombre de quien recibe en portería; una entrega por zona y por semana (S-42). | | | |
| 32 | ¿Hasta cuándo se puede reclamar un artículo? | Hasta 24 horas después de la entrega (S-43). | | | |
| 33 | ¿Qué debe traer un reclamo? | Motivo (faltó o llegó dañado), foto y cantidad (S-44). | | | |
| 34 | Si se aprueba un reclamo, ¿cuánto se devuelve y a dónde? | El precio final del artículo, redondeado a favor del cliente, como saldo (S-45). | | | |
| 35 | ¿Qué se guarda como colchón de reposición? | Solo limpieza (no perecible), con un tope de S/ 500 (S-46). | | | |
| 36 | ¿Cómo medimos la recompra? | De los que compran por primera vez en una semana, cuántos vuelven a comprar 3 semanas después. Meta: 50 % (S-48). | | | |
| 37 | ¿Qué cuenta en el margen por pedido? | Lo cobrado − reclamos − costo del proveedor − parada repartida. **No incluye costos operativos** (S-49, ver urgentes). | | | |

## E3. Web y acceso (iteraciones 9 y 10)

| # | Pregunta | Se decidió por defecto | Kalos | Aaron | Otra idea |
|---|---|---|---|---|---|
| 38 | ¿Cómo entra un vecino? | Número de cliente + PIN de 6 dígitos, que no puede ser fácil como 123456 o 111111 (S-64, S-66). | | | |
| 39 | ¿Quién le da el PIN inicial? | El administrador, al darlo de alta (por ejemplo, por WhatsApp). Después el vecino lo puede cambiar (S-65). | | | |
| 40 | ¿Qué pasa si alguien falla el PIN varias veces? | Con 5 intentos fallidos se bloquea 15 minutos (S-68). | | | |
| 41 | ¿Cuánto dura la sesión? | 8 horas (S-69). | | | |

## E4. Pantallas de operación (iteración 12)

| # | Pregunta | Se decidió por defecto | Kalos | Aaron | Otra idea |
|---|---|---|---|---|---|
| 42 | ¿Cómo se guardan las fotos de la bolsa, la entrega y el reclamo? | Por ahora, como texto con la ruta o el enlace del archivo; todavía no se suben archivos (S-72). | | | |
| 43 | ¿Quién activa la zona, la une con otra o pasa el rol? | El vecino que es admin de esa zona, desde su cuenta; el administrador de Yapa no lo hace (S-73). | | | |
| 44 | ¿Cómo registra el vecino su ubicación para crear o unirse a una zona? | Desde "Mi cuenta", con latitud y longitud (S-109, iteración 18). Falta decidir si se buscará por dirección. | | | |
| 45 | ¿Qué pasa con las zonas del piloto que no tienen ubicación? | Ya tienen coordenadas de ejemplo (S-112, iteración 18). Una zona sin ubicación sigue sin recibir vecinos (S-75). | | | |
| 46 | ¿Qué muestra el tablero de métricas? | Margen por pedido, ahorro entregado y recompra en la semana 4, para un ciclo liquidado (S-78). | | | |

## E5. Iteraciones 11 a 18 (persistencia, dinero, entrega fallida, robustez)

| # | Pregunta | Se decidió por defecto | Kalos | Aaron | Otra idea |
|---|---|---|---|---|---|
| 47 | ¿Qué pasa si el servidor se reinicia? | Se guarda todo en una base SQLite después de cada operación; solo hay que volver a entrar (S-90, S-91). | | | |
| 48 | ¿Qué costos operativos usamos para decidir? | Dos escenarios documentados: optimista (Plin 0 %, proveedor entrega) y pesimista (Yape Empresa 2.95 %, flete de compra) (S-95..S-97). **Hay que elegir cuál se parece a la realidad.** | | | |
| 49 | ¿Yapa se queda con parte del ahorro por volumen? | Hoy 0 % (todo vuelve al cliente). El simulador muestra que con 25 % se deja de perder (S-100). **Decisión pendiente.** | | | |
| 50 | Si la portería no recibe, ¿se reintenta? | No en el piloto (S-102). | | | |
| 51 | Si la portería no recibe, ¿cuánto se devuelve? | Todo menos el envío real de la zona, como saldo (S-103). | | | |
| 52 | Lo que se compró para una zona fallida, ¿cuenta para los descuentos por volumen? | Sí, porque ya se compró; los frescos son merma de Yapa (S-104, S-107). | | | |
| 53 | ¿Un admin de zona puede mudarse a otra zona? | Solo después de pasar el rol a otro vecino (S-110). | | | |
| 54 | ¿Se puede rechazar o retirar una solicitud para unir zonas? | Sí (S-111). | | | |

## E6. Iteraciones 19 a 21 (conciliación, catálogo desde la web, armado y colchón)

| # | Pregunta | Se decidió por defecto | Kalos | Aaron | Otra idea |
|---|---|---|---|---|---|
| 55 | ¿Cuándo cuenta un Yape/Plin como dinero recibido? | Cuando el admin lo verifica con su código. Lo pagado con saldo no es dinero nuevo (S-113, S-114). | | | |
| 56 | ¿Cómo sabemos que no se pierde ni se inventa plata? | La pantalla de conciliación debe dar diferencia 0: lo recibido = pedidos sin liquidar + lo que se quedó Yapa + lo que debemos + lo ya devuelto (S-115). | | | |
| 57 | ¿Cómo carga el admin la lista semanal del proveedor? | Pegándola desde Excel o Sheets, separada por comas y con punto decimal. La pantalla ya trae la lista de la semana para solo cambiar precios (S-116, S-117). | | | |
| 58 | ¿Se puede retirar un producto en una semana sin catálogo propio? | Sí: se guarda una copia del catálogo base solo para esa semana (S-118). | | | |
| 59 | Si falta algo después de entregar la zona, ¿se puede mandar otra bolsa? | No: va por reclamo y se devuelve como saldo (S-121). | | | |
| 60 | Cuando se repone con el colchón, ¿se anota a qué pedido fue? | Sí, y no se repone más de lo que el vecino pidió (S-122). Falta decidir si se descuenta del acuerdo con el proveedor. | | | |
| 61 | Si un proveedor deja de ser aliado a mitad de semana, ¿qué pasa con sus productos? | Se mantienen esa semana (se respeta el precio que vio el vecino). El admin puede desactivarlos. Desde la semana siguiente ya no se publican (S-124). | | | |

## E. Técnicos (no requieren decisión de negocio, solo revisión)

S-38 (orden de errores del catálogo), S-47 y S-50..S-52 (detalles de métricas), S-62/S-63 (datos en memoria, hora fija para la demo), S-67 (hash del PIN), S-70/S-71 (contraseña de admin, protección de formularios), S-11 (orden de los errores), S-16/S-17 (saldo en pedidos no atendidos, liquidar una sola vez), S-21 (un código de operación no se reutiliza), S-24 (no se genera saldo con pagos sin confirmar: evita fraude), S-27 (distancia en línea recta), S-35 (stock por semana), S-37 (catálogo base si no se publicó uno), S-76/S-77 (formato de los datos y ciclo en las pantallas web), S-79/S-80 (listas de reclamos del vecino y del administrador).

---

## Lo que **no** es un supuesto sino una tarea de campo

- **Precios del mercado de barrio.** Es el competidor real en frescos y no está medido. Ver `kit-validacion-campo.md`.
- **Precio del galón de Exlim** y de otras marcas emergentes de limpieza.
- **Confirmar con un proveedor aliado real** que aceptaría respetar su lista semanal y declarar su stock máximo.
