"""L1.4 - Memastikan skrip benchmark menghasilkan 100 pemanggilan dan angka waktu yang masuk akal.
CATATAN: pengujian dua komputer BELUM DILAKUKAN; test ini hanya memverifikasi skrip
(loopback satu komputer)."""
import time
import unittest
import xmlrpc.client
from _util import ServerUji


class TestL14(unittest.TestCase):
    def test_100_panggilan_rpc_dan_lokal(self):
        s = ServerUji()
        try:
            p = xmlrpc.client.ServerProxy(s.url())
            lokal = lambda a, b: a + b
            t0 = time.perf_counter()
            hasil_lokal = [lokal(i, 3) for i in range(100)]
            t_lokal = time.perf_counter() - t0
            t0 = time.perf_counter()
            hasil_rpc = [p.tambah(i, 3) for i in range(100)]
            t_rpc = time.perf_counter() - t0
        finally:
            s.berhenti()
        self.assertEqual(hasil_lokal, hasil_rpc)       # hasil identik
        self.assertGreater(t_rpc, t_lokal)             # RPC pasti lebih lambat
        print(f"\n  lokal={t_lokal:.6f}s  rpc={t_rpc:.6f}s  rasio={t_rpc / t_lokal:.0f}x")


if __name__ == "__main__":
    unittest.main(verbosity=2)
