"""Aplicación web (WSGI, solo biblioteca estándar). Adaptador: no tiene reglas de negocio.

Specs: docs/desarrollo/09-interfaz-web.md, 10-acceso.md y 12-web-operacion.md.
"""

from __future__ import annotations

import hmac
import math
import re
import secrets
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from http.cookies import SimpleCookie
from urllib.parse import parse_qs

from .. import audit, auth, buffer, claims, cycle, fulfillment, metrics, reference, wallet, zones
from ..catalog import deactivate_product, export_catalog, parse_catalog, publish_catalog
from ..domain import PILOT_DISTRICTS, BusinessRuleError
from ..order_changes import cancel_order
from ..order_registration import quote_order, register_order, verify_payment
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


def _float(value: str, what: str) -> float:
    """S-76: una coordenada es un número finito."""
    try:
        number = float((value or "").strip())
    except ValueError:
        number = math.nan
    if not math.isfinite(number):
        raise BusinessRuleError("INVALID_INPUT", f"{what} no válida.")
    return number


def _money(value: str, what: str) -> Decimal:
    """S-76: un monto son soles con hasta 2 decimales."""
    value = (value or "").strip()
    if not re.fullmatch(r"\d+(\.\d{1,2})?", value):
        raise BusinessRuleError("INVALID_INPUT", f"{what} no válido.")
    return Decimal(value)


def _query(environ) -> dict[str, str]:
    return {key: values[0] for key, values in parse_qs(environ.get("QUERY_STRING", "")).items()}


def _lines(form: dict[str, str]) -> list[tuple[str, str]]:
    """WB-02: solo cuentan las cantidades con valor distinto de 0."""
    lines = []
    for key, value in form.items():
        if key.startswith("cant_") and value.strip() and value.strip() != "0":
            lines.append((key[len("cant_"):], value.strip()))
    return lines


