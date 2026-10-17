"""Semana de demo (S-141..S-143): la 2026-W39 entregada y liquidada, y la 2026-W40 abierta con pedidos.

Todo se hace con los casos de uso, en el orden de una semana real, para que la conciliación dé 0.
Spec: docs/desarrollo/25-presentacion-web.md.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal as D

from . import fulfillment, reference
from .cycle import LIMA
from .domain import Customer
from .order_registration import quote_order, register_order, verify_payment
from .seed import pilot_store
from .store import InMemoryStore


DEMO_NOW = datetime(2026, 9, 30, 10, 0, tzinfo=LIMA)  # S-143: miércoles, ciclo 2026-W40 abierto
ADMIN = "admin-yapa"

W39_WEDNESDAY = datetime(2026, 9, 23, 10, 0, tzinfo=LIMA)
W39_PRICES_SEEN = datetime(2026, 9, 24, 18, 0, tzinfo=LIMA)
W39_SATURDAY = datetime(2026, 9, 26, 10, 0, tzinfo=LIMA)

# Vecinos ficticios (S-141)
DEMO_CUSTOMERS = [
    Customer(106, "Lucía Ramos", "Z-LINCE-01"),
    Customer(107, "Pedro Huamán", "Z-LINCE-01"),
    Customer(108, "Elena Vargas", "Z-LINCE-01"),
    Customer(109, "Miguel Chávez", "Z-LINCE-01"),
    Customer(110, "Sofía Mendoza", "Z-LINCE-01"),
    Customer(111, "Raúl Paredes", "Z-LINCE-01"),
    Customer(112, "Teresa Flores", "Z-LINCE-01"),
    Customer(113, "Julio Castro", "Z-JM-01"),
    Customer(114, "Rosa Medina", "Z-JM-01"),
]

BASKETS = [
    {"PAPA-AMARILLA": "5", "PAPA-BLANCA": "10", "CEBOLLA-ROJA": "10"},
    {"PAPA-AMARILLA": "8", "CEBOLLA-ROJA": "5", "LIMON": "4", "AJO": "1", "ZANAHORIA": "5"},
    {"PAPA-BLANCA": "10", "CAMOTE": "6", "ZANAHORIA": "6", "LIMON": "3", "LIMPIATODO-GALON": "2"},
    {"PAPA-AMARILLA": "6", "CEBOLLA-ROJA": "6", "AJO": "0.5", "DETERGENTE-LIQUIDO-GALON": "1"},
]

# Plaza Vea, 24/09/2026 (docs/analisis/08_validacion_economica.md). Sin precios de mercado: no se midieron.
SUPERMARKET = {"PAPA-BLANCA": "2.39", "PAPA-AMARILLA": "7.99", "CEBOLLA-ROJA": "3.89", "AJO": "16.49",
               "LIMON": "4.29", "CAMOTE": "3.39", "ZANAHORIA": "3.69"}


def _order(store: InMemoryStore, customer_id: int, basket: dict, now: datetime):
    lines = list(basket.items())
    total = quote_order(store, lines).total
    return register_order(store, customer_id=customer_id, lines=lines, payment_method="YAPE",
                          operation_code=f"DEMO-{now:%V}-{customer_id}", amount=total, now=now)


def demo_store() -> InMemoryStore:
    store = pilot_store()
    for customer in DEMO_CUSTOMERS:
        store.add_customer(customer)

    # Semana 2026-W39: Lince llega al mínimo; Jesús María no (vuelve todo)
    w39 = [101, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]
    for i, customer_id in enumerate(w39):
        order = _order(store, customer_id, BASKETS[i % len(BASKETS)], W39_WEDNESDAY)
        verify_payment(store, order.order_id, now=W39_WEDNESDAY)
    for product_id, price in SUPERMARKET.items():
        reference.register_reference(store, product_id, "SUPERMERCADO", D(price), "Plaza Vea", date(2026, 9, 24),
                                     by=ADMIN, now=W39_PRICES_SEEN)
    for order in store.orders_in_cycle("2026-W39"):
        if fulfillment.is_attended(store, order):
            fulfillment.pack_bag(store, order.order_id, by=ADMIN, photo=f"fotos/w39-pedido-{order.order_id}.jpg",
                                 now=W39_SATURDAY)
    fulfillment.deliver_zone(store, "2026-W39", "Z-LINCE-01", by=ADMIN, photo="fotos/w39-entrega-alamos.jpg",
                             received_by="Portería Los Álamos", now=W39_SATURDAY)
    fulfillment.close_cycle(store, "2026-W39", at=W39_SATURDAY)

    # Desde la 2026-W40, Ana (101) organiza Los Álamos (AZ-01, AZ-02) e invitó a Diana (AZ-06)
    alamos = store.zones["Z-LINCE-01"]
    alamos.admin_id, alamos.created_cycle = 101, "2026-W40"
    alamos.reception_kind, alamos.reception_contact = "PORTERIA", "Portería Los Álamos"
    store.add_customer(Customer(115, "Diana Rojas", "Z-LINCE-01", referred_by=101))

    # Semana 2026-W40, abierta: Ana (101) queda libre para pedir en vivo
    for i, customer_id in enumerate([105, 106, 107, 108, 109, 110, 115]):
        order = _order(store, customer_id, BASKETS[(i + 1) % len(BASKETS)], DEMO_NOW)
        if i < 4:
            verify_payment(store, order.order_id, now=DEMO_NOW)
    return store
