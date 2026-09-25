import os
import sys
from decimal import Decimal
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from validar_precios import AHORRO_OBJETIVO, ahorro, comision_maxima, precio_yapa  # noqa: E402


class ValidarPreciosTests(unittest.TestCase):
    def test_papa_blanca_matches_economic_analysis(self):
        # docs/analisis/08_validacion_economica.md: 0.98 mayorista -> ~1.19 Yapa, ~50 % de ahorro vs 2.39
        yapa = precio_yapa(Decimal("0.98"), "FRESCOS")
        self.assertAlmostEqual(float(yapa), 1.19, places=2)
        self.assertAlmostEqual(float(ahorro(yapa, Decimal("2.39"))), 50.0, delta=0.5)

    def test_max_commission_gives_exactly_the_target_saving(self):
        maxima = comision_maxima(Decimal("2.00"), "FRESCOS", Decimal("3.00"))
        yapa = precio_yapa(Decimal("2.00"), "FRESCOS", maxima / 100)
        self.assertAlmostEqual(float(ahorro(yapa, Decimal("3.00"))), float(AHORRO_OBJETIVO), places=6)

    def test_cleaning_has_no_merma(self):
        yapa = precio_yapa(Decimal("100"), "LIMPIEZA")
        self.assertEqual(yapa, Decimal("100") * Decimal("1.09") * (1 + Decimal("5") / Decimal("150")))


if __name__ == "__main__":
    unittest.main()
