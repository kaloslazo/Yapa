"""HTML de la interfaz web (WB-07: todo texto se escapa; WB-09: una columna, apto para celular)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from html import escape

from ..domain import MIN_SUBTOTAL
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
details>summary{cursor:pointer;font-weight:700;color:var(--verde-osc);list-style:none}
details>summary::-webkit-details-marker{display:none}
details>summary::before{content:"▸";display:inline-block;width:1.1em;transition:transform .15s}
details[open]>summary::before{transform:rotate(90deg)}
.plegable>summary{padding:2px 0}
.plegable[open]>summary{margin-bottom:8px}
.mini{margin-top:6px}
.mini>summary{font-size:.86rem;color:var(--verde);font-weight:600}
.grupo{margin:8px 0 4px}
.grupo>summary{font-size:1.15rem;padding:8px 0}
.card.en-carrito{border-color:var(--hoja);box-shadow:0 0 0 2px #3fa66b55}
.stepper{display:flex;align-items:center;gap:4px;flex:0 0 auto}
.stepper button{width:40px;height:40px;padding:0;margin:0;border-radius:50%;font-size:1.3rem;line-height:1}
.stepper button[data-delta="-1"]{background:var(--verde-claro);color:var(--verde-osc)}
.stepper .qty{width:62px;flex:0 0 62px;margin:0;padding:8px 4px}
.carrito{position:sticky;bottom:10px;z-index:4;display:flex;gap:12px;align-items:center;flex-wrap:wrap;
background:var(--verde-osc);color:#fff;border-radius:18px;padding:12px 16px;margin-top:16px;
box-shadow:0 8px 24px #14482f55}
.carrito-info{flex:1 1 260px;min-width:0}
.carrito progress{height:8px;margin:6px 0 4px;background:#ffffff33}
.carrito progress::-webkit-progress-bar{background:#ffffff33}
.carrito progress::-webkit-progress-value{background:var(--sol)}
.carrito progress::-moz-progress-bar{background:var(--sol)}
.carrito-meta{font-size:.86rem;color:#d7ecdf;display:flex;gap:10px;flex-wrap:wrap}
.carrito-ahorro{color:var(--sol);font-weight:800}
.carrito button{width:auto;flex:0 0 auto;background:var(--sol);color:var(--tinta);margin:0}
.carrito button:disabled{opacity:.5;cursor:not-allowed}
.carrito.vacio{opacity:.92}
.total{font-size:1.5rem;font-weight:800;color:var(--verde-osc);margin:10px 0 4px}
.resumen td{border:0;padding:3px 6px;color:var(--suave)}
.resumen td:last-child{text-align:right}
.celebra{background:linear-gradient(90deg,var(--sol-claro),#fff);border:2px solid var(--sol);border-radius:14px;
padding:12px 14px;font-weight:700;color:#5e3d00;margin:10px 0}
.grande-ahorro{font-size:1.3rem;text-align:center;padding:16px}
.dos{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0 12px;align-items:end}
.ok{text-align:center}
.check{width:56px;height:56px;border-radius:50%;background:var(--verde);color:#fff;font-size:2rem;font-weight:800;
display:flex;align-items:center;justify-content:center;margin:4px auto 8px}
.aviso-titulo{font-size:1.15rem;font-weight:800;color:var(--verde-osc);margin-bottom:4px}
.error .aviso-titulo{color:var(--rojo)}
.aviso{background:var(--sol-claro);border-color:#f3dca7}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:10px 0}
.kpi{background:#fff;border:1px solid var(--linea);border-radius:14px;padding:12px 14px;box-shadow:0 1px 3px #1d2a2214}
.kpi span{display:block;color:var(--suave);font-size:.82rem;font-weight:600}
.kpi strong{display:block;font-size:1.6rem;color:var(--verde-osc)}
.pedido-cab{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.pedido-total{margin-left:auto;font-weight:800;font-size:1.1rem}
.detalle{background:var(--verde-claro);border-radius:10px;padding:8px 12px;margin:8px 0;font-size:.92rem}
.tracker{display:flex;list-style:none;padding:0;margin:12px 0 6px;counter-reset:paso}
.tracker li{flex:1;text-align:center;font-size:.76rem;color:var(--suave);position:relative;counter-increment:paso}
.tracker li::before{content:counter(paso);display:flex;width:26px;height:26px;margin:0 auto 4px;border-radius:50%;
background:var(--linea);color:var(--suave);align-items:center;justify-content:center;font-weight:800;position:relative;
z-index:1}
.tracker li::after{content:"";position:absolute;top:13px;left:-50%;width:100%;height:3px;background:var(--linea)}
.tracker li:first-child::after{display:none}
.tracker li.hecho{color:var(--verde-osc);font-weight:700}
.tracker li.hecho::before{content:"✓";background:var(--hoja);color:#fff}
.tracker li.hecho::after{background:var(--hoja)}
.acciones{margin-top:8px}
.acciones button{flex:1 1 220px;font-size:.92rem}
.hero-acciones{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-top:10px}
.hero-acciones .btn{padding:9px 14px}
.login-logo{text-align:center}
.login-logo .logo{width:64px;height:64px}
.pasos-tabla td:first-child{width:34px;font-weight:800;color:var(--verde)}
code{background:var(--fondo);border-radius:6px;padding:2px 6px;font-size:.88rem}
.medios{display:flex;gap:10px;margin:8px 0}
.medio{flex:1;display:flex;align-items:center;gap:8px;border:2px solid var(--linea);border-radius:12px;padding:12px;
margin:0;cursor:pointer}
.medio:has(input:checked){border-color:var(--verde);background:var(--verde-claro)}
.medio input,.casilla input{width:auto;margin:0}
.casilla{display:flex;align-items:center;gap:8px;margin:10px 0 0}
.pagar{text-align:center;border:2px solid var(--sol);background:var(--sol-claro)}
.pagar-monto{font-size:2rem;font-weight:800;color:var(--verde-osc)}
.codigo-pago{font-family:ui-monospace,Consolas,monospace;font-size:1.5rem;font-weight:800;letter-spacing:.06em;
background:#fff;border:2px dashed var(--verde);border-radius:12px;padding:10px;margin:8px auto;max-width:360px;
user-select:all}
input[type=file]{padding:8px;background:var(--fondo)}
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


STATUS_WORDS = {  # S-146: lo que ve el vecino
    "REGISTRADO": "Registrado", "CANCELADO_POR_CLIENTE": "Cancelado", "CANCELADO": "Cancelado",
    "LIQUIDADO": "Liquidado", "NO_ATENDIDO": "No se atendió", "NO_ENTREGADO": "No se entregó",
    "POR_VERIFICAR": "Pago por verificar", "VERIFICADO": "Pago verificado", "PENDIENTE": "Pendiente",
    "PAGADO": "Pagado", "APROBADO": "Aprobado", "RECHAZADO": "Rechazado",
}


def pill(status: str, words: bool = False) -> str:
    text = STATUS_WORDS.get(status, status) if words else status
    return f'<span class="pill pill-{escape(status)}">{escape(text)}</span>'


def error_box(code: str, message: str) -> str:
    return (f'<div class="card error" data-code="{escape(code)}"><div class="aviso-titulo">⚠️ {escape(message)}</div>'
            f'<div class="muted">Código: {escape(code)}</div>'
            '<p><a class="btn secundario" href="/" onclick="history.back();return false">Volver</a></p></div>')


ICONS = {"PAPA": "🥔", "CEBOLLA": "🧅", "AJO": "🧄", "LIMON": "🍋", "CAMOTE": "🍠", "ZANAHORIA": "🥕",
         "PLATANO": "🍌", "NARANJA": "🍊", "ZAPALLO": "🎃"}
CATEGORIES = {"FRESCOS": "🥬 Frescos de la semana", "LIMPIEZA": "🧴 Limpieza en galón"}


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
    "</div>"
    '<details class="card plegable"><summary>¿Por qué confiar en Yapa?</summary><table>'
    "<tr><td>💰</td><td>Pagas como máximo el precio que ves. Nunca un cobro extra en la puerta.</td></tr>"
    "<tr><td>↩️</td><td>Lo que ahorramos entre todos vuelve como saldo, y lo puedes pedir de vuelta a tu Yape o Plin."
    "</td></tr>"
    "<tr><td>📸</td><td>Foto de cada bolsa al armarla y foto de la entrega en tu portería.</td></tr>"
    "<tr><td>🧾</td><td>Si algo falta o llega dañado, lo reclamas por artículo y se te devuelve.</td></tr>"
    "<tr><td>🛑</td><td>Si tu grupo no llega al mínimo, te devolvemos el 100 %.</td></tr>"
    "</table></details><h2>Lo de esta semana</h2>"
)

CART_SCRIPT = """<script>
(function(){
  var form=document.getElementById('pedido'); if(!form) return;
  var bar=document.getElementById('carrito'), min=parseFloat(bar.dataset.minimo);
  function money(v){return 'S/ '+v.toFixed(2);}
  function update(){
    var items=0,total=0,ref=0,yref=0;
    form.querySelectorAll('.card[data-precio]').forEach(function(card){
      var q=parseFloat(card.querySelector('.qty').value)||0, p=parseFloat(card.dataset.precio);
      card.classList.toggle('en-carrito', q>0);
      if(q>0){items++; total+=q*p; var r=parseFloat(card.dataset.ref); if(r){ref+=q*r; yref+=q*p;}}
    });
    bar.querySelector('[data-items]').textContent=items+(items==1?' producto':' productos');
    bar.querySelector('[data-total]').textContent=money(total);
    var falta=min-total, meta=bar.querySelector('[data-falta]');
    meta.textContent= falta>0 ? 'Faltan '+money(falta)+' para el mínimo' : '✓ Llegaste al mínimo';
    bar.querySelector('progress').value=Math.min(total,min);
    var ah=bar.querySelector('[data-ahorro]');
    ah.textContent= ref-yref>0 ? '🎉 Ahorras aprox. '+money(ref-yref)+' frente al supermercado' : '';
    bar.classList.toggle('vacio', items==0);
    bar.querySelector('button').disabled= falta>0;
  }
  form.addEventListener('click',function(e){
    var b=e.target.closest('[data-delta]'); if(!b) return; e.preventDefault();
    var input=b.parentNode.querySelector('.qty'), step=parseFloat(input.dataset.step);
    var v=Math.max(0,(parseFloat(input.value)||0)+step*parseFloat(b.dataset.delta));
    var max=parseFloat(input.max); if(max) v=Math.min(v,max);
    input.value= v ? +v.toFixed(2) : ''; update();
  });
  form.addEventListener('input',update); update();
})();
</script>"""


def _product_card(row: dict, shopping: bool) -> str:
    supermarket = next((r.price for r in row.get("references", ()) if r.kind == "SUPERMERCADO"), "")
    name = escape(row["name"])
    stepper = (
        f'<div class="stepper"><button type="button" data-delta="-1" aria-label="Quitar uno de {name}">−</button>'
        f'<input class="qty" type="number" min="0" step="{qty(row["step"])}" data-step="{qty(row["step"])}" '
        f'max="{qty(row["max_quantity"])}" name="cant_{escape(row["product_id"])}" placeholder="0" '
        f'aria-label="Cantidad de {name}">'
        f'<button type="button" data-delta="1" aria-label="Agregar uno de {name}">+</button></div>'
    ) if shopping else ""
    references = "".join(f"<tr><td>{escape(r.source)}: {money(r.price)}</td>"
                         f"<td class=muted>visto el {r.observed_on.strftime('%d/%m')}</td></tr>"
                         for r in row.get("references", ()))
    return (
        f'<div class="card" data-precio="{row["max_price"]}" data-ref="{supermarket}"><div class="producto">'
        f'<div class="icono" aria-hidden="true">{icon(row["product_id"], row["unit"])}</div><div class="info">'
        f'<div class="nombre">{name}</div>'
        f'<div class="precio">{money(row["max_price"])} <small>por {escape(row["unit"])} · hoy pagas máximo '
        f'{money(row["max_price"])}</small></div>'
        + savings_badge(row["max_price"], row.get("references", ()))
        + f'<progress value="{qty(row["ordered"])}" max="{qty(row["goal"])}" '
          f'aria-label="Avance hacia el siguiente descuento"></progress>'
        f'<div class="muted">👥 {escape(row["progress"])}</div>'
        + (f'<details class="mini"><summary>Comparar precios</summary><table>{references}</table></details>'
           if references else "")
        + "</div>" + stepper + "</div></div>"
    )


def _grouped(rows: list[dict], shopping: bool) -> str:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row.get("category", ""), []).append(row)
    return "".join(
        f'<details class="grupo" open><summary>{escape(CATEGORIES.get(cat, cat.title() or "Productos"))} '
        f'<span class="muted">({len(items)})</span></summary>'
        + "".join(_product_card(row, shopping) for row in items) + "</details>"
        for cat, items in groups.items()
    )


def home(cycle_label: str, is_open: bool, rows: list[dict], csrf: str | None = None) -> str:
    estado = "abierto · cierra el miércoles 20:00" if is_open else "cerrado"
    ciclo = f'<div class="ciclo">🗓️ <span>Semana {escape(cycle_label)}: <strong>{estado}</strong></span></div>'
    if not csrf:
        return page("Catálogo de la semana", HOW_IT_WORKS + ciclo + _grouped(rows, False))
    bar = (
        f'<div id="carrito" class="carrito vacio" data-minimo="{MIN_SUBTOTAL}">'
        '<div class="carrito-info"><strong>🛒 Tu carrito</strong> · <span data-items>0 productos</span> · '
        '<strong data-total>S/ 0.00</strong> <small>aprox.</small>'
        f'<progress value="0" max="{MIN_SUBTOTAL}" aria-label="Avance hacia el pedido mínimo"></progress>'
        f'<div class="carrito-meta"><span data-falta>Mínimo {money(MIN_SUBTOTAL)}</span> '
        '<span data-ahorro class="carrito-ahorro"></span></div></div>'
        '<button>Ver mi carrito →</button></div>'
    )
    form = ('<form id="pedido" method="post" action="/cotizar">' + hidden(csrf)
            + _grouped(rows, True) + bar + "</form>" + CART_SCRIPT)
    return page("Catálogo de la semana", ciclo + form, csrf)


def order_lines(lines, names=None) -> str:
    names = names or {}
    rows = "".join(
        f"<tr><td>{escape(names.get(line.product_id, line.product_id))}</td><td>{qty(line.quantity)}</td>"
        f"<td>{money(line.max_unit_price)}</td><td>{money(line.max_total)}</td></tr>"
        for line in lines
    )
    return f"<table><tr><th>Producto</th><th>Cant.</th><th>Precio máx.</th><th>Total</th></tr>{rows}</table>"


def cart(result, names, savings, balance, csrf: str | None = None) -> str:
    """EC-02: el total que vale es este, calculado por el servidor (S-144)."""
    use = min(balance, result.total) if balance > 0 else Decimal("0")  # S-148
    keep = "".join(f'<input type="hidden" name="cant_{escape(line.product_id)}" value="{qty(line.quantity)}">'
                   for line in result.lines)
    saving = (f'<div class="celebra">🎉 Ahorras aprox. <strong>{money(savings)}</strong> frente al supermercado'
              '</div>') if savings > 0 else ""
    body = (
        f'<div class="card">{order_lines(result.lines, names)}'
        f'<table class="resumen"><tr><td>Subtotal</td><td>{money(result.subtotal)}</td></tr>'
        f'<tr><td>Envío máximo</td><td>{money(result.delivery_fee)}</td></tr></table>'
        f'<p class="total">Total a yapear: {money(result.total)}</p>{saving}'
        '<details class="mini"><summary>¿Por qué "máximo"?</summary><p class="muted">Si entre todos llegamos al '
        'siguiente descuento, la diferencia vuelve a tu saldo el sábado. Nunca pagas más de esto.</p></details>'
        '<p><a href="/">← Seguir comprando</a></p></div>'
        f'<form class="card pago" method="post" action="/pedidos">{hidden(csrf)}{keep}'
        '<strong>💳 ¿Cómo pagas?</strong>'
        '<div class="medios"><label class="medio"><input type="radio" name="metodo" value="YAPE" checked> Yape</label>'
        '<label class="medio"><input type="radio" name="metodo" value="PLIN"> Plin</label></div>'
        + (f'<label class="casilla"><input type="checkbox" name="usar_saldo" value="si" checked> Usar mi saldo '
           f'({money(use)})</label><p class="muted">Con tu saldo yapeas {money(result.total - use)}.</p>'
           if balance > 0 else "")
        + '<button>Confirmar pedido</button><p class="muted">Al confirmar te damos el código para poner en el '
          'mensaje de tu Yape o Plin.</p></form>'
    )
    return page("Tu carrito", body, csrf)


NEXT_STEPS = (
    '<table class="pasos-tabla"><tr><td>1</td><td>Yapeas con tu código y verificamos el pago</td>'
    '<td class="muted">hoy</td></tr>'
    '<tr><td>2</td><td>Compramos al por mayor</td><td class="muted">jueves</td></tr>'
    '<tr><td>3</td><td>Entregamos en tu portería, con foto</td><td class="muted">sábado</td></tr>'
    '<tr><td>4</td><td>Te devolvemos lo ahorrado como saldo</td><td class="muted">al liquidar</td></tr></table>'
)


METHOD_NAMES = {"YAPE": "Yape", "PLIN": "Plin"}


def registered(order, csrf: str | None = None, name: str = "", names=None) -> str:
    first = escape(name.split()[0]) if name else ""
    body = (f'<div class="card ok"><div class="check">✓</div>'
            f'<div class="aviso-titulo">¡Listo{", " + first if first else ""}! Tu pedido quedó registrado</div>'
            f'<p><strong>Pedido {order.order_id}</strong> {pill(order.status, True)} '
            f'{pill(order.payment_status, True)}</p>'
            f'<p class="total">Total máximo {money(order.total)}</p></div>'
            + (f'<div class="card pagar"><div class="pagar-monto">Yapea {money(order.paid_external)}</div>'
               f'<div class="muted">y escribe este código en el mensaje de tu {METHOD_NAMES.get(order.payment_method, "")}:</div>'
               f'<div class="codigo-pago">{escape(order.operation_code)}</div>'
               '<div class="muted">Con ese código verificamos tu pago.</div></div>'
               if order.paid_external > 0 else
               '<div class="celebra">💚 Tu saldo cubrió todo: no tienes que yapear.</div>')
            + f'<div class="card"><strong>Qué sigue</strong>{NEXT_STEPS}</div>'
            f'<details class="card plegable"><summary>Ver mis productos ({len(order.lines)})</summary>'
            f'{order_lines(order.lines, names)}</details>'
            '<p><a class="btn" href="/cuenta">Ir a mi cuenta</a></p>')
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


def _tracker(order, delivered: bool) -> str:
    if order.status not in ("REGISTRADO", "LIQUIDADO"):
        return ""
    steps = [("Pedido", True), ("Pago verificado", order.payment_status == "VERIFICADO"),
             ("Entregado", delivered or order.status == "LIQUIDADO"), ("Liquidado", order.status == "LIQUIDADO")]
    return '<ol class="tracker">' + "".join(
        f'<li class="{"hecho" if done else ""}">{label}</li>' for label, done in steps) + "</ol>"


def _order_card(order, csrf, detail, cancellable, delivered, names) -> str:
    actions = ""
    if cancellable:  # EC-04, S-147
        actions = (f'<form method="post" action="/cuenta/cancelar" class="acciones">{hidden(csrf)}'
                   f'<input type="hidden" name="pedido" value="{order.order_id}">'
                   '<button class="secundario" name="destino" value="MEDIO_DE_PAGO">Cancelar y devolver a mi '
                   'Yape/Plin</button><button class="secundario" name="destino" value="SALDO">Cancelar y pasar a mi '
                   'saldo</button></form>')
    return (
        f'<div class="card pedido"><div class="pedido-cab"><strong>Pedido {order.order_id}</strong>'
        f'<span class="muted">semana {escape(order.cycle)}</span>{pill(order.status, True)}'
        f'<span class="pedido-total">{money(order.total)}</span></div>'
        + _tracker(order, delivered)
        + (f'<div class="detalle">💳 Falta tu pago: yapea <strong>{money(order.paid_external)}</strong> por '
           f'{METHOD_NAMES.get(order.payment_method, "")} con el código <code>{escape(order.operation_code)}</code></div>'
           if order.status == "REGISTRADO" and order.payment_status == "POR_VERIFICAR" and order.paid_external > 0
           else "")
        + (f'<div class="detalle">{detail}</div>' if detail else "")
        + f'<details class="mini"><summary>Ver productos ({len(order.lines)})</summary>'
          f'{order_lines(order.lines, names)}</details>' + actions + "</div>"
    )


def account(customer, balance, orders, refunds, csrf: str | None = None, details=None, returned=None,
            cancellable=(), delivered=(), names=None, saved=None) -> str:
    details = details or {}
    cards = "".join(
        _order_card(o, csrf, order_detail(*details[o.order_id]) if o.order_id in details else "",
                    o.order_id in cancellable, o.order_id in delivered, names)
        for o in sorted(orders, key=lambda o: o.order_id, reverse=True)
    ) or '<div class="card muted">Todavía no tienes pedidos. <a href="/">Haz el primero</a>.</div>'
    total_back = (f'<div class="devuelto">Con Yapa ya te devolvimos {money(returned)}</div>'
                  if returned else "")  # S-132
    celebrate = (f'<div class="celebra grande-ahorro">🎉 Ahorraste {money(saved)} frente al supermercado</div>'
                 if saved and saved > 0 else "")  # EC-04
    pending = "".join(f"<tr><td>{money(r.amount)}</td><td>{escape(r.reason)}</td><td>{pill(r.status, True)}</td></tr>"
                      for r in refunds)
    body = (f'<div class="hero-balance">Hola, <strong>{escape(customer.name)}</strong> · zona '
            f'{escape(customer.zone_id)}<div class="grande">Saldo: {money(balance)}</div>{total_back}'
            '<div class="hero-acciones"><a class="btn btn-sol" href="/">🛒 Hacer mi pedido</a>'
            '<a href="/zona">Mi zona</a><a href="/reclamos">Reclamos</a></div></div>'
            + celebrate + '<h2>Mis pedidos</h2>' + cards
            + (f'<details class="card plegable" open><summary>Devoluciones pendientes ({len(refunds)})</summary>'
               f'<table><tr><th>Monto</th><th>Motivo</th><th>Estado</th></tr>{pending}</table></details>'
               if refunds else "")
            + '<details class="card plegable"><summary>⚙️ Más opciones</summary>'
            '<form method="post" action="/cuenta/devolucion">' + hidden(csrf) +
            '<label>Devolverme de mi saldo a mi Yape/Plin (S/) <input name="monto" inputmode="decimal" '
            f'value="{money(balance)[3:] if balance > 0 else ""}" placeholder="0.00"></label>'
            '<button>Pedir devolución</button></form>'
            '<form method="post" action="/cuenta/pin">' + hidden(csrf) +
            '<div class="dos"><label>PIN actual <input name="actual" type="password" inputmode="numeric"></label>'
            '<label>PIN nuevo (6 dígitos) <input name="nuevo" type="password" inputmode="numeric"></label></div>'
            '<button class="secundario">Cambiar PIN</button></form></details>')
    return page("Mi cuenta", body, csrf)


def login(error: str = "") -> str:
    body = ('<div class="login">' + error + '<form class="card" method="post" action="/entrar">'
            '<div class="login-logo">' + LOGO + '</div>'
            '<label>Soy <select name="tipo"><option value="vecino">Vecino</option>'
            '<option value="admin">Administrador</option></select></label>'
            '<label>Número de cliente o usuario <input name="usuario" autocomplete="username"></label>'
            '<label>PIN o contraseña <input name="secreto" type="password" autocomplete="current-password"></label>'
            '<button>Entrar</button>'
            '<details class="mini"><summary>¿No tienes PIN?</summary><p class="muted">Pídeselo al admin de Yapa '
            'por WhatsApp. Te lo envía una sola vez.</p></details></form></div>')
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


def cycle_select(cycles, selected: str) -> str:
    """EC-07: el ciclo se elige de una lista."""
    options = "".join(f'<option value="{escape(c)}"{" selected" if c == selected else ""}>{escape(c)}</option>'
                      for c in cycles)
    return f'<select name="ciclo">{options}</select>'


def kpis(items) -> str:
    return '<div class="kpis">' + "".join(
        f'<div class="kpi"><span>{escape(label)}</span><strong>{escape(str(value))}</strong></div>'
        for label, value in items) + "</div>"


def admin(cycle_label: str, pending, csrf: str | None = None, stats=None, cycles=()) -> str:
    rows = "".join(
        f"<tr><td>{o.order_id}</td><td>{o.customer_id}</td><td>{money(o.total)}</td>"
        f"<td>{escape(o.payment_method)}</td><td><code>{escape(o.operation_code)}</code></td><td>"
        f'<form method="post" action="/admin/verificar">{hidden(csrf)}'
        f'<input type="hidden" name="pedido" value="{o.order_id}"><button>✓ Verificar</button></form></td></tr>'
        for o in pending
    )
    tiles = "".join(f'<a class="tile" href="{path}"><strong>{title}</strong><span>{text}</span></a>'
                    for path, title, text in ADMIN_SECTIONS)
    pending_box = (f'<table><tr><th>Pedido</th><th>Cliente</th><th>Total</th><th>Medio</th><th>Código</th><th></th>'
                   f'</tr>{rows}</table>' if pending else '<p class="muted">✓ No hay pagos por verificar.</p>')
    body = (f'<div class="ciclo">🗓️ <span>Semana <strong>{escape(cycle_label)}</strong></span></div>'
            + kpis(stats or ())
            + f'<div class="card"><strong>💳 Pagos por verificar ({len(pending)})</strong>{pending_box}</div>'
            f'<div class="tiles">{tiles}</div>'
            '<form class="card" method="post" action="/admin/liquidar">' + hidden(csrf) +
            '<strong>🧮 Liquidar una semana</strong><div class="dos"><label>Semana '
            f'{cycle_select(cycles or [cycle_label], cycle_label)}</label>'
            '<button>Liquidar</button></div></form>')
    return page("Administración", body, csrf)


def settlement(result, csrf: str | None = None) -> str:
    products = "".join(
        f"<tr><td>{escape(p.product_id)}</td><td>{qty(p.total_quantity)}</td><td>desde {qty(p.tier_min_quantity)}</td>"
        f"<td>{money(p.final_unit_price)}</td></tr>" for p in result.products.values()
    )
    orders = "".join(
        f"<tr><td>{o.order_id}</td><td>{pill(o.status)}</td><td>{money(o.paid)}</td><td>{money(o.final_amount)}</td>"
        f"<td>{money(o.refund_amount)} {escape(o.refund_destination or '')}</td></tr>" for o in result.orders.values()
    )
    settled = sum(1 for o in result.orders.values() if o.status == "LIQUIDADO")
    body = (kpis([("Pedidos liquidados", settled), ("Devuelto como saldo", money(result.total_credited)),
                  ("Reembolsado", money(result.total_refunded))])
            + f'<details class="card plegable" open><summary>Pedidos ({len(result.orders)})</summary>'
            f'<table><tr><th>Pedido</th><th>Estado</th><th>Pagado</th><th>Final</th><th>Devuelto</th></tr>{orders}'
            '</table></details>'
            f'<details class="card plegable"><summary>Precio final por producto ({len(result.products)})</summary>'
            f'<table><tr><th>Producto</th><th>Total</th><th>Tramo</th><th>Precio final</th></tr>{products}</table>'
            '</details>')
    return page(f"Liquidación {result.cycle}", body, csrf)


def simple(title: str, message: str, csrf: str | None = None, back: str | None = None, ok: bool = True) -> str:
    """EC-06: lo que sale bien se ve como éxito; 404, 405 y 403 no."""
    link = f'<p><a class="btn secundario" href="{escape(back)}">Volver</a></p>' if back else ""
    if ok:
        return page(title, f'<div class="card ok"><div class="check">✓</div>'
                           f'<div class="aviso-titulo">{escape(message)}</div>{link}</div>', csrf)
    return page(title, f'<div class="card aviso">{escape(message)}'
                       '<p><a class="btn secundario" href="/">Ir al inicio</a></p></div>', csrf)


# --- iteración 12: zonas, reclamos, armado, entrega, colchón y métricas ---

ZONE_STATUS = {"ACTIVA": "Activa", "PENDIENTE_RECEPCION": "Falta quien reciba"}
RECEPTION = [("PORTERIA", "Portería"), ("ENCARGADO", "Encargado"), ("ADMIN", "Yo, el admin de la zona")]
REASONS = {"FALTANTE": "Faltó", "DANADO": "Llegó dañado"}


def photo(reference: str) -> str:
    """S-72: la foto es una referencia de texto; se muestra como texto, nunca como enlace ni imagen."""
    return f'<span class="muted">foto: {escape(reference)}</span>'


def _zone_options(zones, exclude: str = "") -> str:
    return "".join(f'<option value="{escape(z.zone_id)}">{escape(z.name)} · {escape(z.district)}</option>'
                   for z in zones if z.zone_id != exclude)


def _zone_admin_forms(zone, requests, csrf, zones=(), neighbors=()) -> str:
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
        f'<label>Unirme con la zona <select name="destino">{_zone_options(zones, zone.zone_id)}</select></label>'
        '<button>Pedir unión</button></form>'
        f'<div class="card"><strong>Solicitudes de unión</strong>{received or "<p class=muted>No hay.</p>"}</div>'
        f'<form class="card" method="post" action="/zona/separar">{hidden(csrf)}{zone_field}'
        '<button>Separar mi zona del grupo</button></form>'
        f'<form class="card" method="post" action="/zona/transferir">{hidden(csrf)}{zone_field}'
        f'<label>Nuevo admin <select name="nuevo">'
        + "".join(f'<option value="{c.customer_id}">{escape(c.name)} ({c.customer_id})</option>' for c in neighbors)
        + '</select></label>'
        '<button>Transferir el rol</button></form>'
    )


def zone_page(customer, my_zone, zones, admin_zone, requests, districts, csrf: str | None = None,
              neighbors=()) -> str:
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
        mine + (_zone_admin_forms(admin_zone, requests, csrf, zones, neighbors) if admin_zone else "")
        + f'<div class="card"><strong>Zonas</strong><table><tr><th>Código</th><th>Nombre</th><th>Distrito</th>'
          f'<th>Estado</th></tr>{rows}</table></div>'
        + f'<form class="card" method="post" action="/zona/unirse">{hidden(csrf)}'
          f'<label>Unirme a la zona <select name="zona">{_zone_options(zones, customer.zone_id)}</select></label>'
          '<button>Unirme</button></form>'
        + '<details class="card plegable"><summary>➕ Crear una zona nueva</summary>'
        + f'<form method="post" action="/zona/crear">{hidden(csrf)}'
          '<label>Nombre del edificio o barrio <input name="nombre"></label>'
          f'<label>Distrito <select name="distrito">{options}</select></label>'
          '<button type="button" class="secundario" onclick="ubicar(this.form)">📍 Usar mi ubicación</button>'
          '<div class="dos"><label>Latitud <input name="lat" inputmode="decimal" readonly></label>'
          '<label>Longitud <input name="lon" inputmode="decimal" readonly></label></div>'
          '<script>function ubicar(f){if(!navigator.geolocation)return;navigator.geolocation.getCurrentPosition('
          'function(p){f.lat.value=p.coords.latitude.toFixed(5);f.lon.value=p.coords.longitude.toFixed(5);});}'
          '</script>'
          '<button>Crear zona</button></form>'
        + '</details>'
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
    form = (f'<form class="card" method="post" action="/reclamos" enctype="multipart/form-data">{hidden(csrf)}'
            f'<label>Artículo <select name="articulo">{items}</select></label>'
            '<label>Cantidad <input name="cantidad" inputmode="decimal"></label>'
            f'<label>Motivo <select name="motivo">{reasons}</select></label>'
            '<label>📷 Foto <input type="file" name="foto_archivo" accept="image/*" capture="environment"></label>'
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
            f'<form method="post" action="/admin/bolsa" enctype="multipart/form-data">{hidden(csrf)}'
            f'<input type="hidden" name="pedido" value="{order.order_id}">'
            '<label>📷 Foto de la bolsa <input type="file" name="foto_archivo" accept="image/*" capture="environment"></label><button>Registrar bolsa</button></form></div>'
        )
    deliveries = []
    for zone, delivery in stops:
        if delivery:
            state = (f"Entregada a {escape(delivery.received_by)} · {len(delivery.order_ids)} pedidos · "
                     f"{photo(delivery.photo)}")
            form = ""
        else:
            state = "Sin entregar"
            form = (f'<form method="post" action="/admin/entrega" enctype="multipart/form-data">{hidden(csrf)}'
                    f'<input type="hidden" name="ciclo" value="{escape(cycle_label)}">'
                    f'<input type="hidden" name="zona" value="{escape(zone.zone_id)}">'
                    '<label>📷 Foto de la entrega <input type="file" name="foto_archivo" accept="image/*" capture="environment"></label>'
                    '<label>Nombre de quien recibe <input name="recibe"></label><button>Registrar entrega</button>'
                    '</form>'
                    f'<form method="post" action="/admin/entrega-fallida" enctype="multipart/form-data">{hidden(csrf)}'
                    f'<input type="hidden" name="ciclo" value="{escape(cycle_label)}">'
                    f'<input type="hidden" name="zona" value="{escape(zone.zone_id)}">'
                    '<label>Si no recibieron: motivo <select name="motivo">'
                    '<option value="PORTERIA_CERRADA">Portería cerrada</option>'
                    '<option value="NADIE_RECIBE">No había quién reciba</option>'
                    '<option value="PORTERIA_RECHAZA">La portería no aceptó</option></select></label>'
                    '<label>📷 Foto de evidencia <input type="file" name="foto_archivo" accept="image/*" capture="environment"></label>'
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


def buffer_page(stocks, total, limit, products, csrf: str | None = None, uses=(), orders=()) -> str:
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
            f'<label>Pedido <select name="pedido">'
            + "".join(f'<option value="{o.order_id}">Pedido {o.order_id} · cliente {o.customer_id} · '
                      f'{escape(o.cycle)}</option>' for o in orders)
            + '</select></label>'
            f'<label>Producto <select name="producto">{options}</select></label>'
            '<label>Cantidad <input name="cantidad" inputmode="decimal"></label><button>Usar para reponer</button>'
            '</form>')
    if uses:  # CO-08
        used = "".join(f"<tr><td>Pedido {u.order_id}</td><td>{escape(u.product_id)}</td><td>{qty(u.quantity)}</td>"
                       f"<td>{money(u.value)}</td><td>{escape(u.by)}</td></tr>" for u in uses)
        body += ('<div class="card"><strong>Reposiciones</strong><table><tr><th>Pedido</th><th>Producto</th>'
                 f'<th>Cantidad</th><th>Valor</th><th>Quién</th></tr>{used}</table></div>')
    return page("Colchón de reposición", body, csrf)


def metrics_error(cycle_label: str, cycles, error, csrf: str | None = None) -> str:
    """EC-07: si la semana no se puede ver, el selector sigue a mano para elegir otra."""
    body = (f'<form class="card dos" method="get" action="/admin/metricas"><label>Semana '
            f'{cycle_select(cycles or [cycle_label], cycle_label)}</label><button>Ver</button></form>'
            + error_box(error.code, str(error)))
    return page(f"Métricas {cycle_label}", body, csrf)


def metrics_page(cycle_label: str, margins, alerts, savings, repurchase, repurchase_error,
                 csrf: str | None = None, compared=None, cycles=()) -> str:
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
    body = (f'<form class="card dos" method="get" action="/admin/metricas"><label>Semana '
            f'{cycle_select(cycles or [cycle_label], cycle_label)}</label><button>Ver</button></form>'
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


def catalog_admin(cycle_label: str, published: bool, products, text: str, csrf: str | None = None,
                  cycles=()) -> str:
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
    body = (f'<form class="card dos" method="get" action="/admin/catalogo"><label>Semana '
            f'{cycle_select(cycles or [cycle_label], cycle_label)}</label><button>Ver</button></form>'
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
    people = "".join(f'<option value="{c.customer_id}">{escape(c.name)} ({c.customer_id})</option>'
                     for c in customers)
    body = (f'<form class="card" method="post" action="/admin/vecinos">{hidden(csrf)}'
            '<strong>Dar de alta</strong>'
            '<label>Nombre <input name="nombre"></label>'
            '<label>Celular <input name="celular" inputmode="numeric" placeholder="9XXXXXXXX"></label>'
            f'<label>Zona <select name="zona">{zones}</select></label>'
            '<label><input type="checkbox" name="consentimiento" value="si" style="width:auto"> El vecino aceptó '
            'que Yapa guarde su nombre y celular para sus pedidos</label>'
            '<button>Registrar y generar PIN</button></form>'
            f'<form class="card" method="post" action="/admin/vecinos/pin">{hidden(csrf)}'
            f'<strong>Olvidó su PIN</strong><label>Vecino <select name="cliente">{people}</select>'
            '</label><button>Generar PIN nuevo</button></form>'
            '<div class="card"><table><tr><th>N.º</th><th>Nombre</th><th>Celular</th><th>Zona</th>'
            f'<th>Consentimiento</th></tr>{rows}</table></div>')
    return page("Vecinos", body, csrf)
