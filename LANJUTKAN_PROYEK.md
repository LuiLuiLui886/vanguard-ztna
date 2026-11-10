# Lanjutkan proyek VanGuard

## Mulai dari sini

Baca `AGENTS.md`, `VANGUARD_CONTEXT.md`, lalu
[checkpoint terbaru](docs/CHECKPOINT.md). Branch kerja:
`feature/2026-10-22-physical-endpoints`. Periksa perubahan pengguna dan commit
terbaru sebelum mengedit. Semua perubahan memerlukan intent dan hasil di
[jurnal](docs/progress/PROGRESS_2026-11-11.md).

[Manual utama](docs/MODUL_PENGGUNAAN_VANGUARD.md) edisi 10 November dimulai dari
arti host/VM, prompt terminal, `cd /home/lui/vanguard`, boot dan SSH. Revisi
11 November memakai `scripts/export_endpoint_public.py` tanpa input username. Gunakan
profil existing schema2 pada Bagian 1.1.
Detail lokasi file dan terminal ada pada Bagian0.2.1–0.2.3 serta1.1.1–1.1.2;
contoh ekspor existing diuji tanpa membuat ulang identitas. Jangan mengulang instalasi CA atau
mengganti profil ke schema1 hanya untuk mengikuti tutorial dari awal.

## Kondisi terakhir dan prioritas

- CA 0.1.17, server/admin dan installer Windows 0.1.15. Keputusan mempertahankan
  server/admin berdasarkan perbandingan kode, bukan sekadar nomor versi.
- Pengguna11November mengizinkan penghapusan Windows11/10: domain dan dua disk
  sudah dihapus,135file identitas/config dan XML disimpan privat; NVRAM/TPM tetap.
  Lima Ubuntu terpelihara; CA/server/admin running. Jangan buat ulang Windows otomatis.
- Host kini Wi-Fi .66.9; sambungkan kembali Ethernet .50.10. DHCP reservation, forwarding/filter host dan
  koneksi endpoint fisik belum dibuktikan. Ikuti
  [dokumen lapangan](docs/PERSIAPAN_UJI_LAPANGAN.md).
- Baseline 355 PASS/1 SKIP dan postflight 30/30 sudah selesai. Jangan mengulang
  suite/rollout lama tanpa perubahan atau masalah konkret yang memerlukannya.
  Readiness CA masih pernah timeout; retry ready tidak membuktikan penyebab selesai.
- Disk kini sekitar77GiB bebas. Windows OS perlu instalasi ulang jika dibutuhkan;
  backup kecil bukan image OS. Hasil uji historis dan installer tetap tersedia.
- Helper ekspor publik lulus uji aktual schema2; output terbaru
  `state/endpoint-public-u8wsu2hh/`.14teshelper/preflight PASS, bukan uji fisik.
- DNS router .50.1 pernah timeout dan menghambat push; periksa DNS/HTTPS jika
  push gagal, jangan langsung mengubah autentikasi GitHub.

## Cleanup yang sudah dikerjakan

Cleanup tercatat pada `ec45628`, sudah dipush dan SHA remote terverifikasi.

Empat salinan ekstraksi paket lama di dist dihapus setelah dicocokkan seluruh
anggotanya dengan ZIP yang tetap tersedia. Cache dan build sementara dibersihkan.
Manifest/hash ada di `state/cleanup-20261110/`. Jangan menjalankan cleanup.py
ulang: hasil lengkap ada pada result.json. File unik, state, backup, credential,
installer dan seluruh definisi VM dipertahankan.

Catatan lama tetap tersedia di
[arsip handoff](docs/history/checkpoints/LANJUTKAN_PROYEK_2026-11-10_before_cleanup.md)
dan [arsip checkpoint](docs/history/checkpoints/CHECKPOINT_2026-11-10_before_cleanup.md).
Status lama pada arsip bukan instruksi untuk mengulang milestone yang selesai.
