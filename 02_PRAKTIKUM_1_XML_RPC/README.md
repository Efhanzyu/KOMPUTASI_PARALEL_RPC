# Praktikum 1 - RPC Dasar dengan XML-RPC

Hanya memakai library bawaan Python (`xmlrpc.server`, `xmlrpc.client`). Server memakai port **8000**.

## Daftar File

| File | Fungsi |
|---|---|
| `server_kalkulator.py` | Server: tambah, kali, bagi, pangkat, akar, statistik + fungsi uji L1.3 |
| `client_kalkulator.py` | Client: menguji semua method, `verbose=True`, penanganan error berlapis |
| `analisis_xml.py` | Mengukur ukuran XML `tambah(5,3)` dari byte mentah (proxy TCP perekam) |
| `l13_eksperimen.py` | L1.3: datetime dan bilangan > 2^31 (pengujian asli + solusi alternatif) |
| `benchmark_l14.py` | L1.4: 100 panggilan lokal vs RPC (`time.perf_counter`) |
| `demo_l15_client.py` | L1.5: demo manual mematikan server saat client aktif |
| `PANDUAN_BENCHMARK_DUA_KOMPUTER.md` | Panduan lengkap langkah uji jaringan 2 komputer (IP, firewall, routing) |
| `pengujian/test_l11.py` s.d. `test_l15.py` | Unit test otomatis (23 test, 100% lulus) |
| `hasil_pengujian/` | Folder keluaran aktual (log teks dan file CSV) |

## Persiapan (PowerShell)

```powershell
cd "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC"
.\venv\Scripts\Activate.ps1
cd 02_PRAKTIKUM_1_XML_RPC
```

## Menjalankan

**Terminal 1 (Server):**

```powershell
python server_kalkulator.py
```

**Terminal 2 (Client):**

```powershell
python client_kalkulator.py                       # verbose=True: tampil HTTP + <methodCall>/<methodResponse>
python client_kalkulator.py --tenang              # tanpa dump XML (output ringkas)
python l13_eksperimen.py                          # L1.3 (server di terminal 1 harus aktif)
python analisis_xml.py                            # mandiri (menyalakan server uji internal)
python benchmark_l14.py --host 127.0.0.1 --label satu-komputer-loopback
```

> **Catatan Server:**
>
> 1. Setiap kali `server_kalkulator.py` diubah, tekan `Ctrl+C` di Terminal 1 lalu jalankan ulang.
> 2. Error `method "pangkat" is not supported` terjadi jika proses server lama masih aktif di port 8000.
> 3. Cek method aktif dengan: `python -c "import xmlrpc.client as c; print(c.ServerProxy('http://127.0.0.1:8000/').system.listMethods())"`
> 4. Jika port 8000 masih terkunci oleh proses lama:
>    ```powershell
>    Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
>    Stop-Process -Id <PID> -Force
>    ```

## L1.4 - Pengujian Dua Komputer

File `hasil_pengujian/L1_4_benchmark_satu-komputer-loopback.csv` merupakan hasil **loopback satu komputer**.

Petunjuk pengujian dua komputer fisik:

1. Baca panduan lengkap pada file: `PANDUAN_BENCHMARK_DUA_KOMPUTER.md`.
2. Komputer 1 (Server):
   - Cek IPv4 via `ipconfig`.
   - Buka firewall:
     ```powershell
     New-NetFirewallRule -DisplayName "XMLRPC 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
     ```
   - Jalankan: `python server_kalkulator.py`
3. Komputer 2 (Client):
   - Jalankan:
     ```powershell
     python benchmark_l14.py --host <IP_SERVER> --label dua-komputer
     ```
4. Hasil otomatis tersimpan di `hasil_pengujian/L1_4_benchmark_dua-komputer.csv`.

## L1.5 - Uji Toleransi Kegagalan (Manual)

1. Jalankan server di Terminal 1: `python server_kalkulator.py`
2. Jalankan client di Terminal 2: `python demo_l15_client.py`
3. Tekan `Ctrl+C` di Terminal 1 untuk mematikan server.
4. Terminal 2 akan mendeteksi `[ConnectionRefusedError]` secara tertangani tanpa membuat program crash.
5. Jalankan kembali server di Terminal 1; client akan otomatis pulih pada panggilan berikutnya.

## Pengujian Otomatis (Unit Test)

```powershell
python -m unittest discover -s pengujian -p "test_l1*.py" -v
```

Pengujian memakai port acak bebas (port 0) di thread internal sehingga tidak bentrok dengan server port 8000. Seluruh 23 unit test terverifikasi **LULUS (100%)** di Windows 11.

