"""
L1.5 - Demo manual: matikan server ketika client masih berjalan.

Terminal 1:  python server_kalkulator.py
Terminal 2:  python demo_l15_client.py
Lalu di Terminal 1 tekan Ctrl+C (server mati), amati pesan di Terminal 2,
kemudian jalankan server lagi dan lihat client pulih sendiri.
Client berhenti dengan Ctrl+C.
"""
import sys
import time

from client_kalkulator import buat_proxy, panggil_aman


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    proxy = buat_proxy(host, verbose=False, timeout=3)
    print("Client aktif. Memanggil tambah(5, 3) tiap 1 detik. Matikan server sekarang...")
    nomor = 0
    try:
        while True:
            nomor += 1
            status, nilai = panggil_aman(proxy.tambah, 5, 3)
            if status == "OK":
                print(f"#{nomor:03d} OK    tambah(5,3) = {nilai}")
            else:
                print(f"#{nomor:03d} {status:8} {nilai}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nClient dihentikan oleh pengguna (tidak ada crash).")


if __name__ == "__main__":
    main()
