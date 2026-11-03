# Panduan Screenshot (diambil manual di Windows)

Screenshot **tidak dibuat otomatis** karena lingkungan pengembangan tidak memiliki terminal Windows Anda.
Ambil dengan `Win + Shift + S`, simpan sesuai nama di bawah ke folder `hasil_pengujian/` praktikum terkait,
lalu masukkan ke laporan menggantikan penanda `[SCREENSHOT: nama.png]`.
Tampilkan jendela terminal yang memuat **perintah dan keluarannya**.

## Praktikum 1 -> 02_PRAKTIKUM_1_XML_RPC/hasil_pengujian/
| Nama file | Isi yang harus tampak | Perintah |
|---|---|---|
| L1_1_server.png | Server berjalan + daftar method + log request | `python server_kalkulator.py` |
| L1_1_client.png | listMethods, hasil, Fault bagi nol, pangkat, akar | `python client_kalkulator.py --tenang` |
| L1_1_verbose.png | Dump HTTP + `<methodCall>` / `<methodResponse>` | `python client_kalkulator.py` |
| L1_2_statistik.png | Hasil statistik + Fault input kosong/tidak valid | `python client_kalkulator.py --tenang` |
| L1_3_datetime.png | Bagian A dan B eksperimen L1.3 | `python l13_eksperimen.py` |
| L1_4_benchmark.png | Tabel benchmark (satu komputer; dua komputer bila sudah) | `python benchmark_l14.py ...` |
| L1_5_server_error.png | ConnectionRefusedError saat server dimatikan | `python demo_l15_client.py` |
| L1_analisis_xml.png | Tabel ukuran XML tambah(5,3) | `python analisis_xml.py` |
| L1_unittest.png | `OK` pada 23 test | `python -m unittest discover -s pengujian -p "test_l1*.py" -v` |

## Praktikum 2 -> 03_PRAKTIKUM_2_GRPC/hasil_pengujian/
| Nama file | Isi | Perintah |
|---|---|---|
| L2_server.png | Server berjalan di 50051 | `python server_grpc.py` |
| L2_1_client_dasar.png | Unary, streaming 0,5 s, NOT_FOUND, INVALID_ARGUMENT | `python client_grpc.py` |
| L2_1_client_banyak.png | Client streaming "4 nilai tersimpan" | `python client_grpc.py banyak` |
| L2_2_diskusi_andi.png, L2_2_diskusi_sari.png | Dua terminal diskusi berdampingan | `python client_grpc.py diskusi Andi` / `Sari` |
| L2_3_client_lama.png | Client lama berhasil terhadap server baru | `cd client_lama; python client_lama.py` |
| L2_4_ukuran.png | Tabel Protobuf vs XML | `python l24_ukuran.py` |
| L2_5_async.png | Serial vs asinkron | `python l25_async.py` |
| L2_unittest.png | `OK` pada 20 test | `python -m unittest discover -s pengujian -p "test_l2*.py" -v` |

## Praktikum 3 -> 04_PRAKTIKUM_3_FAILURE/hasil_pengujian/
| Nama file | Isi | Perintah |
|---|---|---|
| L3_1_transfer.png | Tabel L3.1 (A=800, B=700) | `python transfer_test.py --seed 42` |
| L3_2_uuid.png | Tabel L3.2 + perbandingan | `python uuid_test.py --seed 42` |
| L3_3_concurrency.png | Ringkasan dengan/tanpa LOCK | `python concurrency_test.py` |
| L3_4_benchmark.png | Tabel + tampilan `benchmark_results.png` | `python benchmark.py` |
| L3_5_failover.png | UNAVAILABLE -> pindah server | `python failover_test.py` |
| L3_unittest.png | `OK` pada 14 test | `python -m unittest discover -s pengujian -p "test_l3*.py" -v` |

`benchmark_results.png` dan `benchmark_results.csv` sudah dihasilkan skrip (bukan screenshot).
