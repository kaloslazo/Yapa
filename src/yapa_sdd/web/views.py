"""HTML de la interfaz web (WB-07: todo texto se escapa; WB-09: una columna, apto para celular)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from html import escape


CSS = """
body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;background:#f6f8f7;color:#1f2a24}
main{max-width:720px;margin:0 auto;padding:16px}
header{background:#1f3d2b;color:#fff;padding:12px 16px}
header a{color:#cfe3d6;margin-right:14px;text-decoration:none}
h1{font-size:1.4rem;margin:.4rem 0}
.card{background:#fff;border-radius:10px;padding:12px 14px;margin:10px 0;box-shadow:0 1px 2px #0001}
.muted{color:#5f6f66;font-size:.9rem}
.ok{border-left:0;background:#e6f1ea}
.error{background:#fbeadb}
table{width:100%;border-collapse:collapse;font-size:.92rem}
td,th{padding:6px 4px;border-bottom:1px solid #e3e8e5;text-align:left}
input,select,button{font-size:1rem;padding:8px;margin:4px 0;width:100%;box-sizing:border-box}
button{background:#2e7d4f;color:#fff;border:0;border-radius:8px}
*{box-sizing:border-box}
.row{display:flex;justify-content:space-between;align-items:center;gap:8px}
.row>div{flex:1;min-width:0;overflow-wrap:anywhere}
.qty{width:80px;flex:0 0 80px}
.card{overflow-x:auto}
"""


def money(value) -> str:
    return f"S/ {Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"


def qty(value: Decimal) -> str:
    return f"{Decimal(value).normalize():f}"


def hidden(csrf: str | None) -> str:
    """S-71: todo formulario que cambia datos lleva el token de la sesión."""
    return f'<input type="hidden" name="csrf" value="{escape(csrf)}">' if csrf else ""


def page(title: str, body: str, csrf: str | None = None) -> str:
    if csrf:
        session_link = ('<form method="post" action="/salir" style="display:inline">' + hidden(csrf)
                        + '<button style="width:auto;padding:4px 10px;margin:0">Salir</button></form>')
    else:
        session_link = '<a href="/entrar">Entrar</a>'
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(title)} · Yapa</title><style>{CSS}</style></head><body>"
        '<header><strong>Yapa</strong> &nbsp; <a href="/">Catálogo</a><a href="/cuenta">Mi cuenta</a>'
        f'<a href="/admin">Admin</a>{session_link}</header>'
        f"<main><h1>{escape(title)}</h1>{body}</main></body></html>"
    )


def error_box(code: str, message: str) -> str:
    return (f'<div class="card error" data-code="{escape(code)}"><strong>{escape(message)}</strong>'
            f'<div class="muted">Código: {escape(code)}</div></div>')


def home(cycle_label: str, is_open: bool, rows: list[dict], csrf: str | None = None) -> str:
    estado = "abierto hasta el miércoles 20:00" if is_open else "cerrado"
    items = []
    for row in rows:
        items.append(
            '<div class="card"><div class="row"><div>'
            f'<strong>{escape(row["name"])}</strong><div class="muted">por {escape(row["unit"])} · '
            f'hoy pagas máximo {money(row["max_price"])}</div>'
            f'<div class="muted">{escape(row["progress"])}</div></div>'
            + (f'<input class="qty" type="number" min="0" step="{qty(row["step"])}" '
               f'name="cant_{escape(row["product_id"])}" placeholder="0">' if csrf else "")
            + '</div></div>'
        )
    if not csrf:
        entrar = '<p><a href="/entrar"><button>Entrar para pedir</button></a></p>'
        return page("Catálogo de la semana", entrar + "".join(items))
    form = (
        '<form method="post" action="/cotizar">' + hidden(csrf)
        + "".join(items)
        + '<div class="card"><label>Medio <select name="metodo"><option>YAPE</option><option>PLIN</option>'
          '</select></label><label>Código de operación <input name="codigo"></label>'
          '<label>Monto yapeado <input name="monto" placeholder="0.00"></label>'
          '<label>Saldo a usar <input name="saldo" placeholder="0.00"></label>'
          '<button>Cotizar</button> <button formaction="/pedidos">Pagar y registrar</button></div></form>'
    )
    intro = (f'<p class="muted">Ciclo {escape(cycle_label)}: {estado}. Pagas el precio máximo; lo que ahorremos '
             'entre todos te lo devolvemos como saldo después de la entrega.</p>')
    return page("Catálogo de la semana", intro + form, csrf)


def order_lines(lines) -> str:
    rows = "".join(
        f"<tr><td>{escape(line.product_id)}</td><td>{qty(line.quantity)}</td>"
        f"<td>{money(line.max_unit_price)}</td><td>{money(line.max_total)}</td></tr>"
        for line in lines
    )
    return f"<table><tr><th>Producto</th><th>Cant.</th><th>Precio máx.</th><th>Total</th></tr>{rows}</table>"


def quote(result, csrf: str | None = None) -> str:
    body = (f'<div class="card">{order_lines(result.lines)}<p>Envío máximo: {money(result.delivery_fee)}</p>'
            f'<p><strong>Total a yapear: {money(result.total)}</strong></p></div>')
    return page("Cotización", body, csrf)


def registered(order, csrf: str | None = None) -> str:
    body = (f'<div class="card ok"><strong>Pedido {order.order_id} · {escape(order.status)}</strong>'
            f'<p>Total: {money(order.total)} · pago {escape(order.payment_status)}</p>'
            f'{order_lines(order.lines)}</div>')
    return page("Pedido registrado", body, csrf)


def account(customer, balance, orders, refunds, csrf: str | None = None) -> str:
    rows = "".join(
        f"<tr><td>Pedido {o.order_id}</td><td>{escape(o.cycle)}</td><td>{escape(o.status)}</td>"
        f"<td>{money(o.total)}</td></tr>" for o in orders
    )
    pending = "".join(f"<li>{money(r.amount)} · {escape(r.reason)} · {escape(r.status)}</li>" for r in refunds)
    body = (f'<div class="card"><strong>{escape(customer.name)}</strong> · zona {escape(customer.zone_id)}'
            f'<p><strong>Saldo: {money(balance)}</strong></p>'
            '<p><a href="/zona">Mi zona</a> · <a href="/reclamos">Reclamos</a></p></div>'
            '<form class="card" method="post" action="/cuenta/devolucion">' + hidden(csrf) +
            '<label>Devolverme de mi saldo a mi Yape/Plin (S/) <input name="monto" inputmode="decimal" '
            'placeholder="0.00"></label><button>Pedir devolución</button></form>'
            f'<div class="card"><table><tr><th>Pedido</th><th>Ciclo</th><th>Estado</th><th>Total</th></tr>{rows}'
            f'</table></div><div class="card"><strong>Devoluciones pendientes</strong><ul>{pending}</ul></div>'
            '<form class="card" method="post" action="/cuenta/cancelar">' + hidden(csrf) +
            '<label>Pedido a cancelar <input name="pedido"></label>'
            '<label>Devolver a <select name="destino"><option value="MEDIO_DE_PAGO">Mi Yape/Plin</option>'
            '<option value="SALDO">Mi saldo</option></select></label><button>Cancelar pedido</button></form>'
            '<form class="card" method="post" action="/cuenta/pin">' + hidden(csrf) +
            '<label>PIN actual <input name="actual" type="password" inputmode="numeric"></label>'
            '<label>PIN nuevo (6 dígitos) <input name="nuevo" type="password" inputmode="numeric"></label>'
            '<button>Cambiar PIN</button></form>')
    return page("Mi cuenta", body, csrf)


def login(error: str = "") -> str:
    body = (error + '<form class="card" method="post" action="/entrar">'
            '<label>Soy <select name="tipo"><option value="vecino">Vecino</option>'
            '<option value="admin">Administrador</option></select></label>'
            '<label>Número de cliente o usuario <input name="usuario" autocomplete="username"></label>'
            '<label>PIN o contraseña <input name="secreto" type="password" autocomplete="current-password"></label>'
            '<button>Entrar</button></form>')
    return page("Entrar", body)


def admin(cycle_label: str, pending, csrf: str | None = None) -> str:
    rows = "".join(
        f"<tr><td>{o.order_id}</td><td>{o.customer_id}</td><td>{money(o.total)}</td>"
        f"<td>{escape(o.payment_method)} {escape(o.operation_code)}</td><td>"
        f'<form method="post" action="/admin/verificar">{hidden(csrf)}<input type="hidden" name="pedido" value="{o.order_id}">'
        "<button>Verificar</button></form></td></tr>" for o in pending
    )
    body = ('<div class="card"><a href="/admin/armado">Armado y entrega</a> · <a href="/admin/reclamos">Reclamos</a>'
            ' · <a href="/admin/colchon">Colchón</a> · <a href="/admin/metricas">Métricas</a>'
            ' · <a href="/admin/devoluciones">Devoluciones</a></div>'
            f'<div class="card"><strong>Pagos por verificar · ciclo {escape(cycle_label)}</strong>'
            f'<table><tr><th>Pedido</th><th>Cliente</th><th>Total</th><th>Pago</th><th></th></tr>{rows}</table></div>'
            '<form class="card" method="post" action="/admin/liquidar">' + hidden(csrf) +
            f'<label>Ciclo a liquidar <input name="ciclo" value="{escape(cycle_label)}"></label>'
            '<button>Liquidar ciclo</button></form>')
    return page("Administración", body, csrf)


def settlement(result, csrf: str | None = None) -> str:
    products = "".join(
        f"<tr><td>{escape(p.product_id)}</td><td>{qty(p.total_quantity)}</td><td>desde {qty(p.tier_min_quantity)}</td>"
        f"<td>{money(p.final_unit_price)}</td></tr>" for p in result.products.values()
    )
    orders = "".join(
        f"<tr><td>{o.order_id}</td><td>{escape(o.status)}</td><td>{money(o.paid)}</td><td>{money(o.final_amount)}</td>"
        f"<td>{money(o.refund_amount)} {escape(o.refund_destination or '')}</td></tr>" for o in result.orders.values()
    )
    body = (f'<div class="card"><table><tr><th>Producto</th><th>Total</th><th>Tramo</th><th>Precio final</th></tr>'
            f'{products}</table></div><div class="card"><table><tr><th>Pedido</th><th>Estado</th><th>Pagado</th>'
            f'<th>Final</th><th>Devuelto</th></tr>{orders}</table>'
            f'<p>Devuelto como saldo: {money(result.total_credited)} · '
            f'reembolsado: {money(result.total_refunded)}</p></div>')
    return page(f"Liquidación {result.cycle}", body, csrf)


def simple(title: str, message: str, csrf: str | None = None, back: str | None = None) -> str:
    link = f'<p><a href="{escape(back)}">Volver</a></p>' if back else ""
    return page(title, f'<div class="card">{escape(message)}{link}</div>', csrf)


# --- iteración 12: zonas, reclamos, armado, entrega, colchón y métricas ---

ZONE_STATUS = {"ACTIVA": "Activa", "PENDIENTE_RECEPCION": "Falta quien reciba"}
RECEPTION = [("PORTERIA", "Portería"), ("ENCARGADO", "Encargado"), ("ADMIN", "Yo, el admin de la zona")]
REASONS = {"FALTANTE": "Faltó", "DANADO": "Llegó dañado"}


def photo(reference: str) -> str:
    """S-72: la foto es una referencia de texto; se muestra como texto, nunca como enlace ni imagen."""
    return f'<span class="muted">foto: {escape(reference)}</span>'


def _zone_admin_forms(zone, requests, csrf) -> str:
    zone_field = f'<input type="hidden" name="zona" value="{escape(zone.zone_id)}">'
    kinds = "".join(f'<option value="{value}">{label}</option>' for value, label in RECEPTION)
    received = "".join(
        f'<form method="post" action="/zona/aceptar">{hidden(csrf)}'
        f'<input type="hidden" name="solicitud" value="{merge_id}">'
        f'La zona {escape(zone_id)} quiere unirse a la tuya <button>Aceptar</button></form>'
        for merge_id, zone_id in requests
    )
    return (
        f'<div class="card"><strong>Administras {escape(zone.name)} ({escape(zone.zone_id)})</strong></div>'
        f'<form class="card" method="post" action="/zona/activar">{hidden(csrf)}{zone_field}'
        f'<label>Quién recibe <select name="tipo">{kinds}</select></label>'
        '<label>Nombre de quien recibe <input name="contacto"></label><button>Activar zona</button></form>'
        f'<form class="card" method="post" action="/zona/unir">{hidden(csrf)}{zone_field}'
        '<label>Unirme con la zona (código) <input name="destino"></label><button>Pedir unión</button></form>'
        f'<div class="card"><strong>Solicitudes de unión</strong>{received or "<p class=muted>No hay.</p>"}</div>'
        f'<form class="card" method="post" action="/zona/separar">{hidden(csrf)}{zone_field}'
        '<button>Separar mi zona del grupo</button></form>'
        f'<form class="card" method="post" action="/zona/transferir">{hidden(csrf)}{zone_field}'
        '<label>Número de cliente del nuevo admin <input name="nuevo" inputmode="numeric"></label>'
        '<button>Transferir el rol</button></form>'
    )


def zone_page(customer, my_zone, zones, admin_zone, requests, districts, csrf: str | None = None) -> str:
    if my_zone:
        mine = (f'<div class="card"><strong>{escape(my_zone.name)}</strong> · {escape(my_zone.district)}'
                f'<p>{escape(ZONE_STATUS.get(my_zone.status, my_zone.status))} · grupo {escape(my_zone.group_id)}</p>'
                '</div>')
    else:
        mine = '<div class="card">Todavía no tienes zona.</div>'
    rows = "".join(
        f"<tr><td>{escape(z.zone_id)}</td><td>{escape(z.name)}</td><td>{escape(z.district)}</td>"
        f"<td>{escape(ZONE_STATUS.get(z.status, z.status))}</td></tr>" for z in zones
    )
    options = "".join(f"<option>{escape(d)}</option>" for d in districts)
    body = (
        mine + (_zone_admin_forms(admin_zone, requests, csrf) if admin_zone else "")
        + f'<div class="card"><strong>Zonas</strong><table><tr><th>Código</th><th>Nombre</th><th>Distrito</th>'
          f'<th>Estado</th></tr>{rows}</table></div>'
        + f'<form class="card" method="post" action="/zona/unirse">{hidden(csrf)}'
          '<label>Unirme a la zona (código) <input name="zona"></label><button>Unirme</button></form>'
        + f'<form class="card" method="post" action="/zona/crear">{hidden(csrf)}'
          '<label>Nombre del edificio o barrio <input name="nombre"></label>'
          f'<label>Distrito <select name="distrito">{options}</select></label>'
          '<label>Latitud del punto de recepción <input name="lat" inputmode="decimal" placeholder="-12.0850"></label>'
          '<label>Longitud <input name="lon" inputmode="decimal" placeholder="-77.0350"></label>'
          '<button>Crear zona</button></form>'
    )
    return page("Mi zona", body, csrf)


def claims_page(options, claims, csrf: str | None = None) -> str:
    rows = "".join(
        f"<tr><td>{c.claim_id}</td><td>Pedido {c.order_id} · {escape(c.product_id)}</td><td>{qty(c.quantity)}</td>"
        f"<td>{escape(REASONS.get(c.reason, c.reason))}</td><td>{escape(c.status)}</td>"
        f"<td>{money(c.refund_amount)}</td></tr>" for c in claims
    )
    items = "".join(f'<option value="{escape(value)}">{escape(label)}</option>' for value, label in options)
    reasons = "".join(f'<option value="{value}">{label}</option>' for value, label in REASONS.items())
    form = (f'<form class="card" method="post" action="/reclamos">{hidden(csrf)}'
            f'<label>Artículo <select name="articulo">{items}</select></label>'
            '<label>Cantidad <input name="cantidad" inputmode="decimal"></label>'
            f'<label>Motivo <select name="motivo">{reasons}</select></label>'
            '<label>Foto (ruta o enlace del archivo) <input name="foto"></label>'
            '<button>Enviar reclamo</button></form>') if options else (
            '<div class="card muted">Todavía no tienes pedidos entregados para reclamar.</div>')
    body = (form + '<div class="card"><strong>Mis reclamos</strong><table><tr><th>#</th><th>Artículo</th>'
            f'<th>Cant.</th><th>Motivo</th><th>Estado</th><th>Devuelto</th></tr>{rows}</table></div>')
    return page("Reclamos", body, csrf)


def packing(cycle_label: str, orders, bags, stops, csrf: str | None = None) -> str:
    cards = []
    for order in orders:
        listed = "".join(f"<li>Bolsa {b.number} · {photo(b.photo)}</li>" for b in bags.get(order.order_id, []))
        cards.append(
            f'<div class="card"><strong>Pedido {order.order_id}</strong> · cliente {order.customer_id} · '
            f'zona {escape(order.zone_id)}<ul>{listed}</ul>'
            f'<form method="post" action="/admin/bolsa">{hidden(csrf)}'
            f'<input type="hidden" name="pedido" value="{order.order_id}">'
            '<label>Foto de la bolsa <input name="foto"></label><button>Registrar bolsa</button></form></div>'
        )
    deliveries = []
    for zone, delivery in stops:
        if delivery:
            state = (f"Entregada a {escape(delivery.received_by)} · {len(delivery.order_ids)} pedidos · "
                     f"{photo(delivery.photo)}")
            form = ""
        else:
            state = "Sin entregar"
            form = (f'<form method="post" action="/admin/entrega">{hidden(csrf)}'
                    f'<input type="hidden" name="ciclo" value="{escape(cycle_label)}">'
                    f'<input type="hidden" name="zona" value="{escape(zone.zone_id)}">'
                    '<label>Foto de la entrega <input name="foto"></label>'
                    '<label>Nombre de quien recibe <input name="recibe"></label><button>Registrar entrega</button>'
                    '</form>'
                    f'<form method="post" action="/admin/entrega-fallida">{hidden(csrf)}'
                    f'<input type="hidden" name="ciclo" value="{escape(cycle_label)}">'
                    f'<input type="hidden" name="zona" value="{escape(zone.zone_id)}">'
                    '<label>Si no recibieron: motivo <select name="motivo">'
                    '<option value="PORTERIA_CERRADA">Portería cerrada</option>'
                    '<option value="NADIE_RECIBE">No había quién reciba</option>'
                    '<option value="PORTERIA_RECHAZA">La portería no aceptó</option></select></label>'
                    '<label>Foto de evidencia <input name="foto"></label>'
                    '<button>Registrar entrega fallida</button></form>')
        deliveries.append(f'<div class="card"><strong>{escape(zone.name)} ({escape(zone.zone_id)})</strong>'
                          f'<p>{state}</p>{form}</div>')
    empty = '<div class="card muted">No hay pedidos que se atiendan en este ciclo.</div>'
    body = (f'<p class="muted">Ciclo {escape(cycle_label)}.</p><h2>Entregas por zona</h2>'
            + ("".join(deliveries) or empty) + "<h2>Armado por pedido</h2>" + ("".join(cards) or empty))
    return page("Armado y entrega", body, csrf)


def admin_claims(claims, csrf: str | None = None) -> str:
    pending = []
    reviewed = []
    for c in claims:
        detail = (f"Reclamo {c.claim_id} · pedido {c.order_id} · cliente {c.customer_id} · {escape(c.product_id)} "
                  f"× {qty(c.quantity)} · {escape(REASONS.get(c.reason, c.reason))} · {photo(c.photo)}")
        if c.status == "PENDIENTE":
            pending.append(
                f'<div class="card">{detail}'
                f'<form method="post" action="/admin/reclamos/revisar">{hidden(csrf)}'
                f'<input type="hidden" name="reclamo" value="{c.claim_id}">'
                '<button name="decision" value="aprobar">Aprobar</button>'
                '<button name="decision" value="rechazar">Rechazar</button></form></div>'
            )
        else:
            reviewed.append(f'<div class="card">{detail}<p>{escape(c.status)} · devuelto '
                            f'{money(c.refund_amount)}</p></div>')
    empty = '<div class="card muted">No hay.</div>'
    body = ("<h2>Pendientes</h2>" + ("".join(pending) or empty)
            + "<h2>Revisados</h2>" + ("".join(reviewed) or empty))
    return page("Reclamos", body, csrf)


def buffer_page(stocks, total, limit, products, csrf: str | None = None) -> str:
    rows = "".join(f"<tr><td>{escape(s.product_id)}</td><td>{qty(s.quantity)}</td><td>{money(s.value)}</td></tr>"
                   for s in stocks)
    options = "".join(f'<option value="{escape(p.product_id)}">{escape(p.name)}</option>' for p in products)
    body = (f'<div class="card"><p><strong>Valor guardado: {money(total)} de un tope de {money(limit)}</strong></p>'
            f'<table><tr><th>Producto</th><th>Cantidad</th><th>Valor</th></tr>{rows}</table></div>'
            f'<form class="card" method="post" action="/admin/colchon/agregar">{hidden(csrf)}'
            f'<label>Producto <select name="producto">{options}</select></label>'
            '<label>Cantidad <input name="cantidad" inputmode="decimal"></label><button>Guardar en el colchón</button>'
            '</form>'
            f'<form class="card" method="post" action="/admin/colchon/usar">{hidden(csrf)}'
            f'<label>Producto <select name="producto">{options}</select></label>'
            '<label>Cantidad <input name="cantidad" inputmode="decimal"></label><button>Usar para reponer</button>'
            '</form>')
    return page("Colchón de reposición", body, csrf)


def metrics_page(cycle_label: str, margins, alerts, savings, repurchase, repurchase_error,
                 csrf: str | None = None) -> str:
    rows = "".join(
        f"<tr><td>{m.order_id}</td><td>{money(m.revenue)}</td><td>{money(m.claims)}</td>"
        f"<td>{money(m.product_cost)}</td><td>{money(m.stop_cost)}</td><td>{money(m.margin)}"
        f"{' · negativo' if m.order_id in alerts else ''}</td></tr>"
        for m in sorted(margins.values(), key=lambda m: m.order_id)
    )
    if repurchase:
        rate = repurchase.rate.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        verdict = "cumple la meta del 50 %" if repurchase.meets_target else "no llega a la meta del 50 %"
        returning = (f"<p>De {repurchase.cohort_size} vecinos que compraron por primera vez en "
                     f"{escape(repurchase.cohort_cycle)}, {repurchase.returned} volvieron en "
                     f"{escape(repurchase.target_cycle)}: {rate} %, {verdict}.</p>")
    else:
        returning = error_box(repurchase_error.code, str(repurchase_error))
    body = (f'<form class="card" method="get" action="/admin/metricas"><label>Ciclo '
            f'<input name="ciclo" value="{escape(cycle_label)}"></label><button>Ver</button></form>'
            f'<div class="card"><strong>Margen por pedido</strong> <span class="muted">(antes de costos operativos)'
            '</span><table><tr><th>Pedido</th><th>Cobrado</th><th>Reclamos</th><th>Proveedor</th><th>Parada</th>'
            f'<th>Margen</th></tr>{rows}</table><p>Pedidos con margen negativo: {len(alerts)}</p></div>'
            f'<div class="card"><strong>Ahorro entregado</strong><p>Por volumen: {money(savings.volume)} · '
            f'por envío: {money(savings.delivery)} · total: {money(savings.total)}</p></div>'
            f'<div class="card"><strong>Recompra en la semana 4</strong>{returning}</div>')
    return page(f"Métricas {cycle_label}", body, csrf)


def refunds_page(pending, csrf: str | None = None) -> str:
    """HR-08: devoluciones pendientes y registro de su pago."""
    rows = "".join(
        f"<tr><td>{r.refund_id}</td><td>{r.customer_id}</td><td>{money(r.amount)}</td><td>{escape(r.reason)}</td>"
        f"<td>{escape(r.due_date.date().isoformat() if r.due_date else '-')}</td><td>"
        f'<form method="post" action="/admin/devoluciones/pagar">{hidden(csrf)}'
        f'<input type="hidden" name="reembolso" value="{r.refund_id}">'
        '<input name="codigo" placeholder="Código de operación"><button>Marcar pagado</button></form></td></tr>'
        for r in pending
    )
    body = ('<div class="card"><table><tr><th>N.º</th><th>Cliente</th><th>Monto</th><th>Motivo</th><th>Vence</th>'
            f'<th></th></tr>{rows}</table></div>')
    return page("Devoluciones pendientes", body, csrf)
