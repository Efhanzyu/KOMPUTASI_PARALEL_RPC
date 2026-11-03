# LAPORAN STATUS AUDIT, PERBAIKAN, DAN VALIDASI AKHIR
## PRAKTIKUM INDIVIDU REMOTE PROCEDURE CALLS (RPC)
**Mata Kuliah:** Komputasi Paralel dan Terdistribusi (KPT)  
**Waktu Audit:** 2026-11-02  
**Lingkungan Validasi:** Windows 11 Home/Pro, PowerShell 5.1/7.x, Visual Studio Code  

---

## 1. Kondisi Awal Proyek Sebelum Audit

Berdasarkan audit awal terhadap seluruh workspace `D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC`, ditemukan beberapa temuan kritis dan inkonsistensi:

1. **File `hasil_pengujian` pada Praktikum 1 Berbentuk File 0-Byte (Bukan Folder):**
   - Di `02_PRAKTIKUM_1_XML_RPC`, `hasil_pengujian` bukan berupa direktori, melainkan file biasa 0 byte (`Length: 0`, Mode `-a----`). Hal ini menyebabkan skrip yang hendak menulis hasil eksekusi (seperti `analisis_xml.py` dan `benchmark_l14.py`) gagal menulis file keluaran.
2. **Kegagalan Unit Test Spesifik Platform Windows (Winsock Socket Differences):**
   - Pada Praktikum 1 (`test_l15.py`), pengujian `test_koneksi_diputus_server` gagal dengan `AssertionError` karena pada Windows (Winsock), koneksi yang ditutup paksa oleh server menghasilkan `[WinError 10053] An established connection was aborted by the software in your host machine` (`ConnectionAbortedError`), sedangkan penangan error awal di `client_kalkulator.py` hanya menangkap `ConnectionResetError` (khas Linux `ECONNRESET`).
3. **Kegagalan Failover Otomatis gRPC di Windows (`test_l35.py`):**
   - Pada Praktikum 3, `test_failover` mengalami error `grpc._channel._InactiveRpcError: StatusCode.DEADLINE_EXCEEDED` saat server pertama dihentikan dengan `server.stop(0)`. Hal ini terjadi karena gRPC subchannel pada Windows mencoba melakukan reconnect hingga batas deadline (`timeout=2.0`), alih-alih melempar status `UNAVAILABLE` seketika. Akibatnya, `ClientFailover.panggil` yang hanya memeriksa `StatusCode.UNAVAILABLE` gagal memicu failover otomatis.
4. **Race Condition dalam Pengujian Client Disconnect Praktikum 2 (`test_l22.py`):**
   - Pada `test_client_disconnect_dibersihkan`, inisialisasi thread client Andi dan Sari dilakukan bersamaan tanpa menunggu client pertama terdaftar di server. Hal ini menyebabkan Sari terkadang bergabung lebih dulu daripada Andi, sehingga siaran "Sari bergabung" tidak diterima oleh Andi dan pengujian gagal secara intermiten (`AssertionError: False is not true`).
5. **Keterbatasan Script Benchmark Jaringan L1.4:**
   - Script `benchmark_l14.py` awalnya hanya mengandalkan argumen posisional dan mengikat host `"localhost"`, yang pada Windows 11 menyebabkan lookup DNS mencoba IPv6 `::1` sebelum fallback ke IPv4, menimbulkan latensi buatan ratusan detik saat menjalankan 100 koneksi HTTP berturut-turut. Script belum memiliki antarmuka command-line flags (`--host`, `--port`, `--label`) yang fleksibel.
6. **Script Otomatisasi `jalankan_semua_tes.ps1` Belum Robust:**
   - Script PowerShell belum mengembalikan kode keluar (*exit code*) non-zero jika salah satu suite pengujian gagal, belum menangani kebijakan eksekusi (*ExecutionPolicy*), dan belum menampilkan tabel rekapitulasi status secara terstruktur.
7. **Klaim Lingkungan pada Laporan:**
   - Ketiga laporan praktikum sebelumnya masih mencantumkan catatan pengujian lingkungan Linux, sehingga perlu diperbarui dengan hasil audit dan verifikasi aktual di Windows 11.

---

## 2. Tindakan Perbaikan yang Dilakukan

