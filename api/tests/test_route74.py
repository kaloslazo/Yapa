"""Iteración 74: recorrido por calles para el reparto. Spec: docs/desarrollo/74-ruta-por-calles.md.

El servicio de rutas se reemplaza en todas las pruebas: nunca salen a internet.
"""
import json
import unittest
from unittest.mock import patch

from api_client import ApiClient
from test_settlement import CYCLE, NOW, Scenario
from web_client import fast_hashing
from yapa_sdd import street_routing
from yapa_sdd.auth import set_admin_password
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.web.api import create_api

TWO_STOPS = [(-77, -12), (-77.01, -12.01)]
OSRM_OK = {"code": "Ok", "routes": [{"distance": 1200, "duration": 240,
                                     "geometry": {"type": "LineString", "coordinates": [[-77, -12], [-77.01, -12.01]]}}]}


class RouteByStreetTests(unittest.TestCase):
    def setUp(self):
        street_routing.clear_cache()

    def test_rp74_a_geometry_distance_and_cache(self):
        with patch.object(street_routing, "fetch_route", return_value=OSRM_OK) as fetch:
            first = street_routing.street_route(TWO_STOPS)
            again = street_routing.street_route(TWO_STOPS)
        self.assertEqual(first["distancia_m"], 1200)
        self.assertEqual(first["coordenadas"], OSRM_OK["routes"][0]["geometry"]["coordinates"])
        self.assertEqual(first, again)
        fetch.assert_called_once()  # la segunda sale de la caché

    def test_rp74_b_invalid_stop_or_service_down_never_returns_a_fake_line(self):
        with self.assertRaises(BusinessRuleError) as e:
            street_routing.street_route([(999, 0), (0, 0)])
        self.assertEqual(e.exception.code, "INVALID_ROUTE")
        with patch.object(street_routing, "fetch_route", side_effect=TimeoutError):
            with self.assertRaises(BusinessRuleError) as e:
                street_routing.street_route(TWO_STOPS)
        self.assertEqual(e.exception.code, "ROUTE_UNAVAILABLE")

    def test_rp74_c_malformed_geometry_is_rejected(self):
        broken = {"code": "Ok", "routes": [{"distance": 1, "duration": 1,
                                            "geometry": {"coordinates": [[float("nan"), 0], [0, 0]]}}]}
        with patch.object(street_routing, "fetch_route", return_value=broken):
            with self.assertRaises(BusinessRuleError) as e:
                street_routing.street_route(TWO_STOPS)
        self.assertEqual(e.exception.code, "ROUTE_UNAVAILABLE")

    def test_rp74_d_api_uses_only_pending_attended_zones_and_needs_a_session(self):
        fast_hashing(self)
        s = Scenario()
        s.orders("Z-JM-01", 8)
        s.orders("Z-LINCE-01", 8)
        set_admin_password(s.store, "admin-yapa", "yapa-admin-2026")
        app = create_api(s.store, clock=lambda: NOW)
        client = ApiClient(app)
        client.login("admin-yapa", "yapa-admin-2026", "admin")
        payload = {"ciclo": CYCLE, "zonas": json.dumps(["Z-JM-01", "Z-LINCE-01"])}
        with patch("yapa_sdd.web.api.street_route", return_value={"distancia_m": 100}) as routing:
            self.assertEqual(client.post("/api/reparto/ruta", payload)[0], 200)
        routing.assert_called_once_with([(s.store.zones[z].lon, s.store.zones[z].lat) for z in ["Z-JM-01", "Z-LINCE-01"]])
        payload["zonas"] = json.dumps(["Z-JM-01", "DESCONOCIDA"])
        self.assertEqual(client.post("/api/reparto/ruta", payload)[1]["error"]["codigo"], "INVALID_ROUTE")
        self.assertEqual(ApiClient(app).post("/api/reparto/ruta", payload)[0], 401)


if __name__ == "__main__":
    unittest.main()
