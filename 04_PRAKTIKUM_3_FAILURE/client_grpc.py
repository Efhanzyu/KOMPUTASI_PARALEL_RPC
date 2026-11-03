"""
Praktikum 3 - Client gRPC dengan timeout, retry (exponential backoff), dan failover.

Menjalankan demo (server P3 sudah berjalan di terminal lain):
    python client_grpc.py                      # 1 transfer 10 dari A ke B, UUID tetap
    python client_grpc.py --uuid-baru          # versi L3.2 (UUID baru tiap percobaan - SALAH)
    python client_grpc.py --alamat localhost:50051
"""
import argparse
import time
import uuid

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc

# Hanya kegagalan SEMENTARA (jaringan/server lambat) yang boleh diulang.
STATUS_BISA_DIULANG = (grpc.StatusCode.DEADLINE_EXCEEDED, grpc.StatusCode.UNAVAILABLE)


def transfer_dengan_retry(stub, dari, ke, jumlah, maks=3, timeout=2.0,
                          uuid_baru_tiap_percobaan=False, jejak=None, tampilkan=print):
    """
    Mengirim Transfer dengan timeout dan retry.

    uuid_baru_tiap_percobaan=False (L3.1, BENAR) : satu request_id untuk semua percobaan.
    uuid_baru_tiap_percobaan=True  (L3.2, SALAH) : setiap percobaan membuat UUID baru, sehingga
                                                   server menganggapnya transaksi berbeda.
    jejak: list opsional; diisi (percobaan, request_id, hasil) untuk keperluan analisis/pengujian.
    Kesalahan permanen (NOT_FOUND, INVALID_ARGUMENT, ...) langsung dilempar ulang, TIDAK diulang.
    """
    rid = str(uuid.uuid4())                       # ID transaksi logis
    for percobaan in range(1, maks + 1):
        if uuid_baru_tiap_percobaan and percobaan > 1:
            rid = str(uuid.uuid4())               # (L3.2) ID baru -> dianggap permintaan baru
        try:
            req = pb.TransferRequest(request_id=rid, dari=dari, ke=ke, jumlah=jumlah)
            hasil = stub.Transfer(req, timeout=timeout)
            if jejak is not None:
                jejak.append((percobaan, rid, "OK"))
            return hasil
        except grpc.RpcError as e:
            if jejak is not None:
                jejak.append((percobaan, rid, e.code().name))
            bisa_ulang = e.code() in STATUS_BISA_DIULANG
            if not bisa_ulang or percobaan == maks:
                raise
            jeda = 0.5 * 2 ** (percobaan - 1)     # exponential backoff: 0,5 s, 1 s, 2 s ...
            tampilkan(f"Percobaan {percobaan} gagal ({e.code().name}), ulang dalam {jeda} s")
            time.sleep(jeda)


class ClientFailover:
    """
    L3.5 - Client yang berpindah ke server berikutnya bila server aktif UNAVAILABLE.
    Hanya dipakai untuk RPC idempoten (mis. GetMahasiswa): server-server ini TIDAK berbagi
    state (SALDO/PROSES), sehingga Transfer yang dialihkan tidak terlindungi deduplikasi.
    """

    def __init__(self, daftar_alamat, tampilkan=print):
        self.alamat = list(daftar_alamat)
        self.indeks = 0
        self.tampilkan = tampilkan
        self.catatan = []                    # riwayat pindah server
        self._buka()

    def _buka(self):
        self.channel = grpc.insecure_channel(self.alamat[self.indeks])
        self.stub = pb_grpc.LayananNilaiStub(self.channel)

    @property
    def alamat_aktif(self):
        return self.alamat[self.indeks]

    def panggil(self, nama_rpc, request, timeout=None):
        """Memanggil RPC unary; pada UNAVAILABLE coba server berikutnya (sekali putaran penuh)."""
        percobaan = 0
        while True:
            try:
                kwargs = {}
                if timeout is not None:
                    kwargs["timeout"] = timeout
                return getattr(self.stub, nama_rpc)(request, **kwargs)
            except grpc.RpcError as e:
                if (e.code() not in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED)) or percobaan >= len(self.alamat) - 1:
                    raise                      # bukan error jaringan/mati, atau semua server sudah dicoba
                lama = self.alamat_aktif
                self.channel.close()
                self.indeks = (self.indeks + 1) % len(self.alamat)
                self._buka()
                percobaan += 1
                pesan = f"{lama} UNAVAILABLE -> pindah ke {self.alamat_aktif}"
                self.catatan.append(pesan)
                self.tampilkan(pesan)

    def tutup(self):
        self.channel.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alamat", default="localhost:50051")
    ap.add_argument("--uuid-baru", action="store_true", help="L3.2: UUID baru di tiap percobaan")
    ap.add_argument("--jumlah", type=float, default=10)
    a = ap.parse_args()
    with grpc.insecure_channel(a.alamat) as channel:
        stub = pb_grpc.LayananNilaiStub(channel)
        try:
            hasil = transfer_dengan_retry(stub, "A", "B", a.jumlah,
                                          uuid_baru_tiap_percobaan=a.uuid_baru)
            print("Hasil:", hasil.sukses, hasil.pesan)
        except grpc.RpcError as e:
            print("Transfer GAGAL setelah semua percobaan:", e.code().name, "-", e.details())


if __name__ == "__main__":
    main()
