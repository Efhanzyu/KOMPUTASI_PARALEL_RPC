# Script Validasi & Pengujian Otomatis Praktikum RPC di Windows
# Penggunaan:
#   .\venv\Scripts\Activate.ps1
#   .\jalankan_semua_tes.ps1

$root = $PSScriptRoot
$python = if (Test-Path "$root\venv\Scripts\python.exe") { "$root\venv\Scripts\python.exe" } else { "python" }

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   PENGUJIAN SELURUH PRAKTIKUM RPC (WINDOWS 11 / POWERSHELL)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Interpreter: $python"
& $python --version
Write-Host ""

# Praktikum 1
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host "[1/3] Menjalankan Unit Test Praktikum 1 (XML-RPC)..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Push-Location "$root\02_PRAKTIKUM_1_XML_RPC"
& $python -c "import subprocess, sys; res = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'pengujian', '-p', 'test_l1*.py', '-v'], capture_output=True, text=True); sys.stdout.write(res.stdout); sys.stderr.write(res.stderr); open('hasil_pengujian/unittest_praktikum1_windows.txt', 'w', encoding='utf-8').write(res.stdout + '\n' + res.stderr); sys.exit(res.returncode)"
$k1 = $LASTEXITCODE
Pop-Location

# Praktikum 2
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host "[2/3] Menjalankan Unit Test Praktikum 2 (gRPC & Protobuf)..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Push-Location "$root\03_PRAKTIKUM_2_GRPC"
& $python -c "import subprocess, sys; res = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'pengujian', '-p', 'test_l2*.py', '-v'], capture_output=True, text=True); sys.stdout.write(res.stdout); sys.stderr.write(res.stderr); open('hasil_pengujian/unittest_praktikum2_windows.txt', 'w', encoding='utf-8').write(res.stdout + '\n' + res.stderr); sys.exit(res.returncode)"
$k2 = $LASTEXITCODE
Pop-Location

# Praktikum 3
Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Write-Host "[3/3] Menjalankan Unit Test Praktikum 3 (Failure & Concurrency)..." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
Push-Location "$root\04_PRAKTIKUM_3_FAILURE"
& $python -c "import subprocess, sys; res = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'pengujian', '-p', 'test_l3*.py', '-v'], capture_output=True, text=True); sys.stdout.write(res.stdout); sys.stderr.write(res.stderr); open('hasil_pengujian/unittest_praktikum3_windows.txt', 'w', encoding='utf-8').write(res.stdout + '\n' + res.stderr); sys.exit(res.returncode)"
$k3 = $LASTEXITCODE
Pop-Location

# Ringkasan
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "                    RINGKASAN HASIL TEST                    " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
$p1_status = if ($k1 -eq 0) { "LULUS (23/23)" } else { "GAGAL" }
$p2_status = if ($k2 -eq 0) { "LULUS (20/20)" } else { "GAGAL" }
$p3_status = if ($k3 -eq 0) { "LULUS (14/14)" } else { "GAGAL" }

Write-Host "Praktikum 1 (XML-RPC)              : $p1_status [Exit Code: $k1]" -ForegroundColor $(if ($k1 -eq 0) { "Green" } else { "Red" })
Write-Host "Praktikum 2 (gRPC & Protobuf)      : $p2_status [Exit Code: $k2]" -ForegroundColor $(if ($k2 -eq 0) { "Green" } else { "Red" })
Write-Host "Praktikum 3 (Failure & Concurrency): $p3_status [Exit Code: $k3]" -ForegroundColor $(if ($k3 -eq 0) { "Green" } else { "Red" })
Write-Host "------------------------------------------------------------"

if ($k1 -eq 0 -and $k2 -eq 0 -and $k3 -eq 0) {
    Write-Host "STATUS KESELURUHAN: SEMUA UNIT TEST LULUS (57/57)!" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "STATUS KESELURUHAN: TERDAPAT PENGUJIAN YANG GAGAL!" -ForegroundColor Red
    exit 1
}
