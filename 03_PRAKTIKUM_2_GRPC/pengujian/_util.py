"""Utilitas pengujian Praktikum 2: server gRPC in-process pada port bebas."""
import os
import sys

import grpc

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import akademik_pb2 as pb              # noqa: E402
import akademik_pb2_grpc as pb_grpc    # noqa: E402
import server_grpc                     # noqa: E402


class ServerUji:
    def __init__(self, **opsi):
        self.server, self.port, self.layanan = server_grpc.buat_server(0, 10, **opsi)
        self.channel = grpc.insecure_channel(f"localhost:{self.port}")
        self.stub = pb_grpc.LayananNilaiStub(self.channel)

    def tutup(self):
        self.channel.close()
        self.server.stop(0).wait()
