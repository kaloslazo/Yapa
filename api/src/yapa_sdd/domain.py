"""Datos del negocio y constantes del piloto de Yapa (iteración 2)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_UP


PILOT_DISTRICTS = frozenset({"Lince", "Jesús María", "La Victoria"})  # S-01
MIN_SUBTOTAL = Decimal("50.00")  # S-04
MAX_DELIVERY_FEE = Decimal("5.00")  # S-05
MIN_ORDERS_PER_GROUP = 8  # S-06
COMMISSION = {"FRESCOS": Decimal("0.12"), "LIMPIEZA": Decimal("0.09")}  # S-07
MAX_QUANTITY = {"kg": Decimal("10"), "unidad": Decimal("6")}  # S-08
PAYMENT_METHODS = frozenset({"YAPE", "PLIN"})  # C-03


class BusinessRuleError(ValueError):
    """Error observable: el código es el contrato, el mensaje es para el cliente."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def is_multiple(value: Decimal, step: Decimal) -> bool:
    """AD-03: un número tan grande que no cabe en la división no es múltiplo de nada."""
    try:
        return value % step == 0
    except InvalidOperation:
        return False


def floor_cents(value: Decimal) -> Decimal:
    """S-09: redondea al céntimo a favor del cliente cuando es un cobro."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def ceil_cents(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_UP)


@dataclass(frozen=True)
class PriceTier:
    min_quantity: Decimal
    base_price: Decimal


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    category: str
    unit: str
    step: Decimal
    max_available: Decimal
    tiers: tuple[PriceTier, ...]
    active: bool = True
    supplier_id: str | None = None

    def price_with_commission(self, base_price: Decimal) -> Decimal:
        return base_price * (1 + COMMISSION[self.category])

    def max_unit_price(self) -> Decimal:
        """RP-09: primer tramo del proveedor más la comisión."""
        return self.price_with_commission(self.tiers[0].base_price)

    def tier_for(self, total_quantity: Decimal) -> PriceTier:
        """LQ-04: el mayor tramo alcanzado por la cantidad total."""
        reached = [tier for tier in self.tiers if tier.min_quantity <= total_quantity]
        if not reached:
            return self.tiers[0]
        return max(reached, key=lambda tier: tier.min_quantity)


@dataclass(frozen=True)
class Supplier:
    supplier_id: str
    name: str
    allied: bool = True


@dataclass
class Zone:
    zone_id: str
    name: str
    district: str
    group_id: str
    stop_cost: Decimal
    reception_accepted: bool = True
    lat: float | None = None
    lon: float | None = None
    admin_id: int | None = None
    reception_kind: str = ""
    reception_contact: str = ""
    created_cycle: str | None = None  # S-159: semana en que se creó la zona

    @property
    def status(self) -> str:
        return "ACTIVA" if self.reception_accepted else "PENDIENTE_RECEPCION"


@dataclass(frozen=True)
class Customer:
    customer_id: int
    name: str
    zone_id: str
    suspended: bool = False
    lat: float | None = None
    lon: float | None = None
    phone: str | None = None  # S-134
    consent_at: datetime | None = None  # S-133, Ley 29733
    referred_by: int | None = None  # S-162: quién lo invitó
    email: str | None = None  # S-201: obligatorio en el alta
    email_verified_at: datetime | None = None  # S-202: solo un correo verificado sirve para recuperar
    google_sub: str | None = None  # S-211: identificador estable de su cuenta de Google
    email_notices: bool = True  # S-217: quiere también los avisos importantes por correo
    withdrawn_at: datetime | None = None  # S-304: retiró su consentimiento; sus datos se anonimizaron


@dataclass(frozen=True)
class OrderLine:
    product_id: str
    quantity: Decimal
    max_unit_price: Decimal

    @property
    def max_total(self) -> Decimal:
        return self.max_unit_price * self.quantity


@dataclass
class Payment:
    """Un pago del pedido: SALDO, YAPE o PLIN (S-13)."""

    method: str
    amount: Decimal
    operation_code: str = ""
    status: str = "POR_VERIFICAR"


@dataclass
class Order:
    order_id: int
    cycle: str
    customer_id: int
    zone_id: str
    lines: list[OrderLine]
    subtotal: Decimal
    delivery_fee: Decimal
    total: Decimal
    payments: list[Payment]
    status: str = "REGISTRADO"
    registered_at: datetime | None = None  # S-310: hora del registro, para el seguimiento

    @property
    def payment_status(self) -> str:
        if all(payment.status == "VERIFICADO" for payment in self.payments):
            return "VERIFICADO"
        return "POR_VERIFICAR"

    @property
    def external_payment(self) -> Payment | None:
        for payment in self.payments:
            if payment.method != "SALDO":
                return payment
        return None

    @property
    def payment_method(self) -> str:
        external = self.external_payment
        return external.method if external else "SALDO"

    @property
    def operation_code(self) -> str:
        external = self.external_payment
        return external.operation_code if external else ""

    @property
    def paid_with_balance(self) -> Decimal:
        return sum((p.amount for p in self.payments if p.method == "SALDO"), Decimal("0"))

    @property
    def paid_external(self) -> Decimal:
        return sum((p.amount for p in self.payments if p.method != "SALDO"), Decimal("0"))
