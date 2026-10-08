# Aktivasi administrator VanGuard

Panduan untuk lab pada laptop ini, diperbarui 8 Oktober 2026.

1. Buka file lokal
   `/home/lui/vanguard/state/deployment/aktivasi-admin.html` di Firefox.
   Halaman privat ini berisi QR TOTP, username, dan password yang bisa ditampilkan.
2. Di aplikasi authenticator HP, pilih tambah akun lalu pindai QR tersebut.
   Jika memasukkan manual, pilih TOTP berbasis waktu, SHA-1, enam digit, 30 detik.
3. Buka <https://192.168.100.40:5000> di Firefox laptop ini.
4. Login dengan username, password, dan kode enam digit terbaru dari HP.
   Kode yang sudah dipakai ditolak; tunggu kode berikutnya untuk login ulang.

Aktifkan waktu otomatis pada HP. Jika lima percobaan login gagal, tunggu lima menit
sebelum mencoba kembali. Jangan bagikan QR, kunci TOTP, atau password di laporan TA.

Root CA lab sudah diimpor ke profil Firefox `nik2r4ma.default` dan fingerprint
sertifikat hasil impor sudah dicocokkan dengan VM-CA. Untuk browser lain, impor
`state/deployment/root.crt` melalui pengaturan Authorities untuk identifikasi website.
Jika Firefox sudah berjalan sebelum impor, tutup dan buka kembali bila masih muncul
peringatan trust. Jangan melewati peringatan untuk sertifikat yang tidak cocok.

Halaman aktivasi bekerja secara offline, tanpa CDN, font, atau generator QR eksternal.
File mode 0600 berada di direktori state privat. Kredensial asli tetap berada di
`state/deployment/admin-onboarding.json`; tidak ada penggantian akun atau secret.
Pemasangan TOTP di HP dan login oleh pengguna masih merupakan langkah operator.

## Membuka lab setelah laptop dinyalakan

Jalankan dari folder proyek:

```bash
bash scripts/open_dashboard.sh
```

Skrip menyalakan kelima VM yang sudah ada jika masih mati, menunggu HTTPS dashboard,
lalu membuka browser. VM tidak dibuat ulang. Untuk pengelolaan manual, buka
Virtual Machine Manager dengan koneksi `qemu:///system`.

## Alur demo singkat

1. Login dashboard dan lihat `vm-client` beserta status peer.
2. Jalankan `ping -c 3 10.8.0.1` di VM-CLIENT untuk menunjukkan akses tunnel.
3. Jalankan skrip attacker untuk menunjukkan permintaan tanpa identitas ditolak:
   `/opt/vanguard/venv/bin/python /opt/vanguard/attacker_checks.py` di VM-ATTACKER.
4. Gunakan bukti uji di laporan untuk menjelaskan registrasi, admission, lease,
   CRL, dan pencabutan. Tombol **Cabut akses & sertifikat** bersifat permanen untuk
   identitas tersebut; gunakan identitas uji jika melakukan demo pencabutan langsung.
