import unittest,tempfile
from pathlib import Path
from test_settlement import Scenario, NOW
from web_client import fast_hashing
from yapa_sdd import partners, persistence, supplier_stock
from yapa_sdd.domain import BusinessRuleError

class Stock72Tests(unittest.TestCase):
 def setUp(self):
  fast_hashing(self);self.store=Scenario().store
  partners.create_supplier_account(self.store,'stock-frescos','SUP-FRESCOS','clave-prueba-2026',by='admin-yapa',now=NOW)
  partners.create_supplier_account(self.store,'stock-limpieza','SUP-LIMPIEZA','clave-prueba-2026',by='admin-yapa',now=NOW)
 def confirm(self,rows,photo=b'\xff\xd8\xffprimera-foto',user='stock-frescos'):
  return supplier_stock.confirm(self.store,user,'2026-W39',rows,('foto.jpg',photo),NOW)
 def test_multiple_rows_accumulate_and_same_photo_is_idempotent(self):
  rows=[{'id':'PAPA-AMARILLA','unidades':2,'peso':'1.2'},{'id':'PAPA-AMARILLA','unidades':3,'peso':'2.3'}]
  first=self.confirm(rows);repeat=self.confirm(rows)
  self.assertEqual(first['productos'][0]['cantidad'],'3.5');self.assertEqual(repeat['productos'][0]['cantidad'],'3.5');self.assertTrue(repeat['repetida'])
  second=self.confirm([{'id':'PAPA-AMARILLA','unidades':1,'peso':'0.6'}],b'\xff\xd8\xffsegunda-foto')
  self.assertEqual(second['productos'][0]['cantidad'],'4.1');self.assertEqual(second['productos'][0]['disponible'],'4');self.assertEqual(second['productos'][0]['unidades'],6)
 def test_weight_required_no_automatic_units_to_kg(self):
  for value in [None,'NaN','Infinity','0','-1']:
   with self.assertRaises(BusinessRuleError) as e:self.confirm([{'id':'ZANAHORIA','unidades':3,'peso':value}])
   self.assertEqual(e.exception.code,'WEIGHT_REQUIRED')
  self.assertFalse(self.store.supplier_stock_batches)
 def test_rejects_other_supplier_without_partial_update(self):
  with self.assertRaises(BusinessRuleError) as e:self.confirm([{'id':'AJO','unidades':1,'peso':'1'},{'id':'LIMPIATODO-GALON','unidades':1}])
  self.assertEqual(e.exception.code,'INVALID_STOCK_ITEM');self.assertFalse(self.store.supplier_stock_batches)
 def test_units_are_units_and_persist(self):
  result=self.confirm([{'id':'LIMPIATODO-GALON','unidades':3}],user='stock-limpieza');self.assertEqual(result['productos'][0]['disponible'],'3')
  with tempfile.TemporaryDirectory() as t:
   p=str(Path(t)/'stock.db');persistence.save(self.store,p);loaded=persistence.load(p)
   self.assertEqual(supplier_stock.snapshot(loaded,'stock-limpieza','2026-W39')['productos'],result['productos'])
 def test_cannot_change_already_confirmed_photo(self):
  self.confirm([{'id':'AJO','unidades':1,'peso':'1'}])
  with self.assertRaises(BusinessRuleError) as e:self.confirm([{'id':'AJO','unidades':2,'peso':'2'}])
  self.assertEqual(e.exception.code,'STOCK_ALREADY_CONFIRMED')
