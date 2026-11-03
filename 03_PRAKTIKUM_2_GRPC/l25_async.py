"""
L2.5 - RPC asinkron: stub.GetMahasiswa.future(...) x 10 vs 10 pemanggilan serial.

Dua skenario diukur (keduanya diukur nyata, tidak ada angka rekaan):
  A. Server apa adanya (GetMahasiswa sangat cepat, hanya latensi jaringan lokal)
  B. Server dengan latensi buatan 100 ms per GetMahasiswa (mensimulasikan layanan
     yang butuh waktu, mis. query database) -> keuntungan asinkron terlihat jelas.
Skenario B ditandai SIMULASI di semua keluaran.

Menjalankan:
    python l25_async.py                     # server di-start otomatis (in-process)
    python l25_async.py --alamat localhost:50051   # ukur server yang sudah berjalan
"""
import argparse
import os
import time

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc
import server_grpc

DIR_HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil_pengujian")
JUMLAH = 10
NIM_BERGANTIAN = ["2023001", "2023002"]


def serial(stub, daftar_nim):
    mulai = time.perf_counter()
    hasil = [stub.GetMahasiswa(pb.MahasiswaRequest(nim=n)) for n in daftar_nim]
    return time.perf_counter() - mulai, hasil


def asinkron(stub, daftar_nim):
    mulai = time.perf_counter()
    futures = [stub.GetMahasiswa.future(pb.MahasiswaRequest(nim=n)) for n in daftar_nim]  # kirim semua
    hasil, galat = [], []
    for i, f in enumerate(futures):
        try:
            hasil.append(f.result(timeout=10))       # blokir hanya saat hasil diambil
        except grpc.RpcError as e:
            galat.append((i, e.code(), e.details()))
    return time.perf_counter() - mulai, hasil, galat


def bandingkan(stub, label):
    daftar = [NIM_BERGANTIAN[i % 2] for i in range(JUMLAH)]
    stub.GetMahasiswa(pb.MahasiswaRequest(nim="2023001"))        # warm-up (tidak dihitung)
    t_serial, h_serial = serial(stub, daftar)
    t_async, h_async, galat = asinkron(stub, daftar)
    sama = [m.SerializeToString() for m in h_serial] == [m.SerializeToString() for m in h_async]
    print(f"\n[{label}]  {JUMLAH} permintaan")
    print(f"  serial    : {t_serial * 1000:9.2f} ms")
    print(f"  asinkron  : {t_async * 1000:9.2f} ms   (galat: {len(galat)})")
    print(f"  speedup   : {t_serial / t_async:6.2f}x   hasil identik: {sama}")
    return label, t_serial, t_async, t_serial / t_async, sama


def demo_galat(stub):
    """Satu dari beberapa future berisi NIM salah -> RpcError ditangkap per-future."""
    nim = ["2023001", "9999", "2023002"]
    t, hasil, galat = asinkron(stub, nim)
    print(f"\n[Penanganan RpcError] {len(hasil)} berhasil, galat: {galat}")
    return galat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alamat", default=None)
    a = ap.parse_args()
    baris = []
    if a.alamat:
        with grpc.insecure_channel(a.alamat) as ch:
            stub = pb_grpc.LayananNilaiStub(ch)
            baris.append(bandingkan(stub, f"Server di {a.alamat}"))
            demo_galat(stub)
    else:
        for label, jeda in [("A. server apa adanya", 0.0), ("B. SIMULASI latensi 100 ms/permintaan", 0.1)]:
            server, port, _ = server_grpc.buat_server(0, 10, jeda_get=jeda)
            try:
                with grpc.insecure_channel(f"localhost:{port}") as ch:
                    stub = pb_grpc.LayananNilaiStub(ch)
                    baris.append(bandingkan(stub, label))
                    if jeda == 0.0:
                        demo_galat(stub)
            finally:
                server.stop(0).wait()
    os.makedirs(DIR_HASIL, exist_ok=True)
    with open(os.path.join(DIR_HASIL, "L2_5_async.txt"), "w", encoding="utf-8") as f:
        f.write("| Skenario | Serial (ms) | Asinkron (ms) | Speedup | Hasil identik |\n|---|---:|---:|---:|---|\n")
        for label, ts, ta, sp, sama in baris:
            f.write(f"| {label} | {ts * 1000:.2f} | {ta * 1000:.2f} | {sp:.2f}x | {sama} |\n")


if __name__ == "__main__":
    main()
