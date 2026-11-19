"""Iteración 78: leer fotos con Amazon Bedrock (cuenta estudiantil UTEC), sin dependencias.

La API Converse de `bedrock-runtime` con la firma de AWS (SigV4) hecha con la biblioteca estándar.
Spec: docs/desarrollo/78-fotos-con-bedrock.md.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import parse_qsl, quote, urlsplit

DEFAULT_REGION = "us-east-2"  # S-382: la región del servidor
DEFAULT_MODEL = "us.amazon.nova-pro-v1:0"  # S-382: Claude Haiku 4.5 cuando la cuenta envíe el formulario de Anthropic
DEFAULT_MAX_TOKENS = 2000  # S-385: cotizaciones; las bolsas piden 400
FORMATS = {"image/jpeg": "jpeg", "image/png": "png", "image/webp": "webp"}
STS_BODY = b"Action=GetCallerIdentity&Version=2011-06-15"

_accounts: dict[str, bool] = {}  # S-384: clave -> si es de la cuenta esperada (se pregunta una vez)


def forget_accounts() -> None:
    _accounts.clear()


def _hmac(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def signed_headers(method: str, url: str, body: bytes, *, key_id: str, secret: str, region: str, service: str,
                   now: datetime, content_type: str, token: str = "") -> dict[str, str]:
    """BR-02: cabeceras firmadas con AWS Signature Version 4 (las del ejemplo publicado por AWS, BR-D)."""
    parts = urlsplit(url)
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    day = stamp[:8]
    headers = {"content-type": content_type, "host": parts.netloc, "x-amz-date": stamp}
    if token:
        headers["x-amz-security-token"] = token
    names = sorted(headers)
    canonical_headers = "".join(f"{name}:{headers[name].strip()}\n" for name in names)
    signed = ";".join(names)
    query = "&".join(f"{quote(k, safe='~')}={quote(v, safe='~')}"
                     for k, v in sorted(parse_qsl(parts.query, keep_blank_values=True)))
    # fuera de S3, la ruta ya codificada se vuelve a codificar (el ":" del modelo queda %253A)
    canonical = "\n".join([method, quote(parts.path or "/", safe="/~"), query, canonical_headers, signed,
                           hashlib.sha256(body).hexdigest()])
    scope = f"{day}/{region}/{service}/aws4_request"
    to_sign = "\n".join(["AWS4-HMAC-SHA256", stamp, scope, hashlib.sha256(canonical.encode("utf-8")).hexdigest()])
    key = _hmac(("AWS4" + secret).encode("utf-8"), day)
    for part in (region, service, "aws4_request"):
        key = _hmac(key, part)
    signature = hmac.new(key, to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    result = {"Content-Type": content_type, "X-Amz-Date": stamp, "Accept": "application/json",
              "Authorization": f"AWS4-HMAC-SHA256 Credential={key_id}/{scope}, SignedHeaders={signed}, Signature={signature}"}
    if token:
        result["X-Amz-Security-Token"] = token
    return result


def _check_account(provider, post: Callable, timeout: float) -> None:
    """S-384: si se pidió una cuenta, STS dice de cuál son las credenciales; otra cuenta apaga Bedrock."""
    if not provider.account:
        return
    if provider.key not in _accounts:
        url = f"https://sts.{provider.region}.amazonaws.com/"
        headers = signed_headers("POST", url, STS_BODY, key_id=provider.key, secret=provider.secret,
                                 region=provider.region, service="sts", now=datetime.now(timezone.utc),
                                 content_type="application/x-www-form-urlencoded; charset=utf-8", token=provider.token)
        answer = post(url, headers, STS_BODY, timeout)
        found = answer["GetCallerIdentityResponse"]["GetCallerIdentityResult"]["Account"]
        _accounts[provider.key] = found == provider.account
    if not _accounts[provider.key]:
        raise ValueError("las credenciales de Bedrock no son de la cuenta esperada")


def converse(provider, system: str, user: str, image: tuple[str, bytes], max_tokens: int | None,
             post: Callable, timeout: float) -> str:
    """BR-02: una foto y su texto a Converse; devuelve el texto de la respuesta."""
    _check_account(provider, post, timeout)
    kind = FORMATS.get(image[0])
    if kind is None:
        raise ValueError("formato de foto que Bedrock no lee")
    body = json.dumps({
        "system": [{"text": system}],
        "messages": [{"role": "user", "content": [
            {"image": {"format": kind, "source": {"bytes": base64.b64encode(image[1]).decode("ascii")}}},
            {"text": user}]}],
        "inferenceConfig": {"maxTokens": max_tokens or DEFAULT_MAX_TOKENS, "temperature": 0.2},
    }).encode("utf-8")
    url = (f"https://bedrock-runtime.{provider.region}.amazonaws.com/model/"
           f"{quote(provider.model, safe='')}/converse")
    headers = signed_headers("POST", url, body, key_id=provider.key, secret=provider.secret, region=provider.region,
                             service="bedrock", now=datetime.now(timezone.utc), content_type="application/json",
                             token=provider.token)
    answer = post(url, headers, body, timeout)
    return next(block["text"] for block in answer["output"]["message"]["content"] if "text" in block)
