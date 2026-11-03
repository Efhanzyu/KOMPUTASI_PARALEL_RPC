"""
L3.3 - Race condition: 50 transfer (10 dari A ke B) dari 10 thread client bersamaan,
dengan LOCK dan tanpa LOCK ("with LOCK:" dihapus = server dijalankan dengan pakai_lock=False).

Bagian 1 (PENGUJIAN DASAR, sesuai modul)  : tanpa instrumentasi, diulang beberapa kali.
Bagian 2 (PENGUJIAN TAMBAHAN, terpisah)   : jeda kecil antara BACA dan TULIS saldo di server
                                            untuk meningkatkan peluang interleaving.
Bagian 3 (PENGUJIAN TAMBAHAN, terpisah)   : 10 permintaan DUPLIKAT (request_id sama) bersamaan.

Target tanpa race: A = 500, B = 1000, total = 1500, 50 transaksi tereksekusi.
Race condition bergantung pada interleaving dan waktu eksekusi, jadi hasil dapat berbeda
tiap kali dijalankan; semua angka di bawah adalah hasil AKTUAL eksekusi ini.

Menjalankan:  python concurrency_test.py [--ulang 20]
"""
import argparse
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc
import server_grpc

DIR_HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil_pengujian")


def _satu_transfer(stub, rid):
    try:
        r = stub.Transfer(pb.TransferRequest(request_id=rid, dari="A", ke="B", jumlah=10.0), timeout=30)
        return "sukses" if r.sukses else "gagal"
    except grpc.RpcError:
        return "gagal"


def jalankan(pakai_lock, jeda_race=0.0, n=50, threads=10, id_sama=False):
    """Satu eksekusi: n transfer dari `threads` thread. Mengembalikan dict hasil dari sisi server."""
    server_grpc.reset_state()
    server, port, _ = server_grpc.buat_server(0, 16, pakai_lock=pakai_lock,
                                              prob_lambat=0.0, jeda_race=jeda_race)
    try:
        with grpc.insecure_channel(f"localhost:{port}") as ch:
            stub = pb_grpc.LayananNilaiStub(ch)
            ids = [("sama" if id_sama else str(uuid.uuid4())) for _ in range(n)]
            with ThreadPoolExecutor(max_workers=threads) as pool:
                hasil = list(pool.map(lambda rid: _satu_transfer(stub, rid), ids))
        saldo = dict(server_grpc.SALDO)
        eksekusi = server_grpc.STAT["eksekusi"]
        id_unik = len(server_grpc.PROSES)
    finally:
        server.stop(0).wait()
    return {"A": saldo["A"], "B": saldo["B"], "total": saldo["A"] + saldo["B"],
            "transaksi": eksekusi, "id_unik": id_unik,
            "sukses": hasil.count("sukses"), "gagal": hasil.count("gagal")}


def ringkas(daftar, target_a=500.0):
    menyimpang = [h for h in daftar if h["total"] != 1500 or h["A"] != target_a or h["transaksi"] != 50]
    return len(daftar), len(menyimpang)


def baris(label, h):
    return (f"| {label} | {h['A']:.0f} | {h['B']:.0f} | {h['total']:.0f} | {h['transaksi']} | "
            f"{h['sukses']} | {h['gagal']} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ulang", type=int, default=20)
    a = ap.parse_args()
    out = ["# L3.3 Race condition (hasil aktual)", "",
           "Target tanpa race: A=500, B=1000, total=1500, transaksi=50.", ""]
    kepala = ["| Kondisi | Saldo A | Saldo B | Total | Transaksi dieksekusi | Sukses | Gagal |",
              "|---|---:|---:|---:|---:|---:|---:|"]

    # ---------------- Bagian 1: dasar
    out += ["## Bagian 1 - Pengujian dasar (sesuai modul, tanpa instrumentasi)", ""] + kepala
    h_lock = jalankan(True)
    h_tanpa = jalankan(False)
    out += [baris("DENGAN LOCK (1 eksekusi)", h_lock), baris("TANPA LOCK (1 eksekusi)", h_tanpa), ""]
    print("\n".join(out))
    runs_lock = [jalankan(True) for _ in range(a.ulang)]
    runs_tanpa = [jalankan(False) for _ in range(a.ulang)]
    n1, m1 = ringkas(runs_lock)
    n2, m2 = ringkas(runs_tanpa)
    out += [f"Pengulangan {a.ulang}x: DENGAN LOCK menyimpang {m1}/{n1} eksekusi; "
            f"TANPA LOCK menyimpang {m2}/{n2} eksekusi.", ""]
    print(out[-2])

    # ---------------- Bagian 2: instrumentasi
    out += ["## Bagian 2 - Pengujian TAMBAHAN (instrumentasi: jeda 2 ms antara baca dan tulis saldo)", ""] + kepala
    inst_tanpa = [jalankan(False, jeda_race=0.002) for _ in range(5)]
    inst_lock = [jalankan(True, jeda_race=0.002) for _ in range(5)]
    for i, h in enumerate(inst_tanpa, 1):
        out.append(baris(f"TANPA LOCK #{i}", h))
    for i, h in enumerate(inst_lock, 1):
        out.append(baris(f"DENGAN LOCK #{i}", h))
    n3, m3 = ringkas(inst_tanpa)
    n4, m4 = ringkas(inst_lock)
    out += ["", f"Instrumentasi: TANPA LOCK menyimpang {m3}/{n3}; DENGAN LOCK menyimpang {m4}/{n4}.", ""]
    print(out[-2])

    # ---------------- Bagian 3: duplikat bersamaan
    out += ["## Bagian 3 - Pengujian TAMBAHAN: 10 permintaan DUPLIKAT (request_id sama) bersamaan", "",
            "Yang benar: transfer dieksekusi SATU kali (A=990). Jeda 10 ms disisipkan agar interleaving terjadi.", "",
            "| Kondisi | Saldo A | Saldo B | Transaksi dieksekusi |", "|---|---:|---:|---:|"]
    d_tanpa = jalankan(False, jeda_race=0.01, n=10, id_sama=True)
    d_lock = jalankan(True, jeda_race=0.01, n=10, id_sama=True)
    out += [f"| TANPA LOCK | {d_tanpa['A']:.0f} | {d_tanpa['B']:.0f} | {d_tanpa['transaksi']} |",
            f"| DENGAN LOCK | {d_lock['A']:.0f} | {d_lock['B']:.0f} | {d_lock['transaksi']} |"]
    print(out[-2]); print(out[-1])

    os.makedirs(DIR_HASIL, exist_ok=True)
    with open(os.path.join(DIR_HASIL, "L3_3_hasil.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\nDisimpan di hasil_pengujian/L3_3_hasil.md")


if __name__ == "__main__":
    main()
