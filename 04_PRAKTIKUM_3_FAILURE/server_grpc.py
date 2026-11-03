"""
Praktikum 3 - Server gRPC dengan RPC Transfer (deduplikasi request_id, respons lambat acak).

Menjalankan (PowerShell, folder 04_PRAKTIKUM_3_FAILURE):
    python server_grpc.py                              # port 50051, max_workers=10, respons lambat 30%
    python server_grpc.py --port 50052 --workers 4
    python server_grpc.py --jeda-get 0.1 --workers 1   # eksperimen throughput L3.4
    python server_grpc.py --tanpa-lock                 # eksperimen race condition L3.3

State (sesuai modul) disimpan sebagai variabel global di memori:
    SALDO  : saldo akun
    PROSES : request_id -> StatusResponse yang sudah dikirim (untuk deduplikasi)
    LOCK   : melindungi pemeriksaan PROSES + perubahan SALDO
"""
import argparse
import contextlib
import random
import threading
import time
from concurrent import futures

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc

DATA = {
    "2023001": {"nama": "Andi", "nilai": {"Basis Data": 85.0, "Jaringan": 78.0}},
    "2023002": {"nama": "Sari", "nilai": {"Basis Data": 92.0}},
}

SALDO_AWAL = {"A": 1000.0, "B": 500.0}
SALDO = dict(SALDO_AWAL)
PROSES = {}                    # request_id -> StatusResponse yang sudah dikirim
LOCK = threading.Lock()
STAT = {"eksekusi": 0, "duplikat": 0}   # eksekusi = berapa kali transfer BENAR-BENAR mengubah saldo


def reset_state():
    """Mengembalikan saldo dan PROSES ke keadaan awal (dipakai antar-pengujian)."""
    with LOCK:
        SALDO.clear()
        SALDO.update(SALDO_AWAL)
        PROSES.clear()
        STAT["eksekusi"] = 0
        STAT["duplikat"] = 0


class LayananNilai(pb_grpc.LayananNilaiServicer):
    def __init__(self, pakai_lock=True, prob_lambat=0.3, durasi_lambat=3.0,
                 jeda_get=0.0, jeda_race=0.0):
        self.pakai_lock = pakai_lock        # False = sama dengan menghapus "with LOCK:" (L3.3)
        self.prob_lambat = prob_lambat      # peluang respons lambat (modul: 0.3)
        self.durasi_lambat = durasi_lambat  # lama tidur (modul: 3 detik)
        self.jeda_get = jeda_get            # sleep di GetMahasiswa (L3.4: 0.1)
        self.jeda_race = jeda_race          # instrumentasi TAMBAHAN untuk L3.3 (default 0 = tidak aktif)

    # ------------------------------------------------------------ RPC dari Praktikum 2
    def GetMahasiswa(self, request, context):
        if self.jeda_get:
            time.sleep(self.jeda_get)
        mhs = DATA.get(request.nim)
        if mhs is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"NIM {request.nim} tidak ditemukan")
        daftar = list(mhs["nilai"].values())
        ipk = sum(daftar) / len(daftar) / 25 if daftar else 0.0
        return pb.Mahasiswa(nim=request.nim, nama=mhs["nama"], ipk=round(ipk, 2))

    def TambahNilai(self, request, context):
        if not 0 <= request.nilai <= 100:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Nilai harus 0-100")
        mhs = DATA.setdefault(request.nim, {"nama": "(baru)", "nilai": {}})
        mhs["nilai"][request.matkul] = request.nilai
        return pb.StatusResponse(sukses=True, pesan="Nilai tersimpan")

    def StreamNilai(self, request, context):
        mhs = DATA.get(request.nim)
        if mhs is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "NIM tidak ditemukan")
        for matkul, nilai in dict(mhs["nilai"]).items():
            yield pb.Nilai(matkul=matkul, nilai=nilai)
            time.sleep(0.5)

    # ------------------------------------------------------------ P3: Transfer
    def _pindahkan(self, dari, ke, jumlah):
        """Mengubah saldo. Dengan jeda_race > 0 dipakai bentuk baca-tunda-tulis (instrumentasi)."""
        if self.jeda_race:
            a = SALDO[dari]
            time.sleep(self.jeda_race)       # beri kesempatan thread lain menyela (interleaving)
            SALDO[dari] = a - jumlah
            b = SALDO[ke]
            time.sleep(self.jeda_race)
            SALDO[ke] = b + jumlah
        else:
            SALDO[dari] -= jumlah            # bentuk asli modul (baca-ubah-tulis, tidak atomik)
            SALDO[ke] += jumlah

    def Transfer(self, request, context):
        # Kesalahan bisnis PERMANEN -> status gRPC non-retryable (client tidak akan mengulang)
        if not request.request_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "request_id wajib diisi")
        if not request.jumlah > 0:           # juga menolak NaN
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "jumlah harus > 0")
        if request.dari not in SALDO or request.ke not in SALDO:
            context.abort(grpc.StatusCode.NOT_FOUND, "akun tidak ditemukan")
        if request.dari == request.ke:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "akun asal dan tujuan sama")

        kunci = LOCK if self.pakai_lock else contextlib.nullcontext()
        with kunci:                          # <- baris yang "dihapus" pada L3.3 (tanpa LOCK)
            if request.request_id in PROSES:         # permintaan duplikat -> hasil lama
                STAT["duplikat"] += 1
                return PROSES[request.request_id]
            if SALDO[request.dari] < request.jumlah:
                hasil = pb.StatusResponse(sukses=False, pesan="Saldo tidak cukup")
            else:
                self._pindahkan(request.dari, request.ke, request.jumlah)
                STAT["eksekusi"] += 1
                hasil = pb.StatusResponse(sukses=True, pesan=f"Saldo kini {SALDO}")
            PROSES[request.request_id] = hasil

        # Di LUAR lock dan SETELAH transaksi tersimpan: balasan terlambat, transfer SUDAH terjadi.
        if random.random() < self.prob_lambat:
            time.sleep(self.durasi_lambat)
        return hasil


