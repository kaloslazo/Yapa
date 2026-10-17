from decimal import Decimal as D
import unittest

from test_settlement import CYCLE, Scenario

from yapa_sdd import settlement
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.metrics import PESSIMISTIC
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.simulator import savings_share_table, simulate


class SavingsShareSpecTests(unittest.TestCase):
    # RA-A
    def test_ra_a_default_share_is_zero(self):
        s = Scenario()
        orders = s.orders("Z-JM-01", 20)
        result = settle_cycle(s.store, CYCLE)
        self.assertEqual(settlement.VOLUME_SAVINGS_SHARE, D("0"))
        self.assertEqual(result.orders[orders[0].order_id].final_amount, D("48.14"))
        self.assertEqual(result.orders[orders[0].order_id].refund_amount, D("12.86"))

    # RA-B
    def test_ra_b_half_share(self):
        s = Scenario()
        orders = s.orders("Z-JM-01", 20)
        result = settle_cycle(s.store, CYCLE, savings_share=D("0.5"))
        self.assertEqual(result.products["PAPA-AMARILLA"].final_unit_price, D("3.9088"))
        sim = simulate(20, D("40"), D("0.12"), PESSIMISTIC, savings_share=D("0.5"))
        self.assertAlmostEqual(float(sim.average_net_margin), 2.41, delta=0.011)
        self.assertAlmostEqual(float(sim.average_customer_savings), 7.93, delta=0.011)

    # RA-C
    def test_ra_c_invalid_share(self):
        for share in (D("-0.1"), D("1.5")):
            with self.subTest(share=share):
                s = Scenario()
                s.orders("Z-JM-01", 8)
                with self.assertRaises(BusinessRuleError) as raised:
                    settle_cycle(s.store, CYCLE, savings_share=share)
                self.assertEqual(raised.exception.code, "INVALID_SAVINGS_SHARE")

    # RA-D
    def test_ra_d_full_share_never_exceeds_max(self):
        s = Scenario()
        orders = s.orders("Z-JM-01", 20)
        result = settle_cycle(s.store, CYCLE, savings_share=D("1"))
        self.assertEqual(result.products["PAPA-AMARILLA"].final_unit_price, D("4.032"))
        self.assertEqual(result.orders[orders[0].order_id].refund_amount, D("3.00"))  # solo el envío

    # RA-E
    def test_ra_e_simulation_does_not_change_default(self):
        simulate(20, D("40"), D("0.12"), PESSIMISTIC, savings_share=D("0.5"))
        self.assertEqual(settlement.VOLUME_SAVINGS_SHARE, D("0"))
        table = savings_share_table(D("40"), 20)
        self.assertEqual(set(table), {D("0"), D("0.25"), D("0.5")})


if __name__ == "__main__":
    unittest.main()
