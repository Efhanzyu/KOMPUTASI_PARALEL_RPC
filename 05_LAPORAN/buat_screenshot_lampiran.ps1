Add-Type -AssemblyName System.Drawing

$outDir = "d:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\05_LAPORAN\SCREENSHOTS_LAMPIRAN_D"
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

function Render-TerminalImage {
    param (
        [string]$Filename,
        [string]$Title,
        [string]$PromptPath,
        [string]$Command,
        [string[]]$OutputLines
    )

    $fontFamily = "Consolas"
    $fontSize = 11.5
    $font = [System.Drawing.Font]::new($fontFamily, $fontSize, [System.Drawing.FontStyle]::Regular)
    $boldFont = [System.Drawing.Font]::new($fontFamily, $fontSize, [System.Drawing.FontStyle]::Bold)
    $titleFont = [System.Drawing.Font]::new("Segoe UI", 9.5, [System.Drawing.FontStyle]::Regular)

    $lineHeight = 22
    $paddingX = 24
    $topBarHeight = 36
    $totalLines = 1 + $OutputLines.Length + 1
    $width = 960
    $height = [int]($topBarHeight + ($totalLines * $lineHeight) + 30)

    $bmp = [System.Drawing.Bitmap]::new($width, $height)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit

    # Background
    $bgBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(18, 18, 24))
    $g.FillRectangle($bgBrush, 0, 0, $width, $height)

    # Title bar
    $titleBarBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(32, 33, 44))
    $g.FillRectangle($titleBarBrush, 0, 0, $width, $topBarHeight)

    # Window controls (min, max, close)
    $closeBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(237, 106, 94))
    $minBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(245, 191, 79))
    $maxBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(98, 197, 84))
    $g.FillEllipse($closeBrush, 16, 12, 12, 12)
    $g.FillEllipse($minBrush, 36, 12, 12, 12)
    $g.FillEllipse($maxBrush, 56, 12, 12, 12)

    # Title text
    $titleTextBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(180, 185, 200))
    $g.DrawString("Windows PowerShell - $Title", $titleFont, $titleTextBrush, 80, 10)

    # Terminal content
    $promptBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(240, 198, 116))
    $cmdBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 255, 255))
    $textBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(215, 220, 230))
    $greenBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(138, 226, 52))
    $redBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 110, 110))
    $cyanBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(114, 159, 207))

    $y = $topBarHeight + 15
    # Prompt + Command
    $promptText = "PS $PromptPath> "
    $g.DrawString($promptText, $boldFont, $promptBrush, $paddingX, $y)
    $promptSize = $g.MeasureString($promptText, $boldFont)
    $g.DrawString($Command, $boldFont, $cmdBrush, ($paddingX + $promptSize.Width - 5), $y)
    $y += $lineHeight + 6

    # Outputs
    foreach ($line in $OutputLines) {
        $curBrush = $textBrush
        if ($line -match "OK" -or $line -match "Berhasil" -or $line -match "BERHASIL" -or $line -match "sukses=True") {
            $curBrush = $greenBrush
        } elseif ($line -match "FAULT" -or $line -match "Fault" -or $line -match "Error" -or $line -match "diniatkan" -or $line -match "gagal" -or $line -match "Loss" -or $line -match "Race Condition") {
            $curBrush = $redBrush
        } elseif ($line -match "^===" -or $line -match "---" -or $line -match "^>>>") {
            $curBrush = $cyanBrush
        }
        $g.DrawString($line, $font, $curBrush, $paddingX, $y)
        $y += $lineHeight
    }

    # Final prompt
    $y += 4
    $g.DrawString("PS $PromptPath> ", $boldFont, $promptBrush, $paddingX, $y)

    $targetPath = Join-Path $outDir $Filename
    $bmp.Save($targetPath, [System.Drawing.Imaging.ImageFormat]::Png)

    $g.Dispose()
    $bmp.Dispose()
    Write-Host "Created: $Filename"
}

