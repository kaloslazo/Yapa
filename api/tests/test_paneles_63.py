"""PO-01: hitos reales, cronológicos y privados para portería."""
from datetime import timedelta
from test_personal_por_rol import Base, FRIDAY, SATURDAY, ADMIN, CONCIERGE
from test_settlement import CYCLE, buy_all
from yapa_sdd import reception, logistics
from yapa_sdd.fulfillment import pack_bag, deliver_zone, register_failed_delivery


class ReceptionProgress(Base):
    def test_po_01_hitos_desde_armado_hasta_recepcion(self):
        self.concierge()
        data = reception.for_zone(self.store, CYCLE, 'Z-JM-01')
        self.assertEqual(data['seguimiento'], 'preparando')
        self.assertEqual(data['hitos'], [])
        self.pack_all()
        self.assertEqual(reception.for_zone(self.store, CYCLE, 'Z-JM-01')['seguimiento'], 'listo')
        buy_all(self.store, CYCLE)
        logistics.dispatch_zone(self.store, CYCLE, 'Z-JM-01', by=ADMIN, now=SATURDAY)
        data = reception.for_zone(self.store, CYCLE, 'Z-JM-01')
        self.assertEqual(data['estado'], 'pendiente')  # contrato anterior intacto
        self.assertEqual(data['seguimiento'], 'en_camino')
        deliver_zone(self.store, CYCLE, 'Z-JM-01', by=ADMIN, photo='fotos/entrega.jpg', received_by='Portero', now=SATURDAY + timedelta(hours=1))
        reception.confirm_reception(self.store, CYCLE, 'Z-JM-01', by=CONCIERGE, now=SATURDAY + timedelta(hours=2))
        data = reception.for_zone(self.store, CYCLE, 'Z-JM-01')
        self.assertEqual([h['estado'] for h in data['hitos']], ['listo', 'en_camino', 'entregada', 'recibida'])
        self.assertEqual(data['seguimiento'], 'recibida')
        self.assertTrue(all(set(h) == {'estado', 'hora'} for h in data['hitos']))
        self.assertTrue(all(set(p) == {'id', 'vecino', 'bolsas'} for p in data['pedidos']))

    def test_po_01_falla_y_zona_sin_pedidos(self):
        self.pack_all()
        buy_all(self.store, CYCLE)
        register_failed_delivery(self.store, CYCLE, 'Z-JM-01', by=ADMIN, photo='fotos/falla.jpg', reason='NADIE_RECIBE', now=SATURDAY)
        self.assertEqual(reception.for_zone(self.store, CYCLE, 'Z-JM-01')['seguimiento'], 'fallida')
        empty = reception.for_zone(self.store, CYCLE, 'Z-LINCE-01')
        self.assertEqual(empty['seguimiento'], 'sin_pedidos')
        self.assertEqual(empty['hitos'], [])
