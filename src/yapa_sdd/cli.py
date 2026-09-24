"""Consola para la demo en vivo.

Uso (desde la raíz del repo, con PYTHONPATH=src):
    python -m yapa_sdd.cli cotizar ejemplos/pedido_valido.json
    python -m yapa_sdd.cli registrar ejemplos/pedido_valido.json
    python -m yapa_sdd.cli ciclo ejemplos/ciclo_demo.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from .domain import BusinessRuleError, Customer
from .order_registration import quote_order, register_order, verify_payment
from .seed import pilot_store
from .settlement import settle_cycle


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def _lines(data: dict) -> list[tuple[str, str]]:
    return [(line["productId"], line["quantity"]) for line in data["lines"]]


def _print_lines(lines) -> None:
    for line in lines:
        print(f"  {line.product_id:<26} {line.quantity:>6}  x S/ {line.max_unit_price:.3f}  = S/ {line.max_total:.3f}")


def cotizar(path: str) -> None:
    data = _load(path)
    quote = quote_order(pilot_store(), _lines(data))
    print("COTIZACION (precio maximo, nunca pagaras mas)")
    _print_lines(quote.lines)
    print(f"  Subtotal: S/ {quote.subtotal:.3f}   Envio maximo: S/ {quote.delivery_fee}")
    print(f"  Total a yapear: S/ {quote.total}")


def registrar(path: str) -> None:
    data = _load(path)
    payment = data["payment"]
    order = register_order(
        pilot_store(),
        customer_id=data["customerId"],
        lines=_lines(data),
        payment_method=payment["method"],
        operation_code=payment.get("operationCode", ""),
        amount=payment["amount"],
        now=datetime.fromisoformat(data["requestedAt"]),
    )
    print(f"PEDIDO {order.order_id} {order.status}  (ciclo {order.cycle}, zona {order.zone_id})")
    _print_lines(order.lines)
    print(f"  Subtotal: S/ {order.subtotal:.3f}   Envio: S/ {order.delivery_fee}   Total: S/ {order.total}")
    print(f"  Pago {order.payment_method} op. {order.operation_code}: {order.payment_status}")


def ciclo(path: str) -> None:
    data = _load(path)
    store = pilot_store()
    now = datetime.fromisoformat(data["requestedAt"])
    customer_id = 1000
    for group in data["groups"]:
        lines = _lines(group)
        for _ in range(group["count"]):
            customer_id += 1
            store.add_customer(Customer(customer_id, f"Vecino {customer_id}", group["zoneId"]))
            order = register_order(
                store, customer_id=customer_id, lines=lines, payment_method="YAPE",
                operation_code=f"OP{customer_id}", amount=quote_order(store, lines).total, now=now,
            )
            if group.get("verified", True):
                verify_payment(store, order.order_id, now=now)

    missing = [(m["orderId"], m["productId"], m["quantity"]) for m in data.get("missing", [])]
    result = settle_cycle(store, store.orders[1].cycle, missing)

    print(f"LIQUIDACION DEL CICLO {result.cycle}")
    print("\nPrecio final por producto (tramo alcanzado entre todos):")
    for summary in result.products.values():
        product = store.products[summary.product_id]
        print(f"  {summary.product_id:<26} total {summary.total_quantity:>6} {product.unit:<6}"
              f" tramo desde {summary.tier_min_quantity:>4}  max S/ {product.max_unit_price():.4f}"
              f" -> final S/ {summary.final_unit_price:.4f}")

    print("\nPedidos:")
    print(f"  {'id':>3} {'zona':<11} {'estado':<12} {'pagado':>8} {'envio':>6} {'final':>8} {'devuelto':>9}  destino")
    for settled in result.orders.values():
        zone = store.orders[settled.order_id].zone_id
        print(f"  {settled.order_id:>3} {zone:<11} {settled.status:<12} {settled.paid:>8} "
              f"{settled.delivery_fee:>6.2f} {settled.final_amount:>8} {settled.refund_amount:>9}  "
              f"{settled.refund_destination or '-'}")

    print(f"\nTotal devuelto como saldo: S/ {result.total_credited}")
    print(f"Total reembolsado al medio de pago: S/ {result.total_refunded}")


def main(argv=None) -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="yapa", description="Demo SDD de Yapa")
    parser.add_argument("comando", choices=["cotizar", "registrar", "ciclo"])
    parser.add_argument("archivo")
    args = parser.parse_args(argv)
    commands = {"cotizar": cotizar, "registrar": registrar, "ciclo": ciclo}
    try:
        commands[args.comando](args.archivo)
    except BusinessRuleError as error:
        print(f"RECHAZADO {error.code}: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
