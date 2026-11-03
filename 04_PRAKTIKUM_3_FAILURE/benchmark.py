"""
L3.4 - Throughput dan latensi: 200 pemanggilan GetMahasiswa dari 20 thread client,
server dengan time.sleep(0.1) per permintaan, max_workers = 1, 4, 10.

Metodologi (agar adil dan dapat diulang):
  * Tiap konfigurasi memakai PROSES SERVER BARU (python server_grpc.py --workers N --jeda-get 0.1)
    pada port berbeda (50151-50153) sehingga tidak bentrok dengan server praktikum lain.
  * Pengukuran dimulai SETELAH server siap (channel_ready_future) dan setelah warm-up
    (20 panggilan, satu per thread client; tidak dihitung). Waktu start-up server TIDAK diukur.
  * 20 thread client, masing-masing memakai channel + stub sendiri (20 koneksi).
  * Latensi tiap request = waktu dari sebelum stub.GetMahasiswa() sampai respons diterima.
  * Throughput = jumlah permintaan BERHASIL / waktu total. Permintaan gagal dicatat terpisah.

Menjalankan:  python benchmark.py
Keluaran   :  hasil_pengujian/benchmark_results.csv dan benchmark_results.png
Catatan    :  grafik memerlukan matplotlib (pip install matplotlib).
"""
import csv
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc

BASE = os.path.dirname(os.path.abspath(__file__))
DIR_HASIL = os.path.join(BASE, "hasil_pengujian")
WORKERS = [1, 4, 10]
PORT_DASAR = 50151
JUMLAH_REQUEST = 200
JUMLAH_THREAD = 20
JEDA_SERVER = 0.1


def nyalakan_server(workers, port):
    proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE, "server_grpc.py"), "--port", str(port),
         "--workers", str(workers), "--jeda-get", str(JEDA_SERVER), "--prob-lambat", "0"],
        cwd=BASE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with grpc.insecure_channel(f"localhost:{port}") as ch:   # tunggu sampai server siap
        grpc.channel_ready_future(ch).result(timeout=20)
    return proc


def ukur(workers, port):
    proc = nyalakan_server(workers, port)
    lokal = threading.local()
    channels = []
    kunci = threading.Lock()

    def init_thread():
        ch = grpc.insecure_channel(f"localhost:{port}")
        with kunci:
            channels.append(ch)
        lokal.stub = pb_grpc.LayananNilaiStub(ch)

    def satu_panggilan(_):
        mulai = time.perf_counter()
        try:
            lokal.stub.GetMahasiswa(pb.MahasiswaRequest(nim="2023001"), timeout=120)
            return time.perf_counter() - mulai, True
        except grpc.RpcError:
            return time.perf_counter() - mulai, False

    try:
        with ThreadPoolExecutor(max_workers=JUMLAH_THREAD, initializer=init_thread) as pool:
            # Warm-up: 1 panggilan per thread, tidak dihitung
            list(pool.map(satu_panggilan, range(JUMLAH_THREAD)))
            # Pengukuran
            t0 = time.perf_counter()
            hasil = list(pool.map(satu_panggilan, range(JUMLAH_REQUEST)))
            total = time.perf_counter() - t0
    finally:
        for ch in channels:
            ch.close()
        proc.terminate()
        proc.wait(timeout=10)

    sukses = [l for l, ok in hasil if ok]
    gagal = len(hasil) - len(sukses)
    lat_ms = sorted(l * 1000 for l in sukses)
    return {
        "max_workers": workers,
        "waktu_total_s": total,
        "throughput_req_s": len(sukses) / total,
        "latensi_rata2_ms": sum(lat_ms) / len(lat_ms) if lat_ms else float("nan"),
        "latensi_min_ms": lat_ms[0] if lat_ms else float("nan"),
        "latensi_p95_ms": lat_ms[int(0.95 * (len(lat_ms) - 1))] if lat_ms else float("nan"),
        "latensi_maks_ms": lat_ms[-1] if lat_ms else float("nan"),
        "sukses": len(sukses), "gagal": gagal,
    }


def gambar(hasil, path_png):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib belum terpasang -> grafik dilewati. Jalankan: python -m pip install matplotlib")
        return False
    w = [str(h["max_workers"]) for h in hasil]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    ax1.bar(w, [h["throughput_req_s"] for h in hasil], color="#2f6fb0")
    ax1.set_xlabel("max_workers"); ax1.set_ylabel("Throughput (req/s)")
    ax1.set_title("max_workers vs throughput")
    for i, h in enumerate(hasil):
        ax1.text(i, h["throughput_req_s"], f"{h['throughput_req_s']:.1f}", ha="center", va="bottom")
    ax2.bar(w, [h["latensi_rata2_ms"] for h in hasil], color="#c0623a")
    ax2.set_xlabel("max_workers"); ax2.set_ylabel("Latensi rata-rata (ms)")
    ax2.set_title("max_workers vs latensi rata-rata")
    for i, h in enumerate(hasil):
        ax2.text(i, h["latensi_rata2_ms"], f"{h['latensi_rata2_ms']:.0f}", ha="center", va="bottom")
    fig.suptitle(f"{JUMLAH_REQUEST} GetMahasiswa, {JUMLAH_THREAD} thread client, sleep server {JEDA_SERVER} s")
    fig.tight_layout()
    fig.savefig(path_png, dpi=150)
    return True


def main():
    hasil = []
    for i, w in enumerate(WORKERS):
        print(f"Mengukur max_workers={w} ...", flush=True)
        h = ukur(w, PORT_DASAR + i)
        hasil.append(h)
        print(f"  total={h['waktu_total_s']:.3f}s throughput={h['throughput_req_s']:.2f} req/s "
              f"lat_rata2={h['latensi_rata2_ms']:.1f} ms sukses={h['sukses']} gagal={h['gagal']}", flush=True)
    os.makedirs(DIR_HASIL, exist_ok=True)
    csv_path = os.path.join(DIR_HASIL, "benchmark_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(hasil[0].keys()))
        w.writeheader()
        for h in hasil:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in h.items()})
    print("\n| max_workers | Waktu total (s) | Throughput (req/s) | Latensi rata-rata (ms) | Gagal |")
    print("|---|---:|---:|---:|---:|")
    for h in hasil:
        print(f"| {h['max_workers']} | {h['waktu_total_s']:.3f} | {h['throughput_req_s']:.2f} | "
              f"{h['latensi_rata2_ms']:.1f} | {h['gagal']} |")
    if gambar(hasil, os.path.join(DIR_HASIL, "benchmark_results.png")):
        print("Grafik disimpan: hasil_pengujian/benchmark_results.png")
    print("CSV disimpan   :", csv_path)


if __name__ == "__main__":
    main()
