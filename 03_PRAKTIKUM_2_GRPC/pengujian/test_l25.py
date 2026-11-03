"""L2.5 - RPC asinkron dengan .future(): 10 permintaan sekaligus, hasil via .result()."""
import time
import unittest

import grpc
from _util import ServerUji, pb


class TestL25(unittest.TestCase):
    def test_sepuluh_future(self):
        s = ServerUji(jeda_get=0.1)
        try:
            nim = ["2023001", "2023002"] * 5
            s.stub.GetMahasiswa(pb.MahasiswaRequest(nim="2023001"))   # warm-up
            t0 = time.perf_counter()
            fs = [s.stub.GetMahasiswa.future(pb.MahasiswaRequest(nim=n)) for n in nim]
            hasil = [f.result(timeout=10) for f in fs]
            t_async = time.perf_counter() - t0
            t0 = time.perf_counter()
            serial = [s.stub.GetMahasiswa(pb.MahasiswaRequest(nim=n)) for n in nim]
            t_serial = time.perf_counter() - t0
        finally:
            s.tutup()
        self.assertEqual(len(hasil), 10)
        self.assertEqual(hasil, serial)
        self.assertGreater(t_serial, 0.95)    # 10 x 0,1 s
        self.assertLess(t_async, 0.5)         # paralel di server (max_workers=10)
        print(f"\n  serial={t_serial*1000:.0f} ms async={t_async*1000:.0f} ms speedup={t_serial/t_async:.1f}x")

    def test_rpcerror_pada_future(self):
        s = ServerUji()
        try:
            f = s.stub.GetMahasiswa.future(pb.MahasiswaRequest(nim="9999"))
            with self.assertRaises(grpc.RpcError) as c:
                f.result(timeout=5)
            self.assertEqual(c.exception.code(), grpc.StatusCode.NOT_FOUND)
            self.assertEqual(f.code(), grpc.StatusCode.NOT_FOUND)
        finally:
            s.tutup()


if __name__ == "__main__":
    unittest.main(verbosity=2)
