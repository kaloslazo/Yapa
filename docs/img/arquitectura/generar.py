"""Genera el diagrama de la arquitectura de Yapa en AWS con los íconos oficiales de AWS.

Uso: python3 docs/img/arquitectura/generar.py
Sale docs/img/arquitectura-aws.svg (para el README) y, si está rsvg-convert, docs/img/arquitectura-aws.png (para informes).

Estilo de los diagramas de referencia de AWS: grupos (AWS Cloud, Region, instancia) con su ícono en la esquina,
nodos con el ícono oficial y una etiqueta corta, flechas en ángulo recto y la explicación en una leyenda numerada.
Los íconos de iconos-aws/ son del paquete oficial "AWS Architecture Icons" (versión del 31/07/2026,
https://aws.amazon.com/architecture/icons/), que AWS permite usar en diagramas. Se incrustan dentro del SVG porque
GitHub no carga imágenes enlazadas desde un SVG.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from html import escape
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ICONOS = AQUI / "iconos-aws"
SALIDA = AQUI.parent / "arquitectura-aws.svg"
ANCHO, ALTO = 1600, 920

TINTA, GRIS, GRIS_CLARO, LINEA = "#232F3E", "#5F6B7A", "#8A96A3", "#D5DBDB"
NARANJA, VERDE_AZULADO, AZUL, VERDE, ROJO = "#ED7100", "#00A4A6", "#1F6FEB", "#1E8E3E", "#DD344C"
FUENTE = "Helvetica Neue, Helvetica, Arial, sans-serif"


def icono(nombre: str, cx: float, cy: float, tam: float) -> str:
    """Ícono oficial centrado en (cx, cy)."""
    texto = (ICONOS / f"{nombre}.svg").read_text(encoding="utf-8")
    caja = re.search(r'viewBox="([^"]+)"', texto).group(1)
    interior = re.search(r"<svg[^>]*>(.*)</svg>", texto, re.S).group(1)
    interior = re.sub(r"<title>.*?</title>", "", interior, flags=re.S)
    interior = re.sub(r'\sid="[^"]*"', "", interior)
    return (f'<svg x="{cx - tam / 2}" y="{cy - tam / 2}" width="{tam}" height="{tam}" viewBox="{caja}">'
            f"{interior.strip()}</svg>")


def texto(x, y, contenido, tam=13, color=TINTA, peso=400, ancla="middle", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{tam}" font-weight="{peso}" fill="{color}" text-anchor="{ancla}"'
            f'{extra}>{escape(contenido)}</text>')


def nodo(nombre, cx, cy, titulo, *detalle, tam=56):
    """Nodo al estilo AWS: ícono y, debajo, nombre en negrita y una o dos líneas cortas."""
    partes = [icono(nombre, cx, cy, tam), texto(cx, cy + tam / 2 + 20, titulo, 14, TINTA, 700)]
    for i, linea in enumerate(detalle):
        partes.append(texto(cx, cy + tam / 2 + 38 + i * 16, linea, 12.5, GRIS))
    return "".join(partes)


def grupo(x, y, w, h, nombre_icono, titulo, color, punteado="", fondo="none", detalle=""):
    """Grupo al estilo AWS: borde de color, ícono de 32 px en la esquina y título al lado."""
    guion = f' stroke-dasharray="{punteado}"' if punteado else ""
    partes = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fondo}" stroke="{color}" stroke-width="1.5"{guion}/>',
              icono(nombre_icono, x + 16, y + 16, 32),
              texto(x + 42, y + 21, titulo, 13.5, TINTA, 700, "start")]
    if detalle:
        partes.append(texto(x + w - 12, y + 21, detalle, 12, GRIS, 400, "end"))
    return "".join(partes)


def flecha(puntos, color=TINTA, punteado="", marcador="f-tinta"):
    """Flecha en ángulo recto por una lista de puntos."""
    d = "M" + " L".join(f"{x} {y}" for x, y in puntos)
    guion = f' stroke-dasharray="{punteado}"' if punteado else ""
    return (f'<path d="{d}" stroke="{color}" stroke-width="1.8" fill="none" stroke-linejoin="round"{guion} '
            f'marker-end="url(#{marcador})"/>')


def paso(cx, cy, etiqueta, color=TINTA):
    return (f'<circle cx="{cx}" cy="{cy}" r="11" fill="{color}" stroke="#FFFFFF" stroke-width="2"/>'
            + texto(cx, cy + 4.5, etiqueta, 12, "#FFFFFF", 700))


def etiqueta(cx, cy, contenido, color):
    ancho = len(contenido) * 7 + 12
    return (f'<rect x="{cx - ancho / 2}" y="{cy - 10}" width="{ancho}" height="20" rx="4" fill="#FFFFFF"/>'
            + texto(cx, cy + 4, contenido, 12, color, 700))


def leyenda(x, y, w, titulo, filas, color):
    partes = [f'<rect x="{x}" y="{y}" width="{w}" height="136" rx="8" fill="#F8F9FA" stroke="{LINEA}"/>',
              texto(x + 20, y + 28, titulo, 14, TINTA, 700, "start")]
    for i, (marca, contenido) in enumerate(filas):
        cy = y + 54 + i * 22
        if marca == "+":  # continuación de la fila anterior
            partes.append(texto(x + 50, cy, contenido, 12.5, TINTA, 400, "start"))
        elif marca:
            partes.append(paso(x + 30, cy - 4, marca, color))
            partes.append(texto(x + 50, cy, contenido, 12.5, TINTA, 400, "start"))
        else:
            partes.append(texto(x + 20, cy, contenido, 12.5, TINTA, 400, "start"))
    return "".join(partes)


def generar() -> str:
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO}" height="{ALTO}" viewBox="0 0 {ANCHO} {ALTO}" '
         f'font-family="{FUENTE}">', "<title>Yapa · arquitectura en AWS</title>", "<defs>"]
    for ident, color in (("f-tinta", TINTA), ("f-azul", AZUL), ("f-verde", VERDE)):
        s.append(f'<marker id="{ident}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
                 f'orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9 z" fill="{color}"/></marker>')
    s += ["</defs>", f'<rect width="{ANCHO}" height="{ALTO}" fill="#FFFFFF"/>']

    # Encabezado
    s.append(texto(40, 52, "Yapa · Arquitectura en AWS", 26, TINTA, 700, "start"))
    s.append(texto(40, 78, "Producción en https://holayapa.app · un solo servidor Lightsail con despliegue continuo "
                           "desde GitHub", 14, GRIS, 400, "start"))

    # Usuarios (fuera de AWS)
    s.append(f'<rect x="40" y="110" width="170" height="410" rx="8" fill="#FFFFFF" stroke="{LINEA}" stroke-width="1.5"/>')
    s.append(texto(56, 134, "Usuarios", 13.5, TINTA, 700, "start"))
    s.append(nodo("Res_Mobile-client_48_Light", 125, 240, "Vecinos", "compran y siguen", "su pedido"))
    s.append(nodo("Res_Users_48_Light", 125, 410, "Equipo Yapa", "admin, compras, armado,", "reparto, portería…"))

    # Let's Encrypt (externo)
    s.append(f'<rect x="40" y="560" width="170" height="190" rx="8" fill="#FFFFFF" stroke="{LINEA}" stroke-width="1.5"/>')
    s.append(texto(56, 584, "Externo", 13.5, TINTA, 700, "start"))
    s.append(nodo("Res_SSL-padlock_48_Light", 125, 650, "Let's Encrypt", "certificado HTTPS"))

    # AWS Cloud
    s.append(grupo(250, 110, 960, 640, "AWS-Cloud-logo_32", "AWS Cloud", TINTA,
                   detalle="cuenta estudiantil UTEC · USD 100 de crédito"))
    s.append(nodo("Arch_Amazon-Route-53_48", 340, 240, "Route 53", "holayapa.app", "→ 18.225.85.8"))

    # Región
    s.append(grupo(430, 160, 760, 570, "Region_32", "us-east-2 (Ohio)", VERDE_AZULADO, punteado="6 4"))

    # Instancia Lightsail
    s.append(grupo(455, 205, 710, 505, "Arch_Amazon-Lightsail_48", "Amazon Lightsail · instancia nano", NARANJA,
                   fondo="#FFFBF5", detalle="Ubuntu 24.04 · 2 vCPU · 512 MB · 20 GB SSD"))
    s.append(nodo("Res_Amazon-EC2_Elastic-IP-Address_48", 515, 410, "IP fija", "18.225.85.8"))
    s.append(nodo("Res_Firewall_48_Light", 630, 410, "Firewall", "22 · 80 · 443"))
    s.append(nodo("Res_Internet_48_Light", 750, 410, "Caddy", "HTTPS y proxy"))
    s.append(nodo("Res_Generic-Application_48_Light", 870, 410, "Motor Yapa", "Python 3.12", "API y web React"))

    # Disco
    s.append(f'<rect x="975" y="250" width="170" height="440" rx="6" fill="#F4F6FE" stroke="#3B48CC" '
             f'stroke-width="1.2" stroke-dasharray="4 3"/>')
    s.append(icono("Res_Amazon-Elastic-Block-Store_Volume_48", 993, 270, 24))
    s.append(texto(1011, 275, "Disco SSD 20 GB", 12.5, TINTA, 700, "start"))
    s.append(nodo("Res_Database_48_Light", 1060, 340, "SQLite", "yapa.db", tam=48))
    s.append(nodo("Res_Multimedia_48_Light", 1060, 470, "Fotos", "bolsas y reclamos", tam=48))
    s.append(nodo("Res_Amazon-Elastic-Block-Store_Snapshot_48", 1060, 600, "Respaldos", "uno por despliegue", tam=48))

    # GitHub (fuera de AWS)
    s.append(f'<rect x="1250" y="110" width="310" height="640" rx="8" fill="#FFFFFF" stroke="{LINEA}" stroke-width="1.5"/>')
    s.append(texto(1266, 136, "GitHub · CI/CD", 13.5, TINTA, 700, "start"))
    s.append(nodo("Res_User_48_Light", 1405, 190, "Desarrollo", "git push a main", tam=44))
    s.append(nodo("Res_Git-Repository_48_Light", 1405, 330, "Repositorio", "kaloslazo/Yapa"))
    s.append(nodo("Res_Gear_48_Light", 1405, 475, "GitHub Actions", "671 + 119 pruebas", "y build de la web"))
    s.append(nodo("Res_Toolkit_48_Light", 1405, 645, "Despliegue", "desplegar.sh por SSH"))

    # Flujo del pedido (1–4)
    s.append(flecha([(186, 240), (306, 240)]))
    s.append(paso(246, 240, "1"))
    s.append(flecha([(186, 410), (485, 410)]))
    s.append(paso(380, 410, "2"))
    s.append(flecha([(545, 410), (600, 410)]))
    s.append(flecha([(660, 410), (720, 410)]))
    s.append(flecha([(780, 410), (840, 410)]))
    s.append(paso(810, 410, "3"))
    s.append(flecha([(900, 400), (940, 400), (940, 340), (1034, 340)]))
    s.append(flecha([(900, 420), (940, 420), (940, 470), (1034, 470)]))
    s.append(paso(940, 410, "4"))
    s.append(flecha([(155, 650), (750, 650), (750, 482)], VERDE, "5 4", "f-verde"))
    s.append(etiqueta(340, 650, "certificado", VERDE))

    # Flujo del código (A–C)
    s.append(flecha([(1405, 260), (1405, 300)], AZUL, marcador="f-azul"))
    s.append(paso(1430, 280, "A", AZUL))
    s.append(flecha([(1405, 406), (1405, 444)], AZUL, marcador="f-azul"))
    s.append(paso(1430, 425, "B", AZUL))
    s.append(flecha([(1405, 568), (1405, 614)], AZUL, marcador="f-azul"))
    s.append(flecha([(1373, 645), (1167, 645)], AZUL, marcador="f-azul"))
    s.append(paso(1300, 645, "C", AZUL))
    s.append(etiqueta(1300, 671, "SSH", AZUL))

    # Leyendas
    s.append(leyenda(40, 770, 500, "Cómo se atiende un pedido", [
        ("1", "El navegador pregunta a Route 53 la IP de holayapa.app."),
        ("2", "Entra por HTTPS a la IP fija; el firewall solo abre 22, 80 y 443."),
        ("3", "Caddy pone el certificado y pasa la petición al motor."),
        ("4", "El motor aplica las reglas y guarda en SQLite y en fotos/.")], TINTA))
    s.append(leyenda(560, 770, 500, "Cómo llega el código a producción", [
        ("A", "Un push a main dispara GitHub Actions."),
        ("B", "Corren las pruebas del motor y de la web y se arma el paquete."),
        ("C", "Si pasan, sube el paquete por SSH; desplegar.sh respalda la"),
        ("+", "base, cambia de versión y vuelve atrás si /salud no responde.")], AZUL))
    s.append(leyenda(1080, 770, 480, "Costo y capacidad", [
        ("", "Lightsail nano con IP fija: ≈ USD 5,00 al mes"),
        ("", "Route 53 (zona holayapa.app): ≈ USD 0,50 al mes"),
        ("", "Total ≈ USD 5,50 al mes: unos 18 meses con USD 100"),
        ("", "Motor medido en producción: ≈ 32 MB de RAM")], TINTA))
    s.append("</svg>")
    return "\n".join(s)


if __name__ == "__main__":
    SALIDA.write_text(generar(), encoding="utf-8")
    print(f"listo: {SALIDA}")
    if shutil.which("rsvg-convert"):
        png = SALIDA.with_suffix(".png")
        subprocess.run(["rsvg-convert", "-z", "2", "-o", str(png), str(SALIDA)], check=True)
        print(f"listo: {png}")
