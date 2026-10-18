"""Iteración 37: análisis por zona y propuestas (docs/desarrollo/37-analisis-zonas-propuestas.md)."""

from datetime import datetime
from decimal import Decimal as D
import unittest

from api_client import ApiClient
from web_client import fast_hashing

from yapa_sdd.audit import money_balance
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.demo import DEMO_NOW, demo_store
from yapa_sdd.domain import Customer, Zone
from yapa_sdd.order_registration import register_order, verify_payment
from yapa_sdd.seed import pilot_store
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.web.api import create_api

PREVIOUS = datetime(2026, 9, 9, 10, 0, tzinfo=LIMA)  # miércoles de la 2026-W37
WEDNESDAY = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)  # miércoles de la 2026-W38, ciclo abierto
SATURDAY = datetime(2026, 9, 19, 10, 0, tzinfo=LIMA)
BASKET = [("PAPA-AMARILLA", "5"), ("PAPA-BLANCA", "10"), ("CEBOLLA-ROJA", "10")]  # S/ 61.00
PIN, ADMIN, ADMIN_PASS = "482915", "admin-yapa", "yapa-admin-2026"
ALAMOS, PALMERAS, ARENALES, MIRAFLORES = "Z-LINCE-01", "Z-LINCE-02", "Z-LINCE-03", "Z-MIRA-01"


