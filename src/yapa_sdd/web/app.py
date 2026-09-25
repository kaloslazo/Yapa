"""Aplicación web (WSGI, solo biblioteca estándar). Adaptador: no tiene reglas de negocio.

Specs: docs/desarrollo/09-interfaz-web.md y 10-acceso.md.
"""

from __future__ import annotations

import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from http.cookies import SimpleCookie
from urllib.parse import parse_qs

from .. import auth, cycle, wallet
from ..domain import BusinessRuleError
from ..order_changes import cancel_order
from ..order_registration import quote_order, register_order, verify_payment
from ..settlement import settle_cycle
from ..store import InMemoryStore
from . import views


COOKIE = "yapa_sesion"
SESSION_TIME = timedelta(hours=8)  # S-69


@dataclass
class Session:
    principal: object  # número de cliente (vecino) o usuario (admin)
    role: str  # "vecino" o "admin"
    csrf: str
    expires: datetime


class Response(Exception):
    """Respuesta directa (redirección o error de acceso)."""

    def __init__(self, status: str, html: str = "", headers=None):
        super().__init__(status)
        self.status = status
        self.html = html
        self.headers = headers or []


def _redirect(location: str, headers=None) -> Response:
    return Response("303 See Other", "", [("Location", location)] + (headers or []))


