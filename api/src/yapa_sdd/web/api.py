"""API JSON para el frontend React (iteración 27). Adaptador: no tiene reglas de negocio.

Spec: docs/desarrollo/27-api-json.md. Usa los mismos casos de uso que la web HTML (app.py).
"""

from __future__ import annotations

import hmac
import json
import re
import secrets
import threading
import traceback
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from urllib.parse import parse_qs
from ..street_routing import street_route

from .. import supplier_stock
from .. import quote_reader, vision
from .. import assistant, audit, auth, buffer, claims, customers, cycle, forecast, fulfillment, ia, incidents, insights, invitations, logistics, metrics, notices, partners, purchase, reception, recovery, reference, supplier_offers, wallet, zones
from ..google_identity import GoogleError
from ..mailer import ConsoleMailer, MailError
from ..catalog import deactivate_product, export_catalog, parse_catalog, publish_catalog
from ..domain import MAX_QUANTITY, MIN_ORDERS_PER_GROUP, MIN_SUBTOTAL, PILOT_DISTRICTS, BusinessRuleError
from ..settlement import ZONE_ADMIN_DISCOUNT, ZONE_ADMIN_DISCOUNT_WEEKS, _in_discount_weeks
from ..order_changes import cancel_order
from ..order_registration import quote_order, register_order, verify_payment
from ..store import InMemoryStore
from ..throttle import Throttle
from .app import _cookie, _form, _save_photo
from .produccion import client_ip


KINDS = ("vecino", "admin", partners.DRIVER, partners.SUPPLIER, *partners.STAFF_KINDS)  # CX-06, CX-09
PACKING = ("admin", partners.PACKER)  # CX-09: rutas que el admin comparte con cada rol
BUYING = ("admin", partners.BUYER)
ATTENDING = ("admin", partners.SUPPORT)
PHOTO_VIEWERS = ("admin", partners.PACKER, partners.SUPPORT)
PACKER_ORDER = ("id", "ciclo", "zona", "zona_nombre", "estado", "entregado", "vecino", "bolsas")  # AM-01, S-290: sin montos ni pagos
PHOTO_PATH = re.compile(r"fotos/[0-9a-f]{16}.(jpg|jpeg|png|webp|heic)")  # S-180: lo que escribe _save_photo
PHOTO_MIME = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "heic": "image/heic"}
PHOTO_ROUTES = {"/api/reclamos", "/api/admin/bolsas", "/api/admin/entregas", "/api/admin/entregas-fallidas",
                "/api/reparto/entregas", "/api/reparto/entregas-fallidas", "/api/admin/danados"}  # S-260, TR-02, DA-04
VIEW_AS_BLOCKED = re.compile(r"/api/(saldo/devolucion|pedidos/\d+/cancelar|zonas/[\w-]+/transferir)")  # S-262
LOGIN_FAILURES = (30, timedelta(minutes=15))  # S-264
MAILS_PER_IP = (10, timedelta(hours=1))  # S-265
FAILURE_CODES = {"INVALID_CREDENTIALS", "INVALID_CODE"}
COOKIE = "yapa_api"
SESSION_TIME = timedelta(hours=8)  # S-69
WINDOWS = ["09:00 – 12:00", "12:00 – 15:00", "15:00 – 18:00"]


