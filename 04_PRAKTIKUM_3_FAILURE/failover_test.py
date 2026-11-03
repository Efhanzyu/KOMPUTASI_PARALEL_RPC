"""
L3.5 (Pengayaan) - Failover otomatis: server 1 (port 50051) dimatikan -> client pindah ke server 2 (50052).

Skrip ini menyalakan dua proses server sendiri, sehingga port 50051/50052 harus bebas.
Menjalankan:  python failover_test.py
Hasil        :  hasil_pengujian/L3_5_hasil.txt
"""
import os
import subprocess
import sys

import grpc

import akademik_pb2 as pb
from client_grpc import ClientFailover

BASE = os.path.dirname(os.path.abspath(__file__))
DIR_HASIL = os.path.join(BASE, "hasil_pengujian")
LOG = []


def cetak(teks):
    print(teks, flush=True)
    LOG.append(teks)


def start(port):
    proc = subprocess.Popen([sys.executable, os.path.join(BASE, "server_grpc.py"), "--port", str(port),
                             "--prob-lambat", "0"], cwd=BASE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with grpc.insecure_channel(f"localhost:{port}") as ch:
        grpc.channel_ready_future(ch).result(timeout=20)
    return proc


def main():
    s1 = s2 = None
    try:
        s1, s2 = start(50051), start(50052)
        cetak("Server 1 (50051) dan server 2 (50052) berjalan.")
        cf = ClientFailover(["localhost:50051", "localhost:50052"], tampilkan=cetak)
        r = cf.panggil("GetMahasiswa", pb.MahasiswaRequest(nim="2023001"))
        cetak(f"[1] Terhubung ke {cf.alamat_aktif}: {r.nama}, IPK {r.ipk}")
        cetak("[2] Mematikan server 1 ...")
        s1.terminate()
        s1.wait(timeout=10)
        r = cf.panggil("GetMahasiswa", pb.MahasiswaRequest(nim="2023001"))
        cetak(f"[3] Setelah failover, dilayani oleh {cf.alamat_aktif}: {r.nama}, IPK {r.ipk}")
        r = cf.panggil("GetMahasiswa", pb.MahasiswaRequest(nim="2023002"))
        cetak(f"[4] Permintaan berikutnya tetap ke {cf.alamat_aktif}: {r.nama}, IPK {r.ipk}")
        # Kesalahan non-UNAVAILABLE tidak memicu failover
        try:
            cf.panggil("GetMahasiswa", pb.MahasiswaRequest(nim="9999"))
        except grpc.RpcError as e:
            cetak(f"[5] NIM salah -> {e.code().name} (BUKAN UNAVAILABLE, tidak pindah server; tetap {cf.alamat_aktif})")
        # Semua server mati -> error jelas, tanpa loop tak berujung
        s2.terminate()
        s2.wait(timeout=10)
        try:
            cf.panggil("GetMahasiswa", pb.MahasiswaRequest(nim="2023001"))
        except grpc.RpcError as e:
            cetak(f"[6] Semua server mati -> {e.code().name} dilempar ke pemanggil setelah mencoba semua server")
        cf.tutup()
        cetak(f"Riwayat pindah server: {cf.catatan}")
    finally:
        for p in (s1, s2):
            if p and p.poll() is None:
                p.terminate()
                p.wait(timeout=10)
    os.makedirs(DIR_HASIL, exist_ok=True)
    with open(os.path.join(DIR_HASIL, "L3_5_hasil.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
