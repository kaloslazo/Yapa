# 07 · Precios por grupo, zonas, mínimos y proveedor

Propuestas para los problemas más graves del modelo (conversación del 23/09/2026). Los números son **supuestos de ejemplo** y hay que validarlos con precios reales.

## Estado al 24/09/2026

| Punto | Estado |
|---|---|
| 1. Todos pagan el máximo y el ahorro se liquida al final ("te devolvemos") | ✅ Aprobado por Carlos y Kalos · Aaron pendiente |
| 2. Zonas creadas por vecinos (punto + radio, unión de zonas) | 👍 Le gusta a Carlos; falta cuidar que sea flexible y a la vez estricto |
| 3–4. Envío compartido por zona + comisión | 👍 En investigación (costos reales) |
| 5. Prevención de faltantes | ✅ Carlos |
| 6. Entrega en portería | ✅ Carlos + **foto del contenido de cada bolsa al terminar de armarla** (evidencia si algo se pierde en portería o en manos del cliente), además de foto y registro de la entrega |
| 7. Productos | ✅ Piloto solo no perecibles. **Fase 2: perecibles** (más retorno, más riesgo) |
| 8. Sobrantes | ✅ Colchón de reposición con tope de monto |

**Ajustes de Carlos (24/09/2026):**

- **Piloto geográfico concentrado:** se empieza solo donde hay más demanda y se eligen zonas cercanas entre sí, para que la camioneta no cruce de punta a punta. Propuesta: una lista de espera previa que muestre dónde se agrupa la gente.
- **Zonas unidas = dos paradas cortas**, no una. Cada zona recibe lo suyo en su punto. Hay un radio máximo por zona y una distancia máxima entre zonas unidas.
- **Catálogo por fases, corto y con marca única por producto:**
  - Fase 1: limpieza en envase grande (detergente líquido, lavavajillas, limpiatodo) y papel higiénico por volumen.
  - Fase 2: frescos resistentes al tiempo y a los golpes.
  - Fase 3: frutas.
  - En frescos, solo los más pedidos (papa amarilla, papa blanca...) y en **pasos fijos de kg (1 kg, 2 kg...)**.
  - ⚠️ Hay que validar con precios: en la investigación, el papel higiénico mayorista perdió contra Tottus y el detergente Bolívar solo tuvo 7.9 % de brecha.

---

## Idea base: separar dos cosas que hoy están mezcladas

| Qué | De qué depende | Para qué sirve |
|---|---|---|
| **Descuento del producto** | De cuánto compra **Yapa en total** de ese producto (sumando todas las zonas) | Es lo que negocia el proveedor: le compras 300 kg de arroz, no 40. |
| **Costo del envío** | De cuántos pedidos hay **en tu zona** | El camión para una vez en tu edificio; mientras más vecinos, más se reparte. |

Separarlos resuelve dos cosas:

- El descuento se vuelve **mucho más estable**: que un vecino se retire casi no mueve el total de toda Yapa.
- Cada zona sigue teniendo su motivación propia ("faltan 3 vecinos para que el envío baje").

---

## 1. Descuentos que suben y bajan en vivo: el problema de los que se retiran

**El problema:** alguien compra cuando ya se desbloqueó el segundo descuento. Luego dos personas cancelan, se vuelve al primer descuento, y esa persona pagó menos de lo que realmente cuesta. Yapa pierde.

### Opciones

| Opción | Cómo funciona | ¿Yapa puede perder? | Veredicto |
|---|---|---|---|
| **A. Todos pagan el precio máximo; el ahorro se liquida al final** | Todos pagan el precio de lista. En pantalla se muestra en vivo "precio final estimado: S/ 2.85". Lo que cuenta es la cantidad **al cierre**, y la diferencia vuelve como saldo después de la entrega. | **Nunca.** Si alguien cancela, solo baja el ahorro estimado de los demás. | ✅ **Recomendada** |
| B. Cada uno paga el precio del momento y se congela | El que llegó al segundo descuento paga ese precio y Yapa absorbe si luego baja. | Sí | ❌ |
| C. Un descuento ganado ya no se pierde | Al llegar a la meta, queda asegurado para todos. | Sí: el proveedor cobra según lo que realmente se compra el jueves. | ❌ |
| D. Margen de tolerancia | El descuento se "suelta" solo si se baja bastante de la meta (por ejemplo 10 %). | Algo, pero acotado | Solo como complemento de B |
| E. No dejar cancelar después de cierta hora | Nadie se retira desde el martes. | No | Se puede combinar, pero incomoda y no hace falta con A |
| F. Fondo de estabilidad | Una parte de la comisión cubre estas pérdidas. | Sí, pero cubierto | Innecesario con A |

