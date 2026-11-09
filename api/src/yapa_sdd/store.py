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
        self.email_codes: dict = {}  # códigos de correo: (cliente, motivo) -> resumen, vencimiento, envíos (iteración 40)
        self.notices: list = []  # avisos dentro de la app (iteración 42)
        self.demo_now = None  # reloj de la demostración: miércoles 10:00 de la semana sembrada (iteración 48, S-254)
        self.debug_admins: set = set()  # admins que pueden "ver como" (S-256)
        self.debug_log: list = []  # quién vio como quién y cuándo (S-257)
        self.invites: dict = {}  # enlaces de invitación: código al azar -> dueño, si vale, registros (iteración 45)
        self.signups: dict = {}  # registros a medio hacer, por correo (iteración 45)
        self.pin_requests: dict = {}  # "Olvidé mi PIN": id -> (cliente, hora) (iteración 39, S-199)
        self.settlements: dict = {}  # resultado de la liquidación por ciclo (iteración 7)
        self.bags: dict = {}  # armado: bolsas por pedido
        self.deliveries: dict = {}  # entrega: (ciclo, zona) -> entrega
        self.cash_in: list = []  # registro de caja (iteración 19, S-114)
        self.failed_deliveries: dict = {}  # entrega fallida: (ciclo, zona) -> falla (iteración 16)
        self.claims: dict = {}  # reclamos por artículo
        self.buffer: dict = {}  # colchón de reposición por producto
        self.buffer_uses: list = []  # S-122: a qué pedido fue cada reposición
        self.reference_prices: list = []  # S-125: precios del mercado y del supermercado
        self.partners: dict = {}  # cuentas de proveedores, transportistas y personal por usuario (iteraciones 54 y 55)
        self.supplier_offers: dict = {}  # lista propuesta por el proveedor: (ciclo, proveedor) -> propuesta (S-284)
        self.receptions: dict = {}  # recepción en el edificio: (ciclo, zona) -> confirmación (iteración 55, S-294)
        self.purchases: dict = {}  # compra real: ciclo -> lo que llegó del proveedor (iteración 56, S-295)
        self.shortages: list = []  # faltantes de compra y dañados al armar, por pedido (S-296, S-297)
        self.incidents: dict = {}  # incidencias de atención (S-300)
        self._next_claim_id = 1
        self._next_zone_number = 1
        self._next_merge_id = 1
        self._next_order_id = 1
        self._next_refund_id = 1
        self._next_notice_id = 1
        self._next_incident_id = 1

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

    def next_notice_id(self) -> int:
        notice_id = self._next_notice_id
        self._next_notice_id += 1
        return notice_id

    def next_claim_id(self) -> int:
        claim_id = self._next_claim_id
        self._next_claim_id += 1
        return claim_id

    def save_new_order(self, order: Order) -> Order:
        order.order_id = self._next_order_id
        self._next_order_id += 1
        self.orders[order.order_id] = order
        return order
