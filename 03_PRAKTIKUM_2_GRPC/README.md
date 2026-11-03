# Praktikum 2 - gRPC dan Protocol Buffers

## File
| File | Fungsi |
|---|---|
| `akademik.proto` | Kontrak layanan (v2, dengan `prodi = 4`) |
| `akademik_pb2.py`, `akademik_pb2_grpc.py` | **Hasil generate** - jangan diedit manual |
| `server_grpc.py` | Server (port 50051, `ThreadPoolExecutor(max_workers=10)`) |
| `client_grpc.py` | Client: `dasar`, `banyak` (L2.1), `diskusi` (L2.2) |
| `client_lama/` | Schema v1 + stub lama + `client_lama.py` untuk L2.3 |
| `l24_ukuran.py` | L2.4: ukuran Protobuf vs XML-RPC |
| `l25_async.py` | L2.5: `.future()` x 10 vs serial |
| `pengujian/test_l21.py` ... `test_l25.py` | Unit test otomatis (20 test) |

## PENTING: generate ulang stub di komputer Anda
Stub yang ikut di folder ini digenerate dengan protobuf 7.x dan mengunci versi runtime tersebut. Agar cocok dengan
versi `protobuf` di venv Anda, **selalu generate ulang** (PowerShell, dari folder ini):
```powershell
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. akademik.proto
# stub client lama (schema v1) - dari DALAM client_lama:
cd client_lama
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. akademik.proto
cd ..
```
Periksa versi: `python -m pip list | findstr /i "grpcio protobuf"`.

## Menjalankan
```powershell
cd "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC"
.\venv\Scripts\Activate.ps1
cd 03_PRAKTIKUM_2_GRPC
```
**Terminal 1:** `python server_grpc.py`

**Terminal 2:**
```powershell
python client_grpc.py                       # unary + server streaming + error NOT_FOUND / INVALID_ARGUMENT
python client_grpc.py banyak                # L2.1 client streaming
python l24_ukuran.py                        # L2.4 (tanpa server)
python l25_async.py                         # L2.5 (menyalakan server sendiri)
```
**L2.2 ruang diskusi** (butuh 2-3 terminal client selain server):
```powershell
python client_grpc.py diskusi Andi          # ketik pesan, /keluar untuk selesai
python client_grpc.py diskusi Sari          # terminal lain
python client_grpc.py diskusi Budi --otomatis   # kirim 4 pesan otomatis
```
**L2.3 client lama vs server baru** (server baru harus aktif di Terminal 1):
```powershell
cd client_lama
python client_lama.py
```

## Pengujian otomatis
```powershell
python -m unittest discover -s pengujian -p "test_l2*.py" -v
```
Catatan: bila server dijalankan dua kali pada port yang sama, server kedua gagal dengan pesan jelas
(`grpc.so_reuseport` dimatikan agar perilaku sama di Linux dan Windows).
