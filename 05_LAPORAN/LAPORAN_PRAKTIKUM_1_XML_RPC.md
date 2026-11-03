# LAPORAN PRAKTIKUM REMOTE PROCEDURE CALLS (RPC) 1
## RPC Dasar dengan XML-RPC

| | |
|---|---|
| Nama | [ISI NAMA] |
| NIM | [ISI NIM] |
| Kelas | [ISI KELAS] |
| Mata kuliah | Komputasi Paralel dan Terdistribusi |
| Praktikum | RPC-1 (XML-RPC) |

---

## 1. Tujuan dan Dasar Teori Singkat

**Tujuan.** Membangun server kalkulator dan client XML-RPC, mengamati pesan XML yang dipertukarkan, menguji batas tipe data, mengukur overhead RPC dibanding pemanggilan lokal, dan menangani kegagalan server.

**Dasar teori.** RPC membuat pemanggilan fungsi di mesin lain tampak seperti pemanggilan lokal. Client memanggil *client stub*, yang melakukan *marshalling* (mengemas nama prosedur dan parameter menjadi pesan). Pesan dikirim lewat jaringan, *server stub* melakukan *unmarshalling* lalu memanggil prosedur asli, dan hasilnya kembali lewat jalur yang sama. XML-RPC memakai HTTP POST dengan badan XML (`<methodCall>` dan `<methodResponse>`). Kesalahan fungsi server dikirim sebagai `<fault>` (di Python menjadi `xmlrpc.client.Fault`), berbeda dari kesalahan jaringan yang muncul sebagai exception soket. Tipe `<int>`/`<i4>` XML-RPC adalah 32-bit bertanda. Server memakai `SimpleXMLRPCServer` dan `register_introspection_functions()` agar `system.listMethods()` tersedia.

## 2. Langkah Kerja dan Kode Program

Lingkungan Pengujian: Windows 11, PowerShell, Python 3.11.9, virtual environment (`venv`). Seluruh kode program, skrip pengujian, dan penanganan exception telah diverifikasi dan diaudit langsung pada lingkungan Windows lokal. Panduan eksekusi perintah Windows tersedia di `README.md` dan `PANDUAN_BENCHMARK_DUA_KOMPUTER.md`.

Kode lengkap: `server_kalkulator.py` dan `client_kalkulator.py` (folder `02_PRAKTIKUM_1_XML_RPC`).

**Program dasar.** Server mendaftarkan `tambah`, `kali`, `bagi` dengan `register_function`. `bagi(a, 0)` melempar `xmlrpc.client.Fault(1001, "Pembagian dengan nol")`. Client memakai `ServerProxy(..., verbose=True)`.

**Perbaikan error `method "pangkat" is not supported`.** Pesan ini adalah `Fault` dari server: fungsi `pangkat` tidak ada di tabel method server **yang sedang berjalan**. Penyebab paling mungkin adalah server lama (sebelum `pangkat` ditambahkan) masih hidup di port 8000. Perbaikan: (1) semua fungsi didaftarkan dari satu daftar `FUNGSI_TERDAFTAR` sehingga tidak ada yang terlewat; (2) server dihentikan (`Ctrl+C`) dan dijalankan ulang; (3) `test_l11.py::test_list_methods_lengkap` memastikan `tambah, kali, bagi, pangkat, akar, statistik` muncul di `system.listMethods()`. Saya tidak dapat melihat kode lama Anda, jadi penyebab pastinya di mesin Anda tidak terverifikasi; periksa dengan `system.listMethods()`.

### L1.1 Pangkat dan akar
Implementasi: `pangkat(a, b)` memakai `a ** b`; `akar(x)` memakai `math.sqrt` (hasil bulat dikembalikan sebagai `int`), bilangan negatif ditolak dengan `Fault(1002)`.

| Uji | Target | Hasil aktual |
|---|---|---|
| 2 pangkat 3 | 8 | 8 |
| 3 pangkat 4 | 81 | 81 |
| akar(25) | 5 | 5 |
| akar(81) | 9 | 9 |
| akar(-4) | Fault | `[Fault 1002] Akar bilangan negatif (-4) tidak didefinisikan` |

Analisis: error dikirim sebagai Fault sehingga server tidak crash dan client dapat membedakannya dari error jaringan. Temuan tambahan: `pangkat(2, 31)` menghasilkan `Fault 1: OverflowError: int exceeds XML-RPC limits`, karena *hasil* melebihi batas int 32-bit dan gagal dimarshalling di server (lihat L1.3).

[SCREENSHOT: L1_1_server.png]  [SCREENSHOT: L1_1_client.png]

