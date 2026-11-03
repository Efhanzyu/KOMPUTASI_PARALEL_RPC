"""Praktikum 2 dasar + L2.1: unary, server streaming, client streaming."""
import time
import unittest

import grpc
from _util import ServerUji, pb


class TestDasarDanL21(unittest.TestCase):
    def setUp(self):
        self.s = ServerUji(jeda_stream=0.5)
        self.stub = self.s.stub

    def tearDown(self):
        self.s.tutup()

    # ---- unary
    def test_get_mahasiswa(self):
        m = self.stub.GetMahasiswa(pb.MahasiswaRequest(nim="2023001"))
        self.assertEqual((m.nama, m.ipk), ("Andi", 3.26))      # (85+78)/2/25
        m2 = self.stub.GetMahasiswa(pb.MahasiswaRequest(nim="2023002"))
        self.assertEqual((m2.nama, m2.ipk), ("Sari", 3.68))    # 92/25

    def test_get_not_found(self):
        with self.assertRaises(grpc.RpcError) as c:
            self.stub.GetMahasiswa(pb.MahasiswaRequest(nim="9999"))
        self.assertEqual(c.exception.code(), grpc.StatusCode.NOT_FOUND)

    def test_tambah_nilai_dan_invalid(self):
        r = self.stub.TambahNilai(pb.NilaiRequest(nim="2023001", matkul="Komputasi Paralel", nilai=88))
        self.assertTrue(r.sukses)
        for buruk in (-1, 101, float("nan")):
            with self.subTest(nilai=buruk):
                with self.assertRaises(grpc.RpcError) as c:
                    self.stub.TambahNilai(pb.NilaiRequest(nim="2023001", matkul="X", nilai=buruk))
                self.assertEqual(c.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)
        for batas in (0, 100):
            self.assertTrue(self.stub.TambahNilai(
                pb.NilaiRequest(nim="2023001", matkul=f"B{batas}", nilai=batas)).sukses)

    # ---- server streaming
    def test_stream_nilai_bertahap(self):
        mulai = time.perf_counter()
        waktu, hasil = [], []
        for n in self.stub.StreamNilai(pb.MahasiswaRequest(nim="2023001")):
            waktu.append(time.perf_counter() - mulai)
            hasil.append((n.matkul, n.nilai))
        self.assertEqual(hasil, [("Basis Data", 85.0), ("Jaringan", 78.0)])
        self.assertGreaterEqual(waktu[1] - waktu[0], 0.45)     # jeda ~0,5 detik antar-pesan

    def test_stream_not_found(self):
        with self.assertRaises(grpc.RpcError) as c:
            list(self.stub.StreamNilai(pb.MahasiswaRequest(nim="0000")))
        self.assertEqual(c.exception.code(), grpc.StatusCode.NOT_FOUND)

    # ---- L2.1 client streaming
    def _kirim(self, daftar):
        return self.stub.KirimBanyakNilai(iter(
            [pb.NilaiRequest(nim=n, matkul=m, nilai=v) for n, m, v in daftar]))

    def test_tiga_nilai(self):
        r = self._kirim([("2023001", "A", 70), ("2023001", "B", 80), ("2023002", "C", 90)])
        self.assertTrue(r.sukses)
        self.assertIn("3 nilai tersimpan", r.pesan)
        with self.s.layanan.lock:
            d = self.s.layanan.data
            self.assertEqual(d["2023001"]["nilai"]["A"], 70)
            self.assertEqual(d["2023001"]["nilai"]["B"], 80)
            self.assertEqual(d["2023002"]["nilai"]["C"], 90)

    def test_lebih_dari_tiga(self):
        data = [("2023001", f"MK{i}", 50 + i) for i in range(12)]
        r = self._kirim(data)
        self.assertIn("12 nilai tersimpan", r.pesan)
        self.assertEqual(sum(1 for k in self.s.layanan.data["2023001"]["nilai"] if k.startswith("MK")), 12)

    def test_hanya_data_valid_dihitung(self):
        r = self._kirim([("2023001", "ok1", 90), ("2023001", "buruk", 500),
                         ("2023001", "ok2", 60), ("2023001", "neg", -3)])
        self.assertIn("2 nilai tersimpan", r.pesan)
        self.assertIn("2 ditolak", r.pesan)
        self.assertNotIn("buruk", self.s.layanan.data["2023001"]["nilai"])

    def test_stream_kosong(self):
        r = self._kirim([])
        self.assertFalse(r.sukses)
        self.assertIn("0 nilai tersimpan", r.pesan)


if __name__ == "__main__":
    unittest.main(verbosity=2)
