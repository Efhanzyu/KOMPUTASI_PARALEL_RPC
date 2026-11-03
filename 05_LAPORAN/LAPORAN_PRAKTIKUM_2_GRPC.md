# LAPORAN PRAKTIKUM REMOTE PROCEDURE CALLS (RPC) 2
## gRPC dan Protocol Buffers

| | |
|---|---|
| Nama | [ISI NAMA] |
| NIM | [ISI NIM] |
| Kelas | [ISI KELAS] |
| Mata kuliah | Komputasi Paralel dan Terdistribusi |
| Praktikum | RPC-2 (gRPC) |

---

## 1. Tujuan dan Dasar Teori Singkat

**Tujuan.** Mendefinisikan layanan dengan IDL (file `.proto`), menghasilkan stub otomatis, serta memakai pola unary, server streaming, client streaming, dan bidirectional streaming; menguji kompatibilitas schema; membandingkan ukuran pesan dengan XML-RPC; dan memakai RPC asinkron.

**Dasar teori.** gRPC memakai Protocol Buffers (serialisasi biner) di atas HTTP/2. File `.proto` adalah kontrak antarmuka yang netral bahasa. `protoc` menghasilkan `akademik_pb2.py` (kelas message) dan `akademik_pb2_grpc.py` (`LayananNilaiStub` untuk client dan `LayananNilaiServicer` sebagai kelas dasar server). Empat pola panggilan: unary, server streaming, client streaming, dan bidirectional streaming. Protobuf mengenali field berdasarkan **nomor field**, bukan nama, sehingga field baru dengan nomor baru dapat ditambahkan tanpa memutus client lama (field yang tidak dikenal disimpan sebagai *unknown fields*).

## 2. Langkah Kerja dan Kode Program

Folder: `03_PRAKTIKUM_2_GRPC`. Generate stub:
```powershell
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. akademik.proto
```
File generate tidak diedit manual. Stub pada workspace ini telah diverifikasi kompatibel penuh dengan runtime Python 3.11.9, grpcio 1.85.1, dan protobuf 7.36.2 di Windows.

Server: `ThreadPoolExecutor(max_workers=10)`, port 50051, data awal Andi (Basis Data 85, Jaringan 78) dan Sari (Basis Data 92). `GetMahasiswa` menghitung IPK = rata-rata nilai / 25 (Andi 3,26; Sari 3,68), `NOT_FOUND` bila NIM tidak ada. `TambahNilai` menolak nilai di luar 0-100 dengan `INVALID_ARGUMENT` (termasuk NaN). `StreamNilai` mengirim nilai satu per satu dengan jeda 0,5 detik. Data dilindungi `threading.Lock`.

Bukti dasar (output aktual client terhadap server sungguhan, `hasil_pengujian/L2_1_client_dasar.txt`):
```
GetMahasiswa : Andi - IPK 3.26 - prodi 'Informatika'
TambahNilai  : Nilai tersimpan
StreamNilai  : Basis Data: 85.0 / Jaringan: 78.0 / Komputasi Paralel: 88.0
Error NIM salah   : StatusCode.NOT_FOUND - NIM 9999 tidak ditemukan
Error nilai 150   : StatusCode.INVALID_ARGUMENT - Nilai harus 0-100
```

[SCREENSHOT: L2_server.png]  [SCREENSHOT: L2_1_client_dasar.png]

### L2.1 Client streaming `KirimBanyakNilai`
Proto: `rpc KirimBanyakNilai(stream NilaiRequest) returns (StatusResponse)`. Server membaca iterator permintaan sampai client selesai, menyimpan nilai yang valid, dan menjawab jumlahnya. Data tidak valid dilewati dan tidak dihitung.

| Pengujian | Target | Hasil aktual |
|---|---|---|
| Kirim 3 nilai | "3 nilai tersimpan", ketiganya tersimpan | Sesuai |
| Kirim 12 nilai | "12 nilai tersimpan" | Sesuai |
| 4 nilai, 2 tidak valid (500 dan -3) | 2 tersimpan, 2 ditolak | "2 nilai tersimpan, 2 ditolak" |
| Stream kosong | sukses=False, "0 nilai tersimpan" | Sesuai |