### Por qué A

Es el mismo mecanismo que ya decidiste ("nunca se cobra más de lo mostrado, la diferencia vuelve"). Solo se aplica también a los descuentos por volumen. El proveedor cobra lo que Yapa compra el jueves, así que **lo único que importa es la foto del cierre**. Todo lo que se muestra antes es un pronóstico que motiva a comprar.

### Qué ve el cliente

```text
Arroz Costeño 5 kg
Pagas hoy:              S/ 16.00
Precio final estimado:  S/ 14.25   ← baja si se suman más vecinos
[██████████░░] 80 de 100 bolsas para el siguiente descuento
Te devolvemos la diferencia como saldo después de la entrega.
```

### Cuándo se liquida

Hay **una sola liquidación después de la entrega**, que junta todo:

- ahorro por volumen;
- ahorro en el envío;
- devolución de artículos faltantes o dañados.

El cliente ve un solo resumen ("esta semana te devolvemos S/ 8.40") como saldo que no vence, y puede pedir la devolución a su Yape/Plin (hasta 30 días).

Si el cliente cancela antes del cierre, se le devuelve el 100 % y listo.

---

## 2. Zonas creadas por los vecinos

Tu propuesta: un vecino "admin" crea la zona, invita a los demás, y las zonas cercanas pueden unirse.

### Cómo aterrizarla

- **La zona es un punto de recepción**, no un polígono dibujado. Dibujar en el mapa es difícil de programar y de explicar. La zona se define por:
  - la **dirección de recepción** (portería del edificio, caseta del condominio, bodega aliada, casa del admin);
  - un **radio máximo** para los miembros (por ejemplo, 300 m ≈ 3 cuadras).
- **El camión hace una sola parada por zona.** Ahí está el ahorro real: no se entrega casa por casa sino a un punto. Es la lección más fuerte de los antecedentes.
- **El admin de zona es un vecino, no un empleado:**
  - Crea la zona, registra el punto de recepción y a la persona responsable, e invita a sus vecinos.
  - **Nunca toca plata**: cada vecino paga directo a Yapa.
  - Rol **transferible**, para que si se va la zona no muera.
  - Incentivo chico, sin sueldo. Por ejemplo, envío gratis para él. Favo pagaba S/ 500–1,000 a sus líderes y eso le rompió los costos.
- **Unión de zonas cercanas:**
  - El sistema muestra "hay otra zona a 200 m".
  - Si **los dos admins aceptan**, cuentan como un **grupo** para el mínimo y el envío.
  - Cada una conserva su punto; son dos paradas pegadas.
  - Distancia máxima entre puntos: por ejemplo, 500 m.
  - Unirse puede ser **por esa semana** (para llegar al mínimo) o permanente.
- **Antes de activar una zona**, el admin confirma que el punto de recepción acepta (portería o junta de propietarios). Sin eso, la zona no se activa.
- En el piloto, las zonas solo pueden estar en Lince, Jesús María y La Victoria.

---

## 3. Mínimo, costo del camión y comisión

### Estructura de precio recomendada (dos partes, ambas transparentes)

1. **Comisión de servicio (% sobre el precio del producto).** Cubre armar los pedidos, verificar pagos, el fondo para imprevistos y la ganancia de Yapa.
2. **Envío compartido de la zona**: el costo de la parada dividido entre los pedidos de la zona. Funciona igual que los descuentos: se paga el máximo y lo que sobra vuelve.

No conviene meter el camión dentro de un % fijo. Con pocos pedidos pierdes y con muchos cobras de más. Si el envío se reparte, **la variable del camión la pagan los vecinos de forma justa y a la vista**, y eso refuerza la idea de "compra en grupo".

### Cómo sale el mínimo

```text
mínimo de pedidos por zona = costo de una parada ÷ envío máximo que aceptamos cobrar
```

Ejemplo (supuestos a validar):

