# JAWABAN LATIHAN SOAL TEORI RPC
**Mata Kuliah:** Komputasi Paralel dan Terdistribusi (KPT)  
**Topik:** Remote Procedure Calls (RPC)  
**Acuan:** Modul Praktikum Dosen Halaman 3–4  

---

## Bagian A: Pilihan Ganda

1. **Komponen yang bertugas mengemas parameter menjadi pesan di sisi client disebut...**  
   **Jawaban: b. Client stub**  
   *Penjelasan:* Client stub bertindak sebagai proxy lokal di sisi client yang mengabstraksikan pemanggilan prosedur dan bertanggung jawab melakukan *marshalling* terhadap nama prosedur dan argumen/parameter ke dalam format pesan jaringan.

2. **Proses mengubah struktur data menjadi aliran byte untuk dikirim lewat jaringan disebut...**  
   **Jawaban: c. Marshalling**  
   *Penjelasan:* Marshalling (atau serialisasi) adalah proses transformasi struktur data atau objek dalam memori ke format aliran byte (*byte stream*) yang siap ditransmisikan melalui media komunikasi jaringan.

3. **Semantik yang menjamin prosedur tidak pernah dieksekusi lebih dari sekali adalah...**  
   **Jawaban: c. At-most-once**  
   *Penjelasan:* At-most-once menjamin bahwa operasi dieksekusi maksimal satu kali (0 atau 1 kali) dengan memfilter duplikasi permintaan menggunakan Request ID unik di sisi server, sehingga mencegah eksekusi berulang.

4. **Operasi berikut yang paling aman diulang (retry) secara otomatis adalah...**  
   **Jawaban: c. get_saldo(id)**  
   *Penjelasan:* `get_saldo(id)` adalah operasi *idempoten* (bersifat membaca/read-only). Memanggil fungsi ini satu kali atau berkali-kali menghasilkan state sistem yang tetap sama tanpa efek samping, berbeda dengan operasi debit atau transfer.

5. **Format serialisasi yang digunakan gRPC secara bawaan adalah...**  
   **Jawaban: d. Protocol Buffers**  
   *Penjelasan:* gRPC secara default menggunakan Protocol Buffers (Protobuf) sebagai Interface Definition Language (IDL) dan mekanisme serialisasi biner berkinerja tinggi.

6. **Protokol transport yang dipakai gRPC adalah...**  
   **Jawaban: b. HTTP/2**  
   *Penjelasan:* gRPC berjalan di atas HTTP/2, yang menyediakan fitur *multiplexing* koneksi, *bidirectional streaming*, kompresi header (HPACK), dan manajemen aliran (*flow control*).

7. **Mengapa pointer tidak dapat dikirim langsung sebagai parameter RPC?**  
   **Jawaban: b. Ruang alamat client dan server berbeda**  
   *Penjelasan:* Pointer adalah alamat memori virtual lokal pada suatu proses. Mesin client dan server memiliki ruang alamat memori (*address space*) yang terisolasi dan berada pada mesin fisik/proses yang berbeda.

8. **Peran file .proto dalam gRPC adalah sebagai...**  
   **Jawaban: b. IDL / kontrak layanan**  
   *Penjelasan:* File `.proto` mendefinisikan skema antarmuka layanan (*service interface*) dan struktur pesan secara netral bahasa, yang menjadi kontrak komunikasi antara client dan server.

9. **Pada RPC sinkron, apa yang dilakukan client setelah mengirim permintaan?**  
   **Jawaban: b. Menunggu sampai balasan diterima**  
   *Penjelasan:* Pada model synchronous (blocking), thread pemanggil di sisi client akan diblokir (menunggu) hingga server mengembalikan respons atau batas waktu timeout tercapai.

10. **Tipe gRPC yang memungkinkan server mengirim banyak respons untuk satu permintaan adalah...**  
    **Jawaban: b. Server streaming**  
    *Penjelasan:* Server streaming menerima satu permintaan dari client (`unary request`) dan mengembalikan aliran banyak pesan secara bertahap (`stream response`) ke client.

---

## Bagian B: Esai

### 1. Enam Langkah Pemanggilan `add(2, 3)` hingga Hasil `5` Diterima
1. **Pemanggilan Prosedur Lokal di Client:** Program client memanggil fungsi `add(2, 3)` pada **client stub**, seolah-olah memanggil fungsi lokal biasa.
2. **Client-Side Marshalling:** Client stub mengemas (*marshalling*) identifier prosedur (`"add"`) dan parameter (`2`, `3`) ke dalam format serialisasi (misal XML-RPC atau Protobuf).
3. **Transmisi Jaringan:** Pesan yang telah dimarshalling dikirim melalui jaringan (HTTP/TCP) menuju host server.
4. **Server-Side Unmarshalling:** Server stub (skeleton) menerima paket jaringan dan membongkar (*unmarshalling*) byte mentah menjadi identifier prosedur asli dan nilai parameter numerik.
5. **Eksekusi Prosedur Sebenarnya:** Server stub memanggil fungsi `add(2, 3)` yang sebenarnya berjalan pada lingkungan runtime server dan mendapatkan nilai return `5`.
6. **Balasan & Pengembalian Hasil:** Server stub mengemas hasil `5` ke dalam paket respons, mengirimkannya kembali melalui jaringan ke client; client stub membongkar respons tersebut dan menyerahkan nilai `5` ke pemanggil di client.

