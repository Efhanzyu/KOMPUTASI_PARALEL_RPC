# Repositori Praktikum Komputasi Paralel dan Terdistribusi (KPT)

## Topik: Remote Procedure Call (RPC) — XML-RPC, gRPC & Protocol Buffers, dan Failure Handling

Repositori ini berisi kode sumber lengkap, dokumentasi, pengujian unit, data benchmark riil (termasuk pengujian antar dua komputer fisik), serta bukti pendukung untuk **Tugas Individu Praktikum RPC**.

---

## 📋 Daftar Isi

1. [Ringkasan Praktikum](#-ringkasan-praktikum)
2. [Struktur Direktori](#-struktur-direktori)
3. [Kebutuhan Sistem & Instalasi](#-kebutuhan-sistem--instalasi)
4. [Panduan Menjalankan Program](#-panduan-menjalankan-program)
   - [Praktikum 1: XML-RPC](#1-praktikum-1-xml-rpc)
   - [Praktikum 2: gRPC & Protocol Buffers](#2-praktikum-2-grpc--protocol-buffers)
   - [Praktikum 3: Failure Handling & Konkurensi](#3-praktikum-3-failure-handling--konkurensi)
5. [Otomasi Pengujian (Automated Test Suite)](#-otomasi-pengujian-automated-test-suite)
6. [Hasil Utama & Temuan Eksperimen](#-hasil-utama--temuan-eksperimen)
7. [Dokumentasi Laporan](#-dokumentasi-laporan)

---

## 🎯 Ringkasan Praktikum

Praktikum ini dibagi menjadi 3 modul utama:

### 1. Praktikum 1: XML-RPC (`02_PRAKTIKUM_1_XML_RPC`)

- **Implementasi Layanan:** Kalkulator matematika dasar (`tambah`, `kurang`, `kali`, `bagi`), fungsi pangkat & akar kuadrat (L1.1), serta analisis statistik (`min`, `max`, `rata2`) dari list angka (L1.2).
- **Eksplorasi Batas:** Analisis keterbatasan tipe data XML-RPC (batas integer bertanda 32-bit $-2^{31}$ s.d. $2^{31}-1$, hilangnya mikrodetik pada tipe `DateTime`) (L1.3).
- **Benchmark Jaringan 2 Komputer:** Pengukuran latensi dan overhead pemanggilan fungsi lokal vs RPC melalui jaringan nyata (Wi-Fi/Hotspot) (L1.4).
- **Penanganan Kegagalan:** Membedakan error aplikasi (`Fault`), HTTP error (`ProtocolError`), dan kegagalan soket jaringan (`ConnectionRefusedError`, `ConnectionAbortedError [WinError 10053]`) (L1.5).

### 2. Praktikum 2: gRPC & Protocol Buffers (`03_PRAKTIKUM_2_GRPC`)

- **Kontrak Antarmuka (IDL):** Definisi service `LayananNilai` menggunakan `akademik.proto`.
- **Pola Komunikasi Lengkap:**
  - *Unary RPC:* `GetMahasiswa`, `TambahNilai`
  - *Server Streaming:* `StreamNilai` (pengiriman nilai bertahap dengan jeda 0,5 detik)
  - *Client Streaming:* `KirimBanyakNilai` (klien mengirim sekumpulan nilai secara streaming) (L2.1)
  - *Bidirectional Streaming:* `Diskusi` (chat multi-klien interaktif dua arah) (L2.2)
- **Evolusi Skema (Kompatibilitas):** Membuktikan klien ber-stub lama tetap kompatibel dengan server baru yang menambahkan field `prodi = 4` tanpa kegagalan (L2.3).
- **Analisis Serialisasi:** Perbandingan ukuran payload Protobuf biner vs JSON teks (L2.4).
- **Pemanggilan Asinkron:** Penggunaan `stub.future()` non-blocking dengan speedup konkurensi signifikan dibanding eksekusi serial (L2.5).

### 3. Praktikum 3: Failure Handling & Konkurensi (`04_PRAKTIKUM_3_FAILURE`)

- **Semantik Idempotensi (At-Most-Once):** Penggunaan `request_id` unik untuk menjamin transaksi transfer bank tidak dieksekusi ganda saat klien melakukan *retry* akibat network timeout (L3.1).
- **Simulasi Kerentanan Non-Idempotent:** Bukti terjadinya transfer berlebih (*double-spending*) jika *retry* membuat ID baru (L3.2).
- **Konkurensi & Thread Safety:** Simulasi *race condition* / *lost update* pada 100 thread serentak tanpa proteksi vs integritas saldo dengan `threading.Lock` (L3.3).
- **Skalabilitas Server:** Pengukuran throughput dan latensi gRPC dengan variasi *thread pool worker* (1, 4, 10 workers) (L3.4).
- **Client Failover Otomatis:** Mekanisme pengalihan otomatis (*failover*) ke server cadangan (*backup server*) saat server primer padam tanpa interupsi pada pengguna (L3.5).

---

## 📁 Struktur Direktori

```text
KOMPUTASI_PARALEL_RPC/
├── 02_PRAKTIKUM_1_XML_RPC/         # Kode sumber & pengujian Praktikum 1 (XML-RPC)
│   ├── server_kalkulator.py        # Server XML-RPC
│   ├── client_kalkulator.py        # Client XML-RPC dengan panggil_aman()
│   ├── benchmark_l14.py            # Skrip benchmark 1 komputer & 2 komputer
│   ├── l13_eksperimen.py           # Eksperimen batas int 32-bit & DateTime
│   ├── demo_l15_client.py          # Demo penanganan error jaringan & soket
│   ├── hasil_pengujian/            # Log keluaran, CSV benchmark, & screenshot L1.4
│   └── pengujian/                  # Unit test unittest (test_l11.py s.d test_l15.py)
│
├── 03_PRAKTIKUM_2_GRPC/            # Kode sumber & pengujian Praktikum 2 (gRPC)
│   ├── akademik.proto              # Definisi interface gRPC & Protobuf
│   ├── akademik_pb2.py             # Stub message Python (generated)
│   ├── akademik_pb2_grpc.py        # Stub service Python (generated)
│   ├── server_grpc.py              # Server gRPC LayananNilai
│   ├── client_grpc.py              # Client gRPC (unary, streaming, chat)
│   ├── l24_ukuran.py               # Benchmark ukuran Protobuf vs JSON
│   ├── l25_async.py                # Benchmark serial vs asynchronous Future
│   ├── client_lama/                # Stub lama untuk uji kompatibilitas skema L2.3
│   ├── hasil_pengujian/            # Log hasil eksekusi aktual gRPC
│   └── pengujian/                  # Unit test unittest (test_l21.py s.d test_l25.py)
│
├── 04_PRAKTIKUM_3_FAILURE/         # Kode sumber & pengujian Praktikum 3 (Failure Handling)
│   ├── akademik.proto              # Kontrak service Transfer Bank & Idempotensi
│   ├── server_grpc.py              # Server gRPC dengan simulasi latensi, lock, & cache ID
│   ├── client_grpc.py              # Client gRPC dengan retry otomatis & failover
│   ├── transfer_test.py            # Uji transfer idempotent (request_id tetap)
│   ├── uuid_test.py                # Uji bahaya non-idempotent (UUID baru saat retry)
│   ├── concurrency_test.py         # Uji race condition multi-threading vs LOCK
│   ├── benchmark.py                # Benchmark skalabilitas throughput worker
│   ├── failover_test.py            # Uji failover otomatis antar server
│   ├── hasil_pengujian/            # Log keluaran & grafik benchmark_results.png
│   └── pengujian/                  # Unit test unittest (test_l31.py s.d test_l35.py)
│
├── 05_LAPORAN/                     # Dokumen laporan akhir & aset screenshot
│   ├── JAWABAN_LATIHAN_TEORI.md    # Jawaban lengkap 10 Soal Pilihan Ganda & 5 Esai
│   ├── LAPORAN_PRAKTIKUM_1_XML_RPC.md
│   ├── LAPORAN_PRAKTIKUM_2_GRPC.md
│   ├── LAPORAN_PRAKTIKUM_3_FAILURE.md
│   ├── STATUS_AUDIT_FINAL.md       # Status audit kepatuhan terhadap modul praktikum
│   └── SCREENSHOTS_LAMPIRAN_D/     # 14 File PNG screenshot terminal (B-01 s.d D-05)
│
├── jalankan_semua_tes.ps1          # Skrip runner otomasi pengujian seluruh unit test
├── requirements.txt                # Dependensi Python
└── README.md                       # Dokumentasi repositori
```

---

## ⚙️ Kebutuhan Sistem & Instalasi

### 1. Prasyarat

- **Sistem Operasi:** Windows 10/11 atau Linux
- **Python:** Versi `3.10` atau `3.11` (direkomendasikan Python 3.11.9)
- **PowerShell** (pada Windows)

### 2. Setup Virtual Environment

Buka terminal PowerShell pada direktori root proyek:

```powershell
# Buat virtual environment
python -m venv venv

# Aktivasi virtual environment di Windows PowerShell
.\venv\Scripts\Activate.ps1

# Instal dependensi yang diperlukan
pip install -r requirements.txt
```

---

## 🚀 Panduan Menjalankan Program

### 1. Praktikum 1: XML-RPC

Masuk ke folder Praktikum 1:

```powershell
cd .\02_PRAKTIKUM_1_XML_RPC
```

- **Menjalankan Server Kalkulator:**

  ```powershell
  python server_kalkulator.py
  ```

  *(Server akan berjalan di port `8000` dan menampilkan daftar method yang terdaftar)*.

- **Menjalankan Client Kalkulator:**
  Buka jendela terminal baru:

  ```powershell
  python client_kalkulator.py --tenang
  ```

  *(Untuk melihat detail XML request/response HTTP lengkap, jalankan tanpa flag `--tenang`: `python client_kalkulator.py`)*.

- **Menjalankan Eksperimen Batas Integer & DateTime (L1.3):**

  ```powershell
  python l13_eksperimen.py
  ```

- **Menjalankan Benchmark Latensi & Overhead (L1.4):**

  ```powershell
  # Mode satu komputer (loopback localhost):
  python benchmark_l14.py

  # Mode dua komputer fisik (ganti IP dengan IP komputer server):
  python benchmark_l14.py --host 172.20.10.2 --label dua-komputer
  ```

---

### 2. Praktikum 2: gRPC & Protocol Buffers

Masuk ke folder Praktikum 2:

```powershell
cd .\03_PRAKTIKUM_2_GRPC
```

- **Mengompilasi Ulang File `.proto` (Jika Diperlukan):**

  ```powershell
  python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. akademik.proto
  ```

- **Menjalankan Server gRPC:**

  ```powershell
  python server_grpc.py
  ```

  *(Server akan aktif di port `50051`)*.

- **Menjalankan Client Dasar (Unary & Server Streaming):**

  ```powershell
  python client_grpc.py
  ```

- **Menjalankan Client Streaming (L2.1):**

  ```powershell
  python client_grpc.py banyak
  ```

- **Menjalankan Bidirectional Streaming Chat (L2.2):**
  Buka dua terminal terpisah:

  ```powershell
  # Terminal 1:
  python client_grpc.py diskusi Andi

  # Terminal 2:
  python client_grpc.py diskusi Sari
  ```

- **Uji Kompatibilitas Skema Protobuf (L2.3):**

  ```powershell
  cd client_lama
  python client_lama.py
  cd ..
  ```

- **Benchmark Ukuran Payload Protobuf vs JSON (L2.4):**

  ```powershell
  python l24_ukuran.py
  ```

- **Uji Pemanggilan Asinkron Future (L2.5):**

  ```powershell
  python l25_async.py
  ```

---

### 3. Praktikum 3: Failure Handling & Konkurensi

Masuk ke folder Praktikum 3:

```powershell
cd .\04_PRAKTIKUM_3_FAILURE
```

- **Uji Idempotensi Transfer Bank dengan `request_id` (L3.1):**

  ```powershell
  python transfer_test.py --seed 42
  ```

- **Simulasi Bahaya Transfer Non-Idempotent (L3.2):**

  ```powershell
  python uuid_test.py --seed 42
  ```

- **Uji Konkurensi & Race Condition dengan vs tanpa LOCK (L3.3):**

  ```powershell
  python concurrency_test.py
  ```

- **Benchmark Skalabilitas Worker Thread Pool (L3.4):**

  ```powershell
  python benchmark.py
  ```

  *(Menghasilkan tabel throughput dan berkas grafik visual `hasil_pengujian/benchmark_results.png`)*.

- **Uji Client Failover Otomatis (L3.5):**

  ```powershell
  python failover_test.py
  ```

---

## 🧪 Otomasi Pengujian (Automated Test Suite)

Proyek ini dilengkapi dengan skrip test runner otomatis yang menguji seluruh fungsionalitas dari ketiga praktikum dalam satu perintah.

Jalankan perintah berikut di PowerShell dari direktori root proyek:

```powershell
powershell -ExecutionPolicy Bypass -File .\jalankan_semua_tes.ps1
```

### Hasil Verifikasi Pengujian

```text
============================================================
                    RINGKASAN HASIL TEST                    
============================================================
Praktikum 1 (XML-RPC)              : LULUS (23/23) [Exit Code: 0]
Praktikum 2 (gRPC & Protobuf)      : LULUS (20/20) [Exit Code: 0]
Praktikum 3 (Failure & Concurrency): LULUS (14/14) [Exit Code: 0]
------------------------------------------------------------
STATUS KESELURUHAN: SEMUA UNIT TEST LULUS (57/57)!
============================================================
```

---

## 📊 Hasil Utama & Temuan Eksperimen

1. **Overhead Jaringan XML-RPC (Pengujian 2 Komputer Asli):**
   - Pemanggilan Fungsi Lokal: **0.000191 ms** per panggilan.
   - Pemanggilan XML-RPC (Wi-Fi/Hotspot `172.20.10.2:8000`): **84.691049 ms** per panggilan.
   - **Overhead RPC:** Pemanggilan RPC beroperasi **443.408,6 kali lebih lambat** akibat transmisi paket TCP, negosiasi HTTP, dan serialisasi/deserialisasi format teks XML.

2. **Efisiensi Serialisasi Protobuf vs JSON:**
   - Format biner Protobuf berukuran **2 hingga 4 kali lebih ringkas** dibanding representasi JSON teks, serta tidak memerlukan parsing string berulang sehingga menghemat pemakaian bandwidth dan CPU.

3. **Kompatibilitas Skema ke Depan/Belakang (Backward/Forward Compatibility):**
   - Penambahan field baru (`prodi = 4`) pada server gRPC tidak membuat klien ber-stub lama mengalami error. Nilai field yang tidak dikenali disimpan rapi sebagai *unknown fields*.

4. **Keuntungan Pemanggilan Asinkron (gRPC Future):**
   - Eksekusi 10 pemanggilan secara serial membutuhkan waktu **1027 ms**, sementara eksekusi asinkron (`stub.future()`) hanya membutuhkan **116 ms** (peningkatan kecepatan / *speedup* mencapai **8.8x**).

5. **Pentingnya Semantik Idempotensi pada Sistem Terdistribusi:**
   - Penggunaan `request_id` memastikan bahwa ketika terjadi *network timeout* dan klien melakukan *retry*, transaksi transfer bank tidak dieksekusi berulang kali (*at-most-once*).
   - Pengabaian idempotensi (mengganti UUID saat retry) terbukti mengakibatkan *double-spending* dan kerusakan saldo finansial.

6. **Konkurensi & Skalabilitas:**
   - Pengujian 100 thread serentak tanpa proteksi sinkronisasi (`threading.Lock`) memicu *race condition* dan *lost updates*.
   - Throughput server gRPC berskala linier terhadap jumlah worker thread: meningkat dari **9.8 req/s** (1 worker) menjadi **89.0 req/s** (10 worker).
