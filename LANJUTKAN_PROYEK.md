# Lanjutkan proyek VanGuard

## Mulai dari sini

Baca `AGENTS.md`, `VANGUARD_CONTEXT.md`, lalu
[checkpoint terbaru](docs/CHECKPOINT.md). Branch kerja:
`feature/2026-10-22-physical-endpoints`. Periksa perubahan pengguna dan commit
terbaru sebelum mengedit. Semua perubahan memerlukan intent dan hasil di
[jurnal](docs/progress/PROGRESS_2026-11-10.md).

[Manual utama](docs/MODUL_PENGGUNAAN_VANGUARD.md) edisi 10 November dimulai dari
arti host/VM, prompt terminal, `cd /home/lui/vanguard`, boot dan SSH. Gunakan
profil existing schema2 pada Bagian 1.1. Jangan mengulang instalasi CA atau
mengganti profil ke schema1 hanya untuk mengikuti tutorial dari awal.

## Kondisi terakhir dan prioritas

- CA 0.1.17, server/admin dan installer Windows 0.1.15. Keputusan mempertahankan
  server/admin berdasarkan perbandingan kode, bukan sekadar nomor versi.
- Ketujuh VM sudah dinyalakan dan lima Ubuntu lolos SSH pada 10 November.
  Periksa keadaan aktual jika melanjutkan setelah reboot.
- Host Ethernet .50.10 aktif; DHCP reservation, forwarding/filter host dan
  koneksi endpoint fisik belum dibuktikan. Ikuti
  [dokumen lapangan](docs/PERSIAPAN_UJI_LAPANGAN.md).
- Baseline 355 PASS/1 SKIP dan postflight 30/30 sudah selesai. Jangan mengulang
  suite/rollout lama tanpa perubahan atau masalah konkret yang memerlukannya.
  Readiness CA masih pernah timeout; retry ready tidak membuktikan penyebab selesai.
- Sertifikat Windows existing berakhir 14 November 13:16:28 WIB; periksa sebelum
  uji berikutnya. Disk host tinggal sekitar 480 MiB pada pemeriksaan cleanup;
  siapkan kapasitas sebelum backup/operasi yang banyak menulis.
- DNS router .50.1 pernah timeout dan menghambat push; periksa DNS/HTTPS jika
  push gagal, jangan langsung mengubah autentikasi GitHub.

## Cleanup yang sudah dikerjakan

Empat salinan ekstraksi paket lama di dist dihapus setelah dicocokkan seluruh
anggotanya dengan ZIP yang tetap tersedia. Cache dan build sementara dibersihkan.
Manifest/hash ada di `state/cleanup-20261110/`. Jangan menjalankan cleanup.py
ulang: hasil lengkap ada pada result.json. File unik, state, backup, credential,
installer dan seluruh definisi VM dipertahankan.

Catatan lama tetap tersedia di
[arsip handoff](docs/history/checkpoints/LANJUTKAN_PROYEK_2026-11-10_before_cleanup.md)
dan [arsip checkpoint](docs/history/checkpoints/CHECKPOINT_2026-11-10_before_cleanup.md).
Status lama pada arsip bukan instruksi untuk mengulang milestone yang selesai.
