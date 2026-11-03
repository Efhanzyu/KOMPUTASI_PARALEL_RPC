# L3.2 UUID baru tiap percobaan (seed=42)

| Besaran | Nilai |
|---|---:|
| Saldo awal A / B / total | 1000 / 500 / 1500 |
| Jumlah transfer logis x nominal | 20 x 10 |
| Transfer sukses / gagal (sisi client) | 19 / 1 |
| Total percobaan RPC (termasuk retry) | 32 |
| Transfer yang benar-benar dieksekusi server | 32 |
| Duplikat ditolak oleh deduplikasi | 0 |
| Saldo akhir A / B | 680 / 820 |
| Total saldo akhir | 1500 |
| Target (A / B / total) | 800 / 700 / 1500 |
| Status pengujian | TIDAK SESUAI TARGET |
| Durasi | 34.1 s |

Selisih A terhadap target 800: -120
Eksekusi berlebih di server (eksekusi - 20 transfer logis): 12
Saldo total tetap 1500: uang tidak hilang/bertambah, tetapi A terdebit 32 x 10 = 320 (seharusnya 200). Total saja TIDAK cukup untuk mendeteksi transfer ganda.

## Perbandingan L3.1 vs L3.2

| Besaran | L3.1 ID tetap | L3.2 UUID baru |
|---|---:|---:|
| Percobaan RPC total | 30 | 32 |
| Eksekusi di server | 20 | 32 |
| Duplikat ditolak | 10 | 0 |
| Transfer gagal total (client) | 0 | 1 |
| Saldo akhir A | 800 | 680 |
| Saldo akhir B | 700 | 820 |
| Total saldo | 1500 | 1500 |
