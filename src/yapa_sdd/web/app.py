"""Aplicación web (WSGI, solo biblioteca estándar). Adaptador: no tiene reglas de negocio.

Spec: docs/desarrollo/09-interfaz-web.md.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from urllib.parse import parse_qs

from .. import cycle, wallet
from ..domain import BusinessRuleError
from ..order_changes import cancel_order
from ..order_registration import quote_order, register_order, verify_payment
from ..settlement import settle_cycle
from ..store import InMemoryStore
from . import views


class NotFound(Exception):
    pass


def _form(environ) -> dict[str, str]:
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        length = 0
    raw = environ["wsgi.input"].read(length).decode("utf-8") if length else ""
    return {key: values[0] for key, values in parse_qs(raw, keep_blank_values=True).items()}


def _query(environ) -> dict[str, str]:
    return {key: values[0] for key, values in parse_qs(environ.get("QUERY_STRING", "")).items()}


def _int(value: str, what: str) -> int:
    try:
        return int((value or "").strip())
    except ValueError:
        raise BusinessRuleError("INVALID_INPUT", f"{what} no válido.")


def _lines(form: dict[str, str]) -> list[tuple[str, str]]:
    """WB-02: solo cuentan las cantidades con valor distinto de 0."""
    lines = []
    for key, value in form.items():
        if key.startswith("cant_") and value.strip() and value.strip() != "0":
            lines.append((key[len("cant_"):], value.strip()))
    return lines


def create_app(store: InMemoryStore, clock=None):
    clock = clock or (lambda: datetime.now(cycle.LIMA))

    def home(environ):
        now = clock()
        cycle_id = cycle.cycle_id(now)
        catalog = store.catalog_for(cycle_id)
        ordered: dict[str, Decimal] = {}
        for order in store.orders_in_cycle(cycle_id):
            if order.status == "REGISTRADO":
                for line in order.lines:
                    ordered[line.product_id] = ordered.get(line.product_id, Decimal("0")) + line.quantity
        rows = []
        for product in catalog.values():
            if not product.active:
                continue
            total = ordered.get(product.product_id, Decimal("0"))
            following = [t for t in product.tiers if t.min_quantity > total]
            if following:
                tier = following[0]
                progress = (f"{views.qty(total)} de {views.qty(tier.min_quantity)} {product.unit} · desde "
                            f"{views.qty(tier.min_quantity)} {product.unit} baja a "
                            f"{views.money(product.price_with_commission(tier.base_price))}")
            else:
                progress = f"{views.qty(total)} {product.unit} pedidos · ya estamos en el mejor precio"
            rows.append({"product_id": product.product_id, "name": product.name, "unit": product.unit,
                         "step": product.step, "max_price": product.max_unit_price(), "progress": progress})
        return views.home(cycle_id, cycle.is_open(now), rows)

    def cotizar(environ):
        form = _form(environ)
        _int(form.get("cliente", ""), "Número de cliente")
        return views.quote(quote_order(store, _lines(form), cycle.cycle_id(clock())))

    def pedidos(environ):
        form = _form(environ)
        order = register_order(
            store,
            customer_id=_int(form.get("cliente", ""), "Número de cliente"),
            lines=_lines(form),
            payment_method=form.get("metodo") or None,
            operation_code=form.get("codigo") or None,
            amount=form.get("monto") or "0",
            use_balance=form.get("saldo") or "0",
            now=clock(),
        )
        return views.registered(order)

    def cuenta(environ):
        query = _query(environ)
        if "cliente" not in query:
            return views.ask_customer()
        try:
            customer_id = int(query["cliente"])
        except ValueError:
            raise NotFound()
        customer = store.customers.get(customer_id)
        if customer is None:
            raise NotFound()
        orders = [o for o in store.orders.values() if o.customer_id == customer_id]
        refunds = [r for r in store.refunds.values() if r.customer_id == customer_id and r.status == "PENDIENTE"]
        return views.account(customer, wallet.balance(store, customer_id), orders, refunds)

    def cancelar(environ):
        form = _form(environ)
        order = cancel_order(store, _int(form.get("pedido", ""), "Número de pedido"),
                             customer_id=_int(form.get("cliente", ""), "Número de cliente"), now=clock(),
                             refund_to=form.get("destino") or "MEDIO_DE_PAGO")
        return views.simple("Pedido cancelado", f"El pedido {order.order_id} quedó {order.status}.")

    def admin(environ):
        cycle_id = cycle.cycle_id(clock())
        pending = [o for o in store.orders_in_cycle(cycle_id)
                   if o.status == "REGISTRADO" and o.payment_status == "POR_VERIFICAR"]
        return views.admin(cycle_id, pending)

    def verificar(environ):
        form = _form(environ)
        order = verify_payment(store, _int(form.get("pedido", ""), "Número de pedido"), now=clock())
        return views.simple("Pago verificado", f"El pago del pedido {order.order_id} quedó {order.payment_status}.")

    def liquidar(environ):
        form = _form(environ)
        return views.settlement(settle_cycle(store, (form.get("ciclo") or "").strip(), at=clock()))

    routes = {
        "/": {"GET": home},
        "/cotizar": {"POST": cotizar},
        "/pedidos": {"POST": pedidos},
        "/cuenta": {"GET": cuenta},
        "/cuenta/cancelar": {"POST": cancelar},
        "/admin": {"GET": admin},
        "/admin/verificar": {"POST": verificar},
        "/admin/liquidar": {"POST": liquidar},
    }

    def app(environ, start_response):
        path = environ.get("PATH_INFO") or "/"
        method = environ.get("REQUEST_METHOD", "GET")
        handlers = routes.get(path)
        try:
            if handlers is None:  # WB-08
                raise NotFound()
            handler = handlers.get(method)
            if handler is None:
                status, html = "405 Method Not Allowed", views.simple("Método no permitido", "Usa el formulario.")
            else:
                status, html = "200 OK", handler(environ)
        except NotFound:
            status, html = "404 Not Found", views.simple("No encontrado", "Esa página o cliente no existe.")
        except BusinessRuleError as error:
            status, html = "422 Unprocessable Entity", views.page("No se pudo", views.error_box(error.code, str(error)))
        body = html.encode("utf-8")
        start_response(status, [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))])
        return [body]

    return app
