"""
L2.4 - Perbandingan ukuran pesan Protobuf vs XML-RPC untuk data mahasiswa yang SAMA.

Ruang lingkup pengukuran (konsisten untuk kedua format):
    yang dihitung  = payload pesan (body) yang berisi objek mahasiswa
    tidak dihitung = header HTTP (XML-RPC) maupun header HTTP/2 + prefix 5 byte gRPC
Protobuf : len(mhs.SerializeToString())
XML-RPC  : len(xmlrpc.client.dumps((struct,), methodresponse=True).encode("utf-8"))
           (struct berisi field yang sama dan dikirim sebagai respons)
Menjalankan:  python l24_ukuran.py
"""
import os
import xmlrpc.client

import akademik_pb2 as pb

DIR_HASIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hasil_pengujian")


def ukur(nama, mhs_pb, dict_xml):
    n_pb = len(mhs_pb.SerializeToString())
    xml = xmlrpc.client.dumps((dict_xml,), methodresponse=True).encode("utf-8")
    n_xml = len(xml)
    selisih = n_xml - n_pb
    return nama, n_pb, n_xml, selisih, 100 * selisih / n_xml, n_xml / n_pb, xml


def main():
    kasus = [
        ukur("Andi (nim, nama, ipk)",
             pb.Mahasiswa(nim="2023001", nama="Andi", ipk=3.26),
             {"nim": "2023001", "nama": "Andi", "ipk": 3.26}),
        ukur("Sari (nim, nama, ipk)",
             pb.Mahasiswa(nim="2023002", nama="Sari", ipk=3.68),
             {"nim": "2023002", "nama": "Sari", "ipk": 3.68}),
        ukur("Andi + prodi (4 field)",
             pb.Mahasiswa(nim="2023001", nama="Andi", ipk=3.26, prodi="Informatika"),
             {"nim": "2023001", "nama": "Andi", "ipk": 3.26, "prodi": "Informatika"}),
    ]
    out = ["Ukuran dalam byte (XML dikodekan UTF-8). Selisih = XML - Protobuf.",
           "Persen hemat = selisih / ukuran XML x 100%.  Rasio = XML / Protobuf.\n",
           "| Data | Protobuf (B) | XML-RPC (B) | Selisih (B) | Hemat (%) | Rasio |",
           "|---|---:|---:|---:|---:|---:|"]
    for nama, n_pb, n_xml, sel, persen, rasio, _ in kasus:
        out.append(f"| {nama} | {n_pb} | {n_xml} | {sel} | {persen:.2f} | {rasio:.2f}x |")
    out.append("\nXML-RPC yang diukur (Andi, 3 field):\n" + kasus[0][6].decode("utf-8"))
    out.append("Protobuf (hex, Andi 3 field): " +
               pb.Mahasiswa(nim="2023001", nama="Andi", ipk=3.26).SerializeToString().hex())
    teks = "\n".join(out)
    print(teks)
    os.makedirs(DIR_HASIL, exist_ok=True)
    with open(os.path.join(DIR_HASIL, "L2_4_ukuran.txt"), "w", encoding="utf-8") as f:
        f.write(teks + "\n")


if __name__ == "__main__":
    main()