def _form(environ) -> dict[str, str]:
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        length = 0
    raw = environ["wsgi.input"].read(length).decode("utf-8") if length else ""
    return {key: values[0] for key, values in parse_qs(raw, keep_blank_values=True).items()}


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
    sessions: dict[str, Session] = {}

    def current_session(environ) -> tuple[str | None, Session | None]:
        cookie = SimpleCookie(environ.get("HTTP_COOKIE", ""))
        token = cookie[COOKIE].value if COOKIE in cookie else None
        session = sessions.get(token) if token else None
        if session and clock() >= session.expires:
            del sessions[token]
            session = None
        return token, session

    # --- páginas públicas ---

    def home(environ, form, session):
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
        csrf = session.csrf if session and session.role == "vecino" else None
        return views.home(cycle_id, cycle.is_open(now), rows, csrf)

    def entrar_form(environ, form, session):
        return views.login()

    def entrar(environ, form, session):
        kind = form.get("tipo") if form.get("tipo") in ("vecino", "admin") else "vecino"
        principal = auth.authenticate(store, kind, form.get("usuario", ""), form.get("secreto", ""), clock())
        token = secrets.token_urlsafe(32)
        sessions[token] = Session(principal, kind, secrets.token_urlsafe(16), clock() + SESSION_TIME)
        cookie = f"{COOKIE}={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={int(SESSION_TIME.total_seconds())}"
        raise _redirect("/admin" if kind == "admin" else "/cuenta", [("Set-Cookie", cookie)])

    def salir(environ, form, session):
        token, _ = current_session(environ)
        sessions.pop(token, None)
        raise _redirect("/", [("Set-Cookie", f"{COOKIE}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0")])

    # --- vecino (AC-04: el cliente siempre es el de la sesión) ---

    def cotizar(environ, form, session):
        return views.quote(quote_order(store, _lines(form), cycle.cycle_id(clock())), session.csrf)

    def pedidos(environ, form, session):
        order = register_order(
            store,
            customer_id=session.principal,
            lines=_lines(form),
            payment_method=form.get("metodo") or None,
            operation_code=form.get("codigo") or None,
            amount=form.get("monto") or "0",
            use_balance=form.get("saldo") or "0",
            now=clock(),
        )
        return views.registered(order, session.csrf)

    def cuenta(environ, form, session):
        customer_id = session.principal
        customer = store.customers[customer_id]
        orders = [o for o in store.orders.values() if o.customer_id == customer_id]
        refunds = [r for r in store.refunds.values() if r.customer_id == customer_id and r.status == "PENDIENTE"]
        return views.account(customer, wallet.balance(store, customer_id), orders, refunds, session.csrf)

    def cancelar(environ, form, session):
        order = cancel_order(store, _int(form.get("pedido", ""), "Número de pedido"),
                             customer_id=session.principal, now=clock(),
                             refund_to=form.get("destino") or "MEDIO_DE_PAGO")
        return views.simple("Pedido cancelado", f"El pedido {order.order_id} quedó {order.status}.", session.csrf)

    def cambiar_pin(environ, form, session):
        auth.change_pin(store, session.principal, form.get("actual", ""), form.get("nuevo", ""), clock())
        return views.simple("PIN actualizado", "Tu PIN se cambió correctamente.", session.csrf)

    # --- administrador (AC-05) ---

    def admin(environ, form, session):
        cycle_id = cycle.cycle_id(clock())
        pending = [o for o in store.orders_in_cycle(cycle_id)
                   if o.status == "REGISTRADO" and o.payment_status == "POR_VERIFICAR"]
        return views.admin(cycle_id, pending, session.csrf)

    def verificar(environ, form, session):
        order = verify_payment(store, _int(form.get("pedido", ""), "Número de pedido"), now=clock())
        return views.simple("Pago verificado", f"El pago del pedido {order.order_id} quedó {order.payment_status}.",
                            session.csrf)

    def liquidar(environ, form, session):
        return views.settlement(settle_cycle(store, (form.get("ciclo") or "").strip(), at=clock()), session.csrf)

    # ruta -> método -> (función, rol requerido)
    routes = {
        "/": {"GET": (home, None)},
        "/entrar": {"GET": (entrar_form, None), "POST": (entrar, None)},
        "/salir": {"POST": (salir, None)},
        "/cotizar": {"POST": (cotizar, "vecino")},
        "/pedidos": {"POST": (pedidos, "vecino")},
        "/cuenta": {"GET": (cuenta, "vecino")},
        "/cuenta/cancelar": {"POST": (cancelar, "vecino")},
        "/cuenta/pin": {"POST": (cambiar_pin, "vecino")},
        "/admin": {"GET": (admin, "admin")},
        "/admin/verificar": {"POST": (verificar, "admin")},
        "/admin/liquidar": {"POST": (liquidar, "admin")},
    }

    def dispatch(environ):
        path = environ.get("PATH_INFO") or "/"
        method = environ.get("REQUEST_METHOD", "GET")
        methods = routes.get(path)
        if methods is None:  # WB-08
            return "404 Not Found", views.simple("No encontrado", "Esa página no existe."), []
        if method not in methods:
            return "405 Method Not Allowed", views.simple("Método no permitido", "Usa el formulario."), []
        handler, role = methods[method]
        _, session = current_session(environ)
        form = _form(environ) if method == "POST" else {}
        if role and session is None:  # AC-04, AC-05
            raise _redirect("/entrar")
        if role and session.role != role:
            raise Response("403 Forbidden", views.simple("Sin permiso", "Esta página no es para tu tipo de cuenta."))
        if method == "POST" and session and path != "/entrar":  # AC-06
            if not hmac.compare_digest(form.get("csrf", ""), session.csrf):
                raise Response("403 Forbidden", views.simple("Formulario vencido", "Recarga la página e intenta de nuevo."))
        try:
            return "200 OK", handler(environ, form, session), []
        except BusinessRuleError as error:
            if path == "/entrar":
                return "422 Unprocessable Entity", views.login(views.error_box(error.code, str(error))), []
            csrf = session.csrf if session else None
            return "422 Unprocessable Entity", views.page("No se pudo", views.error_box(error.code, str(error)), csrf), []

    def app(environ, start_response):
        try:
            status, html, headers = dispatch(environ)
        except Response as response:
            status, html, headers = response.status, response.html, response.headers
        body = html.encode("utf-8")
        start_response(status, [("Content-Type", "text/html; charset=utf-8"),
                                ("Content-Length", str(len(body)))] + headers)
        return [body]

    return app
