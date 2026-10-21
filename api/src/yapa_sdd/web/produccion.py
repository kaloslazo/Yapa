"""Operar Yapa en un servidor (iteración 44). Docs: docs/desarrollo/44-produccion.md."""

from __future__ import annotations

import json
import mimetypes
import threading
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import unquote
from wsgiref.simple_server import WSGIServer

from .. import auth
from ..domain import BusinessRuleError

LOCAL = "127.0.0.1"
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".json": "application/json", ".map": "application/json",
         ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
         ".ico": "image/x-icon", ".woff2": "font/woff2", ".woff": "font/woff", ".txt": "text/plain; charset=utf-8"}
SECURITY = [("X-Content-Type-Options", "nosniff"), ("X-Frame-Options", "DENY"),
            ("Referrer-Policy", "strict-origin-when-cross-origin")]  # S-235


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


def secure_cookie(env) -> bool:
    """S-230."""
    return (env.get("YAPA_PUBLIC_URL") or "").lower().startswith("https://")


def locked(app):
    """S-232: el almacén no es seguro entre hilos; el motor atiende una petición a la vez."""
    lock = threading.Lock()

    def wrapped(environ, start_response):
        with lock:
            return list(app(environ, start_response))
    return wrapped


def _reply(start_response, status, headers, body: bytes = b"", method="GET"):
    start_response(status, [("Content-Length", str(len(body)))] + headers + SECURITY)
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
    cache = "no-cache" if found.name == "index.html" else "public, max-age=3600"
    return _reply(start_response, "200 OK", [("Content-Type", kind), ("Cache-Control", cache)], found.read_bytes(), method)


def compose(api, html, static_dir=None):
    """Un solo punto de entrada: /salud, /api/..., la web construida (S-234) o la página de siempre."""
    root = Path(static_dir).resolve() if static_dir else None

    def app(environ, start_response):
        path = environ.get("PATH_INFO") or "/"
        method = environ.get("REQUEST_METHOD", "GET")
        if path == "/salud" and method in ("GET", "HEAD"):  # S-233
            return _reply(start_response, "200 OK", [("Content-Type", "application/json; charset=utf-8"),
                                                     ("Cache-Control", "no-store")], json.dumps({"ok": True}).encode(), method)
        if path.startswith("/api/") or root is None:
            return (api if path.startswith("/api/") else html)(environ, start_response)
        return _static(root, environ, start_response)
    return app
