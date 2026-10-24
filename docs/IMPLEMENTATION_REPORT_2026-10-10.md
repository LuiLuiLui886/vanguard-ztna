# Hasil implementasi VanGuard — 10 Oktober 2026

> Arsip tahap 0.1.4. Lihat [checkpoint aktif](CHECKPOINT.md) untuk keadaan terbaru.

**Versi 0.1.4 terpasang pada lima VM Ubuntu Server 22.04.** Instrumentasi penolakan
admission dan sepuluh percobaan S-01 selesai: mean MTTD aplikasi **69,649 ms**,
mean MTTR **Respond** aplikasi **19,383 ms**. Akun karyawan valid pada attacker
berhasil login, tetapi proof perangkat salah ditolak tanpa peer VPN.
[Hasil per sampel dan batas pengukuran](RESPONSE_METRICS_2026-10-10.md).

## Perubahan dan perilaku

0.1.4 menambahkan jam monotonic per request dan correlation ID buatan server untuk
penolakan challenge/verify. MTTD berlangsung dari awal penanganan Flask sampai
penolakan terdeteksi; MTTR Respond dari deteksi sampai JSON penolakan siap, setelah
audit kebijakan biasa tetapi sebelum penyimpanan telemetry/header/jaringan.
Mean total server **89,032 ms** dan RTT attacker **119,313 ms** dicatat terpisah.
Definisi ditetapkan sebelum eksperimen pada [protokol metrik](RESPONSE_METRICS.md).

Event `admission_timing` hanya mencatat penolakan 400/403, bukan 429/503, login,
management atau keberhasilan. Password, token, body, sertifikat, signature dan
nonce tidak disimpan di event ini. ID kiriman caller tidak dipercaya. Runner
menyimpan hasil bertahap, mencocokkan ID dengan audit terautentikasi, menguji
kontrol positif perangkat sah dan membersihkan akun/identitas sementara.

Akun karyawan tetap terpisah dari administrator, sesi delapan jam, binding akun
immutable dan token server berupa hash. Semua enam pemeriksaan perangkat tetap
wajib: signature X.509, validity, CRL aktual, serial revocation, proof-of-possession
dan binding public key WireGuard. Registrasi hanya menyimpan identitas; peer
ditambah setelah admission. Metadata dashboard tidak mengubah key/sertifikat.
Topologi lima node dan kernel/source WireGuard dipertahankan.

## Bukti versi 0.1.4

| Pemeriksaan | Hasil |
|---|---|
| Suite lokal Python 3.12 | 100 PASS, 107,875 detik; [JUnit](test-results-0.1.4.xml) |
| Suite guest Ubuntu 22.04/Python 3.10 | 100 PASS, 168,907 detik; [JUnit](guest-test-results-0.1.4.xml) |
| Tes target akhir | 10 PASS, 9,090 detik |
| CI Python 3.10 / 3.12 | 100 / 100 PASS, 88,080 / 86,419 detik; nol failure/error/skip |
| Kualitas/build | Ruff, pip check, shell, build/checksum dan checksum artefak unduhan PASS |
| Rollout | Backup konsisten lima role, instalasi 0.1.4 dan startup COMPLETE |
| Integritas | 13 berkas aplikasi setiap VM cocok source; config, CA/key dan identitas utama cocok backup |
| S-01 terukur | Login valid 200; 10/10 proof_invalid 403 dengan ID unik; tidak ada peer attacker |
| Kontrol positif / cleanup | Perangkat sah diterima, identitas sementara dicabut/disabled, akun disabled; main ping PASS |
| Identity / S-02 | Registry-only, binding/proof/replay, CA-only revoke dan readmission ditolak PASS |
| Firewall | 40 pemeriksaan TCP dan uji negatif API/attacker/bypass LAN PASS |
| Health akhir | 7/7 PASS selama 84,18 detik; tiga deadline lease, nol removal selama observasi |

