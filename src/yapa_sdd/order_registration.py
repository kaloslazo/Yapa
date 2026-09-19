"""Dominio mínimo de CUN-02: registrar pedido semanal de Yapa."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


MIN_SUBTOTAL = Decimal("50.00")
FREE_DELIVERY_FROM = Decimal("120.00")
DELIVERY_FEE = Decimal("7.90")
PILOT_DISTRICTS = frozenset({"Lince", "Jesús María", "La Victoria"})
PAYMENT_METHODS = frozenset({"TRANSFERENCIA", "BILLETERA_DIGITAL", "CONTRAENTREGA"})
DELIVERY_WINDOWS = frozenset({"SAT_09_12", "SAT_12_15", "SAT_15_18"})


class OrderRegistrationError(ValueError):
    """Error observable que corresponde a una regla de negocio."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CatalogItem:
    product_id: int
    name: str
    unit: str
    unit_price: Decimal
    active: bool
    valid_from: datetime
    valid_until: datetime


@dataclass(frozen=True)
class CustomerAddress:
    district: str
    validated: bool


@dataclass(frozen=True)
class DeliveryWindow:
    code: str
    capacity: int
    reserved: int


@dataclass(frozen=True)
class OrderLine:
    item: CatalogItem
    quantity: Decimal


@dataclass(frozen=True)
class RegisteredOrder:
    order_id: int
    status: str
    subtotal: Decimal
    delivery_fee: Decimal
    total: Decimal
    delivery_window: str
    payment_method: str


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_delivery_fee(subtotal: Decimal) -> Decimal:
    """RN-04: cobra delivery bajo S/ 120 y exonera desde ese monto."""
    return Decimal("0.00") if subtotal >= FREE_DELIVERY_FROM else DELIVERY_FEE


def _validate_address(address: CustomerAddress) -> None:
    if not address.validated or address.district not in PILOT_DISTRICTS:
        raise OrderRegistrationError(
            "ADDRESS_OUTSIDE_COVERAGE",
            "La dirección no está validada dentro de la cobertura piloto.",
        )


def _validate_cycle(now: datetime, cycle_start: datetime, cycle_close: datetime) -> None:
    if not cycle_start <= now <= cycle_close:
        raise OrderRegistrationError(
            "CYCLE_CLOSED",
            "El ciclo semanal no está recibiendo pedidos.",
        )


def _validate_item(line: OrderLine, now: datetime) -> None:
    if line.quantity <= 0 or not line.item.active:
        raise OrderRegistrationError(
            "PRODUCT_NOT_ACTIVE",
            "Cada línea debe tener un producto activo y una cantidad positiva.",
        )
    if not line.item.unit or not line.item.valid_from <= now <= line.item.valid_until:
        raise OrderRegistrationError(
            "PRICE_NOT_VALID",
            "El producto debe tener unidad y un precio vigente.",
        )


def _validate_window(window: DeliveryWindow) -> None:
    if window.code not in DELIVERY_WINDOWS or window.reserved >= window.capacity:
        raise OrderRegistrationError(
            "DELIVERY_WINDOW_FULL",
            "La ventana de entrega no existe o ya no tiene capacidad.",
        )


def _validate_payment_method(payment_method: str) -> None:
    if payment_method not in PAYMENT_METHODS:
        raise OrderRegistrationError(
            "PAYMENT_METHOD_NOT_ALLOWED",
            "El medio de pago no está habilitado para Yapa.",
        )


def register_weekly_order(
    *,
    order_id: int,
    address: CustomerAddress,
    lines: Iterable[OrderLine],
    delivery_window: DeliveryWindow,
    payment_method: str,
    now: datetime,
    cycle_start: datetime,
    cycle_close: datetime,
) -> RegisteredOrder:
    """Valida y construye el resultado de CUN-02.

    La función no persiste ni procesa pagos externos. Esas responsabilidades
    pertenecen a módulos posteriores del proyecto general.
    """
    _validate_address(address)
    _validate_cycle(now, cycle_start, cycle_close)
    _validate_window(delivery_window)
    _validate_payment_method(payment_method)

    validated_lines = list(lines)
    if not validated_lines:
        raise OrderRegistrationError(
            "PRODUCT_NOT_ACTIVE",
            "El pedido debe contener al menos un producto.",
        )
    for line in validated_lines:
        _validate_item(line, now)

    subtotal = _money(sum((line.item.unit_price * line.quantity for line in validated_lines), Decimal("0.00")))
    if subtotal < MIN_SUBTOTAL:
        raise OrderRegistrationError(
            "SUBTOTAL_BELOW_MINIMUM",
            "El subtotal mínimo para confirmar un pedido es S/ 50.00.",
        )

    delivery_fee = calculate_delivery_fee(subtotal)
    return RegisteredOrder(
        order_id=order_id,
        status="REGISTRADO",
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=_money(subtotal + delivery_fee),
        delivery_window=delivery_window.code,
        payment_method=payment_method,
    )

