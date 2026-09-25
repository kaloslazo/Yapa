from decimal import Decimal as D
import unittest

from yapa_sdd.domain import COMMISSION
from yapa_sdd.metrics import OPTIMISTIC, PESSIMISTIC
from yapa_sdd.simulator import break_even_orders, decision_table, simulate


class SimulatorSpecTests(unittest.TestCase):
    # SA-01
    def test_sa01_matches_iteration_13(self):
        self.assertEqual(simulate(8, D("40"), D("0.12"), PESSIMISTIC).average_net_margin, D("-1.8195"))
        self.assertEqual(simulate(8, D("40"), D("0.12"), OPTIMISTIC).average_net_margin, D("3.31"))

    # SA-02
    def test_sa02_more_orders_better_margin(self):
        small = simulate(8, D("40"), D("0.12"), PESSIMISTIC)
        big = simulate(20, D("40"), D("0.12"), PESSIMISTIC)
        self.assertGreater(big.average_net_margin, small.average_net_margin)
        self.assertGreater(big.average_customer_savings, small.average_customer_savings)

    # SA-03
    def test_sa03_does_not_touch_real_commission(self):
        simulate(8, D("40"), D("0.15"), PESSIMISTIC)
        self.assertEqual(COMMISSION["FRESCOS"], D("0.12"))

    # SA-04
    def test_sa04_break_even(self):
        self.assertEqual(break_even_orders(D("40"), D("0.12"), OPTIMISTIC), 8)
        pessimistic = break_even_orders(D("40"), D("0.12"), PESSIMISTIC)
        self.assertTrue(pessimistic is None or pessimistic > 8)

    # SA-05
    def test_sa05_decision_table(self):
        table = decision_table(D("40"))
        self.assertEqual(set(table), {"OPTIMISTA", "PESIMISTA"})
        self.assertEqual(len(table["PESIMISTA"]), 12)
        self.assertEqual(table["PESIMISTA"][(8, D("0.12"))], D("-1.8195"))


if __name__ == "__main__":
    unittest.main()