Source aplikasi: `c5b94af`, sudah dipush ke repository private;
[CI 37897878616](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/37897878616)
success. Perubahan dokumentasi setelahnya tidak mengubah source yang diuji.
Wheel terpasang `vanguard_ztna-0.1.4-py3-none-any.whl`, SHA-256
`14a64dce532894870cf4d5a6906f8e411bc7986b4f34905c53a057c0038b4c78`.
Arsip `dist/vanguard-0.1.4.tar.gz` dibuat sebelum catatan akhir dan tidak ditimpa;
Git menyimpan dokumentasi terbaru.

## Bukti dan pemulihan

- Bukti privat sesi ini: `state/deployment/metrics-2026-10-10/`: `rollout.json`,
  `installed-manifest.json`, `resume-login.json`, `s01-response/response-metrics.json`,
  `identity/`, `before-upgrade/`, `final-health/`, `final-firewall/`, `ci-artifacts/`.
- XML lokal/guest/tes target asli: `state/deployment/metrics-2026-10-09/`.
- Backup sebelum upgrade: `state/backups/before-0.1.4-2026-10-10/`, lima role.
  Backup mengandung rahasia; tetap lokal, bukan backup disk/perangkat terpisah.
- Riwayat [0.1.3](IMPLEMENTATION_REPORT_2026-10-09.md),
  [S-03/S-04](SECURITY_RESULTS_2026-10-09.md),
  [0.1.2](IMPLEMENTATION_REPORT_2026-10-08.md) dipertahankan.
  JUnit 90 tes diarsipkan sebagai `test-results-0.1.3-security.xml` dan
  `guest-test-results-0.1.3-security.xml`; pilot gagal lama tidak dihapus.
- Jangan memulihkan index CA/CRL lama. Rollback 0.1.3 kehilangan telemetry;
  rollback 0.1.2 juga kehilangan enforcement akun dan bukan pemulihan otomatis.

Kelima VM ditemukan mati saat resume; penyebab belum diketahui. Domain lama
dinyalakan, sesi USERNAME_LOKAL yang expired diperbarui secara privat tanpa enrollment
ulang, lalu health sebelum upgrade lulus. Sesi baru berakhir **10 Oktober 08:52:10
WIB**. Renewal admission tidak memperpanjang sesi; lihat [panduan akun](https://github.com/LuiLuiLui886/vanguard-ztna/blob/31c6981/docs/EMPLOYEE_ACCESS.md).

## Batas kesimpulan dan pekerjaan berikutnya

Angka S-01 mengukur respons aplikasi pada proof salah sesudah login akun valid;
bukan waktu sejak password bocor, respons operator/SOC, recovery atau semua ancaman.
Default-deny sudah menahan akses. Hasil sepuluh sampel bukan SLA atau pembuktian
superioritas tanpa pembanding. Tes unit memakai adapter WireGuard memori; bukti
peer kernel berasal dari uji live terpisah.

S-03 3/3 dan S-04 ICMP 10/10 adalah bukti **0.1.3**, tidak diulang penuh pada
0.1.4. Batas konfirmasi revoke 7,351–12,737 detik termasuk SSH/polling bukan
MTTD/MTTR. Capture bukan pembuktian MITM/kriptografi formal; sesi TCP/aplikasi
belum diuji. Hasil reboot/lease/stabilitas versi lama tetap bukti historis.

Berikutnya implementasikan runner/cleanup dan pilot benchmark clear serta VanGuard
sesuai [rencana tiga kondisi × 10](BENCHMARK_PLAN.md). Benchmark belum dijalankan,
iperf3 belum dipasang, dan baseline WG tanpa admission memerlukan pengecualian
eksplisit setelah runner tersedia untuk review. Gap Windows, lifecycle sertifikat,
provisioning/notifikasi dan kebijakan resource ada di [matriks proposal](PROPOSAL_ALIGNMENT.md).
TOTP HP/login pribadi belum dikonfirmasi; reboot workstation belum diuji, autostart
VM nonaktif. Seluruh TA belum dinyatakan selesai. [Checkpoint](CHECKPOINT.md)
dan [jurnal](PROGRESS_2026-10-10.md) menjadi acuan melanjutkan.
