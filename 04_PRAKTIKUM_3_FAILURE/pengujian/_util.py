"""Utilitas pengujian Praktikum 3: server in-process pada port bebas + reset state global."""
import os
import sys

import grpc

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import akademik_pb2 as pb              # noqa: E402,F401
import akademik_pb2_grpc as pb_grpc    # noqa: E402
import client_grpc                     # noqa: E402,F401
import server_grpc                     # noqa: E402


class ServerUji:
    def __init__(self, **opsi):
        server_grpc.reset_state()
        self.server, self.port, self.layanan = server_grpc.buat_server(0, opsi.pop("workers", 10), **opsi)
        self.channel = grpc.insecure_channel(f"localhost:{self.port}")
        self.stub = pb_grpc.LayananNilaiStub(self.channel)

    def tutup(self):
        self.channel.close()
        self.server.stop(0).wait()