### 2. Tiga Perbedaan Mendasar Panggilan Lokal vs RPC serta Dampaknya bagi Programmer
1. **Ruang Alamat Memori (Address Space):**
   - *Perbedaan:* Panggilan lokal berbagi memori proses yang sama, sedangkan RPC berjalan di mesin/proses terpisah.
   - *Dampak:* Parameter bertipe pointer/referensi objek kompleks tidak dapat diteruskan langsung; semua data harus dapat diserialisasi (*by-value*, bukan *by-reference*).
2. **Latensi dan Bandwidth:**
   - *Perbedaan:* Panggilan lokal hanya memerlukan waktu beberapa nanodetik/mikrodetik (akses CPU/RAM), sedangkan RPC membutuhkan waktu milidetik (overhead TCP/IP dan fisik jaringan).
   - *Dampak:* Programmer harus meminimalkan frekuensi pemanggilan (*chatty calls*) dan menggabungkan data (*coarse-grained interfaces*) atau menggunakan asynchronous RPC.
3. **Kegagalan Parsial (Partial Failure):**
   - *Perbedaan:* Panggilan lokal bersifat biner (proses hidup atau crash total). Pada RPC, jaringan bisa putus saat server tetap hidup, atau server crash setelah operasi selesai namun balasan hilang.
   - *Dampak:* Programmer wajib menerapkan penanganan error jaringan, timeout, retry policy, dan deduplikasi idempoten.

### 3. Masalah Semantik *At-Least-Once* pada `transfer()` dan Dua Solusinya
- **Masalah:** Fungsi `transfer()` adalah operasi *non-idempoten* (mengubah saldo akun). Jika balasan dari server hilang di tengah jalan, client dengan semantik *at-least-once* akan mengulang pengiriman permintaan. Server yang tidak memiliki pengaman akan mengeksekusi pemindahan saldo untuk kedua kalinya, mengakibatkan penarikan dana berganda (*double debit* / transfer ganda).
- **Dua Cara Mengatasinya:**
  1. **Penerapan Request ID Unik dan Deduplikasi (Menjadi *At-Most-Once*):** Setiap transaksi logis diberi ID unik (misalnya UUID). Server menyimpan tabel histori `PROSES[request_id]`. Jika ID yang sama diterima kembali, server langsung mengembalikan respons tersimpan tanpa memproses ulang mutasi saldo.
  2. **Perancangan Operasi Menjadi Idempoten:** Mengubah antarmuka mutasi dari format imperatif `transfer(jumlah)` menjadi operasi berbasis status/transaksi yang idempoten, misalnya `eksekusi_transaksi(id_transaksi, status="SELESAI")` di mana pemanggilan berulang dengan ID transaksi yang sama tidak menambah mutasi baru.

### 4. Perbandingan XML-RPC, REST/JSON, dan gRPC
| Aspek | XML-RPC | REST / JSON | gRPC |
|---|---|---|---|
| **Format Data** | Teks XML (berbasis tag verbose) | Teks JSON (lebih ringkas dan mudah dibaca manusia) | Biner (Protocol Buffers, sangat terkompresi) |
| **Protokol Transport** | HTTP/1.0 atau HTTP/1.1 (POST saja) | HTTP/1.1 atau HTTP/2 (Metode HTTP: GET, POST, PUT, DELETE) | HTTP/2 murni |
| **Kinerja & Overhead** | Paling lambat; overhead pembungkus tag XML > 95% | Menengah; parsing teks JSON cukup cepat namun tidak sepadat biner | Paling cepat; efisiensi serialisasi biner dan overhead header sangat rendah |
| **Dukungan Streaming** | Tidak mendukung (hanya request-response) | Terbatas (Server-Sent Events / WebSocket terpisah) | Penuh (Unary, Server, Client, dan Bidirectional Streaming bawaan) |

### 5. Perbedaan RPC Sinkron vs Asinkron dan Contoh Kasusnya
- **Perbedaan:**
  - *RPC Sinkron:* Pemanggil memblokir (*block*) eksekusi thread-nya sampai menerima jawaban lengkap dari server. Cocok untuk operasi cepat di mana langkah berikutnya mutlak memerlukan data balasan (misal otentikasi login).
  - *RPC Asinkron:* Pemanggil langsung menerima objek penampung (*Future* atau *Promise*) dan dapat segera melanjutkan tugas komputasi lainnya. Hasil pemanggilan diambil kemudian melalui polling `.result()` atau fungsi *callback*.
- **Contoh Kasus yang Cocok untuk RPC Asinkron:**
  - *Pemrosesan Rendering Video atau Komputasi Saintifik:* Client aplikasi web mengirimkan tugas encoding video resolusi tinggi ke server backend rendering. Menggunakan RPC asinkron memungkinkan client tetap responsif melayani antarmuka pengguna tanpa membekukan (*freeze*) aplikasi selama proses rendering yang memakan waktu lama berlangsung.