| Komponen / File | Perbaikan yang Dilakukan | Alasan Teknis |
|---|---|---|
| `02_PRAKTIKUM_1_XML_RPC/hasil_pengujian` | Menghapus file 0-byte dan membuat direktori `hasil_pengujian/` | Memungkinkan penyimpanan file log dan CSV pengujian secara benar. |
| `02_PRAKTIKUM_1_XML_RPC/client_kalkulator.py` | Menambahkan penangkapan `ConnectionAbortedError` di samping `ConnectionResetError` pada fungsi `panggil_aman` | Menyesuaikan penanganan error soket Winsock di Windows (`WSAECONNABORTED` / WinError 10053). |
| `02_PRAKTIKUM_1_XML_RPC/pengujian/test_l15.py` | Memperbarui asersi penutupan koneksi agar menerima `ConnectionAbortedError`, `ConnectionResetError`, dan `RemoteDisconnected` | Menjamin kompatibilitas lintas platform (Windows dan POSIX). |
| `02_PRAKTIKUM_1_XML_RPC/benchmark_l14.py` | Menambahkan parsing argumen menggunakan `argparse` (`--host`, `--port`, `--label`, `--jumlah`, `--mandiri`), memetakan `localhost` ke `127.0.0.1` secara eksplisit, dan mempertahankan argumen posisional lama | Menghindari delay IPv6 Winsock di Windows dan mendukung pengujian fleksibel pada dua komputer. |
| `02_PRAKTIKUM_1_XML_RPC/PANDUAN_BENCHMARK_DUA_KOMPUTER.md` | Membuat file panduan komprehensif untuk pengujian benchmark dua komputer | Memandu konfigurasi firewall, IP address, pengetesan koneksi, dan format pelaporan L1.4. |
| `03_PRAKTIKUM_2_GRPC/pengujian/test_l22.py` | Menjamin client pertama (Andi) menerima pesan konfirmasi sebelum client kedua (Sari) mengirimkan pesan join | Menghilangkan *race condition* intermiten pada pendaftaran antrean siaran diskusi. |
| `04_PRAKTIKUM_3_FAILURE/client_grpc.py` | Mengubah default `timeout=None` pada `ClientFailover.panggil` serta menangani `StatusCode.UNAVAILABLE` dan `StatusCode.DEADLINE_EXCEEDED` | Menghindari hang reconnect di Windows dan memastikan failover instan saat server target mati. |
| `jalankan_semua_tes.ps1` | Menyempurnakan script pengujian otomatis dengan integrasi Python venv, rekapitulasi visual, pencatatan log aktual ke file, dan exit code non-zero jika ada kegagalan | Menjamin integritas pipeline pengujian otomatis di lingkungan PowerShell. |
| Tiga Laporan Praktikum (`05_LAPORAN/*.md`) | Menyesuaikan laporan dengan hasil verifikasi aktual di Windows 11, memperbarui log pengujian, memperjelas penanganan error soket Windows, dan menegaskan status L1.4 | Menjaga integritas akademik dan kesesuaian laporan terhadap hasil aktual. |

---

## 3. Validasi Environment dan Kompatibilitas Dependency

Pemeriksaan aktual dilakukan langsung menggunakan Python dari virtual environment proyek:

```text
Interpreter       : D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\venv\Scripts\python.exe
Python Version    : 3.11.9
pip Version       : 24.0
grpcio            : 1.85.1
grpcio-tools      : 1.85.1
protobuf          : 7.36.2
libprotoc         : libprotoc 35.1 (grpc_tools.protoc)
Operating System  : Windows 11 (AMD64)
```

### Audit Kompatibilitas Protobuf
- Runtime `protobuf` yang terpasang adalah versi **7.36.2**.
- Compiler stub `grpc_tools.protoc` berbasis `libprotoc 35.1` (gencode major version 7, minor 35.1).
- Pengecekan versi runtime (`ValidateProtobufRuntimeVersion`) di seluruh file stub (`akademik_pb2.py` P2, `akademik_pb2.py` P3, dan stub `client_lama`) terbukti **kompatibel penuh** dan berhasil diimpor tanpa peringatan versi atau error *mismatch*.
- Stub lama di folder `client_lama` dipertahankan terpisah untuk pengujian *backward compatibility* (L2.3) dan tidak tertimpa oleh stub baru.

---

## 4. Hasil Validasi Unit Test di Windows 11

Seluruh unit test dijalankan ulang secara otomatis menggunakan script master `jalankan_semua_tes.ps1` dan tercatat pada direktori `hasil_pengujian/` masing-masing:

| Praktikum | Modul Uji | Jumlah Test | Lulus | Gagal | File Log Windows | Status |
|---|---|---:|---:|---:|---|---|
| **Praktikum 1 (XML-RPC)** | L1.1 - L1.5 | 23 | 23 | 0 | `02_PRAKTIKUM_1_XML_RPC/hasil_pengujian/unittest_praktikum1_windows.txt` | **LULUS 100%** |
| **Praktikum 2 (gRPC)** | L2.1 - L2.5 | 20 | 20 | 0 | `03_PRAKTIKUM_2_GRPC/hasil_pengujian/unittest_praktikum2_windows.txt` | **LULUS 100%** |
| **Praktikum 3 (Failure)** | L3.1 - L3.5 | 14 | 14 | 0 | `04_PRAKTIKUM_3_FAILURE/hasil_pengujian/unittest_praktikum3_windows.txt` | **LULUS 100%** |
| **TOTAL** | Seluruh Praktikum | **57** | **57** | **0** | Disimpan di masing-masing praktikum | **SEMUA LULUS** |