def buat_server(port=50051, max_workers=10, host="[::]", **opsi_layanan):
    """Membuat dan menjalankan server. port=0 -> port bebas. Mengembalikan (server, port, layanan)."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers),
                         options=[("grpc.so_reuseport", 0)])   # bind ganda harus gagal
    layanan = LayananNilai(**opsi_layanan)
    pb_grpc.add_LayananNilaiServicer_to_server(layanan, server)
    port_nyata = server.add_insecure_port(f"{host}:{port}")
    if port_nyata == 0:
        raise RuntimeError(f"Gagal bind ke port {port}")
    server.start()
    return server, port_nyata, layanan


def main():
    ap = argparse.ArgumentParser(description="Server gRPC Praktikum 3")
    ap.add_argument("--port", type=int, default=50051)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--prob-lambat", type=float, default=0.3)
    ap.add_argument("--durasi-lambat", type=float, default=3.0)
    ap.add_argument("--jeda-get", type=float, default=0.0)
    ap.add_argument("--jeda-race", type=float, default=0.0)
    ap.add_argument("--tanpa-lock", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args()
    if a.seed is not None:
        random.seed(a.seed)
    try:
        server, port, _ = buat_server(a.port, a.workers, pakai_lock=not a.tanpa_lock,
                                      prob_lambat=a.prob_lambat, durasi_lambat=a.durasi_lambat,
                                      jeda_get=a.jeda_get, jeda_race=a.jeda_race)
    except RuntimeError as e:
        print(f"GAGAL menjalankan server: {e}\nPort {a.port} kemungkinan sudah dipakai server lain.")
        raise SystemExit(1)
    print(f"Server gRPC P3 berjalan di port {port} (max_workers={a.workers}, "
          f"lock={'MATI' if a.tanpa_lock else 'aktif'}, respons lambat={a.prob_lambat:.0%})", flush=True)
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print(f"\nServer dihentikan. SALDO akhir={SALDO}, eksekusi={STAT['eksekusi']}, "
              f"duplikat ditolak={STAT['duplikat']}")
        server.stop(grace=1).wait()


if __name__ == "__main__":
    main()
