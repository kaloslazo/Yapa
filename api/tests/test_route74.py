import json, unittest
from unittest.mock import patch
from yapa_sdd import street_routing
from yapa_sdd.domain import BusinessRuleError

class StreetRouteTests(unittest.TestCase):
 def setUp(self):street_routing.clear_cache()
 def test_geometry_distance_and_cache(self):
  data={'code':'Ok','routes':[{'distance':1200,'duration':240,'geometry':{'type':'LineString','coordinates':[[-77,-12],[-77.01,-12.01]]}}]}
  with patch.object(street_routing,'fetch_route',return_value=data) as fetch:
   first=street_routing.street_route([(-77,-12),(-77.01,-12.01)])
   again=street_routing.street_route([(-77,-12),(-77.01,-12.01)])
  self.assertEqual(first['distancia_m'],1200);self.assertEqual(first['coordenadas'],data['routes'][0]['geometry']['coordinates']);self.assertEqual(first,again);fetch.assert_called_once()
 def test_invalid_or_unavailable_never_returns_fake_line(self):
  with self.assertRaises(BusinessRuleError) as e:street_routing.street_route([(999,0),(0,0)])
  self.assertEqual(e.exception.code,'INVALID_ROUTE')
  with patch.object(street_routing,'fetch_route',side_effect=TimeoutError):
   with self.assertRaises(BusinessRuleError) as e:street_routing.street_route([(-77,-12),(-77.01,-12.01)])
  self.assertEqual(e.exception.code,'ROUTE_UNAVAILABLE')
 def test_malformed_geometry_rejected(self):
  with patch.object(street_routing,'fetch_route',return_value={'code':'Ok','routes':[{'distance':1,'duration':1,'geometry':{'coordinates':[[float('nan'),0],[0,0]]}}]}):
   with self.assertRaises(BusinessRuleError) as e:street_routing.street_route([(-77,-12),(-77.01,-12.01)])
  self.assertEqual(e.exception.code,'ROUTE_UNAVAILABLE')

 def test_api_derives_only_pending_attended_zones_and_requires_session(self):
  from api_client import ApiClient
  from test_settlement import Scenario,CYCLE,NOW
  from web_client import fast_hashing
  from yapa_sdd.auth import set_admin_password
  from yapa_sdd.web.api import create_api
  fast_hashing(self);s=Scenario();s.orders('Z-JM-01',8);s.orders('Z-LINCE-01',8)
  set_admin_password(s.store,'admin-yapa','yapa-admin-2026');app=create_api(s.store,clock=lambda:NOW)
  client=ApiClient(app);client.login('admin-yapa','yapa-admin-2026','admin')
  payload={'ciclo':CYCLE,'zonas':json.dumps(['Z-JM-01','Z-LINCE-01'])}
  with patch('yapa_sdd.web.api.street_route',return_value={'distancia_m':100}) as routing:
   self.assertEqual(client.post('/api/reparto/ruta',payload)[0],200)
  routing.assert_called_once_with([(s.store.zones[z].lon,s.store.zones[z].lat) for z in ['Z-JM-01','Z-LINCE-01']])
  payload['zonas']=json.dumps(['Z-JM-01','DESCONOCIDA']);self.assertEqual(client.post('/api/reparto/ruta',payload)[1]['error']['codigo'],'INVALID_ROUTE')
  self.assertEqual(ApiClient(app).post('/api/reparto/ruta',payload)[0],401)
