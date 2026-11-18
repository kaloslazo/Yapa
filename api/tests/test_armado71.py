import unittest, tempfile
from pathlib import Path
from test_settlement import Scenario, CYCLE
from test_fulfillment import FRIDAY, BEFORE_CLOSE
from yapa_sdd import fulfillment, persistence
from yapa_sdd.domain import BusinessRuleError

class Armado71Tests(unittest.TestCase):
    def setUp(self):
        self.s=Scenario(); self.store=self.s.store; self.order=self.s.orders('Z-JM-01',8)[0]
    def test_review_survives_persistence_and_removal_keeps_ids(self):
        first=fulfillment.pack_bag(self.store,self.order.order_id,by='admin-yapa',photo='uno.jpg',now=FRIDAY,review=[{'id':'PAPA-AMARILLA','unidades':2}])
        second=fulfillment.pack_bag(self.store,self.order.order_id,by='admin-yapa',photo='dos.jpg',now=FRIDAY)
        fulfillment.remove_bag(self.store,self.order.order_id,first.number,by='admin-yapa',now=FRIDAY)
        third=fulfillment.pack_bag(self.store,self.order.order_id,by='admin-yapa',photo='tres.jpg',now=FRIDAY)
        self.assertEqual((second.number,third.number),(2,3));self.assertEqual(len(self.store.bag_removals),1)
        with tempfile.TemporaryDirectory() as t:
            p=str(Path(t)/'test.db');persistence.save(self.store,p);loaded=persistence.load(p)
            self.assertEqual(loaded.bag_removals[0]['foto'],'uno.jpg')
    def test_rejects_foreign_product_and_invalid_counts_without_bag(self):
        for row in [{'id':'NO-EXISTE','unidades':1},{'id':'PAPA-AMARILLA','unidades':0},{'id':'PAPA-AMARILLA','unidades':1.5}]:
            with self.assertRaises(BusinessRuleError) as e:
                fulfillment.pack_bag(self.store,self.order.order_id,by='admin-yapa',photo='x.jpg',now=FRIDAY,review=[row])
            self.assertEqual(e.exception.code,'INVALID_BAG_REVIEW')
        self.assertFalse(self.store.bags)
    def test_cannot_remove_after_dispatch_and_cannot_pack_before_close(self):
        bag=fulfillment.pack_bag(self.store,self.order.order_id,by='admin-yapa',photo='x.jpg',now=FRIDAY)
        self.store.dispatches[(CYCLE,'Z-JM-01')]=object()
        with self.assertRaises(BusinessRuleError) as e:fulfillment.remove_bag(self.store,self.order.order_id,bag.number,by='admin-yapa',now=FRIDAY)
        self.assertEqual(e.exception.code,'ZONE_ALREADY_CLOSED');self.assertEqual(len(self.store.bags[self.order.order_id]),1)
        with self.assertRaises(BusinessRuleError) as e:fulfillment.pack_bag(self.store,self.order.order_id,by='admin-yapa',photo='x.jpg',now=BEFORE_CLOSE)
        self.assertEqual(e.exception.code,'CYCLE_STILL_OPEN')
    def test_missing_bag_has_clear_error(self):
        with self.assertRaises(BusinessRuleError) as e:fulfillment.remove_bag(self.store,self.order.order_id,99,by='admin-yapa',now=FRIDAY)
        self.assertEqual(e.exception.code,'BAG_NOT_FOUND')
