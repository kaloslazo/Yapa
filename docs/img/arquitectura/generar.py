"""Genera el diagrama de la arquitectura de Yapa en AWS con los íconos oficiales de AWS.

Uso: python3 docs/img/arquitectura/generar.py
Sale docs/img/arquitectura-aws.svg (para el README) y, si está rsvg-convert, docs/img/arquitectura-aws.png (para informes).

Los íconos de iconos-aws/ son del paquete oficial "AWS Architecture Icons" (versión del 31/07/2026,
https://aws.amazon.com/architecture/icons/), que AWS permite usar en diagramas de arquitectura. Se incrustan dentro
del SVG porque GitHub no carga imágenes enlazadas desde un SVG.
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

TINTA, GRIS, GRIS_CLARO = "#232F3E", "#545B64", "#7D8998"
NARANJA, VERDE_AZULADO, MORADO, AZUL_GH, VERDE = "#ED7100", "#00A4A6", "#8C4FFF", "#1F6FEB", "#1E8E3E"


def icono(nombre: str, x: float, y: float, tam: float) -> str:
    """Incrusta un ícono oficial como <svg> anidado en (x, y) con lado tam."""
    texto = (ICONOS / f"{nombre}.svg").read_text(encoding="utf-8")
    caja = re.search(r'viewBox="([^"]+)"', texto).group(1)
    interior = re.search(r"<svg[^>]*>(.*)</svg>", texto, re.S).group(1)
    interior = re.sub(r"<title>.*?</title>", "", interior, flags=re.S)
    interior = re.sub(r'\sid="[^"]*"', "", interior)  # sin id repetidos entre íconos
    return f'<svg x="{x}" y="{y}" width="{tam}" height="{tam}" viewBox="{caja}">{interior.strip()}</svg>'


def t(x, y, contenido, tam=12.5, color=GRIS, peso="400", ancla="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{tam}" font-weight="{peso}" fill="{color}" '
            f'text-anchor="{ancla}"{extra}>{escape(contenido)}</text>')


def lineas(x, y, textos, tam=12.5, color=GRIS, paso=18):
    return "".join(t(x, y + i * paso, s, tam, color) for i, s in enumerate(textos))


def caja(x, y, w, h, borde, fondo="#FFFFFF", grosor=1.5, radio=8, punteado=""):
    guion = f' stroke-dasharray="{punteado}"' if punteado else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radio}" fill="{fondo}" stroke="{borde}" '
            f'stroke-width="{grosor}"{guion}/>')


def grupo(x, y, w, h, nombre_icono, titulo, color, detalle="", punteado="", fondo="none"):
    """Grupo al estilo AWS: borde de color, ícono en la esquina y título al lado."""
    guion = f' stroke-dasharray="{punteado}"' if punteado else ""
    partes = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fondo}" stroke="{color}" stroke-width="2"{guion}/>',
              icono(nombre_icono, x, y, 32), t(x + 42, y + 21, titulo, 14.5, TINTA, "700")]
    if detalle:
        partes.append(t(x + 42 + len(titulo) * 8.4 + 14, y + 21, detalle, 12.5, GRIS))
    return "".join(partes)


def componente(x, y, w, h, nombre_icono, titulo, sub, detalles, borde=TINTA, tam_icono=40):
    """Tarjeta: ícono oficial, título, subtítulo y viñetas."""
    partes = [caja(x, y, w, h, borde), icono(nombre_icono, x + 12, y + 12, tam_icono),
              t(x + tam_icono + 22, y + 30, titulo, 14.5, TINTA, "700")]
    if sub:
        partes.append(t(x + tam_icono + 22, y + 48, sub, 12, GRIS))
    partes.append(lineas(x + 14, y + tam_icono + 42, detalles, 12.5, TINTA))
    return "".join(partes)


def numero(x, y, n, color=TINTA):
    return (f'<circle cx="{x}" cy="{y}" r="10" fill="{color}"/>'
            + t(x, y + 4, str(n), 11, "#FFFFFF", "700", "middle"))


def flecha(d, color=TINTA, marcador="f-tinta", ancho=2, punteado=""):
    guion = f' stroke-dasharray="{punteado}"' if punteado else ""
    return f'<path d="{d}" stroke="{color}" stroke-width="{ancho}" fill="none"{guion} marker-end="url(#{marcador})"/>'


def generar() -> str:
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="960" viewBox="0 0 1440 960" '
         'font-family="Helvetica, Arial, sans-serif">',
         "<title>Yapa · arquitectura en AWS</title>", "<defs>"]
    for ident, color in (("f-tinta", TINTA), ("f-gh", AZUL_GH), ("f-ok", VERDE)):
        s.append(f'<marker id="{ident}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                 f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>')
    s.append("</defs>")
    s.append('<rect width="1440" height="960" fill="#FFFFFF"/>')
    s.append(t(30, 46, "Yapa · arquitectura en AWS", 26, TINTA, "700"))
    s.append(t(30, 72, "Cómo llega un pedido desde el celular del vecino hasta la base de datos, y cómo llega el código "
                       "desde GitHub al servidor. Íconos oficiales de AWS.", 14, GRIS))

    # --- Usuarios y servicios externos ---
    s.append(t(30, 128, "USUARIOS", 13, GRIS, "700", extra=' letter-spacing="1"'))
    s.append(componente(30, 140, 220, 150, "Res_Mobile-client_48_Light", "Vecinos", "celular o computadora",
                        ["Compran, pagan por Plin", "(simulado) y siguen su", "pedido en 7 pasos."]))
    s.append(componente(30, 306, 220, 206, "Res_Users_48_Light", "Equipo Yapa", "una cuenta por rol",
                        ["• Administrador", "• Compras · Armado", "• Atención · Portería", "• Transportista",
                         "• Proveedor aliado", "Todos usan la misma web."]))
    s.append(t(30, 552, "SERVICIOS EXTERNOS", 13, GRIS, "700", extra=' letter-spacing="1"'))
    s.append(caja(30, 564, 220, 96, VERDE, grosor=2))
    s.append(icono("Res_SSL-padlock_48_Light", 42, 576, 40))
    s.append(t(92, 596, "Let's Encrypt", 14.5, TINTA, "700"))
    s.append(lineas(92, 616, ["certificado HTTPS gratis,", "se renueva solo"], 12.5, GRIS))
    s.append(caja(30, 676, 220, 96, "#AAB7B8", punteado="6 5"))
    s.append(icono("Res_Email_48_Light", 42, 688, 40))
    s.append(t(92, 708, "Opcionales", 14.5, GRIS, "700"))
    s.append(lineas(92, 728, ["correo SMTP y Google;", "apagados en la demo"], 12.5, GRIS))

    # --- AWS Cloud ---
    s.append(grupo(290, 108, 770, 830, "AWS-Cloud-logo_32", "AWS Cloud", TINTA,
                   "cuenta estudiantil UTEC · USD 100 de crédito"))
    s.append(caja(320, 160, 340, 100, MORADO, "#F7F3FF", 2))
    s.append(icono("Arch_Amazon-Route-53_48", 334, 174, 48))
    s.append(t(394, 186, "Amazon Route 53", 15, TINTA, "700"))
    s.append(icono("Res_Amazon-Route-53-Hosted-Zone_48", 394, 196, 22))
    s.append(t(422, 212, "zona hospedada holayapa.app", 12.5, GRIS))
    s.append(t(394, 232, "A: holayapa.app y www → 18.225.85.8", 12.5, GRIS))
    s.append(t(394, 250, "servicio global · ≈ USD 0,50/mes", 12, GRIS_CLARO))

    # --- Región ---
    s.append(grupo(320, 282, 710, 626, "Region_32", "Región us-east-2 (Ohio)", VERDE_AZULADO,
                   "la única que permite la cuenta estudiantil", punteado="8 6"))
    s.append(caja(340, 326, 300, 44, NARANJA, "#FFF7ED", 1.5, 22))
    s.append(icono("Res_Amazon-EC2_Elastic-IP-Address_48", 348, 331, 34))
    s.append(t(390, 353, "IP fija 18.225.85.8 (incluida)", 13, TINTA, "700"))
    s.append(caja(656, 326, 354, 44, "#DD344C", "#FDF1F2", 1.5, 22))
    s.append(icono("Res_Firewall_48_Light", 664, 331, 34))
    s.append(t(706, 353, "Firewall: solo 22 (SSH), 80 y 443", 13, TINTA, "700"))

    # --- Instancia Lightsail ---
    s.append(grupo(340, 388, 670, 500, "Arch_Amazon-Lightsail_48", "Amazon Lightsail · instancia \"yapa\"", NARANJA,
                   fondo="#FFFBF5"))
    s.append(t(382, 440, "plan nano · Ubuntu 24.04 · 2 vCPU · 512 MB + 1 GB swap · 20 GB SSD · ≈ USD 5/mes", 12.5, GRIS))
    s.append(componente(362, 460, 200, 176, "Res_Internet_48_Light", "Caddy", "servidor web · :443",
                        ["• HTTPS automático", "• http → https", "• compresión gzip/zstd", "• pasa todo al motor"]))
    s.append(componente(600, 460, 392, 196, "Res_Generic-Application_48_Light", "Motor Yapa (servicio \"yapa\")",
                        "Python 3.12, solo biblioteca estándar · 127.0.0.1:8000",
                        ["• Reglas de los 8 casos de uso (SDD)", "• API JSON /api: sesión, CSRF y permisos por rol",
                         "• Sirve la web React ya construida (dist/)", "• systemd lo reinicia si se cae o se reinicia",
                         "≈ 32 MB de RAM medidos en producción"]))

    # disco
    s.append(caja(362, 688, 630, 182, "#3B48CC", "#F5F6FE", 1.5, 6))
    s.append(icono("Res_Amazon-Elastic-Block-Store_Volume_48", 372, 696, 30))
    s.append(t(410, 716, "Disco SSD del servidor · /opt/yapa", 13.5, TINTA, "700"))
    for i, (nombre, titulo, detalle) in enumerate((
            ("Res_Database_48_Light", "SQLite", ["data/yapa.db", "todo el estado,", "una transacción", "por cambio"]),
            ("Res_Multimedia_48_Light", "Fotos", ["data/fotos/", "bolsas, entregas,", "reclamos y", "dañados"]),
            ("Res_Amazon-Elastic-Block-Store_Snapshot_48", "Respaldos", ["backups/", "copia en cada", "despliegue;",
                                                                         "quedan 14"]),
            ("Res_Folders_48_Light", "Versiones", ["releases/", "las 3 últimas;", "current = la", "que corre"]))):
        x = 374 + i * 154
        s.append(caja(x, 730, 144, 128, "#3B48CC"))
        s.append(icono(nombre, x + 10, 740, 30))
        s.append(t(x + 48, 760, titulo, 13.5, TINTA, "700"))
        s.append(lineas(x + 12, 790, detalle, 12, GRIS, 16))

    # --- GitHub ---
    s.append(t(1090, 128, "CI/CD · GITHUB", 13, GRIS, "700", extra=' letter-spacing="1"'))
    s.append(t(1090, 154, "El equipo hace git push a main", 12.5, GRIS))
    s.append(flecha("M1250 160 v16", AZUL_GH, "f-gh"))
    s.append(componente(1090, 180, 320, 84, "Res_Git-Repository_48_Light", "Repositorio kaloslazo/Yapa",
                        "motor, web, docs y deploy/aws/", []))
    s.append(flecha("M1250 264 v14", AZUL_GH, "f-gh"))
    s.append(caja(1090, 280, 320, 400, AZUL_GH, "#F3F8FF", 2))
    s.append(icono("Res_Gear_48_Light", 1102, 290, 36))
    s.append(t(1148, 314, "GitHub Actions", 15, TINTA, "700"))
    s.append(caja(1106, 340, 140, 88, AZUL_GH))
    s.append(t(1118, 362, "motor", 13.5, TINTA, "700"))
    s.append(lineas(1118, 381, ["671 pruebas", "(Python 3.11)"], 12, GRIS, 17))
    s.append(caja(1254, 340, 140, 88, AZUL_GH))
    s.append(t(1266, 362, "web", 13.5, TINTA, "700"))
    s.append(lineas(1266, 381, ["tipos, 119 pruebas", "y build → paquete"], 12, GRIS, 17))
    s.append('<path d="M1176 428 v14 h148 v-14" stroke="#1F6FEB" stroke-width="2" fill="none"/>')
    s.append(flecha("M1250 442 v24", AZUL_GH, "f-gh"))
    s.append(t(1258, 460, "si las dos pasan", 11.5, AZUL_GH))
    s.append(caja(1106, 470, 288, 196, AZUL_GH))
    s.append(t(1118, 492, "desplegar en AWS", 13.5, TINTA, "700"))
    s.append(t(1118, 510, "solo en push a main", 12, GRIS))
    s.append(lineas(1118, 534, ["1. sube el paquete por SSH (scp)", "2. desplegar.sh en el servidor:"], 12.5, TINTA, 19))
    s.append(lineas(1132, 572, ["respalda la base", "cambia a la versión nueva", "revisa /salud por 40 s",
                                "si falla, vuelve a la anterior"], 12.5, TINTA, 19))
    s.append(t(1118, 656, "secretos: AWS_HOST y AWS_SSH_KEY", 12, GRIS_CLARO))

    # --- Leyenda ---
    s.append(caja(1090, 700, 320, 238, "#AAB7B8", "#F2F3F3", 1.5, 10))
    s.append(t(1106, 726, "Cómo se lee", 14, TINTA, "700"))
    for i, texto in enumerate(("El navegador pregunta la IP a Route 53", "y entra por HTTPS a Caddy",
                               "Caddy pasa la petición al motor", "el motor guarda en SQLite y fotos")):
        s.append(numero(1116, 748 + i * 24, i + 1))
        s.append(t(1134, 752 + i * 24, texto, 12.5, TINTA))
    s.append(flecha("M1106 848 h20", AZUL_GH, "f-gh", 2.5))
    s.append(t(1134, 852, "camino del código (CI/CD)", 12.5, TINTA))
    s.append('<line x1="1106" y1="874" x2="1126" y2="874" stroke="#1E8E3E" stroke-width="2.5" stroke-dasharray="5 4"/>')
    s.append(t(1134, 878, "certificado HTTPS", 12.5, TINTA))
    s.append(t(1106, 904, "Costo total ≈ USD 5,50/mes", 12.5, TINTA, "700"))
    s.append(t(1106, 922, "(≈ 18 meses con USD 100)", 12.5, GRIS))

    # --- Flechas ---
    s.append(flecha("M250 196 C 280 196, 296 210, 318 210"))
    s.append(numero(278, 180, 1))
    s.append(flecha("M250 262 C 300 262, 312 540, 360 548"))
    s.append(flecha("M250 410 C 300 410, 312 556, 360 560"))
    s.append(numero(302, 470, 2))
    s.append(flecha("M562 548 H 598"))
    s.append(numero(580, 530, 3))
    s.append(flecha("M796 656 V 686"))
    s.append(numero(818, 672, 4))
    s.append(flecha("M250 612 C 300 612, 330 610, 360 612", VERDE, "f-ok", punteado="6 5"))
    s.append(flecha("M1106 566 C 1060 566, 1040 610, 1012 610", AZUL_GH, "f-gh", 2.5))
    s.append(t(1064, 556, "SSH", 11, AZUL_GH, "700"))
    s.append("</svg>")
    return "\n".join(s)


if __name__ == "__main__":
    SALIDA.write_text(generar(), encoding="utf-8")
    print(f"listo: {SALIDA}")
    if shutil.which("rsvg-convert"):
        png = SALIDA.with_suffix(".png")
        subprocess.run(["rsvg-convert", "-z", "2", "-o", str(png), str(SALIDA)], check=True)
        print(f"listo: {png}")