class AnalysisBase(unittest.TestCase):
    now = WEDNESDAY

    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        self.store.zones[ARENALES] = Zone(ARENALES, "Edificio Arenales", "Lince", "G-LINCE-3", D("40"),
                                          lat=-12.0852, lon=-77.0375)
        set_pin(self.store, 101, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.clock = [self.now]
        self.api = create_api(self.store, clock=lambda: self.clock[0])

    def neighbors(self, zone, first, count):
        ids = list(range(first, first + count))
        for customer_id in ids:
            self.store.add_customer(Customer(customer_id, f"Vecino {customer_id}", zone))
        return ids

    def order(self, customer_id, verified=True, now=None):
        now = now or self.now
        placed = register_order(self.store, customer_id=customer_id, lines=BASKET, payment_method="YAPE",
                                operation_code=f"OP-{now:%V}-{customer_id}", amount="61.00", now=now)
        if verified:
            verify_payment(self.store, placed.order_id, now=now)
        return placed

    def admin(self):
        client = ApiClient(self.api)
        client.login(ADMIN, ADMIN_PASS, "admin")
        return client

    def analysis(self, query="?ciclo=2026-W38"):
        status, body, _ = self.admin().get(f"/api/admin/analisis{query}")
        self.assertEqual(status, 200, body)
        return body

    def zone(self, body, zone_id):
        return next(z for z in body["zonas"] if z["id"] == zone_id)

    def types(self, body):
        return [p["tipo"] for p in body["propuestas"]]


class ZoneAnalysisTests(AnalysisBase):
    def setUp(self):
        super().setUp()
        self.alamos = self.neighbors(ALAMOS, 901, 7)
        self.arenales = self.neighbors(ARENALES, 911, 5)
        for customer_id in self.alamos[:5]:
            self.order(customer_id, verified=customer_id < 905)  # 5 pidieron, 4 pagaron verificado
        for customer_id in self.arenales[:4]:
            self.order(customer_id)  # 4 pidieron y pagaron

    # AN-A
    def test_an_a_solo_el_admin(self):
        status, body, _ = ApiClient(self.api).get("/api/admin/analisis")
        self.assertEqual((status, body["error"]["codigo"]), (401, "LOGIN_REQUIRED"))
        neighbor = ApiClient(self.api)
        neighbor.login(101, PIN, "vecino")
        status, body, _ = neighbor.get("/api/admin/analisis")
        self.assertEqual((status, body["error"]["codigo"]), (403, "FORBIDDEN"))

    # AN-B
    def test_an_b_datos_de_la_zona(self):
        zone = self.zone(self.analysis(), ALAMOS)
        self.assertEqual((zone["vecinos"], zone["pedidos"], zone["verificados"], zone["adopcion"]), (7, 5, 4, 71))

    # AN-C
    def test_an_c_margen_sin_liquidar_es_nulo(self):
        self.assertIsNone(self.zone(self.analysis(), ALAMOS)["margen"])

    # AN-D
    def test_an_d_union_posible(self):
        pair = next(u for u in self.analysis()["uniones"] if {u["a"], u["b"]} == {ARENALES, ALAMOS})
        self.assertEqual((pair["distancia_m"], pair["motivo"]), (391, ""))

    # AN-E
    def test_an_e_union_bloqueada_por_ciclo_cerrado(self):
        self.clock[0] = SATURDAY
        pair = next(u for u in self.analysis()["uniones"] if {u["a"], u["b"]} == {ARENALES, ALAMOS})
        self.assertEqual(pair["motivo"], "CYCLE_CLOSED")

    # AN-F
    def test_an_f_las_zonas_lejanas_no_aparecen(self):
        for union in self.analysis()["uniones"]:
            self.assertNotIn(MIRAFLORES, (union["a"], union["b"]))

    # AN-G
    def test_an_g_propone_unir_si_juntas_llegan(self):
        proposal = next(p for p in self.analysis()["propuestas"] if p["tipo"] == "UNIR")
        self.assertEqual(proposal["datos"]["verificados_juntos"], 8)
        self.assertIn(ARENALES, proposal["zonas"])
        self.assertIn(ALAMOS, proposal["zonas"])

    # AN-I
    def test_an_i_propone_recordar(self):
        proposal = next(p for p in self.analysis()["propuestas"] if p["tipo"] == "RECORDAR" and p["zonas"] == [ARENALES])
        self.assertEqual(proposal["datos"]["sin_pedir"], 1)

    # AN-J
    def test_an_j_propone_invitar_a_una_zona_chica(self):
        proposal = next(p for p in self.analysis()["propuestas"] if p["tipo"] == "INVITAR" and p["zonas"] == [ARENALES])
        self.assertEqual(proposal["datos"]["vecinos"], 5)

    # AN-M
    def test_an_m_las_que_ayudan_a_llegar_van_primero(self):
        order = self.types(self.analysis())
        self.assertEqual(order, sorted(order, key=["UNIR", "RECORDAR", "INVITAR", "REVISAR_COSTO", "REACTIVAR"].index))

    # AN-P
    def test_an_p_consultar_no_cambia_nada(self):
        groups = {z.zone_id: z.group_id for z in self.store.zones.values()}
        before = money_balance(self.store)
        self.analysis()
        self.analysis()
        self.assertEqual({z.zone_id: z.group_id for z in self.store.zones.values()}, groups)
        self.assertEqual(money_balance(self.store), before)
        self.assertEqual(self.store.merge_requests, {})


class FewOrdersTests(AnalysisBase):
    # AN-H
    def test_an_h_no_propone_unir_si_juntas_no_llegan(self):
        for customer_id in self.neighbors(ALAMOS, 901, 4)[:2]:
            self.order(customer_id)
        for customer_id in self.neighbors(ARENALES, 911, 4)[:3]:
            self.order(customer_id)
        self.assertNotIn("UNIR", self.types(self.analysis()))

    # AN-N
    def test_an_n_sin_pedidos_responde_con_ceros(self):
        body = self.analysis()
        self.assertEqual(self.zone(body, ALAMOS)["pedidos"], 0)
        self.assertEqual(self.zone(body, ALAMOS)["adopcion"], 0)
        self.assertNotIn("REVISAR_COSTO", self.types(body))
        self.assertNotIn("REACTIVAR", self.types(body))

    # AN-O
    def test_an_o_ciclo_invalido(self):
        status, body, _ = self.admin().get("/api/admin/analisis?ciclo=hola")
        self.assertEqual((status, body["error"]["codigo"]), (422, "INVALID_INPUT"))


class SettledWeekTests(AnalysisBase):
    def setUp(self):
        super().setUp()
        self.jm = self.neighbors("Z-JM-01", 801, 8)
        for customer_id in self.jm:
            self.order(customer_id, now=PREVIOUS)
        self.store.zones["Z-JM-01"].stop_cost = D("400")  # la parada cuesta más de lo que deja la zona
        settle_cycle(self.store, "2026-W37")

    # AN-K
    def test_an_k_propone_revisar_el_costo(self):
        body = self.analysis("?ciclo=2026-W37")
        proposal = next(p for p in body["propuestas"] if p["tipo"] == "REVISAR_COSTO")
        self.assertEqual(proposal["zonas"], ["Z-JM-01"])
        self.assertLess(D(proposal["datos"]["margen"]), 0)
        self.assertLess(D(self.zone(body, "Z-JM-01")["margen"]), 0)

    # AN-L
    def test_an_l_propone_reactivar_a_quienes_recibieron_y_no_piden(self):
        for customer_id in self.jm[:5]:
            self.order(customer_id)  # 5 ya piden esta semana
        proposal = next(p for p in self.analysis()["propuestas"] if p["tipo"] == "REACTIVAR")
        self.assertEqual(proposal["datos"]["vecinos"], 3)

    # AN-M
    def test_an_m_unir_sale_antes_que_reactivar(self):
        for customer_id in self.neighbors(ALAMOS, 901, 4):
            self.order(customer_id)
        for customer_id in self.neighbors(ARENALES, 911, 4):
            self.order(customer_id)
        order = self.types(self.analysis())
        self.assertIn("REACTIVAR", order)
        self.assertLess(order.index("UNIR"), order.index("REACTIVAR"))


class DemoTests(unittest.TestCase):
    # AN-Q
    def test_an_q_la_demo_tiene_dos_admins_de_zona_cercanos(self):
        from yapa_sdd.zones import distance_m
        store = demo_store()
        arenales, alamos = store.zones[ARENALES], store.zones[ALAMOS]
        self.assertEqual(arenales.admin_id, 116)
        self.assertEqual(round(distance_m(arenales.lat, arenales.lon, alamos.lat, alamos.lon)), 391)
        self.assertEqual(store.customers[116].zone_id, ARENALES)
        in_week = [o for o in store.orders_in_cycle("2026-W40")]
        self.assertEqual(len(in_week), 7)  # la zona nueva no suma pedidos a la semana vivida
        self.assertEqual(DEMO_NOW.isoweekday(), 3)


if __name__ == "__main__":
    unittest.main()
