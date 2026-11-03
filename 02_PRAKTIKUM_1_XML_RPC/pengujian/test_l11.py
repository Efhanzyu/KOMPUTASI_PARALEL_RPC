"""L1.1 - pangkat() dan akar(); semua method harus muncul di system.listMethods()."""
import unittest
import xmlrpc.client
from _util import ServerUji


class TestL11(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = ServerUji()
        cls.p = xmlrpc.client.ServerProxy(cls.s.url())

    @classmethod
    def tearDownClass(cls):
        cls.s.berhenti()

    def test_list_methods_lengkap(self):
        daftar = self.p.system.listMethods()
        for nama in ("tambah", "kali", "bagi", "pangkat", "akar", "statistik"):
            self.assertIn(nama, daftar)   # mencegah error 'method "pangkat" is not supported'

    def test_pangkat(self):
        self.assertEqual(self.p.pangkat(2, 3), 8)
        self.assertEqual(self.p.pangkat(3, 4), 81)
        self.assertEqual(self.p.pangkat(5, 0), 1)

    def test_akar(self):
        self.assertEqual(self.p.akar(25), 5)
        self.assertEqual(self.p.akar(81), 9)
        self.assertAlmostEqual(self.p.akar(2), 2 ** 0.5)

    def test_akar_negatif_fault(self):
        with self.assertRaises(xmlrpc.client.Fault) as c:
            self.p.akar(-4)
        self.assertEqual(c.exception.faultCode, 1002)

    def test_dasar(self):
        self.assertEqual(self.p.tambah(5, 3), 8)
        self.assertEqual(self.p.kali(4, 7), 28)
        self.assertEqual(self.p.bagi(10, 4), 2.5)
        with self.assertRaises(xmlrpc.client.Fault) as c:
            self.p.bagi(10, 0)
        self.assertEqual(c.exception.faultCode, 1001)


if __name__ == "__main__":
    unittest.main(verbosity=2)
