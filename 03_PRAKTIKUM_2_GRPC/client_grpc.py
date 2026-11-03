"""
Praktikum 2 - Client gRPC.

Menjalankan (PowerShell, server sudah aktif di terminal lain):
    python client_grpc.py                      # demo dasar: unary + server streaming + error
    python client_grpc.py banyak               # L2.1 client streaming
    python client_grpc.py diskusi Andi         # L2.2 ruang diskusi interaktif (ketik pesan)
    python client_grpc.py diskusi Sari --otomatis   # kirim beberapa pesan otomatis
Opsi umum: --alamat localhost:50051
"""
import argparse
import sys
import threading
import time

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc


def demo_dasar(stub):
    mhs = stub.GetMahasiswa(pb.MahasiswaRequest(nim="2023001"))
    print(f"GetMahasiswa : {mhs.nama} - IPK {mhs.ipk} - prodi '{mhs.prodi}'")
    print("TambahNilai  :", stub.TambahNilai(
        pb.NilaiRequest(nim="2023001", matkul="Komputasi Paralel", nilai=88)).pesan)
    print("StreamNilai  :")
    for n in stub.StreamNilai(pb.MahasiswaRequest(nim="2023001")):
        print(f"   {n.matkul}: {n.nilai}")
    # Error handling: NOT_FOUND dan INVALID_ARGUMENT
    try:
        stub.GetMahasiswa(pb.MahasiswaRequest(nim="9999"))
    except grpc.RpcError as e:
        print("Error NIM salah   :", e.code(), "-", e.details())
    try:
        stub.TambahNilai(pb.NilaiRequest(nim="2023001", matkul="X", nilai=150))
    except grpc.RpcError as e:
        print("Error nilai 150   :", e.code(), "-", e.details())


def demo_banyak(stub):
    """L2.1 - client streaming: banyak NilaiRequest dalam satu RPC."""
    def hasilkan():
        for matkul, nilai in [("Aljabar", 80), ("Kalkulus", 75), ("Fisika", 90), ("Statistika", 88)]:
            print(f"  kirim {matkul}={nilai}")
            yield pb.NilaiRequest(nim="2023002", matkul=matkul, nilai=nilai)
    resp = stub.KirimBanyakNilai(hasilkan())
    print("Respons:", resp.sukses, "-", resp.pesan)


def demo_diskusi(stub, nama, otomatis):
    """L2.2 - bidirectional streaming. Satu thread mengirim, loop utama menerima."""
    selesai = threading.Event()

    def kirim():
        yield pb.Pesan(pengirim=nama, isi="halo semua!", waktu=int(time.time() * 1000))
        if otomatis:
            for i in range(1, 4):
                time.sleep(1.0)
                yield pb.Pesan(pengirim=nama, isi=f"pesan otomatis ke-{i}",
                               waktu=int(time.time() * 1000))
            time.sleep(2.0)           # tetap terhubung sebentar untuk menerima balasan
        else:
            print("(ketik pesan lalu Enter; ketik /keluar untuk selesai)")
            for baris in sys.stdin:
                baris = baris.strip()
                if baris == "/keluar":
                    break
                if baris:
                    yield pb.Pesan(pengirim=nama, isi=baris, waktu=int(time.time() * 1000))
        selesai.set()

    try:
        for masuk in stub.Diskusi(kirim()):
            print(f"[{masuk.pengirim}] {masuk.isi}")
    except grpc.RpcError as e:
        print("Koneksi diskusi terputus:", e.code(), "-", e.details())
    print("Keluar dari ruang diskusi.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("perintah", nargs="?", default="dasar", choices=["dasar", "banyak", "diskusi"])
    ap.add_argument("nama", nargs="?", default="Peserta")
    ap.add_argument("--alamat", default="localhost:50051")
    ap.add_argument("--otomatis", action="store_true")
    a = ap.parse_args()
    try:
        with grpc.insecure_channel(a.alamat) as channel:
            stub = pb_grpc.LayananNilaiStub(channel)
            if a.perintah == "dasar":
                demo_dasar(stub)
            elif a.perintah == "banyak":
                demo_banyak(stub)
            else:
                demo_diskusi(stub, a.nama, a.otomatis)
    except grpc.RpcError as e:
        print("Gagal memanggil server:", e.code(), "-", e.details())
        sys.exit(1)


if __name__ == "__main__":
    main()
