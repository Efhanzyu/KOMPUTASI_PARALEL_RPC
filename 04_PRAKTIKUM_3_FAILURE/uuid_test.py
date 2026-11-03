"""
L3.2 - Mengulang L3.1 dengan UUID BARU di setiap percobaan (retry yang tidak aman).

Skrip menjalankan dua kondisi dengan seed acak yang sama lalu membandingkannya:
    (1) request ID tetap  -> hasil L3.1
    (2) UUID baru tiap percobaan -> hasil L3.2
Hasil aktual dicatat apa adanya; tidak ada angka yang dipaksakan.

Menjalankan:  python uuid_test.py [--seed 42] [--tanpa-baseline]
"""
import argparse
import os

from transfer_test import DIR_HASIL, jalankan, tabel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--tanpa-baseline", action="store_true")
    a = ap.parse_args()

    hasil = {}
    if not a.tanpa_baseline:
        print(f"=== (1) Baseline L3.1: request ID TETAP (seed={a.seed}) ===")
        hasil["tetap"] = jalankan(False, a.seed)
    print(f"\n=== (2) L3.2: UUID BARU di tiap percobaan (seed={a.seed}) ===")
    hasil["baru"] = jalankan(True, a.seed)

    teks_baru, _ = tabel(hasil["baru"], 800.0, 700.0)
    h = hasil["baru"]
    berlebih = h["eksekusi_server"] - h["n"]          # eksekusi di server - transfer logis
    out = [f"# L3.2 UUID baru tiap percobaan (seed={a.seed})", "", teks_baru, ""]
    out.append(f"Selisih A terhadap target 800: {h['saldo_akhir']['A'] - 800:+.0f}")
    out.append(f"Eksekusi berlebih di server (eksekusi - {h['n']} transfer logis): {berlebih}")
    out.append(f"Saldo total tetap {h['total_akhir']:.0f}: uang tidak hilang/bertambah, tetapi A terdebit "
               f"{h['eksekusi_server']} x {h['jumlah']:.0f} = {h['eksekusi_server'] * h['jumlah']:.0f} "
               f"(seharusnya {h['n'] * h['jumlah']:.0f}). Total saja TIDAK cukup untuk mendeteksi transfer ganda.")
    if "tetap" in hasil:
        t = hasil["tetap"]
        out += ["", "## Perbandingan L3.1 vs L3.2", "",
                "| Besaran | L3.1 ID tetap | L3.2 UUID baru |", "|---|---:|---:|",
                f"| Percobaan RPC total | {t['percobaan_rpc']} | {h['percobaan_rpc']} |",
                f"| Eksekusi di server | {t['eksekusi_server']} | {h['eksekusi_server']} |",
                f"| Duplikat ditolak | {t['duplikat_ditolak']} | {h['duplikat_ditolak']} |",
                f"| Transfer gagal total (client) | {t['transfer_gagal_client']} | {h['transfer_gagal_client']} |",
                f"| Saldo akhir A | {t['saldo_akhir']['A']:.0f} | {h['saldo_akhir']['A']:.0f} |",
                f"| Saldo akhir B | {t['saldo_akhir']['B']:.0f} | {h['saldo_akhir']['B']:.0f} |",
                f"| Total saldo | {t['total_akhir']:.0f} | {h['total_akhir']:.0f} |"]
    teks = "\n".join(out)
    print("\n" + teks)
    os.makedirs(DIR_HASIL, exist_ok=True)
    with open(os.path.join(DIR_HASIL, f"L3_2_hasil_seed{a.seed}.md"), "w", encoding="utf-8") as f:
        f.write(teks + "\n")


if __name__ == "__main__":
    main()
