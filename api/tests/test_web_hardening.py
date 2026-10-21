from datetime import datetime
from decimal import Decimal as D
import unittest

from test_settlement import CYCLE, Scenario
from web_client import WebClient, fast_hashing

from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.wallet import credit, request_withdrawal
from yapa_sdd.web.app import create_app


WEDNESDAY = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 10, 0, tzinfo=LIMA)
ADMIN, ADMIN_PASS, PIN = "admin-yapa", "yapa-admin-2026", "482915"


class WebHardeningSpecTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.s = Scenario()
        self.store = self.s.store
        self.orders = self.s.orders("Z-JM-01", 8)  # clientes 1001..1008, pedidos 1..8, pagos verificados
        set_pin(self.store, 1001, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.app = create_app(self.store, clock=lambda: self.now)
        self.at(WEDNESDAY)

    def at(self, moment):
        self.now = moment
        self.admin = WebClient(self.app)
        self.admin.login(ADMIN, ADMIN_PASS, kind="admin")

    def pack_all(self):
        for order in self.orders:
            status, _, _ = self.admin.post("/admin/bolsa", {"pedido": str(order.order_id), "foto": "bolsa.jpg"})
            self.assertEqual(status, 200)

    # HA-01 (web)
    def test_ha01_neighbor_registers_location(self):
        neighbor = WebClient(self.app)
        neighbor.login(1001, PIN)
        status, _, _ = neighbor.post("/cuenta/ubicacion", {"lat": "-12.0770", "lon": "-77.0470"})
        self.assertEqual(status, 200)
        self.assertEqual(self.store.customers[1001].lat, -12.0770)
        status, _, html = neighbor.post("/cuenta/ubicacion", {"lat": "1000", "lon": "-77.0470"})
        self.assertEqual(status, 422)
        self.assertIn("INVALID_LOCATION", html)

    # HA-08
    def test_ha08_admin_pays_refund(self):
        credit(self.store, 1001, D("20"), "ABONO_LIQUIDACION", WEDNESDAY)
        refund = request_withdrawal(self.store, 1001, "12.50", WEDNESDAY)
        html = self.admin.get("/admin/devoluciones")[2]
        self.assertIn("12.50", html)
        status, _, _ = self.admin.post("/admin/devoluciones/pagar", {"reembolso": str(refund.refund_id),
                                                                     "codigo": "YP-1234"})
        self.assertEqual(status, 200)
        self.assertEqual(self.store.refunds[refund.refund_id].status, "PAGADO")
        status, _, html = self.admin.post("/admin/devoluciones/pagar", {"reembolso": str(refund.refund_id),
                                                                        "codigo": "YP-1235"})
        self.assertEqual(status, 422)
        self.assertIn("REFUND_ALREADY_PAID", html)

    # HA-09
    def test_ha09_failed_delivery_from_web(self):
        self.at(SATURDAY)
        self.pack_all()
        status, _, _ = self.admin.post("/admin/entrega-fallida", {"ciclo": CYCLE, "zona": "Z-JM-01",
                                                                  "motivo": "NADIE_RECIBE", "foto": "puerta.jpg"})
        self.assertEqual(status, 200)
        self.assertIn((CYCLE, "Z-JM-01"), self.store.failed_deliveries)

    # HA-10
    def test_ha10_settle_from_web_requires_closed_zones(self):
        self.at(SATURDAY)
        status, _, html = self.admin.post("/admin/liquidar", {"ciclo": CYCLE})
        self.assertEqual(status, 422)
        self.assertIn("ZONES_PENDING", html)
        self.pack_all()
        self.admin.post("/admin/entrega", {"ciclo": CYCLE, "zona": "Z-JM-01", "foto": "entrega.jpg",
                                           "recibe": "Sr. Ramos"})
        status, _, html = self.admin.post("/admin/liquidar", {"ciclo": CYCLE})
        self.assertEqual(status, 200)
        self.assertIn("LIQUIDADO", html)

    def test_ha06_web_rejects_invalid_cycle(self):
        status, _, html = self.admin.post("/admin/liquidar", {"ciclo": "abc"})
        self.assertEqual(status, 422)
        self.assertIn("INVALID_CYCLE", html)


if __name__ == "__main__":
    unittest.main()
