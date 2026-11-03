"""L2.4 - Ukuran Protobuf vs XML-RPC (data sama, lingkup sama: hanya payload pesan)."""
import unittest
import xmlrpc.client

from _util import pb


class TestL24(unittest.TestCase):
    def test_ukuran_aktual(self):
        mhs = pb.Mahasiswa(nim="2023001", nama="Andi", ipk=3.26)
        n_pb = len(mhs.SerializeToString())
        xml = xmlrpc.client.dumps(({"nim": "2023001", "nama": "Andi", "ipk": 3.26},),
                                  methodresponse=True).encode("utf-8")
        self.assertEqual(n_pb, 24)    # 9 (nim) + 6 (nama) + 9 (ipk double)
        self.assertEqual(len(xml), 350)
        self.assertLess(n_pb, len(xml) / 10)   # protobuf < 10% dari XML

    def test_round_trip_isi_sama(self):
        mhs = pb.Mahasiswa(nim="2023001", nama="Andi", ipk=3.26, prodi="Informatika")
        self.assertEqual(pb.Mahasiswa.FromString(mhs.SerializeToString()), mhs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
