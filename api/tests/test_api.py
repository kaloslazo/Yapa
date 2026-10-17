"""Iteración 27: API JSON para el frontend (docs/desarrollo/27-api-json.md)."""

from datetime import datetime
import re
import unittest

from api_client import ApiClient
from web_client import fast_hashing

from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import Customer
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api


WEDNESDAY = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 10, 0, tzinfo=LIMA)
PIN, ADMIN, ADMIN_PASS = "482915", "admin-yapa", "yapa-admin-2026"
BASKET = {"PAPA-AMARILLA": "5", "PAPA-BLANCA": "10", "CEBOLLA-ROJA": "10"}  # S/ 61.00
LAT, LON = -12.0850, -77.0350
M100 = 0.0009  # ~100 m de latitud


class ApiSpecTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        set_pin(self.store, 101, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.now = WEDNESDAY
        self.api = create_api(self.store, clock=lambda: self.now)

    def client(self, user=101, secret=PIN, kind="vecino"):
        client = ApiClient(self.api)
        client.login(user, secret, kind)
        return client

    def admin(self):
        return self.client(ADMIN, ADMIN_PASS, "admin")

    def neighbor(self, customer_id, zone="Z-JM-01", lat=None, lon=None):
        self.store.add_customer(Customer(customer_id, f"Vecino {customer_id}", zone, lat=lat, lon=lon))
        set_pin(self.store, customer_id, PIN)
        return self.client(customer_id)

    # API-A
    def test_api_a_public_data(self):
        public = ApiClient(self.api)
        status, catalog, _ = public.get("/api/catalogo")
        self.assertEqual(status, 200)
        products = {p["id"]: p for p in catalog["productos"]}
        self.assertEqual(products["PAPA-AMARILLA"]["precio_max"], "4.03")
        self.assertEqual(products["PAPA-AMARILLA"]["siguiente_tramo"], {"desde": "100", "precio": "3.79"})
        self.assertNotIn("PLATANO-SEDA", products)
        status, state, _ = public.get("/api/estado")
        self.assertEqual((state["ciclo"], state["abierto"]), ("2026-W38", True))
        zones = public.get("/api/zonas")[1]["zonas"]
        self.assertIn("Z-LINCE-01", [z["id"] for z in zones])

    # API-B
    def test_api_b_session(self):
        client = ApiClient(self.api)
        status, data, headers = client.login(101, PIN)
        self.assertEqual(status, 200)
        self.assertEqual((data["rol"], data["nombre"]), ("vecino", "Ana Torres"))
        self.assertTrue(data["csrf"])
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        status, data, _ = ApiClient(self.api).login(101, "000000")
        self.assertEqual((status, data["error"]["codigo"]), (422, "INVALID_CREDENTIALS"))
        self.assertEqual(client.request("DELETE", "/api/sesion")[0], 200)
        self.assertEqual(client.get("/api/mis-pedidos")[0], 401)

    # API-C
    def test_api_c_csrf_required(self):
        client = self.client()
        status, _, _ = client.post("/api/pedidos", {"lineas": BASKET, "metodo": "YAPE"}, with_csrf=False)
        self.assertEqual(status, 403)

    # API-D
    def test_api_d_buy(self):
        client = self.client()
        status, quote, _ = client.post("/api/cotizar", {"lineas": BASKET})
        self.assertEqual((status, quote["total"]), (200, "61.00"))
        self.assertIn("Papa amarilla", [line["nombre"] for line in quote["lineas"]])
        status, order, _ = client.post("/api/pedidos", {"lineas": BASKET, "metodo": "YAPE"})
        self.assertEqual(status, 201)
        self.assertEqual((order["id"], order["a_yapear"]), (1, "61.00"))
        self.assertRegex(order["codigo_pago"], r"^YP-2026W38-101-[A-Z0-9]{4}$")
        status, data, _ = self.neighbor(105, "Z-LINCE-01").post("/api/cotizar", {"lineas": {"AJO": "1"}})
        self.assertEqual((status, data["error"]["codigo"]), (422, "SUBTOTAL_BELOW_MINIMUM"))

    # API-E
    def test_api_e_my_orders_and_cancel(self):
        client = self.client()
        client.post("/api/pedidos", {"lineas": BASKET, "metodo": "YAPE"})
        orders = client.get("/api/mis-pedidos")[1]["pedidos"]
        self.assertEqual((orders[0]["id"], orders[0]["estado"], orders[0]["cancelable"]), (1, "REGISTRADO", True))
        self.admin().post("/api/admin/pedidos/1/verificar")
        status, _, _ = client.post("/api/pedidos/1/cancelar", {"destino": "SALDO"})
        self.assertEqual(status, 200)
        self.assertEqual(client.get("/api/mis-pedidos")[1]["pedidos"][0]["estado"], "CANCELADO_POR_CLIENTE")
        self.assertEqual(client.get("/api/sesion")[1]["saldo"], "61.00")

    # API-F
    def test_api_f_admin(self):
        client = self.client()
        client.post("/api/pedidos", {"lineas": BASKET, "metodo": "YAPE"})
        self.assertEqual(client.get("/api/admin/resumen")[0], 403)
        admin = self.admin()
        summary = admin.get("/api/admin/resumen")[1]
        self.assertEqual([o["id"] for o in summary["por_verificar"]], [1])
        self.assertEqual(admin.post("/api/admin/pedidos/1/verificar")[0], 200)
        self.assertEqual(admin.get("/api/admin/resumen")[1]["por_verificar"], [])

    # API-G
    def test_api_g_whole_week(self):
        for customer_id in range(801, 809):
            self.neighbor(customer_id).post("/api/pedidos", {"lineas": BASKET, "metodo": "YAPE"})
        admin = self.admin()
        for order_id in range(1, 9):
            admin.post(f"/api/admin/pedidos/{order_id}/verificar")
        self.now = SATURDAY
        admin = self.admin()
        for order_id in range(1, 9):
            self.assertEqual(admin.post("/api/admin/bolsas", {"pedido": order_id, "foto": f"b{order_id}.jpg"})[0], 200)
        status, _, _ = admin.post("/api/admin/entregas", {"ciclo": "2026-W38", "zona": "Z-JM-01",
                                                          "foto": "entrega.jpg", "recibe": "Sr. Ramos"})
        self.assertEqual(status, 200)
        status, result, _ = admin.post("/api/admin/ciclos/2026-W38/liquidar")
        self.assertEqual(status, 200)
        self.assertEqual({o["estado"] for o in result["pedidos"]}, {"LIQUIDADO"})
        self.assertEqual(admin.get("/api/admin/conciliacion")[1]["diferencia"], "0.00")

    # API-H
    def test_api_h_zone(self):
        first = self.neighbor(201, "Z-LINCE-01", LAT, LON)
        status, zone, _ = first.post("/api/zonas", {"nombre": "Torre Sol", "distrito": "Lince", "lat": LAT, "lon": LON})
        self.assertEqual(status, 201)
        self.assertEqual(first.get("/api/sesion")[1]["rol"], "admin_zona")
        self.assertEqual(first.get("/api/mi-zona")[1]["zona"]["id"], zone["id"])
        second = self.neighbor(202, "Z-LINCE-01", LAT + M100, LON)
        self.assertEqual(second.post(f"/api/zonas/{zone['id']}/unirme")[0], 200)
        status, _, _ = first.post(f"/api/zonas/{zone['id']}/transferir", {"nuevo": 202})
        self.assertEqual(status, 200)
        self.assertEqual(first.get("/api/sesion")[1]["rol"], "vecino")
        self.assertEqual(second.get("/api/sesion")[1]["rol"], "admin_zona")

    # API-I
    def test_api_i_errors(self):
        status, data, _ = ApiClient(self.api).get("/api/no-existe")
        self.assertEqual(status, 404)
        self.assertIn("error", data)
        status, data, _ = self.client().post("/api/pedidos/99/cancelar", {"destino": "SALDO"})
        self.assertEqual(status, 422)
        self.assertEqual(data["error"]["codigo"], "ORDER_NOT_FOUND")
        self.assertTrue(data["error"]["mensaje"])

    # FE-F (iteración 29)
    def test_fe_f_location_through_api(self):
        client = self.neighbor(203, "Z-LINCE-01")
        status, data, _ = client.post("/api/ubicacion", {"lat": "abc", "lon": LON})
        self.assertEqual((status, data["error"]["codigo"]), (422, "INVALID_LOCATION"))
        self.assertEqual(client.post("/api/ubicacion", {"lat": LAT, "lon": LON})[0], 200)
        status, _, _ = client.post("/api/zonas", {"nombre": "Torre Luna", "distrito": "Lince", "lat": LAT, "lon": LON})
        self.assertEqual(status, 201)


if __name__ == "__main__":
    unittest.main()
