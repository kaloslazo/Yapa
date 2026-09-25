from datetime import datetime
from decimal import Decimal as D
import unittest

from test_settlement import CYCLE, Scenario
from web_client import WebClient, fast_hashing

from yapa_sdd import wallet
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import Customer
from yapa_sdd.fulfillment import deliver_zone, pack_bag
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.web.app import create_app


WEDNESDAY = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
FRIDAY = datetime(2026, 9, 18, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 9, 0, tzinfo=LIMA)
SUNDAY = datetime(2026, 9, 20, 8, 0, tzinfo=LIMA)
PIN = "482915"
ADMIN = "admin-yapa"
ADMIN_PASS = "yapa-admin-2026"
LAT, LON = -12.0850, -77.0350
M100 = 0.0009  # ~100 m de latitud


def north(meters):
    return LAT + M100 * meters / 100


class WebOperationBase(unittest.TestCase):
    """Criterios de la iteración 12 (docs/desarrollo/12-web-operacion.md)."""

    def setUp(self):
        fast_hashing(self)
        self.s = Scenario()
        self.store = self.s.store
        self.orders = self.s.orders("Z-JM-01", 8)  # clientes 1001..1008, pedidos 1..8
        for customer_id in (1001, 1002):
            set_pin(self.store, customer_id, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.app = create_app(self.store, clock=lambda: self.now)
        self.at(WEDNESDAY)

    def at(self, moment):
        """Mueve la hora del servidor. La sesión dura 8 h (S-69): el admin vuelve a entrar."""
        self.now = moment
        self.admin = WebClient(self.app)
        self.admin.login(ADMIN, ADMIN_PASS, kind="admin")

    def neighbor(self, customer_id, lat=None, lon=LON, zone_id="Z-LINCE-01"):
        if customer_id not in self.store.customers:
            self.store.add_customer(Customer(customer_id, f"Vecino {customer_id}", zone_id, lat=lat,
                                             lon=lon if lat is not None else None))
            set_pin(self.store, customer_id, PIN)
        client = WebClient(self.app)
        client.login(customer_id, PIN)
        return client

    def create_zone(self, client, name="Torre Sol", lat=LAT, district="Lince"):
        return client.post("/zona/crear", {"nombre": name, "distrito": district, "lat": str(lat), "lon": str(LON)})

    def pack_all(self, orders=None):
        for order in orders or self.orders:
            pack_bag(self.store, order.order_id, by=ADMIN, photo="fotos/bolsa.jpg", now=FRIDAY)

    def delivered_and_settled(self):
        self.pack_all()
        deliver_zone(self.store, CYCLE, "Z-JM-01", by=ADMIN, photo="fotos/entrega.jpg", received_by="Sr. Ramos",
                     now=SATURDAY)
        settle_cycle(self.store, CYCLE, at=SATURDAY)
        self.at(SUNDAY)

    def claim(self, client, articulo="1:CEBOLLA-ROJA", cantidad="1", motivo="DANADO", foto="fotos/cebolla.jpg"):
        return client.post("/reclamos", {"articulo": articulo, "cantidad": cantidad, "motivo": motivo, "foto": foto})


class NeighborZoneTests(WebOperationBase):
    # OA-01
    def test_oa01_create_zone(self):
        client = self.neighbor(3001, lat=LAT)
        status, _, _ = self.create_zone(client)
        self.assertEqual(status, 200)
        zone = self.store.zones["Z-001"]
        self.assertEqual(zone.admin_id, 3001)
        self.assertEqual(self.store.customers[3001].zone_id, "Z-001")
        status, _, html = client.get("/zona")
        self.assertEqual(status, 200)
        self.assertIn("Torre Sol", html)
        self.assertIn("Falta quien reciba", html)
        other = self.neighbor(3002, lat=north(100))
        status, _, html = self.create_zone(other, name="Otra", district="Miraflores")
        self.assertEqual(status, 422)
        self.assertIn("DISTRICT_NOT_IN_PILOT", html)

    # OA-02
    def test_oa02_activate_zone(self):
        client = self.neighbor(3001, lat=LAT)
        self.create_zone(client)
        status, _, _ = client.post("/zona/activar", {"zona": "Z-001", "tipo": "PORTERIA", "contacto": "Sr. Ramos"})
        self.assertEqual(status, 200)
        self.assertTrue(self.store.zones["Z-001"].reception_accepted)
        self.assertIn("Activa", client.get("/zona")[2])
        intruder = self.neighbor(3002, lat=north(100))
        status, _, html = intruder.post("/zona/activar", {"zona": "Z-001", "tipo": "ADMIN", "contacto": "Yo"})
        self.assertEqual(status, 422)
        self.assertIn("NOT_ZONE_ADMIN", html)
        self.assertEqual(self.store.zones["Z-001"].reception_contact, "Sr. Ramos")

    # OA-03
    def test_oa03_join_zone(self):
        self.create_zone(self.neighbor(3001, lat=LAT))
        near = self.neighbor(3002, lat=north(100))
        status, _, _ = near.post("/zona/unirse", {"zona": "Z-001"})
        self.assertEqual(status, 200)
        self.assertEqual(self.store.customers[3002].zone_id, "Z-001")
        far = self.neighbor(3003, lat=north(400))
        status, _, html = far.post("/zona/unirse", {"zona": "Z-001"})
        self.assertEqual(status, 422)
        self.assertIn("OUTSIDE_ZONE_RADIUS", html)
        status, _, html = near.post("/zona/unirse", {"zona": "Z-LINCE-01"})
        self.assertEqual(status, 422)
        self.assertIn("LOCATION_REQUIRED", html)
        self.assertEqual(self.store.customers[3002].zone_id, "Z-001")

    # OA-04
    def test_oa04_merge_leave_and_transfer(self):
        first = self.neighbor(3001, lat=LAT)
        self.create_zone(first)
        second = self.neighbor(3003, lat=north(300))
        self.create_zone(second, name="Torre Luna", lat=north(300))
        status, _, _ = first.post("/zona/unir", {"zona": "Z-001", "destino": "Z-002"})
        self.assertEqual(status, 200)
        status, _, html = second.get("/zona")
        self.assertIn("Z-001", html)
        self.assertIn('action="/zona/aceptar"', html)
        status, _, _ = second.post("/zona/aceptar", {"solicitud": "1"})
        self.assertEqual(status, 200)
        self.assertEqual(self.store.zones["Z-001"].group_id, "G-Z-002")
        self.assertEqual(self.store.zones["Z-002"].group_id, "G-Z-002")
        status, _, _ = first.post("/zona/separar", {"zona": "Z-001"})
        self.assertEqual(status, 200)
        self.assertEqual(self.store.zones["Z-001"].group_id, "G-Z-001")
        status, _, html = first.post("/zona/unir", {"zona": "Z-001", "destino": "Z-LINCE-01"})
        self.assertEqual(status, 422)
        self.assertIn("LOCATION_REQUIRED", html)
        self.neighbor(3002, lat=north(100)).post("/zona/unirse", {"zona": "Z-001"})
        status, _, _ = first.post("/zona/transferir", {"zona": "Z-001", "nuevo": "3002"})
        self.assertEqual(status, 200)
        self.assertEqual(self.store.zones["Z-001"].admin_id, 3002)

    # OA-05
    def test_oa05_malformed_zone_data(self):
        client = self.neighbor(3001, lat=LAT)
        for lat in ("abc", "nan"):
            with self.subTest(lat=lat):
                status, _, html = client.post("/zona/crear", {"nombre": "X", "distrito": "Lince", "lat": lat,
                                                              "lon": str(LON)})
                self.assertEqual(status, 422)
                self.assertIn("INVALID_INPUT", html)
        self.assertNotIn("Z-001", self.store.zones)
        self.create_zone(client)
        status, _, html = client.post("/zona/transferir", {"zona": "Z-001", "nuevo": "abc"})
        self.assertEqual(status, 422)
        self.assertIn("INVALID_INPUT", html)


class NeighborMoneyAndClaimTests(WebOperationBase):
    # OA-06
    def test_oa06_withdrawal_request(self):
        wallet.credit(self.store, 1001, D("20.00"), "ABONO_LIQUIDACION", WEDNESDAY)
        client = self.neighbor(1001)
        status, _, _ = client.post("/cuenta/devolucion", {"monto": "12.50"})
        self.assertEqual(status, 200)
        html = client.get("/cuenta")[2]
        self.assertIn("Saldo: S/ 7.50", html)
        self.assertIn("S/ 12.50", html)
        for amount, code in (("30", "INSUFFICIENT_BALANCE"), ("0", "INVALID_AMOUNT"), ("abc", "INVALID_INPUT"),
                             ("0.001", "INVALID_INPUT")):
            with self.subTest(amount=amount):
                status, _, html = client.post("/cuenta/devolucion", {"monto": amount})
                self.assertEqual(status, 422)
                self.assertIn(code, html)
        self.assertEqual(wallet.balance(self.store, 1001), D("7.50"))

    # OA-07
    def test_oa07_file_claim(self):
        self.delivered_and_settled()
        client = self.neighbor(1001)
        status, _, html = client.get("/reclamos")
        self.assertEqual(status, 200)
        self.assertIn("Cebolla roja", html)
        self.assertIn('value="1:CEBOLLA-ROJA"', html)
        status, _, _ = self.claim(client)
        self.assertEqual(status, 200)
        claim = self.store.claims[1]
        self.assertEqual((claim.customer_id, claim.status, claim.quantity), (1001, "PENDIENTE", D("1")))
        self.assertIn("CEBOLLA-ROJA", client.get("/reclamos")[2])
        other = self.neighbor(1002)
        status, _, html = self.claim(other)
        self.assertEqual(status, 422)
        self.assertIn("ORDER_NOT_FOUND", html)
        status, _, html = self.claim(client, articulo="xx")
        self.assertEqual(status, 422)
        self.assertIn("INVALID_INPUT", html)
        self.assertEqual(len(self.store.claims), 1)


class AdminOperationTests(WebOperationBase):
    # OA-08
    def test_oa08_packing(self):
        status, _, html = self.admin.post("/admin/bolsa", {"pedido": "1", "foto": "fotos/p1-b1.jpg"})
        self.assertEqual(status, 422)
        self.assertIn("CYCLE_STILL_OPEN", html)
        self.at(FRIDAY)
        status, _, html = self.admin.get("/admin/armado")
        self.assertEqual(status, 200)
        for order in self.orders:
            self.assertIn(f"Pedido {order.order_id}", html)
        status, _, _ = self.admin.post("/admin/bolsa", {"pedido": "1", "foto": "fotos/p1-b1.jpg"})
        self.assertEqual(status, 200)
        bag = self.store.bags[1][0]
        self.assertEqual((bag.number, bag.photo, bag.packed_by), (1, "fotos/p1-b1.jpg", ADMIN))
        self.assertIn("fotos/p1-b1.jpg", self.admin.get("/admin/armado")[2])
        status, _, html = self.admin.post("/admin/bolsa", {"pedido": "1", "foto": "  "})
        self.assertEqual(status, 422)
        self.assertIn("PHOTO_REQUIRED", html)

    # OA-09
    def test_oa09_delivery(self):
        self.pack_all(self.orders[:7])
        self.at(SATURDAY)
        data = {"ciclo": CYCLE, "zona": "Z-JM-01", "foto": "fotos/entrega.jpg", "recibe": "Sr. Ramos"}
        status, _, html = self.admin.post("/admin/entrega", data)
        self.assertEqual(status, 422)
        self.assertIn("ORDERS_NOT_PACKED", html)
        self.admin.post("/admin/bolsa", {"pedido": "8", "foto": "fotos/p8.jpg"})
        status, _, _ = self.admin.post("/admin/entrega", data)
        self.assertEqual(status, 200)
        delivery = self.store.deliveries[(CYCLE, "Z-JM-01")]
        self.assertEqual(delivery.order_ids, tuple(o.order_id for o in self.orders))
        self.assertEqual(delivery.received_by, "Sr. Ramos")
        self.assertIn("Entregada", self.admin.get("/admin/armado")[2])

    # OA-10
    def test_oa10_review_claims(self):
        self.delivered_and_settled()
        client = self.neighbor(1001)
        self.claim(client)
        self.claim(client, articulo="1:PAPA-BLANCA", motivo="FALTANTE", foto="fotos/papa.jpg")
        status, _, html = self.admin.get("/admin/reclamos")
        self.assertEqual(status, 200)
        self.assertIn("fotos/cebolla.jpg", html)
        before = wallet.balance(self.store, 1001)
        status, _, _ = self.admin.post("/admin/reclamos/revisar", {"reclamo": "1", "decision": "aprobar"})
        self.assertEqual(status, 200)
        self.assertEqual(self.store.claims[1].status, "APROBADO")
        self.assertEqual(self.store.claims[1].refund_amount, D("2.02"))
        self.assertEqual(wallet.balance(self.store, 1001), before + D("2.02"))
        status, _, html = self.admin.post("/admin/reclamos/revisar", {"reclamo": "1", "decision": "aprobar"})
        self.assertEqual(status, 422)
        self.assertIn("CLAIM_ALREADY_REVIEWED", html)
        status, _, _ = self.admin.post("/admin/reclamos/revisar", {"reclamo": "2", "decision": "rechazar"})
        self.assertEqual(status, 200)
        self.assertEqual(self.store.claims[2].status, "RECHAZADO")
        self.assertEqual(wallet.balance(self.store, 1001), before + D("2.02"))

    # OA-11
    def test_oa11_buffer(self):
        status, _, html = self.admin.post("/admin/colchon/agregar", {"producto": "LIMPIATODO-GALON", "cantidad": "10"})
        self.assertEqual(status, 200)
        html = self.admin.get("/admin/colchon")[2]
        self.assertIn("S/ 79.00", html)
        self.assertIn("S/ 500.00", html)
        status, _, html = self.admin.post("/admin/colchon/agregar", {"producto": "PAPA-AMARILLA", "cantidad": "1"})
        self.assertEqual(status, 422)
        self.assertIn("PERISHABLE_NOT_ALLOWED", html)
        status, _, html = self.admin.post("/admin/colchon/agregar", {"producto": "LIMPIATODO-GALON", "cantidad": "60"})
        self.assertEqual(status, 422)
        self.assertIn("BUFFER_LIMIT_EXCEEDED", html)
        status, _, _ = self.admin.post("/admin/colchon/usar", {"producto": "LIMPIATODO-GALON", "cantidad": "4"})
        self.assertEqual(status, 200)
        stock = self.store.buffer["LIMPIATODO-GALON"]
        self.assertEqual((stock.quantity, stock.value), (D("6"), D("47.40")))
        self.assertIn("S/ 47.40", self.admin.get("/admin/colchon")[2])

    # OA-12
    def test_oa12_metrics_dashboard(self):
        settle_cycle(self.store, CYCLE, at=SATURDAY)
        self.at(SATURDAY)
        status, _, html = self.admin.get("/admin/metricas?ciclo=2026-W38")
        self.assertEqual(status, 200)
        self.assertIn("S/ 5.64", html)
        self.assertIn("S/ 26.88", html)
        self.assertIn("CYCLE_NOT_SETTLED", html)
        status, _, html = self.admin.get("/admin/metricas?ciclo=2026-W39")
        self.assertEqual(status, 422)
        self.assertIn("CYCLE_NOT_SETTLED", html)


class CrossCuttingTests(WebOperationBase):
    # OA-13
    def test_oa13_access(self):
        status, headers, _ = WebClient(self.app).get("/zona")
        self.assertEqual(status, 303)
        self.assertEqual(headers["Location"], "/entrar")
        neighbor = self.neighbor(1001)
        self.assertEqual(neighbor.get("/admin/armado")[0], 403)
        self.assertEqual(neighbor.post("/admin/colchon/agregar", {"producto": "LIMPIATODO-GALON", "cantidad": "1"})[0],
                         403)
        self.assertEqual(self.admin.get("/zona")[0], 403)
        self.delivered_and_settled()
        neighbor = self.neighbor(1001)
        status, _, _ = neighbor.post("/reclamos", {"articulo": "1:CEBOLLA-ROJA", "cantidad": "1", "motivo": "DANADO",
                                                   "foto": "f.jpg"}, with_csrf=False)
        self.assertEqual(status, 403)
        self.assertEqual(self.store.claims, {})
        self.assertEqual(self.store.buffer, {})

    # OA-14
    def test_oa14_routes_and_escaping(self):
        self.assertEqual(self.admin.get("/admin/no-existe")[0], 404)
        client = self.neighbor(3001, lat=LAT)
        self.assertEqual(client.get("/zona/crear")[0], 405)
        self.create_zone(client, name="<script>alert(1)</script>")
        html = client.get("/zona")[2]
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.at(FRIDAY)
        self.admin.post("/admin/bolsa", {"pedido": "1", "foto": "javascript:alert(1)"})
        html = self.admin.get("/admin/armado")[2]
        self.assertIn("javascript:alert(1)", html)
        self.assertNotIn('href="javascript:', html)

    # OA-15
    def test_oa15_mobile_viewport(self):
        neighbor = self.neighbor(1001)
        pages = [neighbor.get("/zona"), neighbor.get("/reclamos"), self.admin.get("/admin/armado"),
                 self.admin.get("/admin/reclamos"), self.admin.get("/admin/colchon")]
        settle_cycle(self.store, CYCLE, at=SATURDAY)
        pages.append(self.admin.get("/admin/metricas?ciclo=2026-W38"))
        for status, _, html in pages:
            with self.subTest(status=status):
                self.assertEqual(status, 200)
                self.assertIn('<meta name="viewport"', html)


if __name__ == "__main__":
    unittest.main()
