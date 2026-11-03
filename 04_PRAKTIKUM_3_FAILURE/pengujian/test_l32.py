"""L3.2 - UUID baru tiap percobaan -> transfer ganda (skenario deterministik)."""
import unittest

import grpc
from _util import ServerUji, client_grpc, server_grpc


class TestL32(unittest.TestCase):
    def test_uuid_baru_menyebabkan_transfer_ganda(self):
        # Semua respons lambat (3 s) dan timeout 2 s: tiap percobaan timeout padahal transfer TERJADI.
        s = ServerUji(prob_lambat=1.0, durasi_lambat=3.0)
        try:
            jejak = []
            with self.assertRaises(grpc.RpcError):
                client_grpc.transfer_dengan_retry(s.stub, "A", "B", 10, maks=2,
                                                  uuid_baru_tiap_percobaan=True, jejak=jejak,
                                                  tampilkan=lambda m: None)
            self.assertEqual(len({j[1] for j in jejak}), 2)             # 2 ID berbeda
            self.assertEqual(server_grpc.SALDO["A"], 980.0)             # didebit 2x untuk 1 transfer logis
            self.assertEqual(server_grpc.SALDO["B"], 520.0)
            self.assertEqual(sum(server_grpc.SALDO.values()), 1500.0)   # total tetap -> ganda tidak terlihat
            self.assertEqual(server_grpc.STAT["duplikat"], 0)
        finally:
            s.tutup()


if __name__ == "__main__":
    unittest.main(verbosity=2)
