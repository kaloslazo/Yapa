"""Iteración 41: verificar el token de "Entrar con Google" (docs/desarrollo/41-entrar-con-google.md).

Dependencia opcional (S-214): `pip install PyJWT cryptography`. Solo se importa cuando se verifica un token,
así que el resto del motor sigue usando solo la biblioteca estándar.
"""

from __future__ import annotations

import json
import time
import urllib.request

CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
ISSUERS = ("https://accounts.google.com", "accounts.google.com")
CERTS_CACHE_SECONDS = 3600  # S-214
LEEWAY_SECONDS = 30  # GO-05


class GoogleError(Exception):
    """El token no sirve (o no se pudo comprobar)."""


class GoogleVerifier:
    def __init__(self, client_id: str, jwks_provider=None):
        self.client_id = client_id
        self._jwks_provider = jwks_provider or self._download_certs
        self._cached: tuple[float, dict] | None = None

    def _download_certs(self) -> dict:
        if self._cached and time.monotonic() - self._cached[0] < CERTS_CACHE_SECONDS:
            return self._cached[1]
        try:
            with urllib.request.urlopen(CERTS_URL, timeout=10) as response:
                certs = json.load(response)
        except (OSError, ValueError) as error:
            raise GoogleError("no se pudieron pedir las llaves de Google") from error
        self._cached = (time.monotonic(), certs)
        return certs

    def verify(self, credential) -> dict:
        """GO-05: devuelve sub, email y email_verified, o GoogleError ante cualquier problema."""
        import jwt

        try:
            header = jwt.get_unverified_header(credential)
            if header.get("alg") != "RS256":  # nada de "none" ni HS256
                raise GoogleError("algoritmo no permitido")
            jwk = next((k for k in self._jwks_provider().get("keys", []) if k.get("kid") == header.get("kid")), None)
            if jwk is None:
                raise GoogleError("llave desconocida")
            claims = jwt.decode(credential, jwt.PyJWK(jwk).key, algorithms=["RS256"], audience=self.client_id,
                                leeway=LEEWAY_SECONDS, options={"require": ["exp", "iat", "sub", "iss", "aud"]})
        except GoogleError:
            raise
        except (jwt.PyJWTError, KeyError, ValueError, TypeError, AttributeError) as error:
            raise GoogleError(str(error)) from error
        if claims.get("iss") not in ISSUERS or claims.get("email_verified") not in (True, "true"):
            raise GoogleError("emisor o correo no verificado")
        return {"sub": str(claims["sub"]), "email": str(claims.get("email", "")).strip().lower(), "email_verified": True}


def google_from_env(env=None):
    """S-210: sin YAPA_GOOGLE_CLIENT_ID no hay "Entrar con Google"."""
    import os

    client_id = (os.environ if env is None else env).get("YAPA_GOOGLE_CLIENT_ID", "").strip()
    return GoogleVerifier(client_id) if client_id else None
