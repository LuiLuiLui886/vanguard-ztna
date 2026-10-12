# Aktivitas dan arsip administrator VanGuard 0.1.6

Versi 0.1.6 memperluas audit dashboard 0.1.5. Buka menu **Aktivitas admin**
untuk pencarian, dan **Arsip** untuk melihat serta mengunduh salinan yang sudah
disimpan. Panduan pemakaian ada di [tutorial](TUTORIAL_PENGGUNAAN.md#cari-dan-arsipkan-aktivitas-admin).

## Informasi yang dicatat

Setiap peristiwa mempunyai timestamp presisi subdetik Unix UTC pada SQLite.
Dashboard dan ekspor menampilkan **tanggal, jam, menit, detik dalam WIB
(Asia/Jakarta, UTC+7)**. Tidak melakukan pembulatan timestamp sumber sebelum
ekspor; kolom UTC disertakan untuk audit dan korelasi.

Daftar tindakan mencakup login/logout admin, registrasi perangkat, penerbitan
sertifikat, binding akun, perubahan metadata, retry, permintaan/penyelesaian
pencabutan, pembuatan/nonaktif akun karyawan, unduhan sertifikat/bundle, pembukaan
riwayat perangkat, kegagalan tindakan, penolakan CSRF, dan pembuatan/unduhan arsip.
Aktivitas keamanan otomatis dari server ditampilkan di bagian terpisah.

Tampilan menerjemahkan kode peristiwa dan detail terpilih ke bahasa Indonesia.
Untuk perubahan metadata, bagian yang berubah disebutkan; nilai sebelumnya/sesudahnya
tidak disalin karena bisa memuat data pribadi. Nama aktor dibaca dari sesi admin
terautentikasi, bukan field aktor kiriman form. Kegagalan proses juga dicatat dengan
tindakan dan kode respons; log tidak menyimpan body form, password, seed TOTP,
session token, atau private key.

## Cari dan telusuri

Filter tanggal mulai/akhir menggunakan hari WIB (kedua tanggal inklusif), username
admin/pelaku dan ID perangkat dicocokkan utuh, serta jenis tindakan dipilih dari
daftar. Filter memakai parameter database, bukan potongan SQL. Hasil diurutkan
berdasarkan ID catatan dan ditampilkan **50 per halaman**. Tautan riwayat perangkat
membuka pencarian seluruh tindakan untuk satu ID.

Satu alur dapat membuat beberapa catatan. Sebagai contoh, permintaan pencabutan
serta pencabutan selesai memiliki waktu/hasil sendiri, dan aktor saat retry bisa
berbeda dari pemohon. Peristiwa lama yang sudah tersimpan sejak 0.1.5 tetap terlihat;
event code yang belum dikenal tetap muncul sebagai “Aktivitas lain” tanpa menampilkan
detail mentah yang tidak dipahami UI. Tidak menciptakan ulang catatan sebelum audit
administrator pertama diaktifkan pada 0.1.5.

## Arsip snapshot

1. Atur filter dan klik **Simpan arsip aktivitas**.
2. Aplikasi mengambil seluruh catatan yang cocok saat snapshot dibuat, termasuk
   halaman berikutnya. Batas arsip adalah **10.000 catatan** dan 8 MiB data sebelum
   ZIP; bila melewati batas, tidak dibuat arsip parsial.
3. Aplikasi menyimpan snapshot sebagai BLOB dalam database admin. Log sumber tetap
   ada. Pembuatan arsip dicatat secara atomik bersama snapshot dan tercatat setelah
   isi snapshot, sehingga event pembuatannya sendiri tidak termasuk di dalam ZIP.
4. Buka **Arsip**, periksa pembuat, waktu WIB, filter, jumlah dan rentang ID, lalu
   unduh ZIP. SHA-256 ZIP ditampilkan dan juga dikirim pada header respons. Server
   menghitung ulang hash sebelum download; mismatch membatalkan unduhan dan dicatat.
5. ZIP memuat `aktivitas.csv`, `aktivitas.json`, `manifest.json`, dan `PETUNJUK.txt`.
   CSV memakai UTF-8 BOM untuk aplikasi spreadsheet, menetralkan nilai formula,
   serta berisi kolom WIB dan timestamp UTC. Manifest menyimpan hash CSV/JSON.

Arsip tidak mempunyai fungsi edit/hapus pada dashboard. Backup database admin juga
mencadangkan snapshot. Kegagalan VM tanpa backup dapat menghilangkan log dan arsip;
arsip disimpan pada disk VM ADMIN yang sama, bukan salinan off-site.

## Integritas dan batas audit

Checksum mendeteksi perubahan tidak sengaja pada ZIP/database record. Ini bukan
tanda tangan digital: administrator root pada VM dapat mengubah database serta
checksum. Administrator dashboard terautentikasi dapat membuat aktivitas baru,
tetapi tidak menghapus arsip melalui UI. Terapkan backup berkala dan simpan hasil
ekspor di lokasi privat jika dibutuhkan sebagai bukti jangka panjang.

UI dashboard mewajibkan login password/TOTP dan token CSRF. Endpoint memakai sesi
yang sama dengan dashboard; tidak ada API publik untuk mengekspor log. Pembukaan
dashboard, pencarian/filter, daftar arsip, riwayat perangkat dan unduhan dicatat
dengan waktu tersendiri, termasuk saat halaman di-refresh.

Log admin juga mencatat pembukaan dashboard, pencarian/filternya, dan pembukaan
daftar arsip agar penelusuran audit turut terlihat. Refresh menghasilkan peristiwa
baru dengan waktu masing-masing. Filter tersimpan sebagai kriteria pencarian.
Log admin mencatat tindakan dashboard. Peristiwa admission/peer otomatis berasal
dari tabel audit server yang berbeda; bagian dashboard server menyajikan ringkasan
Indonesia. Keduanya tidak satu transaksi lintas VM. Detail event server yang tidak
dikenal menggunakan keterangan umum. Simpan backup konsisten `admin.db` sebelum
upgrade schema.
