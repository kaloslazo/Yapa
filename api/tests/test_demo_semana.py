"""Herramienta de la demo de la semana completa (api/tools/demo_semana.py): reloj movible y lejía a punto de bajar."""

import importlib.util
import tempfile
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from yapa_sdd import cycle
from yapa_sdd.cycle import LIMA
from yapa_sdd.web.api import PHOTO_PATH

_spec = importlib.util.spec_from_file_location("demo_semana", Path(__file__).resolve().parents[1] / "tools" / "demo_semana.py")
demo_semana = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(demo_semana)

NOW = datetime(2026, 11, 12, 18, 0, tzinfo=LIMA)  # jueves de la semana 46


class RelojDeLaDemo(unittest.TestCase):
    def setUp(self):
        self.base = datetime(2026, 11, 11, 10, 0, tzinfo=LIMA)
        self.reloj = {"ahora": self.base}
        self.app = demo_semana.con_reloj(lambda environ, start: [b"tienda"], self.reloj, self.base)

    def get(self, path, query=""):
        estado = []
        cuerpo = self.app({"PATH_INFO": path, "QUERY_STRING": query}, lambda status, headers: estado.append(status))
        return estado, b"".join(cuerpo).decode()

    def test_mover_reloj_al_jueves_cierra_el_pedido(self):
        _, cuerpo = self.get(demo_semana.RUTA, "ir=jueves")
        self.assertEqual(self.reloj["ahora"], self.base + timedelta(days=1))
        self.assertFalse(cycle.is_open(self.reloj["ahora"]))
        self.assertIn("jueves 12/11 10:00", cuerpo)

    def test_domingo_queda_dentro_de_las_24_horas_del_reclamo(self):
        self.get(demo_semana.RUTA, "ir=domingo")
        sabado = demo_semana.momento(self.base, "sabado")
        self.assertLess(self.reloj["ahora"] - sabado, timedelta(hours=24))

    def test_siguiente_abre_la_semana_nueva(self):
        self.get(demo_semana.RUTA, "ir=siguiente")
        self.assertTrue(cycle.is_open(self.reloj["ahora"]))
        self.assertNotEqual(cycle.cycle_id(self.reloj["ahora"]), cycle.cycle_id(self.base))

    def test_momento_desconocido_no_mueve_el_reloj(self):
        self.get(demo_semana.RUTA, "ir=feriado")
        self.assertEqual(self.reloj["ahora"], self.base)

    def test_lo_demas_pasa_a_la_tienda(self):
        _, cuerpo = self.get("/api/estado")
        self.assertEqual(cuerpo, "tienda")


class FotosDeLaSemilla(unittest.TestCase):
    def test_la_semana_pasada_queda_con_fotos_que_el_motor_sirve(self):
        store = demo_semana.armar(NOW, credenciales=False)
        with tempfile.TemporaryDirectory() as carpeta:
            demo_semana.fotos_de_la_semilla(store, carpeta)
            rutas = [bag.photo for bags in store.bags.values() for bag in bags]
            rutas += [delivery.photo for delivery in store.deliveries.values()]
            self.assertTrue(rutas)
            for ruta in rutas:
                self.assertRegex(ruta, PHOTO_PATH)
                self.assertTrue((Path(carpeta) / ruta.split("/", 1)[1]).is_file())


class SemanaArmada(unittest.TestCase):
    def test_la_lejia_queda_a_dos_galones_de_bajar(self):
        store = demo_semana.armar(NOW, credenciales=False)
        semana = cycle.cycle_id(store.demo_now)
        lejia = sum((linea.quantity for orden in store.orders_in_cycle(semana)
                     for linea in orden.lines if linea.product_id == "LEJIA-GALON"), Decimal("0"))
        self.assertEqual(lejia, Decimal("10"))


if __name__ == "__main__":
    unittest.main()
