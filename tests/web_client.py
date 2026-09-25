"""Cliente de prueba para la app WSGI: guarda la cookie de sesión y el token CSRF."""

import io
import re
from urllib.parse import urlencode
from wsgiref.util import setup_testing_defaults


class WebClient:
    def __init__(self, app):
        self.app = app
        self.cookie = None
        self.csrf = None

    def request(self, method, path, data=None, with_csrf=True):
        environ = {}
        setup_testing_defaults(environ)
        path, _, query = path.partition("?")
        if data is not None and with_csrf and self.csrf:
            data = dict(data, csrf=self.csrf)
        body = urlencode(data or {}).encode("utf-8")
        environ.update({
            "REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query,
            "CONTENT_TYPE": "application/x-www-form-urlencoded", "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
        })
        if self.cookie:
            environ["HTTP_COOKIE"] = f"yapa_sesion={self.cookie}"
        result = {}

        def start_response(status, headers):
            result["status"] = int(status.split()[0])
            result["headers"] = dict(headers)

        html = b"".join(self.app(environ, start_response)).decode("utf-8")
        cookie = result["headers"].get("Set-Cookie", "")
        match = re.match(r"yapa_sesion=([^;]*)", cookie)
        if match:
            self.cookie = match.group(1) or None
        found = re.search(r'name="csrf" value="([^"]+)"', html)
        if found:
            self.csrf = found.group(1)
        return result["status"], result["headers"], html

    def get(self, path):
        return self.request("GET", path)

    def post(self, path, data=None, with_csrf=True):
        return self.request("POST", path, data or {}, with_csrf)

    def login(self, user, secret, kind="vecino"):
        status, headers, html = self.post("/entrar", {"tipo": kind, "usuario": str(user), "secreto": secret},
                                          with_csrf=False)
        if status == 303:
            self.get("/admin" if kind == "admin" else "/cuenta")  # trae el token CSRF
        return status, headers, html