### L1.2 Statistik
`statistik(daftar)` mengembalikan `{"min", "max", "rata2"}`. Input `[10, 20, 30, 40, 50]` menghasilkan `{'min': 10, 'max': 50, 'rata2': 30}` (sesuai target). Input kosong, bukan list, atau berisi elemen non-angka (termasuk `bool`) ditolak dengan `Fault 1003`.

**Marshalling list dan dictionary.** List menjadi `<array><data>` berisi `<value>` per elemen. Dictionary menjadi `<struct>` berisi `<member>`, masing-masing dengan `<name>` (kunci) dan `<value>`. Contoh respons aktual:

```xml
<value><struct>
<member>
<name>min</name>
<value><int>10</int></value>
</member>
<member>
<name>max</name>
<value><int>50</int></value>
</member>
<member>
<name>rata2</name>
<value><int>30</int></value>
</member>
</struct></value>
```

Pengujian: `test_l12.py` (5 test lulus).

[SCREENSHOT: L1_2_statistik.png]

### L1.3 Datetime dan bilangan besar
Berkas hasil: `hasil_pengujian/L1_3_hasil.txt`. **Pengujian asli** (tanpa konversi sebelumnya):

| Uji | Hasil aktual |
|---|---|
| `datetime(2026,11,2,13,45,30,123456)` dikirim | **Sukses.** Server menerima `xmlrpc.client.DateTime` bernilai `20261102T13:45:30` |
| datetime dikembalikan server | Sukses, tipe `xmlrpc.client.DateTime` (bukan `datetime`) |
| `2**31 - 1` | Sukses |
| `2**31`, `2**40`, `-(2**31) - 1` | **Gagal di client:** `OverflowError: int exceeds XML-RPC limits` |
| `pangkat(2, 31)` (hasil dikemas server) | **Gagal:** `Fault 1: OverflowError: int exceeds XML-RPC limits` |

Penjelasan. Datetime didukung lewat tipe `<dateTime.iso8601>`, tetapi formatnya hanya sampai detik sehingga **mikrodetik (123456) hilang**, dan objek yang diterima adalah `DateTime`, bukan `datetime.datetime`. Bilangan di luar rentang -2^31..2^31-1 ditolak *marshaller* Python karena `<int>` XML-RPC 32-bit; pengecekan terjadi di sisi pengirim sebelum pesan dikirim.

**Solusi alternatif (dipisahkan dari pengujian asli):** datetime dikirim sebagai string ISO 8601 (mikrodetik terjaga); bilangan besar dikirim sebagai string (`2**62` berhasil); `float` dapat membawa 2^40 tetapi hanya presisi 53 bit (`2**62+1` kehilangan ketelitian). Pengujian: `test_l13.py` (7 test lulus).

[SCREENSHOT: L1_3_datetime.png]

### L1.4 Pemanggilan lokal vs RPC
Skrip: `benchmark_l14.py` (100 panggilan, `time.perf_counter()`).

**Status uji dua komputer: BELUM DILAKUKAN.** Kode dan panduan (termasuk Windows Firewall) ada di `README.md`. Satu-satunya hasil aktual adalah **loopback satu komputer** (client dan server di mesin yang sama):

| Jenis pemanggilan | Jumlah pemanggilan | Waktu total | Waktu rata-rata |
|---|---:|---:|---:|
| Fungsi lokal | 100 | 0,000008 s | 0,000082 ms |
| XML-RPC (loopback) | 100 | 0,050920 s | 0,509196 ms |

Overhead: 0,050920 / 0,000008 ≈ 6.200 kali pada eksekusi ini (eksekusi lain memberi sekitar 3.800 kali). Waktu lokal sangat kecil sehingga rasionya sensitif terhadap derau; kesimpulan yang aman: satu panggilan RPC loopback memakan sekitar setengah milidetik, ribuan kali lebih lama daripada panggilan lokal. Pada dua komputer asli, latensi jaringan menambah waktu ini.

**Tabel dua komputer (isi setelah pengujian):**

| Jenis pemanggilan | Jumlah | Waktu total | Waktu rata-rata |
|---|---:|---:|---:|
| Fungsi lokal | 100 | [BELUM DILAKUKAN] | [BELUM DILAKUKAN] |
| XML-RPC (2 komputer) | 100 | [BELUM DILAKUKAN] | [BELUM DILAKUKAN] |

[SCREENSHOT: L1_4_benchmark.png]

### L1.5 Kegagalan server
Client memakai `panggil_aman()` yang membedakan jenis error:

| Kategori | Exception | Penyebab |
|---|---|---|
| FAULT | `xmlrpc.client.Fault` | Fungsi server menolak / method tidak ada (server hidup) |
| PROTOKOL | `xmlrpc.client.ProtocolError` | HTTP bukan 200 (mis. 404 karena path salah) |
| JARINGAN | `ConnectionRefusedError`, `ConnectionResetError`, `OSError` (timeout dll.) | Server mati / koneksi putus |
| PROTOKOL_HTTP | `http.client.HTTPException`, `ResponseError` | Respons HTTP tidak lengkap |
| LOKAL | `OverflowError`, `TypeError` | Argumen tak dapat dimarshalling |

