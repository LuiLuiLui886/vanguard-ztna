# Lanjutkan proyek VanGuard

> **Pembaruan 13:52 WIB:** S-03 3/3 dan S-04 ICMP 10/10 PASS; eksperimen serta
> cleanup selesai. [Hasil per putaran](docs/SECURITY_RESULTS_2026-10-09.md).

Status **9 Oktober 2026**: tahap **0.1.3 selesai dan terpasang pada lima VM**.
Akun karyawan untuk VPN dan metadata dashboard sudah tersedia. Skenario S-01
dengan kredensial karyawan valid pada perangkat attacker **PASS**: login akun
berhasil, tetapi perangkat tanpa proof sah tidak mendapatkan peer VPN.

Baca `AGENTS.md`, `VANGUARD_CONTEXT.md`, [checkpoint](docs/CHECKPOINT.md) dan
[jurnal terbaru](docs/PROGRESS_2026-10-09.md) sebelum mengubah apa pun.

## Hasil terakhir

- **90 tes lokal, 90 guest, serta 90 pada masing-masing job CI Python 3.10/3.12 lulus.**
- Paket/config/identitas diverifikasi; CA, key dan sertifikat client utama tetap.
- S-01, disable akun, proof/binding/replay, pencabutan sertifikat dan cleanup lulus.
- Firewall 40 pemeriksaan dan penolakan bypass LAN lulus.
- S-03 capture 3/3 PASS. S-04 revoke ICMP 10/10 PASS, batas atas konfirmasi
  7,351–12,737 detik termasuk SSH/polling; bukan MTTD/MTTR. Resource uji dibersihkan.
- Health akhir 7/7 sampel selama 85,90 detik: renewal berjalan, nol removal,
  layanan dan tunnel utama sehat. Tidak ada pengujian/rollout yang masih berjalan.
- Source `0c56374` dipush ke [GitHub private](https://github.com/LuiLuiLui886/vanguard-ztna);
  instrumentasi `f29ff67` dan
  [CI run 37895229707](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/37895229707) success.
  Catatan akhir disimpan dalam commit dokumentasi setelahnya.

## Mulai sesi berikutnya

Periksa domain yang ada dan jalankan preflight/health dengan direktori bukti baru;
perintah lengkap ada pada checkpoint. Jangan membuat ulang lab atau enrollment.
Lima node/alamat tetap: CA `.10`, SERVER `.20`, CLIENT `.30`, ADMIN `.40`, ATTACKER
`.50`, subnet `192.168.100.0/24`; client tunnel `10.8.0.2`, server `10.8.0.1`.

**Sesi karyawan berlaku delapan jam.** Jika sudah habis, login ulang pada VM-CLIENT
lalu restart layanan sesuai [panduan akun](docs/EMPLOYEE_ACCESS.md). Akun lab
`employee-lab` terikat ke `vm-client`; kredensial bootstrap ada dalam file privat
`state/deployment/proposal-2026-10-09/employee-onboarding.json`. Jangan cetak atau
unggah isinya. TOTP admin terpisah dari login karyawan.

Pekerjaan berikutnya: definisikan/instrumentasikan MTTD/MTTR (deteksi dan recovery
terpisah), lalu siapkan benchmark tiga konfigurasi × 10 pengulangan. Penutupan
sesi TCP/aplikasi belum tercakup hasil ICMP. Baseline
WireGuard tanpa admission memerlukan keputusan eksplisit setelah rencana isolasi
dan pemulihan tersedia. Gap Windows/lifecycle/notifikasi/resource ada di
[matriks proposal](docs/PROPOSAL_ALIGNMENT.md). Seluruh TA belum dinyatakan selesai.

## Penyimpanan dan dokumentasi

- Bukti rilis: `state/deployment/proposal-2026-10-09/`; eksperimen terbaru:
  `state/deployment/security-2026-10-09/`. Bukti pilot gagal tetap dipertahankan.
- Backup privat sebelum upgrade: `state/backups/before-0.1.3-2026-10-09/`.
- Source/wheel/checksum: `dist/`; arsip terdahulu tidak ditimpa.
- [Laporan aktif](docs/IMPLEMENTATION_REPORT.md), [panduan demo](docs/DEMO_TA.md),
  [panduan aktivasi admin](docs/AKTIVASI_ADMIN.md).
- Branch `main`, remote `origin`; CLI lokal `state/tooling/github/cli/usr/bin/gh`.

Catat rencana sebelum setiap kelompok perubahan dan hasil/validasi/sisa pekerjaan
sesudahnya. Perbarui checkpoint serta file ini sebelum berhenti, lalu commit/push.
State/database/private key/disk VM tetap lokal. Jangan mengembalikan index CA/CRL
lama atau otomatis downgrade ke 0.1.2 yang belum mewajibkan akun karyawan.

TOTP di HP/login pribadi belum dikonfirmasi; reboot workstation belum diuji.
Autostart VM nonaktif. Bukti reboot/lease/stabilitas panjang versi lama disimpan
terpisah; jangan menganggapnya sebagai hasil ulang 0.1.3.
