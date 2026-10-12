# Hasil implementasi VanGuard — 12 Oktober 2026

**Versi 0.1.5 terpasang pada lima VM Ubuntu 22.04.** Audit proposal menghasilkan
perbaikan dashboard dan [catatan revisi per bagian](SARAN_REVISI_PROPOSAL_2026-10-12.md).
Proposal Google Docs tetap sebagai sumber yang dibaca; usulan redaksi disimpan di Git.

## Perubahan sistem

- Health HTTPS CA/server ditampilkan terpisah; CA diperiksa sebelum issuance.
- Audit administrator menyimpan aktor dari sesi, waktu dan peristiwa. Migrasi
  menambah tabel/kolom tanpa mengganti sertifikat atau merekonstruksi histori lama.
- Pencabutan memiliki alasan bisnis, waktu selesai dan riwayat per identitas;
  retry mempertahankan alasan pertama. Reason CRL tetap cessationOfOperation.
- Masa berlaku/fingerprint sertifikat dan ZIP onboarding publik tersedia.
  Bundle berisi sertifikat, root, manifest dan instruksi; key tetap pada client.
- Runner pilot benchmark dan regresi parser UDP iperf3 3.9 ditambahkan.

[Panduan dashboard](DASHBOARD_0.1.5.md) dan [tutorial lengkap](TUTORIAL_PENGGUNAAN.md)
menjelaskan pemakaian. Enam pemeriksaan admission dan binding akun karyawan tetap
wajib; registrasi/bundle tidak menambah peer. Topologi lima node dan WireGuard
standar dipertahankan. Riwayat aktivitas belum menjadi renewal sertifikat 1:N.

## Bukti 0.1.5

| Pemeriksaan | Hasil |
|---|---|
| Suite lokal | 132 PASS, 183,97 detik; [JUnit](test-results.xml) |
| Suite guest Ubuntu 22.04/Python 3.10 | 132 PASS, 255,11 detik; [JUnit](guest-test-results.xml) |
| Suite target | 47 PASS, 47,95 detik |
| Rollout | COMPLETE, backup konsisten lima role dan startup |
| Integritas | 14 berkas aplikasi setiap VM cocok source; config/CA/key/identitas utama cocok backup saat rollout |
| Dashboard HTTPS live | Login TOTP/CSRF, health, registry-only, bundle/history, admission, revoke beralasan/aktor, cleanup PASS |
| Benchmark pilot | Clear/VanGuard n=1 masing-masing PASS, cleanup PASS; [hasil dan batas](BENCHMARK_PILOT_2026-10-12.md) |
| CI / pemeriksaan sesudah resume | Sedang diselesaikan; lihat checkpoint dan jurnal aktual |

Wheel terpasang SHA-256:
`115b10881595d4208b881c76e3be880bdd76377f983e6528979eab9b6fabf548`.
Arsip source lokal immutable dibuat sebelum runner UI/catatan akhir; Git memuat
berkas terbaru. Bukti privat ada pada `state/deployment/audit-2026-10-12/`;
backup sebelum rollout `state/backups/before-0.1.5-2026-10-12/`.

## Pemulihan operasional dan akses lokal

Sesudah interupsi, VM ditemukan mati. Saat boot, counter CRL CA kosong dan config
tunnel client tertinggal. Backup dibuat sebelum pemulihan counter monoton dari
CRL bertanda tangan/old; index revocation tidak dikembalikan. Bukti gagal dan
pemulihan disimpan dalam direktori audit. Jangan memulihkan index CA/CRL lama.

Sesuai permintaan pengguna, kredensial hanya ada pada komputer ini, di luar repo:
`/home/lui/VanGuard-Privat/KREDENSIAL_VANGUARD.md`. Direktori 0700, file 0600.
Lima akun console VM diberi password unik; SSH tetap memakai key. Password admin/
VPN utama cocok hash aktual. Password akun uji yang tidak tersimpan ditandai
tidak tersedia. Git hanya menyimpan catatan lokasi, tanpa nilai rahasia.

## Batas kesimpulan dan tindak lanjut proposal

S-01 10/10 serta MTTD aplikasi 69,649 ms/MTTR Respond 19,383 ms adalah bukti
**0.1.4**, [hasil 10 Oktober](RESPONSE_METRICS_2026-10-10.md).
S-03 3/3 dan S-04 ICMP 10/10 (batas atas 7,351–12,737 detik) adalah bukti
**0.1.3**, [hasil 9 Oktober](SECURITY_RESULTS_2026-10-09.md).
Seri tersebut tidak diulang penuh pada 0.1.5. MTTD/MTTR tidak mengukur onset
kebocoran, recovery atau respons SOC; batas revoke termasuk SSH/polling.

Pilot n=1 bukan evaluasi statistik tiga konfigurasi × 10. Baseline WG tanpa
admission masih memerlukan pengecualian eksplisit. Windows, renewal/history 1:N,
notifikasi pemilik, auto-import bundle, kebijakan resource/departemen dan
pemutusan sesi TCP/aplikasi belum lengkap. Ketidaksesuaian arsitektur handshake,
skenario S-01/S-02, definisi metrik dan penomoran referensi proposal dijelaskan pada
[catatan revisi](SARAN_REVISI_PROPOSAL_2026-10-12.md).

Seluruh TA belum dinyatakan selesai. TOTP HP pribadi, login console interaktif,
reboot workstation dan penyebab shutdown belum terverifikasi. Gunicorn melaporkan
control socket tidak dapat ditulis pada sandbox service; API tetap berjalan.
[Checkpoint](CHECKPOINT.md), [jurnal](PROGRESS_2026-10-12.md), dan
[arsip laporan 0.1.4](IMPLEMENTATION_REPORT_2026-10-10.md) menyimpan konteks lanjutan.
