# L3.1 request ID tetap (seed=42)

| Besaran | Nilai |
|---|---:|
| Saldo awal A / B / total | 1000 / 500 / 1500 |
| Jumlah transfer logis x nominal | 20 x 10 |
| Transfer sukses / gagal (sisi client) | 20 / 0 |
| Total percobaan RPC (termasuk retry) | 30 |
| Transfer yang benar-benar dieksekusi server | 20 |
| Duplikat ditolak oleh deduplikasi | 10 |
| Saldo akhir A / B | 800 / 700 |
| Total saldo akhir | 1500 |
| Target (A / B / total) | 800 / 700 / 1500 |
| Status pengujian | LULUS |
| Durasi | 25.2 s |
