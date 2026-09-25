# Supuestos para que el equipo valide

Estas son las decisiones que se tomaron **por defecto** para poder especificar y programar. Ninguna es definitiva: si Kalos o Aaron no están de acuerdo con alguna, se cambia primero aquí y en la spec, y después en las pruebas y el código (así funciona SDD).

Cómo usar esta lista: marca ✅ si estás de acuerdo o escribe tu propuesta en la columna "Otra idea". Entre paréntesis va el código del supuesto, para buscarlo en las specs.

---

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

## E. Técnicos (no requieren decisión de negocio, solo revisión)

S-11 (orden de los errores), S-16/S-17 (saldo en pedidos no atendidos, liquidar una sola vez), S-21 (un código de operación no se reutiliza), S-24 (no se genera saldo con pagos sin confirmar: evita fraude), S-27 (distancia en línea recta), S-35 (stock por semana), S-37 (catálogo base si no se publicó uno).

---

## Lo que **no** es un supuesto sino una tarea de campo

- **Precios del mercado de barrio.** Es el competidor real en frescos y no está medido. Ver `kit-validacion-campo.md`.
- **Precio del galón de Exlim** y de otras marcas emergentes de limpieza.
- **Confirmar con un proveedor aliado real** que aceptaría respetar su lista semanal y declarar su stock máximo.
