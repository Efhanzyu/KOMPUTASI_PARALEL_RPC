"""L2.3 - Backward compatibility: client LAMA (stub tanpa prodi) vs server BARU (dengan prodi)."""
import os
import subprocess
import sys
import unittest

from _util import BASE, ServerUji, pb

DIR_LAMA = os.path.join(BASE, "client_lama")


class TestL23(unittest.TestCase):
    def test_client_lama_vs_server_baru(self):
        s = ServerUji()
        try:
            # Subprocess + cwd=client_lama => 'import akademik_pb2' memakai stub LAMA, bukan yang baru.
            r = subprocess.run([sys.executable, "client_lama.py", f"localhost:{s.port}"],
                               cwd=DIR_LAMA, capture_output=True, text=True, timeout=30)
        finally:
            s.tutup()
        print("\n" + r.stdout)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("['nim', 'nama', 'ipk']", r.stdout)           # benar-benar stub lama
        self.assertIn("BERHASIL: nim=2023001 nama=Andi ipk=3.26", r.stdout)
        self.assertIn("hasField prodi? False", r.stdout)            # client lama tidak mengenal prodi
        # Unknown field dipertahankan: bytes hasil serialisasi ulang oleh client lama masih memuat prodi
        hex_ulang = [b for b in r.stdout.splitlines() if b.startswith("bytes_ulang_hex:")][0].split(": ")[1]
        m = pb.Mahasiswa.FromString(bytes.fromhex(hex_ulang))
        self.assertEqual(m.prodi, "Informatika")

    def test_stub_lama_dan_baru_berbeda(self):
        with open(os.path.join(DIR_LAMA, "akademik_pb2.py"), encoding="utf-8") as f:
            lama = f.read()
        with open(os.path.join(BASE, "akademik_pb2.py"), encoding="utf-8") as f:
            baru = f.read()
        self.assertNotIn("prodi", lama)
        self.assertIn("prodi", baru)

    def test_stub_baru_membaca_pesan_lama(self):
        # Arah sebaliknya: pesan v1 (tanpa prodi) dibaca stub v2 -> prodi kosong (nilai default)
        v1_bytes = bytes.fromhex("0a07323032333030311204416e64691914ae47e17a140a40")
        m = pb.Mahasiswa.FromString(v1_bytes)
        self.assertEqual((m.nim, m.nama, m.prodi), ("2023001", "Andi", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
