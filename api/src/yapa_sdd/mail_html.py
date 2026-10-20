"""Diseño de los correos (iteración 43). Docs: docs/desarrollo/43-correo-html.md.

Arma el HTML a partir del mismo texto del correo (S-225). Solo texto y color, sin imágenes ni scripts (S-223).
"""

from __future__ import annotations

import re
from html import escape

INK, ACCENT, GREEN, GREEN_SOFT = "#263430", "#be4d36", "#3b7158", "#dceadf"
PAGE, CANVAS, LINE, COPY, MUTED = "#f7f1e9", "#fffdf9", "#e4ddd2", "#47544e", "#526059"
FONT = "'Helvetica Neue', Helvetica, Arial, sans-serif"

CODE_LINE = re.compile(r"^Tu código es (\d{4,8})\.\s*(.*)$", re.S)
OPT_OUT = "Si no quieres recibir"


def _paragraph(lines: list[str], color: str = COPY, size: int = 16) -> str:
    text = "<br>".join(escape(line) for line in lines)
    return f'<p style="margin:0 0 16px;font-size:{size}px;line-height:1.55;color:{color};">{text}</p>'


def _code_box(code: str, note: str) -> str:
    caption = _paragraph([note], MUTED, 14) if note else ""
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:8px 0 20px;"><tr>'
            f'<td align="center" style="padding:22px 12px;border:2px dashed {GREEN};border-radius:12px;background:#ffffff;">'
            f'<div data-role="code" style="font-family:Consolas,Menlo,monospace;font-size:34px;font-weight:700;'
            f'letter-spacing:8px;color:{GREEN};">{escape(code)}</div></td></tr></table>{caption}')


def _button(url: str) -> str:
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 24px;"><tr>'
            f'<td bgcolor="{ACCENT}" style="border-radius:8px;">'
            f'<a href="{escape(url, quote=True)}" style="display:inline-block;padding:14px 28px;font-size:16px;'
            f'font-weight:700;color:#ffffff;text-decoration:none;">Abrir Yapa</a></td></tr></table>')


def _valid_url(url: str) -> bool:
    return url.lower().startswith(("http://", "https://"))


def render(subject: str, body: str, app_url: str = "") -> str:
    """HT-02 a HT-06: el HTML del correo. Todo texto que viene de datos se escapa."""
    blocks = [block.strip() for block in body.replace("\r\n", "\n").split("\n\n") if block.strip()]
    if blocks and blocks[-1] == "Yapa":
        blocks.pop()  # la marca ya va en el encabezado

    content, footer, preview = [], [], ""
    for block in blocks:
        match = CODE_LINE.match(block)
        if match:
            rest = match.group(2).split("\n")
            content.append(_code_box(match.group(1), rest[0]))
            lines = [line for line in rest[1:] if line]
            if lines:
                content.append(_paragraph(lines, MUTED, 14))
            continue
        lines = [line for line in block.split("\n") if not line.startswith(OPT_OUT)]
        footer += [line for line in block.split("\n") if line.startswith(OPT_OUT)]
        if lines:
            content.append(_paragraph(lines))
            if not preview and not lines[0].startswith("Hola"):
                preview = lines[0][:110]

    if app_url and _valid_url(app_url):
        content.append(_button(app_url))
    footer_text = "".join(f"{escape(line)}<br>" for line in footer)

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light"><title>{escape(subject)}</title></head>
<body style="margin:0;padding:0;background:{PAGE};font-family:{FONT};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{escape(preview)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAGE};"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:{CANVAS};border:1px solid {LINE};border-radius:14px;overflow:hidden;">
<tr><td style="padding:20px 28px;background:{INK};"><span style="font-size:26px;font-weight:800;letter-spacing:.5px;color:#ffffff;">Yapa</span><span style="display:inline-block;margin-left:10px;width:8px;height:8px;border-radius:4px;background:{ACCENT};"></span></td></tr>
<tr><td style="padding:28px 28px 8px;"><h1 style="margin:0 0 18px;font-size:22px;line-height:1.3;color:{INK};">{escape(subject)}</h1>
{"".join(content)}</td></tr>
<tr><td style="padding:16px 28px 24px;border-top:1px solid {LINE};font-size:13px;line-height:1.5;color:{MUTED};">{footer_text}Yapa · compras grupales de vecinos</td></tr>
</table></td></tr></table></body></html>
"""
