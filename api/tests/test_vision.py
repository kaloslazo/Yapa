import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from api_client import ApiClient
from test_api import ADMIN, ADMIN_PASS, PIN, WEDNESDAY
from web_client import fast_hashing
from yapa_sdd import partners, vision
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api

class VisionTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store(); set_admin_password(self.store, ADMIN, ADMIN_PASS); set_pin(self.store, 101, PIN)
        partners.create_staff(self.store, 'armador-vision', partners.PACKER, 'Armado', 'clave-prueba-2026', by=ADMIN, now=WEDNESDAY)
        partners.create_supplier_account(self.store, 'proveedor-vision', 'SUP-FRESCOS', 'clave-prueba-2026', by=ADMIN, now=WEDNESDAY)
        self.folder = tempfile.TemporaryDirectory(); self.addCleanup(self.folder.cleanup)
        self.api = create_api(self.store, clock=lambda: WEDNESDAY, photo_dir=self.folder.name)

    def test_count_is_boxes_not_weight_and_filters_unknown_low_scores(self):
        rows = vision.summarize({0:'papa', 1:'cebolla', 2:'person'}, [(0,.9),(0,.6),(0,.1),(1,.7),(2,.9)])
        self.assertEqual([(r['producto'],r['cantidad']) for r in rows], [('papa',2),('cebolla',1)])

    def test_analysis_allowed_for_packer_supplier_admin_and_does_not_save(self):
        for user, secret, role in [(ADMIN,ADMIN_PASS,'admin'), ('armador-vision','clave-prueba-2026',partners.PACKER), ('proveedor-vision','clave-prueba-2026',partners.SUPPLIER)]:
            client = ApiClient(self.api); self.assertEqual(client.login(user,secret,role)[0],200)
            with patch.object(vision,'analyze_photo',return_value={'productos':[{'producto':'papa','cantidad':2}]}) as detector:
                status, body = client.post_file('/api/vision/analizar', {}, {'foto_archivo':('foto.jpg',b'image')})
            self.assertEqual(status,200); self.assertEqual(body['productos'][0]['cantidad'],2)
            detector.assert_called_once_with(('foto.jpg',b'image'))
        self.assertEqual(list(Path(self.folder.name).iterdir()),[]); self.assertFalse(self.store.bags)

    def test_neighbor_and_anonymous_cannot_analyze(self):
        public = ApiClient(self.api); self.assertEqual(public.post('/api/vision/analizar')[0],401)
        public.login(101,PIN); self.assertEqual(public.post('/api/vision/analizar')[0],403)

    def test_csrf_required(self):
        client=ApiClient(self.api); client.login(ADMIN,ADMIN_PASS,'admin')
        self.assertEqual(client.post('/api/vision/analizar',with_csrf=False)[0],403)

    def test_missing_photo_and_size(self):
        client=ApiClient(self.api);client.login(ADMIN,ADMIN_PASS,'admin')
        self.assertEqual(client.post('/api/vision/analizar')[1]['error']['codigo'],'PHOTO_REQUIRED')
        from yapa_sdd.domain import BusinessRuleError
        with self.assertRaises(BusinessRuleError) as error: vision.analyze_photo(('big.jpg',b'x'*(8*1024*1024+1)))
        self.assertEqual(error.exception.code,'PHOTO_TOO_LARGE')
