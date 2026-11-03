"""
Praktikum 1 - Server XML-RPC Kalkulator (port 8000).

Menggunakan library bawaan Python: xmlrpc.server.
Fungsi yang disediakan:
    tambah(a, b), kali(a, b), bagi(a, b)          -> program dasar modul
    pangkat(a, b), akar(x)                        -> L1.1
    statistik(daftar)                             -> L1.2
    uji_datetime(waktu), uji_bilangan_besar(n)    -> L1.3

PENTING: setiap kali file ini diubah, server HARUS dihentikan (Ctrl+C) dan
dijalankan ulang. Error  'method "pangkat" is not supported'  muncul karena
server lama (tanpa fungsi pangkat) masih berjalan di port 8000.
"""
import math
import sys
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

HOST_DEFAULT = "0.0.0.0"   # 0.0.0.0 = dapat diakses dari komputer lain di jaringan
PORT_DEFAULT = 8000

# Kode Fault kustom agar client dapat membedakan jenis kesalahan fungsi server.
FAULT_BAGI_NOL = 1001
FAULT_AKAR_NEGATIF = 1002
FAULT_INPUT_TIDAK_VALID = 1003


# ----------------------------------------------------------------- program dasar
def tambah(a, b):
    return a + b


def kali(a, b):
    return a * b


def bagi(a, b):
    # Kesalahan dilaporkan sebagai XML-RPC Fault (bukan crash server).
    if b == 0:
        raise xmlrpc.client.Fault(FAULT_BAGI_NOL, "Pembagian dengan nol")
    return a / b


# ----------------------------------------------------------------- L1.1
def pangkat(a, b):
    """a pangkat b. Contoh: pangkat(2, 3) = 8."""
    try:
        return a ** b
    except (OverflowError, ZeroDivisionError) as e:
        raise xmlrpc.client.Fault(FAULT_INPUT_TIDAK_VALID, f"pangkat gagal: {e}")


def akar(x):
    """Akar kuadrat x. Bilangan negatif ditolak dengan Fault."""
    if x < 0:
        raise xmlrpc.client.Fault(FAULT_AKAR_NEGATIF,
                                  f"Akar bilangan negatif ({x}) tidak didefinisikan")
    hasil = math.sqrt(x)
    # Agar akar(25) menghasilkan 5 (int) dan bukan 5.0 bila hasilnya bulat.
    return int(hasil) if hasil.is_integer() else hasil


# ----------------------------------------------------------------- L1.2
def statistik(daftar):
    """Menerima list angka, mengembalikan dict {min, max, rata2}."""
    if not isinstance(daftar, list):
        raise xmlrpc.client.Fault(FAULT_INPUT_TIDAK_VALID, "Input harus berupa list")
    if len(daftar) == 0:
        raise xmlrpc.client.Fault(FAULT_INPUT_TIDAK_VALID, "List tidak boleh kosong")
    for x in daftar:
        # bool adalah subclass int di Python, tolak secara eksplisit
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise xmlrpc.client.Fault(FAULT_INPUT_TIDAK_VALID,
                                      f"Elemen tidak valid (bukan angka): {x!r}")
    rata2 = sum(daftar) / len(daftar)
    if float(rata2).is_integer():
        rata2 = int(rata2)
    return {"min": min(daftar), "max": max(daftar), "rata2": rata2}


# ----------------------------------------------------------------- L1.3
def uji_datetime(waktu):
    """Melaporkan tipe objek yang DITERIMA server setelah unmarshalling."""
    return {
        "tipe_diterima": type(waktu).__name__,
        "nilai_diterima": str(waktu),
    }


def uji_bilangan_besar(n):
    """Melaporkan tipe dan nilai bilangan yang diterima server."""
    return {"tipe_diterima": type(n).__name__, "nilai_diterima": str(n)}


def uji_kembalikan_besar(n):
    """Server MENGEMBALIKAN bilangan besar (marshalling terjadi di sisi server)."""
    return n


def uji_kembalikan_besar_string(n):
    """Solusi alternatif: bilangan besar dikirim sebagai string."""
    return str(int(n))


def uji_echo(x):
    """Mengembalikan argumen apa adanya (untuk menguji marshalling)."""
    return x


FUNGSI_TERDAFTAR = [
    tambah, kali, bagi, pangkat, akar, statistik,
    uji_datetime, uji_bilangan_besar, uji_kembalikan_besar,
    uji_kembalikan_besar_string, uji_echo,
]


class _Handler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/", "/RPC2")


def buat_server(host=HOST_DEFAULT, port=PORT_DEFAULT, log_requests=True):
    """Membuat server dan mendaftarkan seluruh fungsi (dipakai juga oleh unit test)."""
    server = SimpleXMLRPCServer((host, port), requestHandler=_Handler,
                                allow_none=True, logRequests=log_requests)
    server.register_introspection_functions()   # system.listMethods, dst.
    for fungsi in FUNGSI_TERDAFTAR:
        server.register_function(fungsi, fungsi.__name__)
    return server


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT_DEFAULT
    server = buat_server(port=port)
    print(f"Server XML-RPC berjalan di port {port}...")
    print("Method terdaftar:", ", ".join(sorted(f.__name__ for f in FUNGSI_TERDAFTAR)))
    print("Tekan Ctrl+C untuk berhenti.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
