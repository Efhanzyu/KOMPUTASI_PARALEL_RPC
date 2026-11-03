"""
Client LAMA (stub dari schema v1, tanpa field prodi) untuk L2.3.
Jalankan dari DALAM folder client_lama/ agar 'import akademik_pb2' memakai stub lama:
    cd client_lama
    python client_lama.py [alamat]
"""
import sys

import grpc

import akademik_pb2 as pb          # stub LAMA (folder ini)
import akademik_pb2_grpc as pb_grpc

alamat = sys.argv[1] if len(sys.argv) > 1 else "localhost:50051"
print("Field Mahasiswa menurut stub lama:", [f.name for f in pb.Mahasiswa.DESCRIPTOR.fields])
with grpc.insecure_channel(alamat) as channel:
    stub = pb_grpc.LayananNilaiStub(channel)
    try:
        mhs = stub.GetMahasiswa(pb.MahasiswaRequest(nim="2023001"))
    except grpc.RpcError as e:
        print("GAGAL:", e.code(), e.details())
        sys.exit(1)
    print(f"BERHASIL: nim={mhs.nim} nama={mhs.nama} ipk={mhs.ipk}")
    print("hasField prodi?", hasattr(mhs, "prodi"))
    # Bukti unknown fields tetap dipertahankan: serialisasi ulang lalu tampilkan hex
    print("bytes_ulang_hex:", mhs.SerializeToString().hex())
