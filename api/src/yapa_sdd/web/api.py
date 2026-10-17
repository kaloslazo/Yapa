"""API JSON para el frontend React (iteración 27). Adaptador: no tiene reglas de negocio.

Spec: docs/desarrollo/27-api-json.md. Usa los mismos casos de uso que la web HTML (app.py).
"""

from __future__ import annotations

import hmac
import json
import re
import secrets
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from http.cookies import SimpleCookie
from urllib.parse import parse_qs

from .. import audit, auth, buffer, claims, customers, cycle, fulfillment, metrics, reference, wallet, zones
from ..catalog import deactivate_product, export_catalog, parse_catalog, publish_catalog
from ..domain import MAX_QUANTITY, MIN_ORDERS_PER_GROUP, MIN_SUBTOTAL, PILOT_DISTRICTS, BusinessRuleError
from ..settlement import ZONE_ADMIN_DISCOUNT, ZONE_ADMIN_DISCOUNT_WEEKS, _in_discount_weeks
from ..order_changes import cancel_order
from ..order_registration import quote_order, register_order, verify_payment
from ..store import InMemoryStore
from .app import _form, _save_photo


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
        return (data if isinstance(data, dict) else {}), {}
    return _form(environ)  # multipart con fotos (S-151) o formulario simple


def create_api(store: InMemoryStore, clock=None, on_change=None, photo_dir: str = "fotos"):
    clock = clock or (lambda: datetime.now(cycle.LIMA))
    sessions: dict[str, dict] = {}

    # --- ayudas ---

    def session_of(environ) -> tuple[str | None, dict | None]:
        cookie = SimpleCookie(environ.get("HTTP_COOKIE", ""))
        token = cookie[COOKIE].value if COOKIE in cookie else None
        session = sessions.get(token) if token else None
        if session and clock() >= session["expires"]:
            del sessions[token]
            session = None
        return token, session

    def role_of(session: dict) -> str:
        """S-157: el admin de zona es un vecino que administra una zona."""
        if session["kind"] == "admin":
            return "admin"
        administers = any(z.admin_id == session["principal"] for z in store.zones.values())
        return "admin_zona" if administers else "vecino"

    def names_for(cycle_id: str) -> dict[str, str]:
        return {p.product_id: p.name for p in store.catalog_for(cycle_id).values()}

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
        data = {
            "id": order.order_id, "ciclo": order.cycle, "zona": order.zone_id, "cliente": order.customer_id,
            "estado": order.status, "pago": order.payment_status, "metodo": order.payment_method,
            "codigo_pago": order.operation_code, "total": money(order.total), "subtotal": money(order.subtotal),
            "envio": money(order.delivery_fee), "con_saldo": money(order.paid_with_balance),
            "a_yapear": money(order.paid_external), "entregado": delivered,
            "cancelable": order.status == "REGISTRADO" and cycle.is_open(now) and cycle.cycle_id(now) == order.cycle,
            "lineas": [{"id": l.product_id, "nombre": names.get(l.product_id, l.product_id), "cantidad": qty(l.quantity),
                        "precio_max": money(l.max_unit_price), "total": money(l.max_total)} for l in order.lines],
        }
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
                "distritos": sorted(PILOT_DISTRICTS)}

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
        return {"zonas": [zone_json(z) for z in store.zones.values()]}

    # --- sesión (API-02) ---

    def sesion_entrar(environ, data, session):
        kind = data.get("tipo") if data.get("tipo") in ("vecino", "admin") else "vecino"
        principal = auth.authenticate(store, kind, data.get("usuario", ""), data.get("secreto", ""), clock())
        token = secrets.token_urlsafe(32)
        new = {"principal": principal, "kind": kind, "csrf": secrets.token_urlsafe(16),
               "expires": clock() + SESSION_TIME}
        sessions[token] = new
        cookie = f"{COOKIE}={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={int(SESSION_TIME.total_seconds())}"
        return me(new), [("Set-Cookie", cookie)]

    def me(session) -> dict:
        data = {"rol": role_of(session), "csrf": session["csrf"], "usuario": session["principal"]}
        if session["kind"] == "vecino":
            customer = store.customers[session["principal"]]
            data.update({"nombre": customer.name, "zona": customer.zone_id,
                         "saldo": money(wallet.balance(store, customer.customer_id)),
                         "codigo_referido": customers.referral_code(customer)})
        else:
            data.update({"nombre": "Equipo Yapa"})
        return data

    def sesion_ver(environ, data, session):
        return me(session)

    def sesion_salir(environ, data, session):
        token, _ = session_of(environ)
        sessions.pop(token, None)
        return {"ok": True}, [("Set-Cookie", f"{COOKIE}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0")]

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

    def cambiar_pin(environ, data, session):
        auth.change_pin(store, session["principal"], data.get("actual", ""), data.get("nuevo", ""), clock())
        return {"ok": True}

    def reclamos(environ, data, session):
        delivered = {oid for d in store.deliveries.values() for oid in d.order_ids}
        options = []
        for order in store.orders.values():
            if order.customer_id == session["principal"] and order.order_id in delivered:
                names = names_for(order.cycle)
                for line in order.lines:
                    options.append({"pedido": order.order_id, "producto": line.product_id,
                                    "nombre": names.get(line.product_id, line.product_id), "cantidad": qty(line.quantity)})
        mine = [c for c in store.claims.values() if c.customer_id == session["principal"]]
        return {"reclamables": options, "reclamos": [claim_json(c) for c in mine]}

    def claim_json(c) -> dict:
        return {"id": c.claim_id, "pedido": c.order_id, "cliente": c.customer_id, "producto": c.product_id,
                "cantidad": qty(c.quantity), "motivo": c.reason, "foto": c.photo, "estado": c.status,
                "devuelto": money(c.refund_amount)}

    def reclamar(environ, data, session):
        claim = claims.file_claim(store, _int(data.get("pedido"), "Número de pedido"), customer_id=session["principal"],
                                  product_id=str(data.get("producto", "")), quantity=str(data.get("cantidad", "")).strip(),
                                  reason=data.get("motivo", ""), photo=data.get("foto", ""), now=clock())
        return claim_json(claim), [], "201 Created"

    # --- zona (API-05) ---

    def zone_admin_panel(zone) -> dict:
        """AZ-08: lo que ve el admin de su zona (S-165: nombres y si pidió, sin montos ni ubicaciones)."""
        current = cycle.cycle_id(clock())
        in_cycle = [o for o in store.orders_in_cycle(current) if o.status != "CANCELADO_POR_CLIENTE"]
        group = {z.zone_id for z in store.zones.values() if z.group_id == zone.group_id}
        verified = sum(1 for o in in_cycle if o.zone_id in group and o.payment_status == "VERIFICADO")
        ordered = {o.customer_id for o in in_cycle}
        nearby = []
        if zone.lat is not None and zone.lon is not None:
            for other in store.zones.values():
                if other.zone_id == zone.zone_id or other.lat is None or other.lon is None:
                    continue
                meters = zones.distance_m(zone.lat, zone.lon, other.lat, other.lon)
                if meters <= zones.MERGE_DISTANCE_M:
                    nearby.append(zone_json(other) | {"distancia_m": round(meters),
                                                      "mismo_grupo": other.group_id == zone.group_id})
        discount = _in_discount_weeks(zone.created_cycle, current)
        last_week = cycle.add_weeks(zone.created_cycle, ZONE_ADMIN_DISCOUNT_WEEKS - 1) if zone.created_cycle else None
        requests = [{"id": mid, "zona": zid, "nombre": store.zones[zid].name if zid in store.zones else zid}
                    for mid, (zid, target) in store.merge_requests.items() if target == zone.zone_id]
        admin = store.customers[zone.admin_id]
        return zone_json(zone) | {
            "avance": {"verificados": verified, "minimo": MIN_ORDERS_PER_GROUP, "ciclo": current},
            "vecinos": [{"id": c.customer_id, "nombre": c.name, "pidio": c.customer_id in ordered}
                        for c in sorted(store.customers.values(), key=lambda c: c.customer_id)
                        if c.zone_id == zone.zone_id],
            "cercanas": sorted(nearby, key=lambda z: z["distancia_m"]),
            "solicitudes": requests,
            "beneficios": {"envio_gratis": True, "descuento_pct": money(ZONE_ADMIN_DISCOUNT * 100),
                           "descuento_activo": discount, "descuento_hasta": last_week if discount else None},
            "codigo_referido": customers.referral_code(admin),
        }

    def mi_zona(environ, data, session):
        customer = store.customers[session["principal"]]
        zone = store.zones.get(customer.zone_id)
        administered = next((z for z in store.zones.values() if z.admin_id == session["principal"]), None)
        return {"zona": zone_json(zone) if zone else None,
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
        return {"solicitud": merge_id}

    def zona_separar(environ, data, session, zone_id):
        return zone_json(zones.leave_group(store, zone_id, session["principal"], now=clock()))

    def zona_transferir(environ, data, session, zone_id):
        return zone_json(zones.transfer_admin(store, zone_id, session["principal"], _int(data.get("nuevo"), "Vecino")))

    def solicitud_aceptar(environ, data, session, merge_id):
        return zone_json(zones.accept_merge(store, _int(merge_id, "Solicitud"), session["principal"], now=clock()))

    def solicitud_rechazar(environ, data, session, merge_id):
        zones.reject_merge(store, _int(merge_id, "Solicitud"), session["principal"])
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
        if not re.fullmatch(r"\d{4}-W\d{2}", value):
            raise BusinessRuleError("INVALID_INPUT", "Ciclo no válido; usa el formato 2026-W38.")
        return value

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
        return order_json(order, names_for(order.cycle), clock())

    def admin_liquidar(environ, data, session, cycle_id):
        result = fulfillment.close_cycle(store, cycle_id, at=clock())
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
                          "fallida": bool(failed)})
        return {"ciclo": cycle_id, "ciclos": known_cycles(), "paradas": stops,
                "pedidos": [order_json(o, names, clock()) | {
                    "vecino": store.customers[o.customer_id].name,
                    "bolsas": [{"numero": b.number, "foto": b.photo} for b in store.bags.get(o.order_id, [])]}
                    for o in attended]}

    def admin_bolsa(environ, data, session):
        bag = fulfillment.pack_bag(store, _int(data.get("pedido"), "Número de pedido"), by=session["principal"],
                                   photo=data.get("foto", ""), now=clock())
        return {"pedido": bag.order_id, "numero": bag.number, "foto": bag.photo}

    def admin_entrega(environ, data, session):
        delivery = fulfillment.deliver_zone(store, str(data.get("ciclo", "")).strip(), str(data.get("zona", "")),
                                            by=session["principal"], photo=data.get("foto", ""),
                                            received_by=data.get("recibe", ""), now=clock())
        return {"zona": delivery.zone_id, "pedidos": len(delivery.order_ids), "recibe": delivery.received_by}

    def admin_entrega_fallida(environ, data, session):
        failure = fulfillment.register_failed_delivery(store, str(data.get("ciclo", "")).strip(), str(data.get("zona", "")),
                                                       by=session["principal"], photo=data.get("foto", ""),
                                                       reason=data.get("motivo", ""), now=clock())
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
        return claim_json(claim)

    def admin_devoluciones(environ, data, session):
        return {"devoluciones": [{"id": r.refund_id, "cliente": r.customer_id,
                                  "vecino": store.customers[r.customer_id].name, "monto": money(r.amount),
                                  "motivo": r.reason, "estado": r.status,
                                  "vence": r.due_date.date().isoformat() if r.due_date else None}
                                 for r in store.refunds.values() if r.status == "PENDIENTE"]}

    def admin_devolucion_pagar(environ, data, session, refund_id):
        refund = wallet.mark_refund_paid(store, _int(refund_id, "Devolución"), str(data.get("codigo", "")))
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
        return {"ciclo": cycle_id, "ciclos": known_cycles(),
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
                                                    referral=str(data.get("referido", "")))
        return {"id": customer.customer_id, "nombre": customer.name, "pin": pin}, [], "201 Created"

    def admin_vecino_pin(environ, data, session, customer_id):
        pin = customers.reset_pin(store, _int(customer_id, "Vecino"), by=session["principal"])
        return {"id": int(customer_id), "pin": pin}

    def admin_colchon(environ, data, session):
        return {"valor": money(buffer.buffer_value(store)), "tope": money(buffer.BUFFER_LIMIT),
                "stock": [{"producto": s.product_id, "cantidad": qty(s.quantity), "valor": money(s.value)}
                          for s in store.buffer.values()]}

    # ruta (expresión) -> método -> (función, rol requerido)
    routes = [
        (r"/api/estado", {"GET": (estado, None)}),
        (r"/api/catalogo", {"GET": (catalogo, None)}),
        (r"/api/zonas", {"GET": (zonas, None), "POST": (zona_crear, "vecino")}),
        (r"/api/sesion", {"POST": (sesion_entrar, None), "GET": (sesion_ver, "any"), "DELETE": (sesion_salir, "any")}),
        (r"/api/cotizar", {"POST": (cotizar, "vecino")}),
        (r"/api/pedidos", {"POST": (pedidos, "vecino")}),
        (r"/api/mis-pedidos", {"GET": (mis_pedidos, "vecino")}),
        (r"/api/pedidos/(\d+)/cancelar", {"POST": (cancelar, "vecino")}),
        (r"/api/saldo/devolucion", {"POST": (devolucion, "vecino")}),
        (r"/api/pin", {"POST": (cambiar_pin, "vecino")}),
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
        (r"/api/admin/resumen", {"GET": (admin_resumen, "admin")}),
        (r"/api/admin/pedidos/(\d+)/verificar", {"POST": (admin_verificar, "admin")}),
        (r"/api/admin/ciclos/(\d{4}-W\d{2})/liquidar", {"POST": (admin_liquidar, "admin")}),
        (r"/api/admin/armado", {"GET": (admin_armado, "admin")}),
        (r"/api/admin/bolsas", {"POST": (admin_bolsa, "admin")}),
        (r"/api/admin/entregas", {"POST": (admin_entrega, "admin")}),
        (r"/api/admin/entregas-fallidas", {"POST": (admin_entrega_fallida, "admin")}),
        (r"/api/admin/reclamos", {"GET": (admin_reclamos, "admin")}),
        (r"/api/admin/reclamos/(\d+)/revisar", {"POST": (admin_revisar, "admin")}),
        (r"/api/admin/devoluciones", {"GET": (admin_devoluciones, "admin")}),
        (r"/api/admin/devoluciones/(\d+)/pagar", {"POST": (admin_devolucion_pagar, "admin")}),
        (r"/api/admin/conciliacion", {"GET": (admin_conciliacion, "admin")}),
        (r"/api/admin/metricas", {"GET": (admin_metricas, "admin")}),
        (r"/api/admin/catalogo", {"GET": (admin_catalogo, "admin"), "POST": (admin_catalogo_publicar, "admin")}),
        (r"/api/admin/catalogo/desactivar", {"POST": (admin_catalogo_desactivar, "admin")}),
        (r"/api/admin/referencias", {"GET": (admin_referencias, "admin"), "POST": (admin_referencia_registrar, "admin")}),
        (r"/api/admin/vecinos", {"GET": (admin_vecinos, "admin"), "POST": (admin_vecino_alta, "admin")}),
        (r"/api/admin/vecinos/(\d+)/pin", {"POST": (admin_vecino_pin, "admin")}),
        (r"/api/admin/colchon", {"GET": (admin_colchon, "admin")}),
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
        if role in ("vecino", "admin") and session["kind"] != role:
            raise ApiError("403 Forbidden", "FORBIDDEN", "Esta acción no es para tu tipo de cuenta.")
        if method in ("POST", "DELETE") and session is not None and handler is not sesion_entrar:  # S-155
            if not hmac.compare_digest(environ.get("HTTP_X_YAPA_CSRF", ""), session["csrf"]):
                raise ApiError("403 Forbidden", "CSRF", "La sesión venció. Recarga la página.")
        data, files = _body(environ) if method in ("POST", "DELETE") else ({}, {})
        if files.get("foto_archivo") and files["foto_archivo"][1]:  # S-151
            data["foto"] = _save_photo(photo_dir, files["foto_archivo"])
        result = handler(environ, data, session, *match.groups())
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
        if on_change and environ.get("REQUEST_METHOD") in ("POST", "DELETE") and status[:1] == "2":
            on_change(store)
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        start_response(status, [("Content-Type", "application/json; charset=utf-8"),
                                ("Content-Length", str(len(raw))), ("Cache-Control", "no-store")] + headers)
        return [raw]

    return app
