# Informe de verificación SDD Yapa

## Iteración 2 (24/09/2026)

### Pruebas

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

| Momento | Resultado | Evidencia |
|---|---|---|
| Pruebas escritas, sin código | 2 módulos de prueba fallan al importar (el código no existe) | `docs/evidencia/01-pruebas-en-rojo.txt` |
| Registro implementado | Registro en verde, liquidación en rojo | `docs/evidencia/02-registro-verde-liquidacion-rojo.txt` |
| Final | **45 pruebas, OK** | `docs/evidencia/03-pruebas-en-verde.txt` |

### Demo

`docs/evidencia/04-demo-consola.txt`: cotización, registro válido, tres rechazos (ciclo cerrado, bajo el mínimo, zona fuera del piloto) y un ciclo completo liquidado.

### Especificación frente a resultado implementado

| Criterio | Esperado según la spec | Obtenido |
|---|---|---|
| CA-01 | Total S/ 59.51, subtotal S/ 54.518 | Igual (demo `registrar`, `test_ca01_*`) |
| CA-04 | Miércoles 20:00:00 → `CYCLE_CLOSED` | Igual (demo `pedido_fuera_de_hora`, `test_ca04_rejects_exactly_at_close`) |
| CA-11 | S/ 49.99568 rechazado, "faltan S/ 0.01" | Igual (`test_ca11_minimum_uses_exact_subtotal`) |
| CL-02 | Grupo con 7 pedidos → `NO_ATENDIDO`, 100 % al medio de pago | Igual (demo `ciclo`: Lince 5 + 2 → reembolso S/ 58.28 c/u) |
| CL-04 | 100 kg de papa amarilla → S/ 3.7856 | Igual (demo `ciclo` y `test_cl04_*`) |
| CL-07 | 1 kg de limón faltante → vuelve S/ 2.35 | Igual (demo: pedido 19 vs 20, 6.58 vs 4.23) |
| CL-08 | Saldo ≥ 0 y final + saldo = pagado | Igual en todos los pedidos liquidados |

## Iteración 1 (19/09/2026)

Vertical inicial de CUN-02 con 8 reglas y 8 pruebas, y presentación de 12 diapositivas. Ver el historial de Git hasta el commit `bd48598`.
