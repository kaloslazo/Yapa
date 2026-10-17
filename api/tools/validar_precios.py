"""Compara el precio Yapa contra el mercado de barrio y el supermercado.

Uso:
    PYTHONPATH=src python tools/validar_precios.py docs/campo/precios_plantilla.csv

Fórmula (la misma de docs/analisis/08_validacion_economica.md):
    precio Yapa = mayorista × (1 + comisión) × (1 + envío prorrateado) / (1 − merma)
La merma solo se aplica a frescos. El envío prorrateado es S/ 5 sobre un pedido de S/ 150.
"""

import csv
import sys
from decimal import Decimal, ROUND_HALF_UP

from yapa_sdd.domain import COMMISSION, MAX_DELIVERY_FEE


TICKET = Decimal("150")
MERMA_FRESCOS = Decimal("0.05")
AHORRO_OBJETIVO = Decimal("15")  # % mínimo que queremos ofrecer


def precio_yapa(mayorista: Decimal, categoria: str, comision: Decimal | None = None) -> Decimal:
    comision = COMMISSION[categoria] if comision is None else comision
    precio = mayorista * (1 + comision) * (1 + MAX_DELIVERY_FEE / TICKET)
    if categoria == "FRESCOS":
        precio = precio / (1 - MERMA_FRESCOS)
    return precio


def ahorro(yapa: Decimal, otro: Decimal | None) -> Decimal | None:
    if not otro:
        return None
    return (1 - yapa / otro) * 100


def comision_maxima(mayorista: Decimal, categoria: str, referencia: Decimal) -> Decimal:
    """Comisión más alta que todavía deja AHORRO_OBJETIVO frente a la referencia."""
    base = precio_yapa(mayorista, categoria, Decimal("0"))
    tope = referencia * (1 - AHORRO_OBJETIVO / 100)
    return (tope / base - 1) * 100


def _num(value: str) -> Decimal | None:
    value = (value or "").strip()
    return Decimal(value) if value else None


def _fmt(value: Decimal | None, suffix: str = "", places: str = "0.1") -> str:
    if value is None:
        return "-"
    return f"{value.quantize(Decimal(places), rounding=ROUND_HALF_UP)}{suffix}"


def main(path: str) -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    with open(path, encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    print(f"{'producto':<22} {'yapa':>7} {'vs mercado':>11} {'vs super':>9} {'comisión máx':>13}  veredicto")
    for row in rows:
        mayorista = _num(row["precio_mayorista"])
        if mayorista is None:
            continue
        categoria = row["categoria"].strip().upper()
        yapa = precio_yapa(mayorista, categoria)
        mercado, superm = _num(row["precio_mercado_barrio"]), _num(row["precio_supermercado"])
        vs_mercado, vs_super = ahorro(yapa, mercado), ahorro(yapa, superm)
        referencia = mercado or superm
        maxima = comision_maxima(mayorista, categoria, referencia) if referencia else None
        clave = vs_mercado if vs_mercado is not None else vs_super
        veredicto = "sin dato" if clave is None else ("conviene" if clave >= AHORRO_OBJETIVO else "NO conviene")
        print(f"{row['producto'][:22]:<22} {_fmt(yapa, places='0.01'):>7} {_fmt(vs_mercado, '%'):>11} {_fmt(vs_super, '%'):>9} "
              f"{_fmt(maxima, '%'):>13}  {veredicto}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "docs/campo/precios_plantilla.csv"))
