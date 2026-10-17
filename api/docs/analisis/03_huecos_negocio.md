# 03 · Huecos de negocio de Yapa

Fuentes comparadas:

- `Proyecto/Idea_inicial.pdf`: v1 (por **zona**) y v2 "compra consolidada por **edificio**", con el análisis de antecedentes.
- `Proyecto/Proyecto_entrega1/README.md` (Entregable 1, 03/09/2026): el modelo oficial.
- Repos de Kalos (19/09/2026).

## Hallazgo principal

**El Entregable 1 abandonó casi todas las correcciones que la propia Idea inicial había sacado de los fracasos anteriores.** La v2 de la idea decía que Favo murió por agregar por **líder/distrito** en lugar de por **dirección física**, por no tener mínimo de activación y porque su pedido promedio nunca dejó margen. El Entregable 1 agrega **por zona = distrito**, no tiene mínimo de activación por zona y no tiene ninguna regla de margen. Es decir, reproduce el patrón de Favo.

No es obligatorio volver al modelo por edificio, pero el equipo tiene que **decidirlo y dejarlo escrito** (ver D-01 en `04_decisiones_pendientes.md`). Hoy nadie lo decidió: simplemente se perdió.

## H1 · Correcciones de la Idea v2 que no llegaron al Entregable 1

| # | Lección / corrección (Idea v2) | Antecedente | Qué pasa en el Entregable 1 | Gravedad |
|---|---|---|---|---|
| H1.1 | Agregar por **dirección física (edificio)**, no por persona ni distrito | Favo (líder disperso en un distrito) | Zona = distrito (EN-03, RN-01). | **Crítica** |
| H1.2 | **Mínimo de activación** (p. ej. 15 pedidos o S/ 1,500); si no se alcanza, el ciclo no corre y **nadie es cobrado** | Favo, social commerce LatAm | Solo existe el mínimo individual de S/ 50 (RN-03). CUN-04 FA-01 dice "se mantiene si cubre el costo; de lo contrario se contacta al cliente": no hay número, no dice quién decide ni qué pasa con los pagos ya recibidos. | **Crítica** |
| H1.3 | **Precio techo**: el cliente nunca paga más de lo mostrado; el cobro final es ≤ techo. Cobrar de más es "el riesgo legal más serio" (Ley 29571). | Idea v2, legal | **RN-21 y RN-22 hacen lo contrario**: se cobra un saldo en la puerta si el peso real sube (hasta +5 % por RN-06), y si el cliente no paga se retiene el pedido y se le suspende. | **Crítica (legal)** |
| H1.4 | **Margen de seguridad 8–12 %** frente a la volatilidad del precio mayorista entre el cierre (miércoles) y la compra | Idea v2 | Ninguna regla dice quién absorbe una subida del precio mayorista el jueves. | Alta |
| H1.5 | **Margen verificado por pedido** antes de escalar | Favo ("unit economics nunca cerraron") | CUN-01 paso 4 dice "revisa el margen estimado", pero no hay margen mínimo ni costo por pedido. El delivery es gratis desde S/ 120 sin ningún cálculo que lo respalde. | **Crítica** |
| H1.6 | **Catálogo curado** de 1–2 marcas por categoría (el volumen por SKU tiene que ser real) | Idea v2 | Nada. | Alta |
| H1.7 | **Sin cadena de frío** en el MVP (sin cárnicos, lácteos ni congelados), por DIGESA y merma | Missfresh, Idea v2 | El catálogo incluye "frutas, verduras y otros perecibles" sin excluir nada. | Alta (sanitaria) |
| H1.8 | **Sin inventario**: se compra solo lo ya pedido (cross-docking) | Missfresh, Merqueo (sobrestock) | CUN-05 FA-02 "producto vendido por bulto: se ajusta la compra a la unidad mayorista" **genera sobrante**. No se dice quién lo paga ni qué se hace con él. | Alta |
| H1.9 | **Recompra** como métrica principal; "repetir pedido anterior" + recordatorio | "La métrica que mató a casi todos" | No hay métricas, ni reportes, ni función de repetir pedido. Los reportes de la Idea v1 (ventas, ahorro entregado, eficiencia de rutas) desaparecieron. | Alta |
| H1.10 | **Ahorro verificable**: fecha, fuente y SKU del precio del supermercado, con histórico auditable | Ley 29571 (publicidad comparativa) | Se promete "cuánto se estaría ahorrando" sin fuente ni fecha. | Media–alta (legal) |
| H1.11 | **Punto de recepción** (portería) para el vecino ausente | Idea v2 | RN-18: 2 intentos, 10 min y se retorna. **No se dice qué pasa con el pedido retornado**: ¿reembolso?, ¿cargo por reintento?, ¿qué se hace con los perecibles? | Alta |
| H1.12 | Coordinador de edificio **no remunerado**, rol transferible | Favo (líderes pagados S/ 500–1,000 que igual rotaban) | El rol desapareció. Puede ser válido, pero no hay registro de la decisión. | Media |
| H1.13 | **Tributario**: RUC, comprobante electrónico (boleta/factura), IGV modelados desde el diseño | Idea v2 | No hay entidad Comprobante ni IGV en ningún precio. | Alta |
| H1.14 | **Libro de reclamaciones virtual** y política de devoluciones publicada | Idea v2, Indecopi | CUN-08 cubre incidencias internas, pero no el reclamo formal. | Alta (legal) |
| H1.15 | **Trazabilidad por lote**: de qué proveedor y qué día salió cada producto | Idea v2 | No existe. | Media |
| H1.16 | **Cierre transaccional**: durante el recálculo nadie entra ni modifica | Idea v2 (técnico) | No existe; además no se define si un pedido puede editarse antes del cierre. | Media |
| H1.17 | **Componente técnico central**: motor de agregación con escalones de precio (v2) o ruteo (v1) | Idea | El Entregable 1 solo lo toca en RN-17 (aprobación humana). El corazón técnico del proyecto no tiene caso de uso propio. | Media (para el curso) |

