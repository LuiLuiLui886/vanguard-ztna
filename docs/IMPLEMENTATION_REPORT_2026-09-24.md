# Hasil implementasi VanGuard — 24 September 2026

## Status

**Deployment lima VM sudah berjalan di KVM/libvirt.** VM-CA `.10`, VM-SERVER `.20`,
VM-CLIENT `.30`, VM-ADMIN `.40`, dan VM-ATTACKER `.50` menggunakan Ubuntu Server 22.04.
CA, HTTPS, token antarlayanan, akun admin/TOTP, registry, daemon, dan client sudah dikonfigurasi.
Client utama `vm-client` memiliki satu peer aktif dengan allowed IP `10.8.0.2/32`;
handshake kernel WireGuard dan ping ke `10.8.0.1` berhasil.

Kelima VM ditemukan dalam kondisi mati saat sesi dilanjutkan, kemudian dinyalakan tanpa
membuat ulang disk atau mengubah topologi. Installer diperbarui pada seluruh VM untuk
memperbaiki akses akun layanan ke virtual environment. Cara akses ada di [LAB_ACCESS.md](LAB_ACCESS.md).

## Bukti pada VM nyata

`scripts/verify_lab.py` menggunakan identitas sementara sebelum enrollment client utama.
Uji terakhir dimulai pada **24 September 2026 06:08:47 UTC**. Sepuluh pemeriksaan lulus:

| Pemeriksaan | Bukti |
|---|---|
| Boot layanan bersih | Server tidak memiliki peer |
| Registrasi | Sertifikat dan binding tersimpan; peer tetap kosong |
| Admission dan replay | Binding WG salah, proof salah, serta replay ditolak; proof sah diterima |
| Restart API | Peer dan lease dibersihkan |
| Tunnel kernel | Timestamp handshake bukan nol dan ping tunnel berhasil |
| CA offline | Peer dihapus daemon dan ping gagal |
| CA pulih | Admission baru memulihkan tunnel |
| Daemon dihentikan | Interface wg0 dan admission API ikut berhenti |
| Pencabutan oleh CA | Daemon membaca CRL, menghapus peer, dan admission berikutnya mendapat 403 |
| Pembersihan | Identitas uji dicabut dan dinonaktifkan, slot tunnel tersedia untuk client utama |

Bukti tambahan:

- VM-ATTACKER: registry tanpa token mendapat 401, verify palsu 403, challenge palsu 400.
- Dashboard HTTPS: verifikasi CA, login password + TOTP, logout, penolakan CSRF kosong,
  dan penolakan replay TOTP lulus.
- Restart layanan client berhasil membersihkan lalu membangun ulang tunnel.
- VM-SERVER direboot (boot kembali 06:10:17 UTC); layanan aktif otomatis dan client
  berhasil admission ulang serta ping tanpa penambahan peer manual.
- Suite lokal tetap lulus: 44 test. Ruff dan pemeriksaan dependency juga lulus.

Artefak bukti privat ada di `state/deployment/`: `live-verification.json`,
`dashboard-checks.json`, `restart-checks.json`, `attacker-checks.txt`,
`peers-before-registration.txt`, `peers-after-registration.txt`, dan
`wireguard-after-enrollment.txt`. Output WireGuard menggunakan format yang menyembunyikan
private key. Kredensial admin ada di file terpisah mode 0600 dan tidak masuk laporan/arsip.

Uji awal menemukan kegagalan pembersihan tunnel ketika systemd menghentikan client.
Unit client kini memakai `KillMode=mixed` dan batas shutdown 40 detik agar subprocess
`wg-quick down` dapat selesai. Uji pemulihan dan restart sesudah perbaikan lulus;
bukti percobaan awal disimpan sebagai `live-verification-first-attempt.json`.

## Komponen yang dibuat

| Komponen | Hasil |
|---|---|
| CA | OpenSSL private CA, issue, revoke, CRL, signing CSR HTTPS, locking index dan serial |
| Server | Registry SQLite immutable, enam admission checks, challenge sekali pakai, audit, rate limit |
| WireGuard | Adapter perintah native `wg`; satu jalur penambahan peer setelah admission |
| Daemon | Revalidasi CRL, lease 300 detik, removal expired/revoked/unknown, fail-closed saat CRL gagal |
| Client | Key X.509 dan WG independen, CSR/request JSON, proof ECDSA, connect dan renewal |
| Admin | Flask/Jinja2, SQLite, password hash, TOTP anti-replay, CSRF, sesi, enrollment/revoke/retry |
| Attacker | Tiga pemeriksaan API negatif terbatas pada lab |
| Deployment | Installer per-role Ubuntu 22.04, empat unit systemd, env/inventory contoh, constraints dependency |
| Dokumentasi | Topologi/alur, kontrak API, langkah deployment, keputusan keamanan, matriks uji TA |