def create_app(store: InMemoryStore, clock=None, on_change=None):
    """on_change(store) se llama después de cada POST que termina bien (PS-03)."""
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
            references = reference.current_references(store, product.product_id, cycle.to_lima(now).date())  # RF-06
            rows.append({"product_id": product.product_id, "name": product.name, "unit": product.unit,
                         "step": product.step, "max_price": product.max_unit_price(), "progress": progress,
                         "references": [references[k] for k in reference.KINDS if k in references]})
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
        # HR-10: se usa close_cycle (EF-06), que exige todas las zonas entregadas o fallidas
        result = fulfillment.close_cycle(store, (form.get("ciclo") or "").strip(), at=clock())
        return views.settlement(result, session.csrf)

    def ubicacion(environ, form, session):
        zones.set_location(store, session.principal, _float(form.get("lat"), "Latitud"),
                           _float(form.get("lon"), "Longitud"))  # HR-01
        return views.simple("Ubicación guardada", "Ya puedes crear una zona o unirte a una cercana.", session.csrf)

    def catalogo(environ, form, session):
        # CW-01, S-117: por defecto, el ciclo siguiente
        label = (_query(environ).get("ciclo") or "").strip() or cycle.add_weeks(cycle.cycle_id(clock()), 1)
        cycle.check_cycle_id(label)
        products = list(store.catalog_for(label).values())
        return views.catalog_admin(label, label in store.catalogs, products, export_catalog(products), session.csrf)

    def catalogo_publicar(environ, form, session):
        label = (form.get("ciclo") or "").strip()
        cycle.check_cycle_id(label)
        products = parse_catalog(form.get("lista", ""))  # CW-02
        published = publish_catalog(store, label, products, by=session.principal, now=clock())  # CW-03
        return views.simple("Catálogo publicado", f"El ciclo {label} tiene {len(published)} productos.",
                            session.csrf, back=f"/admin/catalogo?ciclo={label}")

    def catalogo_desactivar(environ, form, session):
        label = (form.get("ciclo") or "").strip()
        cycle.check_cycle_id(label)
        product = deactivate_product(store, label, form.get("producto", "").strip(), by=session.principal)  # CW-04
        return views.simple("Producto desactivado", f"{product.name} ya no recibe pedidos en {label}.",
                            session.csrf, back=f"/admin/catalogo?ciclo={label}")

    def referencias(environ, form, session):
        today = cycle.to_lima(clock()).date()
        products = [p for p in store.catalog_for(cycle.cycle_id(clock())).values() if p.active]
        rows = [(p, reference.current_references(store, p.product_id, today)) for p in products]
        return views.references_page(rows, session.csrf)  # RF-07

    def referencia_registrar(environ, form, session):
        try:
            observed = date.fromisoformat((form.get("fecha") or "").strip())
        except ValueError:
            raise BusinessRuleError("INVALID_INPUT", "Fecha no válida; usa el formato AAAA-MM-DD.")
        saved = reference.register_reference(store, form.get("producto", "").strip(), form.get("tipo", "").strip(),
                                             _money(form.get("precio", ""), "Precio"), form.get("fuente", ""),
                                             observed, by=session.principal, now=clock())
        return views.simple("Precio registrado", f"{saved.product_id}: {views.money(saved.price)} en {saved.source}.",
                            session.csrf, back="/admin/referencias")

    def conciliacion(environ, form, session):
        return views.balance_page(audit.money_balance(store), session.csrf)  # AU-03

    def devoluciones(environ, form, session):
        pending = [r for r in store.refunds.values() if r.status == "PENDIENTE"]
        return views.refunds_page(pending, session.csrf)

    def devolucion_pagar(environ, form, session):
        refund = wallet.mark_refund_paid(store, _int(form.get("reembolso", ""), "Número de devolución"),
                                         form.get("codigo", ""))  # HR-08
        return views.simple("Devolución pagada", f"La devolución {refund.refund_id} quedó {refund.status}.",
                            session.csrf)

    def entrega_fallida(environ, form, session):
        failure = fulfillment.register_failed_delivery(store, (form.get("ciclo") or "").strip(),
                                                       form.get("zona", "").strip(), by=session.principal,
                                                       photo=form.get("foto", ""), reason=form.get("motivo", ""),
                                                       now=clock())  # HR-09
        return views.simple("Entrega fallida registrada",
                            f"Zona {failure.zone_id}: {len(failure.order_ids)} pedidos vuelven como saldo al liquidar.",
                            session.csrf)

    # --- vecino: zona, devolución y reclamos (iteración 12) ---

    def zona(environ, form, session):
        customer = store.customers[session.principal]
        administered = [z for z in store.zones.values() if z.admin_id == session.principal]
        admin_zone = administered[0] if administered else None
        requests = [(merge_id, zone_id) for merge_id, (zone_id, target_id) in store.merge_requests.items()
                    if admin_zone and target_id == admin_zone.zone_id]
        return views.zone_page(customer, store.zones.get(customer.zone_id), list(store.zones.values()), admin_zone,
                               requests, sorted(PILOT_DISTRICTS), session.csrf)

    def zona_crear(environ, form, session):
        zone = zones.create_zone(store, session.principal, name=form.get("nombre", "").strip(),
                                 district=form.get("distrito", ""), lat=_float(form.get("lat"), "Latitud"),
                                 lon=_float(form.get("lon"), "Longitud"), now=clock())
        return views.simple("Zona creada", f"Creaste la zona {zone.name} ({zone.zone_id}). Para activarla, "
                            "registra quién recibe los pedidos.", session.csrf, back="/zona")

    def zona_unirse(environ, form, session):
        customer = zones.join_zone(store, session.principal, form.get("zona", "").strip(), now=clock())
        return views.simple("Te uniste", f"Ahora eres vecino de la zona {customer.zone_id}.", session.csrf,
                            back="/zona")

    def zona_activar(environ, form, session):
        zone = zones.activate_zone(store, form.get("zona", "").strip(), session.principal,
                                   reception_kind=form.get("tipo", ""), contact=form.get("contacto", ""))
        return views.simple("Zona activa", f"La zona {zone.name} ya recibe pedidos.", session.csrf, back="/zona")

    def zona_unir(environ, form, session):
        merge_id = zones.request_merge(store, form.get("zona", "").strip(), form.get("destino", "").strip(),
                                       session.principal, now=clock())
        return views.simple("Solicitud enviada", f"Solicitud {merge_id}: falta que el admin de la otra zona acepte.",
                            session.csrf, back="/zona")

    def zona_aceptar(environ, form, session):
        zone = zones.accept_merge(store, _int(form.get("solicitud", ""), "Número de solicitud"), session.principal,
                                  now=clock())
        return views.simple("Zonas unidas", f"La zona {zone.name} ahora cuenta junto con la tuya.", session.csrf,
                            back="/zona")

    def zona_separar(environ, form, session):
        zone = zones.leave_group(store, form.get("zona", "").strip(), session.principal, now=clock())
        return views.simple("Zona separada", f"La zona {zone.name} vuelve a contar sola.", session.csrf, back="/zona")

    def zona_transferir(environ, form, session):
        zone = zones.transfer_admin(store, form.get("zona", "").strip(), session.principal,
                                    _int(form.get("nuevo", ""), "Número de cliente"))
        return views.simple("Rol transferido", f"El nuevo admin de {zone.name} es el cliente {zone.admin_id}.",
                            session.csrf, back="/zona")

    def devolucion(environ, form, session):
        refund = wallet.request_withdrawal(store, session.principal, _money(form.get("monto", ""), "Monto"), clock())
        return views.simple("Devolución pedida", f"Te devolveremos {views.money(refund.amount)} a tu Yape o Plin "
                            "en un plazo máximo de 30 días.", session.csrf, back="/cuenta")

    def reclamos(environ, form, session):
        delivered = {order_id for delivery in store.deliveries.values() for order_id in delivery.order_ids}
        options = []
        for order in store.orders.values():
            if order.customer_id == session.principal and order.order_id in delivered:  # S-79
                catalog = store.catalog_for(order.cycle)
                for line in order.lines:
                    name = catalog[line.product_id].name if line.product_id in catalog else line.product_id
                    options.append((f"{order.order_id}:{line.product_id}", f"Pedido {order.order_id} · {name}"))
        mine = [c for c in store.claims.values() if c.customer_id == session.principal]
        return views.claims_page(options, mine, session.csrf)

    def reclamar(environ, form, session):
        order_id, separator, product_id = form.get("articulo", "").partition(":")
        if not separator:
            raise BusinessRuleError("INVALID_INPUT", "Elige el artículo a reclamar.")
        claim = claims.file_claim(store, _int(order_id, "Número de pedido"), customer_id=session.principal,
                                  product_id=product_id, quantity=form.get("cantidad", "").strip(),
                                  reason=form.get("motivo", ""), photo=form.get("foto", ""), now=clock())
        return views.simple("Reclamo registrado", f"Tu reclamo {claim.claim_id} quedó pendiente de revisión.",
                            session.csrf, back="/reclamos")

    # --- administrador: armado, entrega, reclamos, colchón y métricas (iteración 12) ---

    def selected_cycle(environ) -> str:
        """S-77: el ciclo actual, o el de ?ciclo= (S-76: con el formato AAAA-Wnn)."""
        value = (_query(environ).get("ciclo") or "").strip()
        if not value:
            return cycle.cycle_id(clock())
        try:
            valid = re.fullmatch(r"\d{4}-W\d{2}", value) and cycle.cycle_id(cycle.opens_at(value)) == value
        except ValueError:
            valid = False
        if not valid:
            raise BusinessRuleError("INVALID_INPUT", "Ciclo no válido; usa el formato 2026-W38.")
        return value

    def armado(environ, form, session):
        cycle_id = selected_cycle(environ)
        attended = sorted((o for o in store.orders_in_cycle(cycle_id) if fulfillment.is_attended(store, o)),
                          key=lambda o: o.order_id)
        zone_ids = sorted({o.zone_id for o in attended})
        stops = [(store.zones[z], store.deliveries.get((cycle_id, z))) for z in zone_ids]
        return views.packing(cycle_id, attended, store.bags, stops, session.csrf)

    def bolsa(environ, form, session):
        bag = fulfillment.pack_bag(store, _int(form.get("pedido", ""), "Número de pedido"), by=session.principal,
                                   photo=form.get("foto", ""), now=clock())
        return views.simple("Bolsa registrada", f"Pedido {bag.order_id}: bolsa {bag.number} con su foto.",
                            session.csrf, back="/admin/armado")

    def entrega(environ, form, session):
        delivery = fulfillment.deliver_zone(store, (form.get("ciclo") or "").strip(), form.get("zona", "").strip(),
                                            by=session.principal, photo=form.get("foto", ""),
                                            received_by=form.get("recibe", ""), now=clock())
        return views.simple("Entrega registrada", f"Zona {delivery.zone_id}: {len(delivery.order_ids)} pedidos "
                            f"recibidos por {delivery.received_by}.", session.csrf, back="/admin/armado")

    def admin_reclamos(environ, form, session):
        return views.admin_claims(list(store.claims.values()), session.csrf)

    def revisar(environ, form, session):
        decision = form.get("decision", "")
        if decision not in ("aprobar", "rechazar"):
            raise BusinessRuleError("INVALID_INPUT", "Elige aprobar o rechazar.")
        claim = claims.review_claim(store, _int(form.get("reclamo", ""), "Número de reclamo"), by=session.principal,
                                    approve=decision == "aprobar", now=clock())
        return views.simple("Reclamo revisado", f"El reclamo {claim.claim_id} quedó {claim.status}. Devuelto como "
                            f"saldo: {views.money(claim.refund_amount)}.", session.csrf, back="/admin/reclamos")

    def colchon(environ, form, session):
        catalog = store.catalog_for(cycle.cycle_id(clock()))
        return views.buffer_page(list(store.buffer.values()), buffer.buffer_value(store), buffer.BUFFER_LIMIT,
                                 [p for p in catalog.values() if p.active], session.csrf, store.buffer_uses)

    def colchon_agregar(environ, form, session):
        stock = buffer.add_to_buffer(store, cycle.cycle_id(clock()), form.get("producto", ""),
                                     form.get("cantidad", "").strip(), by=session.principal)
        return views.simple("Colchón actualizado", f"{stock.product_id}: hay {views.qty(stock.quantity)} guardados.",
                            session.csrf, back="/admin/colchon")

    def colchon_usar(environ, form, session):
        stock = buffer.use_buffer(store, form.get("producto", ""), form.get("cantidad", "").strip(),
                                  order_id=_int(form.get("pedido", ""), "Número de pedido"),
                                  by=session.principal, now=clock())  # S-122
        return views.simple("Colchón actualizado", f"{stock.product_id}: hay {views.qty(stock.quantity)} guardados.",
                            session.csrf, back="/admin/colchon")

    def metricas(environ, form, session):
        cycle_id = selected_cycle(environ)
        margins = metrics.order_margins(store, cycle_id)  # S-78: sin liquidar, 422
        alerts = metrics.margin_alerts(store, cycle_id)
        savings = metrics.delivered_savings(store, cycle_id)
        try:
            repurchase, repurchase_error = metrics.repurchase_week4(store, cycle_id), None
        except BusinessRuleError as error:
            repurchase, repurchase_error = None, error
        compared = reference.reference_savings(store, cycle_id)  # RF-08
        return views.metrics_page(cycle_id, margins, alerts, savings, repurchase, repurchase_error, session.csrf,
                                  compared)

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
        "/cuenta/devolucion": {"POST": (devolucion, "vecino")},
        "/cuenta/ubicacion": {"POST": (ubicacion, "vecino")},
        "/zona": {"GET": (zona, "vecino")},
        "/zona/crear": {"POST": (zona_crear, "vecino")},
        "/zona/unirse": {"POST": (zona_unirse, "vecino")},
        "/zona/activar": {"POST": (zona_activar, "vecino")},
        "/zona/unir": {"POST": (zona_unir, "vecino")},
        "/zona/aceptar": {"POST": (zona_aceptar, "vecino")},
        "/zona/separar": {"POST": (zona_separar, "vecino")},
        "/zona/transferir": {"POST": (zona_transferir, "vecino")},
        "/reclamos": {"GET": (reclamos, "vecino"), "POST": (reclamar, "vecino")},
        "/admin": {"GET": (admin, "admin")},
        "/admin/verificar": {"POST": (verificar, "admin")},
        "/admin/liquidar": {"POST": (liquidar, "admin")},
        "/admin/armado": {"GET": (armado, "admin")},
        "/admin/bolsa": {"POST": (bolsa, "admin")},
        "/admin/entrega": {"POST": (entrega, "admin")},
        "/admin/reclamos": {"GET": (admin_reclamos, "admin")},
        "/admin/reclamos/revisar": {"POST": (revisar, "admin")},
        "/admin/colchon": {"GET": (colchon, "admin")},
        "/admin/colchon/agregar": {"POST": (colchon_agregar, "admin")},
        "/admin/colchon/usar": {"POST": (colchon_usar, "admin")},
        "/admin/metricas": {"GET": (metricas, "admin")},
        "/admin/devoluciones": {"GET": (devoluciones, "admin")},
        "/admin/conciliacion": {"GET": (conciliacion, "admin")},
        "/admin/referencias": {"GET": (referencias, "admin"), "POST": (referencia_registrar, "admin")},
        "/admin/catalogo": {"GET": (catalogo, "admin"), "POST": (catalogo_publicar, "admin")},
        "/admin/catalogo/desactivar": {"POST": (catalogo_desactivar, "admin")},
        "/admin/devoluciones/pagar": {"POST": (devolucion_pagar, "admin")},
        "/admin/entrega-fallida": {"POST": (entrega_fallida, "admin")},
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
        if on_change and environ.get("REQUEST_METHOD") == "POST" and status[:3] in ("200", "303"):
            on_change(store)
        body = html.encode("utf-8")
        start_response(status, [("Content-Type", "text/html; charset=utf-8"),
                                ("Content-Length", str(len(body)))] + headers)
        return [body]

    return app
