"""Iteración 76 · La revisión del detector se guarda en una bolsa ya registrada.

Spec: docs/desarrollo/76-bolsa-con-un-toque-y-detector-a-pedido.md.
"""
from api_client import ApiClient
from test_personal_por_rol import ADMIN, ADMIN_PASS, FRIDAY, PASS, PIN, Base
from test_settlement import CYCLE, NOW

from yapa_sdd import fulfillment, partners
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.web.api import create_api

PACKER_USER = "armado-76"


class BagReviewLaterTests(Base):
    def setUp(self):
        super().setUp()
        partners.create_staff(self.store, PACKER_USER, partners.PACKER, "Rosa Armado", PASS, by=ADMIN, now=NOW)
        self.bag = fulfillment.pack_bag(self.store, self.first.order_id, by=PACKER_USER, photo="fotos/bolsa.jpg",
                                        now=FRIDAY)

    def review(self, rows, number=None):
        return fulfillment.review_bag(self.store, self.first.order_id, number or self.bag.number, rows,
                                      by=PACKER_USER, now=FRIDAY)

    # AR76-B
    def test_ar76_b_the_review_is_saved_on_the_bag_and_replaced(self):
        self.review([{"id": "PAPA-AMARILLA", "unidades": 2}])
        self.assertEqual(self.store.bag_reviews[(self.first.order_id, self.bag.number)],
                         [{"id": "PAPA-AMARILLA", "unidades": 2}])
        self.review([{"id": "PAPA-AMARILLA", "unidades": 3}])
        self.assertEqual(self.store.bag_reviews[(self.first.order_id, self.bag.number)],
                         [{"id": "PAPA-AMARILLA", "unidades": 3}])

    # AR76-C
    def test_ar76_c_an_invalid_review_changes_nothing(self):
        self.review([{"id": "PAPA-AMARILLA", "unidades": 2}])
        for rows in ([], [{"id": "LIMPIATODO-GALON", "unidades": 1}], [{"id": "PAPA-AMARILLA", "unidades": 0}]):
            self.assertRule("INVALID_BAG_REVIEW", self.review, rows)
        self.assertEqual(self.store.bag_reviews[(self.first.order_id, self.bag.number)],
                         [{"id": "PAPA-AMARILLA", "unidades": 2}])

    # AR76-D
    def test_ar76_d_unknown_bag(self):
        self.assertRule("BAG_NOT_FOUND", self.review, [{"id": "PAPA-AMARILLA", "unidades": 1}], 99)

    # AR76-E
    def test_ar76_e_not_after_the_zone_left(self):
        self.store.dispatches[(CYCLE, "Z-JM-01")] = object()
        self.assertRule("ZONE_ALREADY_CLOSED", self.review, [{"id": "PAPA-AMARILLA", "unidades": 1}])


class BagReviewApiTests(Base):
    def setUp(self):
        super().setUp()
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        partners.create_staff(self.store, PACKER_USER, partners.PACKER, "Rosa Armado", PASS, by=ADMIN, now=NOW)
        self.api = create_api(self.store, clock=lambda: FRIDAY, security_clock=lambda: FRIDAY)
        self.packer = ApiClient(self.api)
        self.assertEqual(self.packer.login(PACKER_USER, PASS, "armador")[0], 200)
        self.bag = fulfillment.pack_bag(self.store, self.first.order_id, by=PACKER_USER, photo="fotos/bolsa.jpg",
                                        now=FRIDAY)

    def send(self, client, rows):
        return client.post("/api/admin/bolsas/revision", {"pedido": self.first.order_id, "numero": self.bag.number,
                                                          "revision": '[{"id": "PAPA-AMARILLA", "unidades": 2}]'
                                                          if rows is None else rows})

    # AR76-B: la pantalla de armado devuelve la revisión con la bolsa
    def test_ar76_b_api_saves_and_shows_the_review(self):
        status, data, _ = self.send(self.packer, None)
        self.assertEqual(status, 200)
        self.assertEqual(data["revision"], [{"id": "PAPA-AMARILLA", "unidades": 2}])
        status, board, _ = self.packer.get(f"/api/admin/armado?ciclo={CYCLE}")
        self.assertEqual(status, 200)
        mine = next(o for o in board["pedidos"] if o["id"] == self.first.order_id)
        self.assertEqual(mine["bolsas"][0]["productos"], [{"id": "PAPA-AMARILLA", "unidades": 2}])

    # AR76-C: texto que no es JSON
    def test_ar76_c_api_rejects_a_broken_review(self):
        status, data, _ = self.send(self.packer, "no es json")
        self.assertEqual(data["error"]["codigo"], "INVALID_BAG_REVIEW")

    # AR76-F
    def test_ar76_f_a_neighbor_cannot(self):
        set_pin(self.store, self.first.customer_id, PIN)
        neighbor = ApiClient(self.api)
        self.assertEqual(neighbor.login(self.first.customer_id, PIN)[0], 200)
        self.assertEqual(self.send(neighbor, None)[0], 403)
