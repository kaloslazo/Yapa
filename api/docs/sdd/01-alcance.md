# Alcance SDD · iteración 2

## Incluido

### CUN-02 · Registrar pedido semanal (reescrito)

El cliente registra su pedido del ciclo desde su zona. Paga por adelantado con Yape o Plin el **precio máximo** que calcula el sistema, e informa el código de operación. El administrador verifica ese código antes del cierre.

Spec: `02-especificacion-cun-02.md`.

### Liquidación del ciclo (nuevo): "te devolvemos"

Después de la entrega, el sistema calcula para cada pedido cuánto costó realmente. Toma en cuenta:

- el descuento por volumen alcanzado entre todos;
- el envío repartido en la zona;
- los artículos faltantes o dañados.

Con eso devuelve la diferencia **como saldo a favor**. Si la zona no llegó al mínimo, devuelve el 100 % al medio de pago.

Spec: `11-especificacion-liquidacion.md`.

### Límite de CUN-03 · Procesar pago

Incluye solo lo que estas dos funcionalidades necesitan:

- medio permitido (Yape o Plin);
- código de operación único;
- monto igual al total;
- verificación por el administrador.

No incluye integración con Yape o Plin, que no tienen API pública.

## Reglas del Entregable 1 que cambian

| Regla original | Qué pasa ahora | Motivo |
|---|---|---|
| RN-01 distritos piloto | Se mantiene, aplicada a la **zona** (punto de recepción) | C-07 |
| RN-02 cierre del miércoles 20:00 | Se mantiene; el pedido tardío se rechaza (ya no "pasa al siguiente ciclo") | S-02 |
| RN-03 mínimo S/ 50 | Se mantiene, sobre el subtotal exacto | S-04 |
| RN-04 envío S/ 7.90, gratis desde S/ 120 | **Reemplazada** por envío compartido con tope de S/ 5 | C-09 |
| RN-05 precio con unidad y vigencia | Se mantiene: el precio sale del catálogo del ciclo | C-12 |
| RN-06 variación de peso ±5 % | **Eliminada**: frescos en pasos fijos de kg | C-11 |
| RN-07 producto activo, dirección válida | Se mantiene, con la zona como dirección | C-07 |
| RN-08 sustitución hasta +10 % | **Reemplazada** por devolución del artículo faltante | C-10 |
| RN-09 ventana elegida por el cliente | **Reemplazada**: Yapa asigna la ventana a la zona | S-10 |
| RN-10 transferencia, billetera y contraentrega | **Solo Yape y Plin**, sin contraentrega | C-03 |
| RN-11 verificación hasta el jueves 12:00 | **Reemplazada**: solo cuentan los pagos verificados al cierre | C-03, S-02 |
| RN-12 referencia única | Se mantiene como código de operación único | C-04 |
| RN-21 cobro del saldo en la entrega | **Eliminada** (Ley 29571, art. 4.2) | C-01 |
| RN-22 no entregar si no paga el saldo | Queda solo la suspensión del cliente, que se valida al registrar | C-03 |

## Fuera de alcance

Ver `10-clarificaciones-v2.md`, sección "Fuera de alcance".
