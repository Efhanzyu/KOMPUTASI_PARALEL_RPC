"""L1.2 - statistik(): list masuk, dictionary keluar, serta penanganan input salah."""
import unittest
import xmlrpc.client
from _util import ServerUji
from analisis_xml_helper import ambil_xml_dumps


class TestL12(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = ServerUji()
        cls.p = xmlrpc.client.ServerProxy(cls.s.url(), allow_none=True)

    @classmethod
    def tearDownClass(cls):
        cls.s.berhenti()

    def test_contoh_modul(self):
        self.assertEqual(self.p.statistik([10, 20, 30, 40, 50]),
                         {"min": 10, "max": 50, "rata2": 30})

    def test_float_dan_negatif(self):
        h = self.p.statistik([-1.5, 2.5, 5])
        self.assertEqual(h["min"], -1.5)
        self.assertEqual(h["max"], 5)
        self.assertAlmostEqual(h["rata2"], 2.0)

    def test_kosong_fault(self):
        with self.assertRaises(xmlrpc.client.Fault):
            self.p.statistik([])

    def test_tidak_valid_fault(self):
        for salah in ([1, "a"], [1, None], [True, 2], "bukan list", 5):
            with self.subTest(salah=salah):
                with self.assertRaises(xmlrpc.client.Fault):
                    self.p.statistik(salah)

    def test_marshalling_list_dan_dict(self):
        # List -> <array><data><value>..., dict -> <struct><member><name>/<value>
        req = ambil_xml_dumps([[10, 20]], "statistik")
        self.assertIn("<array><data>", req)
        res = ambil_xml_dumps(({"min": 10, "max": 50, "rata2": 30},), None)
        self.assertIn("<struct>", res)
        self.assertIn("<member>\n<name>min</name>", res)


if __name__ == "__main__":
    unittest.main(verbosity=2)
