"""Operar Yapa en un servidor (iteración 44). Docs: docs/desarrollo/44-produccion.md."""

from __future__ import annotations

import io
import json
import mimetypes
import re
import threading
from html import escape
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import unquote
from wsgiref.simple_server import WSGIServer

from .. import auth
from ..domain import BusinessRuleError

LOCAL = "127.0.0.1"
MAX_BODY = 9 * 1024 * 1024  # S-259: la foto de 8 MB (S-151) y el formulario
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".json": "application/json", ".map": "application/json",
         ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
         ".ico": "image/x-icon", ".woff2": "font/woff2", ".woff": "font/woff", ".txt": "text/plain; charset=utf-8"}
INVITE_PATH = re.compile(r"/unete/([\w-]+)/?")
CSP = "; ".join((  # S-269: lo propio, entrar con Google y los mapas de OpenStreetMap
    "default-src 'self'",
    "script-src 'self' https://accounts.google.com/gsi/client",
    "style-src 'self' 'unsafe-inline' https://accounts.google.com/gsi/style",
    "img-src 'self' data: blob: https://tile.openstreetmap.org https://*.googleusercontent.com",
    "font-src 'self' data:",
    "connect-src 'self' https://accounts.google.com/gsi/",
    "frame-src https://accounts.google.com/gsi/",
    "object-src 'none'", "base-uri 'self'", "form-action 'self'", "frame-ancestors 'none'"))
SECURITY = [("X-Content-Type-Options", "nosniff"), ("X-Frame-Options", "DENY"),
            ("Referrer-Policy", "strict-origin-when-cross-origin"), ("Content-Security-Policy", CSP)]  # S-235, S-269
HSTS = ("Strict-Transport-Security", "max-age=31536000")
LOOPBACK = {"127.0.0.1", "::1"}


def client_ip(environ) -> str:
    """SG-08, S-263: la dirección del socket; detrás del proxy local, la última de X-Forwarded-For."""
    remote = environ.get("REMOTE_ADDR") or ""
    forwarded = [part.strip() for part in (environ.get("HTTP_X_FORWARDED_FOR") or "").split(",") if part.strip()]
    return forwarded[-1] if remote in LOOPBACK and forwarded else remote


class ThreadedServer(ThreadingMixIn, WSGIServer):
    """S-232: cada conexión en su hilo, para que un cliente lento no bloquee a los demás."""
    daemon_threads = True


def prepare_server_credentials(store, env) -> None:
    """S-228, S-229: en modo servidor no hay credenciales de demo; el administrador sale del entorno."""
    user, password = (env.get("YAPA_ADMIN_USUARIO") or "").strip(), env.get("YAPA_ADMIN_CLAVE") or ""
    if user and password:
        auth.set_admin_password(store, user, password)
        return
    if any(kind == "admin" for kind, _ in store.credentials):
        return
    raise BusinessRuleError("ADMIN_NOT_CONFIGURED",
                            "Falta el administrador: define YAPA_ADMIN_USUARIO y YAPA_ADMIN_CLAVE para el primer arranque.")


def check_listen(host: str, base) -> None:
    """S-231: un servidor abierto nunca arranca con datos de demo."""
    if host != LOCAL and not base:
        raise BusinessRuleError("UNSAFE_LISTEN", "Escuchar fuera de esta máquina exige --base (nunca con datos de demo).")


SIMULATED_PAYEE = {"numero": "999 000 111", "titular": "Yapa (cuenta simulada, proyecto UTEC)"}  # S-305


def payee(env, demo: bool) -> dict:
    """S-305: el Plin negocios donde paga el vecino. Proyecto académico sin empresa: sin variables, cuenta simulada."""
    number = (env.get("YAPA_PLIN_NUMERO") or "").strip()
    holder = (env.get("YAPA_PLIN_TITULAR") or "").strip()
    if number and holder:
        return {"numero": number, "titular": holder}
    return dict(SIMULATED_PAYEE)


def secure_cookie(env) -> bool:
    """S-230."""
    return (env.get("YAPA_PUBLIC_URL") or "").lower().startswith("https://")


def locked(app):
    """S-232: el almacén no es seguro entre hilos; el motor atiende una petición a la vez.
    SG-01, S-259: el cuerpo se lee antes del cerrojo y con tope, para que un cliente lento o enorme no frene a todos."""
    lock = threading.Lock()

    def wrapped(environ, start_response):
        try:
            length = max(int(environ.get("CONTENT_LENGTH") or 0), 0)
        except ValueError:
            length = 0
        if length > MAX_BODY:
            body = json.dumps({"error": {"codigo": "PAYLOAD_TOO_LARGE", "mensaje": "El envío pesa demasiado. La foto debe pesar menos de 8 MB."}},
                              ensure_ascii=False).encode("utf-8")
            return _reply(start_response, "413 Content Too Large", [("Content-Type", "application/json; charset=utf-8"),
                                                                    ("Connection", "close")] + SECURITY, body)
        environ["wsgi.input"] = io.BytesIO(environ["wsgi.input"].read(length) if length else b"")
        environ["CONTENT_LENGTH"] = str(length)
        with lock:
            return list(app(environ, start_response))
    return wrapped