Demo nyata: `Respons: True - 4 nilai tersimpan`. Pengujian: `test_l21.py` (9 test bersama pengujian dasar).

[SCREENSHOT: L2_1_client_banyak.png]

### L2.2 Bidirectional streaming `Diskusi`
Proto: `rpc Diskusi(stream Pesan) returns (stream Pesan)` dengan `Pesan{pengirim, isi, waktu}`. Pesan pertama dari sebuah client dianggap bergabung. Server memakai satu thread pembaca per client (menyiarkan pesan ke antrean peserta lain) dan generator yang mengirim isi antrean ke client. Server juga membalas tiap pesan dengan konfirmasi ("pesan diterima, diteruskan ke N peserta lain"). Saat client putus (`cancel`) bagian `finally` menghapus peserta dari ruang dan menyiarkan "X keluar".

Output aktual dua client otomatis (`L2_2_client_andi.txt` dan `L2_2_client_sari.txt`), sebagian:
```
[Sari]  menerima: [server] Andi bergabung / [Andi] halo semua! / [Andi] pesan otomatis ke-1 ...
[Andi]  menerima: [Sari] pesan otomatis ke-2 / [server] Sari keluar
```
Test: pertukaran dua arah satu client, dua client saling menerima, tiga client (siaran), dan disconnect (ruang berkurang dari 2 menjadi 1 dan server tetap melayani). Semua lulus (`test_l22.py`, 4 test).

[SCREENSHOT: L2_2_diskusi_andi.png]  [SCREENSHOT: L2_2_diskusi_sari.png]

### L2.3 Backward compatibility Protobuf
Langkah: (1) schema lama (tanpa `prodi`) disimpan di `client_lama/akademik.proto` dan stub lamanya digenerate di folder itu, sehingga stub utama tidak ditimpa; (2) `akademik.proto` utama ditambah `string prodi = 4;`; (3) stub utama digenerate ulang; (4) server baru dijalankan; (5) `client_lama/client_lama.py` dijalankan dari folder `client_lama` (subprocess pada test).

Hasil aktual:
```
Field Mahasiswa menurut stub lama: ['nim', 'nama', 'ipk']
BERHASIL: nim=2023001 nama=Andi ipk=3.26
hasField prodi? False
bytes_ulang_hex: 0a07323032333030311204416e64691914ae47e17a140a40 220b496e666f726d6174696b61
```
(bagian hex terakhir `220b...` = field nomor 4, string "Informatika", ditambahkan manual spasinya untuk dibaca).

Analisis. Client lama **tetap berjalan**. Protobuf mengidentifikasi field dengan nomor; ketika client lama menerima field nomor 4 yang tidak ada di schema-nya, ia tidak error, melainkan menyimpannya sebagai *unknown field*. Buktinya: ketika client lama menserialisasi ulang pesan, byte field 4 masih ada dan dapat dibaca stub baru sebagai `prodi="Informatika"` (diverifikasi di `test_l23.py`). Arah sebaliknya juga aman: pesan lama yang dibaca stub baru memberi `prodi=""` (nilai default). Syarat kompatibilitas: nomor field lama tidak diubah/dipakai ulang dan tipenya tidak berubah. Field `prodi` tidak terlihat oleh kode client lama (`hasattr(mhs,'prodi')` bernilai `False`).

[SCREENSHOT: L2_3_client_lama.png]

### L2.4 Ukuran Protobuf vs XML-RPC
Ruang lingkup konsisten: **hanya payload pesan** yang berisi objek mahasiswa. Header HTTP (XML-RPC) dan framing HTTP/2 + prefix 5 byte gRPC tidak dihitung. Protobuf: `len(mhs.SerializeToString())`. XML-RPC: `xmlrpc.client.dumps((struct,), methodresponse=True).encode("utf-8")` dengan struct berisi data yang sama (`hasil_pengujian/L2_4_ukuran.txt`).

| Data | Protobuf (B) | XML-RPC (B) | Selisih (B) | Hemat (%) | Rasio |
|---|---:|---:|---:|---:|---:|
| Andi (nim, nama, ipk) | 24 | 350 | 326 | 93,14 | 14,58x |
| Sari (nim, nama, ipk) | 24 | 350 | 326 | 93,14 | 14,58x |
| Andi + prodi (4 field) | 37 | 432 | 395 | 91,44 | 11,68x |

