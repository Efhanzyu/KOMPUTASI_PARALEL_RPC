"""
Praktikum 2 - Server gRPC LayananNilai (port 50051, ThreadPoolExecutor max_workers=10).

RPC yang diimplementasikan:
    GetMahasiswa      unary
    TambahNilai       unary
    StreamNilai       server streaming   (jeda 0,5 detik per nilai)
    KirimBanyakNilai  client streaming   (L2.1)
    Diskusi           bidirectional      (L2.2, ruang diskusi multi-client)

Menjalankan (PowerShell, folder 03_PRAKTIKUM_2_GRPC):
    python server_grpc.py
    python server_grpc.py --port 50051 --workers 10
"""
import argparse
import copy
import queue
import threading
import time
from concurrent import futures

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc

# Data awal sesuai modul. Field "prodi" ditambahkan untuk L2.3 (agar server baru
# benar-benar mengirim field ke-4 yang tidak dikenal oleh client lama).
DATA_AWAL = {
    "2023001": {"nama": "Andi", "prodi": "Informatika",
                "nilai": {"Basis Data": 85.0, "Jaringan": 78.0}},
    "2023002": {"nama": "Sari", "prodi": "Sistem Informasi",
                "nilai": {"Basis Data": 92.0}},
}


def _nilai_valid(nilai):
    # "not 0 <= x <= 100" juga menolak NaN karena perbandingan dengan NaN selalu False
    return 0 <= nilai <= 100


