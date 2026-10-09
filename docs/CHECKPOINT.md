# Checkpoint VanGuard — 10 Oktober 2026

**Tahap 0.1.4 selesai dan terpasang pada lima VM.** Pengukuran S-01 selesai
10/10 PASS: mean MTTD aplikasi **69,649 ms**, MTTR **Respond** aplikasi
**19,383 ms**. MTTR proposal bukan recovery. Source `c5b94af` dipush ke
[GitHub private](https://github.com/LuiLuiLui886/vanguard-ztna);
[CI 37897878616](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/37897878616)
success. Catatan akhir masuk commit dokumentasi setelahnya; periksa HEAD dan
`origin/main` saat melanjutkan.

## Keadaan terverifikasi

| Bagian | Hasil |
|---|---|
| Lima VM Ubuntu 22.04 | CA .10, SERVER .20, CLIENT .30, ADMIN .40, ATTACKER .50 aktif; subnet 192.168.100.0/24 |
| Paket / integritas | 0.1.4, 13 berkas per VM cocok source; config, CA/key dan identitas utama cocok backup |
| Akun VPN | employee-lab terikat ke vm-client; sesi berakhir 10 Oktober 2026 08:52:10 WIB |
| Tes | 100 lokal + 100 guest; CI Python 3.10/3.12 masing-masing 100 PASS |
| S-01 kuantitatif | Login valid 200; 10 proof_invalid 403; tanpa peer attacker; kontrol positif dan cleanup PASS |
| Identity / S-02 | Registry-only, proof/binding/replay, CA-only revoke, readmission ditolak dan cleanup PASS |
| Firewall | 40 TCP dan uji negatif API/attacker/bypass LAN PASS |
| Health akhir | 7/7 PASS, 84,18 detik; tiga deadline lease, nol removal selama observasi |
| Tunnel utama | Server 10.8.0.1, peer client 10.8.0.2/32; handshake/ping sehat |
| Historis 0.1.3 | S-03 3/3 dan S-04 ICMP 10/10 PASS; tidak diulang penuh pada 0.1.4 |

Tidak ada rollout atau eksperimen yang masih berjalan. Enam pemeriksaan admission,
topologi lima node dan WireGuard standar tetap. Angka timing hanya mencakup batas
aplikasi yang didefinisikan sebelum pengujian; RTT dicatat terpisah.
Lihat [hasil S-01](RESPONSE_METRICS_2026-10-10.md),
[laporan](IMPLEMENTATION_REPORT.md) dan [jurnal terbaru](PROGRESS_2026-10-10.md).

Tutorial operator dari awal sampai akhir tersedia di
[TUTORIAL_PENGGUNAAN.md](TUTORIAL_PENGGUNAAN.md). Disusun dari CLI/template 0.1.4;
latihan registrasi manual dan shutdown tidak dieksekusi saat penulisannya.
Panduan deployment diperbaiki agar enrollment baru mencakup akun/binding/login
karyawan sebelum connect. Tidak ada perubahan source atau VM pada pekerjaan ini.

## Melanjutkan sesi berikutnya

1. Baca `AGENTS.md`, `VANGUARD_CONTEXT.md`, checkpoint ini dan jurnal terbaru.
2. Periksa domain lama. Saat resume terakhir semuanya mati tanpa sebab diketahui;
   `bash scripts/open_dashboard.sh` dapat menyalakannya. Jangan membuat ulang
   lab/CA/identitas atau mengulang rollout/enrollment utama.
3. Jalankan preflight dan health dengan direktori bukti baru:

```bash
.venv/bin/python scripts/ssh_preflight.py state/lab/inventory.json
.venv/bin/python scripts/health_lab.py state/lab/inventory.json \
  --state state/deployment/health-run-baru
```

4. Jika sesi delapan jam expired, login ulang privat pada VM-CLIENT lalu restart
   `vanguard-client` sesuai [panduan akun](EMPLOYEE_ACCESS.md). Renewal/boot tidak
   memperpanjang sesi atau melakukan login otomatis. Jangan cetak token/password.
5. Implementasikan runner/cleanup benchmark sesuai [rencana](BENCHMARK_PLAN.md),
   pasang iperf3 tanpa daemon persisten, lalu pilot clear dan VanGuard. Ketiga
   konfigurasi × 10 belum dijalankan. WG standar tanpa admission masih memerlukan
   pengecualian eksplisit aturan; siapkan implementasi yang bisa ditinjau dahulu.
6. Catat rencana sebelum setiap kelompok perubahan dan hasil setelahnya; simpan
   kegagalan/hasil parsial, update checkpoint/resume, validasi, commit/push private.

Runner identity/employee/response memakai peer uji 10.8.0.3: jalankan berurutan,
bukan bersamaan. Jangan menjalankan benchmark bersama suite guest atau eksperimen
lain. Sisa cakupan TCP/aplikasi, Windows, lifecycle/provisioning/notifikasi/resource
tercantum pada [matriks proposal](PROPOSAL_ALIGNMENT.md).

## Bukti dan pemulihan

- Aktif: `state/deployment/metrics-2026-10-10/`: rollout/integritas/login,
  `s01-response/`, `identity/`, `before-upgrade/`, `final-health/`,
  `final-firewall/`, `ci-artifacts/`. Suite asli: `metrics-2026-10-09/`.
- Backup privat lima role: `state/backups/before-0.1.4-2026-10-10/`.
- Kredensial bootstrap: `state/deployment/proposal-2026-10-09/employee-onboarding.json`.
- Wheel/source/checksum: `dist/`; arsip immutable mendahului catatan akhir.
- CLI GitHub: `state/tooling/github/cli/usr/bin/gh`; branch main, remote origin.
- Arsip [checkpoint 9 Oktober](CHECKPOINT_2026-10-09.md),
  [resume 9 Oktober](LANJUTKAN_PROYEK_2026-10-09.md),
  [laporan 0.1.3](IMPLEMENTATION_REPORT_2026-10-09.md),
  [S-03/S-04](SECURITY_RESULTS_2026-10-09.md). Pernyataan WIP/versi di arsip adalah
  keadaan saat itu, bukan status sekarang. Bukti gagal lama tetap dipertahankan.

Backup mengandung rahasia dan bukan snapshot disk atau backup perangkat terpisah.
Jangan unggah state/key/env atau memulihkan index CA/CRL lama. Downgrade 0.1.3
menghilangkan telemetry, 0.1.2 menghilangkan enforcement akun; jangan otomatis.

TOTP HP/login pribadi belum dikonfirmasi; reboot workstation belum diuji.
Autostart VM nonaktif. Penyebab VM mati pada resume belum diketahui. Hasil
reboot/lease/stabilitas lama bukan hasil ulang 0.1.4. Seluruh TA belum selesai.