Dokumen aturan asli AGENTS.md dan VANGUARD_CONTEXT.md dipertahankan. Lima VM, alamat,
tunnel `10.8.0.1/24` dan `10.8.0.2/24`, serta UDP 51820 tetap sesuai instruksi.

## Bukti verifikasi lokal

Perintah final:

```text
.venv/bin/pytest -q --junitxml=docs/test-results.xml
44 passed in 38.96s

.venv/bin/ruff check vanguard tests scripts
All checks passed!

.venv/bin/pip check
No broken requirements found.
```

Detail machine-readable ada di [test-results.xml](test-results.xml).

- PKI memakai **OpenSSL nyata**, sertifikat/CRL temporer, bukan validasi signature yang dimock.
- Registrasi terbukti tidak menambah peer; admission sah menambah key dan allowed IP yang terikat registry.
- Replay bersamaan, signature salah, private key salah, binding salah, challenge expired,
  sertifikat expired/future/revoked/issuer salah, CA certificate, serverAuth certificate,
  extension kritis asing, dan CRL stale/future/issuer/signature salah ditolak.
- Revoke saat peer aktif, CA offline, lease habis, restart, dan peer asing diuji.
- Login TOTP, replay TOTP, rate limit login, CSRF, logout, serta workflow registrasi/revoke parsial diuji.
- Alur CA → admin workflow → server → client → revoke berjalan melalui **socket HTTPS lokal**
  dengan verifikasi trust; CA publik yang tidak mempercayai lab ditolak.
- Interface WireGuard dalam suite lokal menggunakan adapter memori. Bukti kernel dan
  paket antar-VM berasal dari pengujian VM terpisah pada bagian di atas.
- `bash -n deploy/install.sh` lulus.
- Unit systemd lolos `systemd-analyze verify` dalam temporary root dengan fixture dependency
  wg-quick dan executable. Validasi pada host langsung tidak lengkap karena WireGuard dan
  path `/opt/vanguard` belum dipasang. Ini memvalidasi sintaks/dependency, bukan runtime service.
- Wheel Python berhasil dibangun, termasuk template Jinja dan stylesheet.
- Seluruh 18 dependency runtime yang dipin berhasil di-resolve/download untuk CPython 3.10
  Linux x86_64 dengan wheel yang kompatibel glibc Ubuntu 22.04. Suite lokal berjalan pada
  Python 3.12.3; suite lengkap belum diulang pada Python 3.10 guest. Pengujian layanan
  end-to-end terpisah telah dijalankan pada VM target.

## Artefak

- `dist/vanguard-0.1.0.tar.gz`: source aplikasi, tests, deployment, dan dokumentasi.
- `dist/vanguard_ztna-0.1.0-py3-none-any.whl`: paket Python yang dapat dipasang.
- `dist/SHA256SUMS`: checksum artefak.

Arsip tidak menyertakan virtual environment, state/database, private key, token, atau
sertifikat deployment. `docs/test-results.xml` hanya memuat hasil test, bukan secret lab.

## Pekerjaan lanjutan dan batas verifikasi

Pemeriksaan akhir mendapati satu penghapusan peer di luar skenario uji (audit ID 29,
24 September 2026 sekitar 06:13:50 UTC), kemudian admission otomatis berhasil lagi.
Satu pemeriksaan ping gagal; pemeriksaan berikutnya mendapat 5/5 balasan. Audit saat ini
menggabungkan penyebab expired/revoked/disabled/unknown/CRL unavailable dalam satu pesan,
sehingga akar masalah belum dapat dipastikan. Probe lanjutan terhadap 40 CRL baru tidak
menemukan kegagalan validasi. Kedua VM memakai NTP; validasi waktu tetap ketat.
Stabilitas jangka panjang perlu dipantau dan detail alasan pencabutan otomatis perlu
ditingkatkan sebelum mengklaim tunnel bebas gangguan.

1. Terapkan dan uji matriks firewall guest pada [DEPLOYMENT.md](DEPLOYMENT.md).
   Deployment ini belum mengaktifkan kebijakan firewall tersebut; UFW client teramati inactive.
2. Uji lease habis tanpa renewal selama 300 detik, peer asing, serta fixture PKI negatif
   tambahan pada VM bila diperlukan untuk bukti TA. Skenario tersebut sudah dicakup suite
   lokal, tetapi belum semuanya diulang dengan WireGuard kernel.
3. Reboot CA, client, admin, attacker, dan host secara terencana; reboot VM-SERVER sudah lulus.
4. Operator memasukkan TOTP ke authenticator dan memasang trust CA pada browser yang digunakan.

Identitas uji yang telah dicabut dipertahankan dalam riwayat CA/registry; identitas utama
`vm-client` tetap aktif. Batas teknis dan prosedur recovery ada di [SECURITY.md](SECURITY.md).