## H2 · Contradicciones dentro del Entregable 1

| # | Contradicción | Dónde |
|---|---|---|
| H2.1 | **Cronograma imposible**: el cierre es el miércoles 20:00, la transferencia se verifica "hasta el jueves 12:00" (RN-11) y la compra en el mayorista es el jueves. Santa Anita opera de madrugada, así que **se compra antes de saber quién pagó**. Y los perecibles comprados el jueves pasan 2 días guardados hasta el sábado. | RN-11, §4.11, CUN-05 |
| H2.2 | **"Precio referencial" significa dos cosas**: en EN-06/CUN-01 es el precio del supermercado para comparar el ahorro; en RN-21 es el precio estimado que se cobra. | EN-06, RN-21 |
| H2.3 | RN-11: si la transferencia no se verifica, el pedido pasa a contraentrega "si el cliente lo acepta". **¿Y si no lo acepta?** No está definido (¿se cancela?, ¿se compra igual?). | RN-11 |
| H2.4 | **Contraentrega sin límite**: Yapa compra perecibles para alguien que puede no pagar. RN-22 solo suspende al cliente; la pérdida no se trata. No hay tope (p. ej. solo clientes con N pedidos pagados). | RN-10, RN-22 |
| H2.5 | RN-22 suspende "para nuevos pedidos", pero CUN-02 no lista RN-22 y la matriz tampoco. | §4.7, §5 |
| H2.6 | **Máquina de estados incompleta**: en §4.1 aparecen registrado, consolidado, comprado, preparado, en ruta, entregado y con incidencia. Faltan `CANCELADO` (CUN-04 lo excluye), `RETORNADO`/`NO_ENTREGADO` (RN-18, RN-22) y `PENDIENTE_SIGUIENTE_CICLO` (EX-02). Los estados de Pago (verificado, pendiente, contraentrega, observado) no se modelan como tales. | §4.1, CUN-03 |
| H2.7 | RN-02 dice que "una solicitud posterior pasa al siguiente ciclo", pero ¿con qué precios? El catálogo del ciclo siguiente todavía no existe (CUN-01). | RN-02, CUN-01 |
| H2.8 | Delivery S/ 7.90 por pedido **en un modelo cuya promesa es repartir el costo**. Además la tarifa no depende de cuántos pedidos tenga la zona. La competencia da envío gratis desde S/ 79–150 (Idea v1). | RN-04 |
| H2.9 | RN-06 (±5 %) + RN-08 (sustituto hasta +10 %): el cliente puede terminar pagando hasta ~15 % más que lo que vio, sin haber confirmado. | RN-06, RN-08 |
| H2.10 | Reembolsos: RN-08, RN-20 y CUN-05 EX-01 hablan de "devolver el importe", pero no dicen **cómo** (transferencia, nota de crédito o saldo a favor), **en qué plazo**, ni qué pasa con un contraentrega que no pagó nada. | RN-08, RN-20 |
| H2.11 | Pedido: ¿cuántos por cliente por ciclo? ¿Se puede editar hasta el cierre? RN-20 cubre la cancelación, pero no la edición. | CUN-02 |
| H2.12 | Capacidad por ventana y zona: RN-09 la menciona, pero no hay número ni fórmula (y "decisiones pendientes" de Kalos lo repite). | RN-09 |
| H2.13 | Multi-dirección: ¿un cliente puede tener varias direcciones o cambiarla después de registrar el pedido? | EN-02 |
| H2.14 | Notificaciones: el cliente "sigue su pedido por estados", pero ningún CUN notifica (cierre del ciclo, ajuste de precio, faltante, "en ruta"). | §4.1 |

## H3 · Riesgos de viabilidad que el software sí puede mitigar

Estos no se resuelven con código, pero el código puede **medirlos y hacer cumplir** los límites. Son lo que se aprendió de los fracasos:

1. **Umbral de activación por zona o edificio** evaluado al cierre → si no se alcanza, no se compra y se devuelve todo (H1.2).
2. **Margen por pedido calculado y registrado** en cada ciclo → alerta si un pedido deja margen negativo (H1.5).
3. **Recompra en la semana 4** como KPI del piloto; si es < 50 %, el problema es la propuesta de valor, no el software (Idea v2).
4. **No subsidiar**: ninguna regla de envío gratis o descuento sin un cálculo de costo detrás (lección de Facily, Muni y Favo, que quemaron capital en CAC y subsidios).
5. **Nada de inventario**: la compra es igual a lo pedido; el sobrante por bulto se registra como costo del ciclo (H1.8).

## Antecedentes ampliados

→ Ver `05_antecedentes.md` (investigación web con fuentes).
