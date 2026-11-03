"""
L3.1 - 20 kali transfer 10 dari A ke B dengan request ID tetap (retry aman).

Server dijalankan in-process (alamat loopback, tetap lewat jaringan gRPC sungguhan) supaya saldo
dapat diverifikasi LANGSUNG dari sisi server (variabel SALDO di memori server).
Respons lambat acak 30% (3 detik) aktif sesuai modul; seed acak dapat diatur agar dapat diulang.

Menjalankan:  python transfer_test.py [--seed 42]
"""
import argparse
import os
import random
import time

import grpc

import akademik_pb2_grpc as pb_grpc
import client_grpc
import server_grpc

DIR_HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil_pengujian")


def jalankan(uuid_baru, seed, n=20, jumlah=10.0, prob_lambat=0.3, tampilkan=print):
    """Menjalankan n transfer berurutan. Mengembalikan dict hasil (diukur dari sisi server)."""
    server_grpc.reset_state()
    random.seed(seed)                                   # urutan respons lambat dapat diulang
    server, port, _ = server_grpc.buat_server(0, 10, prob_lambat=prob_lambat)
    saldo_awal = dict(server_grpc.SALDO)
    sukses = gagal = percobaan_total = 0
    mulai = time.perf_counter()
    try:
        with grpc.insecure_channel(f"localhost:{port}") as ch:
            stub = pb_grpc.LayananNilaiStub(ch)
            for i in range(1, n + 1):
                jejak = []
                try:
                    client_grpc.transfer_dengan_retry(stub, "A", "B", jumlah, jejak=jejak,
                                                      uuid_baru_tiap_percobaan=uuid_baru,
                                                      tampilkan=lambda m, i=i: tampilkan(f"  [transfer #{i:02d}] {m}"))
                    sukses += 1
                except grpc.RpcError as e:
                    gagal += 1
                    tampilkan(f"  [transfer #{i:02d}] GAGAL TOTAL setelah {len(jejak)} percobaan: {e.code().name}")
                percobaan_total += len(jejak)
        durasi = time.perf_counter() - mulai
        # ---- verifikasi dari SISI SERVER (membaca memori server langsung) ----
        saldo_akhir = dict(server_grpc.SALDO)
        stat = dict(server_grpc.STAT)
        id_diproses = len(server_grpc.PROSES)
    finally:
        server.stop(0).wait()
    return {
        "uuid_baru": uuid_baru, "seed": seed, "n": n, "jumlah": jumlah,
        "saldo_awal": saldo_awal, "saldo_akhir": saldo_akhir,
        "total_awal": sum(saldo_awal.values()), "total_akhir": sum(saldo_akhir.values()),
        "transfer_sukses_client": sukses, "transfer_gagal_client": gagal,
        "percobaan_rpc": percobaan_total, "eksekusi_server": stat["eksekusi"],
        "duplikat_ditolak": stat["duplikat"], "id_unik_di_server": id_diproses, "durasi_s": durasi,
    }


def tabel(h, harapan_a, harapan_b):
    status = "LULUS" if (h["saldo_akhir"]["A"] == harapan_a and h["saldo_akhir"]["B"] == harapan_b
                         and h["total_akhir"] == h["total_awal"]) else "TIDAK SESUAI TARGET"
    baris = [
        "| Besaran | Nilai |", "|---|---:|",
        f"| Saldo awal A / B / total | {h['saldo_awal']['A']:.0f} / {h['saldo_awal']['B']:.0f} / {h['total_awal']:.0f} |",
        f"| Jumlah transfer logis x nominal | {h['n']} x {h['jumlah']:.0f} |",
        f"| Transfer sukses / gagal (sisi client) | {h['transfer_sukses_client']} / {h['transfer_gagal_client']} |",
        f"| Total percobaan RPC (termasuk retry) | {h['percobaan_rpc']} |",
        f"| Transfer yang benar-benar dieksekusi server | {h['eksekusi_server']} |",
        f"| Duplikat ditolak oleh deduplikasi | {h['duplikat_ditolak']} |",
        f"| Saldo akhir A / B | {h['saldo_akhir']['A']:.0f} / {h['saldo_akhir']['B']:.0f} |",
        f"| Total saldo akhir | {h['total_akhir']:.0f} |",
        f"| Target (A / B / total) | {harapan_a:.0f} / {harapan_b:.0f} / {h['total_awal']:.0f} |",
        f"| Status pengujian | {status} |",
        f"| Durasi | {h['durasi_s']:.1f} s |",
    ]
    return "\n".join(baris), status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    print(f"=== L3.1 request ID TETAP (seed={a.seed}) ===")
    h = jalankan(False, a.seed)
    teks, status = tabel(h, 800.0, 700.0)
    print(teks)
    os.makedirs(DIR_HASIL, exist_ok=True)
    with open(os.path.join(DIR_HASIL, f"L3_1_hasil_seed{a.seed}.md"), "w", encoding="utf-8") as f:
        f.write(f"# L3.1 request ID tetap (seed={a.seed})\n\n{teks}\n")


if __name__ == "__main__":
    main()
