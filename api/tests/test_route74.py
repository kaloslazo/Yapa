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