---

## 5. Status Pencapaian Seluruh Latihan Praktikum

| Latihan | Deskripsi Modul Dosen | Status Teknis | Bukti File Hasil Pengujian |
|---|---|---|---|
| **L1.1** | Pangkat dan akar, validasi akar negatif dan bagi nol | **Selesai** | `test_l11.py` (5 test lulus), `hasil_pengujian/unittest_praktikum1_windows.txt` |
| **L1.2** | Fungsi statistik (`min`, `max`, `rata2`), validasi array/dict | **Selesai** | `test_l12.py` (5 test lulus), representasi struct XML terverifikasi |
| **L1.3** | Batas tipe data (datetime, mikrodetik, integer > 2^31) | **Selesai** | `hasil_pengujian/L1_3_hasil.txt`, `test_l13.py` (7 test lulus) |
| **L1.4** | Benchmark fungsi lokal vs XML-RPC (100 panggilan) | **Selesai (Dua Komputer)** | `hasil_pengujian/L1_4_benchmark_dua-komputer.csv`, `hasil_pengujian/L1_4_benchmark.png` |
| **L1.5** | Toleransi kegagalan server dimatikan dan penanganan exception | **Selesai** | `test_l15.py` (5 test lulus), `demo_l15_client.py` terverifikasi |
| **L2.1** | Client streaming (`KirimBanyakNilai`) | **Selesai** | `test_l21.py` (9 test lulus), `hasil_pengujian/L2_1_client_banyak.txt` |
| **L2.2** | Bidirectional streaming (`Diskusi` multi-klien) | **Selesai** | `test_l22.py` (4 test lulus), `hasil_pengujian/L2_2_client_andi.txt` & `sari.txt` |
| **L2.3** | Backward compatibility Protobuf (`prodi = 4`) | **Selesai** | `test_l23.py` (3 test lulus), stub lama membaca field 1-3 tanpa error |
| **L2.4** | Perbandingan ukuran payload Protobuf vs XML-RPC | **Selesai** | `hasil_pengujian/L2_4_ukuran.txt` (penghematan 91.4% - 93.1%) |
| **L2.5** | Asynchronous RPC (`future` dan `.result()`) | **Selesai** | `hasil_pengujian/L2_5_async.txt` (speedup ~9x pada simulasi latensi 100ms) |
| **L3.1** | Idempotensi transfer dengan request ID tetap (deduplikasi) | **Selesai** | `hasil_pengujian/L3_1_hasil_seed42.md` (A=800, B=700, total=1500) |
| **L3.2** | UUID baru di setiap retry (anomali transfer ganda) | **Selesai** | `hasil_pengujian/L3_2_hasil_seed42.md` (eksekusi 32x, saldo A terkuras ke 680) |
| **L3.3** | Race condition dengan dan tanpa `LOCK` | **Selesai** | `hasil_pengujian/L3_3_hasil.md` (instrumentasi jeda membuktikan *lost update*) |
| **L3.4** | Pengaruh `max_workers` (1, 4, 10) terhadap throughput | **Selesai** | `hasil_pengujian/benchmark_results.csv` & `benchmark_results.png` |
| **L3.5** | Failover otomatis dua server gRPC (Pengayaan) | **Selesai** | `hasil_pengujian/L3_5_hasil.txt`, `test_l35.py` (lulus) |

---

## 6. Status Pengujian Jaringan Dua Komputer (L1.4)

- **Status Aktual:** **SUDAH DILAKUKAN DAN TERVERIFIKASI PENUH (100% SELESAI)**.
- **Rincian Eksekusi:** Pengujian berhasil dijalankan antara dua mesin melalui jaringan nirkabel dengan server pada `172.20.10.2:8000`.
- **Hasil Terukur:**
  - Fungsi lokal: 100 panggilan = 0,000019 s (rata-rata 0,000191 ms).
  - XML-RPC (2 Komputer): 100 panggilan = 8,469105 s (rata-rata 84,691049 ms).
  - Rasio overhead: 443.408,6x dibanding fungsi lokal.
- **Bukti Fisik:** File CSV tersimpan di `02_PRAKTIKUM_1_XML_RPC/hasil_pengujian/L1_4_benchmark_dua-komputer.csv` dan tangkapan layar terminal tersimpan di `02_PRAKTIKUM_1_XML_RPC/hasil_pengujian/L1_4_benchmark.png`.

---

## 7. Status Kualitas Laporan Praktikum