- Camioneta con chofer el sábado ≈ S/ 300, y hace ≈ 8 paradas → **S/ 37.50 por parada** (redondeado a S/ 40).
- Envío máximo por pedido: **S/ 5**.
- **Mínimo = 40 ÷ 5 = 8 pedidos por zona.**
- Si la zona llega a 20 pedidos, el envío real es S/ 2 y a cada uno le vuelven S/ 3.

Hay que costear también el viaje de compra del jueves al proveedor. Ese se reparte entre **todas** las zonas y va dentro de la comisión.

### Comisión: cómo se arma

Ejemplo ilustrativo de un 12 %:

| Parte | % aprox. |
|---|---|
| Armado de pedidos (mano de obra) | 4 % |
| Gestión de pagos y atención | 1 % |
| Viaje de compra al proveedor | 1 % |
| Fondo para imprevistos (proveedor alterno, daños) | 1 % |
| Ganancia de Yapa | 5 % |

**Prueba de que tiene sentido**, con una canasta de ejemplo (a validar):

| | Monto |
|---|---|
| Precio del proveedor | S/ 100 |
| + comisión 12 % | S/ 112 |
| + envío máximo | S/ 5 |
| **Total que paga el cliente** | **S/ 117** |
| La misma canasta en el supermercado (supuesto) | S/ 140 |
| **Ahorro para el cliente** | ~16 % (y más con el saldo que vuelve) |

**Tarea concreta para validar:** tomen 10 productos de la canasta, anoten el precio en Plaza Vea/Tottus y el precio mayorista, y comprueben que con 12 % + envío sigue habiendo al menos 15 % de ahorro. Si no, hay que bajar la comisión o cambiar productos.

**Regla de oro (lección de los antecedentes):** ningún pedido puede dejar ganancia negativa. El sistema calcula la ganancia por pedido en cada ciclo y la reporta.

### Si la zona no llega al mínimo

En orden:

1. **Aviso temprano:** el martes por la noche el admin y los vecinos ven "faltan 3 pedidos".
2. **Unión automática sugerida** con la zona cercana (si existe y ambos admins aceptan).
3. Si igual no llega: **devolución del 100 % lo antes posible**, sin opción de saldo, como dijiste, para cuidar la imagen. El compromiso es "devolución el jueves".

### Sobre el miedo a que la gente desconfíe

La confianza se construye con **reglas claras antes de pagar**:

- barra de progreso visible;
- "si tu zona no llega a 8 pedidos, te devolvemos todo el jueves";
- el admin es un vecino conocido;
- la primera devolución se hace rápido.

Alternativa para zonas nuevas: **reservar sin pagar hasta activarse** y dar 24 h para pagar después. Genera menos desconfianza, pero más gente abandona. Se puede usar solo en el primer ciclo de una zona.

---

## 4. Envío

Queda resuelto con el punto 3: **envío compartido por zona, con tope máximo, y lo que sobra vuelve**. Se elimina el "S/ 7.90, gratis desde S/ 120" del Entregable 1, que era un subsidio sin cálculo detrás.

---

## 5. Faltantes del proveedor: prevenir antes que devolver

Hay que prevenir en varias capas:

1. **Stock comprometido en la lista semanal.** El proveedor aliado no solo manda precios: también **cuánto puede vender como máximo** de cada producto. Cuando Yapa llega a ese tope, el producto sale "agotado" en la web. **Nunca se vende lo que el proveedor no prometió.** Esta es la capa más importante.
2. **Confirmación al cierre.** El miércoles a las 20:00 se le envía la lista consolidada al proveedor y él confirma esa misma noche (reserva).
3. **Proveedor de respaldo.** Con 3–4 aliados, cada producto importante tiene uno principal y uno alterno. Si el alterno es más caro, lo cubre el fondo de imprevistos; el cliente no paga más.
4. **Colchón de sobrantes** (ver el punto 8): lo que sobró la semana pasada cubre faltantes pequeños.
5. **Catálogo de no perecibles**: su stock es mucho más predecible.
6. **Si aun así falta**, se devuelve ese artículo automáticamente en la liquidación. Lo que se incumpla se descuenta de la siguiente compra al proveedor, según el acuerdo de alianza.

---

## 6. Entrega en portería o con un encargado

Tu idea, cerrada:

