"""
Analisis ukuran pesan XML-RPC untuk tambah(5, 3) - Praktikum 1 (pertanyaan analisis).

Cara kerja: client dihubungkan ke sebuah proxy TCP kecil yang meneruskan byte
persis apa adanya ke server dan MEREKAM byte mentah request dan response.
Dengan begitu ukuran yang dihitung adalah ukuran AKTUAL (bukan perkiraan), dan
body XML dapat dipisahkan dari header HTTP.

Menjalankan:  python analisis_xml.py
Keluaran   :  tabel di layar + hasil_pengujian/L1_analisis_xml.txt
"""
import os
import socket
import threading
import xmlrpc.client

import server_kalkulator as sk

DIR_HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil_pengujian")


class ProxyRekam:
    """Proxy TCP satu-arah-per-koneksi yang merekam request dan response mentah."""

    def __init__(self, port_tujuan):
        self.port_tujuan = port_tujuan
        self.request_mentah = b""
        self.response_mentah = b""
        self._srv = socket.socket()
        self._srv.bind(("127.0.0.1", 0))
        self._srv.listen(5)
        self.port = self._srv.getsockname()[1]
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    @staticmethod
    def _baca_http(sock):
        """Membaca satu pesan HTTP lengkap (header + body sesuai Content-Length)."""
        data = b""
        while b"\r\n\r\n" not in data:
            potongan = sock.recv(4096)
            if not potongan:
                return data
            data += potongan
        header, _, sisa = data.partition(b"\r\n\r\n")
        panjang = 0
        for baris in header.split(b"\r\n"):
            if baris.lower().startswith(b"content-length:"):
                panjang = int(baris.split(b":")[1])
        while len(sisa) < panjang:
            potongan = sock.recv(4096)
            if not potongan:
                break
            sisa += potongan
        return header + b"\r\n\r\n" + sisa

    def _loop(self):
        while True:
            try:
                klien, _ = self._srv.accept()
            except OSError:
                return
            try:
                self.request_mentah = self._baca_http(klien)
                with socket.create_connection(("127.0.0.1", self.port_tujuan)) as ke_server:
                    ke_server.sendall(self.request_mentah)
                    # Server (HTTP/1.0) menutup koneksi setelah menjawab -> baca sampai EOF.
                    jawaban = b""
                    while True:
                        potongan = ke_server.recv(4096)
                        if not potongan:
                            break
                        jawaban += potongan
                self.response_mentah = jawaban
                klien.sendall(jawaban)
            finally:
                klien.close()

    def tutup(self):
        self._srv.close()


def pisah(pesan_mentah):
    header, _, body = pesan_mentah.partition(b"\r\n\r\n")
    return header + b"\r\n\r\n", body


def ukur_tambah(a=5, b=3):
    """Mengembalikan dict berisi semua ukuran hasil pengukuran tambah(a, b)."""
    server = sk.buat_server(port=0, log_requests=False)
    port_server = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    proxy = ProxyRekam(port_server)
    try:
        hasil = xmlrpc.client.ServerProxy(f"http://127.0.0.1:{proxy.port}/").tambah(a, b)
    finally:
        proxy.tutup()
        server.shutdown()
        server.server_close()

    hdr_req, body_req = pisah(proxy.request_mentah)
    hdr_res, body_res = pisah(proxy.response_mentah)
    return {
        "hasil": hasil,
        "request_header": hdr_req, "request_body": body_req,
        "response_header": hdr_res, "response_body": body_res,
    }


def main():
    a, b = 5, 3
    d = ukur_tambah(a, b)
    body_req, body_res = d["request_body"], d["response_body"]
    n_hdr_req, n_hdr_res = len(d["request_header"]), len(d["response_header"])
    n_body_req, n_body_res = len(body_req), len(body_res)

    # DEFINISI "data sebenarnya": nilai yang dikirim, ditulis sebagai teks UTF-8
    # (karakter "5" dan "3" untuk request; "8" untuk response). Ini isi informasi
    # yang berubah antar pemanggilan; sisanya adalah struktur format (tag XML,
    # deklarasi XML, nama method).
    data_req = len(f"{a}{b}".encode("utf-8"))
    data_res = len(str(d["hasil"]).encode("utf-8"))
    # Definisi alternatif (pembanding): integer biner 32-bit (4 byte per angka)
    alt_req, alt_res = 4 * 2, 4 * 1

    def baris(nama, n_body, n_hdr, n_data, alt):
        ov = n_body - n_data
        return (nama, n_body, n_hdr, n_body + n_hdr, n_data, ov,
                100 * n_data / n_body, 100 * ov / n_body, alt, 100 * alt / n_body)

    tabel = [
        baris("Request  tambah(5,3)", n_body_req, n_hdr_req, data_req, alt_req),
        baris("Response (hasil 8)", n_body_res, n_hdr_res, data_res, alt_res),
    ]

    out = []
    out.append("=== Request XML (body, aktual) ===")
    out.append(body_req.decode("utf-8"))
    out.append("\n=== Response XML (body, aktual) ===")
    out.append(body_res.decode("utf-8"))
    out.append("\n=== Header HTTP request (aktual) ===")
    out.append(d["request_header"].decode("utf-8").rstrip())
    out.append("\n=== Header HTTP response (aktual) ===")
    out.append(d["response_header"].decode("utf-8").rstrip())
    out.append("\nRumus:")
    out.append("  persen_data     = data_sebenarnya / ukuran_body_XML x 100%")
    out.append("  persen_overhead = (ukuran_body_XML - data_sebenarnya) / ukuran_body_XML x 100%")
    out.append("\nDefinisi data sebenarnya: nilai argumen/hasil sebagai teks UTF-8 ('5','3' -> 2 byte; '8' -> 1 byte).\n")
    out.append(f"{'Pesan':22}{'Body XML':>9}{'Hdr HTTP':>9}{'Total':>7}{'Data':>6}{'Overhead':>9}{'%Data':>8}{'%Overhd':>9}")
    for t in tabel:
        out.append(f"{t[0]:22}{t[1]:>9}{t[2]:>9}{t[3]:>7}{t[4]:>6}{t[5]:>9}{t[6]:>7.2f}%{t[7]:>8.2f}%")
    out.append("\nSensitivitas (definisi alternatif: int32 biner = 4 byte per angka):")
    for t in tabel:
        out.append(f"  {t[0]:22} data={t[8]} byte -> {t[9]:.2f}% data, {100 - t[9]:.2f}% overhead (dari body XML)")
    teks = "\n".join(out)
    print(teks)
    os.makedirs(DIR_HASIL, exist_ok=True)
    with open(os.path.join(DIR_HASIL, "L1_analisis_xml.txt"), "w", encoding="utf-8") as f:
        f.write(teks + "\n")


if __name__ == "__main__":
    main()