class ApiError(Exception):
    def __init__(self, status: str, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def money(value) -> str:
    """S-154: montos como texto con dos decimales."""
    return f"{Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"


def qty(value) -> str:
    return f"{Decimal(value).normalize():f}"


def _int(value, what: str) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise BusinessRuleError("INVALID_INPUT", f"{what} no es válido.")


def _money_in(value, what: str) -> Decimal:
    try:
        amount = Decimal(str(value).strip())
    except Exception:
        raise BusinessRuleError("INVALID_INPUT", f"{what} no es válido.")
    if not amount.is_finite() or amount < 0:
        raise BusinessRuleError("INVALID_INPUT", f"{what} no es válido.")
    return amount


FLAGS = ("usar_saldo", "consentimiento", "avisos_correo")  # los únicos datos de sí o no
STRUCTURED = ("lineas", "recibido")  # cada ruta valida su forma (cotizar y pedir; CR-04)


def _scalars(data: dict) -> dict:
    """AD-04, S-171: los datos son texto, número o sí/no; un número se lee como su texto."""
    clean = {}
    for key, value in data.items():
        if key in STRUCTURED or key in FLAGS or value is None or isinstance(value, str):
            clean[key] = value
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            clean[key] = str(value)
        else:
            raise BusinessRuleError("INVALID_INPUT", f"El dato '{key}' no es válido.")
    return clean


def _body(environ) -> tuple[dict, dict]:
    if environ.get("CONTENT_TYPE", "").startswith("application/json"):
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        raw = environ["wsgi.input"].read(length) if length else b""
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except ValueError:
            raise ApiError("400 Bad Request", "INVALID_JSON", "El cuerpo no es JSON válido.")
        return (_scalars(data) if isinstance(data, dict) else {}), {}
    return _form(environ)  # multipart con fotos (S-151) o formulario simple


def create_api(store: InMemoryStore, clock=None, on_change=None, photo_dir: str = "fotos", mailer=None, google=None,
               background_mail: bool = True, secure_cookie: bool = False, security_clock=None, payee: dict | None = None,
               ai=None):
    clock = clock or (lambda: datetime.now(cycle.LIMA))
    mailer = mailer or ConsoleMailer()  # S-208: sin credenciales, el código sale en la consola del motor
    sessions: dict[str, dict] = {}
    security = security_clock or clock  # DM-05, S-254: bloqueos y sesiones con la hora real aunque el negocio use otro reloj
    credential_paths = frozenset({"/api/pin", "/api/pin/crear", "/api/cuenta/correo", "/api/cuenta/correo/verificar",
                                  "/api/cuenta/google", "/api/cuenta/google/desvincular"})  # DM-08
    secure = "; Secure" if secure_cookie else ""  # S-230
    login_failures, mails = Throttle(*LOGIN_FAILURES), Throttle(*MAILS_PER_IP)

    # --- ayudas ---

    def tell(event, *args) -> None:
        """AV-11: un aviso nunca debe romper la acción que lo causa."""
        try:
            event(store, *args, clock())
        except Exception:
            traceback.print_exc()

    def send_notice_emails(errors) -> None:
        """AV-08, AV-10, S-219: los correos de aviso salen en segundo plano y se intentan una sola vez."""
        batch = notices.claim_emails(store)
        if not batch:
            return

        def send_all() -> None:
            for to, subject, body in batch:
                try:
                    mailer.send(to, subject, body)
                except MailError:
                    traceback.print_exc(file=errors)

        if background_mail:
            threading.Thread(target=send_all, daemon=True).start()
        else:
            send_all()

    def session_of(environ) -> tuple[str | None, dict | None]:
        token = _cookie(environ, COOKIE)
        session = sessions.get(token) if token else None
        if session and (security() >= session["expires"]
                        or session["stamp"] != auth.credential_stamp(store, session["kind"], session["principal"])):  # SG-05
            del sessions[token]
            session = None
        return token, session

    def counting_failures(environ, action):
        """SG-09: desde una dirección con muchos fallos no se revisa la clave; cada fallo de clave o código cuenta."""
        ip = client_ip(environ)
        if login_failures.blocked(ip, security()):
            raise ApiError("429 Too Many Requests", "TOO_MANY_ATTEMPTS",
                           "Demasiados intentos desde tu conexión. Vuelve a intentar en 15 minutos.")
        try:
            return action()
        except BusinessRuleError as error:
            if error.code in FAILURE_CODES:
                login_failures.hit(ip, security())
            raise

    def role_of(session: dict) -> str:
        """S-157: el admin de zona es un vecino que administra una zona."""
        if session["kind"] != "vecino":  # CX-06, CX-09
            return session["kind"]
        administers = any(z.admin_id == session["principal"] for z in store.zones.values())
        return "admin_zona" if administers else "vecino"

    def names_for(cycle_id: str) -> dict[str, str]:
        return {p.product_id: p.name for p in store.catalog_for(cycle_id).values()}

    def units_for(cycle_id: str) -> dict[str, str]:
        """UN-01, S-338: kg o unidad, según el catálogo de la semana."""
        return {p.product_id: p.unit for p in store.catalog_for(cycle_id).values()}

    def zone_json(zone) -> dict:
        members = [c for c in store.customers.values() if c.zone_id == zone.zone_id]
        return {"id": zone.zone_id, "nombre": zone.name, "distrito": zone.district, "grupo": zone.group_id,
                "estado": zone.status, "lat": zone.lat, "lon": zone.lon, "admin": zone.admin_id,
                "vecinos": len(members), "costo_parada": money(zone.stop_cost),
                "recibe": zone.reception_kind, "contacto": zone.reception_contact}

    def lines_in(data) -> list[tuple[str, str]]:
        raw = data.get("lineas") or {}
        if not isinstance(raw, dict):
            raise BusinessRuleError("INVALID_INPUT", "El carrito no es válido.")
        return [(str(k), str(v)) for k, v in raw.items() if str(v).strip() not in ("", "0")]

    def order_json(order, names, now) -> dict:
        settled = store.settlements.get(order.cycle)
        settled = settled.orders.get(order.order_id) if settled else None
        delivered = any(order.order_id in d.order_ids for d in store.deliveries.values())
        units = units_for(order.cycle)  # UN-01
        data = {
            "id": order.order_id, "ciclo": order.cycle, "zona": order.zone_id, "cliente": order.customer_id,
            "zona_nombre": store.zones[order.zone_id].name if order.zone_id in store.zones else order.zone_id,  # OC-05
            "estado": order.status, "pago": order.payment_status, "metodo": order.payment_method,
            "codigo_pago": order.operation_code, "total": money(order.total), "subtotal": money(order.subtotal),
            "envio": money(order.delivery_fee), "con_saldo": money(order.paid_with_balance),
            "a_yapear": money(order.paid_external), "entregado": delivered,
            "cancelable": order.status == "REGISTRADO" and cycle.is_open(now) and cycle.cycle_id(now) == order.cycle,
            "lineas": [{"id": l.product_id, "nombre": names.get(l.product_id, l.product_id), "cantidad": qty(l.quantity),
                        "unidad": units.get(l.product_id, ""),
                        "precio_max": money(l.max_unit_price), "total": money(l.max_total)} for l in order.lines],
        }
        data["seguimiento"] = logistics.tracking(store, order)  # SG-01, SG-03
        data["estado_seguimiento"] = logistics.order_status(store, order)  # SG-02
        photos = logistics.order_photos(store, order)
        data["fotos"] = {"entrega": photos["entrega"] is not None, "bolsas": len(photos["bolsas"])}  # SG-05
        if payee and order.payment_status == "POR_VERIFICAR" and order.paid_external > 0:  # PL-01, S-305: falta pagar
            data["pagar_a"] = dict(payee)
        if settled:
            comparison = reference.order_comparison(store, order.order_id)
            data["liquidacion"] = {
                "estado": settled.status, "pagado": money(settled.paid), "costo": money(settled.final_amount),
                "devuelto": money(settled.refund_amount + settled.returned_to_balance),
                "destino": settled.refund_destination, "beneficio": money(settled.benefit),
                "comparacion": {kind: {"costaba": money(c.reference_total), "ahorro": money(c.savings)}
                                for kind, c in comparison.items()},
            }
        return data

    # --- público (API-01) ---

    def estado(environ, data, session):
        now = clock()
        cycle_id = cycle.cycle_id(now)
        return {"ciclo": cycle_id, "abierto": cycle.is_open(now), "ahora": now.isoformat(),
                "cierre": "miércoles 20:00", "entrega": "sábado", "ventanas": WINDOWS,
                "minimo_pedido": money(MIN_SUBTOTAL), "minimo_grupo": MIN_ORDERS_PER_GROUP,
                "distritos": sorted(PILOT_DISTRICTS),
                "google_client_id": getattr(google, "client_id", None),  # GO-01: el id es público
                "ia": ai is not None}  # IA-01

    def catalogo(environ, data, session):
        now = clock()
        cycle_id = cycle.cycle_id(now)
        ordered: dict[str, Decimal] = {}
        for order in store.orders_in_cycle(cycle_id):
            if order.status == "REGISTRADO":
                for line in order.lines:
                    ordered[line.product_id] = ordered.get(line.product_id, Decimal("0")) + line.quantity
        today = cycle.to_lima(now).date()
        products = []
        for p in store.catalog_for(cycle_id).values():
            if not p.active:
                continue
            total = ordered.get(p.product_id, Decimal("0"))
            following = next((t for t in p.tiers if t.min_quantity > total), None)
            refs = reference.current_references(store, p.product_id, today)
            products.append({
                "id": p.product_id, "nombre": p.name, "categoria": p.category, "unidad": p.unit,
                "paso": qty(p.step), "maximo_por_pedido": qty(MAX_QUANTITY.get(p.unit, 0)),
                "precio_max": money(p.max_unit_price()), "pedido_total": qty(total),
                "siguiente_tramo": ({"desde": qty(following.min_quantity),
                                     "precio": money(p.price_with_commission(following.base_price))}
                                    if following else None),
                "tramos": [{"desde": qty(t.min_quantity), "precio": money(p.price_with_commission(t.base_price))}
                           for t in p.tiers],
                "referencias": [{"tipo": r.kind, "fuente": r.source, "precio": money(r.price),
                                 "visto": r.observed_on.isoformat()} for r in refs.values()],
            })
        return {"ciclo": cycle_id, "productos": products}

    def zonas(environ, data, session):
        """SG-12, S-267: el equipo ve todo; los demás, sin contacto ni admin; quien no entró, la ubicación redondeada."""
        result = [zone_json(z) for z in store.zones.values()]
        if session is None or session["kind"] != "admin":
            for zone in result:
                del zone["contacto"], zone["admin"]
                if session is None:
                    zone["lat"], zone["lon"] = (round(zone[k], 3) if zone[k] is not None else None for k in ("lat", "lon"))
        return {"zonas": result}

    # --- sesión (API-02) ---

    def sesion_entrar(environ, data, session):
        kind = data.get("tipo") if data.get("tipo") in KINDS else "vecino"  # CX-A
        user = customers.resolve_login(store, data.get("usuario", "")) if kind == "vecino" else data.get("usuario", "")  # S-244
        principal = counting_failures(environ, lambda: auth.authenticate(store, kind, user, data.get("secreto", ""), security()))
        return open_session(principal, kind)

    def open_session(principal, kind, **extra):
        for old in [t for t, s in sessions.items() if security() >= s["expires"]]:  # SG-15
            del sessions[old]
        token = secrets.token_urlsafe(32)
        new = {"principal": principal, "kind": kind, "csrf": secrets.token_urlsafe(16),
               "expires": security() + SESSION_TIME, "stamp": auth.credential_stamp(store, kind, principal), **extra}
        sessions[token] = new
        cookie = f"{COOKIE}={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={int(SESSION_TIME.total_seconds())}{secure}"
        return me(new), [("Set-Cookie", cookie)]

    def google_identity(data) -> dict:
        """GO-05, GO-06 (S-214): el token se comprueba aquí; cualquier problema da el mismo error."""
        if google is None:
            raise BusinessRuleError("GOOGLE_NOT_CONFIGURED", "Entrar con Google todavía no está activado.")
        try:
            return google.verify(data.get("credential", ""))
        except ImportError:
            raise BusinessRuleError("GOOGLE_NOT_CONFIGURED", "Entrar con Google todavía no está activado.") from None
        except GoogleError:
            raise BusinessRuleError("INVALID_GOOGLE_TOKEN", "No pudimos comprobar tu cuenta de Google. Inténtalo de nuevo.") from None

    def sesion_google(environ, data, session):
        """GO-03."""
        return open_session(recovery.customer_by_google(store, google_identity(data)["sub"]), "vecino")

    def cuenta_google(environ, data, session):
        """GO-02."""
        recovery.link_google(store, session["principal"], google_identity(data), clock())
        return {"google_vinculado": True}

    def mi_invitacion(environ, data, session):
        """IN-01."""
        return invitations.link_for(store, session["principal"], clock())

    def mi_invitacion_renovar(environ, data, session):
        """IN-02."""
        return invitations.renew(store, session["principal"], clock())

    def invitacion_ver(environ, data, session, token):
        """IN-03."""
        return invitations.preview(store, token)

    def invitacion_correo(environ, data, session, token):
        """IN-04."""
        ip = client_ip(environ)
        if mails.blocked(ip, security()):  # SG-10
            raise ApiError("429 Too Many Requests", "TOO_MANY_ATTEMPTS",
                           "Pediste muchos códigos desde tu conexión. Intenta de nuevo en una hora.")
        email, code = invitations.start_signup(store, token, data.get("nombre", ""), data.get("celular", ""),
                                               data.get("correo", ""), bool(data.get("consentimiento")), clock())
        mails.hit(ip, security())
        try:
            send_code(email, "Confirma tu correo en Yapa", "Estás creando tu cuenta de Yapa.", code)
        except MailError:
            raise BusinessRuleError("EMAIL_SEND_FAILED", "No pudimos enviar el correo. Revisa que esté bien escrito e inténtalo de nuevo.") from None
        return {"enviado": True}

    def invitacion_confirmar(environ, data, session, token):
        """IN-05."""
        customer = counting_failures(environ, lambda: invitations.finish_signup(
            store, token, data.get("correo", ""), data.get("codigo", ""), data.get("pin", ""), clock()))
        return open_session(customer.customer_id, "vecino")

    def invitacion_google(environ, data, session, token):
        """IN-06: primero el enlace, después el token de Google."""
        invitations.resolve(store, token)
        customer = invitations.signup_google(store, token, google_identity(data), data.get("celular", ""),
                                             bool(data.get("consentimiento")), clock())
        return open_session(customer.customer_id, "vecino")

    def cuenta_google_desvincular(environ, data, session):
        """GO-04."""
        recovery.unlink_google(store, session["principal"])
        return {"google_vinculado": False}

    def me(session) -> dict:
        data = {"rol": role_of(session), "csrf": session["csrf"], "usuario": session["principal"]}
        if session["kind"] == "vecino":
            customer = store.customers[session["principal"]]
            data.update({"nombre": customer.name, "zona": customer.zone_id,
                         "saldo": money(wallet.balance(store, customer.customer_id)),
                         "codigo_referido": customers.referral_code(customer),
                         "correo": recovery.mask_email(customer.email),  # CR-08
                         "correo_verificado": customer.email_verified_at is not None,
                         "google_vinculado": customer.google_sub is not None,  # GO-06
                         "avisos_sin_leer": notices.unread_count(store, customer.customer_id),  # AV-04
                         "correo_avisos": customer.email_notices,
                         "tiene_pin": ("vecino", str(customer.customer_id)) in store.credentials})  # S-248
        elif session["kind"] == "admin":
            data.update({"nombre": "Equipo Yapa", "puede_ver_como": session["principal"] in store.debug_admins})  # DM-06
        else:
            partner = store.partners[session["principal"]]
            data.update({"nombre": partner.name, "proveedor": partner.supplier_id, "zona": partner.zone_id})
        if session.get("viewing_as"):  # DM-06
            data["viendo_como"] = {"admin": session["viewing_as"]}
        return data

    def sesion_ver(environ, data, session):
        return me(session)

    def log_debug(admin, target, action) -> None:
        store.debug_log.append({"admin": admin, "como": target, "accion": action, "momento": security()})  # DM-09

    def ver_como(environ, data, session):
        """DM-06, S-256, S-257: el admin global abre la pantalla de un vecino o admin de zona."""
        if session["principal"] not in store.debug_admins:
            raise BusinessRuleError("NOT_DEBUG_ADMIN", "Solo el admin global de depuración puede ver Yapa como otra persona.")
        try:
            target = customers.parse_customer_number(data.get("usuario"))
        except BusinessRuleError:
            target = None
        if target not in store.customers:
            raise BusinessRuleError("CUSTOMER_NOT_FOUND", "Esa persona no está registrada.")
        token, _ = session_of(environ)
        log_debug(session["principal"], target, "ver-como")
        return open_session(target, "vecino", viewing_as=session["principal"], return_token=token, csrf=session["csrf"])

    def sesion_volver(environ, data, session):
        """DM-07."""
        back = sessions.get(session.get("return_token") or "")
        if back is not None and back["stamp"] != auth.credential_stamp(store, back["kind"], back["principal"]):  # SG-16
            back = None
        if back is None:
            raise BusinessRuleError("NOT_VIEWING_AS", "No estás viendo Yapa como otra persona.")
        token, _ = session_of(environ)
        sessions.pop(token, None)
        log_debug(session["viewing_as"], session["principal"], "volver")
        cookie = f"{COOKIE}={session['return_token']}; HttpOnly; SameSite=Lax; Path=/; Max-Age={int(SESSION_TIME.total_seconds())}{secure}"
        return me(back), [("Set-Cookie", cookie)]

    def sesion_salir(environ, data, session):
        token, _ = session_of(environ)
        sessions.pop(token, None)
        return {"ok": True}, [("Set-Cookie", f"{COOKIE}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0{secure}")]

    # --- vecino (API-03, API-04) ---

    def cotizar(environ, data, session):
        cycle_id = cycle.cycle_id(clock())
        result = quote_order(store, lines_in(data), cycle_id)
        names = names_for(cycle_id)
        today = cycle.to_lima(clock()).date()
        savings = Decimal("0")  # S-145
        for line in result.lines:
            ref = reference.current_references(store, line.product_id, today).get("SUPERMERCADO")
            if ref:
                savings += line.quantity * ref.price - line.max_total
        return {"lineas": [{"id": l.product_id, "nombre": names.get(l.product_id, l.product_id),
                            "cantidad": qty(l.quantity), "precio_max": money(l.max_unit_price),
                            "total": money(l.max_total)} for l in result.lines],
                "subtotal": money(result.subtotal), "envio": money(result.delivery_fee), "total": money(result.total),
                "ahorro_supermercado": money(max(savings, Decimal("0"))),
                "saldo": money(wallet.balance(store, session["principal"]))}

    def payment_code(cycle_id: str, customer_id) -> str:
        """S-150: código de pago único que el vecino pone en el mensaje del Yape o Plin."""
        while True:
            code = f"YP-{cycle_id.replace('-', '')}-{customer_id}-{secrets.token_hex(2).upper()}"
            if code not in store.used_codes:
                return code

    def pedidos(environ, data, session):
        now = clock()
        cycle_id = cycle.cycle_id(now)
        lines = lines_in(data)
        total = quote_order(store, lines, cycle_id).total
        use = min(wallet.balance(store, session["principal"]), total) if data.get("usar_saldo") else Decimal("0")
        due = total - use
        code = payment_code(cycle_id, session["principal"]) if due > 0 else None
        order = register_order(store, customer_id=session["principal"], lines=lines,
                               payment_method=(data.get("metodo") or None) if code else None, operation_code=code,
                               amount=due, use_balance=use, now=now)
        return order_json(order, names_for(order.cycle), now), [], "201 Created"

    def mis_pedidos(environ, data, session):
        now = clock()
        mine = sorted((o for o in store.orders.values() if o.customer_id == session["principal"]),
                      key=lambda o: o.order_id, reverse=True)
        refunds = [r for r in store.refunds.values() if r.customer_id == session["principal"]
                   and r.status == "PENDIENTE"]
        returned = Decimal("0")
        saved = Decimal("0")
        result = []
        for order in mine:
            item = order_json(order, names_for(order.cycle), now)
            settled = item.get("liquidacion")
            if settled and settled["estado"] in ("LIQUIDADO", "NO_ATENDIDO", "NO_ENTREGADO"):
                returned += Decimal(settled["devuelto"])
                if "SUPERMERCADO" in settled["comparacion"]:
                    saved += Decimal(settled["comparacion"]["SUPERMERCADO"]["ahorro"])
            result.append(item)
        return {"pedidos": result, "saldo": money(wallet.balance(store, session["principal"])),
                "devuelto_total": money(returned), "ahorro_supermercado": money(saved),
                "devoluciones": [{"id": r.refund_id, "monto": money(r.amount), "motivo": r.reason,
                                  "estado": r.status} for r in refunds]}

    def cancelar(environ, data, session, order_id):
        order = cancel_order(store, _int(order_id, "Número de pedido"), customer_id=session["principal"], now=clock(),
                             refund_to=data.get("destino") or "MEDIO_DE_PAGO")
        return order_json(order, names_for(order.cycle), clock())

    def devolucion(environ, data, session):
        refund = wallet.request_withdrawal(store, session["principal"], _money_in(data.get("monto"), "Monto"), clock())
        return {"id": refund.refund_id, "monto": money(refund.amount), "estado": refund.status}

    def crear_pin(environ, data, session):
        """LG-05."""
        auth.create_pin(store, session["principal"], data.get("pin", ""))
        session["stamp"] = auth.credential_stamp(store, "vecino", session["principal"])  # SG-06
        return {"tiene_pin": True}

    def cambiar_pin(environ, data, session):
        auth.change_pin(store, session["principal"], data.get("actual", ""), data.get("nuevo", ""), security())
        session["stamp"] = auth.credential_stamp(store, "vecino", session["principal"])  # SG-06
        return {"ok": True}

    def reclamos(environ, data, session):
        # RV-01, RV-02, S-334: solo lo que todavía se puede reclamar (RC-03), con su hora límite
        until = {oid: d.delivered_at + claims.CLAIM_WINDOW for d in store.deliveries.values() for oid in d.order_ids}
        now = clock()
        options = []
        for order in store.orders.values():
            if order.customer_id == session["principal"] and order.order_id in until and now < until[order.order_id]:
                names, units = names_for(order.cycle), units_for(order.cycle)
                for line in order.lines:
                    options.append({"pedido": order.order_id, "producto": line.product_id,
                                    "nombre": names.get(line.product_id, line.product_id), "cantidad": qty(line.quantity),
                                    "unidad": units.get(line.product_id, ""),  # UN-02
                                    "hasta": until[order.order_id].isoformat()})
        mine = [c for c in store.claims.values() if c.customer_id == session["principal"]]
        return {"reclamables": options, "reclamos": [claim_json(c) for c in mine]}

    def claim_json(c) -> dict:
        return {"id": c.claim_id, "pedido": c.order_id, "cliente": c.customer_id, "producto": c.product_id,
                "cantidad": qty(c.quantity), "motivo": c.reason, "foto": c.photo, "estado": c.status,
                "devuelto": money(c.refund_amount),
                "nombre": names_for(store.orders[c.order_id].cycle).get(c.product_id, c.product_id)}  # OC-03

    def reclamar(environ, data, session):
        claim = claims.file_claim(store, _int(data.get("pedido"), "Número de pedido"), customer_id=session["principal"],
                                  product_id=str(data.get("producto", "")), quantity=str(data.get("cantidad", "")).strip(),
                                  reason=data.get("motivo", ""), photo=data.get("foto", ""), now=clock())
        return claim_json(claim), [], "201 Created"

    # --- zona (API-05) ---

    def group_progress(zone) -> dict:
        """AZ-08 y AG-02: pedidos verificados del grupo en el ciclo actual, sin cancelados (S-320: solo el conteo)."""
        current = cycle.cycle_id(clock())
        group = {z.zone_id for z in store.zones.values() if z.group_id == zone.group_id}
        verified = sum(1 for o in store.orders_in_cycle(current)
                       if o.status != "CANCELADO_POR_CLIENTE" and o.zone_id in group and o.payment_status == "VERIFICADO")
        return {"verificados": verified, "minimo": MIN_ORDERS_PER_GROUP, "ciclo": current}

    def zone_admin_panel(zone) -> dict:
        """AZ-08: lo que ve el admin de su zona (S-165: nombres y si pidió, sin montos ni ubicaciones)."""
        current = cycle.cycle_id(clock())
        in_cycle = [o for o in store.orders_in_cycle(current) if o.status != "CANCELADO_POR_CLIENTE"]
        ordered = {o.customer_id for o in in_cycle}
        nearby = []
        if zone.lat is not None and zone.lon is not None:
            for other in store.zones.values():
                if other.zone_id == zone.zone_id or other.lat is None or other.lon is None:
                    continue
                meters = zones.distance_m(zone.lat, zone.lon, other.lat, other.lon)
                if meters <= zones.MERGE_DISTANCE_M:
                    same_group = other.group_id == zone.group_id
                    nearby.append(zone_json(other) | {"distancia_m": round(meters), "mismo_grupo": same_group,
                                                      "motivo": "" if same_group else zones.merge_blocker(store, zone, other, clock()) or ""})  # AN-12
        discount = _in_discount_weeks(zone.created_cycle, current)
        last_week = cycle.add_weeks(zone.created_cycle, ZONE_ADMIN_DISCOUNT_WEEKS - 1) if zone.created_cycle else None
        requests = [{"id": mid, "zona": zid, "nombre": store.zones[zid].name if zid in store.zones else zid}
                    for mid, (zid, target) in store.merge_requests.items() if target == zone.zone_id]
        sent = [{"id": mid, "zona": target, "nombre": store.zones[target].name if target in store.zones else target}
                for mid, (zid, target) in store.merge_requests.items() if zid == zone.zone_id]  # AN-13
        admin = store.customers[zone.admin_id]
        return zone_json(zone) | {
            "avance": group_progress(zone),
            "vecinos": [{"id": c.customer_id, "nombre": c.name, "pidio": c.customer_id in ordered}
                        for c in sorted(store.customers.values(), key=lambda c: c.customer_id)
                        if c.zone_id == zone.zone_id],
            "cercanas": sorted(nearby, key=lambda z: z["distancia_m"]),
            "solicitudes": requests, "enviadas": sent,
            "beneficios": {"envio_gratis": True, "descuento_pct": money(ZONE_ADMIN_DISCOUNT * 100),
                           "descuento_activo": discount, "descuento_hasta": last_week if discount else None},
            "codigo_referido": customers.referral_code(admin),
        }

    def mi_zona(environ, data, session):
        customer = store.customers[session["principal"]]
        zone = store.zones.get(customer.zone_id)
        administered = next((z for z in store.zones.values() if z.admin_id == session["principal"]), None)
        return {"zona": zone_json(zone) if zone else None,
                "avance": group_progress(zone) if zone else None,  # AG-01: cualquier vecino con zona
                "administra": zone_admin_panel(administered) if administered else None,
                "codigo_referido": customers.referral_code(customer),
                "radio_m": zones.MEMBER_RADIUS_M, "union_m": zones.MERGE_DISTANCE_M}

    def ubicacion(environ, data, session):
        customer = zones.set_location(store, session["principal"], data.get("lat"), data.get("lon"))  # FE-09, HR-01
        return {"lat": customer.lat, "lon": customer.lon}

    def zona_crear(environ, data, session):
        zone = zones.create_zone(store, session["principal"], name=str(data.get("nombre", "")).strip(),
                                 district=data.get("distrito", ""), lat=data.get("lat"), lon=data.get("lon"), now=clock())
        return zone_json(zone), [], "201 Created"

    def zona_unirme(environ, data, session, zone_id):
        zones.join_zone(store, session["principal"], zone_id, now=clock())
        return zone_json(store.zones[zone_id])

    def zona_activar(environ, data, session, zone_id):
        zone = zones.activate_zone(store, zone_id, session["principal"], reception_kind=data.get("tipo", ""),
                                   contact=data.get("contacto", ""))
        return zone_json(zone)

    def zona_unir(environ, data, session, zone_id):
        merge_id = zones.request_merge(store, zone_id, str(data.get("destino", "")), session["principal"], now=clock())
        tell(notices.merge_requested, *merge_zones(merge_id))
        return {"solicitud": merge_id}

    def zona_separar(environ, data, session, zone_id):
        return zone_json(zones.leave_group(store, zone_id, session["principal"], now=clock()))

    def zona_transferir(environ, data, session, zone_id):
        return zone_json(zones.transfer_admin(store, zone_id, session["principal"], _int(data.get("nuevo"), "Vecino")))

    def merge_zones(merge_id: int):
        """(zona que pidió, zona pedida) de una solicitud, o (None, None) si ya no existe."""
        requester, target = store.merge_requests.get(merge_id, (None, None))
        return store.zones.get(requester), store.zones.get(target)

    def solicitud_aceptar(environ, data, session, merge_id):
        answered = merge_zones(_int(merge_id, "Solicitud"))
        merged = zones.accept_merge(store, _int(merge_id, "Solicitud"), session["principal"], now=clock())
        tell(notices.merge_answered, *answered, True)
        return zone_json(merged)

    def solicitud_retirar(environ, data, session, merge_id):
        zones.withdraw_merge(store, _int(merge_id, "Solicitud"), session["principal"])  # AN-14
        return {"retirada": True}

    def solicitud_rechazar(environ, data, session, merge_id):
        answered = merge_zones(_int(merge_id, "Solicitud"))
        zones.reject_merge(store, _int(merge_id, "Solicitud"), session["principal"])
        tell(notices.merge_answered, *answered, False)
        return {"ok": True}

    # --- admin Yapa (API-06) ---

    def known_cycles(ahead: int = 0) -> list[str]:
        current = cycle.cycle_id(clock())
        found = {o.cycle for o in store.orders.values()} | set(store.catalogs) | {current}
        found |= {cycle.add_weeks(current, n) for n in range(1, ahead + 1)}
        return sorted(found, reverse=True)

    def query_cycle(environ) -> str:
        value = (parse_qs(environ.get("QUERY_STRING", "")).get("ciclo", [""])[0]).strip()
        if not value:
            return cycle.cycle_id(clock())
        cycle.check_cycle_id(value)  # AD-06
        return value

    def admin_analisis(environ, data, session):
        """AN-01..AN-07: zonas, uniones posibles y propuestas; solo lee."""
        result = insights.analysis(store, query_cycle(environ), clock())
        for row in result["zonas"]:
            row["margen"] = money(row["margen"]) if row["margen"] is not None else None
        return result | {"radio_m": zones.MEMBER_RADIUS_M, "union_m": zones.MERGE_DISTANCE_M, "ciclos": known_cycles()}

    def canasta_sugerir(environ, data, session):
        """IA-01..IA-07: la IA sugiere y el motor pone precios, pasos y topes."""
        sug = ia.suggest_basket(store, ai, session["principal"], data.get("texto"), clock())
        return {"lineas": [{"id": l["id"], "nombre": l["nombre"], "unidad": l["unidad"], "cantidad": qty(l["cantidad"]),
                            "precio_max": money(l["precio_max"]), "total": money(l["total"])} for l in sug["lineas"]],
                "subtotal": money(sug["subtotal"]), "falta": money(sug["falta"]), "comentario": sug["comentario"],
                "proveedor": sug["proveedor"]}

    def admin_ia_atencion(environ, data, session):
        """IA-10..IA-13: sugerencia para atención; no cambia nada."""
        return ia.suggest_support(store, ai, str(data.get("tipo", "")), data.get("id"), by=session["principal"])

    def pedido_foto(environ, data, session, order_id, which):
        """SG-04, S-313: el vecino ve las fotos de su propio pedido; la ruta sale del registro, no de la petición."""
        order = store.orders.get(_int(order_id, "Pedido"))
        if order is None or order.customer_id != session["principal"]:
            raise ApiError("404 Not Found", "ORDER_NOT_FOUND", "El pedido no existe.")
        photos = logistics.order_photos(store, order)
        route = None
        if which == "entrega":
            route = photos["entrega"]
        elif re.fullmatch(r"bolsa-[1-9]\d{0,2}", which) and int(which[6:]) <= len(photos["bolsas"]):
            route = photos["bolsas"][int(which[6:]) - 1]
        match = PHOTO_PATH.fullmatch(route or "")
        file = Path(photo_dir) / route.split("/", 1)[1] if match else None
        if file is None or not file.is_file():
            raise ApiError("404 Not Found", "PHOTO_NOT_FOUND", "Esa foto no existe.")
        return file.read_bytes(), [("Content-Type", PHOTO_MIME[match.group(1)]), ("X-Content-Type-Options", "nosniff"),
                                   ("Cache-Control", "private, no-store")]

    def admin_foto(environ, data, session):
        """FA-01..FA-04, S-179, S-180: entrega una foto guardada solo si la ruta tiene la forma exacta que escribe el motor."""
        route = (parse_qs(environ.get("QUERY_STRING", "")).get("ruta") or [""])[0]
        match = PHOTO_PATH.fullmatch(route)
        if not match:
            raise BusinessRuleError("INVALID_INPUT", "La ruta de la foto no es válida.")
        file = Path(photo_dir) / route.split("/", 1)[1]
        if not file.is_file():
            raise ApiError("404 Not Found", "PHOTO_NOT_FOUND", "Esa foto no existe.")
        return file.read_bytes(), [("Content-Type", PHOTO_MIME[match.group(1)]), ("X-Content-Type-Options", "nosniff"),
                                   ("Cache-Control", "private, no-store")]

    def admin_resumen(environ, data, session):
        cycle_id = query_cycle(environ)
        now = clock()
        in_cycle = [o for o in store.orders_in_cycle(cycle_id) if o.status != "CANCELADO_POR_CLIENTE"]
        pending = [o for o in in_cycle if o.status == "REGISTRADO" and o.payment_status == "POR_VERIFICAR"]
        verified = [o for o in in_cycle if o.payment_status == "VERIFICADO"]
        groups: dict[str, dict] = {}
        for zone in store.zones.values():
            group = groups.setdefault(zone.group_id, {"grupo": zone.group_id, "zonas": [], "verificados": 0})
            group["zonas"].append(zone.name)
        for order in verified:
            if order.status == "REGISTRADO":
                zone = store.zones.get(order.zone_id)
                if zone:
                    groups[zone.group_id]["verificados"] += 1
        names = names_for(cycle_id)
        return {
            "ciclo": cycle_id, "ciclos": known_cycles(), "abierto": cycle.is_open(now) and cycle_id == cycle.cycle_id(now),
            "indicadores": {"pedidos": len(in_cycle), "por_verificar": len(pending),
                            "verificado": money(sum((o.total for o in verified), Decimal("0"))),
                            "vecinos": len({o.customer_id for o in in_cycle})},
            "grupos": [dict(g, minimo=MIN_ORDERS_PER_GROUP) for g in groups.values()],
            "por_verificar": [order_json(o, names, now) | {"vecino": store.customers[o.customer_id].name}
                              for o in pending],
            "pedidos": [order_json(o, names, now) | {"vecino": store.customers[o.customer_id].name}
                        for o in sorted(store.orders_in_cycle(cycle_id), key=lambda o: o.order_id)],
            "liquidado": cycle_id in store.settlements,
        }

    def admin_verificar(environ, data, session, order_id):
        order = verify_payment(store, _int(order_id, "Número de pedido"), now=clock())
        tell(notices.payment_verified, order)
        return order_json(order, names_for(order.cycle), clock())

    def admin_liquidar(environ, data, session, cycle_id):
        result = fulfillment.close_cycle(store, cycle_id, at=clock())
        tell(notices.cycle_settled, result)
        return {"ciclo": result.cycle,
                "productos": [{"id": p.product_id, "total": qty(p.total_quantity), "tramo": qty(p.tier_min_quantity),
                               "precio_final": money(p.final_unit_price)} for p in result.products.values()],
                "pedidos": [{"id": o.order_id, "estado": o.status, "pagado": money(o.paid),
                             "costo": money(o.final_amount), "devuelto": money(o.refund_amount),
                             "destino": o.refund_destination} for o in result.orders.values()],
                "a_saldo": money(result.total_credited), "reembolsado": money(result.total_refunded)}

    def admin_armado(environ, data, session):
        cycle_id = query_cycle(environ)
        attended = sorted((o for o in store.orders_in_cycle(cycle_id) if fulfillment.is_attended(store, o)),
                          key=lambda o: o.order_id)
        names = names_for(cycle_id)
        zone_ids = sorted({o.zone_id for o in attended})
        stops = []
        for zone_id in zone_ids:
            delivery = store.deliveries.get((cycle_id, zone_id))
            failed = store.failed_deliveries.get((cycle_id, zone_id))
            stops.append({"zona": zone_json(store.zones[zone_id]),
                          "entrega": ({"recibe": delivery.received_by, "foto": delivery.photo,
                                       "pedidos": len(delivery.order_ids)} if delivery else None),
                          "fallida": bool(failed), "en_camino": (cycle_id, zone_id) in store.dispatches})  # S-308
        orders = [order_json(o, names, clock()) | {
            "vecino": store.customers[o.customer_id].name,
            "bolsas": [{"numero": b.number, "foto": b.photo, "productos": store.bag_reviews.get((o.order_id, b.number), [])} for b in store.bags.get(o.order_id, [])],
            "rotulos": fulfillment.bag_labels(store, o.order_id)} for o in attended]  # RT-01
        if session["kind"] == partners.PACKER:  # AM-01, S-290
            orders = [{key: o[key] for key in PACKER_ORDER + ("rotulos",)} | {
                "lineas": [{k: line[k] for k in ("id", "nombre", "cantidad", "unidad")} for line in o["lineas"]]} for o in orders]
        return {"ciclo": cycle_id, "ciclos": known_cycles(), "paradas": stops, "pedidos": orders}

    def vision_analizar(environ, data, session):
        return vision.analyze_photo(data.get('_vision_upload'))

    def admin_bolsa(environ, data, session):
        try:
            review = json.loads(data.get('revision', '[]'))
        except (ValueError, TypeError):
            raise BusinessRuleError('INVALID_BAG_REVIEW', 'La revisión de la bolsa no es válida.')
        bag = fulfillment.pack_bag(store, _int(data.get("pedido"), "Número de pedido"), by=session["principal"],
                                   photo=data.get("foto", ""), now=clock(), review=review)
        return {"pedido": bag.order_id, "numero": bag.number, "foto": bag.photo}

    def admin_bolsa_quitar(environ, data, session):
        bag = fulfillment.remove_bag(store, _int(data.get('pedido'), 'Pedido'), _int(data.get('numero'), 'Bolsa'),
                                     by=session['principal'], now=clock())
        return {'pedido': bag.order_id, 'numero': bag.number}

    def admin_entrega(environ, data, session):
        delivery = fulfillment.deliver_zone(store, str(data.get("ciclo", "")).strip(), str(data.get("zona", "")),
                                            by=session["principal"], photo=data.get("foto", ""),
                                            received_by=data.get("recibe", ""), now=clock())
        tell(notices.delivered, delivery)
        return {"zona": delivery.zone_id, "pedidos": len(delivery.order_ids), "recibe": delivery.received_by}

    def admin_entrega_fallida(environ, data, session):
        failure = fulfillment.register_failed_delivery(store, str(data.get("ciclo", "")).strip(), str(data.get("zona", "")),
                                                       by=session["principal"], photo=data.get("foto", ""),
                                                       reason=data.get("motivo", ""), now=clock())
        tell(notices.delivery_failed, failure)
        return {"zona": failure.zone_id, "pedidos": len(failure.order_ids)}

    def admin_reclamos(environ, data, session):
        return {"reclamos": [claim_json(c) | {"vecino": store.customers[c.customer_id].name}
                             for c in store.claims.values()]}

    def admin_revisar(environ, data, session, claim_id):
        decision = data.get("decision")
        if decision not in ("aprobar", "rechazar"):
            raise BusinessRuleError("INVALID_INPUT", "Elige aprobar o rechazar.")
        claim = claims.review_claim(store, _int(claim_id, "Reclamo"), by=session["principal"],
                                    approve=decision == "aprobar", now=clock())
        tell(notices.claim_reviewed, claim)
        return claim_json(claim)

    def admin_pedidos(environ, data, session):
        """OC-01, OC-02, S-330: los pedidos de la semana para elegir uno, sin montos ni productos."""
        cycle_id = query_cycle(environ)
        return {"ciclo": cycle_id, "ciclos": known_cycles(),
                "pedidos": [{"id": o.order_id, "vecino": store.customers[o.customer_id].name,
                             "zona": store.zones[o.zone_id].name if o.zone_id in store.zones else o.zone_id, "estado": o.status}
                            for o in sorted(store.orders_in_cycle(cycle_id), key=lambda o: o.order_id)]}

    def admin_devoluciones(environ, data, session):
        return {"devoluciones": [{"id": r.refund_id, "cliente": r.customer_id,
                                  "vecino": store.customers[r.customer_id].name, "monto": money(r.amount),
                                  "motivo": r.reason, "estado": r.status,
                                  "vence": r.due_date.date().isoformat() if r.due_date else None}
                                 for r in store.refunds.values() if r.status == "PENDIENTE"]}

    def admin_devolucion_pagar(environ, data, session, refund_id):
        refund = wallet.mark_refund_paid(store, _int(refund_id, "Devolución"), str(data.get("codigo", "")))
        tell(notices.refund_paid, refund)
        return {"id": refund.refund_id, "estado": refund.status}

    def admin_conciliacion(environ, data, session):
        b = audit.money_balance(store)
        return {"recibido": money(b.received), "en_curso": money(b.in_flight), "retenido": money(b.kept),
                "deuda": money(b.owed), "devoluciones_pagadas": money(b.refunds_paid),
                "diferencia": money(b.difference), "cuadra": b.difference == 0}

    def admin_metricas(environ, data, session):
        cycle_id = query_cycle(environ)
        margins = metrics.order_margins(store, cycle_id)
        alerts = metrics.margin_alerts(store, cycle_id)
        savings = metrics.delivered_savings(store, cycle_id)
        try:
            r = metrics.repurchase_week4(store, cycle_id)
            repurchase = {"cohorte": r.cohort_cycle, "vecinos": r.cohort_size, "volvieron": r.returned,
                          "tasa": money(r.rate), "cumple": r.meets_target}
        except BusinessRuleError as error:
            repurchase = {"error": {"codigo": error.code, "mensaje": str(error)}}
        compared = reference.reference_savings(store, cycle_id)
        costs, freight, estimated = logistics.real_costs(store, cycle_id)  # MR-01, MR-02
        summary = metrics.net_margin_summary(store, cycle_id, costs) if margins else None
        real = {"flete": money(freight), "estimado": estimated, "por_pedido": money(costs.purchase_trip),
                "promedio": money(summary.average_net_margin) if summary else None,
                "pierden": summary.losing_orders if summary else 0}
        return {"ciclo": cycle_id, "ciclos": known_cycles(), "margen_real": real,
                "margenes": [{"pedido": m.order_id, "cobrado": money(m.revenue), "reclamos": money(m.claims),
                              "proveedor": money(m.product_cost), "parada": money(m.stop_cost),
                              "margen": money(m.margin), "negativo": m.order_id in alerts}
                             for m in sorted(margins.values(), key=lambda m: m.order_id)],
                "ahorro": {"volumen": money(savings.volume), "envio": money(savings.delivery),
                           "total": money(savings.total)},
                "recompra": repurchase,
                "frente_a": {kind: {"canastas": c.baskets, "costaba": money(c.reference_total),
                                    "yapa": money(c.yapa_total), "ahorro": money(c.savings),
                                    "porcentaje": money(c.percent) if c.percent is not None else None}
                             for kind, c in compared.items()}}

    def admin_catalogo(environ, data, session):
        label = query_cycle(environ) if "ciclo=" in environ.get("QUERY_STRING", "") else \
            cycle.add_weeks(cycle.cycle_id(clock()), 1)
        products = list(store.catalog_for(label).values())
        return {"ciclo": label, "ciclos": known_cycles(ahead=2), "publicado": label in store.catalogs,
                "lista": export_catalog(products),
                "productos": [{"id": p.product_id, "nombre": p.name, "unidad": p.unit, "activo": p.active,
                               "precio_max": money(p.max_unit_price()), "maximo": qty(p.max_available),
                               "tramos": [{"desde": qty(t.min_quantity), "precio": money(t.base_price)}
                                          for t in p.tiers]} for p in products]}

    def admin_catalogo_publicar(environ, data, session):
        label = str(data.get("ciclo", "")).strip()
        cycle.check_cycle_id(label)
        published = publish_catalog(store, label, parse_catalog(data.get("lista", "")), by=session["principal"],
                                    now=clock())
        return {"ciclo": label, "productos": len(published)}

    def admin_catalogo_desactivar(environ, data, session):
        label = str(data.get("ciclo", "")).strip()
        cycle.check_cycle_id(label)
        product = deactivate_product(store, label, str(data.get("producto", "")), by=session["principal"])
        return {"id": product.product_id, "activo": product.active}

    def admin_referencias(environ, data, session):
        today = cycle.to_lima(clock()).date()
        products = [p for p in store.catalog_for(cycle.cycle_id(clock())).values() if p.active]
        return {"productos": [{"id": p.product_id, "nombre": p.name, "precio_max": money(p.max_unit_price()),
                               "referencias": {kind: {"precio": money(r.price), "fuente": r.source,
                                                      "visto": r.observed_on.isoformat(),
                                                      "ahorro": money(reference.savings_percent(p.max_unit_price(),
                                                                                                r.price))}
                                               for kind, r in reference.current_references(store, p.product_id,
                                                                                            today).items()}}
                              for p in products]}

    def admin_referencia_registrar(environ, data, session):
        try:
            observed = date.fromisoformat(str(data.get("fecha", "")).strip())
        except ValueError:
            raise BusinessRuleError("INVALID_INPUT", "Fecha no válida; usa el formato AAAA-MM-DD.")
        saved = reference.register_reference(store, str(data.get("producto", "")), str(data.get("tipo", "")),
                                             _money_in(data.get("precio"), "Precio"), data.get("fuente", ""),
                                             observed, by=session["principal"], now=clock())
        return {"producto": saved.product_id, "precio": money(saved.price), "fuente": saved.source}, [], "201 Created"

    def admin_vecinos(environ, data, session):
        return {"vecinos": [{"id": c.customer_id, "nombre": c.name, "celular": c.phone, "zona": c.zone_id,
                             "consentimiento": c.consent_at.isoformat() if c.consent_at else None,
                             "suspendido": c.suspended}
                            for c in sorted(store.customers.values(), key=lambda c: c.customer_id)]}

    def admin_vecino_alta(environ, data, session):
        customer, pin = customers.register_customer(store, data.get("nombre", ""), data.get("celular", ""),
                                                    str(data.get("zona", "")), bool(data.get("consentimiento")),
                                                    by=session["principal"], now=clock(),
                                                    email=str(data.get("correo", "")),
                                                    referral=str(data.get("referido", "")))
        return {"id": customer.customer_id, "nombre": customer.name, "pin": pin}, [], "201 Created"

    def admin_vecino_pin(environ, data, session, customer_id):
        pin = customers.reset_pin(store, _int(customer_id, "Vecino"), by=session["principal"])
        return {"id": int(customer_id), "pin": pin}

    def send_code(to: str, subject: str, intro: str, code: str) -> None:
        mailer.send(to, subject, f"{intro}\n\nTu código es {code}. Vale 10 minutos.\nSi no lo pediste tú, ignora este mensaje: nadie puede entrar a tu cuenta sin él.\n\nYapa")

    def pin_olvide(environ, data, session):
        """OP-01, CR-05, S-196, S-205: siempre la misma respuesta, exista o no el número y tenga o no correo verificado."""
        ip = client_ip(environ)
        if mails.blocked(ip, security()):  # SG-10: la respuesta no cambia (S-196)
            sent = None
        else:
            sent = recovery.request_pin_reset(store, customers.resolve_login(store, data.get("usuario")), clock())  # S-246
        if sent:
            mails.hit(ip, security())
            try:
                send_code(sent[0], "Recupera tu PIN de Yapa", "Pediste cambiar tu PIN.", sent[1])
            except MailError:
                traceback.print_exc(file=environ.get("wsgi.errors"))  # CR-09: la respuesta no cambia
        return {"mensaje": "Si tu número está registrado, te mandaremos las instrucciones al correo que verificaste o, si no tienes, el equipo de Yapa te escribirá por WhatsApp al celular que registraste."}

    def pin_restablecer(environ, data, session):
        """CR-06."""
        counting_failures(environ, lambda: recovery.reset_pin_with_code(
            store, customers.resolve_login(store, data.get("usuario")), data.get("codigo"), data.get("pin"), clock()))
        return {"mensaje": "Listo: ya puedes entrar con tu PIN nuevo."}

    def cuenta_retirar(environ, data, session):
        """RD-01..RD-06: el vecino retira su consentimiento; su sesión se cierra en la siguiente llamada (SG-05)."""
        customers.withdraw_consent(store, session["principal"], data.get("confirmar"), now=clock())
        return {"mensaje": "Listo. Borramos tus datos personales y cerramos tu cuenta."}

    def cuenta_correo(environ, data, session):
        """CR-02, CR-09."""
        email, code = recovery.start_email_verification(store, session["principal"], data.get("correo"), clock())
        try:
            send_code(email, "Verifica tu correo en Yapa", "Estás agregando este correo a tu cuenta de Yapa.", code)
        except MailError:
            raise BusinessRuleError("EMAIL_SEND_FAILED", "No pudimos enviar el correo. Revisa que esté bien escrito e inténtalo de nuevo.") from None
        return {"enviado": True}

    def cuenta_correo_verificar(environ, data, session):
        """CR-03."""
        recovery.confirm_email(store, session["principal"], data.get("codigo"), clock())
        return {"correo_verificado": True}

    def admin_pin_solicitudes(environ, data, session):
        """OP-06, OP-09: nunca lleva un PIN."""
        return {"solicitudes": [{"id": rid, "cliente": cid, "vecino": store.customers[cid].name,
                                 "celular": store.customers[cid].phone, "hora": at.isoformat()}
                                for rid, (cid, at) in sorted(store.pin_requests.items(), key=lambda item: item[1][1])]}

    def admin_pin_descartar(environ, data, session, request_id):
        customers.dismiss_pin_request(store, _int(request_id, "Solicitud"), by=session["principal"])
        return {"descartada": True}

    def avisos(environ, data, session):
        """AV-01."""
        customer = store.customers[session["principal"]]
        mine = notices.for_customer(store, customer.customer_id)
        return {"avisos": [{"id": n.notice_id, "tipo": n.kind, "titulo": n.title, "texto": n.body,
                            "hora": n.created_at.isoformat(), "leido": n.read_at is not None} for n in mine],
                "sin_leer": sum(1 for n in mine if n.read_at is None), "correo_avisos": customer.email_notices,
                "correo_verificado": customer.email_verified_at is not None}

    def avisos_leer(environ, data, session):
        """AV-02."""
        notice_id = _int(data["id"], "Aviso") if data.get("id") not in (None, "") else None
        notices.mark_read(store, session["principal"], notice_id, clock())
        return {"sin_leer": notices.unread_count(store, session["principal"])}

    def avisos_preferencias(environ, data, session):
        """AV-03."""
        if not isinstance(data.get("avisos_correo"), bool):
            raise BusinessRuleError("INVALID_INPUT", "Elige si quieres recibir los avisos por correo.")
        notices.set_email_preference(store, session["principal"], data["avisos_correo"])
        return {"correo_avisos": data["avisos_correo"]}

    def admin_colchon(environ, data, session):
        return {"valor": money(buffer.buffer_value(store)), "tope": money(buffer.BUFFER_LIMIT),
                "stock": [{"producto": s.product_id, "nombre": names_for(cycle.cycle_id(clock())).get(s.product_id, s.product_id),
                           "cantidad": qty(s.quantity), "valor": money(s.value)} for s in store.buffer.values()]}  # OC-03

    def partner_json(partner) -> dict:
        return {"usuario": partner.user, "tipo": partner.kind, "nombre": partner.name, "proveedor": partner.supplier_id,
                "zona": partner.zone_id, "activa": partner.active}

    def admin_cuentas(environ, data, session):
        return {"cuentas": [partner_json(p) for p in sorted(store.partners.values(), key=lambda p: p.user)],
                "proveedores": [{"id": s.supplier_id, "nombre": s.name} for s in store.suppliers.values() if s.allied],
                "zonas": [{"id": z.zone_id, "nombre": z.name, "distrito": z.district}
                          for z in sorted(store.zones.values(), key=lambda z: z.zone_id)]}

    def admin_cuenta_crear(environ, data, session):
        """CX-01..CX-04."""
        user, password = str(data.get("usuario", "")), str(data.get("contrasena", ""))
        if data.get("tipo") == partners.DRIVER:
            partner = partners.create_driver(store, user, str(data.get("nombre", "")), password,
                                             by=session["principal"], now=clock())
        elif data.get("tipo") == partners.SUPPLIER:
            partner = partners.create_supplier_account(store, user, str(data.get("proveedor", "")), password,
                                                       by=session["principal"], now=clock(), name=str(data.get("nombre", "")))
        elif data.get("tipo") in partners.STAFF_KINDS:  # CX-07, CX-08
            partner = partners.create_staff(store, user, data["tipo"], str(data.get("nombre", "")), password,
                                            by=session["principal"], now=clock(), zone_id=data.get("zona"))
        else:
            raise BusinessRuleError("INVALID_INPUT", "Elige el tipo de cuenta.")
        return partner_json(partner), [], "201 Created"

    def admin_cuenta_desactivar(environ, data, session, user):
        return partner_json(partners.deactivate(store, user, by=session["principal"]))  # CX-05

    def admin_cuenta_contrasena(environ, data, session, user):
        return partner_json(partners.set_password(store, user, str(data.get("contrasena", "")), by=session["principal"]))

    def reparto(environ, data, session):
        """TR-01, S-282: paradas con bolsas por pedido, sin nombres, celulares ni montos."""
        cycle_id = query_cycle(environ)
        attended = sorted((o for o in store.orders_in_cycle(cycle_id) if fulfillment.is_attended(store, o)),
                          key=lambda o: o.order_id)
        stops = []
        for zone_id in sorted({o.zone_id for o in attended}):
            zone = store.zones[zone_id]
            delivery = store.deliveries.get((cycle_id, zone_id))
            state = "entregada" if delivery else "fallida" if (cycle_id, zone_id) in store.failed_deliveries \
                else "en_camino" if (cycle_id, zone_id) in store.dispatches else "pendiente"  # S-308
            stops.append({"zona": {"id": zone.zone_id, "nombre": zone.name, "distrito": zone.district, "lat": zone.lat,
                                   "lon": zone.lon, "recibe": zone.reception_kind, "contacto": zone.reception_contact},
                          "estado": state, "recibio": delivery.received_by if delivery else None,
                          "pedidos": [{"id": o.order_id, "bolsas": len(store.bags.get(o.order_id, []))}
                                      for o in attended if o.zone_id == zone_id]})
        return {"ciclo": cycle_id, "ciclos": known_cycles(), "cerrado": clock() >= cycle.closes_at(cycle_id),
                "paradas": stops}

    def reparto_salida(environ, data, session):
        """SR-01, SR-02: el reparto sale hacia una zona."""
        dispatch = logistics.dispatch_zone(store, str(data.get("ciclo", "")).strip(), str(data.get("zona", "")),
                                           by=session["principal"], now=clock())
        return {"zona": dispatch.zone_id, "pedidos": len(dispatch.order_ids)}

    def compras_flete(environ, data, session):
        """FL-01..FL-04."""
        freight = logistics.register_freight(store, str(data.get("ciclo", "")).strip(), data.get("empresa"),
                                             data.get("monto"), by=session["principal"], now=clock())
        return {"ciclo": freight.cycle, "empresa": freight.company, "monto": money(freight.amount)}

    def reparto_ruta(environ, data, session):
        week=str(data.get('ciclo',''));cycle.check_cycle_id(week)
        try:ids=json.loads(data.get('zonas','[]'))
        except (ValueError,TypeError):raise BusinessRuleError('INVALID_ROUTE','La lista de paradas no es válida.')
        if not isinstance(ids,list) or not 2<=len(ids)<=25 or not all(isinstance(z,str) for z in ids) or len(set(ids))!=len(ids):
            raise BusinessRuleError('INVALID_ROUTE','Elige entre 2 y 25 zonas distintas.')
        allowed={o.zone_id for o in store.orders_in_cycle(week) if fulfillment.is_attended(store,o)}
        if any(z not in allowed or (week,z) in store.deliveries or (week,z) in store.failed_deliveries for z in ids):
            raise BusinessRuleError('INVALID_ROUTE','La ruta solo puede incluir zonas pendientes de esta semana.')
        return street_route([(store.zones[z].lon,store.zones[z].lat) for z in ids])

    def reparto_entrega(environ, data, session):
        return admin_entrega(environ, data, session)  # TR-02: mismas reglas; el motor revisa quién entrega

    def reparto_entrega_fallida(environ, data, session):
        return admin_entrega_fallida(environ, data, session)  # TR-03

    def offer_json(offer) -> dict:
        return {"ciclo": offer.cycle, "proveedor": offer.supplier_id, "nombre_proveedor": store.suppliers[offer.supplier_id].name,
                "estado": offer.status, "enviada": offer.sent_at.isoformat(), "motivo": offer.reason,
                "lista": export_catalog(offer.products),
                "productos": [{"id": p.product_id, "nombre": p.name, "unidad": p.unit, "maximo": qty(p.max_available),
                               "tramos": [{"desde": qty(t.min_quantity), "precio": money(t.base_price)} for t in p.tiers]}
                              for p in offer.products]}

    def proveedor(environ, data, session):
        """PV-06."""
        supplier_id = store.partners[session["principal"]].supplier_id
        order = supplier_offers.supplier_order(store, query_cycle(environ), supplier_id, clock())
        order = supplier_lines(order)
        offers = sorted((o for o in store.supplier_offers.values() if o.supplier_id == supplier_id),
                        key=lambda o: o.cycle, reverse=True)
        current = cycle.cycle_id(clock())
        return {"proveedor": {"id": supplier_id, "nombre": store.suppliers[supplier_id].name},
                "ciclos": known_cycles(), "proximo": cycle.add_weeks(current, 1), "pedido": order,
                "propuestas": [offer_json(o) for o in offers],
                "lista_actual": export_catalog(p for p in store.catalog_for(cycle.add_weeks(current, 1)).values()
                                               if p.supplier_id == supplier_id)}

    def proveedor_stock(environ, data, session):
        return supplier_stock.snapshot(store, session['principal'], query_cycle(environ))

    def proveedor_stock_confirmar(environ, data, session):
        try:
            rows=json.loads(data.get('conteo','[]'))
        except (ValueError,TypeError):
            raise BusinessRuleError('INVALID_STOCK_ITEM','El conteo de la carga no es válido.')
        return supplier_stock.confirm(store,session['principal'],data.get('ciclo',''),rows,data.get('_stock_upload'),clock())

    def asistente(environ, data, session):
        """AS-01..AS-05: el asistente de compra responde con los datos de este vecino."""
        customer = store.customers[session["principal"]]
        return assistant.answer(store, ai, customer.customer_id, data.get("pregunta"), clock(),
                                group_progress(store.zones[customer.zone_id]))

    def proveedor_lista_leer(environ, data, session):
        """LP-01..LP-06: la cotización (foto o texto) como borrador de la lista; no guarda nada."""
        result = quote_reader.read_quote(store, ai, session["principal"], text=data.get("texto", ""),
                                         photo=data.get("_quote_upload"), now=clock())
        rows = [r | {"paso": qty(r["paso"]), "maximo": qty(r["maximo"]),
                     "tramos": [{"desde": qty(t["desde"]), "precio": money(t["precio"])} for t in r["tramos"]]}
                for r in result["filas"]]
        return result | {"filas": rows}

    def proveedor_propuesta(environ, data, session):
        offer = supplier_offers.submit_offer(store, str(data.get("ciclo", "")).strip(), str(data.get("lista", "")),
                                             by=session["principal"], now=clock())  # PV-01..PV-03
        return offer_json(offer), [], "201 Created"

    def admin_propuestas(environ, data, session):
        offers = sorted(store.supplier_offers.values(), key=lambda o: (o.status != "PENDIENTE", o.cycle, o.supplier_id))
        return {"propuestas": [offer_json(o) for o in offers]}

    def admin_propuesta_aprobar(environ, data, session, cycle_id, supplier_id):
        return offer_json(supplier_offers.approve_offer(store, cycle_id, supplier_id, by=session["principal"], now=clock()))

    def admin_propuesta_rechazar(environ, data, session, cycle_id, supplier_id):
        return offer_json(supplier_offers.reject_offer(store, cycle_id, supplier_id, str(data.get("motivo", "")),
                                                       by=session["principal"], now=clock()))

    def supplier_lines(order: dict) -> dict:
        order["lineas"] = [line | {"cantidad": qty(line["cantidad"]), "desde": qty(line["desde"]),
                                   "precio": money(line["precio"]), "monto": money(line["monto"])} for line in order["lineas"]]
        order["total"] = money(order["total"])
        return order

    def compras(environ, data, session):
        """CP-01, S-291: lo que hay que comprarle a cada proveedor aliado en el ciclo, y el colchón."""
        cycle_id = query_cycle(environ)
        suppliers = []
        for supplier in sorted(store.suppliers.values(), key=lambda s: s.supplier_id):
            if not supplier.allied:
                continue
            order = supplier_lines(supplier_offers.supplier_order(store, cycle_id, supplier.supplier_id, clock()))
            if order["lineas"]:
                suppliers.append({"id": supplier.supplier_id, "nombre": supplier.name} | order)
        bought = store.purchases.get(cycle_id)
        real = None if bought is None else {  # CR-05: lo que faltó y a qué pedido fue
            "recibido": {p: qty(q) for p, q in bought.received.items()},
            "faltantes": [shortage_json(s) for s in store.shortages if s.cycle == cycle_id]}
        keepable = [{"id": p.product_id, "nombre": p.name, "unidad": p.unit} for p in store.catalog_for(cycle_id).values()
                    if p.category in buffer.NON_PERISHABLE and p.active]  # OC-04, S-329
        return {"ciclo": cycle_id, "ciclos": known_cycles(), "proveedores": suppliers,
                "parcial": cycle.to_lima(clock()) < cycle.closes_at(cycle_id), "colchon": admin_colchon(environ, data, session),
                "compra_real": real, "flete": freight_json(store.freights.get(cycle_id)), "guardables": keepable,
                "prediccion": forecast_json(forecast.forecast(store, cycle_id, clock()))}  # PD-01

    def forecast_json(f: dict) -> dict:
        """PD-01..PD-04: cantidades como texto, igual que el resto de la API."""
        products = [p | {"historia": [qty(q) for q in p["historia"]], "estimado": qty(p["estimado"]),
                         "pedido": qty(p["pedido"]), "maximo": qty(p["maximo"])} for p in f["productos"]]
        zones = [z | {"productos": [p | {"estimado": qty(p["estimado"])} for p in z["productos"]]} for z in f["zonas"]]
        return f | {"productos": products, "zonas": zones,
                    "error_medio": None if f["error_medio"] is None else f"{f['error_medio']}"}

    def freight_json(f) -> dict | None:
        return {"empresa": f.company, "monto": money(f.amount)} if f else None

    def shortage_json(s) -> dict:
        return {"pedido": s.order_id, "producto": s.product_id, "cantidad": qty(s.quantity),
                "colchon": qty(s.from_buffer), "origen": s.source,
                "nombre": names_for(s.cycle).get(s.product_id, s.product_id)}  # OC-03

    def compras_recibido(environ, data, session):
        """CR-01..CR-05: lo que llegó del proveedor; lo que falta se reparte solo."""
        received = data.get("recibido") or {}
        if not isinstance(received, dict) or not all(
                isinstance(v, (str, int, float)) and not isinstance(v, bool) for v in received.values()):
            raise BusinessRuleError("INVALID_INPUT", "Indica lo recibido por producto.")
        cycle_id = str(data.get("ciclo", "")).strip()
        purchase.register_purchase(store, cycle_id, received, by=session["principal"], now=clock())
        return {"ciclo": cycle_id, "faltantes": [shortage_json(s) for s in store.shortages if s.cycle == cycle_id]}

    def admin_danado(environ, data, session):
        """DA-01..DA-06."""
        shortage = purchase.register_damaged(store, _int(data.get("pedido"), "Número de pedido"),
                                             str(data.get("producto", "")), data.get("cantidad"),
                                             by=session["principal"], photo=data.get("foto", ""), now=clock())
        return shortage_json(shortage)

    def incident_json(i) -> dict:
        return {"id": i.incident_id, "pedido": i.order_id, "tipo": i.kind, "descripcion": i.description,
                "estado": i.status, "nota": i.note, "abierta": i.opened_at.isoformat(),
                "cerrada": i.closed_at.isoformat() if i.closed_at else None}

    def admin_incidencias(environ, data, session):
        return {"incidencias": [incident_json(i) for i in sorted(store.incidents.values(),
                                                                 key=lambda i: (i.status != "ABIERTA", -i.incident_id))]}

    def admin_incidencia_abrir(environ, data, session):
        """IN-01, IN-02."""
        return incident_json(incidents.open_incident(store, _int(data.get("pedido"), "Número de pedido"),
                                                     str(data.get("tipo", "")), data.get("descripcion"),
                                                     by=session["principal"], now=clock()))

    def admin_incidencia_cerrar(environ, data, session, incident_id):
        """IN-03."""
        return incident_json(incidents.close_incident(store, _int(incident_id, "Incidencia"), data.get("nota"),
                                                      by=session["principal"], now=clock()))

    def compras_colchon(environ, data, session):
        """CP-02."""
        stock = buffer.add_to_buffer(store, str(data.get("ciclo", "")).strip(), str(data.get("producto", "")),
                                     data.get("cantidad"), by=session["principal"])
        return {"producto": stock.product_id, "cantidad": qty(stock.quantity), "valor": money(stock.value)}

    def compras_colchon_usar(environ, data, session):
        """CP-03."""
        stock = buffer.use_buffer(store, str(data.get("producto", "")), data.get("cantidad"),
                                  order_id=_int(data.get("pedido"), "Número de pedido"), by=session["principal"], now=clock())
        return {"producto": stock.product_id, "cantidad": qty(stock.quantity), "valor": money(stock.value)}

    def concierge_zone(session) -> str:
        return store.partners[session["principal"]].zone_id

    def administered_zone(session) -> str:
        zone = next((z for z in store.zones.values() if z.admin_id == session["principal"]), None)
        if zone is None:  # PO-02
            raise BusinessRuleError("FOREIGN_ZONE", "Solo el admin de la zona ve y confirma su recepción.")
        return zone.zone_id

    def confirm_in(zone_id, data, session) -> dict:
        received = reception.confirm_reception(store, str(data.get("ciclo", "")).strip(), zone_id,
                                               by=session["principal"], now=clock())
        tell(notices.in_building, received)  # PO-04
        return reception.for_zone(store, received.cycle, zone_id)

    def porteria(environ, data, session):
        """PO-01, S-293."""
        return reception.for_zone(store, query_cycle(environ), concierge_zone(session)) | {"ciclos": known_cycles()}

    def porteria_recepcion(environ, data, session):
        return confirm_in(concierge_zone(session), data, session)

    def zona_recepcion(environ, data, session):
        """PO-01 para el admin de zona (S-294)."""
        return reception.for_zone(store, query_cycle(environ), administered_zone(session))

    def zona_recepcion_confirmar(environ, data, session):
        return confirm_in(administered_zone(session), data, session)

    # ruta (expresión) -> método -> (función, rol requerido o tupla de roles, CX-09)
    routes = [
        (r"/api/estado", {"GET": (estado, None)}),
        (r"/api/catalogo", {"GET": (catalogo, None)}),
        (r"/api/zonas", {"GET": (zonas, None), "POST": (zona_crear, "vecino")}),
        (r"/api/sesion", {"POST": (sesion_entrar, None), "GET": (sesion_ver, "any"), "DELETE": (sesion_salir, "any")}),
        (r"/api/cotizar", {"POST": (cotizar, "vecino")}),
        (r"/api/pedidos", {"POST": (pedidos, "vecino")}),
        (r"/api/mis-pedidos", {"GET": (mis_pedidos, "vecino")}),
        (r"/api/pedidos/(\d+)/fotos/([\w-]+)", {"GET": (pedido_foto, "vecino")}),
        (r"/api/canasta/sugerir", {"POST": (canasta_sugerir, "vecino")}),
        (r"/api/admin/ia/atencion", {"POST": (admin_ia_atencion, ATTENDING)}),
        (r"/api/pedidos/(\d+)/cancelar", {"POST": (cancelar, "vecino")}),
        (r"/api/saldo/devolucion", {"POST": (devolucion, "vecino")}),
        (r"/api/pin", {"POST": (cambiar_pin, "vecino")}),
        (r"/api/admin/ver-como", {"POST": (ver_como, "admin")}),
        (r"/api/sesion/volver", {"POST": (sesion_volver, "any")}),
        (r"/api/pin/crear", {"POST": (crear_pin, "vecino")}),
        (r"/api/reclamos", {"GET": (reclamos, "vecino"), "POST": (reclamar, "vecino")}),
        (r"/api/mi-zona", {"GET": (mi_zona, "vecino")}),
        (r"/api/ubicacion", {"POST": (ubicacion, "vecino")}),
        (r"/api/zonas/([\w-]+)/unirme", {"POST": (zona_unirme, "vecino")}),
        (r"/api/zonas/([\w-]+)/activar", {"POST": (zona_activar, "vecino")}),
        (r"/api/zonas/([\w-]+)/unir", {"POST": (zona_unir, "vecino")}),
        (r"/api/zonas/([\w-]+)/separar", {"POST": (zona_separar, "vecino")}),
        (r"/api/zonas/([\w-]+)/transferir", {"POST": (zona_transferir, "vecino")}),
        (r"/api/solicitudes/(\d+)/aceptar", {"POST": (solicitud_aceptar, "vecino")}),
        (r"/api/solicitudes/(\d+)/rechazar", {"POST": (solicitud_rechazar, "vecino")}),
        (r"/api/solicitudes/(\d+)/retirar", {"POST": (solicitud_retirar, "vecino")}),
        (r"/api/admin/resumen", {"GET": (admin_resumen, "admin")}),
        (r"/api/admin/foto", {"GET": (admin_foto, PHOTO_VIEWERS)}),
        (r"/api/admin/pedidos/(\d+)/verificar", {"POST": (admin_verificar, "admin")}),
        (r"/api/admin/ciclos/(\d{4}-W\d{2})/liquidar", {"POST": (admin_liquidar, "admin")}),
        (r"/api/admin/armado", {"GET": (admin_armado, PACKING)}),
        (r"/api/vision/analizar", {"POST": (vision_analizar, ("admin", partners.PACKER, partners.SUPPLIER))}),
        (r"/api/admin/bolsas/quitar", {"POST": (admin_bolsa_quitar, PACKING)}),
        (r"/api/admin/bolsas", {"POST": (admin_bolsa, PACKING)}),
        (r"/api/admin/danados", {"POST": (admin_danado, PACKING)}),
        (r"/api/admin/incidencias", {"GET": (admin_incidencias, ATTENDING), "POST": (admin_incidencia_abrir, ATTENDING)}),
        (r"/api/admin/incidencias/(\d+)/cerrar", {"POST": (admin_incidencia_cerrar, ATTENDING)}),
        (r"/api/admin/entregas", {"POST": (admin_entrega, "admin")}),
        (r"/api/admin/salidas", {"POST": (reparto_salida, "admin")}),
        (r"/api/admin/entregas-fallidas", {"POST": (admin_entrega_fallida, "admin")}),
        (r"/api/admin/reclamos", {"GET": (admin_reclamos, ATTENDING)}),
        (r"/api/admin/reclamos/(\d+)/revisar", {"POST": (admin_revisar, ATTENDING)}),
        (r"/api/admin/pedidos", {"GET": (admin_pedidos, ATTENDING)}),  # OC-01
        (r"/api/admin/devoluciones", {"GET": (admin_devoluciones, ATTENDING)}),
        (r"/api/admin/devoluciones/(\d+)/pagar", {"POST": (admin_devolucion_pagar, ATTENDING)}),
        (r"/api/admin/conciliacion", {"GET": (admin_conciliacion, "admin")}),
        (r"/api/admin/metricas", {"GET": (admin_metricas, "admin")}),
        (r"/api/admin/analisis", {"GET": (admin_analisis, "admin")}),
        (r"/api/admin/catalogo", {"GET": (admin_catalogo, "admin"), "POST": (admin_catalogo_publicar, "admin")}),
        (r"/api/admin/catalogo/desactivar", {"POST": (admin_catalogo_desactivar, "admin")}),
        (r"/api/admin/referencias", {"GET": (admin_referencias, "admin"), "POST": (admin_referencia_registrar, "admin")}),
        (r"/api/admin/vecinos", {"GET": (admin_vecinos, "admin"), "POST": (admin_vecino_alta, "admin")}),
        (r"/api/admin/vecinos/(\d+)/pin", {"POST": (admin_vecino_pin, ATTENDING)}),
        (r"/api/pin/olvide", {"POST": (pin_olvide, None)}),
        (r"/api/pin/restablecer", {"POST": (pin_restablecer, None)}),
        (r"/api/sesion/google", {"POST": (sesion_google, None)}),
        (r"/api/cuenta/google", {"POST": (cuenta_google, "vecino")}),
        (r"/api/cuenta/google/desvincular", {"POST": (cuenta_google_desvincular, "vecino")}),
        (r"/api/mi-invitacion", {"GET": (mi_invitacion, "vecino")}),
        (r"/api/mi-invitacion/renovar", {"POST": (mi_invitacion_renovar, "vecino")}),
        (r"/api/invitaciones/([\w-]+)", {"GET": (invitacion_ver, None)}),
        (r"/api/invitaciones/([\w-]+)/correo", {"POST": (invitacion_correo, None)}),
        (r"/api/invitaciones/([\w-]+)/confirmar", {"POST": (invitacion_confirmar, None)}),
        (r"/api/invitaciones/([\w-]+)/google", {"POST": (invitacion_google, None)}),
        (r"/api/cuenta/correo", {"POST": (cuenta_correo, "vecino")}),
        (r"/api/cuenta/retirar-consentimiento", {"POST": (cuenta_retirar, "vecino")}),
        (r"/api/cuenta/correo/verificar", {"POST": (cuenta_correo_verificar, "vecino")}),
        (r"/api/admin/pin-solicitudes", {"GET": (admin_pin_solicitudes, ATTENDING)}),
        (r"/api/admin/pin-solicitudes/(\d+)/descartar", {"POST": (admin_pin_descartar, ATTENDING)}),
        (r"/api/admin/colchon", {"GET": (admin_colchon, "admin")}),
        (r"/api/avisos", {"GET": (avisos, "vecino")}),
        (r"/api/avisos/leer", {"POST": (avisos_leer, "vecino")}),
        (r"/api/avisos/preferencias", {"POST": (avisos_preferencias, "vecino")}),
        (r"/api/admin/cuentas", {"GET": (admin_cuentas, "admin"), "POST": (admin_cuenta_crear, "admin")}),
        (r"/api/admin/cuentas/([a-z0-9-]+)/desactivar", {"POST": (admin_cuenta_desactivar, "admin")}),
        (r"/api/admin/cuentas/([a-z0-9-]+)/contrasena", {"POST": (admin_cuenta_contrasena, "admin")}),
        (r"/api/admin/propuestas", {"GET": (admin_propuestas, "admin")}),
        (r"/api/admin/propuestas/(\d{4}-W\d{2})/([\w-]+)/aprobar", {"POST": (admin_propuesta_aprobar, "admin")}),
        (r"/api/admin/propuestas/(\d{4}-W\d{2})/([\w-]+)/rechazar", {"POST": (admin_propuesta_rechazar, "admin")}),
        (r"/api/reparto/ruta", {"POST": (reparto_ruta, ("admin", partners.DRIVER))}),
        (r"/api/reparto", {"GET": (reparto, partners.DRIVER)}),
        (r"/api/reparto/entregas", {"POST": (reparto_entrega, partners.DRIVER)}),
        (r"/api/reparto/salidas", {"POST": (reparto_salida, partners.DRIVER)}),
        (r"/api/reparto/entregas-fallidas", {"POST": (reparto_entrega_fallida, partners.DRIVER)}),
        (r"/api/proveedor/stock", {"GET": (proveedor_stock, partners.SUPPLIER)}),
        (r"/api/proveedor/stock/confirmar", {"POST": (proveedor_stock_confirmar, partners.SUPPLIER)}),
        (r"/api/proveedor", {"GET": (proveedor, partners.SUPPLIER)}),
        (r"/api/proveedor/propuestas", {"POST": (proveedor_propuesta, partners.SUPPLIER)}),
        (r"/api/proveedor/lista/leer", {"POST": (proveedor_lista_leer, partners.SUPPLIER)}),  # LP-01
        (r"/api/asistente", {"POST": (asistente, "vecino")}),  # AS-01
        (r"/api/compras", {"GET": (compras, BUYING)}),
        (r"/api/compras/colchon", {"POST": (compras_colchon, BUYING)}),
        (r"/api/compras/colchon/usar", {"POST": (compras_colchon_usar, BUYING)}),
        (r"/api/compras/recibido", {"POST": (compras_recibido, BUYING)}),
        (r"/api/compras/flete", {"POST": (compras_flete, BUYING)}),
        (r"/api/porteria", {"GET": (porteria, partners.CONCIERGE)}),
        (r"/api/porteria/recepciones", {"POST": (porteria_recepcion, partners.CONCIERGE)}),
        (r"/api/zona/recepcion", {"GET": (zona_recepcion, "vecino")}),
        (r"/api/zona/recepciones", {"POST": (zona_recepcion_confirmar, "vecino")}),
    ]
    compiled = [(re.compile(pattern + r"/?"), methods) for pattern, methods in routes]

    def dispatch(environ):
        path = environ.get("PATH_INFO") or "/"
        method = environ.get("REQUEST_METHOD", "GET")
        for pattern, methods in compiled:
            match = pattern.fullmatch(path)
            if match:
                break
        else:
            raise ApiError("404 Not Found", "NOT_FOUND", "Esa ruta no existe.")
        if method not in methods:
            raise ApiError("405 Method Not Allowed", "METHOD_NOT_ALLOWED", "Método no permitido.")
        handler, role = methods[method]
        _, session = session_of(environ)
        if role and session is None:
            raise ApiError("401 Unauthorized", "LOGIN_REQUIRED", "Entra a tu cuenta para seguir.")
        if (isinstance(role, tuple) or role in KINDS) and session["kind"] not in (role if isinstance(role, tuple) else (role,)):  # CX-06, CX-09
            raise ApiError("403 Forbidden", "FORBIDDEN", "Esta acción no es para tu tipo de cuenta.")
        if method == "POST" and session is not None and session.get("viewing_as") and (path.rstrip("/") in credential_paths or VIEW_AS_BLOCKED.fullmatch(path.rstrip("/"))):
            raise BusinessRuleError("DEBUG_SESSION_READONLY", "Desde \"ver como\" no se pueden cambiar el PIN, el correo ni la cuenta de Google, ni sacar dinero o ceder una zona.")  # DM-08, SG-07
        if method in ("POST", "DELETE") and session is not None and handler is not sesion_entrar:  # S-155
            if not hmac.compare_digest(environ.get("HTTP_X_YAPA_CSRF", ""), session["csrf"]):
                raise ApiError("403 Forbidden", "CSRF", "La sesión venció. Recarga la página.")
        data, files = _body(environ) if method in ("POST", "DELETE") else ({}, {})
        if handler is vision_analizar:
            data['_vision_upload'] = files.get('foto_archivo')
        if handler is proveedor_lista_leer:
            data['_quote_upload'] = files.get('foto_archivo')
        if handler is proveedor_stock_confirmar:
            data['_stock_upload'] = files.get('foto_archivo')
        saved = ""
        if path.rstrip("/") in PHOTO_ROUTES and files.get("foto_archivo") and files["foto_archivo"][1]:  # S-151, SG-02
            saved = data["foto"] = _save_photo(photo_dir, files["foto_archivo"])
        try:
            result = handler(environ, data, session, *match.groups())
        except Exception:
            if saved:  # PH-01, PH-03: la foto de una acción que falló no se queda sin dueño
                (Path(photo_dir) / saved.split("/", 1)[1]).unlink(missing_ok=True)
            raise
        if isinstance(result, tuple):
            body, headers, *status = result
            return (status[0] if status else "200 OK"), body, headers
        return "200 OK", result, []

    def app(environ, start_response):
        try:
            status, body, headers = dispatch(environ)
        except BusinessRuleError as error:  # S-156
            status, body, headers = "422 Unprocessable Entity", {"error": {"codigo": error.code,
                                                                            "mensaje": str(error)}}, []
        except ApiError as error:
            status, body, headers = error.status, {"error": {"codigo": error.code, "mensaje": error.message}}, []
        except Exception:  # AD-05: el frontend siempre recibe JSON
            traceback.print_exc(file=environ.get("wsgi.errors"))
            status, body, headers = "500 Internal Server Error", {"error": {
                "codigo": "INTERNAL_ERROR", "mensaje": "Algo salió mal de nuestro lado. Intenta de nuevo."}}, []
        if environ.get("REQUEST_METHOD") in ("POST", "DELETE") and status[:1] == "2":
            send_notice_emails(environ.get("wsgi.errors"))  # antes de guardar: el aviso queda marcado como enviado
            if on_change:
                on_change(store)
        if isinstance(body, bytes):  # fotos: se entregan tal cual, con las cabeceras del manejador
            start_response(status, [("Content-Length", str(len(body)))] + headers)
            return [body]
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        start_response(status, [("Content-Type", "application/json; charset=utf-8"),
                                ("Content-Length", str(len(raw))), ("Cache-Control", "no-store")] + headers)
        return [raw]

    app.sessions = sessions  # SG-W: para comprobar la limpieza
    return app