Hasil aktual otomatis (`test_l15.py`, 5 test lulus): setelah server dimatikan, `tambah(5,3)` menghasilkan `[ConnectionRefusedError] Server tidak berjalan / port ditolak: [Errno 111] Connection refused` tanpa crash. Server palsu yang menutup koneksi menghasilkan `ConnectionResetError: Remote end closed connection without response`. Temuan: `xmlrpc.client.Transport` otomatis **mengulang satu kali** bila mendapat `RemoteDisconnected`. Pesan `Errno 111` khas Linux; di Windows teksnya `WinError 10061`, kelasnya tetap `ConnectionRefusedError`.

[SCREENSHOT: L1_5_server_error.png]

## 3. Analisis Ukuran Pesan XML `tambah(5, 3)`

Diukur dari byte mentah yang ditangkap proxy TCP perekam (`analisis_xml.py`; `hasil_pengujian/L1_analisis_xml.txt`).

Request (body):
```xml
<?xml version='1.0'?>
<methodCall>
<methodName>tambah</methodName>
<params>
<param>
<value><int>5</int></value>
</param>
<param>
<value><int>3</int></value>
</param>
</params>
</methodCall>
```
Response (body):
```xml
<?xml version='1.0'?>
<methodResponse>
<params>
<param>
<value><int>8</int></value>
</param>
</params>
</methodResponse>
```

**Definisi data sebenarnya:** nilai argumen/hasil sebagai teks UTF-8 (`5`, `3` = 2 byte; `8` = 1 byte).
Rumus: `% data = data / ukuran body XML x 100%`; `% overhead = (body - data) / body x 100%`.

| Pesan | Body XML (B) | Header HTTP (B) | Total (B) | Data (B) | Overhead (B) | % data | % overhead |
|---|---:|---:|---:|---:|---:|---:|---:|
| Request `tambah(5,3)` | **190** | 142 | 332 | 2 | 188 | 1,05% | 98,95% |
| Response (hasil 8) | 121 | 137 | 258 | 1 | 120 | 0,83% | 99,17% |

**Jawaban:** body XML request `tambah(5,3)` berukuran **190 byte**, terdiri dari sekitar **1,05% data sebenarnya** dan **98,95% overhead format** (tag, deklarasi XML, nama method). Dengan definisi alternatif (integer biner 32-bit, 4 byte per angka), data = 8 byte (4,21%) dan overhead 95,79%; kesimpulannya sama: overhead dominan.

[SCREENSHOT: L1_analisis_xml.png]

## 4. Hasil Pengujian Otomatis
`python -m unittest discover -s pengujian -p "test_l1*.py" -v` menghasilkan **23 test, 100% LULUS (OK)** pada lingkungan Windows 11 (`hasil_pengujian/unittest_praktikum1_windows.txt`). Pengujian mencakup penanganan error jaringan spesifik Windows Winsock (`ConnectionAbortedError [WinError 10053]` dan `ConnectionRefusedError [WinError 10061]`).

[SCREENSHOT: L1_unittest.png]

## 5. Kesimpulan dan Kendala

1. Semua method (tambah, kali, bagi, pangkat, akar, statistik) terdaftar dan muncul di `system.listMethods()`.
2. XML-RPC tidak dapat membawa semua tipe Python apa adanya: datetime kehilangan mikrodetik dan berubah menjadi `DateTime`; integer di luar 32-bit ditolak.
3. Pesan XML sangat boros untuk data kecil (sekitar 99% overhead pada `tambah(5,3)`).
4. RPC jauh lebih lambat daripada panggilan lokal (overhead sekitar 6.000x - 9.000x pada loopback).
5. Client membedakan Fault (error fungsi server), ProtocolError (kesalahan HTTP), dan error jaringan (`ConnectionRefusedError`, `ConnectionAbortedError`, `ConnectionResetError`) sehingga aplikasi tidak crash secara tidak terkendali.

Kendala & Status: Pengujian dua komputer (L1.4) ditandai **BELUM DILAKUKAN** karena keterbatasan fisik ketiadaan perangkat laptop/komputer kedua saat proses audit. Panduan pengujian jaringan dua komputer telah disediakan secara rinci di `02_PRAKTIKUM_1_XML_RPC/PANDUAN_BENCHMARK_DUA_KOMPUTER.md`. Tangkapan layar aktual terminal Windows perlu diambil mandiri mengikuti `05_LAPORAN/TEMPLATE_SCREENSHOT/PANDUAN_SCREENSHOT.md`.
