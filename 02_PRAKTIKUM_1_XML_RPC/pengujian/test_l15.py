"""L1.5 - Server mati saat client aktif: client harus melaporkan error, bukan crash."""
import socket
import threading
import unittest
import xmlrpc.client
from _util import ServerUji
from client_kalkulator import buat_proxy, panggil_aman


class TestL15(unittest.TestCase):
    def test_server_dimatikan_saat_client_aktif(self):
        s = ServerUji()
        proxy = buat_proxy("127.0.0.1", s.port, verbose=False, timeout=3)
        self.assertEqual(panggil_aman(proxy.tambah, 5, 3), ("OK", 8))   # server hidup
        s.berhenti()                                                     # server dimatikan
        status, pesan = panggil_aman(proxy.tambah, 5, 3)                 # panggil lagi
        print(f"\n  setelah server mati -> {status}: {pesan}")
        self.assertEqual(status, "JARINGAN")
        self.assertIn("ConnectionRefusedError", pesan)

    def test_fault_berbeda_dari_error_jaringan(self):
        s = ServerUji()
        try:
            proxy = buat_proxy("127.0.0.1", s.port, verbose=False)
            status, pesan = panggil_aman(proxy.bagi, 1, 0)
            self.assertEqual(status, "FAULT")                           # error FUNGSI server
            status, pesan = panggil_aman(proxy.fungsi_tidak_ada)
            self.assertEqual(status, "FAULT")
            self.assertIn("not supported", pesan)
        finally:
            s.berhenti()

    def test_protocol_error_path_salah(self):
        s = ServerUji()
        try:
            proxy = xmlrpc.client.ServerProxy(f"http://127.0.0.1:{s.port}/salah")
            status, pesan = panggil_aman(proxy.tambah, 1, 2)
            self.assertEqual(status, "PROTOKOL")
            self.assertIn("404", pesan)
        finally:
            s.berhenti()

    def test_koneksi_diputus_server(self):
        # Server palsu yang langsung menutup koneksi -> RemoteDisconnected (ConnectionResetError)
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]

        def tutup_langsung():
            # xmlrpc.client.Transport mengulang SATU kali jika RemoteDisconnected,
            # jadi server palsu harus menutup 2 koneksi berturut-turut.
            for _ in range(2):
                c, _ = srv.accept()
                c.recv(4096)
                c.close()
        threading.Thread(target=tutup_langsung, daemon=True).start()
        proxy = buat_proxy("127.0.0.1", port, verbose=False, timeout=3)
        status, pesan = panggil_aman(proxy.tambah, 1, 2)
        srv.close()
        print(f"\n  koneksi diputus -> {status}: {pesan}")
        self.assertEqual(status, "JARINGAN")
        self.assertTrue(
            any(k in pesan for k in ("ConnectionResetError", "ConnectionAbortedError", "RemoteDisconnected")),
            f"Pesan koneksi diputus tidak mengandung error koneksi yang diharapkan: {pesan}"
        )

    def test_argumen_tidak_bisa_dimarshalling(self):
        s = ServerUji()
        try:
            proxy = buat_proxy("127.0.0.1", s.port, verbose=False)
            status, pesan = panggil_aman(proxy.tambah, 2 ** 40, 1)
            self.assertEqual(status, "LOKAL")
        finally:
            s.berhenti()


if __name__ == "__main__":
    unittest.main(verbosity=2)
