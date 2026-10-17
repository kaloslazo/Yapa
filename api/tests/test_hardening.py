from datetime import datetime
from decimal import Decimal as D
import unittest

from test_settlement import CYCLE, Scenario

from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError, Customer
from yapa_sdd.fulfillment import close_cycle
from yapa_sdd.seed import pilot_store
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.wallet import credit, request_withdrawal
from yapa_sdd.zones import (accept_merge, activate_zone, create_zone, join_zone, reject_merge, request_merge,
                            set_location, transfer_admin, withdraw_merge)


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
LAT, LON = -12.0850, -77.0350


class HardeningSpecTests(unittest.TestCase):
    def setUp(self):
        self.store = pilot_store()
        self.next_id = 7000

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def person(self, lat=LAT):
        self.next_id += 1
        self.store.add_customer(Customer(self.next_id, f"Vecino {self.next_id}", "Z-LINCE-01", lat=lat, lon=LON))
        return self.next_id

    def active_zone(self, lat=LAT, name="Zona"):
        admin = self.person(lat=lat)
        zone = create_zone(self.store, admin, name=name, district="Lince", lat=lat, lon=LON, now=NOW)
        activate_zone(self.store, zone.zone_id, admin, reception_kind="PORTERIA", contact="Sr. Ramos")
        return zone, admin

    # HA-01
    def test_ha01_customer_location(self):
        set_location(self.store, 101, -12.0858, -77.0342)
        self.assertEqual((self.store.customers[101].lat, self.store.customers[101].lon), (-12.0858, -77.0342))
        for lat, lon in ((1000, -77.0), (-12.0, -200), (float("nan"), -77.0)):
            with self.subTest(lat=lat, lon=lon):
                self.assertRule("INVALID_LOCATION", set_location, self.store, 101, lat, lon)

    # HA-02
    def test_ha02_zone_coordinates_are_validated(self):
        admin = self.person()
        self.assertRule("INVALID_LOCATION", create_zone, self.store, admin, name="X", district="Lince",
                        lat=95, lon=LON, now=NOW)

    # HA-03
    def test_ha03_admin_must_transfer_before_leaving(self):
        zone_a, admin_a = self.active_zone()
        zone_b, _ = self.active_zone(lat=LAT + 0.0009, name="B")
        self.assertRule("ADMIN_MUST_TRANSFER", join_zone, self.store, admin_a, zone_b.zone_id, now=NOW)
        neighbor = self.person(lat=LAT + 0.0005)
        join_zone(self.store, neighbor, zone_a.zone_id, now=NOW)
        transfer_admin(self.store, zone_a.zone_id, admin_a, neighbor)
        join_zone(self.store, admin_a, zone_b.zone_id, now=NOW)
        self.assertEqual(self.store.customers[admin_a].zone_id, zone_b.zone_id)

    # HA-04
    def test_ha04_merge_requests(self):
        a, admin_a = self.active_zone()
        b, admin_b = self.active_zone(lat=LAT + 0.0036, name="B")
        first = request_merge(self.store, a.zone_id, b.zone_id, admin_a, now=NOW)
        self.assertRule("MERGE_ALREADY_REQUESTED", request_merge, self.store, a.zone_id, b.zone_id, admin_a, now=NOW)
        self.assertRule("NOT_ZONE_ADMIN", reject_merge, self.store, first, admin_a)
        reject_merge(self.store, first, admin_b)
        self.assertRule("MERGE_REQUEST_NOT_FOUND", accept_merge, self.store, first, admin_b, now=NOW)
        second = request_merge(self.store, a.zone_id, b.zone_id, admin_a, now=NOW)
        self.assertRule("NOT_ZONE_ADMIN", withdraw_merge, self.store, second, admin_b)
        withdraw_merge(self.store, second, admin_a)
        self.assertNotIn(second, self.store.merge_requests)

    # HA-05
    def test_ha05_withdrawal_amounts(self):
        credit(self.store, 101, D("20"), "ABONO_LIQUIDACION", NOW)
        for amount in ("0.001", "0", "-5", "abc"):
            with self.subTest(amount=amount):
                self.assertRule("INVALID_AMOUNT", request_withdrawal, self.store, 101, amount, NOW)
        self.assertEqual(request_withdrawal(self.store, 101, "5.50", NOW).amount, D("5.50"))

    # HA-06
    def test_ha06_cycle_id_is_validated(self):
        for cycle in ("abc", "2026-W99", "2026-38"):
            with self.subTest(cycle=cycle):
                self.assertRule("INVALID_CYCLE", settle_cycle, self.store, cycle)
                self.assertRule("INVALID_CYCLE", close_cycle, self.store, cycle)

    # HA-07
    def test_ha07_pilot_zones_have_coordinates(self):
        for zone in self.store.zones.values():
            with self.subTest(zone=zone.zone_id):
                self.assertIsNotNone(zone.lat)
        customer = join_zone(self.store, 105, "Z-LINCE-02", now=NOW)  # 105 vive a menos de 300 m de ese punto
        self.assertEqual(customer.zone_id, "Z-LINCE-02")


if __name__ == "__main__":
    unittest.main()