- Cada zona registra su **punto de recepción** y **a la persona que recibe** (portero, encargado o admin).
- El repartidor entrega las bolsas **rotuladas con nombre y departamento**, toma **foto** de las bolsas entregadas y registra quién recibió y a qué hora.
- **Con esa entrega termina la responsabilidad de Yapa.** Esto va en las condiciones que el cliente acepta al registrarse en la zona.
- El cliente confirma "recibí" en la web; si no confirma en 24 h, se da por recibido. El plazo para reportar daños o faltantes corre desde la entrega.
- Esto también es un argumento para los no perecibles: las bolsas pueden esperar horas en portería sin problema.

---

## 7. Qué productos vender

**Recomendación para el piloto: no perecibles**, es decir, abarrotes, limpieza e higiene. Por ejemplo: arroz, azúcar, aceite, fideos, menestras, conservas, leche evaporada, avena, detergente, papel higiénico.

Por qué:

- **Desaparece el problema del peso variable.** Todo viene en paquete fijo (bolsa de 5 kg, caja de 12), así que no hay ajustes de precio por peso. Eso elimina un hueco completo del Entregable 1.
- No necesita cadena de frío, que tiene exigencias sanitarias.
- Aguanta en portería.
- El stock del proveedor es predecible (punto 5).
- Los sobrantes se pueden guardar para la semana siguiente (punto 8).

**Costo:** en abarrotes el supermercado compite fuerte con promociones, y el ahorro suele ser mayor en frutas y verduras. Por eso conviene validar el ahorro con los 10 productos del punto 3.

**Fase 2 (opcional):** frescos resistentes (papa, cebolla, ajo, limón) vendidos en **malla o bolsa cerrada de peso fijo**, nunca a granel, para no reabrir el problema del peso.

Pregunta para Kalos: ¿empezamos solo con no perecibles o metemos los frescos resistentes desde el inicio?

---

## 8. Proveedor que vende por caja o saco: qué hacer con lo que sobra

**El problema:** los vecinos piden 37 aceites y el proveedor vende cajas de 12. Si compras 4 cajas (48), sobran 11.

| Opción | Cómo | Pro | Contra |
|---|---|---|---|
| A. El proveedor aliado vende por unidad | Parte del acuerdo: vende por unidad al precio del tramo. | Cero sobrante | No todos los proveedores aceptan. |
| B. Solo comprar cajas completas | Se compran 3 cajas (36); el pedido 37 se devuelve. | Cero sobrante | Un cliente se queda sin producto. |
| C. Redondear hacia arriba y guardar | Se compran 4 cajas; los 11 aceites quedan como **colchón** para la próxima semana o para cubrir faltantes. | Nadie se queda sin producto y ayuda con el punto 5 | Pequeño inventario (aceptable solo con no perecibles). |
| D. Mostrar la caja como meta | "Faltan 11 aceites para completar la caja", para que los vecinos la llenen. | Engancha | No garantiza llenarla. |

**Recomendación:** A con los aliados que acepten. Para el resto, **C + D**:

- Se muestra la meta de la caja.
- Al cierre, si la caja está llena al 70 % o más, se compra completa y el sobrante va al colchón.
- Si está por debajo del 70 %, se compra solo lo que alcanza en cajas completas y el resto se devuelve.
- **Tope del colchón:** por ejemplo, máximo S/ 500 en total, para no convertirse en almacén (lección de Merqueo y Missfresh).

---

## Resumen para llevar a Kalos y Aaron

1. Todos pagan el precio máximo; el ahorro (productos + envío) se liquida después de la entrega como saldo.
2. El descuento depende del volumen total de Yapa; el envío, de los pedidos de tu zona.
3. Zona = punto de recepción + radio, creada por un vecino admin sin sueldo; zonas cercanas se pueden unir.
4. Mínimo de pedidos por zona = costo de parada ÷ envío máximo (ejemplo: 8). Si no se llega, devolución del 100 %.
5. Comisión de servicio de alrededor del 12 %, validada con 10 productos reales.
6. Faltantes: el proveedor informa su stock máximo, confirma al cierre y hay un proveedor de respaldo.
7. Entrega en el punto de recepción con foto; ahí termina la responsabilidad de Yapa.
8. Piloto con no perecibles en paquete fijo.
9. Sobrantes por caja: se redondea arriba y se guarda como colchón (con tope), solo en no perecibles.
