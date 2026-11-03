# PANDUAN PENGUJIAN L1.4: BENCHMARK DUA KOMPUTER (XML-RPC)

Panduan ini disusun untuk pengujian **L1.4: Perbandingan Kinerja Pemanggilan Fungsi Lokal vs XML-RPC pada Dua Komputer Berbeda**.

> [!IMPORTANT]
> **STATUS SAAT INI: BELUM DILAKUKAN (Menunggu Komputer Kedua)**
> Hasil benchmark yang saat ini tersedia di file `hasil_pengujian/L1_4_benchmark_satu-komputer-loopback.csv` adalah hasil pengujian **satu komputer (loopback `127.0.0.1`)**, bukan pengujian dua komputer yang diminta modul. Jangan mengklaim hasil loopback sebagai hasil pengujian dua komputer.

---

## 1. Topologi Jaringan & Kebutuhan

- **Komputer A (Server):** Laptop Windows 11 ini (tempat kode berjalan).
- **Komputer B (Client):** Laptop / PC lain yang berada dalam satu jaringan lokal (Wi-Fi atau kabel LAN yang sama).
- **Protokol:** TCP Port 8000 (XML-RPC).

---

## 2. Langkah di Komputer Server (Komputer A)

### Langkah 2.1: Cari Alamat IPv4 Server
Buka terminal PowerShell:
```powershell
ipconfig
```
Cari bagian adapter jaringan yang sedang aktif (misalnya `Wireless LAN adapter Wi-Fi` atau `Ethernet adapter Ethernet`).
Catat alamat **IPv4 Address**, misalnya: `192.168.1.25`.

### Langkah 2.2: Buka Port 8000 di Windows Firewall
Jalankan PowerShell sebagai **Administrator**:
```powershell
New-NetFirewallRule -DisplayName "XMLRPC 8000 KPT" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

### Langkah 2.3: Jalankan Server XML-RPC
Di direktori proyek:
```powershell
cd "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\02_PRAKTIKUM_1_XML_RPC"
..\venv\Scripts\python.exe server_kalkulator.py
```
Server akan mengikat ke `0.0.0.0:8000` dan siap menerima permintaan dari jaringan luar.

---

## 3. Langkah di Komputer Client (Komputer B)

### Langkah 3.1: Salin Script Benchmark ke Komputer B
Salin file `benchmark_l14.py` dan `server_kalkulator.py` (hanya untuk fungsi lokal pembanding) ke Komputer B.
Pastikan Python 3 sudah terpasang di Komputer B.

### Langkah 3.2: Uji Konektivitas Jaringan ke Server
Buka PowerShell di Komputer B dan jalankan:
```powershell
Test-NetConnection -ComputerName 192.168.1.25 -Port 8000
```
*(Ganti `192.168.1.25` dengan IP server aktual)*.
Pastikan output menunjukkan:
```text
TcpTestSucceeded : True
```

### Langkah 3.3: Jalankan Benchmark 100 Pemanggilan
Jalankan script benchmark dengan flag `--host` dan `--label dua-komputer`:
```powershell
python benchmark_l14.py --host 192.168.1.25 --port 8000 --label dua-komputer --jumlah 100
```

Script akan:
1. Melakukan 1 panggilan pemanasan (handshake TCP/HTTP).
2. Mengukur 100 kali panggilan fungsi lokal `tambah(a, b)` dengan `time.perf_counter()`.
3. Mengukur 100 kali panggilan RPC `proxy.tambah(a, b)` melalui jaringan Wi-Fi/LAN.
4. Menghitung rata-rata dan rasio overhead.
5. Menyimpan hasil resmi ke file `hasil_pengujian/L1_4_benchmark_dua-komputer.csv`.

---

## 4. Format Laporan Hasil Pengujian

Setelah pengujian dilakukan, catat hasil aktual ke dalam tabel berikut:

| Jenis pemanggilan | Jumlah | Waktu total (s) | Rata-rata per panggilan (ms) |
|---|---:|---:|---:|
| Fungsi lokal | 100 | *(Aktual)* | *(Aktual)* |
| XML-RPC dua komputer | 100 | *(Aktual)* | *(Aktual)* |

**Format file CSV hasil (`L1_4_benchmark_dua-komputer.csv`):**
```csv
jenis,jumlah,waktu_total_s,waktu_rata2_ms,host,port,label
Fungsi lokal,100,<waktu_lokal>,<rata_lokal>,192.168.1.25,8000,dua-komputer
XML-RPC,100,<waktu_rpc>,<rata_rpc>,192.168.1.25,8000,dua-komputer
rasio_rpc_per_lokal,,<rasio>,,192.168.1.25,8000,dua-komputer
```

---

## 5. Pembersihan Setelah Pengujian

Setelah pengujian selesai, tutup server dengan menekan `Ctrl+C` di Komputer A.
Hapus aturan firewall di Komputer A (PowerShell Administrator):
```powershell
Remove-NetFirewallRule -DisplayName "XMLRPC 8000 KPT"
```

---

## 6. Troubleshooting Masalah Jaringan

1. **`ConnectionRefusedError: [WinError 10061]`**:
   - Server belum berjalan di Komputer A.
   - IP yang dimasukkan salah.
2. **Koneksi hang / Timeout**:
   - Windows Firewall memblokir port 8000. Pastikan langkah 2.2 sudah dijalankan.
   - Komputer A dan B berada di subnet/VLAN berbeda (misalnya isolasi klien Wi-Fi publik/tethering). Gunakan hotspot tethering yang sama atau hubungkan via kabel LAN.
3. **Port 8000 bentrok**:
   - Periksa port dengan `netstat -ano | findstr :8000`.
   - Hentikan proses lama dengan `taskkill /PID <pid> /F`.

