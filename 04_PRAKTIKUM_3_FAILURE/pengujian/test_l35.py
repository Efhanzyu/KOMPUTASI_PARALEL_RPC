"""L3.5 - Failover: server pertama dimatikan -> client pindah ke server kedua."""
import unittest

import grpc
from _util import client_grpc, pb, server_grpc


class TestL35(unittest.TestCase):
    def test_failover(self):
        s1, p1, _ = server_grpc.buat_server(0, 4, prob_lambat=0.0)
        s2, p2, _ = server_grpc.buat_server(0, 4, prob_lambat=0.0)
        pesan = []
        cf = client_grpc.ClientFailover([f"localhost:{p1}", f"localhost:{p2}"], tampilkan=pesan.append)
        try:
            self.assertEqual(cf.panggil("GetMahasiswa", pb.MahasiswaRequest(nim="2023001")).nama, "Andi")
            self.assertEqual(cf.alamat_aktif, f"localhost:{p1}")
            s1.stop(0).wait()                                   # server 1 mati
            r = cf.panggil("GetMahasiswa", pb.MahasiswaRequest(nim="2023001"))
            self.assertEqual(r.nama, "Andi")
            self.assertEqual(cf.alamat_aktif, f"localhost:{p2}")
            self.assertEqual(len(cf.catatan), 1)
            with self.assertRaises(grpc.RpcError) as c:        # NOT_FOUND tidak memicu pindah
                cf.panggil("GetMahasiswa", pb.MahasiswaRequest(nim="0"))
            self.assertEqual(c.exception.code(), grpc.StatusCode.NOT_FOUND)
            self.assertEqual(len(cf.catatan), 1)
            s2.stop(0).wait()                                   # semua mati -> UNAVAILABLE
            with self.assertRaises(grpc.RpcError) as c:
                cf.panggil("GetMahasiswa", pb.MahasiswaRequest(nim="2023001"))
            self.assertEqual(c.exception.code(), grpc.StatusCode.UNAVAILABLE)
        finally:
            cf.tutup()
            s1.stop(0)
            s2.stop(0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
