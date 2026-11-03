"""L3.3 - Race condition. Tanpa LOCK diuji dengan instrumentasi (jeda baca-tulis) agar interleaving terjadi."""
import unittest

from concurrency_test import jalankan  # noqa: E402  (BASE sudah ada di sys.path via _util)
import _util  # noqa: F401


class TestL33(unittest.TestCase):
    def test_dengan_lock_selalu_benar(self):
        for _ in range(3):
            h = jalankan(True, jeda_race=0.002)
            self.assertEqual((h["A"], h["B"], h["total"], h["transaksi"]), (500.0, 1000.0, 1500.0, 50))

    def test_tanpa_lock_menyimpang_dengan_instrumentasi(self):
        hasil = [jalankan(False, jeda_race=0.002) for _ in range(3)]
        menyimpang = [h for h in hasil if (h["A"], h["B"]) != (500.0, 1000.0)]
        self.assertGreaterEqual(len(menyimpang), 1, f"race tidak terlihat: {hasil}")

    def test_duplikat_bersamaan_dengan_lock_sekali(self):
        h = jalankan(True, jeda_race=0.01, n=10, id_sama=True)
        self.assertEqual(h["transaksi"], 1)
        self.assertEqual(h["A"], 990.0)

    def test_duplikat_bersamaan_tanpa_lock_lebih_dari_sekali(self):
        h = jalankan(False, jeda_race=0.01, n=10, id_sama=True)
        self.assertGreater(h["transaksi"], 1)          # deduplikasi bocor tanpa LOCK


if __name__ == "__main__":
    unittest.main(verbosity=2)