class LayananNilai(pb_grpc.LayananNilaiServicer):
    def __init__(self, jeda_stream=0.5, jeda_get=0.0):
        self.data = copy.deepcopy(DATA_AWAL)   # state per-instance (memudahkan pengujian)
        self.lock = threading.Lock()           # melindungi self.data dari akses bersamaan
        self.jeda_stream = jeda_stream         # simulasi pengiriman bertahap (modul: 0,5 s)
        self.jeda_get = jeda_get               # latensi buatan GetMahasiswa (untuk eksperimen L2.5)
        # Ruang diskusi: queue milik tiap peserta -> nama peserta
        self.ruang = {}
        self.lock_ruang = threading.Lock()

    # ------------------------------------------------------------ unary
    def GetMahasiswa(self, request, context):
        if self.jeda_get:
            time.sleep(self.jeda_get)
        with self.lock:
            mhs = self.data.get(request.nim)
            if mhs is None:
                context.abort(grpc.StatusCode.NOT_FOUND, f"NIM {request.nim} tidak ditemukan")
            daftar = list(mhs["nilai"].values())
            nama, prodi = mhs["nama"], mhs.get("prodi", "")
        ipk = sum(daftar) / len(daftar) / 25 if daftar else 0.0   # konversi sederhana 0-100 -> 0-4
        return pb.Mahasiswa(nim=request.nim, nama=nama, ipk=round(ipk, 2), prodi=prodi)

    def TambahNilai(self, request, context):
        if not request.nim or not request.matkul:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "NIM dan matkul wajib diisi")
        if not _nilai_valid(request.nilai):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Nilai harus 0-100")
        with self.lock:
            mhs = self.data.setdefault(request.nim, {"nama": "(baru)", "prodi": "", "nilai": {}})
            mhs["nilai"][request.matkul] = request.nilai
        return pb.StatusResponse(sukses=True, pesan="Nilai tersimpan")

    # ------------------------------------------------------------ server streaming
    def StreamNilai(self, request, context):
        with self.lock:
            mhs = self.data.get(request.nim)
            salinan = dict(mhs["nilai"]) if mhs else None
        if salinan is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "NIM tidak ditemukan")
        for matkul, nilai in salinan.items():
            if not context.is_active():          # client sudah membatalkan -> berhenti
                return
            yield pb.Nilai(matkul=matkul, nilai=nilai)
            time.sleep(self.jeda_stream)         # simulasi data dikirim bertahap

    # ------------------------------------------------------------ L2.1 client streaming
    def KirimBanyakNilai(self, request_iterator, context):
        tersimpan = ditolak = 0
        for req in request_iterator:             # iterator berhenti saat client selesai mengirim
            if not req.nim or not req.matkul or not _nilai_valid(req.nilai):
                ditolak += 1                     # data tidak valid dilewati, tidak dihitung
                continue
            with self.lock:
                mhs = self.data.setdefault(req.nim, {"nama": "(baru)", "prodi": "", "nilai": {}})
                mhs["nilai"][req.matkul] = req.nilai
            tersimpan += 1
        pesan = f"{tersimpan} nilai tersimpan"
        if ditolak:
            pesan += f", {ditolak} ditolak (tidak valid)"
        return pb.StatusResponse(sukses=tersimpan > 0, pesan=pesan)

    # ------------------------------------------------------------ L2.2 bidirectional streaming
    def _siarkan(self, pesan, kecuali=None):
        """Mengirim pesan ke antrean semua peserta (kecuali pengirimnya)."""
        with self.lock_ruang:
            for antrean in list(self.ruang):
                if antrean is not kecuali:
                    antrean.put(pesan)

    @staticmethod
    def _pesan(pengirim, isi):
        return pb.Pesan(pengirim=pengirim, isi=isi, waktu=int(time.time() * 1000))

    def Diskusi(self, request_iterator, context):
        antrean = queue.Queue()                  # pesan yang menunggu dikirim ke client INI
        nama = {"nilai": None}

        def baca_dari_client():
            """Thread pembaca: menerima pesan client dan menyiarkannya ke peserta lain."""
            try:
                for pesan in request_iterator:
                    if nama["nilai"] is None:    # pesan pertama = bergabung ke ruang
                        nama["nilai"] = pesan.pengirim or "anonim"
                        with self.lock_ruang:
                            self.ruang[antrean] = nama["nilai"]
                        self._siarkan(self._pesan("server", f"{nama['nilai']} bergabung"), kecuali=antrean)
                        print(f"[diskusi] {nama['nilai']} bergabung")
                    print(f"[diskusi] {nama['nilai']}: {pesan.isi}")
                    self._siarkan(pesan, kecuali=antrean)
                    lain = max(len(self.ruang) - 1, 0)
                    antrean.put(self._pesan("server", f"pesan diterima, diteruskan ke {lain} peserta lain"))
            except grpc.RpcError:
                pass                              # client terputus mendadak
            finally:
                antrean.put(None)                 # sinyal: tutup stream

        threading.Thread(target=baca_dari_client, daemon=True).start()
        try:
            while True:
                try:
                    item = antrean.get(timeout=0.5)
                except queue.Empty:
                    if not context.is_active():  # client disconnect -> keluar
                        break
                    continue
                if item is None:
                    break
                yield item
        finally:                                  # dijalankan juga saat client putus / dibatalkan
            with self.lock_ruang:
                self.ruang.pop(antrean, None)
            if nama["nilai"]:
                self._siarkan(self._pesan("server", f"{nama['nilai']} keluar"))
                print(f"[diskusi] {nama['nilai']} keluar")


def buat_server(port=50051, max_workers=10, host="[::]", **opsi_layanan):
    """Membuat dan menjalankan server. port=0 -> port bebas. Mengembalikan (server, port, layanan)."""
    # grpc.so_reuseport=0: di Linux gRPC secara bawaan membolehkan DUA server memakai port
    # yang sama (SO_REUSEPORT). Dimatikan agar bind ganda langsung gagal, sama seperti Windows.
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers),
                         options=[("grpc.so_reuseport", 0)])
    layanan = LayananNilai(**opsi_layanan)
    pb_grpc.add_LayananNilaiServicer_to_server(layanan, server)
    port_nyata = server.add_insecure_port(f"{host}:{port}")
    if port_nyata == 0:
        raise RuntimeError(f"Gagal bind ke port {port} (mungkin sudah dipakai proses lain)")
    server.start()
    return server, port_nyata, layanan


def main():
    ap = argparse.ArgumentParser(description="Server gRPC LayananNilai")
    ap.add_argument("--port", type=int, default=50051)
    ap.add_argument("--workers", type=int, default=10)
    a = ap.parse_args()
    server, port, _ = buat_server(a.port, a.workers)
    print(f"Server gRPC berjalan di port {port} (max_workers={a.workers})...  Ctrl+C untuk berhenti")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nMenghentikan server...")
        server.stop(grace=1).wait()


if __name__ == "__main__":
    main()
