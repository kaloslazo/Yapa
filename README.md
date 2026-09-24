# Yapa · Aplicación de SDD

Repositorio académico del curso **Diseño de Software (EL3304)**, UTEC 2026-2, sección 1. Docente: Jaime Moshe Farfán Madariaga.

| | |
|---|---|
| **Integrantes** | Carlos Bravo · Aaron Gonzales · Kalos Lazo |
| **Metodología asignada** | Specification-Driven Development (SDD) |
| **Proyecto** | Yapa: compras grupales semanales de vecinos de Lince, Jesús María y La Victoria, con entrega el sábado en el punto de recepción de cada zona |
| **Problema seleccionado** | Registrar el pedido semanal con precio máximo garantizado y pago anticipado, y **liquidar el ciclo** devolviendo como saldo el ahorro del grupo ("te devolvemos") |
| **Tecnologías** | Python 3.11+ (solo biblioteca estándar), `unittest`, Markdown + Mermaid, Git, GitHub Actions |

## Qué se implementó

- **CUN-02 Registrar pedido semanal** (spec v2): cliente y zona válidos, ciclo abierto (lunes 00:00 hasta antes del miércoles 20:00, hora de Lima), un pedido por ciclo, cantidades en pasos fijos, stock declarado por el proveedor, precio máximo calculado por el sistema, mínimo de S/ 50, envío con tope de S/ 5 y pago Yape/Plin con código de operación único.
- **Liquidación del ciclo**:
  - pedidos sin pago verificado → cancelados;
  - grupos de zonas bajo el mínimo → reembolso del 100 %;
  - descuento por volumen entre todos;
  - envío repartido por zona;
  - faltantes por artículo;
  - **saldo a favor que nunca es negativo**.

Lo que queda fuera de alcance está declarado en `docs/sdd/10-clarificaciones-v2.md`.

## Instalación

Solo requiere Python 3.11 o superior. No hay dependencias externas.

```bash
git clone https://github.com/kaloslazo/sdd-2026-exposicion.git
cd sdd-2026-exposicion
git checkout sdd-v2-pedido-liquidacion
```

## Ejecutar las pruebas

```bash
# Linux / macOS / Git Bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

```powershell
# Windows PowerShell
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
```

Resultado esperado: `Ran 45 tests ... OK`. La salida real está en `docs/evidencia/03-pruebas-en-verde.txt`.

## Ejecutar la demo

Con `PYTHONPATH=src` configurado como arriba:

```bash
python -m yapa_sdd.cli cotizar   ejemplos/pedido_valido.json       # cuánto yapear (precio máximo)
python -m yapa_sdd.cli registrar ejemplos/pedido_valido.json       # pedido REGISTRADO
python -m yapa_sdd.cli registrar ejemplos/pedido_fuera_de_hora.json  # CYCLE_CLOSED (miércoles 20:00:00)
python -m yapa_sdd.cli registrar ejemplos/pedido_bajo_minimo.json    # SUBTOTAL_BELOW_MINIMUM, informa cuánto falta
python -m yapa_sdd.cli registrar ejemplos/pedido_zona_fuera.json     # ZONE_NOT_AVAILABLE (Miraflores)
python -m yapa_sdd.cli ciclo     ejemplos/ciclo_demo.json            # liquidación completa: "te devolvemos"
```

La salida real está en `docs/evidencia/04-demo-consola.txt`.

## Cómo leer el repositorio (orden SDD)

| Paso | Archivo |
|---|---|
| Contexto | `docs/sdd/00-contexto-yapa.md` |
| Hallazgos y clarificación | `docs/analisis/` y `docs/sdd/10-clarificaciones-v2.md` |
| Alcance | `docs/sdd/01-alcance.md` |
| Especificación | `docs/sdd/02-especificacion-cun-02.md`, `docs/sdd/11-especificacion-liquidacion.md` |
| Criterios de aceptación | `docs/sdd/05-criterios-aceptacion.md` |
| Plan y diseño (diagramas) | `docs/sdd/03-plan.md`, `docs/sdd/12-diseno.md` |
| Tareas | `docs/sdd/04-tareas.md` |
| Código | `src/yapa_sdd/` |
| Pruebas | `tests/` |
| Trazabilidad | `docs/sdd/06-trazabilidad.md` |
| Evidencia | `docs/evidencia/` |
| Convergencia e iteraciones | `docs/sdd/07-checklist-convergencia.md`, `docs/sdd/08-registro-iteraciones.md` |

## Estructura del código

```text
src/yapa_sdd/
  domain.py              datos del negocio, constantes del piloto, redondeo a favor del cliente
  cycle.py               hora de Lima y ciclo semanal
  store.py               repositorio en memoria (reemplazable por base de datos)
  order_registration.py  CUN-02: cotizar, registrar, verificar pago
  settlement.py          liquidación del ciclo
  seed.py                catálogo, zonas y clientes del piloto
  cli.py                 consola para la demo
```

## Repositorio general

Contexto completo y roadmap de Yapa: <https://github.com/kaloslazo/yapa-proyecto-completo>
