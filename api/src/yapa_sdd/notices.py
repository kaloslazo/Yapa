"""Iteración 42: avisos dentro de la app y por correo.

Spec: docs/desarrollo/42-avisos.md. Ninguna función mueve dinero. Un aviso solo lo ve su dueño (AV-06).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from .domain import BusinessRuleError
from .store import InMemoryStore

MAX_PER_CUSTOMER = 50  # S-218
EMAIL_KINDS = frozenset({"LIQUIDADO", "ENTREGADO", "NO_ENTREGADO", "RECLAMO_APROBADO", "RECLAMO_RECHAZADO",
                         "DEVOLUCION_PAGADA", "UNION_SOLICITADA"})  # S-217
FAILURE_TEXT = {"PORTERIA_CERRADA": "la portería estaba cerrada", "NADIE_RECIBE": "no había nadie para recibirlo",
                "PORTERIA_RECHAZA": "la portería no aceptó recibirlo"}


@dataclass
class Notice:
    notice_id: int
    customer_id: int
    kind: str
    title: str
    body: str
    created_at: datetime
    read_at: datetime | None = None
    email: str = ""  # "", "PENDIENTE" o "ENVIADO" (AV-08)


def _money(value) -> str:
    return f"{Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"


def _newest_first(notice: Notice) -> tuple:
    return notice.created_at, notice.notice_id


def _wants_email(store: InMemoryStore, customer_id: int) -> bool:
    customer = store.customers.get(customer_id)
    return bool(customer and customer.email and customer.email_verified_at is not None and customer.email_notices)


def add(store: InMemoryStore, customer_id: int, kind: str, title: str, body: str, now: datetime) -> Notice:
    """AV-05, AV-07, AV-08."""
    pending = kind in EMAIL_KINDS and _wants_email(store, customer_id)
    notice = Notice(store.next_notice_id(), customer_id, kind, title, body, now, email="PENDIENTE" if pending else "")
    store.notices.append(notice)
    mine = sorted((n for n in store.notices if n.customer_id == customer_id), key=_newest_first)
    if len(mine) > MAX_PER_CUSTOMER:
        dropped = {n.notice_id for n in mine[:len(mine) - MAX_PER_CUSTOMER]}
        store.notices[:] = [n for n in store.notices if n.notice_id not in dropped]
    return notice


def for_customer(store: InMemoryStore, customer_id: int) -> list[Notice]:
    """AV-01: los más nuevos primero."""
    return sorted((n for n in store.notices if n.customer_id == customer_id), key=_newest_first, reverse=True)


def unread_count(store: InMemoryStore, customer_id: int) -> int:
    return sum(1 for n in store.notices if n.customer_id == customer_id and n.read_at is None)


def mark_read(store: InMemoryStore, customer_id: int, notice_id: int | None, now: datetime) -> None:
    """AV-02: un aviso o todos; solo los propios."""
    mine = [n for n in store.notices if n.customer_id == customer_id]
    if notice_id is not None:
        mine = [n for n in mine if n.notice_id == notice_id]
        if not mine:
            raise BusinessRuleError("NOTICE_NOT_FOUND", "Ese aviso no existe.")
    for notice in mine:
        if notice.read_at is None:
            notice.read_at = now


def set_email_preference(store: InMemoryStore, customer_id: int, enabled: bool) -> None:
    """AV-03."""
    store.customers[customer_id] = replace(store.customers[customer_id], email_notices=bool(enabled))


def claim_emails(store: InMemoryStore) -> list[tuple[str, str, str]]:
    """AV-08, S-219: los correos que toca mandar. Cada aviso se reclama una sola vez, salga bien o mal el envío.

    Se vuelve a mirar el correo y la preferencia: si ya no hay correo verificado, el aviso se queda solo en la app.
    """
    batch = []
    for notice in store.notices:
        if notice.email != "PENDIENTE":
            continue
        if not _wants_email(store, notice.customer_id):
            notice.email = ""
            continue
        customer = store.customers[notice.customer_id]
        first_name = customer.name.split()[0]
        body = (f"Hola {first_name},\n\n{notice.body}\n\nEntra a Yapa para ver el detalle.\n"
                "Si no quieres recibir estos correos, apágalos en Mi cuenta.\n\nYapa")
        batch.append((customer.email, notice.title, body))
        notice.email = "ENVIADO"
    return batch


# --- los hechos que avisan (S-216) ---


def payment_verified(store: InMemoryStore, order, now: datetime) -> None:
    add(store, order.customer_id, "PAGO_VERIFICADO", "Verificamos tu pago",
        f"Tu pago del pedido {order.order_id} de la semana {order.cycle} está verificado. "
        "Ya cuenta para que tu grupo llegue al mínimo.", now)


def _settled_text(settled) -> str:
    refund, to_balance = settled.refund_amount, settled.returned_to_balance
    if settled.status == "CANCELADO":  # el pago nunca se verificó
        text = "No pudimos verificar tu pago a tiempo, así que tu pedido de esta semana no entró en la compra."
        return f"{text} Te devolvimos S/ {_money(to_balance)} a tu saldo." if to_balance > 0 else text
    if settled.status == "NO_ATENDIDO":
        text = "Tu zona no llegó al mínimo de pedidos esta semana, así que no compramos tu pedido."
        if refund > 0 and to_balance > 0:
            return f"{text} Te devolvemos S/ {_money(refund)} a tu Yape o Plin y S/ {_money(to_balance)} a tu saldo."
        if refund > 0:
            return f"{text} Te devolvemos S/ {_money(refund)} a tu Yape o Plin."
        return f"{text} Te devolvimos S/ {_money(to_balance)} a tu saldo."
    back = refund + to_balance
    if settled.status == "NO_ENTREGADO":
        return f"No pudimos entregar tu pedido. Te devolvimos S/ {_money(back)} a tu saldo."
    text = f"Pagaste S/ {_money(settled.paid)} y tu pedido costó S/ {_money(settled.final_amount)}."
    return f"{text} Te devolvimos S/ {_money(back)} a tu saldo." if back > 0 else text


def cycle_settled(store: InMemoryStore, settlement, now: datetime) -> None:
    for settled in settlement.orders.values():
        add(store, store.orders[settled.order_id].customer_id, "LIQUIDADO",
            f"Cerramos tu pedido de la semana {settlement.cycle}", _settled_text(settled), now)


def delivered(store: InMemoryStore, delivery, now: datetime) -> None:
    zone = store.zones[delivery.zone_id].name
    for order_id in delivery.order_ids:
        add(store, store.orders[order_id].customer_id, "ENTREGADO", "Tu pedido llegó a tu zona",
            f"Tu pedido {order_id} de la semana {delivery.cycle} ya está en {zone}. Lo recibió {delivery.received_by}.", now)


def in_building(store: InMemoryStore, received, now: datetime) -> None:
    """PO-04, S-294: quien recibe en la zona confirmó que las bolsas están en el edificio."""
    zone = store.zones[received.zone_id].name
    for order_id in received.order_ids:
        add(store, store.orders[order_id].customer_id, "EN_EDIFICIO", "Tus bolsas ya están en el edificio",
            f"Tu pedido {order_id} de la semana {received.cycle} ya está en {zone}. Pásalo a recoger cuando puedas.", now)


def delivery_failed(store: InMemoryStore, failure, now: datetime) -> None:
    zone = store.zones[failure.zone_id].name
    why = FAILURE_TEXT.get(failure.reason, "no se pudo recibir")
    for order_id in failure.order_ids:
        add(store, store.orders[order_id].customer_id, "NO_ENTREGADO", "No pudimos entregar tu pedido",
            f"No pudimos entregar tu pedido {order_id} en {zone}: {why}. "
            "Cuando cerremos la semana te devolvemos lo que pagaste.", now)


def claim_reviewed(store: InMemoryStore, claim, now: datetime) -> None:
    if claim.status == "APROBADO":
        add(store, claim.customer_id, "RECLAMO_APROBADO", "Aprobamos tu reclamo",
            f"Aprobamos tu reclamo del pedido {claim.order_id}. Te devolvimos S/ {_money(claim.refund_amount)} a tu saldo.", now)
    else:
        add(store, claim.customer_id, "RECLAMO_RECHAZADO", "No pudimos aprobar tu reclamo",
            f"Revisamos tu reclamo del pedido {claim.order_id} y no pudimos aprobarlo.", now)


def refund_paid(store: InMemoryStore, refund, now: datetime) -> None:
    add(store, refund.customer_id, "DEVOLUCION_PAGADA", f"Te devolvimos S/ {_money(refund.amount)}",
        f"Ya hicimos la transferencia de S/ {_money(refund.amount)} a tu Yape o Plin.", now)


def merge_requested(store: InMemoryStore, requester, target, now: datetime) -> None:
    if target is None or target.admin_id is None or requester is None:
        return
    add(store, target.admin_id, "UNION_SOLICITADA", f"La zona {requester.name} quiere unirse a la tuya",
        "Si aceptan, sus pedidos suman juntos para llegar al mínimo del grupo. Respóndelo en Mi zona.", now)


def merge_answered(store: InMemoryStore, requester, target, accepted: bool, now: datetime) -> None:
    if requester is None or target is None or requester.admin_id is None:
        return
    if accepted:
        add(store, requester.admin_id, "UNION_ACEPTADA", "Tu pedido de unión fue aceptado",
            f"{target.name} aceptó. Desde ahora sus pedidos suman juntos con los de tu zona.", now)
    else:
        add(store, requester.admin_id, "UNION_RECHAZADA", "Tu pedido de unión fue rechazado",
            f"{target.name} no aceptó unirse por ahora.", now)


def neighbor_joined(store: InMemoryStore, customer, inviter, zone, now: datetime) -> None:
    """IN-07, S-242: quien invitó y el admin de la zona (si es otra persona) saben que llegó alguien. Solo en la app."""
    first = (customer.name.split() or [""])[0]
    add(store, inviter.customer_id, "VECINO_NUEVO", f"{first} se unió con tu enlace",
        "Ya forma parte de tu zona. Lo ves en Mi zona.", now)
    if zone.admin_id is not None and zone.admin_id != inviter.customer_id:
        add(store, zone.admin_id, "VECINO_NUEVO", f"{first} se unió a tu zona",
            f"Llegó con el enlace de {(inviter.name.split() or [''])[0]}. Lo ves en Mi zona.", now)
