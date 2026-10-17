"""HTML de la interfaz web (WB-07: todo texto se escapa; WB-09: una columna, apto para celular)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from html import escape

from ..reference import savings_percent


CSS = """
:root{--verde:#1e6b45;--verde-osc:#14482f;--verde-claro:#e5f3ea;--hoja:#3fa66b;--sol:#f4b63f;--sol-claro:#fff4dc;
--tinta:#1d2a22;--suave:#5c6b62;--linea:#e2e8e3;--fondo:#f6f7f2;--rojo:#b3401f;--rojo-claro:#fcebe4}
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;margin:0;background:var(--fondo);
color:var(--tinta);line-height:1.45}
a{color:var(--verde)}
header{background:#fff;border-bottom:1px solid var(--linea);position:sticky;top:0;z-index:5}
.bar{max-width:760px;margin:0 auto;padding:10px 16px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:8px;text-decoration:none;color:var(--verde-osc);font-weight:800;
font-size:1.25rem;margin-right:auto}
.logo{width:34px;height:34px}
nav{display:flex;gap:4px;flex-wrap:wrap;align-items:center}
nav a{text-decoration:none;color:var(--suave);padding:6px 12px;border-radius:999px;font-weight:600;font-size:.95rem}
nav a:hover{background:var(--verde-claro);color:var(--verde-osc)}
nav a[aria-current=page]{background:var(--verde);color:#fff}
nav form{display:inline;margin:0}
nav button{width:auto;margin:0;padding:6px 12px;font-size:.95rem;background:transparent;color:var(--suave);
border:1px solid var(--linea)}
main{max-width:760px;margin:0 auto;padding:18px 16px 40px}
h1{font-size:1.6rem;margin:.3rem 0 .8rem;color:var(--verde-osc)}
h2{font-size:1.15rem;margin:1.4rem 0 .4rem;color:var(--verde-osc)}
.card{background:#fff;border-radius:14px;padding:14px 16px;margin:12px 0;box-shadow:0 1px 3px #1d2a2214;
border:1px solid var(--linea);overflow-x:auto}
.muted{color:var(--suave);font-size:.9rem}
.ok{background:var(--verde-claro);border-color:#bfe0cb}
.error{background:var(--rojo-claro);border-color:#f2c6b5;border-left:5px solid var(--rojo)}
table{width:100%;border-collapse:collapse;font-size:.92rem}
td,th{padding:8px 6px;border-bottom:1px solid var(--linea);text-align:left;vertical-align:top}
th{color:var(--suave);font-weight:600;font-size:.82rem;text-transform:uppercase;letter-spacing:.03em}
tr:last-child td{border-bottom:0}
td{white-space:nowrap}
td[colspan]{white-space:normal}
td button,td input{width:auto;margin:2px 0}
td button{padding:8px 14px}
label{display:block;font-weight:600;font-size:.92rem;margin-top:6px}
input,select,textarea,button{font:inherit;font-size:1rem;padding:10px;margin:4px 0;width:100%;
border:1px solid #cdd6cf;border-radius:10px;background:#fff;color:var(--tinta)}
input:focus,select:focus,textarea:focus{border-color:var(--hoja);outline:3px solid #3fa66b33}
button,.btn{background:var(--verde);color:#fff;border:0;border-radius:10px;font-weight:700;cursor:pointer;
display:inline-block;text-align:center;text-decoration:none;padding:11px 16px}
button:hover,.btn:hover{background:var(--verde-osc)}
button.secundario{background:#fff;color:var(--verde);border:2px solid var(--verde)}
.btn-sol{background:var(--sol);color:var(--tinta)}
.btn-sol:hover{background:#e5a52c}
:focus-visible{outline:3px solid var(--sol);outline-offset:2px}
.hero{background:linear-gradient(135deg,var(--verde-osc),var(--verde) 60%,var(--hoja));color:#fff;
border-radius:18px;padding:24px 20px;margin:4px 0 18px}
.hero h2{color:#fff;font-size:1.5rem;margin:0 0 6px}
.hero p{margin:6px 0 14px;color:#e3f2e8}
.promesa{display:inline-block;background:var(--sol);color:var(--tinta);font-weight:800;border-radius:999px;
padding:6px 14px;margin-bottom:12px}
.pasos{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:8px 0 6px}
.paso{background:#fff;border:1px solid var(--linea);border-radius:14px;padding:12px 14px}
.paso b{display:inline-flex;width:28px;height:28px;border-radius:50%;background:var(--sol-claro);
color:var(--verde-osc);align-items:center;justify-content:center;margin-right:6px}
.ciclo{display:flex;align-items:center;gap:8px;background:var(--sol-claro);border:1px solid #f3dca7;
border-radius:12px;padding:10px 14px;margin:6px 0 4px;font-size:.95rem}
.producto{display:flex;gap:12px;align-items:flex-start}
.icono{font-size:1.9rem;line-height:1;width:44px;height:44px;flex:0 0 44px;display:flex;align-items:center;
justify-content:center;background:var(--verde-claro);border-radius:12px}
.producto .info{flex:1;min-width:0;overflow-wrap:anywhere}
.nombre{font-weight:700;font-size:1.05rem}
.precio{font-size:1.25rem;font-weight:800;color:var(--verde-osc)}
.precio small{font-size:.8rem;font-weight:600;color:var(--suave)}
.ahorro{display:inline-block;background:var(--sol-claro);color:#7a4f00;border:1px solid #f3dca7;border-radius:999px;
padding:2px 10px;font-size:.82rem;font-weight:700;margin:4px 0}
progress{width:100%;height:10px;margin:6px 0 2px;appearance:none;-webkit-appearance:none;border:0;
border-radius:999px;background:var(--linea);overflow:hidden}
progress::-webkit-progress-bar{background:var(--linea);border-radius:999px}
progress::-webkit-progress-value{background:linear-gradient(90deg,var(--hoja),var(--verde));border-radius:999px}
progress::-moz-progress-bar{background:var(--hoja);border-radius:999px}
.qty{width:84px;flex:0 0 84px;text-align:center;font-weight:700}
.pago{border:2px solid var(--verde-claro)}
.acciones{display:flex;gap:8px;flex-wrap:wrap}
.acciones button{flex:1 1 160px}
.hero-balance{background:linear-gradient(135deg,var(--verde-osc),var(--verde));color:#fff;border-radius:18px;
padding:20px;margin:4px 0 14px}
.hero-balance .grande{font-size:2rem;font-weight:800;margin:4px 0}
.hero-balance .devuelto{display:inline-block;background:var(--sol);color:var(--tinta);border-radius:999px;
padding:4px 12px;font-weight:700;margin:4px 0}
.hero-balance a{color:#fff;font-weight:600}
.pill{display:inline-block;border-radius:999px;padding:2px 9px;font-size:.78rem;font-weight:700;
background:var(--linea);color:var(--tinta);white-space:nowrap}
.pill-LIQUIDADO,.pill-VERIFICADO,.pill-APROBADO,.pill-PAGADO,.pill-Activa{background:var(--verde-claro);color:var(--verde-osc)}
.pill-REGISTRADO,.pill-POR_VERIFICAR,.pill-PENDIENTE{background:var(--sol-claro);color:#7a4f00}
.pill-CANCELADO_POR_CLIENTE,.pill-NO_ATENDIDO,.pill-NO_ENTREGADO,.pill-RECHAZADO{background:var(--rojo-claro);color:var(--rojo)}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;margin:8px 0 14px}
.tile{display:block;background:#fff;border:1px solid var(--linea);border-radius:14px;padding:14px;text-decoration:none;
color:var(--tinta);box-shadow:0 1px 3px #1d2a2214}
.tile:hover{border-color:var(--hoja);background:var(--verde-claro)}
.tile strong{display:block;color:var(--verde-osc);font-size:1.02rem}
.tile span{display:block;color:var(--suave);font-size:.86rem;margin-top:2px}
.login{max-width:420px;margin:0 auto}
footer{max-width:760px;margin:0 auto;padding:10px 16px 30px;color:var(--suave);font-size:.8rem;text-align:center}
"""


def money(value) -> str:
    return f"S/ {Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"


def percent(value) -> str:
    if value is None:
        return "sin datos"
    return f"{Decimal(value).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)} %"


def qty(value: Decimal) -> str:
    return f"{Decimal(value).normalize():f}"


def hidden(csrf: str | None) -> str:
    """S-71: todo formulario que cambia datos lleva el token de la sesión."""
    return f'<input type="hidden" name="csrf" value="{escape(csrf)}">' if csrf else ""


# S-140: el logo se dibuja aquí mismo (una bolsa de compras con hojas), sin cargar archivos de otro sitio
LOGO = ('<svg class="logo" viewBox="0 0 40 40" aria-hidden="true">'
        '<path d="M19 17c-1-6-6-9-11-8 0 5 4 9 11 8z" fill="#3fa66b"/>'
        '<path d="M21 17c1-7 6-11 12-10 0 6-5 11-12 10z" fill="#1e6b45"/>'
        '<path d="M6 16h28l-3 19a3 3 0 0 1-3 2.5H12A3 3 0 0 1 9 35z" fill="#f4b63f"/>'
        '<path d="M13 22h14" stroke="#14482f" stroke-width="2.2" stroke-linecap="round"/></svg>')

# PW-01: qué enlace corresponde a cada página
NAV = [("/", "Catálogo"), ("/cuenta", "Mi cuenta"), ("/admin", "Admin")]
CURRENT = {"Catálogo de la semana": "/", "Mi cuenta": "/cuenta", "Administración": "/admin"}


def page(title: str, body: str, csrf: str | None = None) -> str:
    if csrf:
        session_link = ('<form method="post" action="/salir">' + hidden(csrf) + '<button>Salir</button></form>')
    else:
        session_link = '<a href="/entrar">Entrar</a>'
    links = "".join(
        f'<a href="{path}" aria-current="page">{label}</a>' if CURRENT.get(title) == path
        else f'<a href="{path}">{label}</a>'
        for path, label in NAV
    )
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(title)} · Yapa</title><style>{CSS}</style></head><body>"
        f'<header><div class="bar"><a class="brand" href="/">{LOGO}Yapa</a>'
        f'<nav>{links}{session_link}</nav></div></header>'
        f"<main><h1>{escape(title)}</h1>{body}</main>"
        "<footer>Yapa · compras de la semana entre vecinos de Lince, Jesús María y La Victoria · "
        "Diseño de Software, UTEC 2026-2</footer></body></html>"
    )


def pill(status: str) -> str:
    return f'<span class="pill pill-{escape(status)}">{escape(status)}</span>'


def error_box(code: str, message: str) -> str:
    return (f'<div class="card error" data-code="{escape(code)}"><strong>{escape(message)}</strong>'
            f'<div class="muted">Código: {escape(code)}</div></div>')


ICONS = {"PAPA": "🥔", "CEBOLLA": "🧅", "AJO": "🧄", "LIMON": "🍋", "CAMOTE": "🍠", "ZANAHORIA": "🥕",
         "PLATANO": "🍌", "NARANJA": "🍊", "ZAPALLO": "🎃"}


def icon(product_id: str, unit: str) -> str:
    for prefix, emoji in ICONS.items():
        if product_id.startswith(prefix):
            return emoji
    return "🧴" if unit == "unidad" else "🧺"


def savings_badge(max_price, references) -> str:
    """PW-04, S-139: solo si la referencia es más cara que el precio máximo (el peor caso de Yapa)."""
    best = None
    for r in references:
        saving = savings_percent(max_price, r.price)
        if saving > 0 and (best is None or saving > best[0]):
            best = (saving, r.source)
    if best is None:
        return ""
    return f'<div class="ahorro">{percent(best[0])} menos que en {escape(best[1])}</div>'


HOW_IT_WORKS = (
    '<div class="hero"><div class="promesa">Nunca pagas más del precio que ves</div>'
    "<h2>Las compras de la semana, juntos y más baratas</h2>"
    "<p>Los vecinos de tu edificio piden juntos, Yapa compra al por mayor y lo que ahorramos vuelve a ti.</p>"
    '<a class="btn btn-sol" href="/entrar">Entrar para pedir</a></div>'
    "<h2>Cómo funciona</h2>"
    '<div class="pasos">'
    '<div class="paso"><b>1</b>Pides hasta el miércoles 20:00 y pagas con Yape o Plin el precio máximo.</div>'
    '<div class="paso"><b>2</b>Compramos juntos al por mayor: mientras más pedimos, más baja el precio.</div>'
    '<div class="paso"><b>3</b>Recibes el sábado en tu edificio y te devolvemos lo ahorrado como saldo.</div>'
    "</div><h2>Lo de esta semana</h2>"
)


def home(cycle_label: str, is_open: bool, rows: list[dict], csrf: str | None = None) -> str:
    estado = "abierto hasta el miércoles 20:00" if is_open else "cerrado"
    items = []
    for row in rows:
        items.append(
            '<div class="card"><div class="producto">'
            f'<div class="icono" aria-hidden="true">{icon(row["product_id"], row["unit"])}</div><div class="info">'
            f'<div class="nombre">{escape(row["name"])}</div>'
            f'<div class="precio">{money(row["max_price"])} <small>por {escape(row["unit"])}</small></div>'
            f'<div class="muted">hoy pagas máximo {money(row["max_price"])}</div>'
            + savings_badge(row["max_price"], row.get("references", ()))
            + f'<progress value="{qty(row["ordered"])}" max="{qty(row["goal"])}" '
              f'aria-label="Avance hacia el siguiente descuento"></progress>'
            f'<div class="muted">{escape(row["progress"])}</div>'
            + "".join(f'<div class="muted">{escape(r.source)}: {money(r.price)} (visto el '
                      f'{r.observed_on.strftime("%d/%m")})</div>' for r in row.get("references", ()))
            + '</div>'
            + (f'<input class="qty" type="number" min="0" step="{qty(row["step"])}" '
               f'name="cant_{escape(row["product_id"])}" placeholder="0" '
               f'aria-label="Cantidad de {escape(row["name"])}">' if csrf else "")
            + '</div></div>'
        )
    ciclo = f'<div class="ciclo">🗓️ <span>Ciclo {escape(cycle_label)}: {estado}.</span></div>'
    if not csrf:
        return page("Catálogo de la semana", HOW_IT_WORKS + ciclo + "".join(items))
    form = (
        '<form method="post" action="/cotizar">' + hidden(csrf)
        + "".join(items)
        + '<div class="card pago"><strong>Paga tu pedido</strong>'
          '<p class="muted">Primero cotiza para saber cuánto yapear. Luego paga y registra con el código de '
          'operación.</p><label>Medio <select name="metodo"><option>YAPE</option><option>PLIN</option>'
          '</select></label><label>Código de operación <input name="codigo"></label>'
          '<label>Monto yapeado <input name="monto" inputmode="decimal" placeholder="0.00"></label>'
          '<label>Saldo a usar <input name="saldo" inputmode="decimal" placeholder="0.00"></label>'
          '<div class="acciones"><button class="secundario">Cotizar</button>'
          '<button formaction="/pedidos">Pagar y registrar</button></div></div></form>'
    )
    intro = (ciclo + '<p class="muted">Pagas el precio máximo; lo que ahorremos entre todos te lo devolvemos '
             'como saldo después de la entrega.</p>')
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
            f'<p class="precio">Total a yapear: {money(result.total)}</p>'
            '<p class="muted">Es lo máximo que pagas. Lo que ahorremos entre todos vuelve a tu saldo.</p>'
            '<a href="/">Volver al catálogo</a></div>')
    return page("Cotización", body, csrf)


def registered(order, csrf: str | None = None) -> str:
    body = (f'<div class="card ok"><strong>Pedido {order.order_id}</strong> {pill(order.status)}'
            f'<p>Total: {money(order.total)} · pago {pill(order.payment_status)}</p>'
            f'{order_lines(order.lines)}<p><a href="/cuenta">Ver mi cuenta</a></p></div>')
    return page("Pedido registrado", body, csrf)


def order_detail(settled, comparison) -> str:
    """S-130, S-131: qué costó el pedido, qué se devolvió y cuánto costaba en otro lado."""
    returned = settled.refund_amount + settled.returned_to_balance
    where = {"SALDO": " a tu saldo", "MEDIO_DE_PAGO": " a tu Yape/Plin"}.get(settled.refund_destination, "")
    if settled.status == "LIQUIDADO":
        text = [f"Pagaste {money(settled.paid)} · costó {money(settled.final_amount)} · "
                f"te devolvimos {money(settled.refund_amount)}{where}"]
    elif settled.status == "NO_ATENDIDO":
        text = [f"Tu grupo no llegó al mínimo y no se atendió · te devolvimos {money(returned)}"]
    elif settled.status == "NO_ENTREGADO":
        text = [f"No se pudo entregar · te devolvimos {money(returned)}"]
    else:
        return ""
    for kind, label in (("MERCADO", "En el mercado de barrio"), ("SUPERMERCADO", "En el supermercado")):
        if kind in comparison:
            c = comparison[kind]
            result = f"ahorraste {money(c.savings)}" if c.savings >= 0 else f"pagaste {money(-c.savings)} más"
            text.append(f"{label} costaba {money(c.reference_total)}: {result}")
    return "<br>".join(escape(line) for line in text)


def account(customer, balance, orders, refunds, csrf: str | None = None, details=None, returned=None) -> str:
    details = details or {}
    rows = "".join(
        f"<tr><td>Pedido {o.order_id}</td><td>{escape(o.cycle)}</td><td>{pill(o.status)}</td>"
        f"<td>{money(o.total)}</td></tr>"
        + (f'<tr><td colspan="4" class="muted">{order_detail(*details[o.order_id])}</td></tr>'
           if o.order_id in details else "")
        for o in orders
    )
    total_back = (f'<div class="devuelto">Con Yapa ya te devolvimos {money(returned)}</div>'
                  if returned else "")  # S-132
    pending = "".join(f"<li>{money(r.amount)} · {escape(r.reason)} · {pill(r.status)}</li>" for r in refunds)
    body = (f'<div class="hero-balance">Hola, <strong>{escape(customer.name)}</strong> · zona '
            f'{escape(customer.zone_id)}<div class="grande">Saldo: {money(balance)}</div>{total_back}'
            '<p><a href="/">Hacer mi pedido</a> · <a href="/zona">Mi zona</a> · <a href="/reclamos">Reclamos</a>'
            '</p></div><h2>Mis pedidos</h2>'
            f'<div class="card"><table><tr><th>Pedido</th><th>Ciclo</th><th>Estado</th><th>Total</th></tr>{rows}'
            f'</table></div><div class="card"><strong>Devoluciones pendientes</strong>'
            f'<ul>{pending or "<li class=muted>No tienes.</li>"}</ul></div><h2>Opciones</h2>'
            '<form class="card" method="post" action="/cuenta/devolucion">' + hidden(csrf) +
            '<label>Devolverme de mi saldo a mi Yape/Plin (S/) <input name="monto" inputmode="decimal" '
            'placeholder="0.00"></label><button>Pedir devolución</button></form>'
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
    body = ('<div class="login">' + error + '<form class="card" method="post" action="/entrar">'
            '<p class="muted">Vecino: tu número de cliente y tu PIN de 6 dígitos. Si no tienes PIN, pídeselo '
            'al admin de Yapa.</p>'
            '<label>Soy <select name="tipo"><option value="vecino">Vecino</option>'
            '<option value="admin">Administrador</option></select></label>'
            '<label>Número de cliente o usuario <input name="usuario" autocomplete="username"></label>'
            '<label>PIN o contraseña <input name="secreto" type="password" autocomplete="current-password"></label>'
            '<button>Entrar</button></form></div>')
    return page("Entrar", body)


ADMIN_SECTIONS = [  # PW-06
    ("/admin/armado", "📦 Armado y entrega", "Foto de cada bolsa y de la entrega en la portería"),
    ("/admin/reclamos", "🧾 Reclamos", "Faltantes y productos dañados, por artículo"),
    ("/admin/devoluciones", "💸 Devoluciones", "Saldo que los vecinos piden de vuelta a su Yape o Plin"),
    ("/admin/conciliacion", "⚖️ Conciliación", "Que el dinero recibido cuadre al céntimo"),
    ("/admin/metricas", "📈 Métricas", "Margen por pedido, ahorro entregado y recompra"),
    ("/admin/catalogo", "🥔 Catálogo", "Lista semanal del proveedor aliado"),
    ("/admin/referencias", "🏷️ Precios de referencia", "Mercado de barrio y supermercado, con fecha"),
    ("/admin/colchon", "🧺 Colchón", "Sobrantes guardados para reponer faltantes"),
    ("/admin/vecinos", "👥 Vecinos", "Alta con consentimiento y reinicio del PIN"),
]


def admin(cycle_label: str, pending, csrf: str | None = None) -> str:
    rows = "".join(
        f"<tr><td>{o.order_id}</td><td>{o.customer_id}</td><td>{money(o.total)}</td>"
        f"<td>{escape(o.payment_method)} {escape(o.operation_code)}</td><td>"
        f'<form method="post" action="/admin/verificar">{hidden(csrf)}<input type="hidden" name="pedido" value="{o.order_id}">'
        "<button>Verificar</button></form></td></tr>" for o in pending
    )
    tiles = "".join(f'<a class="tile" href="{path}"><strong>{title}</strong><span>{text}</span></a>'
                    for path, title, text in ADMIN_SECTIONS)
    body = (f'<div class="tiles">{tiles}</div>'
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


def buffer_page(stocks, total, limit, products, csrf: str | None = None, uses=()) -> str:
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
            '<label>Pedido <input name="pedido" inputmode="numeric"></label>'
            f'<label>Producto <select name="producto">{options}</select></label>'
            '<label>Cantidad <input name="cantidad" inputmode="decimal"></label><button>Usar para reponer</button>'
            '</form>')
    if uses:  # CO-08
        used = "".join(f"<tr><td>Pedido {u.order_id}</td><td>{escape(u.product_id)}</td><td>{qty(u.quantity)}</td>"
                       f"<td>{money(u.value)}</td><td>{escape(u.by)}</td></tr>" for u in uses)
        body += ('<div class="card"><strong>Reposiciones</strong><table><tr><th>Pedido</th><th>Producto</th>'
                 f'<th>Cantidad</th><th>Valor</th><th>Quién</th></tr>{used}</table></div>')
    return page("Colchón de reposición", body, csrf)


def metrics_page(cycle_label: str, margins, alerts, savings, repurchase, repurchase_error,
                 csrf: str | None = None, compared=None) -> str:
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
    if compared:  # RF-08
        lines = "".join(
            f"<tr><td>{label}</td><td>{c.baskets}</td><td>{money(c.reference_total)}</td><td>{money(c.yapa_total)}</td>"
            f"<td>{money(c.savings) if c.baskets else '-'}</td><td>{percent(c.percent)}</td></tr>"
            for label, c in (("Mercado de barrio", compared["MERCADO"]), ("Supermercado", compared["SUPERMERCADO"])))
        body += ('<div class="card"><strong>Ahorro frente a otros precios</strong> <span class="muted">(solo canastas '
                 'con todos sus precios de referencia; envío incluido)</span><table><tr><th>Frente a</th>'
                 '<th>Canastas</th><th>Allá costaba</th><th>En Yapa</th><th>Ahorro</th><th>%</th></tr>'
                 f'{lines}</table></div>')
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


def balance_page(balance, csrf: str | None = None) -> str:
    """AU-03: recibido = en curso + retenido + deuda + devoluciones pagadas."""
    ok = balance.difference == 0
    state = ('<div class="card ok"><strong>Cuadra</strong></div>' if ok else
             '<div class="card error"><strong>No cuadra: revisar antes de seguir operando</strong></div>')
    rows = "".join(f"<tr><td>{label}</td><td>{money(value)}</td></tr>" for label, value in (
        ("Recibido por Yape/Plin", balance.received), ("En curso (pedidos sin liquidar)", balance.in_flight),
        ("Retenido por Yapa", balance.kept), ("Deuda con clientes (saldos y devoluciones pendientes)", balance.owed),
        ("Devoluciones ya pagadas", balance.refunds_paid), ("Diferencia", balance.difference)))
    return page("Conciliación del dinero", state + f'<div class="card"><table>{rows}</table></div>', csrf)


def catalog_admin(cycle_label: str, published: bool, products, text: str, csrf: str | None = None) -> str:
    """CW-01: catálogo del ciclo, lista para publicar (S-116, S-117) y desactivar productos."""
    rows = "".join(
        f"<tr><td>{escape(p.product_id)}</td><td>{escape(p.name)}</td><td>{money(p.max_unit_price())}</td>"
        f"<td>{escape(', '.join(f'desde {qty(t.min_quantity)}: {money(t.base_price)}' for t in p.tiers))}</td>"
        f"<td>{qty(p.max_available)} {escape(p.unit)}</td><td>"
        + (f'<form method="post" action="/admin/catalogo/desactivar">{hidden(csrf)}'
           f'<input type="hidden" name="ciclo" value="{escape(cycle_label)}">'
           f'<input type="hidden" name="producto" value="{escape(p.product_id)}"><button>Desactivar</button></form>'
           if p.active else "desactivado")
        + "</td></tr>"
        for p in products
    )
    state = "publicado" if published else "sin publicar: se usa el catálogo base"
    body = (f'<form class="card" method="get" action="/admin/catalogo"><label>Ciclo '
            f'<input name="ciclo" value="{escape(cycle_label)}"></label><button>Ver</button></form>'
            f'<div class="card"><strong>Ciclo {escape(cycle_label)} · {state}</strong>'
            '<table><tr><th>Código</th><th>Producto</th><th>Precio máximo</th><th>Tramos del proveedor</th>'
            f'<th>Máximo</th><th></th></tr>{rows}</table></div>'
            f'<form class="card" method="post" action="/admin/catalogo">{hidden(csrf)}'
            f'<input type="hidden" name="ciclo" value="{escape(cycle_label)}">'
            '<label>Lista del proveedor (una línea por producto, separada por comas, decimales con punto)'
            f'<textarea name="lista" rows="14" style="width:100%;font-family:monospace">{escape(text)}</textarea>'
            '</label><p class="muted">Se publica todo o nada, y solo antes de que el ciclo abra (lunes 00:00).</p>'
            '<button>Publicar catálogo</button></form>')
    return page(f"Catálogo {cycle_label}", body, csrf)


def references_page(rows, csrf: str | None = None) -> str:
    """RF-07: precios de referencia vigentes y ahorro del precio máximo de Yapa (S-128)."""
    from ..reference import TARGET_SAVINGS, savings_percent

    def cell(product, ref):
        if ref is None:
            return "<td>-</td>"
        saving = savings_percent(product.max_unit_price(), ref.price)
        warning = " · menos de 15 %" if saving < TARGET_SAVINGS else ""
        return (f"<td>{money(ref.price)} en {escape(ref.source)} ({ref.observed_on.strftime('%d/%m')})<br>"
                f"ahorro {percent(saving)}{warning}</td>")

    table = "".join(
        f"<tr><td>{escape(p.name)}</td><td>{money(p.max_unit_price())}</td>"
        f"{cell(p, refs.get('MERCADO'))}{cell(p, refs.get('SUPERMERCADO'))}</tr>"
        for p, refs in rows
    )
    options = "".join(f'<option value="{escape(p.product_id)}">{escape(p.name)}</option>' for p, _ in rows)
    body = ('<div class="card"><table><tr><th>Producto</th><th>Máximo Yapa</th><th>Mercado de barrio</th>'
            f'<th>Supermercado</th></tr>{table}</table></div>'
            f'<form class="card" method="post" action="/admin/referencias">{hidden(csrf)}'
            f'<label>Producto <select name="producto">{options}</select></label>'
            '<label>Dónde <select name="tipo"><option value="MERCADO">Mercado de barrio</option>'
            '<option value="SUPERMERCADO">Supermercado</option></select></label>'
            '<label>Precio por kg o unidad <input name="precio" inputmode="decimal" placeholder="0.00"></label>'
            '<label>Fuente (nombre del mercado o tienda) <input name="fuente"></label>'
            '<label>Fecha en que se vio <input name="fecha" type="date"></label>'
            '<button>Registrar precio</button></form>')
    return page("Precios de referencia", body, csrf)


def customers_page(customers, zone_ids, csrf: str | None = None) -> str:
    """AV-08: lista de vecinos, alta con consentimiento y reinicio del PIN. El PIN nunca se lista."""
    rows = "".join(
        f"<tr><td>{c.customer_id}</td><td>{escape(c.name)}</td><td>{escape(c.phone or '-')}</td>"
        f"<td>{escape(c.zone_id)}</td>"
        f"<td>{escape(c.consent_at.strftime('%d/%m/%Y %H:%M')) if c.consent_at else '-'}</td></tr>"
        for c in customers
    )
    zones = "".join(f'<option value="{escape(z)}">{escape(z)}</option>' for z in zone_ids)
    body = (f'<form class="card" method="post" action="/admin/vecinos">{hidden(csrf)}'
            '<strong>Dar de alta</strong>'
            '<label>Nombre <input name="nombre"></label>'
            '<label>Celular <input name="celular" inputmode="numeric" placeholder="9XXXXXXXX"></label>'
            f'<label>Zona <select name="zona">{zones}</select></label>'
            '<label><input type="checkbox" name="consentimiento" value="si" style="width:auto"> El vecino aceptó '
            'que Yapa guarde su nombre y celular para sus pedidos</label>'
            '<button>Registrar y generar PIN</button></form>'
            f'<form class="card" method="post" action="/admin/vecinos/pin">{hidden(csrf)}'
            '<strong>Olvidó su PIN</strong><label>Número de cliente <input name="cliente" inputmode="numeric">'
            '</label><button>Generar PIN nuevo</button></form>'
            '<div class="card"><table><tr><th>N.º</th><th>Nombre</th><th>Celular</th><th>Zona</th>'
            f'<th>Consentimiento</th></tr>{rows}</table></div>')
    return page("Vecinos", body, csrf)
