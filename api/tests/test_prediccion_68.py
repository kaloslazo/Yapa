"""Iteración 68 · Predicción de demanda. Spec: docs/desarrollo/68-prediccion-de-demanda.md."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal as D
import unittest

from api_client import ApiClient
from test_personal_por_rol import ADMIN, ADMIN_PASS, FRIDAY, PIN, Base
from test_settlement import CYCLE

from yapa_sdd import forecast
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA, add_weeks
from yapa_sdd.domain import Order, OrderLine
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api

TARGET = "2026-W40"
OPEN = datetime(2026, 9, 30, 10, 0, tzinfo=LIMA)  # miércoles de la W40, antes del cierre
CLOSED = datetime(2026, 10, 2, 10, 0, tzinfo=LIMA)  # viernes de la W40


def week(back: int) -> str:
    return add_weeks(TARGET, -back)


def product(result: dict, product_id: str) -> dict:
    return next(p for p in result["productos"] if p["id"] == product_id)


class ForecastTests(unittest.TestCase):
    def setUp(self):
        self.store = pilot_store()
        for back, kg in zip((4, 3, 2, 1), ("10", "12", "14", "16")):
            self.store.demand_history[(week(back), "Z-LINCE-01", "PAPA-AMARILLA")] = D(kg)
        self.store.demand_history[(week(1), "Z-JM-01", "PAPA-AMARILLA")] = D("5")

    def order(self, cycle: str, zone: str, product_id: str, quantity: str, status="REGISTRADO") -> None:
        line = OrderLine(product_id, D(quantity), D("1"))
        self.store.save_new_order(Order(0, cycle, 101, zone, [line], D("0"), D("0"), D("0"), [], status=status))

    # PD-A
    def test_pd_a_trend_per_zone_and_average_for_short_history(self):
        result = forecast.forecast(self.store, TARGET, OPEN)
        papa = product(result, "PAPA-AMARILLA")
        self.assertEqual(papa["estimado"], D("23"))
        self.assertEqual(papa["metodo"], "tendencia")
        zones = {z["id"]: {p["id"]: p["estimado"] for p in z["productos"]} for z in result["zonas"]}
        self.assertEqual(zones["Z-LINCE-01"]["PAPA-AMARILLA"], D("18"))
        self.assertEqual(zones["Z-JM-01"]["PAPA-AMARILLA"], D("5"))

    # PD-B
    def test_pd_b_history_is_eight_weeks_oldest_first(self):
        papa = product(forecast.forecast(self.store, TARGET, OPEN), "PAPA-AMARILLA")
        self.assertEqual(papa["historia"], [D("0")] * 4 + [D("10"), D("12"), D("14"), D("21")])

    # PD-C
    def test_pd_c_a_zone_that_starts_late_does_not_count_zeros(self):
        result = forecast.forecast(self.store, TARGET, OPEN)
        lince = next(z for z in result["zonas"] if z["id"] == "Z-LINCE-01")
        self.assertEqual(lince["productos"][0]["estimado"], D("18"))
        self.assertNotIn("CEBOLLA-ROJA", [p["id"] for p in lince["productos"]])

    # PD-D
    def test_pd_d_cancelled_orders_are_not_demand(self):
        self.order(week(1), "Z-LINCE-01", "PAPA-AMARILLA", "100", status="CANCELADO_POR_CLIENTE")
        self.assertEqual(product(forecast.forecast(self.store, TARGET, OPEN), "PAPA-AMARILLA")["estimado"], D("23"))

    # PD-E
    def test_pd_e_flags_when_the_estimate_exceeds_the_catalog_maximum(self):
        self.store.products["PAPA-AMARILLA"] = replace(self.store.products["PAPA-AMARILLA"], max_available=D("20"))
        papa = product(forecast.forecast(self.store, TARGET, OPEN), "PAPA-AMARILLA")
        self.assertTrue(papa["supera_maximo"])
        self.assertEqual(papa["maximo"], D("20"))

    # PD-F
    def test_pd_f_rounds_up_to_the_product_step(self):
        for back, units in zip((2, 1), ("2", "2.6")):
            self.store.demand_history[(week(back), "Z-LINCE-02", "LIMPIATODO-GALON")] = D(units)
        galon = product(forecast.forecast(self.store, TARGET, OPEN), "LIMPIATODO-GALON")
        self.assertEqual(galon["estimado"], D("3"))
        self.assertEqual(galon["metodo"], "promedio")

    # PD-G
    def test_pd_g_never_negative(self):
        for back, kg in zip((3, 2, 1), ("9", "6", "3")):
            self.store.demand_history[(week(back), "Z-LINCE-02", "CEBOLLA-ROJA")] = D(kg)
        for back, kg in zip((3, 2, 1), ("9", "5", "1")):
            self.store.demand_history[(week(back), "Z-JM-01", "CEBOLLA-ROJA")] = D(kg)
        self.assertEqual(product(forecast.forecast(self.store, TARGET, OPEN), "CEBOLLA-ROJA")["estimado"], D("0"))

    # PD-H
    def test_pd_h_mean_error_only_when_the_week_closed(self):
        self.order(TARGET, "Z-LINCE-01", "PAPA-AMARILLA", "20")
        self.assertIsNone(forecast.forecast(self.store, TARGET, OPEN)["error_medio"])
        closed = forecast.forecast(self.store, TARGET, CLOSED)
        self.assertEqual(product(closed, "PAPA-AMARILLA")["pedido"], D("20"))
        self.assertEqual(closed["error_medio"], D("0.15"))

    # PD-I
    def test_pd_i_imported_history_adds_to_orders(self):
        self.order(week(1), "Z-JM-01", "PAPA-AMARILLA", "7")
        papa = product(forecast.forecast(self.store, TARGET, OPEN), "PAPA-AMARILLA")
        self.assertEqual(papa["historia"][-1], D("28"))
        self.assertEqual(papa["estimado"], D("30"))

    def test_without_history_there_is_no_estimate(self):
        limon = product(forecast.forecast(self.store, TARGET, OPEN), "LIMON")
        self.assertEqual((limon["estimado"], limon["metodo"]), (D("0"), "sin_historia"))


class ForecastApiTests(Base):
    def setUp(self):
        super().setUp()
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.api = create_api(self.store, clock=lambda: FRIDAY, security_clock=lambda: FRIDAY)

    # PD-01
    def test_pd_01_purchases_bring_the_forecast(self):
        admin = ApiClient(self.api)
        self.assertEqual(admin.login(ADMIN, ADMIN_PASS, "admin")[0], 200)
        status, data, _ = admin.get(f"/api/compras?ciclo={add_weeks(CYCLE, 1)}")
        self.assertEqual(status, 200)
        papa = next(p for p in data["prediccion"]["productos"] if p["id"] == "PAPA-AMARILLA")
        self.assertEqual(set(papa), {"id", "nombre", "unidad", "historia", "estimado", "pedido", "maximo",
                                     "supera_maximo", "metodo"})
        self.assertEqual(papa["historia"][-1], "40")

    # PD-J
    def test_pd_j_a_neighbor_cannot_see_it(self):
        set_pin(self.store, self.first.customer_id, PIN)
        neighbor = ApiClient(self.api)
        self.assertEqual(neighbor.login(self.first.customer_id, PIN)[0], 200)
        self.assertEqual(neighbor.get(f"/api/compras?ciclo={CYCLE}")[0], 403)


if __name__ == "__main__":
    unittest.main()
