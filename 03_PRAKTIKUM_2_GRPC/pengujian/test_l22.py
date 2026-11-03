"""L2.2 - Bidirectional streaming: ruang diskusi multi-client + penanganan disconnect."""
import queue
import threading
import time
import unittest

from _util import ServerUji, pb


class Peserta:
    """Client diskusi: antrean keluar (kirim) dan daftar pesan masuk (terima)."""

    def __init__(self, stub, nama):
        self.nama = nama
        self.keluar = queue.Queue()
        self.masuk = []
        self.call = stub.Diskusi(self._generator())
        self.thread = threading.Thread(target=self._terima, daemon=True)
        self.thread.start()

    def _generator(self):
        while True:
            pesan = self.keluar.get()
            if pesan is None:
                return
            yield pesan

    def _terima(self):
        try:
            for p in self.call:
                self.masuk.append((p.pengirim, p.isi))
        except Exception:
            pass

    def kirim(self, isi):
        self.keluar.put(pb.Pesan(pengirim=self.nama, isi=isi))

    def isi_masuk(self):
        return [f"{a}: {b}" for a, b in self.masuk]

    def tunggu(self, teks, detik=3):
        batas = time.time() + detik
        while time.time() < batas:
            if any(teks in x for x in self.isi_masuk()):
                return True
            time.sleep(0.05)
        return False


class TestL22(unittest.TestCase):
    def setUp(self):
        self.s = ServerUji()

    def tearDown(self):
        self.s.tutup()

    def test_dua_arah_satu_client(self):
        a = Peserta(self.s.stub, "Andi")
        a.kirim("halo")
        self.assertTrue(a.tunggu("pesan diterima"))    # server membalas lewat stream
        a.kirim("pesan kedua")                          # pertukaran berlanjut selama koneksi hidup
        batas = time.time() + 3
        while time.time() < batas and sum("pesan diterima" in x for x in a.isi_masuk()) < 2:
            time.sleep(0.05)
        self.assertEqual(sum("pesan diterima" in x for x in a.isi_masuk()), 2)
        a.keluar.put(None)

    def test_dua_client_saling_menerima(self):
        a = Peserta(self.s.stub, "Andi")
        a.kirim("andi di sini")
        self.assertTrue(a.tunggu("pesan diterima"))
        b = Peserta(self.s.stub, "Sari")
        b.kirim("sari di sini")
        self.assertTrue(a.tunggu("Sari bergabung"))     # A diberi tahu B masuk
        self.assertTrue(a.tunggu("Sari: sari di sini"))  # pesan B sampai ke A
        a.kirim("halo sari")
        self.assertTrue(b.tunggu("Andi: halo sari"))     # pesan A sampai ke B
        print("\n  Andi menerima :", a.isi_masuk())
        print("  Sari menerima :", b.isi_masuk())
        a.keluar.put(None)
        b.keluar.put(None)

    def test_tiga_client_broadcast(self):
        p = [Peserta(self.s.stub, n) for n in ("P1", "P2", "P3")]
        for x in p:
            x.kirim(f"hi dari {x.nama}")
            self.assertTrue(x.tunggu("pesan diterima"))
        time.sleep(0.3)
        p[0].kirim("siaran")
        self.assertTrue(p[1].tunggu("P1: siaran"))
        self.assertTrue(p[2].tunggu("P1: siaran"))
        for x in p:
            x.keluar.put(None)

    def test_client_disconnect_dibersihkan(self):
        a = Peserta(self.s.stub, "Andi")
        a.kirim("a")
        self.assertTrue(a.tunggu("pesan diterima"))
        b = Peserta(self.s.stub, "Sari")
        b.kirim("b")
        self.assertTrue(a.tunggu("Sari bergabung"))
        self.assertEqual(len(self.s.layanan.ruang), 2)
        b.call.cancel()                                  # Sari putus mendadak (cancel)
        self.assertTrue(a.tunggu("Sari keluar", detik=5))
        batas = time.time() + 3
        while time.time() < batas and len(self.s.layanan.ruang) != 1:
            time.sleep(0.05)
        self.assertEqual(len(self.s.layanan.ruang), 1)   # server tidak menyimpan peserta mati
        a.kirim("masih jalan?")                          # server masih sehat
        self.assertTrue(a.tunggu("pesan diterima"))
        a.keluar.put(None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
