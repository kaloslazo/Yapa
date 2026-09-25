# Kit de validación de campo: ¿Yapa le gana al mercado del barrio?

## Por qué hace falta

Con precios reales ya comprobamos que en frescos Yapa sale 36–67 % más barato que **Plaza Vea**. Pero el vecino que compra papa, cebolla o limón probablemente no la compra en Plaza Vea, sino en el **mercado de su barrio**, y ese precio no lo tenemos. Si el mercado está cerca del mayorista, el ahorro de Yapa baja mucho, y lo que ofrecemos pasa a ser la comodidad (no ir, no cargar, recibir en portería) más que el precio.

Esta es la validación más importante que queda pendiente, y no la puede hacer una IA: hay que ir al mercado.

## Qué hacer (unos 45 minutos por mercado)

1. Ir a **2 o 3 mercados** de las zonas piloto. Por ejemplo, el Mercado de Lince, uno de Jesús María, o donde compra cada uno en su casa.
2. En cada mercado, anotar el precio **por kilo** de los 7 frescos del piloto: papa blanca, papa amarilla, cebolla roja, ajo, limón, camote y zanahoria.
3. En la sección de limpieza o en la bodega, anotar el precio del **galón de Exlim** (limpiatodo) y de otra marca emergente si la hay.
4. Si un puesto vende por montón, bolsa o malla, pesar o preguntar cuántos kilos trae, y convertir a precio por kilo.
5. Anotar el nombre del mercado y la fecha. Si se puede, tomar foto del cartel de precios: sirve como evidencia para el profe.

## Cómo registrar

Abrir `docs/campo/precios_plantilla.csv` (se abre en Excel) y completar:

- `precio_mercado_barrio`: precio por kilo (o por unidad en limpieza).
- `fuente_mercado`: nombre del mercado o puesto.
- `fecha`: día de la visita.
- En la fila de Exlim, completar también `precio_mayorista` si se consigue el precio de la distribuidora, y `precio_supermercado` si lo venden ahí.

Si hay varios mercados, copiar la fila de cada producto y poner el mercado en `fuente_mercado`.

## Cómo leer el resultado

```bash
PYTHONPATH=src python tools/validar_precios.py docs/campo/precios_plantilla.csv
```

Por cada producto muestra:

- **yapa**: el precio que pagaría el vecino con la comisión, el envío prorrateado y la merma.
- **vs mercado** y **vs super**: cuánto ahorra el vecino (%).
- **comisión máx**: la comisión más alta que todavía deja **15 % de ahorro** frente al mercado del barrio (o frente al supermercado, si no hay dato del mercado).
- **veredicto**: si con la comisión actual el ahorro llega al 15 %.

## Qué decidir con el resultado

- **Si en la mayoría de frescos el ahorro frente al mercado es ≥ 15 %:** el modelo se sostiene y el piloto sigue como está.
- **Si queda entre 0 y 15 %:** bajar la comisión de esos productos (la columna "comisión máx" dice hasta cuánto), o sacarlos del catálogo.
- **Si Yapa sale más caro que el mercado:** en ese producto el valor que se ofrece es solo la comodidad. Toca decidir en equipo si vale la pena mantenerlo.

Cualquier cambio de comisión se registra primero como cambio del supuesto S-07 en `supuestos-a-validar.md`, y después se actualizan la spec, las pruebas y el catálogo.
