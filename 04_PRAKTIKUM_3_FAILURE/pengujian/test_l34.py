"""L3.4 - Versi ringkas: lebih banyak worker -> throughput lebih tinggi (server sleep 0,1 s)."""
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

from _util import ServerUji, pb


def throughput(workers, n=40, threads=10):
    s = ServerUji(prob_lambat=0.0, jeda_get=0.1, workers=workers)
    try:
        with ThreadPoolExecutor(threads) as pool:
            list(pool.map(lambda _: s.stub.GetMahasiswa(pb.MahasiswaRequest(nim="2023001")), range(threads)))  # warm-up
            t0 = time.perf_counter()
            list(pool.map(lambda _: s.stub.GetMahasiswa(pb.MahasiswaRequest(nim="2023001")), range(n)))
            return n / (time.perf_counter() - t0)
    finally:
        s.tutup()


class TestL34(unittest.TestCase):
    def test_throughput_naik_dengan_worker(self):
        t1, t4, t10 = throughput(1), throughput(4), throughput(10)
        print(f"\n  throughput 1/4/10 worker = {t1:.1f} / {t4:.1f} / {t10:.1f} req/s")
        self.assertLess(t1, 12)          # ~10 req/s: serial karena sleep 0,1 s
        self.assertGreater(t4, 2.5 * t1)
        self.assertGreater(t10, 1.5 * t4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
