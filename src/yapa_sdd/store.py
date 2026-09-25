"""Repositorio en memoria del ciclo (reemplazable por una base de datos)."""

from __future__ import annotations

from decimal import Decimal

from .domain import Customer, Order, Product, Supplier, Zone


class InMemoryStore:
    def __init__(self) -> None:
        self.customers: dict[int, Customer] = {}
        self.zones: dict[str, Zone] = {}
        self.products: dict[str, Product] = {}
        self.orders: dict[int, Order] = {}
        self.reserved: dict[tuple[str, str], Decimal] = {}  # (ciclo, producto), S-35
        self.catalogs: dict[str, dict[str, Product]] = {}  # catálogo por ciclo (iteración 6)
        self.admins: set[str] = set()
        self.credentials: dict = {}  # acceso (iteración 10)
        self.suppliers: dict[str, Supplier] = {}
        self.used_codes: set[str] = set()
        self.movements: list = []  # billetera (iteración 3)
        self.refunds: dict = {}
        self.settled_cycles: set[str] = set()
        self.merge_requests: dict = {}  # zonas (iteración 5)
        self.settlements: dict = {}  # resultado de la liquidación por ciclo (iteración 7)
        self.bags: dict = {}  # armado: bolsas por pedido
        self.deliveries: dict = {}  # entrega: (ciclo, zona) -> entrega
        self.failed_deliveries: dict = {}  # entrega fallida: (ciclo, zona) -> falla (iteración 16)
        self.claims: dict = {}  # reclamos por artículo
        self.buffer: dict = {}  # colchón de reposición por producto
        self._next_claim_id = 1
        self._next_zone_number = 1
        self._next_merge_id = 1
        self._next_order_id = 1
        self._next_refund_id = 1

    def add_customer(self, customer: Customer) -> None:
        self.customers[customer.customer_id] = customer

    def add_zone(self, zone: Zone) -> None:
        self.zones[zone.zone_id] = zone

    def add_product(self, product: Product) -> None:
        self.products[product.product_id] = product

    def add_supplier(self, supplier: Supplier) -> None:
        self.suppliers[supplier.supplier_id] = supplier

    def catalog_for(self, cycle: str | None) -> dict[str, Product]:
        """CT-10: catálogo publicado del ciclo; si no hay, el catálogo base (S-37)."""
        return self.catalogs.get(cycle, self.products)

    def reserved_quantity(self, product_id: str, cycle: str | None) -> Decimal:
        return self.reserved.get((cycle, product_id), Decimal("0"))

    def reserve(self, product_id: str, quantity: Decimal, cycle: str) -> None:
        self.reserved[(cycle, product_id)] = self.reserved_quantity(product_id, cycle) + quantity

    def release(self, product_id: str, quantity: Decimal, cycle: str) -> None:
        self.reserved[(cycle, product_id)] = self.reserved_quantity(product_id, cycle) - quantity

    def find_order(self, customer_id: int, cycle: str) -> Order | None:
        """Pedido activo del cliente en el ciclo (CE-06: los cancelados no cuentan)."""
        for order in self.orders.values():
            if (order.customer_id == customer_id and order.cycle == cycle
                    and order.status != "CANCELADO_POR_CLIENTE"):
                return order
        return None

    def orders_in_cycle(self, cycle: str) -> list[Order]:
        return [order for order in self.orders.values() if order.cycle == cycle]

    def next_zone_id(self) -> str:
        zone_id = f"Z-{self._next_zone_number:03d}"
        self._next_zone_number += 1
        return zone_id

    def next_merge_id(self) -> int:
        merge_id = self._next_merge_id
        self._next_merge_id += 1
        return merge_id

    def next_refund_id(self) -> int:
        refund_id = self._next_refund_id
        self._next_refund_id += 1
        return refund_id

    def next_claim_id(self) -> int:
        claim_id = self._next_claim_id
        self._next_claim_id += 1
        return claim_id

    def save_new_order(self, order: Order) -> Order:
        order.order_id = self._next_order_id
        self._next_order_id += 1
        self.orders[order.order_id] = order
        return order