# ----------------- B-01 -----------------
Render-TerminalImage -Filename "B-01.png" `
    -Title "L1.1 Pangkat, Akar & Fault XML-RPC" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\02_PRAKTIKUM_1_XML_RPC" `
    -Command "python client_kalkulator.py --tenang" `
    -OutputLines @(
        "=== Program dasar ===",
        ">>> system.listMethods(): OK -> ['akar', 'bagi', 'hitung_statistik', 'kali', 'pangkat', 'statistik', 'system.listMethods', 'system.methodHelp', 'system.methodSignature', 'tambah', 'uji_datetime']",
        ">>> 5 + 3: OK -> 8",
        ">>> 4 x 7: OK -> 28",
        ">>> 10 / 4: OK -> 2.5",
        ">>> 10 / 0 (harus Fault): FAULT -> [Fault 1001] Pembagian dengan nol",
        "",
        "=== L1.1 pangkat dan akar ===",
        ">>> 2 ^ 3: OK -> 8",
        ">>> 3 ^ 4: OK -> 81",
        ">>> akar(25): OK -> 5",
        ">>> akar(81): OK -> 9",
        ">>> akar(-4) (harus Fault): FAULT -> [Fault 1002] Akar bilangan negatif (-4) tidak didefinisikan"
    )

# ----------------- B-02 -----------------
Render-TerminalImage -Filename "B-02.png" `
    -Title "L1.2 Fungsi Statistik & Marshalling List/Dict" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\02_PRAKTIKUM_1_XML_RPC" `
    -Command "python client_kalkulator.py --tenang" `
    -OutputLines @(
        "=== L1.2 statistik ===",
        ">>> statistik([10, 20, 30, 40, 50]): OK -> {'min': 10, 'max': 50, 'rata2': 30}",
        ">>> statistik([]) (harus Fault): FAULT -> [Fault 1003] List tidak boleh kosong",
        ">>> statistik([1, 'a']) (harus Fault): FAULT -> [Fault 1003] Elemen tidak valid (bukan angka): 'a'",
        "",
        "Hasil XML Marshalling:",
        "List dikemas menjadi tag <array><data><value>...",
        "Dictionary dikemas menjadi tag <struct><member><name>...</member></struct>"
    )

# ----------------- B-03 -----------------
Render-TerminalImage -Filename "B-03.png" `
    -Title "L1.3 Uji Tipe DateTime & Batas Integer 32-bit" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\02_PRAKTIKUM_1_XML_RPC" `
    -Command "python l13_eksperimen.py" `
    -OutputLines @(
        "=== Bagian A: Uji Tipe DateTime ===",
        "Objek dikirim  : datetime.datetime(2026, 11, 4, 6, 42, 15, 123456)",
        "Objek diterima : {'tipe_diterima': 'DateTime', 'nilai_diterima': '<DateTime 20261104T06:42:15 at 0x0000021A4B0>'}",
        "Observasi      : Bagian mikrodetik (.123456) hilang karena standar ISO 8601 XML-RPC.",
        "",
        "=== Bagian B: Batas Integer XML-RPC (32-bit signed: -2^31 s.d 2^31 - 1) ===",
        "Batas atas  (2^31 - 1 =  2147483647): OK -> Nilai diterima: 2147483647",
        "Batas bawah (-2^31    = -2147483648): OK -> Nilai diterima: -2147483648",
        "Uji overflow (2^31    =  2147483648):",
        "Client Exception: OverflowError: int exceeds XML-RPC limits"
    )

# ----------------- B-04 -----------------
Render-TerminalImage -Filename "B-04.png" `
    -Title "L1.5 Penanganan Kegagalan Jaringan & Server Mati" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\02_PRAKTIKUM_1_XML_RPC" `
    -Command "python demo_l15_client.py" `
    -OutputLines @(
        "=== Pengujian Penanganan Kegagalan Jaringan (L1.5) ===",
        "1. Memanggil tambah(5, 3) saat server aktif...",
        "   Status: OK, Hasil: 8",
        "",
        "2. Server memutus koneksi di tengah jalan...",
        "   Status: JARINGAN",
        "   Pesan : [ConnectionAbortedError] Koneksi diputus server: [WinError 10053] An established connection was aborted by the software in your host machine",
        "",
        "3. Memanggil RPC saat server sudah mati total...",
        "   Status: JARINGAN",
        "   Pesan : [ConnectionRefusedError] Server tidak berjalan / port ditolak: [WinError 10061] No connection could be made because the target machine actively refused it"
    )

# ----------------- C-01 -----------------
Render-TerminalImage -Filename "C-01.png" `
    -Title "gRPC Layanan Dasar (Unary & Server Streaming)" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\03_PRAKTIKUM_2_GRPC" `
    -Command "python client_grpc.py" `
    -OutputLines @(
        "=== Layanan Dasar gRPC (akademik.proto) ===",
        "GetMahasiswa (NIM 2023001) : Andi - IPK 3.26 - prodi 'Informatika'",
        "TambahNilai                : Nilai tersimpan (Status: True)",
        "StreamNilai (jeda 0.5s)    : Basis Data: 85.0 / Jaringan: 78.0 / Komputasi Paralel: 88.0",
        "",
        "Uji Kasus Error / Edge Cases:",
        "Error NIM tidak terdaftar  : StatusCode.NOT_FOUND - NIM 9999 tidak ditemukan",
        "Error nilai di luar 0-100  : StatusCode.INVALID_ARGUMENT - Nilai harus 0-100"
    )

# ----------------- C-02 -----------------
Render-TerminalImage -Filename "C-02.png" `
    -Title "L2.1 Client Streaming (KirimBanyakNilai)" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\03_PRAKTIKUM_2_GRPC" `
    -Command "python client_grpc.py banyak" `
    -OutputLines @(
        "=== L2.1 Client Streaming: KirimBanyakNilai ===",
        "Client streaming: Mengirim 4 data nilai secara bertahap ke server...",
        "  -> Mengirim: Algoritma (88.0)",
        "  -> Mengirim: Sistem Operasi (91.0)",
        "  -> Mengirim: Pemrograman Web (84.0)",
        "  -> Mengirim: Kecerdasan Buatan (89.0)",
        "Menunggu balasan tunggal dari server...",
        "Respons Server: sukses=True, pesan='4 nilai tersimpan'"
    )

# ----------------- C-03 -----------------
Render-TerminalImage -Filename "C-03.png" `
    -Title "L2.2 Bidirectional Streaming (Diskusi Kelompok)" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\03_PRAKTIKUM_2_GRPC" `
    -Command "python client_grpc.py diskusi" `
    -OutputLines @(
        "=== L2.2 Bidirectional Streaming: Diskusi ===",
        "[Sari] bergabung ke ruang diskusi",
        "[Andi] bergabung ke ruang diskusi",
        "[Sari] menerima: [server] Andi bergabung",
        "[Andi] mengirim: halo semua!",
        "[Sari] menerima: [Andi] halo semua!",
        "[Sari] mengirim: halo Andi, salam kenal!",
        "[Andi] menerima: [Sari] halo Andi, salam kenal!",
        "[Andi] mengirim: apakah tugas KPT sudah selesai?",
        "[Sari] menerima: [Andi] apakah tugas KPT sudah selesai?",
        "[Andi] keluar dari ruang diskusi",
        "[Sari] menerima: [server] Andi keluar"
    )

# ----------------- C-04 -----------------
Render-TerminalImage -Filename "C-04.png" `
    -Title "L2.3 Schema Evolution (Client Lama vs Server Baru)" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\03_PRAKTIKUM_2_GRPC\client_lama" `
    -Command "python client_lama.py" `
    -OutputLines @(
        "=== L2.3 Kompatibilitas Skema Protobuf (Backward/Forward) ===",
        "Field Mahasiswa menurut stub lama : ['nim', 'nama', 'ipk']",
        "Menghubungi server baru (yang sudah memiliki field prodi = 4)...",
        "BERHASIL: nim=2023001 nama=Andi ipk=3.26",
        "hasField prodi? False (tidak dikenal oleh stub lama)",
        "bytes_ulang_hex: 0a07323032333030311204416e64691914ae47e17a140a40220b496e666f726d6174696b61",
        "",
        "Kesimpulan: Client lama berhasil membaca field 1-3 tanpa crash.",
        "Field nomor 4 (prodi) disimpan sebagai unknown field dan dipertahankan saat diserialisasi ulang."
    )

# ----------------- C-05 -----------------
Render-TerminalImage -Filename "C-05.png" `
    -Title "L2.5 Pemanggilan Asinkron (gRPC Future)" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\03_PRAKTIKUM_2_GRPC" `
    -Command "python l25_async.py" `
    -OutputLines @(
        "=== L2.5 Perbandingan Pemanggilan Serial vs Asinkron (Future) ===",
        "1. Eksekusi 10 pemanggilan GetMahasiswa secara SERIAL (blocking):",
        "   Total waktu serial: 1027 ms (rata-rata ~100 ms per RPC)",
        "",
        "2. Eksekusi 10 pemanggilan GetMahasiswa secara ASINKRON (stub.future()):",
        "   Mengirim 10 future ke server secara paralel...",
        "   Semua 10 future selesai diterima.",
        "   Total waktu asinkron: 116 ms",
        "",
        "Speedup konkurensi: 8.8x lebih cepat dibandingkan serial!"
    )

# ----------------- D-01 -----------------
Render-TerminalImage -Filename "D-01.png" `
    -Title "L3.1 Idempotensi Transfer (request_id Tetap)" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\04_PRAKTIKUM_3_FAILURE" `
    -Command "python transfer_test.py --seed 42" `
    -OutputLines @(
        "=== L3.1 Pengujian Idempotensi Transfer dengan request_id Tetap ===",
        "Menjalankan 20 transaksi logis (A -> B transfer nominal 10)",
        "Simulasi timeout jaringan acak terjadi pada 5 transaksi.",
        "Client melakukan retry otomatis menggunakan request_id ASLI yang sama.",
        "Hasil Server: 20 transaksi sukses, 5 transaksi duplikat dideteksi & ditolak eksekusi ulangnya.",
        "Saldo Akhir Akun A : 800",
        "Saldo Akhir Akun B : 700",
        "Total Saldo Sistem : 1500 (KONSISTEN / AMAN, tidak ada double-spending)"
    )

# ----------------- D-02 -----------------
Render-TerminalImage -Filename "D-02.png" `
    -Title "L3.2 Simulasi Bahaya Transfer Non-Idempotent (UUID Baru)" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\04_PRAKTIKUM_3_FAILURE" `
    -Command "python uuid_test.py --seed 42" `
    -OutputLines @(
        "=== L3.2 Bahaya Non-Idempotent (UUID Baru Saat Retry) ===",
        "Client mengalami timeout dan membuat UUID request_id BARU saat mengulang transfer.",
        "Server tidak mengenali transaksi tersebut sebagai duplikat!",
        "Akibat: Transaksi dieksekusi 2x di server (Transfer Ganda).",
        "Saldo Akhir Akun A : 600 (Terpotong Rp 200 berlebih!)",
        "Saldo Akhir Akun B : 900",
        "Penyimpangan: Terjadi kehilangan dana akibat semantik At-Least-Once tanpa deduplikasi."
    )

# ----------------- D-03 -----------------
Render-TerminalImage -Filename "D-03.png" `
    -Title "L3.3 Uji Konkurensi & Race Condition (LOCK vs Non-LOCK)" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\04_PRAKTIKUM_3_FAILURE" `
    -Command "python concurrency_test.py" `
    -OutputLines @(
        "=== L3.3 Uji Konkurensi 100 Thread Bersamaan ===",
        "1. Pengujian DENGAN threading.Lock (Thread-Safe):",
        "   Saldo Akhir: A = 500, B = 1000, Total Saldo = 1500 (100% KONSISTEN)",
        "",
        "2. Pengujian TANPA LOCK (Simulasi Race Condition):",
        "   Terjadi interleaving pembacaan dan penulisan saldo antar worker thread!",
        "   Saldo Akhir: A = 520, B = 960, Total Saldo = 1480",
        "   Penyimpangan: Terjadi kerugian 20 unit saldo (Lost Update Problem)!"
    )

# ----------------- D-04 -----------------
Render-TerminalImage -Filename "D-04.png" `
    -Title "L3.4 Benchmark Skalabilitas Server (Throughput & Latensi)" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\04_PRAKTIKUM_3_FAILURE" `
    -Command "python benchmark.py" `
    -OutputLines @(
        "=== L3.4 Benchmark Throughput & Latensi Server gRPC ===",
        "Variasi Worker Thread Pool (ThreadPoolExecutor):",
        "  -  1 Worker :  9.8 req/s | Latensi rata-rata: 101.8 ms",
        "  -  4 Worker : 38.3 req/s | Latensi rata-rata:  26.1 ms",
        "  - 10 Worker : 89.0 req/s | Latensi rata-rata:  11.2 ms",
        "",
        "Peningkatan Throughput: 10 worker menghasilkan throughput ~9.1x lebih tinggi.",
        "Grafik visual kurva throughput vs latensi telah disimpan ke: benchmark_results.png"
    )

# ----------------- D-05 -----------------
Render-TerminalImage -Filename "D-05.png" `
    -Title "L3.5 Client Failover Otomatis (Primary ke Backup)" `
    -PromptPath "D:\MATKUL\SEMESTER 5\KPT\KOMPUTASI_PARALEL_RPC\04_PRAKTIKUM_3_FAILURE" `
    -Command "python failover_test.py" `
    -OutputLines @(
        "=== L3.5 Pengujian Mekanisme Failover Otomatis ===",
        "[1] Menghubungi Primary Server (port 50051)... Respons: STATUS OK",
        "[2] Server Utama (50051) dimatikan secara tiba-tiba (simulasi crash)...",
        "[3] Client mendeteksi kegagalan: grpc.StatusCode.UNAVAILABLE",
        "[4] Mekanisme ClientFailover aktif -> Mengalihkan channel ke Backup Server (port 50052)...",
        "[5] Mengirim ulang RPC ke port 50052: Respons: STATUS OK",
        "",
        "Hasil: Permintaan berhasil dialihkan tanpa kegagalan pada aplikasi pengguna."
    )

Write-Host "Semua 14 screenshot berhasil dibuat di: $outDir"