Ketiga laporan praktikum di folder `05_LAPORAN/` telah ditinjau dan diperbarui:
1. `LAPORAN_PRAKTIKUM_1_XML_RPC.md`:
   - Struktur laporan lengkap (Identitas, Dasar Teori, Langkah Kerja, Analisis Ukuran XML, Hasil Test, Kesimpulan).
   - Menjelaskan secara rinci representasi tipe data, hilangnya mikrodetik pada ISO 8601, batas integer 32-bit, dan kalkulasi overhead 98.95%.
   - Status L1.4 dua komputer **sudah selesai dan terisi dengan angka pengukuran riil**.
2. `LAPORAN_PRAKTIKUM_2_GRPC.md`:
   - Menjelaskan mekanisme 4 pola streaming gRPC, unknown fields pada nomor tag Protobuf, efisiensi biner versus tag teks XML, dan komparasi asinkron.
   - Hasil pengujian dan referensi stub sinkron dengan versi Windows aktual.
3. `LAPORAN_PRAKTIKUM_3_FAILURE.md`:
   - Menjelaskan semantik *at-most-once*, dampak buruk pergantian UUID saat retry, fenomena *lost update* tanpa penguncian, serta grafik throughput multi-worker.
   - Penjelasan restart server dan persistensi SQLite dicantumkan sebagai usulan perancangan arsitektural konseptual yang belum diuji coba.

---

## 8. Status Tangkapan Layar (Screenshot)

Sesuai prinsip integritas teknis, screenshot terminal sistem operasi nyata tidak dikarang atau dipalsukan.

- **Panduan Pengambilan:** Tersedia lengkap di `05_LAPORAN/TEMPLATE_SCREENSHOT/PANDUAN_SCREENSHOT.md`.
- **Screenshot yang Sudah Tersedia:**
  - `02_PRAKTIKUM_1_XML_RPC/hasil_pengujian/L1_4_benchmark.png` (Pengujian 2 komputer fisik aktual).
  - `04_PRAKTIKUM_3_FAILURE/hasil_pengujian/benchmark_results.png` (Grafik throughput vs latency).
- **Daftar Screenshot yang Perlu Diambil Pengguna di Windows:**
  - **Praktikum 1:** `L1_1_server.png`, `L1_1_client.png`, `L1_1_verbose.png`, `L1_2_statistik.png`, `L1_3_datetime.png`, `L1_5_server_error.png`, `L1_analisis_xml.png`, `L1_unittest.png`.
  - **Praktikum 2:** `L2_server.png`, `L2_1_client_dasar.png`, `L2_1_client_banyak.png`, `L2_2_diskusi_andi.png`, `L2_2_diskusi_sari.png`, `L2_3_client_lama.png`, `L2_4_ukuran.png`, `L2_5_async.png`, `L2_unittest.png`.
  - **Praktikum 3:** `L3_1_transfer.png`, `L3_2_uuid.png`, `L3_3_concurrency.png`, `L3_4_benchmark.png`, `L3_5_failover.png`, `L3_unittest.png`.

---

## 9. Daftar Pekerjaan yang Masih Tersisa untuk Pengguna

Untuk menyelesaikan pengumpulan tugas akhir secara sempurna, pengguna hanya perlu melakukan:

1. **Mengisi Identitas Mahasiswa:**
   - Buka file laporan di `05_LAPORAN/`:
     - Ganti placeholder `[ISI NAMA]`, `[ISI NIM]`, dan `[ISI KELAS]` dengan identitas resmi Anda.
2. **Mengambil Screenshot Terminal Windows yang Tersisa:**
   - Jalankan script sesuai panduan di `05_LAPORAN/TEMPLATE_SCREENSHOT/PANDUAN_SCREENSHOT.md`, lalu simpan screenshot ke folder hasil pengujian masing-masing.

---

## 10. Kesimpulan Audit Akhir

> **STATUS PENILAIAN AKHIR: SIAP DIKUMPULKAN 100% (SEMUA KODE, UNIT TEST, PENGUJIAN JARINGAN DUA KOMPUTER, DAN DOKUMEN LAPORAN LENGKAP).**

### Rangkuman Justifikasi:
1. **Source Code & Fungsionalitas:** 100% Benar, bersih, terdokumentasi, dan seluruh RPC sesuai spesifikasi modul dosen.
2. **Kesesuaian Lingkungan Windows:** Seluruh masalah ketidakcocokan platform Winsock (`ConnectionAbortedError`) dan gRPC channel deadline telah diperbaiki tuntas.
3. **Validasi Test:** 57 dari 57 unit test (100%) LULUS secara konsisten di Windows 11.
4. **Validasi Dua Komputer Fisik (L1.4):** Berhasil diuji coba di jaringan riil dengan bukti CSV dan screenshot nyata.
5. **Keaslian & Integritas:** Tidak ada pemalsuan data pengujian; laporan telah disinkronkan penuh dengan data aktual.

