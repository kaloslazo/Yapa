"""Iteración 74: el recorrido por calles del orden que eligió el reparto (OSRM, solo cuando se pide).

No decide entregas ni cambia el orden propuesto: solo dibuja el camino y da distancia y tiempo sin tráfico.
"""
import json
import math
import os
import threading
import time
import urllib.request
from collections import OrderedDict
from urllib.parse import urlsplit

from .domain import BusinessRuleError

DEFAULT_URL = "https://router.project-osrm.org"  # servidor de demostración (S-366): en producción, otro servicio
MAX_STOPS = 25
MAX_BYTES = 2_000_000
CACHE_SECONDS = 600
CACHE_SIZE = 64

_cache: OrderedDict = OrderedDict()
_lock = threading.Lock()
_last_attempt = 0.0


def clear_cache() -> None:
    global _last_attempt
    with _lock:
        _cache.clear()
        _last_attempt = 0.0


def fetch_route(url: str) -> dict:
    """La llamada al servicio de rutas; las pruebas la reemplazan para no salir a internet."""
    request = urllib.request.Request(url, headers={"User-Agent": "Yapa-academico/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=7) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("respuesta demasiado grande")
    return json.loads(raw)


def _is_coordinate(point) -> bool:
    """(lon, lat) con números finitos dentro del rango del mapa."""
    if not isinstance(point, (list, tuple)) or len(point) != 2:
        return False
    if not all(type(x) in (int, float) and math.isfinite(x) for x in point):
        return False
    return abs(point[0]) <= 180 and abs(point[1]) <= 90


def _is_measure(value) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _routing_url() -> str:
    base = os.environ.get("YAPA_ROUTING_URL", DEFAULT_URL).rstrip("/")
    parts = urlsplit(base)
    if parts.scheme not in ("https", "http") or not parts.netloc:
        raise BusinessRuleError("ROUTE_UNAVAILABLE", "El servicio de rutas no está configurado correctamente.")
    return base


def _ask_service(base: str, points) -> dict:
    """RP74-2 y RP74-3: una sola respuesta válida o ROUTE_UNAVAILABLE; nunca una recta disfrazada de calle."""
    coordinates = ";".join(f"{lon:.6f},{lat:.6f}" for lon, lat in points)
    try:
        data = fetch_route(f"{base}/route/v1/driving/{coordinates}?overview=full&geometries=geojson&steps=false")
        if data.get("code") != "Ok":
            raise ValueError("sin ruta")
        route = data["routes"][0]
        geometry = route["geometry"]["coordinates"]
        if not isinstance(geometry, list) or not 2 <= len(geometry) <= 10_000:
            raise ValueError("geometría inválida")
        if not all(_is_coordinate(p) for p in geometry):
            raise ValueError("geometría inválida")
        if not _is_measure(route["distance"]) or not _is_measure(route["duration"]):
            raise ValueError("métricas inválidas")
    except Exception as error:
        raise BusinessRuleError("ROUTE_UNAVAILABLE", "No pudimos trazar por calles. Conservamos el orden y los "
                                "enlaces de navegación; reintenta después.") from error
    return {"distancia_m": route["distance"], "duracion_s": route["duration"], "coordenadas": geometry,
            "fuente": "OSRM",
            "aviso": "Recorrido por calles del orden elegido; tiempo estimado sin tráfico en tiempo real."}


def street_route(points) -> dict:
    """RP74-1..RP74-3: entre 2 y 25 paradas; caché de 10 minutos y como máximo una consulta por segundo."""
    global _last_attempt
    if not isinstance(points, (list, tuple)) or not 2 <= len(points) <= MAX_STOPS:
        raise BusinessRuleError("INVALID_ROUTE", "Elige entre 2 y 25 paradas con coordenadas válidas.")
    if not all(_is_coordinate(p) for p in points):
        raise BusinessRuleError("INVALID_ROUTE", "Elige entre 2 y 25 paradas con coordenadas válidas.")
    base = _routing_url()
    key = (base, tuple(tuple(p) for p in points))
    now = time.monotonic()
    if not _lock.acquire(blocking=False):
        raise BusinessRuleError("ROUTE_BUSY", "Hay una ruta en cálculo. Intenta de nuevo en unos segundos.")
    try:
        cached = _cache.get(key)
        if cached and now - cached[0] < CACHE_SECONDS:
            return cached[1]
        if now - _last_attempt < 1:
            raise BusinessRuleError("ROUTE_BUSY", "Espera un segundo antes de calcular otra ruta.")
        _last_attempt = now
        result = _ask_service(base, points)
        _cache[key] = (now, result)
        _cache.move_to_end(key)
        while len(_cache) > CACHE_SIZE:
            _cache.popitem(last=False)
        return result
    finally:
        _lock.release()
