"""L3.1 + deduplikasi: request ID tetap membuat retry aman (at-most-once)."""
import unittest

import grpc
from _util import ServerUji, client_grpc, pb, server_grpc


class TestL31(unittest.TestCase):
    def test_20_transfer_tanpa_lambat(self):
        s = ServerUji(prob_lambat=0.0)
        try:
            for _ in range(20):
                self.assertTrue(client_grpc.transfer_dengan_retry(s.stub, "A", "B", 10).sukses)
            self.assertEqual((server_grpc.SALDO["A"], server_grpc.SALDO["B"]), (800.0, 700.0))
            self.assertEqual(sum(server_grpc.SALDO.values()), 1500.0)
        finally:
            s.tutup()

    def test_id_sama_dieksekusi_sekali(self):
        s = ServerUji(prob_lambat=0.0)
        try:
            req = pb.TransferRequest(request_id="abc", dari="A", ke="B", jumlah=10)
            r1, r2 = s.stub.Transfer(req), s.stub.Transfer(req)
            self.assertEqual(r1, r2)                         # respons lama dikembalikan
            self.assertEqual(server_grpc.SALDO["A"], 990.0)  # hanya sekali
            self.assertEqual(server_grpc.STAT, {"eksekusi": 1, "duplikat": 1})
        finally:
            s.tutup()

    def test_timeout_lalu_retry_id_tetap(self):
        # Semua respons lambat: percobaan 1 timeout (transfer SUDAH terjadi), percobaan 2 -> dedup
        s = ServerUji(prob_lambat=1.0, durasi_lambat=3.0)
        try:
            jejak = []
            r = client_grpc.transfer_dengan_retry(s.stub, "A", "B", 10, maks=2, jejak=jejak,
                                                  tampilkan=lambda m: None)
            self.assertTrue(r.sukses)
            self.assertEqual([j[2] for j in jejak], ["DEADLINE_EXCEEDED", "OK"])
            self.assertEqual(len({j[1] for j in jejak}), 1)          # ID sama di semua percobaan
            self.assertEqual(server_grpc.SALDO["A"], 990.0)          # TIDAK ganda
        finally:
            s.tutup()

    def test_saldo_tidak_cukup_disimpan_dan_tidak_diubah(self):
        s = ServerUji(prob_lambat=0.0)
        try:
            req = pb.TransferRequest(request_id="besar", dari="B", ke="A", jumlah=9999)
            r = s.stub.Transfer(req)
            self.assertFalse(r.sukses)
            self.assertEqual(server_grpc.SALDO, {"A": 1000.0, "B": 500.0})
        finally:
            s.tutup()

    def test_kesalahan_permanen_tidak_diulang(self):
        s = ServerUji(prob_lambat=0.0)
        try:
            for dari, ke, jml, kode in [("A", "Z", 10, grpc.StatusCode.NOT_FOUND),
                                         ("A", "B", -5, grpc.StatusCode.INVALID_ARGUMENT),
                                         ("A", "A", 5, grpc.StatusCode.INVALID_ARGUMENT)]:
                jejak = []
                with self.assertRaises(grpc.RpcError) as c:
                    client_grpc.transfer_dengan_retry(s.stub, dari, ke, jml, jejak=jejak,
                                                      tampilkan=lambda m: None)
                self.assertEqual(c.exception.code(), kode)
                self.assertEqual(len(jejak), 1)                      # tepat 1 percobaan, tanpa retry
        finally:
            s.tutup()

    def test_request_id_kosong_ditolak(self):
        s = ServerUji(prob_lambat=0.0)
        try:
            with self.assertRaises(grpc.RpcError) as c:
                s.stub.Transfer(pb.TransferRequest(request_id="", dari="A", ke="B", jumlah=1))
            self.assertEqual(c.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)
        finally:
            s.tutup()

    def test_unavailable_diulang_lalu_menyerah(self):
        # Server tidak ada -> UNAVAILABLE diulang sampai maks, lalu dilempar
        with grpc.insecure_channel("localhost:1") as ch:
            stub = __import__("akademik_pb2_grpc").LayananNilaiStub(ch)
            pesan, jejak = [], []
            with self.assertRaises(grpc.RpcError) as c:
                client_grpc.transfer_dengan_retry(stub, "A", "B", 1, maks=2, timeout=1.0,
                                                  jejak=jejak, tampilkan=pesan.append)
            self.assertEqual(c.exception.code(), grpc.StatusCode.UNAVAILABLE)
            self.assertEqual(len(jejak), 2)
            self.assertIn("ulang dalam 0.5 s", pesan[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
