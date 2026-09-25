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
            f'<p><strong>Saldo: {money(balance)}</strong></p></div>'
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
    body = (f'<div class="card"><strong>Pagos por verificar · ciclo {escape(cycle_label)}</strong>'
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


def simple(title: str, message: str, csrf: str | None = None) -> str:
    return page(title, f'<div class="card">{escape(message)}</div>', csrf)
