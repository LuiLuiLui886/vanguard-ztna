# Akses karyawan — VanGuard 0.1.3

Sesuai keputusan pengguna untuk proposal S-01, karyawan memakai akun VPN lokal
yang terpisah dari akun administrator dashboard. Password yang benar hanya
menghasilkan sesi karyawan. Untuk akses tunnel, sesi harus terikat pada perangkat
yang lolos enam pemeriksaan sertifikat/CRL/proof/binding.

## Administrator

1. Login dashboard dengan password dan TOTP admin.
2. Pada **Akun karyawan**, buat username dan password awal minimal 12 karakter.
   Sampaikan password secara privat. Tidak ada akun/password bawaan aplikasi.
3. Daftarkan `request.json` dari client, isi nama perangkat, departemen, pemilik,
   platform, dan pilih akun karyawan. Identitas belum menjadi peer live.
4. Unduh sertifikat dan pasang sebagai `device.crt` pada direktori identitas client.
5. Perangkat lama yang belum memiliki akun dapat memakai **Tautkan akun VPN**.
   Binding akun bersifat immutable: pergantian pemilik akses memerlukan pencabutan
   dan identitas baru. Metadata deskriptif dapat diedit tanpa mengubah binding.

Menonaktifkan akun membatalkan seluruh sesinya dan menghapus peer perangkat yang
terikat. Sertifikat belum otomatis dicabut oleh tindakan ini; gunakan pencabutan
perangkat untuk mengakhiri identitas kriptografisnya. Akun yang dinonaktifkan tidak
memiliki tombol aktivasi ulang pada versi ini.

## Karyawan pada VM-CLIENT

```bash
sudo /opt/vanguard/venv/bin/vanguard-client login --username employee-lab
sudo systemctl restart vanguard-client
ping -c 3 10.8.0.1
```

Nama `employee-lab` hanya akun yang disiapkan eksplisit untuk migrasi lab ini;
gunakan akun yang diberikan administrator pada pemasangan lain. CLI meminta
password tanpa menampilkannya atau menaruhnya dalam argumen proses.

Sesi disimpan dalam `/var/lib/vanguard/client/employee-session.json` dengan mode
0600. Password tidak disimpan pada client. Sesi berlaku delapan jam; renewal
admission tidak memperpanjang sesi login. Setelah expired, login lagi dan restart
client. Selama belum login kembali, daemon server menghapus peer dan client gagal
mendapat akses. Boot workstation tidak otomatis memperbarui login karyawan.

Penggantian sesi saat client aktif berlaku pada renewal admission berikutnya.
Reset password mandiri, notifikasi pemilik, integrasi Windows, dan SSO belum ada.
Secret akun lab pada saat bootstrap disimpan privat di direktori state rollout
sebagai `employee-onboarding.json`; jangan memasukkannya ke Git/lampiran TA.

## Pembuktian S-01

```bash
.venv/bin/python scripts/verify_employee.py state/lab/inventory.json \
  --state state/deployment/s01-run-baru
```

Skrip membuat akun dan identitas sementara pada VM yang sama. VM attacker mendapat
password uji valid dan salinan sertifikat/public key, tanpa private key identitas.
Login harus berhasil, tetapi admission tanpa sertifikat, binding salah, proof dari
private key lain, dan replay harus ditolak tanpa menambah peer. Client sah kemudian
menunjukkan admission positif, diikuti penonaktifan akun dan penolakan sesi lama.
Cleanup mencabut identitas sementara dan menonaktifkan akun. Client utama tetap utuh.

Hasil menyimpan status per tahap. RUNNING/INTERRUPTED bukan keberhasilan; gunakan
device_id/username pada JSON untuk memeriksa cleanup sebelum mengulang. Uji ini
mengukur admission/peer kernel, bukan throughput atau penghentian trafik S-04.