Rumus: selisih = XML - Protobuf; hemat = selisih / XML x 100%. Rincian 24 byte Andi: `nim` 9 B (tag 1 + panjang 1 + 7 karakter), `nama` 6 B, `ipk` 9 B (tag 1 + double 8 B).

Mengapa berbeda: Protobuf tidak menyertakan nama field (cukup nomor field 1 byte di tag), memakai penyandian biner (double 8 byte, panjang string 1 byte), dan tidak memiliki tag pembuka-penutup; XML menulis nama field dan tipe sebagai teks (`<member><name>nim</name><value><string>...`), deklarasi XML, dan whitespace. Kekurangan Protobuf: tidak terbaca manusia dan butuh schema.

[SCREENSHOT: L2_4_ukuran.png]

### L2.5 RPC asinkron
`stub.GetMahasiswa.future(...)` dipanggil 10 kali, semua Future disimpan, lalu `.result()` diambil dengan `try/except grpc.RpcError`. Hasil aktual (`L2_5_async.txt`, `l25_async.py`):

| Skenario | Serial (ms) | Asinkron (ms) | Speedup | Hasil identik |
|---|---:|---:|---:|---|
| A. server apa adanya | 5,29 | 4,82 | 1,10x | Ya |
| B. **SIMULASI** latensi 100 ms/permintaan | 1013,71 | 103,49 | 9,80x | Ya |

Analisis. Pada skenario A tiap panggilan hanya sekitar 0,3-0,5 ms sehingga tidak ada keuntungan berarti (speedup bervariasi sekitar 0,9x-1,1x antar eksekusi; ini derau pengukuran). Pada skenario B (latensi buatan, bukan data layanan nyata) 10 permintaan diproses bersamaan oleh 10 worker, sehingga waktu total mendekati satu latensi (sekitar 103 ms) dibanding 10 x 100 ms secara serial. Asinkron bermanfaat saat tiap panggilan lambat dan server dapat memprosesnya paralel. Penanganan galat: satu future berisi NIM salah menghasilkan `NOT_FOUND` yang ditangkap per-future tanpa membatalkan yang lain.

[SCREENSHOT: L2_5_async.png]

## 3. Ringkasan Bukti Praktikum 2

| Bukti | Status | Berkas |
|---|---|---|
| Unary RPC | Terbukti | `L2_1_client_dasar.txt` |
| Server streaming | Terbukti (jeda 0,5 s diuji) | `test_l21.py` |
| Client streaming | Terbukti | `L2_1_client_banyak.txt` |
| Bidirectional streaming | Terbukti | `L2_2_client_*.txt`, `test_l22.py` |
| Backward compatibility | Terbukti | `test_l23.py` |
| Perbandingan ukuran | Terukur | `L2_4_ukuran.txt` |
| Asinkron 10 permintaan | Terukur | `L2_5_async.txt` |

Pengujian otomatis: **20 test, 100% LULUS (OK)** pada Windows 11 (`hasil_pengujian/unittest_praktikum2_windows.txt`).

[SCREENSHOT: L2_unittest.png]

## 4. Kesimpulan dan Kendala

1. Dengan IDL, kode stub dihasilkan otomatis dan kontrak layanan menjadi jelas; empat pola panggilan berhasil diimplementasikan.
2. Penambahan field baru dengan nomor baru tidak memutus client lama; Protobuf menyimpan unknown fields.
3. Protobuf menghasilkan pesan sekitar 91-93% lebih kecil daripada XML-RPC untuk data yang sama (pada payload saja).
4. RPC asinkron bermanfaat hanya bila latensi per panggilan cukup besar; pada skenario simulasi 100 ms diperoleh speedup ~9x, sedangkan pada panggilan sangat cepat tanpa latensi tidak ada perbedaan signifikan.

Kendala & Status: Seluruh fungsionalitas dan pengujian otomatis telah tervalidasi 100% di Windows 11. Tangkapan layar aktual terminal Windows perlu diambil mandiri mengikuti `05_LAPORAN/TEMPLATE_SCREENSHOT/PANDUAN_SCREENSHOT.md`.
