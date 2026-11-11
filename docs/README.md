# Dokumentasi VanGuard

Mulai dari **[manual penggunaan](MODUL_PENGGUNAAN_VANGUARD.md)** untuk pemasangan
hingga koneksi endpoint. [Versi HTML](MODUL_PENGGUNAAN_VANGUARD.html) dapat dibaca
atau dicetak. Untuk melanjutkan pekerjaan, baca **[checkpoint](CHECKPOINT.md)**.

Untuk jaringan kampus `192.168.50.0/24`, gunakan **[dokumen kerja lapangan](PERSIAPAN_UJI_LAPANGAN.md)**: kebutuhan, urutan uji, recovery dan formulir hasil dalam satu file.

| Kebutuhan | Folder atau dokumen |
| --- | --- |
| Memasang dan menggunakan sistem | [Manual utama](MODUL_PENGGUNAAN_VANGUARD.md) |
| Mengunduh installer terbaru | [Downloads](../downloads/) |
| Melihat kondisi terakhir | [Checkpoint](CHECKPOINT.md) |
| Mencari perubahan per tanggal | [Jurnal progress](progress/) |
| Membaca audit, validasi dan hasil uji | [Laporan](reports/) |
| Menyiapkan pengujian atau memahami metrik | [Metode pengujian](testing/) |
| Membuka keluaran XML pengujian lama | [Artefak pengujian](testing/results/) |
| Menyiapkan paper konferensi berbasis VM | [Rencana B](proposal/RENCANA_B_KONFERENSI.md) |
| Memeriksa kesesuaian proposal TA | [Proposal](proposal/) |
| Membaca catatan kapasitas, hardening dan CI | [Referensi teknis](reference/) |
| Membuka snapshot checkpoint/handoff lama | [Arsip](history/) |
| Melihat seluruh alur sistem dalam satu diagram | [Flowchart lengkap](FLOWCHART_SISTEM_LENGKAP.md) |

Dokumen inti yang alamatnya dipertahankan:

- [API](API.md)
- [Keamanan](SECURITY.md)
- [Client Windows](WINDOWS_CLIENT.md)

Pengelompokan 4 November 2026 memindahkan file tanpa menghapusnya. Nama file dan
histori Git dipertahankan. Installer terbaru tetap di `downloads/`, versi lama
ada di `downloads/archive/`. Dokumen pada ZIP/EXE yang sudah dirilis tetap edisi
saat paket dibangun. Sumber aplikasi ada di `vanguard/`, pengujian di `tests/`,
installer di `deploy/`, dan alat operasional di `scripts/`.

Cleanup 10 November merangkum checkpoint/handoff aktif dan mempertahankan catatan
lengkapnya di [arsip](history/). Source, tes, unduhan dan bukti tetap tersedia.
Salinan ekstraksi lokal yang identik dengan ZIP serta cache/build sementara
dibersihkan; lihat [jurnal](progress/PROGRESS_2026-11-10.md) untuk rinciannya.
