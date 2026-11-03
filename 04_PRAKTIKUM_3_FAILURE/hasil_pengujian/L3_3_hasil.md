# L3.3 Race condition (hasil aktual)

Target tanpa race: A=500, B=1000, total=1500, transaksi=50.

## Bagian 1 - Pengujian dasar (sesuai modul, tanpa instrumentasi)

| Kondisi | Saldo A | Saldo B | Total | Transaksi dieksekusi | Sukses | Gagal |
|---|---:|---:|---:|---:|---:|---:|
| DENGAN LOCK (1 eksekusi) | 500 | 1000 | 1500 | 50 | 50 | 0 |
| TANPA LOCK (1 eksekusi) | 500 | 1000 | 1500 | 50 | 50 | 0 |

Pengulangan 20x: DENGAN LOCK menyimpang 0/20 eksekusi; TANPA LOCK menyimpang 0/20 eksekusi.

## Bagian 2 - Pengujian TAMBAHAN (instrumentasi: jeda 2 ms antara baca dan tulis saldo)

| Kondisi | Saldo A | Saldo B | Total | Transaksi dieksekusi | Sukses | Gagal |
|---|---:|---:|---:|---:|---:|---:|
| TANPA LOCK #1 | 920 | 570 | 1490 | 50 | 50 | 0 |
| TANPA LOCK #2 | 890 | 610 | 1500 | 50 | 50 | 0 |
| TANPA LOCK #3 | 890 | 610 | 1500 | 50 | 50 | 0 |
| TANPA LOCK #4 | 950 | 550 | 1500 | 50 | 50 | 0 |
| TANPA LOCK #5 | 930 | 560 | 1490 | 50 | 50 | 0 |
| DENGAN LOCK #1 | 500 | 1000 | 1500 | 50 | 50 | 0 |
| DENGAN LOCK #2 | 500 | 1000 | 1500 | 50 | 50 | 0 |
| DENGAN LOCK #3 | 500 | 1000 | 1500 | 50 | 50 | 0 |
| DENGAN LOCK #4 | 500 | 1000 | 1500 | 50 | 50 | 0 |
| DENGAN LOCK #5 | 500 | 1000 | 1500 | 50 | 50 | 0 |

Instrumentasi: TANPA LOCK menyimpang 5/5; DENGAN LOCK menyimpang 0/5.

## Bagian 3 - Pengujian TAMBAHAN: 10 permintaan DUPLIKAT (request_id sama) bersamaan

Yang benar: transfer dieksekusi SATU kali (A=990). Jeda 10 ms disisipkan agar interleaving terjadi.

| Kondisi | Saldo A | Saldo B | Transaksi dieksekusi |
|---|---:|---:|---:|
| TANPA LOCK | 990 | 510 | 10 |
| DENGAN LOCK | 990 | 510 | 1 |
