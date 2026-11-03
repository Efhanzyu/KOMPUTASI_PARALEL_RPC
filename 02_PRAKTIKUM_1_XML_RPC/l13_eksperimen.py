"""
L1.3 - Mengirim objek datetime dan bilangan > 2^31 lewat XML-RPC.

Bagian A (PENGUJIAN ASLI)  : objek dikirim APA ADANYA, tanpa konversi, lalu hasil
                             aktual (sukses / exception) dicatat.
Bagian B (SOLUSI ALTERNATIF): hanya dijalankan sebagai pembanding, dipisahkan jelas
                             dari pengujian asli.

Server harus berjalan:  python server_kalkulator.py   (atau pakai --mandiri)
Menjalankan:  python l13_eksperimen.py            (server sudah jalan di localhost:8000)
              python l13_eksperimen.py --mandiri  (skrip menyalakan server sendiri)
"""
import datetime
import os
import sys
import threading
import xmlrpc.client

import server_kalkulator as sk

DIR_HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil_pengujian")
LOG = []


def cetak(teks=""):
    print(teks)
    LOG.append(teks)


def coba(label, fungsi, *args):
    """Memanggil fungsi RPC dan mencatat hasil / exception sebenarnya."""
    try:
        hasil = fungsi(*args)
        cetak(f"[SUKSES ] {label}\n          hasil = {hasil!r}")
        return "SUKSES", hasil
    except Exception as e:   # sengaja menangkap semua: tujuannya mencatat apa yang terjadi
        cetak(f"[GAGAL  ] {label}\n          {type(e).__name__}: {e}")
        return "GAGAL", e


def jalankan(proxy):
    batas = 2 ** 31
    cetak("=" * 70)
    cetak("BAGIAN A - PENGUJIAN ASLI (tanpa konversi)")
    cetak("=" * 70)
    cetak(f"Batas XML-RPC <int>/<i4> = 32-bit bertanda: -2^31 .. 2^31-1  "
          f"({-batas} .. {batas - 1})\n")

    cetak("-- A1. Objek datetime.datetime --")
    sekarang = datetime.datetime(2026, 11, 2, 13, 45, 30, 123456)
    coba(f"datetime dikirim ke server: {sekarang!r}", proxy.uji_datetime, sekarang)
    coba("datetime di-echo oleh server (server -> client)", proxy.uji_echo, sekarang)
    _, balik = coba("datetime dengan mikrodetik; bandingkan nilai balik",
                    proxy.uji_echo, sekarang)
    if isinstance(balik, xmlrpc.client.DateTime):
        cetak(f"          tipe balik = xmlrpc.client.DateTime, nilai = {balik}")
        cetak(f"          mikrodetik hilang? asli={sekarang.microsecond}us "
              f"(format XML hanya sampai detik)")
    cetak("")

    cetak("-- A2. Bilangan di batas 2^31 --")
    coba("2**31 - 1 (nilai int32 maksimum, masih di dalam batas)",
         proxy.uji_bilangan_besar, batas - 1)
    coba("2**31 (satu di atas batas)", proxy.uji_bilangan_besar, batas)
    coba("2**40", proxy.uji_bilangan_besar, 2 ** 40)
    coba("-(2**31) - 1 (satu di bawah batas negatif)",
         proxy.uji_bilangan_besar, -batas - 1)
    # Argumen kecil (2 dan 31) -> client lolos marshalling; HASIL 2**31 dikemas oleh SERVER.
    coba("pangkat(2, 31): server harus mengembalikan 2**31 (marshalling di server)",
         proxy.pangkat, 2, 31)
    coba("pangkat(2, 30): hasil 2**30 masih di dalam batas",
         proxy.pangkat, 2, 30)
    cetak("")

    cetak("=" * 70)
    cetak("BAGIAN B - SOLUSI ALTERNATIF (BUKAN pengujian asli)")
    cetak("=" * 70)
    cetak("-- B1. datetime -> string ISO 8601 (direkonstruksi kembali di client) --")
    iso = sekarang.isoformat()
    coba(f"kirim string ISO: {iso}", proxy.uji_echo, iso)
    cetak(f"          dikembalikan menjadi datetime di client: "
          f"{datetime.datetime.fromisoformat(iso)!r}")
    cetak("")
    cetak("-- B2. datetime dengan xmlrpc.client.DateTime (jenis resmi XML-RPC) --")
    coba("kirim xmlrpc.client.DateTime", proxy.uji_datetime,
         xmlrpc.client.DateTime(sekarang))
    cetak("")
    cetak("-- B3. Bilangan besar sebagai string --")
    besar = 2 ** 62
    coba(f"kirim str({besar})", proxy.uji_kembalikan_besar_string, str(besar))
    cetak("-- B4. Bilangan besar sebagai float (double 64-bit; presisi hanya 53 bit) --")
    coba("kirim float(2**40) = 1099511627776.0", proxy.uji_bilangan_besar, float(2 ** 40))
    coba("kirim float(2**62) kehilangan ketelitian?", proxy.uji_echo, float(2 ** 62 + 1))


def main():
    server = None
    if "--mandiri" in sys.argv:
        server = sk.buat_server(port=0, log_requests=False)
        port = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()
    else:
        port = 8000
    proxy = xmlrpc.client.ServerProxy(f"http://localhost:{port}/", allow_none=True)
    try:
        jalankan(proxy)
    finally:
        if server:
            server.shutdown()
            server.server_close()
    os.makedirs(DIR_HASIL, exist_ok=True)
    with open(os.path.join(DIR_HASIL, "L1_3_hasil.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
