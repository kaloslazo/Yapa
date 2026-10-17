"""Genera las imágenes de la presentación de la iteración 2.

Uso: python slides/iteracion-2/generar_imagenes.py   (desde la raíz del repo)
Los números salen de docs/analisis/08_validacion_economica.md, del código
(src/yapa_sdd) y de docs/evidencia/.
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

OUT = os.path.join(os.path.dirname(__file__), "img")
os.makedirs(OUT, exist_ok=True)

for name in ("Calibri", "Arial"):
    if any(f.name == name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = name
        break

INK = "#1F2A24"
MUTED = "#5F6F66"
GREEN = "#2E7D4F"
DARK = "#1F3D2B"
ORANGE = "#D9822B"
GREEN_T = "#E6F1EA"
ORANGE_T = "#FBEADB"
LINE = "#C9D3CD"
GRAY_T = "#F1F3F2"

W, H = 12.3, 5.6


def canvas(w=W, h=H):
    fig = plt.figure(figsize=(w, h), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fc=GRAY_T, ec="none", color=INK, size=15, weight="normal", r=0.12):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=1.5))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=color, fontsize=size,
            fontweight=weight, linespacing=1.25)


def arrow(ax, x1, y1, x2, y2, color=MUTED, lw=2, style="-|>", ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=18, color=color,
                                 lw=lw, linestyle=ls, connectionstyle=f"arc3,rad={rad}"))


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=200, facecolor="white")
    plt.close(fig)


# 01 · Una frase, muchas preguntas
def ambiguedad():
    fig, ax = canvas()
    cx, cy = W / 2, H / 2
    box(ax, cx - 2.3, cy - 0.55, 4.6, 1.1, "“El vecino debe poder\nregistrar su pedido”", fc=DARK, color="white",
        size=19, weight="bold")
    qs = [("¿Hasta qué hora?", 0.6, 4.4), ("¿Cuánto es el mínimo?", 4.35, 4.5), ("¿Quién pone el precio?", 8.3, 4.4),
          ("¿Y si sube el precio\ndel mayorista?", 0.4, 0.5), ("¿Cómo se paga\ny se verifica?", 4.35, 0.2),
          ("¿Y si mis vecinos\nno compran?", 8.5, 0.5)]
    for text, x, y in qs:
        bw, bh = 3.4, 0.95
        bx, by = x + bw / 2, y + bh / 2
        ey = cy + 0.55 if by > cy else cy - 0.55
        ex = cx + max(-2.0, min(2.0, (bx - cx) * 0.5))
        ty = y if by > cy else y + bh
        ax.plot([ex, bx], [ey, ty], color=LINE, lw=2, zorder=0)
        box(ax, x, y, bw, bh, text, fc=ORANGE_T, color=INK, size=15)
    save(fig, "01_ambiguedad.png")


# 02 · Flujo SDD
def flujo():
    fig, ax = canvas(h=4.6)
    steps = ["Necesidad", "Requisito", "Especificación", "Criterios de\naceptación", "Diseño", "Código", "Validación"]
    n = len(steps)
    xs = [0.9 + i * (W - 1.8) / (n - 1) for i in range(n)]
    y = 2.5
    for i, (x, s) in enumerate(zip(xs, steps)):
        col = GREEN if i in (2, 3) else DARK
        ax.add_patch(Circle((x, y), 0.5, fc=col, ec="none"))
        ax.text(x, y, str(i + 1), ha="center", va="center", color="white", fontsize=22, fontweight="bold")
        ax.text(x, y - 0.95, s, ha="center", va="top", color=INK, fontsize=15, linespacing=1.2)
        if i < n - 1:
            arrow(ax, x + 0.58, y, xs[i + 1] - 0.58, y, color=MUTED)
    arrow(ax, xs[-1], y + 0.55, xs[2], y + 0.55, color=ORANGE, lw=2.2, ls="--", rad=0.18)
    ax.text((xs[-1] + xs[2]) / 2, 3.95, "si algo cambia, se cambia primero la spec", ha="center", va="center",
            color=ORANGE, fontsize=15, fontstyle="italic", bbox=dict(fc="white", ec="none", pad=2))
    save(fig, "02_flujo_sdd.png")


# 03 · Piezas de una especificación (con ejemplo real)
def piezas():
    fig, ax = canvas(h=5.2)
    rows = [("Requisito", "Quiero pedir mi semana sin pagar de más"),
            ("Especificación", "Entrada JSON · reglas en orden · salida · 15 errores"),
            ("Regla de negocio", "RP-10 · subtotal exacto ≥ S/ 50.00"),
            ("Criterio de aceptación", "DADO S/ 49.99568 → SUBTOTAL_BELOW_MINIMUM"),
            ("Contrato", "register_order(...) → Order | BusinessRuleError(code)")]
    for i, (k, v) in enumerate(rows):
        y = 4.3 - i * 1.0
        box(ax, 0.3, y, 3.4, 0.78, k, fc=DARK, color="white", size=16, weight="bold")
        box(ax, 3.9, y, 8.1, 0.78, v, fc=GREEN_T if i % 2 == 0 else GRAY_T, color=INK, size=15)
    save(fig, "03_piezas.png")


# 04 · La semana de Yapa
def ciclo():
    fig, ax = canvas(h=5.0)
    days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Después"]
    x0, dw = 0.35, 1.66
    for i, d in enumerate(days):
        ax.text(x0 + i * dw + dw / 2, 4.55, d, ha="center", color=MUTED, fontsize=16, fontweight="bold")
        ax.plot([x0 + i * dw, x0 + i * dw], [0.35, 4.3], color=LINE, lw=1)
    box(ax, x0 + 0.05, 3.1, dw * 2.72, 0.9, "Vecinos arman y yapean su pedido\n(precio máximo)", fc=GREEN_T, size=14)
    ax.plot([x0 + 2 * dw + dw * 0.8] * 2, [0.35, 4.3], color=ORANGE, lw=3)
    ax.text(x0 + 2 * dw + dw * 0.8, 0.12, "cierre 20:00", ha="center", color=ORANGE, fontsize=14, fontweight="bold")
    box(ax, x0 + 3 * dw + 0.05, 2.0, dw - 0.1, 0.9, "Compra al\nproveedor", fc=GRAY_T, size=14)
    box(ax, x0 + 4 * dw + 0.05, 2.0, dw - 0.1, 0.9, "Armado +\nfoto por bolsa", fc=GRAY_T, size=14)
    box(ax, x0 + 5 * dw + 0.05, 2.0, dw - 0.1, 0.9, "Entrega en\nportería", fc=GRAY_T, size=14)
    box(ax, x0 + 6 * dw + 0.05, 0.9, dw - 0.1, 1.0, "Te\ndevolvemos", fc=DARK, color="white", size=15, weight="bold")
    save(fig, "04_ciclo_semanal.png")


# 05 · Antecedentes que cerraron
def antecedentes():
    data = [("Missfresh (China)", 2014, 2022, "almacenes propios"),
            ("Freshmart (Perú)", 2016, 2024, "cierre de la matriz"),
            ("Merqueo (Colombia)", 2017, 2025, "inventario + deuda"),
            ("Frubana (LatAm)", 2018, 2025, "sin caja"),
            ("Favo (Perú)", 2019, 2024, "sin margen por pedido"),
            ("Muni (LatAm)", 2019, 2022, "CAC alto, ticket bajo"),
            ("Meituan Youxuan", 2020, 2025, "dependía de subsidios")]
    fig = plt.figure(figsize=(W, H), dpi=200)
    ax = fig.add_axes([0.18, 0.12, 0.6, 0.84])
    for i, (name, a, b, why) in enumerate(reversed(data)):
        ax.barh(i, b - a, left=a, height=0.5, color=DARK)
        ax.plot(b, i, marker="X", color=ORANGE, markersize=13, markeredgecolor="white")
        ax.text(2026.3, i, why, va="center", color=INK, fontsize=15)
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels([d[0] for d in reversed(data)], fontsize=15, color=INK)
    ax.set_xlim(2013.5, 2026)
    ax.set_xticks(range(2014, 2027, 2))
    ax.tick_params(axis="x", colors=MUTED, labelsize=13)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRAY_T)
    ax.set_axisbelow(True)
    save(fig, "05_antecedentes.png")


# 06 · Antes / después del cobro
def legal():
    fig, ax = canvas()
    box(ax, 0.3, 0.3, 5.7, 5.0, "", fc=ORANGE_T)
    box(ax, 6.3, 0.3, 5.7, 5.0, "", fc=GREEN_T)
    ax.text(3.15, 4.75, "Antes (Entregable 1)", ha="center", fontsize=19, fontweight="bold", color=ORANGE)
    ax.text(9.15, 4.75, "Ahora (spec v2)", ha="center", fontsize=19, fontweight="bold", color=GREEN)
    left = ["Pagas el precio de referencia", "El peso real sale mayor", "En la puerta te cobran la diferencia",
            "Si no pagas: sin pedido y suspendido"]
    right = ["Pagas el precio máximo", "Entre todos baja el precio", "Nunca pagas más de lo que viste",
             "Te devolvemos la diferencia"]
    for i, (a, b) in enumerate(zip(left, right)):
        y = 3.9 - i * 0.95
        box(ax, 0.7, y - 0.33, 4.9, 0.66, a, fc="white", size=15)
        box(ax, 6.7, y - 0.33, 4.9, 0.66, b, fc="white", size=15)
        if i < 3:
            arrow(ax, 3.15, y - 0.36, 3.15, y - 0.6)
            arrow(ax, 9.15, y - 0.36, 9.15, y - 0.6)
    ax.text(3.15, 0.55, "Ley 29571, art. 4.2: no se pueden cobrar recargos al precio fijado", ha="center",
            fontsize=13, color=ORANGE, fontstyle="italic")
    save(fig, "06_legal_antes_despues.png")


# 08 · Costo de entrega por pedido
def costos():
    fig = plt.figure(figsize=(W, 4.2), dpi=200)
    ax = fig.add_axes([0.26, 0.2, 0.68, 0.72])
    rows = [("Casa por casa (courier)", 8, 15, ORANGE), ("Una parada por edificio", 0.89, 2.6, GREEN)]
    for i, (name, lo, hi, col) in enumerate(rows):
        y = 1 - i
        ax.plot([lo, hi], [y, y], color=col, lw=10, solid_capstyle="round")
        ax.text(lo - 0.3, y, f"S/ {lo:g}", ha="right", va="center", fontsize=16, color=INK)
        ax.text(hi + 0.3, y, f"S/ {hi:g}", ha="left", va="center", fontsize=16, color=INK)
    ax.set_yticks([1, 0])
    ax.set_yticklabels([r[0] for r in rows], fontsize=17, color=INK)
    ax.set_xlim(-1.5, 17.5)
    ax.set_ylim(-0.6, 1.6)
    ax.set_xlabel("costo de transporte por pedido (S/)", color=MUTED, fontsize=14)
    ax.tick_params(axis="x", colors=MUTED, labelsize=13)
    ax.tick_params(axis="y", length=0)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    save(fig, "08_costo_entrega.png")


# 09 · Zonas de vecinos
def zonas():
    fig, ax = canvas()
    for x in [i * 0.9 for i in range(15)]:
        ax.plot([x, x], [0, H], color=GRAY_T, lw=6, zorder=0)
    for y in [i * 0.9 for i in range(8)]:
        ax.plot([0, W], [y, y], color=GRAY_T, lw=6, zorder=0)
    import random
    random.seed(4)
    zones = [(3.0, 3.4, "Zona A\nedificio", GREEN), (5.3, 2.7, "Zona B\ncondominio", GREEN),
             (10.2, 1.3, "Zona C\nlejos", ORANGE)]
    for x, y, label, col in zones:
        ax.add_patch(Circle((x, y), 1.05, fc=col, alpha=0.12, ec=col, lw=2, ls="--"))
        for _ in range(9):
            a, r = random.uniform(0, 6.28), random.uniform(0.3, 0.9)
            ax.plot(x + r * __import__("math").cos(a), y + r * __import__("math").sin(a), "o", color=col,
                    markersize=7, alpha=0.8)
        ax.add_patch(Rectangle((x - 0.18, y - 0.18), 0.36, 0.36, fc=DARK, ec="white", lw=2, zorder=5))
        ax.text(x, y + 1.3, label, ha="center", va="bottom", fontsize=14, color=INK, fontweight="bold")
    ax.plot([3.0, 5.3], [3.4, 2.7], color=GREEN, lw=3, zorder=4)
    ax.text(4.15, 3.35, "unidas", ha="center", fontsize=14, color=GREEN, fontweight="bold", rotation=-17)
    ax.plot([5.3, 10.2], [2.7, 1.3], color=ORANGE, lw=2, ls=":", zorder=4)
    ax.text(7.8, 2.3, "> 500 m: no se une", ha="center", fontsize=14, color=ORANGE, rotation=-16)
    box(ax, 8.3, 4.2, 3.7, 1.1, "", fc="white", ec=LINE)
    ax.add_patch(Rectangle((8.55, 4.84), 0.26, 0.26, fc=DARK))
    ax.text(8.95, 4.97, "punto de recepción (portería)", va="center", fontsize=13, color=INK)
    ax.plot(8.68, 4.5, "o", color=GREEN, markersize=8)
    ax.text(8.95, 4.5, "vecino", va="center", fontsize=13, color=INK)
    save(fig, "09_zonas.png")


# 10 · Te devolvemos (pedido real de CL-04)
def te_devolvemos():
    fig = plt.figure(figsize=(W, H), dpi=200)
    ax = fig.add_axes([0.06, 0.14, 0.9, 0.8])
    steps = [("Pagaste\n(precio máximo)", 0, 61.00, DARK), ("Descuento\npor volumen", 48.14 + 3.00, 9.86, GREEN),
             ("Envío\ncompartido", 48.14, 3.00, GREEN), ("Costo real", 0, 48.14, MUTED),
             ("Te devolvemos", 48.14, 12.86, GREEN)]
    for i, (name, base, h, col) in enumerate(steps):
        ax.bar(i, h, bottom=base, width=0.6, color=col)
        sign = "−" if i in (1, 2) else ""
        ax.text(i, base + h + 1.2, f"{sign}S/ {h:.2f}", ha="center", fontsize=18, color=INK, fontweight="bold")
    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels([s[0] for s in steps], fontsize=15, color=INK)
    ax.set_ylim(0, 70)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.tick_params(axis="x", length=0)
    save(fig, "10_te_devolvemos.png")


# 11 · Si alguien se retira: precio por tramo
def tramos():
    fig = plt.figure(figsize=(W, H), dpi=200)
    ax = fig.add_axes([0.1, 0.15, 0.85, 0.8])
    xs = [0, 100, 100, 250, 250, 320]
    ys = [4.032, 4.032, 3.7856, 3.7856, 3.584, 3.584]
    ax.plot(xs, ys, color=DARK, lw=3)
    ax.axhline(4.032, color=ORANGE, lw=1.5, ls="--")
    ax.text(318, 4.06, "precio máximo pagado S/ 4.032", ha="right", fontsize=14, color=ORANGE)
    ax.plot(100, 3.7856, "o", color=GREEN, markersize=15, markeredgecolor="white", markeredgewidth=2)
    ax.text(104, 3.73, "100 kg → S/ 3.7856", fontsize=15, color=GREEN, fontweight="bold")
    ax.plot(95, 4.032, "o", color=ORANGE, markersize=15, markeredgecolor="white", markeredgewidth=2)
    ax.annotate("uno se retira: 95 kg\nvuelve al máximo,\nnunca lo supera", xy=(95, 4.02), xytext=(15, 3.6),
                fontsize=14, color=INK, arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.5))
    ax.set_xlabel("kg de papa amarilla pedidos entre todos", fontsize=14, color=MUTED)
    ax.set_ylabel("precio final por kg (S/)", fontsize=14, color=MUTED)
    ax.set_ylim(3.45, 4.2)
    ax.set_xlim(0, 320)
    ax.tick_params(colors=MUTED, labelsize=13)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(LINE)
    save(fig, "11_tramos.png")


# 12 · De la regla a la prueba
def trazabilidad():
    fig, ax = canvas(h=4.6)
    chain = [("Decisión", "C-01\nnunca pagar\nde más"), ("Regla", "RP-10\nmínimo exacto\nS/ 50"),
             ("Criterio", "CA-11\nS/ 49.99568\nse rechaza"), ("Código", "order_registration\n.py:116"),
             ("Prueba", "test_ca11_\nminimum_uses_\nexact_subtotal"), ("Demo", "cli registrar\npedido_bajo_\nminimo.json")]
    n = len(chain)
    bw = 1.7
    gap = (W - 0.6 - n * bw) / (n - 1)
    for i, (k, v) in enumerate(chain):
        x = 0.3 + i * (bw + gap)
        box(ax, x, 3.3, bw, 0.7, k, fc=DARK, color="white", size=16, weight="bold")
        box(ax, x, 0.9, bw, 2.2, v, fc=GREEN_T if i % 2 == 0 else GRAY_T, size=14)
        if i < n - 1:
            arrow(ax, x + bw + 0.03, 2.0, x + bw + gap - 0.03, 2.0)
    save(fig, "12_trazabilidad.png")


# 13 · Capas
def capas():
    fig, ax = canvas(h=5.2)
    box(ax, 3.9, 4.1, 4.5, 0.8, "cli.py · consola de la demo", fc=GRAY_T, size=16)
    box(ax, 1.3, 2.4, 4.6, 1.0, "order_registration.py\nRP-01..RP-15", fc=GREEN_T, size=16, weight="bold")
    box(ax, 6.4, 2.4, 4.6, 1.0, "settlement.py\nLQ-01..LQ-09", fc=GREEN_T, size=16, weight="bold")
    for i, (t, x) in enumerate([("domain.py\nreglas del piloto", 0.6), ("cycle.py\nhora de Lima", 4.4),
                                ("store.py\nmemoria → BD", 8.2)]):
        box(ax, x, 0.4, 3.5, 1.0, t, fc=DARK, color="white", size=15)
    arrow(ax, 5.2, 4.08, 3.6, 3.45)
    arrow(ax, 7.1, 4.08, 8.7, 3.45)
    for sx in (3.6, 8.7):
        for tx in (2.35, 6.15, 9.95):
            arrow(ax, sx, 2.37, tx, 1.45, color=LINE, lw=1.6)
    save(fig, "13_capas.png")


# 14 · Historial de Git: spec antes que código
def git_historial():
    commits = ["docs", "docs", "docs", "docs", "docs", "test", "test", "feat", "docs", "test", "feat", "feat", "docs",
               "docs", "docs", "docs"]
    labels = {0: "clarificaciones", 1: "spec v2", 2: "criterios", 3: "plan y diseño", 4: "cotización", 5: "pruebas (rojo)",
              7: "registro", 8: "ajuste spec", 9: "prueba nueva", 10: "liquidación", 11: "demo",
              12: "trazabilidad", 14: "reflexión", 15: "presentación"}
    color = {"docs": GREEN, "test": ORANGE, "feat": DARK}
    fig, ax = canvas(h=3.8)
    n = len(commits)
    xs = [0.6 + i * (W - 1.2) / (n - 1) for i in range(n)]
    ax.plot([xs[0], xs[-1]], [2.0, 2.0], color=LINE, lw=3, zorder=0)
    for i, (x, c) in enumerate(zip(xs, commits)):
        ax.add_patch(Circle((x, 2.0), 0.26, fc=color[c], ec="white", lw=2))
        if i in labels:
            up = i % 2 == 0
            ax.text(x, 2.5 if up else 1.5, labels[i], ha="center", va="bottom" if up else "top", fontsize=13,
                    color=INK, rotation=0)
    for j, (k, c) in enumerate(color.items()):
        ax.add_patch(Circle((4.3 + j * 1.6, 0.35), 0.14, fc=c))
        ax.text(4.5 + j * 1.6, 0.35, k, va="center", fontsize=14, color=INK)
    save(fig, "14_git_historial.png")


# 15 · Rojo → verde
def rojo_verde():
    fig = plt.figure(figsize=(W, 4.6), dpi=200)
    ax = fig.add_axes([0.06, 0.22, 0.9, 0.72])
    etapas = ["1 · pruebas escritas,\nsin código", "2 · registro\nimplementado", "3 · liquidación +\ncasos borde"]
    ok = [0, 30, 45]
    fail = [42, 12, 0]
    ax.bar(range(3), ok, width=0.55, color=GREEN)
    ax.bar(range(3), fail, bottom=ok, width=0.55, color=ORANGE)
    for i in range(3):
        if ok[i]:
            ax.text(i, ok[i] / 2, f"{ok[i]} pasan", ha="center", va="center", color="white", fontsize=16,
                    fontweight="bold")
        if fail[i]:
            ax.text(i, ok[i] + fail[i] / 2, f"{fail[i]} pendientes", ha="center", va="center", color=INK,
                    fontsize=16, fontweight="bold")
    ax.set_xticks(range(3))
    ax.set_xticklabels(etapas, fontsize=15, color=INK)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.tick_params(axis="x", length=0)
    save(fig, "15_rojo_verde.png")


# 16 · Captura de la demo (salida real)
def demo():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "evidencia", "04-demo-consola.txt")
    lines = open(path, encoding="utf-8").read().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("$ python -m yapa_sdd.cli ciclo"))
    block = lines[start:start + 14] + ["   ..."] + [l for l in lines[start:] if " 19 Z-JM" in l or " 22 Z-LINCE" in l] + \
        [""] + [l for l in lines[start:] if l.startswith("Total")]
    fig, ax = canvas(h=6.0)
    ax.add_patch(FancyBboxPatch((0.1, 0.1), W - 0.2, 5.8, boxstyle="round,pad=0,rounding_size=0.15", fc="#14201A"))
    for k, col in enumerate(("#E0655A", "#E7B04A", "#5DBB6C")):
        ax.add_patch(Circle((0.45 + k * 0.32, 5.6), 0.09, fc=col))
    for i, line in enumerate(block):
        col = "#9BE3B0" if line.startswith("$") else ("#F2C38B" if "NO_ATENDIDO" in line or "Total" in line
                                                     else "#E8EFEA")
        ax.text(0.4, 5.3 - i * 0.235, line, family="Consolas", fontsize=10.5, color=col, va="top")
    save(fig, "16_demo.png")


# 17 · Resultados
def resultados():
    fig, ax = canvas(h=3.6)
    kpis = [("24", "reglas\nespecificadas"), ("24", "criterios de\naceptación"), ("45", "pruebas\nen verde"),
            ("16", "commits\ndocs → test → feat")]
    for i, (num, label) in enumerate(kpis):
        x = 0.3 + i * 3.0
        box(ax, x, 0.3, 2.7, 3.0, "", fc=GREEN_T if i % 2 == 0 else GRAY_T)
        ax.text(x + 1.35, 2.35, num, ha="center", va="center", fontsize=54, fontweight="bold", color=DARK)
        ax.text(x + 1.35, 1.0, label, ha="center", va="center", fontsize=16, color=INK, linespacing=1.2)
    save(fig, "17_resultados.png")


# 18 · Lecciones
def lecciones():
    fig, ax = canvas(h=4.4)
    items = [("1", "Preguntar antes\nde programar", "12 decisiones y 12 supuestos\nescritos antes del código"),
             ("2", "Cada regla\ncon su prueba", "24 reglas → 45 pruebas\nque verifican el código de error"),
             ("3", "Cambiar primero\nla spec", "3 cambios en orden\ndocs → test → feat")]
    for i, (num, head, foot) in enumerate(items):
        x = 0.3 + i * 4.0
        box(ax, x, 0.3, 3.7, 3.8, "", fc=GREEN_T if i != 1 else GRAY_T)
        ax.add_patch(Circle((x + 1.85, 3.2), 0.5, fc=DARK))
        ax.text(x + 1.85, 3.2, num, ha="center", va="center", color="white", fontsize=24, fontweight="bold")
        ax.text(x + 1.85, 2.05, head, ha="center", va="center", color=INK, fontsize=20, fontweight="bold",
                linespacing=1.15)
        ax.text(x + 1.85, 0.9, foot, ha="center", va="center", color=MUTED, fontsize=15, linespacing=1.2)
    save(fig, "18_lecciones.png")


if __name__ == "__main__":
    for fn in (ambiguedad, flujo, piezas, ciclo, antecedentes, legal, costos, zonas, te_devolvemos, tramos,
               trazabilidad, capas, git_historial, rojo_verde, demo, resultados, lecciones):
        fn()
    print("imágenes en", OUT)
