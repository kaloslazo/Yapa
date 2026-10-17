from datetime import datetime
from decimal import Decimal
import unittest

from test_settlement import CYCLE, Scenario

from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError, Customer
from yapa_sdd.order_registration import quote_order, register_order
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.zones import (accept_merge, activate_zone, create_zone, distance_m, join_zone, leave_group,
                            request_merge, transfer_admin)


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
THURSDAY = datetime(2026, 9, 17, 10, 0, tzinfo=LIMA)
LAT, LON = -12.0850, -77.0350
M100 = 0.0009  # ~100 m de latitud
LINES = [("PAPA-AMARILLA", "5"), ("LIMPIATODO-GALON", "4")]


def north(meters):
    return LAT + M100 * meters / 100


class ZonesSpecTests(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store
        self.next_id = 3000

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def person(self, lat=LAT, lon=LON, zone_id="Z-LINCE-01"):
        self.next_id += 1
        self.store.add_customer(Customer(self.next_id, f"Vecino {self.next_id}", zone_id, lat=lat, lon=lon))
        return self.next_id

    def active_zone(self, lat=LAT, name="Edificio Los Pinos"):
        admin = self.person(lat=lat)
        zone = create_zone(self.store, admin, name=name, district="Lince", lat=lat, lon=LON, now=NOW)
        activate_zone(self.store, zone.zone_id, admin, reception_kind="PORTERIA", contact="Sr. Ramos")
        return zone, admin

    def order(self, customer_id):
        return register_order(self.store, customer_id=customer_id, lines=LINES, payment_method="YAPE",
                              operation_code=f"Z{customer_id}", amount=quote_order(self.store, LINES).total, now=NOW)

    def test_distance_is_about_100m(self):
        self.assertAlmostEqual(distance_m(LAT, LON, north(100), LON), 100, delta=1)

    # ZA-01
    def test_za01_new_zone_is_pending_and_cannot_take_orders(self):
        admin = self.person()
        zone = create_zone(self.store, admin, name="Edificio Los Pinos", district="Lince", lat=LAT, lon=LON, now=NOW)
        self.assertEqual(zone.status, "PENDIENTE_RECEPCION")
        self.assertEqual(zone.admin_id, admin)
        self.assertEqual(self.store.customers[admin].zone_id, zone.zone_id)
        self.assertRule("ZONE_NOT_AVAILABLE", self.order, admin)

    # ZA-02
    def test_za02_district_outside_pilot(self):
        admin = self.person()
        self.assertRule("DISTRICT_NOT_IN_PILOT", create_zone, self.store, admin, name="Larco", district="Miraflores",
                        lat=LAT, lon=LON, now=NOW)

    # ZA-03
    def test_za03_one_zone_per_admin(self):
        zone, admin = self.active_zone()
        self.assertRule("ALREADY_ADMIN", create_zone, self.store, admin, name="Otra", district="Lince",
                        lat=LAT, lon=LON, now=NOW)

    # ZA-04
    def test_za04_activation_enables_orders(self):
        zone, admin = self.active_zone()
        self.assertEqual(zone.status, "ACTIVA")
        self.assertEqual(zone.reception_contact, "Sr. Ramos")
        self.assertEqual(self.order(admin).zone_id, zone.zone_id)

    # ZA-05
    def test_za05_invalid_activation(self):
        admin = self.person()
        zone = create_zone(self.store, admin, name="Edificio", district="Lince", lat=LAT, lon=LON, now=NOW)
        other = self.person()
        self.assertRule("NOT_ZONE_ADMIN", activate_zone, self.store, zone.zone_id, other,
                        reception_kind="PORTERIA", contact="Sr. Ramos")
        self.assertRule("INVALID_RECEPTION", activate_zone, self.store, zone.zone_id, admin,
                        reception_kind="PORTERIA", contact="  ")
        self.assertRule("INVALID_RECEPTION", activate_zone, self.store, zone.zone_id, admin,
                        reception_kind="VECINO", contact="Ana")

    # ZA-06
    def test_za06_radius(self):
        zone, _ = self.active_zone()
        near = self.person(lat=north(250))
        far = self.person(lat=north(450))
        join_zone(self.store, near, zone.zone_id, now=NOW)
        self.assertEqual(self.store.customers[near].zone_id, zone.zone_id)
        self.assertRule("OUTSIDE_ZONE_RADIUS", join_zone, self.store, far, zone.zone_id, now=NOW)
        nowhere = self.person(lat=None, lon=None)
        self.assertRule("LOCATION_REQUIRED", join_zone, self.store, nowhere, zone.zone_id, now=NOW)
        self.assertRule("ZONE_NOT_FOUND", join_zone, self.store, near, "Z-NO-EXISTE", now=NOW)

    # ZA-07
    def test_za07_cannot_move_with_active_order(self):
        zone, _ = self.active_zone()
        other_zone, other_admin = self.active_zone(lat=north(400), name="Condominio")
        neighbor = self.person(lat=north(150))  # 150 m de A y 250 m de B: el radio no es el motivo
        join_zone(self.store, neighbor, zone.zone_id, now=NOW)
        self.order(neighbor)
        self.assertRule("HAS_ACTIVE_ORDER", join_zone, self.store, neighbor, other_zone.zone_id, now=NOW)

    # ZA-08
    def test_za08_merge_near_zones_count_together(self):
        a, admin_a = self.active_zone()
        b, admin_b = self.active_zone(lat=north(400), name="Condominio")
        request_id = request_merge(self.store, a.zone_id, b.zone_id, admin_a, now=NOW)
        accept_merge(self.store, request_id, admin_b, now=NOW)
        self.assertEqual(self.store.zones[a.zone_id].group_id, self.store.zones[b.zone_id].group_id)
        orders = self.s.orders(a.zone_id, 4) + self.s.orders(b.zone_id, 4)
        result = settle_cycle(self.store, CYCLE)
        self.assertTrue(all(result.orders[o.order_id].status == "LIQUIDADO" for o in orders))

    # ZA-09
    def test_za09_far_zones_cannot_merge(self):
        a, admin_a = self.active_zone()
        b, _ = self.active_zone(lat=north(1500), name="Lejos")
        self.assertRule("ZONES_TOO_FAR", request_merge, self.store, a.zone_id, b.zone_id, admin_a, now=NOW)

    # ZA-10
    def test_za10_no_chains(self):
        a, admin_a = self.active_zone()
        b, admin_b = self.active_zone(lat=north(400), name="B")
        c, admin_c = self.active_zone(lat=north(800), name="C")
        accept_merge(self.store, request_merge(self.store, a.zone_id, b.zone_id, admin_a, now=NOW), admin_b, now=NOW)
        self.assertRule("ZONES_TOO_FAR", request_merge, self.store, c.zone_id, b.zone_id, admin_c, now=NOW)
        self.assertRule("SAME_GROUP", request_merge, self.store, a.zone_id, b.zone_id, admin_a, now=NOW)

    # ZA-11
    def test_za11_only_target_admin_accepts(self):
        a, admin_a = self.active_zone()
        b, _ = self.active_zone(lat=north(400), name="B")
        request_id = request_merge(self.store, a.zone_id, b.zone_id, admin_a, now=NOW)
        self.assertRule("NOT_ZONE_ADMIN", accept_merge, self.store, request_id, admin_a, now=NOW)
        self.assertRule("MERGE_REQUEST_NOT_FOUND", accept_merge, self.store, 999, admin_a, now=NOW)

    # ZA-12
    def test_za12_leave_group(self):
        a, admin_a = self.active_zone()
        b, admin_b = self.active_zone(lat=north(400), name="B")
        accept_merge(self.store, request_merge(self.store, a.zone_id, b.zone_id, admin_a, now=NOW), admin_b, now=NOW)
        leave_group(self.store, a.zone_id, admin_a, now=NOW)
        self.assertNotEqual(self.store.zones[a.zone_id].group_id, self.store.zones[b.zone_id].group_id)

    # ZA-13
    def test_za13_transfer_admin(self):
        zone, admin = self.active_zone()
        neighbor = self.person(lat=north(100))
        join_zone(self.store, neighbor, zone.zone_id, now=NOW)
        outsider = self.person()
        self.assertRule("NOT_ZONE_MEMBER", transfer_admin, self.store, zone.zone_id, admin, outsider)
        transfer_admin(self.store, zone.zone_id, admin, neighbor)
        self.assertEqual(self.store.zones[zone.zone_id].admin_id, neighbor)
        self.assertRule("NOT_ZONE_ADMIN", transfer_admin, self.store, zone.zone_id, admin, neighbor)

    # ZA-14
    def test_za14_merges_only_while_cycle_open(self):
        a, admin_a = self.active_zone()
        b, _ = self.active_zone(lat=north(400), name="B")
        self.assertRule("CYCLE_CLOSED", request_merge, self.store, a.zone_id, b.zone_id, admin_a, now=THURSDAY)


if __name__ == "__main__":
    unittest.main()
