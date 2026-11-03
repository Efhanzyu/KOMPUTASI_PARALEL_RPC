"""L1.3 - datetime dan bilangan > 2^31. Yang diuji adalah PERILAKU AKTUAL implementasi Python."""
import datetime
import unittest
import xmlrpc.client
from _util import ServerUji


class TestL13(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = ServerUji()
        cls.p = xmlrpc.client.ServerProxy(cls.s.url(), allow_none=True)

    @classmethod
    def tearDownClass(cls):
        cls.s.berhenti()

    def test_datetime_diterima_sebagai_DateTime(self):
        t = datetime.datetime(2026, 11, 2, 13, 45, 30, 123456)
        h = self.p.uji_datetime(t)
        self.assertEqual(h["tipe_diterima"], "DateTime")      # bukan datetime.datetime
        self.assertEqual(h["nilai_diterima"], "20261102T13:45:30")

    def test_mikrodetik_hilang(self):
        t = datetime.datetime(2026, 11, 2, 13, 45, 30, 123456)
        balik = self.p.uji_echo(t)
        self.assertIsInstance(balik, xmlrpc.client.DateTime)
        self.assertEqual(balik.value, "20261102T13:45:30")

    def test_int_batas_dalam_rentang(self):
        h = self.p.uji_bilangan_besar(2 ** 31 - 1)
        self.assertEqual(h["nilai_diterima"], str(2 ** 31 - 1))

    def test_int_di_atas_batas_overflow_di_client(self):
        for n in (2 ** 31, 2 ** 40, -(2 ** 31) - 1):
            with self.subTest(n=n):
                with self.assertRaises(OverflowError):
                    self.p.uji_bilangan_besar(n)

    def test_overflow_di_sisi_server_menjadi_fault(self):
        with self.assertRaises(xmlrpc.client.Fault) as c:
            self.p.pangkat(2, 31)
        self.assertIn("OverflowError", c.exception.faultString)

    # ---- solusi alternatif (bukan pengujian asli) ----
    def test_alternatif_string_untuk_bilangan_besar(self):
        self.assertEqual(self.p.uji_kembalikan_besar_string(str(2 ** 62)), str(2 ** 62))

    def test_alternatif_string_iso_untuk_datetime(self):
        t = datetime.datetime(2026, 11, 2, 13, 45, 30, 123456)
        self.assertEqual(datetime.datetime.fromisoformat(self.p.uji_echo(t.isoformat())), t)


if __name__ == "__main__":
    unittest.main(verbosity=2)
