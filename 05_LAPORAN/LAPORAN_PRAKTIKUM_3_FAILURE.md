# LAPORAN PRAKTIKUM REMOTE PROCEDURE CALLS (RPC) 3
## Concurrency, Timeout, dan Toleransi Kegagalan

| | |
|---|---|
| Nama | [ISI NAMA] |
| NIM | [ISI NIM] |
| Kelas | [ISI KELAS] |
| Mata kuliah | Komputasi Paralel dan Terdistribusi |
| Praktikum | RPC-3 (Failure) |

---

## 1. Tujuan dan Dasar Teori Singkat

**Tujuan.** Membuktikan bahwa retry tanpa pengaman dapat menjalankan operasi dua kali, memperbaikinya dengan ID permintaan (semantik at-most-once), menunjukkan race condition tanpa lock, mengukur pengaruh jumlah thread server terhadap throughput, dan (pengayaan) failover.

**Dasar teori.** Pada jaringan nyata, balasan dapat terlambat atau hilang sehingga client tidak tahu apakah operasi sudah dijalankan. *At-least-once* (client mengulang) aman hanya untuk operasi idempoten; `transfer()` tidak idempoten. *At-most-once* dicapai server dengan mencatat `request_id` yang sudah diproses dan mengembalikan hasil lama untuk duplikat. *Race condition* terjadi ketika beberapa thread membaca dan menulis data bersama tanpa sinkronisasi sehingga hasil bergantung pada urutan eksekusi. Throughput = permintaan berhasil / waktu total; latensi = waktu satu permintaan dari kirim hingga balasan. *Exponential backoff* menambah jeda antar-percobaan (0,5 s x 2^(percobaan-1)).

## 2. Langkah Kerja dan Kode Program

Folder `04_PRAKTIKUM_3_FAILURE` (kode terpisah dari Praktikum 2). `akademik.proto` menambah `rpc Transfer(TransferRequest) returns (StatusResponse)` dan `TransferRequest{request_id, dari, ke, jumlah}`, stub digenerate ulang. Setiap eksperimen menyatakan target, hasil aktual, dan analisis. Eksperimen L3.1-L3.3 memakai server in-process (tetap melalui jaringan gRPC loopback) sehingga saldo diverifikasi langsung dari memori server.

**Server (`server_grpc.py`).** `SALDO = {"A": 1000.0, "B": 500.0}`, `PROSES = {}`, `LOCK = threading.Lock()`. Alur `Transfer`: validasi (ID kosong, jumlah <= 0, akun tidak ada, akun sama -> status gRPC permanen), lalu di dalam `LOCK`: jika `request_id` ada di `PROSES` kembalikan hasil lama; jika saldo kurang -> `StatusResponse(sukses=False)`; selain itu kurangi/tambah saldo; simpan hasil di `PROSES`. **Setelah lock dilepas dan setelah transaksi tersimpan**, dengan peluang 30% server tidur 3 detik (balasan terlambat, transfer sudah terjadi).

**Client (`client_grpc.py`).** `transfer_dengan_retry(stub, dari, ke, jumlah, maks=3)`: `uuid.uuid4()` sekali per transaksi logis, `timeout=2.0`, retry hanya untuk `DEADLINE_EXCEEDED` dan `UNAVAILABLE`, jeda `0.5 * 2 ** (percobaan - 1)`, pesan tiap retry dicetak. Kesalahan permanen (mis. `NOT_FOUND`, `INVALID_ARGUMENT`) langsung dilempar tanpa retry (diuji di `test_l31.py`). Parameter `uuid_baru_tiap_percobaan=True` dipakai untuk L3.2.

### L3.1 Transfer dengan request ID tetap
Perintah: `python transfer_test.py --seed 42` (`hasil_pengujian/L3_1_hasil_seed42.md`). Seed membuat urutan respons lambat dapat diulang.

| Besaran | Nilai |
|---|---:|
| Saldo awal A / B / total | 1000 / 500 / 1500 |
| Jumlah transfer | 20 x 10 |
| Total percobaan RPC (termasuk retry) | 30 |
| Transfer benar-benar dieksekusi server | 20 |
| Duplikat ditolak deduplikasi | 10 |
| Saldo akhir A / B | 800 / 700 |
| Total saldo akhir | 1500 |
| Target | A=800, B=700, total=1500 |
| **Status pengujian** | **LULUS** |

Analisis. Sepuluh transfer mengalami respons lambat sehingga percobaan pertama kena `DEADLINE_EXCEEDED` padahal server sudah memotong saldo. Percobaan kedua membawa ID yang sama, server menemukannya di `PROSES` dan mengembalikan hasil lama tanpa mengubah saldo. Hasil akhir sesuai target dari sisi server.

