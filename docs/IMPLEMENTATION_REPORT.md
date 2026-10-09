# Hasil implementasi VanGuard — 9 Oktober 2026

**Versi 0.1.3 terpasang pada lima VM Ubuntu Server 22.04.** Akun karyawan,
binding akun-perangkat dan metadata dashboard telah ditambahkan untuk penyelarasan
proposal. S-01 lulus; pengujian tambahan S-03 capture **3/3** dan S-04 pencabutan
akses ICMP **10/10** lulus. [Hasil per putaran](SECURITY_RESULTS_2026-10-09.md)
memuat angka, checksum, kegagalan pilot dan batas kesimpulan.
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
| Suite lokal Python 3.12 | 90 PASS, 97,417 detik, [JUnit](test-results.xml) |
| Suite guest Ubuntu 22.04/Python 3.10 | 90 PASS, 118,172 detik, [JUnit](guest-test-results.xml) |
| CI Ubuntu 22.04 | 90 PASS Python 3.10 dan 90 PASS Python 3.12, [run 37895229707](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/37895229707) |
| Kualitas/build | Ruff, pip check, shell, wheel/source dan checksum PASS |
| Rollout | Backup lima role, paket 0.1.3 dan startup layanan COMPLETE |
| Integritas | 12 berkas paket setiap VM cocok source; config, CA/key dan identitas utama cocok backup |
| S-01 negatif | Login attacker 200; tanpa cert 400; binding salah, proof key lain dan replay 403; tidak ada peer attacker |
| S-01 kontrol positif | Sesi akun + proof perangkat sah menghasilkan peer kernel |
| Disable akun | Peer dihapus, sesi lama ditolak, client utama tetap bisa ping |
| Identity/S-02 | Registrasi tanpa peer; proof/binding/replay ditolak; CA-only revoke menghapus peer dengan audit certificate_revoked; readmission 403 |
| Cleanup | Kedua identitas sementara dicabut/disabled dan akun disabled |
| Firewall/attacker | 40 TCP allow/deny PASS, API negatif PASS, bypass route LAN ditolak |
| S-03 | 3/3 PASS: marker ada pada kontrol wg0, tidak ada pada underlay eth0; 20 paket per capture, nol drop |
| S-04 ICMP | 10/10 PASS: CA-only revoke, peer dihapus, 25 probe tanpa reply dan readmission 403; batas atas konfirmasi 7,351–12,737 detik |
| Cleanup eksperimen | 12 identitas pilot/seri disabled; timer, namespace, interface dan rule sementara tidak tersisa |
| Health terbaru | 7/7 PASS selama 85,90 detik; tiga deadline lease, nol removal |

Direktori bukti privat: `state/deployment/proposal-2026-10-09/`.
Rollout: `rollout.json`; integritas: `installed-manifest.json`;
S-01: `s01/employee-verification.json`; identity: `identity/final-check-*.json`;
firewall: `firewall/operations-matrix.json`; observasi akhir: `after-upgrade/health.json`.
Itu adalah bukti rilis awal. Bukti eksperimen terbaru berada di
`state/deployment/security-2026-10-09/`: `capture/`, `series/`, `cleanup-audit.json`,
`final-health/`, `final-firewall/`, JUnit, `ci-artifacts/`, serta pilot gagal/valid
yang dipertahankan. Status aktif dicatat pada [checkpoint](CHECKPOINT.md).

Empat artefak CI diunduh ke `ci-artifacts/`; checksum paket diperiksa ulang.
Source aplikasi ada pada commit `0c56374`; instrumentasi S-03/S-04 di `f29ff67`
pada repository GitHub private. JUnit awal 76 tes tersimpan sebagai
`test-results-0.1.3-core.xml` dan `guest-test-results-0.1.3-core.xml`.
Commit catatan setelahnya hanya memperbarui dokumentasi/evidence. Arsip lokal
`dist/vanguard-0.1.3.tar.gz` dibuat sebelum catatan akhir dan tidak ditimpa;
Git adalah sumber dokumentasi terbaru. Wheel terpasang memiliki SHA-256
`b84430b1b3ae53de3b3b758dbd66fe22935accf0d1f1c7fd87c45ec786716097`.

## Batas kesimpulan dan pekerjaan berikutnya

Suite memakai OpenSSL nyata, HTTPS dan database fixture; adapter WireGuard unit
berada dalam memori. Bukti peer kernel berasal dari lab, bukan dari jumlah tes
pytest. Uji identity/S-01 awal memakai peer sementara tanpa tunnel kedua;
S-04 memakai tunnel terisolasi kedua pada VM-CLIENT yang sama, bukan VM baru.
Pengamatan disable akun 1,146 detik mencakup SSH dan hanya satu pengujian;
angka ini bukan MTTD/MTTR ataupun pembuktian trafik S-04.

S-03 tidak membuktikan MITM atau kriptografi secara formal. S-04 mengukur akses
ICMP dengan jam monotonic workstation; mean batas atas konfirmasi 10,645 detik
termasuk SSH/polling. Tidak ada timestamp deteksi terpisah atau uji recovery,
sehingga **MTTD/MTTR belum diukur**. Penutupan sesi TCP/aplikasi dan benchmark
tiga konfigurasi × 10 pengulangan belum selesai. Windows, lifecycle
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