def _reply(start_response, status, headers, body: bytes = b"", method="GET"):
    start_response(status, [("Content-Length", str(len(body)))] + headers)
    return [] if method == "HEAD" else [body]


def _is_safe(path: str) -> bool:
    """PR-08: nada de salirse de la carpeta (también con %, \\ o bytes nulos)."""
    for text in (path, unquote(path)):
        if "\x00" in text or "\\" in text or ".." in text.split("/"):
            return False
    return True


def _static(root: Path, environ, start_response):
    method, path = environ.get("REQUEST_METHOD", "GET"), environ.get("PATH_INFO") or "/"
    if method not in ("GET", "HEAD"):
        return _reply(start_response, "405 Method Not Allowed", [("Allow", "GET, HEAD")], b"", method)
    if not _is_safe(path):
        return _reply(start_response, "404 Not Found", [("Content-Type", "text/plain; charset=utf-8")], b"No existe.", method)
    candidate = (root / path.lstrip("/")).resolve()
    if candidate != root and candidate.is_relative_to(root) and candidate.is_file():
        found = candidate
    elif "." in path.rsplit("/", 1)[-1]:  # un archivo que no existe no se disfraza de página
        return _reply(start_response, "404 Not Found", [("Content-Type", "text/plain; charset=utf-8")], b"No existe.", method)
    else:
        found = root / "index.html"  # S-234: la web maneja sus propias rutas
    if not found.is_file():
        return _reply(start_response, "404 Not Found", [("Content-Type", "text/plain; charset=utf-8")], b"No existe.", method)
    kind = TYPES.get(found.suffix.lower()) or mimetypes.guess_type(found.name)[0] or "application/octet-stream"
    cache = ("no-cache" if found.name == "index.html" else  # S-251: lo que tiene huella en el nombre no cambia nunca
             "public, max-age=31536000, immutable" if path.startswith("/assets/") else "public, max-age=3600")
    return _reply(start_response, "200 OK", [("Content-Type", kind), ("Cache-Control", cache)], found.read_bytes(), method)


def _invite_html(index: str, data: dict, code: str) -> str:
    """PU-03, S-250: el mismo index.html con el título y la descripción de esta invitación; todo se escapa."""
    first, zone, district = escape(str(data["invita"]), quote=True), escape(str(data["zona"]), quote=True), escape(str(data["distrito"]), quote=True)
    count = int(data["vecinos"])
    title = f"{first} te invita a Yapa"
    description = f"{zone} · {district}: ya hay {count} {'vecino' if count == 1 else 'vecinos'} comprando juntos. Entra con el enlace y queda en la zona de {first}."
    base = re.search(r'property="og:url" content="(https?://[^"/]+)', index)
    url = f"{base.group(1) if base else ''}/unete/{escape(code, quote=True)}"
    for prop, value in (("og:title", title), ("og:description", description), ("og:url", url)):
        index = re.sub(rf'(property="{prop}" content=")[^"]*(")', lambda m, v=value: m.group(1) + v + m.group(2), index)
    return re.sub(r"(<title>)[^<]*(</title>)", lambda m: m.group(1) + title + m.group(2), index)


def compose(api, html, static_dir=None, invite_preview=None, secure=False):
    """Un solo punto de entrada: /salud, /api/..., la web construida (S-234) o la página de siempre.
    SG-14: toda respuesta lleva las cabeceras de seguridad; HSTS solo con https."""
    root = Path(static_dir).resolve() if static_dir else None
    extra = SECURITY + ([HSTS] if secure else [])

    def app(environ, start_response):
        def with_security(status, headers, *rest):
            return start_response(status, list(headers) + extra, *rest)
        return route(environ, with_security)

    def route(environ, start_response):
        path = environ.get("PATH_INFO") or "/"
        method = environ.get("REQUEST_METHOD", "GET")
        if path == "/salud" and method in ("GET", "HEAD"):  # S-233
            return _reply(start_response, "200 OK", [("Content-Type", "application/json; charset=utf-8"),
                                                     ("Cache-Control", "no-store")], json.dumps({"ok": True}).encode(), method)
        if path.startswith("/api/") or root is None:
            return (api if path.startswith("/api/") else html)(environ, start_response)
        invite = INVITE_PATH.fullmatch(path)
        if invite and invite_preview and method in ("GET", "HEAD") and (root / "index.html").is_file():  # S-250
            try:
                page = _invite_html((root / "index.html").read_text(encoding="utf-8"), invite_preview(invite.group(1)), invite.group(1))
            except Exception:  # un enlace que no vale, o cualquier falla, muestra la portada normal
                page = None
            if page:
                return _reply(start_response, "200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Cache-Control", "no-cache")],
                              page.encode("utf-8"), method)
        return _static(root, environ, start_response)
    return app
