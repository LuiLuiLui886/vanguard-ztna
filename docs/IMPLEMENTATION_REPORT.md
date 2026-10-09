# Hasil implementasi VanGuard — 9 Oktober 2026

**Versi 0.1.3 terpasang pada lima VM Ubuntu Server 22.04.** Akun karyawan,
binding akun-perangkat dan metadata dashboard telah ditambahkan untuk penyelarasan
proposal. Skenario S-01 dengan akun valid pada perangkat attacker lulus.
Riwayat 0.1.2 dipertahankan pada [laporan 8 Oktober](IMPLEMENTATION_REPORT_2026-10-08.md).

## Perubahan dan perilaku

Karyawan login melalui HTTPS dengan akun lokal yang terpisah dari administrator.
Password di-hash scrypt; server menyimpan hash token sesi, sedangkan client menyimpan
token pada file 0600 tanpa menyimpan password. Sesi berlaku delapan jam. Challenge
dan verify memerlukan sesi yang sama, akun aktif dan binding perangkat yang sah.
Lease tidak melewati kedaluwarsa sesi, sertifikat atau CRL. Disable akun menghapus
peer terkait; sesi expired ditolak dan memerlukan login ulang.

Sesi akun tetap harus disertai enam pemeriksaan perangkat: signature X.509,
periode sertifikat, CRL aktual, serial tidak dicabut, proof-of-possession, dan
binding public key WireGuard. Registrasi hanya menyimpan identitas; peer kernel
ditambah sesudah admission. Tidak ada default akun atau bypass untuk perangkat lama.
Client utama dimigrasikan secara eksplisit ke akun lab tanpa mengganti key/sertifikat.

Dashboard menyediakan pembuatan/penonaktifan akun, pengikatan perangkat lama, serta
nama perangkat, departemen, pemilik dan platform. Metadata dapat diedit tanpa
mengubah identitas kriptografis. Metadata bukan attestation perangkat; data organisasi
nyata tidak dibuat-buat. Binding akun immutable; reset password dan aktivasi ulang
akun belum tersedia. Panduan pengguna: [EMPLOYEE_ACCESS.md](EMPLOYEE_ACCESS.md).

## Bukti versi 0.1.3

| Pemeriksaan | Hasil |
|---|---|
| Suite lokal Python 3.12 | 76 PASS, 152,31 detik, [JUnit](test-results.xml) |
| Suite guest Ubuntu 22.04/Python 3.10 | 76 PASS, 121,05 detik, [JUnit](guest-test-results.xml) |
| CI Ubuntu 22.04 | 76 PASS Python 3.10 dan 76 PASS Python 3.12, [run 37871996411](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/37871996411) |
| Kualitas/build | Ruff, pip check, shell, wheel/source dan checksum PASS |
| Rollout | Backup lima role, paket 0.1.3 dan startup layanan COMPLETE |
| Integritas | 12 berkas paket setiap VM cocok source; config, CA/key dan identitas utama cocok backup |
| S-01 negatif | Login attacker 200; tanpa cert 400; binding salah, proof key lain dan replay 403; tidak ada peer attacker |
| S-01 kontrol positif | Sesi akun + proof perangkat sah menghasilkan peer kernel |
| Disable akun | Peer dihapus, sesi lama ditolak, client utama tetap bisa ping |
| Identity/S-02 | Registrasi tanpa peer; proof/binding/replay ditolak; CA-only revoke menghapus peer dengan audit certificate_revoked; readmission 403 |
| Cleanup | Kedua identitas sementara dicabut/disabled dan akun disabled |
| Firewall/attacker | 40 TCP allow/deny PASS, API negatif PASS, bypass route LAN ditolak |

Direktori bukti privat: `state/deployment/proposal-2026-10-09/`.
Rollout: `rollout.json`; integritas: `installed-manifest.json`;
S-01: `s01/employee-verification.json`; identity: `identity/final-check-*.json`;
firewall: `firewall/operations-matrix.json`; observasi akhir: `after-upgrade/health.json`.
Status dan durasi observasi final dicatat pada [checkpoint](CHECKPOINT.md).

Empat artefak CI diunduh ke `ci-artifacts/`; checksum paket diperiksa ulang.
Source implementasi ada pada commit `0c56374` di repository GitHub private.
Commit catatan setelahnya hanya memperbarui dokumentasi/evidence. Arsip lokal
`dist/vanguard-0.1.3.tar.gz` dibuat sebelum catatan akhir dan tidak ditimpa;
Git adalah sumber dokumentasi terbaru. Wheel terpasang memiliki SHA-256
`b84430b1b3ae53de3b3b758dbd66fe22935accf0d1f1c7fd87c45ec786716097`.

## Batas kesimpulan dan pekerjaan berikutnya

Suite memakai OpenSSL nyata, HTTPS dan database fixture; adapter WireGuard unit
berada dalam memori. Bukti peer kernel berasal dari lab, bukan dari jumlah tes
pytest. Identity sementara memakai `10.8.0.3` tanpa tunnel client kedua.
Pengamatan disable akun 1,146 detik mencakup SSH dan hanya satu pengujian;
angka ini bukan MTTD/MTTR ataupun pembuktian trafik S-04.

S-03 packet capture, S-04 penghentian trafik dengan timestamp berulang, MTTD/MTTR
dan benchmark tiga konfigurasi × 10 pengulangan belum selesai. Windows, lifecycle
sertifikat, provisioning/notifikasi dan pemetaan kebijakan resource masih tercatat
di [matriks proposal](PROPOSAL_ALIGNMENT.md). Baseline WireGuard tanpa admission
perlu rencana isolasi/pemulihan dan keputusan eksplisit atas pengecualian aturan lab.

Konfirmasi TOTP HP/login pribadi belum diterima. Reboot workstation belum diuji;
hasil reboot/lease/stabilitas panjang sebelumnya adalah bukti versi terdahulu,
bukan pengujian ulang 0.1.3. Masalah boot/checksum sore 8 Oktober tidak terulang,
tetapi penyebab perubahan keadaan belum diketahui; bukti lama dipertahankan.

Backup privat sebelum upgrade: `state/backups/before-0.1.3-2026-10-09/`.
Jangan unggah state/secret atau mengembalikan index CA/CRL lama. Rollback ke 0.1.2
menghilangkan enforcement akun karyawan; jangan dilakukan otomatis sebagai recovery.
Topologi lima node dan WireGuard standar tetap dipertahankan.
