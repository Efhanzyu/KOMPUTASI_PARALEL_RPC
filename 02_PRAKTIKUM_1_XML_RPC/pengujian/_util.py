"""Utilitas bersama untuk pengujian Praktikum 1: menyalakan server di thread (port bebas)."""
import os
import sys
import threading

# Agar 'import server_kalkulator' bekerja dari folder pengujian/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server_kalkulator as sk  # noqa: E402


class ServerUji:
    def __init__(self):
        self.server = sk.buat_server(host="127.0.0.1", port=0, log_requests=False)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def url(self):
        return f"http://127.0.0.1:{self.port}/"

    def berhenti(self):
        self.server.shutdown()
        self.server.server_close()