[SCREENSHOT: L3_1_transfer.png]

### L3.2 UUID baru di setiap percobaan
Perintah: `python uuid_test.py --seed 42` (seed sama dengan L3.1, state direset). Hasil aktual (`L3_2_hasil_seed42.md`):

| Besaran | L3.1 ID tetap | L3.2 UUID baru |
|---|---:|---:|
| Percobaan RPC total | 30 | 32 |
| Eksekusi di server | 20 | **32** |
| Duplikat ditolak | 10 | 0 |
| Transfer gagal total (client) | 0 | 1 |
| Saldo akhir A | 800 | **680** |
| Saldo akhir B | 700 | **820** |
| Total saldo | 1500 | 1500 |

Analisis. Dengan UUID baru, percobaan ulang dianggap permintaan **berbeda** karena server hanya mengenali identitas melalui `request_id`; deduplikasi tidak pernah terpicu (0 duplikat). Timeout hanya berarti client tidak menerima balasan, bukan transfer gagal, sehingga setiap retry mengeksekusi transfer lagi: A didebit 32 x 10 = 320 padahal seharusnya 200 (12 eksekusi berlebih). Satu transfer logis (#02) bahkan "gagal" di client setelah 3 percobaan tetapi dieksekusi **tiga kali** di server. Catatan penting: **total saldo tetap 1500**, jadi pemeriksaan total saja tidak mendeteksi transfer ganda; harus diperiksa saldo masing-masing akun atau jumlah eksekusi. Angka ini hasil seed 42 (dapat direproduksi); seed lain memberi angka berbeda. Uji deterministik di `test_l32.py`: bila semua respons lambat dan 2 percobaan, A=980 untuk satu transfer logis.

[SCREENSHOT: L3_2_uuid.png]

### L3.3 Race condition tanpa LOCK
Penghapusan `with LOCK:` diwujudkan sebagai opsi `pakai_lock=False` (jalur kode yang sama seperti baris itu dihapus). Skenario: 50 transfer 10 dari A ke B, 10 thread client, `ThreadPoolExecutor`, ID unik, tanpa respons lambat. Target: A=500, B=1000, total=1500, 50 transaksi (`L3_3_hasil.md`).

**Pengujian dasar (sesuai modul):**

| Kondisi | A | B | Total | Transaksi | Sukses | Gagal |
|---|---:|---:|---:|---:|---:|---:|
| Dengan LOCK | 500 | 1000 | 1500 | 50 | 50 | 0 |
| Tanpa LOCK | 500 | 1000 | 1500 | 50 | 50 | 0 |

Diulang 20 kali: dengan LOCK menyimpang 0/20, **tanpa LOCK juga menyimpang 0/20**. Race condition tidak muncul pada skenario dasar. Race condition bergantung pada interleaving dan waktu; operasi `SALDO[x] -= n` sangat singkat, CPython hanya berpindah thread pada batas bytecode setelah interval tertentu, dan banyak waktu server dihabiskan di luar bagian kritis, sehingga peluang tabrakan kecil. Tidak adanya anomali **bukan bukti bahwa kode tanpa lock aman**.

**Pengujian TAMBAHAN (instrumentasi, dipisahkan dari pengujian dasar):** jeda 2 ms disisipkan antara membaca dan menulis saldo di server untuk memperbesar peluang interleaving.

| Kondisi | A | B | Total | Transaksi |
|---|---:|---:|---:|---:|
| Tanpa LOCK #1 | 920 | 570 | **1490** | 50 |
| Tanpa LOCK #2 | 890 | 610 | 1500 | 50 |
| Tanpa LOCK #3 | 890 | 610 | 1500 | 50 |
| Tanpa LOCK #4 | 950 | 550 | 1500 | 50 |
| Tanpa LOCK #5 | 930 | 560 | **1490** | 50 |
| Dengan LOCK #1-#5 | 500 | 1000 | 1500 | 50 |

Tanpa LOCK menyimpang 5/5, dengan LOCK 0/5. Penjelasan (*lost update*): dua thread membaca saldo A yang sama (mis. 1000), keduanya menghitung 990 dan menulis 990; satu pengurangan hilang. Pengurangan A dan penambahan B hilang secara independen, sehingga total dapat berubah (1490 pada dua eksekusi: uang "lenyap"), atau tetap 1500 secara kebetulan padahal saldo masing-masing salah (A=890, B=610 tidak sama dengan 500/1000). Jadi **total tetap 1500 tidak menjamin benar**; di sini A dan B keliru pada semua eksekusi tanpa LOCK.

**Pengujian TAMBAHAN: 10 permintaan duplikat (ID sama) bersamaan, jeda 10 ms:** tanpa LOCK, penghitung eksekusi = 10 (deduplikasi bocor karena semua thread lolos pemeriksaan `PROSES` sebelum ada yang menyimpan); saldo akhir A=990 karena pembaruan saling menimpa. Dengan LOCK, eksekusi = 1 (A=990). Jadi LOCK melindungi bukan hanya saldo, tetapi juga deduplikasi: pemeriksaan "sudah diproses?" dan penyimpanan hasilnya harus atomik.

[SCREENSHOT: L3_3_concurrency.png]

### L3.4 Throughput terhadap `max_workers`
Metodologi (`benchmark.py`): 200 panggilan `GetMahasiswa` dari 20 thread client (masing-masing satu channel), server dengan `time.sleep(0.1)`; satu proses server baru per konfigurasi (port 50151-50153); waktu start-up server tidak diukur; warm-up 20 panggilan tidak dihitung; latensi per request diukur dengan `perf_counter`; permintaan gagal dicatat terpisah. Hasil aktual (`benchmark_results.csv`; grafik `benchmark_results.png`):

| max_workers | Waktu total (s) | Throughput (req/s) | Latensi rata-rata (ms) | Gagal |
|---|---:|---:|---:|---:|
| 1 | 20,227 | 9,89 | 1926,4 | 0 |
| 4 | 5,069 | 39,45 | 486,0 | 0 |
| 10 | 2,051 | 97,53 | 199,4 | 0 |

[GAMBAR: hasil_pengujian/benchmark_results.png]  [SCREENSHOT: L3_4_benchmark.png]

Analisis. Tiap request memakan 0,1 s di server dan hanya `max_workers` request yang dikerjakan bersamaan; sisanya mengantre. Dengan 1 worker semua request serial: 200 x 0,1 s = 20 s (terukur 20,2 s), throughput maksimum 10 req/s. Dengan 4 worker kapasitas teoretis 40 req/s (terukur 39,5) dan 10 worker 100 req/s (terukur 97,5). Latensi rata-rata mengikuti hukum antrean: 20 request datang bersamaan, jadi latensi sekitar (20 / jumlah worker) x 0,1 s = 2,0 s, 0,5 s, dan 0,2 s (terukur 1,93 s, 0,49 s, 0,20 s). Latensi minimum tetap sekitar 102-106 ms pada semua konfigurasi: penambahan worker mengurangi waktu **menunggu**, bukan waktu layanan. Skala hampir linear karena pekerjaan server adalah `sleep` (menunggu I/O, tidak memakai CPU). Untuk pekerjaan yang terikat CPU, Python dibatasi GIL sehingga menambah thread tidak akan menaikkan throughput sebanding.

### L3.5 (Pengayaan) Failover
`python failover_test.py` menyalakan server di 50051 dan 50052. `ClientFailover` memanggil RPC; bila menerima `UNAVAILABLE` ia berpindah ke alamat berikutnya. Hasil aktual (`L3_5_hasil.txt`):

```
[1] Terhubung ke localhost:50051: Andi, IPK 3.26
[2] Mematikan server 1 ...
localhost:50051 UNAVAILABLE -> pindah ke localhost:50052
[3] Setelah failover, dilayani oleh localhost:50052: Andi, IPK 3.26
[5] NIM salah -> NOT_FOUND (BUKAN UNAVAILABLE, tidak pindah server)
[6] Semua server mati -> UNAVAILABLE dilempar ke pemanggil setelah mencoba semua server
```
Catatan penting: kedua server **tidak berbagi state** (`SALDO`, `PROSES`). Failover aman untuk RPC idempoten seperti `GetMahasiswa`; `Transfer` yang dialihkan ke server kedua tidak terlindungi deduplikasi dari server pertama dan saldonya berbeda. Failover transfer memerlukan penyimpanan bersama atau replikasi.

[SCREENSHOT: L3_5_failover.png]

## 3. Jawaban Pertanyaan Analisis

**Server menyimpan `PROSES` di memori. Apa yang terjadi pada jaminan at-most-once jika server restart?**

1. Data `PROSES` hilang saat proses berhenti karena hanya hidup di RAM.
2. Setelah restart, `request_id` lama tidak dikenal; permintaan lama dianggap **baru**.
3. Contoh: transfer dieksekusi, balasan hilang, server crash lalu restart; client mengulang dengan ID yang sama, server menjalankannya lagi, sehingga transfer ganda dan deduplikasi tidak lagi dapat dijamin.
4. Saldo di memori juga hilang pada restart; masalah persistensi tidak hanya pada `PROSES`.

**Perbaikan:** simpan saldo dan `request_id` di penyimpanan persisten (mis. SQLite) dan perbarui keduanya **dalam satu transaksi atomik**. Jika terpisah (saldo diubah, lalu server crash sebelum ID tercatat), duplikat masih bisa lolos; jika satu transaksi, keduanya berhasil atau gagal bersama. Sketsa (tidak wajib diganti pada implementasi modul, yang sengaja memakai dictionary agar perilaku memori teramati):

```python
import sqlite3
db = sqlite3.connect("bank.db", isolation_level=None, check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS saldo(akun TEXT PRIMARY KEY, nilai REAL)")
db.execute("CREATE TABLE IF NOT EXISTS proses(request_id TEXT PRIMARY KEY, sukses INT, pesan TEXT)")

def transfer(rid, dari, ke, jumlah):
    db.execute("BEGIN IMMEDIATE")              # kunci tulis: serial antar-transaksi
    try:
        baris = db.execute("SELECT sukses, pesan FROM proses WHERE request_id=?", (rid,)).fetchone()
        if baris:                               # duplikat -> hasil lama
            db.execute("COMMIT"); return baris
        (saldo,) = db.execute("SELECT nilai FROM saldo WHERE akun=?", (dari,)).fetchone()
        if saldo < jumlah:
            hasil = (0, "Saldo tidak cukup")
        else:
            db.execute("UPDATE saldo SET nilai=nilai-? WHERE akun=?", (jumlah, dari))
            db.execute("UPDATE saldo SET nilai=nilai+? WHERE akun=?", (jumlah, ke))
            hasil = (1, "OK")
        db.execute("INSERT INTO proses VALUES (?,?,?)", (rid, *hasil))
        db.execute("COMMIT")                    # saldo + request_id tersimpan atomik
        return hasil
    except Exception:
        db.execute("ROLLBACK"); raise
```
Sketsa ini belum dijalankan dalam praktikum ini. Pada praktik, `request_id` lama perlu dihapus berkala (TTL), dan jaminan *exactly-once* tetap membutuhkan protokol tambahan.

## 4. Hasil Pengujian Otomatis
`python -m unittest discover -s pengujian -p "test_l3*.py" -v` -> **14 test, 100% LULUS (OK)** pada Windows 11 (`hasil_pengujian/unittest_praktikum3_windows.txt`). Mencakup deduplikasi, retry timeout dengan ID tetap, penanganan kesalahan permanen, UNAVAILABLE diulang lalu menyerah, mitigasi UUID baru -> transfer ganda, verifikasi race condition dengan dan tanpa LOCK, kenaikan throughput multi-worker, dan failover otomatis.

[SCREENSHOT: L3_unittest.png]

## 5. Kesimpulan dan Kendala

1. Retry dengan request ID tetap + deduplikasi di server memberi semantik at-most-once: 20 transfer menghasilkan A=800, B=700 walau 10 respons terlambat.
2. UUID baru di tiap percobaan merusak jaminan itu: A=680, B=820 (32 eksekusi untuk 20 transfer), sementara total tetap 1500 sehingga kesalahan tidak terlihat dari total.
3. Race condition tidak muncul pada skenario dasar (0/20 eksekusi), tetapi muncul pada 5/5 eksekusi dengan instrumentasi jeda baca-tulis; LOCK menghilangkannya. Tidak terlihatnya race tidak membuktikan keamanan kode.
4. Throughput naik hampir linear dengan `max_workers` (9,89 -> 39,45 -> 97,53 req/s) untuk pekerjaan berbasis tunggu (I/O bound), dan latensi rata-rata turun (1926 -> 486 -> 199 ms).
5. Failover otomatis berhasil untuk RPC idempoten; state tidak dibagi antar-server kecuali diimplementasikan penyimpanan terdistribusi/replikasi.

Kendala & Status: Seluruh fungsionalitas dan pengujian otomatis telah tervalidasi 100% di Windows 11. Contoh sketsa basis data SQLite untuk persistensi restart server merupakan usulan desain arsitektural (belum diimplementasikan dalam praktikum ini). Tangkapan layar aktual terminal Windows perlu diambil mandiri mengikuti `05_LAPORAN/TEMPLATE_SCREENSHOT/PANDUAN_SCREENSHOT.md`.
