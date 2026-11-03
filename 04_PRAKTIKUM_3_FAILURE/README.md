# Praktikum 3 - Concurrency, Timeout, dan Toleransi Kegagalan

Kode dipisah dari Praktikum 2 (proto, stub, server, dan client sendiri).

## File
| File | Fungsi |
|---|---|
| `akademik.proto` | RPC P2 yang dibutuhkan + `Transfer` / `TransferRequest` |
| `akademik_pb2*.py` | Hasil generate (jangan diedit) |
| `server_grpc.py` | Server: `SALDO`, `PROSES`, `LOCK`, respons lambat 30% (3 s), opsi eksperimen |
| `client_grpc.py` | `transfer_dengan_retry` (timeout 2 s, 3 percobaan, backoff) dan `ClientFailover` |
| `transfer_test.py` | L3.1 - 20 transfer, request ID tetap |
| `uuid_test.py` | L3.2 - UUID baru tiap percobaan (+ pembanding L3.1) |
| `concurrency_test.py` | L3.3 - 50 transfer, 10 thread, dengan/tanpa LOCK |
| `benchmark.py` | L3.4 - throughput 1/4/10 worker, CSV + PNG |
| `failover_test.py` | L3.5 - failover 50051 -> 50052 (pengayaan) |
| `pengujian/test_l31.py` ... `test_l35.py` | Unit test cepat (14 test) |

## Persiapan
```powershell
cd "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC"
.\venv\Scripts\Activate.ps1
python -m pip install matplotlib        # hanya untuk grafik L3.4
cd 04_PRAKTIKUM_3_FAILURE
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. akademik.proto   # generate ulang stub
```

## Menjalankan eksperimen
Skrip L3.1-L3.3 menyalakan server **in-process** sendiri (port bebas), jadi cukup satu terminal. Saldo
diverifikasi langsung dari memori server.
```powershell
python transfer_test.py --seed 42        # L3.1 (~25 detik)
python uuid_test.py --seed 42            # L3.2 (~1 menit, termasuk pembanding L3.1)
python concurrency_test.py --ulang 20    # L3.3
python benchmark.py                      # L3.4 (~35 detik; server per konfigurasi di port 50151-50153)
python failover_test.py                  # L3.5 (butuh port 50051 dan 50052 bebas)
```
`--seed` membuat urutan respons lambat dapat diulang; tanpa seed yang sama angka L3.2 akan berbeda.

### Demo manual dengan dua terminal
**Terminal 1:** `python server_grpc.py` (opsi: `--workers 4`, `--tanpa-lock`, `--jeda-get 0.1`, `--prob-lambat 0.3`)
**Terminal 2:** `python client_grpc.py` atau `python client_grpc.py --uuid-baru`
Tekan `Ctrl+C` di Terminal 1 untuk melihat saldo akhir dan jumlah eksekusi/duplikat.

## Pengujian otomatis
```powershell
python -m unittest discover -s pengujian -p "test_l3*.py" -v
```

## Catatan metodologi
* `--tanpa-lock` setara menghapus `with LOCK:` (kode memakai `contextlib.nullcontext()` agar dapat diuji bergantian).
* Pada skenario dasar L3.3 race condition **tidak terlihat** (0/20 eksekusi menyimpang); ini hasil aktual dan
  dijelaskan di laporan. Pengujian tambahan berinstrumentasi (jeda baca-tulis) dipisah jelas dari pengujian dasar.
* Log "Got goaway ... Cancelling all calls" dari inti gRPC saat server dihentikan hanyalah informasi, bukan error.
