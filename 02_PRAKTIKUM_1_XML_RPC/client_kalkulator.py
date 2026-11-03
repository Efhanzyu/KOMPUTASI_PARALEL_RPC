"""
Praktikum 1 - Client XML-RPC Kalkulator.

Pemakaian (PowerShell):
    python client_kalkulator.py                 -> server di localhost:8000, verbose=True
    python client_kalkulator.py 192.168.1.10    -> server di komputer lain
    python client_kalkulator.py localhost --tenang   -> tanpa dump XML (verbose=False)

Client ini menguji seluruh method, termasuk L1.1 dan L1.2, dan memakai
penanganan error yang membedakan:
    - Fault          : kesalahan berasal dari FUNGSI di server (mis. bagi dengan nol)
    - ProtocolError  : server menjawab HTTP tetapi status bukan 200 (mis. 404)
    - Error jaringan : server mati / tidak terjangkau (ConnectionRefusedError, dst.)
"""
import http.client
import sys
import xmlrpc.client


def buat_proxy(host="localhost", port=8000, verbose=True, timeout=None):
    """Membuat ServerProxy. verbose=True mencetak HTTP request/response + XML."""
    url = f"http://{host}:{port}/"
    transport = xmlrpc.client.Transport()
    if timeout is not None:
        # Timeout socket supaya client tidak menggantung bila server tidak merespons.
        class _TransportTimeout(xmlrpc.client.Transport):
            def make_connection(self, host_):
                conn = super().make_connection(host_)
                conn.timeout = timeout
                return conn
        transport = _TransportTimeout()
    return xmlrpc.client.ServerProxy(url, transport=transport,
                                     verbose=verbose, allow_none=True)


def panggil_aman(fungsi, *args):
    """
    Memanggil fungsi RPC dan MENGEMBALIKAN tuple (status, nilai/pesan).
    status: "OK" | "FAULT" | "PROTOKOL" | "JARINGAN" | "PROTOKOL_HTTP" | "LOKAL"
    Tidak pernah melempar exception ke pemanggil sehingga client tidak crash.
    """
    try:
        return "OK", fungsi(*args)
    except xmlrpc.client.Fault as e:
        # Error dari FUNGSI di server (server hidup, fungsi menolak input / tidak ada).
        return "FAULT", f"[Fault {e.faultCode}] {e.faultString}"
    except xmlrpc.client.ProtocolError as e:
        # Server hidup tetapi HTTP bukan 200 (mis. 404 salah path, 500).
        return "PROTOKOL", f"[ProtocolError {e.errcode}] {e.errmsg} ({e.url})"
    except ConnectionRefusedError as e:
        return "JARINGAN", f"[ConnectionRefusedError] Server tidak berjalan / port ditolak: {e}"
    except (ConnectionResetError, ConnectionAbortedError) as e:
        return "JARINGAN", f"[{type(e).__name__}] Koneksi diputus server: {e}"
    except (http.client.HTTPException, xmlrpc.client.ResponseError) as e:
        # Mis. RemoteDisconnected, BadStatusLine, IncompleteRead.
        return "PROTOKOL_HTTP", f"[{type(e).__name__}] Respons HTTP tidak lengkap: {e}"
    except OSError as e:
        # Induk dari error socket lain: timeout, host tidak ditemukan, network unreachable.
        return "JARINGAN", f"[{type(e).__name__}] Gagal berkomunikasi dengan server: {e}"
    except (OverflowError, TypeError, ValueError) as e:
        # Gagal marshalling di sisi client (mis. integer > 2^31-1, tipe tidak didukung).
        return "LOKAL", f"[{type(e).__name__}] Argumen tidak dapat dimarshalling: {e}"


def tampil(label, hasil):
    status, nilai = hasil
    print(f">>> {label}: {status} -> {nilai}")


def main():
    host = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "localhost"
    verbose = "--tenang" not in sys.argv
    proxy = buat_proxy(host, verbose=verbose)

    print("=== Program dasar ===")
    tampil("system.listMethods()", panggil_aman(proxy.system.listMethods))
    tampil("5 + 3", panggil_aman(proxy.tambah, 5, 3))
    tampil("4 x 7", panggil_aman(proxy.kali, 4, 7))
    tampil("10 / 4", panggil_aman(proxy.bagi, 10, 4))
    tampil("10 / 0 (harus Fault)", panggil_aman(proxy.bagi, 10, 0))

    print("\n=== L1.1 pangkat dan akar ===")
    tampil("2 ^ 3", panggil_aman(proxy.pangkat, 2, 3))
    tampil("3 ^ 4", panggil_aman(proxy.pangkat, 3, 4))
    tampil("akar(25)", panggil_aman(proxy.akar, 25))
    tampil("akar(81)", panggil_aman(proxy.akar, 81))
    tampil("akar(-4) (harus Fault)", panggil_aman(proxy.akar, -4))

    print("\n=== L1.2 statistik ===")
    tampil("statistik([10..50])", panggil_aman(proxy.statistik, [10, 20, 30, 40, 50]))
    tampil("statistik([]) (harus Fault)", panggil_aman(proxy.statistik, []))
    tampil("statistik([1,'a']) (harus Fault)", panggil_aman(proxy.statistik, [1, "a"]))


if __name__ == "__main__":
    main()
