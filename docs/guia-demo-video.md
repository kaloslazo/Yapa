# Guía para el video: cada módulo con datos

La demo arranca con la semana poblada: 4 edificios con pedidos (3 llegan al mínimo y Las Palmeras se suma a Lince), pagos por verificar, la lista del proveedor esperando aprobación, una incidencia abierta, un pedido de PIN y 8 semanas de historia para la predicción. Todo vive en memoria: Ctrl+C y se vuelve a empezar.

## Levantar

```bash
scripts/demo.sh                          # motor en 8010 y tienda en 5173 (lee .env con la clave de Groq)
MOTOR=8040 WEB=5180 scripts/demo.sh      # si esos puertos están ocupados
```

En otra terminal, cada paso mueve el reloj y hace lo que cada rol haría ese día:

```bash
YAPA_API=http://127.0.0.1:8040 scripts/semana.sh miercoles   # jueves, viernes, sabado, domingo, siguiente o todo
```

El reloj también se mueve a mano en `/api/demo/reloj`.

## Cuentas

| Rol | Dónde | Usuario | Clave |
|---|---|---|---|
| Vecina y admin de Los Álamos | `/entrar` | 101 (Ana) | PIN 482915 |
| Vecina | `/entrar` | 105 (Carmen) | PIN 739104 |
| Admin | `/equipo?rol=admin` | admin-yapa | yapa-admin-2026 |
| Compras | `/equipo?rol=compras` | compras-demo | compras-yapa-2026 |
| Armado | `/equipo?rol=armador` | armado-demo | armado-yapa-2026 |
| Atención | `/equipo?rol=atencion` | atencion-demo | atencion-yapa-2026 |
| Reparto | `/equipo?rol=transportista` | reparto-demo | reparto-yapa-2026 |
| Portería | `/equipo?rol=porteria` | porteria-demo | porteria-yapa-2026 |
| Proveedor | `/equipo?rol=proveedor` | frescos-demo | frescos-yapa-2026 |

## Qué mostrar, en orden

| Momento | Rol | Qué se ve | IA o algoritmo |
|---|---|---|---|
| Miércoles (al arrancar) | Vecina | Tienda, "Arma mi canasta con IA", avance del grupo, pedido y código de pago | Groq (Arma mi canasta) |
| Miércoles | Admin | Resumen: 7 pagos por verificar y qué grupos llegan al mínimo | — |
| Miércoles | Compras | Compra de la semana: "Lo que se viene esta semana" con estimado, lo ya pedido e historia de 8 semanas | Regresión lineal (iteración 68) |
| Miércoles | Proveedor | "Leer cotización con IA": pegar un mensaje o subir la foto de la lista y ver el borrador lleno | Visión de Groq (iteración 69) |
| Miércoles | Admin | Propuestas del proveedor: la lista de frescos con dos precios más bajos, para aprobar | — |
| Miércoles | Atención | Incidencia abierta de la semana pasada y el pedido de PIN de Rosa (114); sugerencia de IA | Groq (atención) |
| `semana.sh miercoles` | — | Ana pide y el admin verifica: los 3 grupos llegan | — |
| `semana.sh jueves` | Compras / Proveedor | Compra registrada y flete; el proveedor ve lo que Yapa le compra | — |
| `semana.sh viernes` | Armado | 29 bolsas con foto; "Revisar una bolsa con el detector" | YOLO (detector de productos) |
| Viernes (antes del sábado) | Reparto | Mapa real con 4 paradas, ruta sugerida, "Abrir ruta en Google Maps" y "Usar este orden" | Vecino más cercano + 2-opt |
| `semana.sh sabado` | Reparto / Portería | Entregas con foto; la portería confirma y cada vecino recibe el aviso | — |
| `semana.sh domingo` | Vecina / Atención / Admin | Reclamo con foto, liquidación ("te devolvemos"), conciliación en 0 y métricas | — |
| `semana.sh siguiente` | Vecina / Compras | Semana nueva usando el saldo; en Compras, eligiendo la semana anterior, la predicción muestra cuánto se equivocó | Regresión (error medio) |

En cualquier pantalla, "¿Te ayudamos?" abre la ayuda con las preguntas frecuentes.
