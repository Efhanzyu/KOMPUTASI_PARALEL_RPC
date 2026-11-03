"""
L1.4 - Perbandingan 100 pemanggilan tambah() lokal vs XML-RPC (time.perf_counter).

Penggunaan (PowerShell):
  # Komputer 1 (server):   python server_kalkulator.py
  # Komputer 2 (client):   python benchmark_l14.py --host 192.168.1.10 --label dua-komputer
  # Atau positional:       python benchmark_l14.py 192.168.1.10 dua-komputer
  # Uji satu komputer:     python benchmark_l14.py --host 127.0.0.1 --label satu-komputer
  # Mode mandiri (server uji internal):
  #                        python benchmark_l14.py --mandiri

PENTING:
Argumen label menandai jenis pengujian pada file hasil CSV.
Hasil dengan label satu-komputer / loopback BUKAN pengujian dua komputer yang diminta modul.
"""
import argparse
import csv
import os
import sys
import threading
import time
import xmlrpc.client

import server_kalkulator as sk

DIR_HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil_pengujian")
N_DEFAULT = 100


def tambah_lokal(a, b):
    return a + b


def ukur(fungsi, n=N_DEFAULT):
    mulai = time.perf_counter()
    for i in range(n):
        fungsi(i, 3)
    return time.perf_counter() - mulai


def jalankan(host, port, label, n=N_DEFAULT):
    target_host = "127.0.0.1" if host.lower() == "localhost" else host
    proxy = xmlrpc.client.ServerProxy(f"http://{target_host}:{port}/")
    proxy.tambah(1, 1)   # satu pemanggilan pemanasan (tidak dihitung) agar koneksi/TCP handshake siap

    waktu_lokal = ukur(tambah_lokal, n=n)
    waktu_rpc = ukur(proxy.tambah, n=n)
    rata_lokal, rata_rpc = waktu_lokal / n, waktu_rpc / n
    rasio = waktu_rpc / waktu_lokal if waktu_lokal > 0 else float("inf")

    baris = [
        ("Fungsi lokal", n, waktu_lokal, rata_lokal),
        ("XML-RPC", n, waktu_rpc, rata_rpc),
    ]
    print(f"\nPengujian: {label} (server {target_host}:{port})")
    print("| Jenis pemanggilan | Jumlah pemanggilan | Waktu total (s) | Waktu rata-rata (ms) |")
    print("|---|---:|---:|---:|")
    for nama, jml, tot, rata in baris:
        print(f"| {nama} | {jml} | {tot:.6f} | {rata * 1000:.6f} |")
    print(f"\nOverhead RPC = waktu RPC / waktu lokal = {waktu_rpc:.6f} / {waktu_lokal:.6f}"
          f" = {rasio:,.1f} kali lebih lambat")
    print(f"Selisih rata-rata per panggilan = {(rata_rpc - rata_lokal) * 1000:.4f} ms")

    os.makedirs(DIR_HASIL, exist_ok=True)
    nama_file = os.path.join(DIR_HASIL, f"L1_4_benchmark_{label}.csv")
    with open(nama_file, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["jenis", "jumlah", "waktu_total_s", "waktu_rata2_ms", "host", "port", "label"])
        for nama, jml, tot, rata in baris:
            w.writerow([nama, jml, f"{tot:.6f}", f"{rata * 1000:.6f}", target_host, port, label])
        w.writerow(["rasio_rpc_per_lokal", "", f"{rasio:.2f}", "", target_host, port, label])
    print("Disimpan:", nama_file)
    return nama_file


def main():
    parser = argparse.ArgumentParser(description="L1.4 Benchmark Lokal vs XML-RPC")
    parser.add_argument("host_pos", nargs="?", default=None, help="Host server (posisional)")
    parser.add_argument("label_pos", nargs="?", default=None, help="Label hasil (posisional)")
    parser.add_argument("--host", default=None, help="Alamat host/IP server XML-RPC")
    parser.add_argument("--port", type=int, default=8000, help="Port server XML-RPC (default: 8000)")
    parser.add_argument("--label", default=None, help="Label pengujian (misal: satu-komputer / dua-komputer)")
    parser.add_argument("--jumlah", type=int, default=N_DEFAULT, help="Jumlah pemanggilan (default: 100)")
    parser.add_argument("--mandiri", action="store_true", help="Nyalakan server uji internal secara mandiri")
    args = parser.parse_args()

    if args.mandiri:
        server = sk.buat_server(host="127.0.0.1", port=0, log_requests=False)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            jalankan("127.0.0.1", port, "satu-komputer-loopback", n=args.jumlah)
        finally:
            server.shutdown()
            server.server_close()
        return

    host = args.host or args.host_pos or "127.0.0.1"
    label = args.label or args.label_pos
    if label is None:
        label = "satu-komputer" if host in ("127.0.0.1", "localhost") else "dua-komputer"

    jalankan(host, args.port, label, n=args.jumlah)


if __name__ == "__main__":
    main()
