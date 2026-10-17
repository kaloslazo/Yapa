"""Cliente de prueba para la API JSON: guarda la cookie de sesión y manda el token CSRF (S-155)."""

import io
import json
import re
from wsgiref.util import setup_testing_defaults


class ApiClient:
    def __init__(self, app):
        self.app = app
        self.cookie = None
        self.csrf = None

    def request(self, method, path, body=None, with_csrf=True):
        environ = {}
        setup_testing_defaults(environ)
        path, _, query = path.partition("?")
        raw = json.dumps(body).encode("utf-8") if body is not None else b""
        environ.update({
            "REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query,
            "CONTENT_TYPE": "application/json", "CONTENT_LENGTH": str(len(raw)),
            "wsgi.input": io.BytesIO(raw),
        })
        if self.cookie:
            environ["HTTP_COOKIE"] = f"yapa_api={self.cookie}"
        if with_csrf and self.csrf:
            environ["HTTP_X_YAPA_CSRF"] = self.csrf
        result = {}

        def start_response(status, headers):
            result["status"] = int(status.split()[0])
            result["headers"] = dict(headers)

        text = b"".join(self.app(environ, start_response)).decode("utf-8")
        match = re.match(r"yapa_api=([^;]*)", result["headers"].get("Set-Cookie", ""))
        if match:
            self.cookie = match.group(1) or None
        data = json.loads(text) if text else None
        return result["status"], data, result["headers"]

    def get(self, path):
        return self.request("GET", path)

    def post(self, path, body=None, with_csrf=True):
        return self.request("POST", path, body or {}, with_csrf)

    def login(self, user, secret, kind="vecino"):
        status, data, headers = self.post("/api/sesion", {"tipo": kind, "usuario": str(user), "secreto": secret},
                                          with_csrf=False)
        if status == 200:
            self.csrf = data["csrf"]
        return status, data, headers
