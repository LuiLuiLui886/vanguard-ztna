# Checkpoint VanGuard — 9 Oktober 2026

> **Pekerjaan aktif sejak 14:03 WIB:** instrumentasi 0.1.4 untuk MTTD dan
> MTTR **Respond** pada S-01. Proposal dibaca ulang; interpretasi recovery pada
> catatan sebelumnya dikoreksi. Source baru sedang divalidasi, belum rollout.
> Baca [definisi metrik](RESPONSE_METRICS.md) dan jurnal terbaru. Rencana benchmark
> tersedia di [BENCHMARK_PLAN.md](BENCHMARK_PLAN.md); baseline WG belum dijalankan.

> **Pembaruan 13:52 WIB — eksperimen selesai:** S-03 3/3 PASS dan S-04 ICMP
> 10/10 PASS. Batas atas konfirmasi 7,351–12,737 detik; bukan MTTD/MTTR.
> Suite lokal/guest/dua job CI masing-masing 90 PASS. Cleanup dan health akhir
> COMPLETE; tidak ada eksperimen aktif. [Hasil lengkap](SECURITY_RESULTS_2026-10-09.md).

**Tahap 0.1.3 selesai:** akun karyawan dan metadata dashboard terpasang pada lima
VM; S-01 live lulus. Source `0c56374` telah dipush ke
[repository private](https://github.com/LuiLuiLui886/vanguard-ztna).
Catatan akhir disimpan melalui commit dokumentasi setelahnya; cek `git log -1`
dan kesamaan HEAD dengan `origin/main` sebelum memulai perubahan berikutnya.

## Keadaan terverifikasi

| Bagian | Hasil |
|---|---|
| Lima VM Ubuntu 22.04 | CA `.10`, SERVER `.20`, CLIENT `.30`, ADMIN `.40`, ATTACKER `.50` aktif |
| Paket | 0.1.3 semua VM; 12 berkas aplikasi per VM cocok source |
| Identitas/config | Hash sesuai backup; CA/key, key/cert utama dan konfigurasi dipertahankan |
| Akun VPN | `employee-lab` terikat ke `vm-client`; sesi delapan jam, enam pemeriksaan perangkat tetap wajib |
| Tes | 90 lokal + 90 guest; CI Python 3.10/3.12 masing-masing 90 PASS |
| S-01 | Login akun valid dari attacker berhasil; perangkat tanpa proof sah ditolak tanpa peer |
| Disable akun | Peer sementara dihapus, sesi lama ditolak |
| Identity/S-02 | Binding/proof/replay/CA revocation/readmission/cleanup PASS |
| Firewall | 40 TCP allow/deny PASS, attacker API/bypass LAN PASS |
| S-03/S-04 | Capture 3/3 dan revoke ICMP 10/10 PASS; seluruh resource uji dibersihkan |
| Health akhir | 7/7 PASS selama 85,90 detik, tiga deadline lease, nol removal |
| Tunnel utama | Peer `10.8.0.2/32`, handshake dan ping lulus |
| Metadata dashboard | Nama/departemen/pemilik/platform; edit tidak mengubah identitas; data lama kompatibel |

CI terbaru: [run 37895229707](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/37895229707)
pada commit instrumentasi `f29ff67` yang telah dipush. Aplikasi tetap 0.1.3.
Ruff, pip check, shell, build/checksum dan checksum artefak unduhan PASS.
Detail: [laporan implementasi](IMPLEMENTATION_REPORT.md),
[jurnal 9 Oktober](PROGRESS_2026-10-09.md), [panduan akun](EMPLOYEE_ACCESS.md).

## Melanjutkan sesi berikutnya

1. Baca `AGENTS.md`, `VANGUARD_CONTEXT.md`, checkpoint ini dan jurnal terbaru.
2. Periksa lima domain yang ada. Jika mati, `bash scripts/open_dashboard.sh`
   dapat menyalakannya. Jangan membuat ulang lab/CA/identitas utama.
3. Jalankan preflight dan health dengan direktori hasil baru:

```bash
.venv/bin/python scripts/ssh_preflight.py state/lab/inventory.json
.venv/bin/python scripts/health_lab.py state/lab/inventory.json \
  --state state/deployment/health-run-baru
```

4. Sesi akun tidak diperpanjang oleh renewal admission. Jika expired, login ulang
   pada VM-CLIENT lalu restart `vanguard-client` sesuai panduan akun. Bootstrap
   kredensial tersimpan privat pada direktori sesi; jangan cetak/commit isinya.
5. S-03/S-04 untuk ICMP selesai. Berikutnya tetapkan definisi/instrumentasi
   MTTD/MTTR (deteksi dan recovery terpisah), serta protokol benchmark tiga
   konfigurasi × 10. Cakupan penutupan sesi TCP/aplikasi belum diuji.
6. Baseline WireGuard tanpa admission bertentangan dengan aturan peer saat ini:
   siapkan rencana isolasi/backup/pemulihan untuk keputusan eksplisit, jangan
   jalankan bypass. Gap lain ada di [matriks proposal](PROPOSAL_ALIGNMENT.md).
7. Catat rencana sebelum kelompok perubahan dan hasil setelahnya, validasi,
   commit/push ke private repo; perbarui checkpoint sebelum berhenti.

Tidak ada rollout atau pengujian live yang masih berjalan pada akhir tahap ini.
Jangan ulang `rollout.py`, enrollment utama atau pencabutan identitas utama.
Jalankan `verify_employee.py` dan `verify_identity.py` berurutan karena keduanya
memakai peer sementara `10.8.0.3`. Skrip tersebut tidak membuat tunnel kedua.

## Bukti dan pemulihan

- Bukti aktif: `state/deployment/proposal-2026-10-09/`: `rollout.json`,
  `installed-manifest.json`, `s01/`, `identity/`, `firewall/`, `after-upgrade/`,
  `ci-artifacts/`, `local-final.xml`, `guest-final.xml`.
- Bukti terbaru: `state/deployment/security-2026-10-09/`: capture, seri 10,
  tiga direktori pilot, cleanup audit, health/firewall, JUnit dan artefak CI.
  Pilot pertama FAIL sebelum perubahan karena VM mati; pilot kedua FAIL membaca
  output probe sesudah revoke dan cleanup PASS; pilot ketiga PASS. Jangan hapus
  bukti gagal atau masukkan pilot ke statistik seri 10.
- Backup lima role sebelum upgrade: `state/backups/before-0.1.3-2026-10-09/`.
- Snapshot WIP: `state/backups/resume-2026-10-09-0841/source-wip.tar.gz`.
- Kredensial lab: `state/deployment/proposal-2026-10-09/employee-onboarding.json`.
- Artefak 0.1.3 di `dist/`; arsip immutable dibuat sebelum catatan akhir.
- CLI GitHub lokal: `state/tooling/github/cli/usr/bin/gh`; branch `main`.
- Riwayat 0.1.2: [laporan lama](IMPLEMENTATION_REPORT_2026-10-08.md),
  [checkpoint lama](CHECKPOINT_2026-10-08.md) dan [jurnal lama](PROGRESS_2026-10-08.md).

Backup mengandung rahasia dan bukan snapshot disk atau backup di perangkat lain.
Jangan unggah state/key/env atau memulihkan index CA/CRL lama. Downgrade ke 0.1.2
meniadakan enforcement akun; jangan digunakan sebagai recovery otomatis.

## Belum terverifikasi / belum selesai

- TOTP HP dan login pribadi operator belum dikonfirmasi; lihat [aktivasi admin](AKTIVASI_ADMIN.md).
- Reboot workstation belum diuji; autostart VM nonaktif, jaringan libvirt autostart.
- MTTD/MTTR, benchmark, Windows serta fitur lifecycle/provisioning/notifikasi
  dan kebijakan resource belum lengkap. S-03 adalah observasi jalur underlay;
  S-04 terbatas ICMP, belum MITM/TCP/aplikasi manufaktur.
- Disable akun 1,146 detik termasuk SSH bukan pengukuran MTTD/MTTR atau S-04.
- Hasil reboot, lease 300 detik dan stabilitas 681,95 detik adalah bukti versi
  sebelumnya, tidak seluruhnya diulang pada 0.1.3.
- Masalah boot/checksum sore 8 Oktober tidak terulang; penyebab perubahan keadaan
  belum diketahui. Bukti asli dipertahankan. Kernel/source WireGuard tidak diubah.
