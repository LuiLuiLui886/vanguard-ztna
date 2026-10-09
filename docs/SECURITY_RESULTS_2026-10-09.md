# Hasil eksperimen S-03/S-04 — 9 Oktober 2026

**S-03: 3/3 PASS. S-04: 10/10 PASS untuk akses ICMP.** Aplikasi tetap 0.1.3;
tidak ada perubahan kernel WireGuard, CA/key utama, atau jumlah VM.
[Protokol dan batas pengukuran](SECURITY_EXPERIMENTS.md) ditetapkan sebelum pilot.
Instrumentasi akhir tersimpan pada commit `f29ff67`.

## S-03 — capture jalur luar dan kontrol plaintext

Sepuluh echo-request dengan payload 96 byte dan marker acak 16 byte dikirim pada
setiap pengulangan. Setiap capture berisi 20 paket, tanpa kernel drop/truncation.
Pada eth0, marker tidak ditemukan; pada wg0, marker muncul di seluruh 20 paket
request/reply. Checksum keenam capture yang disalin ke workstation diperiksa ulang.

| Putaran | Paket underlay | Paket underlay berisi marker | Paket kontrol berisi marker | Hasil |
|---|---:|---:|---:|---|
| 1 | 20 | 0 | 20 | PASS |
| 2 | 20 | 0 | 20 | PASS |
| 3 | 20 | 0 | 20 | PASS |

| Putaran / capture | SHA-256 |
|---|---|
| 1 / underlay | `b8d7e5cefe8c67a1aaafe48378d412bfb02452c148b94d6cc462537fa21e2808` |
| 1 / plaintext_control | `efe631844f70018e11d6e73436b436dd9d289d30a117d25d7a6a5522207f896a` |
| 2 / underlay | `1e81f62f8060127091df05c0f7765450311701d0296f277f10596c65231048a9` |
| 2 / plaintext_control | `d4b521fa7308d5c6099fe8af50c1e43063a00cb670c1a66fe38f5a712361ea5d` |
| 3 / underlay | `82828febcd176db7cd3df8bf7276f2bca57824dbf9fa292a6eb84c731a1e1d48` |
| 3 / plaintext_control | `8fdab1fe2b84730ec8336055bc06d9962f18d84ee5daf56e14657da83305ad9a` |

Bukti menunjukkan marker uji tidak tampak pada underlay dalam jendela capture.
Ini bukan bukti formal kekuatan kriptografi atau simulasi MITM; alamat, ukuran
dan timing paket tetap dapat diamati. Capture dilakukan di underlay VM-CLIENT,
bukan klaim bahwa VM-ATTACKER menerima semua trafik unicast switch.

## S-04 — pencabutan CA pada tunnel sementara yang aktif

Setiap putaran memakai identitas/akun baru, admission sah dan lima probe positif.
Revoke dikirim hanya ke CA. Daemon menghapus peer dengan alasan audit
`certificate_revoked`; selanjutnya 25 probe konfirmasi menerima nol reply dan
readmission ditolak HTTP 403. Identitas utama tetap dapat mengakses tunnel.

Kolom waktu adalah **batas atas observasi** dari monotonic workstation sebelum
SSH request revoke, termasuk SSH/polling. Kolom konfirmasi juga mencakup rangkaian
25 probe tanpa reply. Bukan waktu deteksi internal daemon yang presisi.

| Putaran | Blok pertama teramati (detik) | Konfirmasi selesai (detik) | Reply konfirmasi | Cleanup |
|---|---:|---:|---:|---|
| 1 | 6,162 | 11,871 | 0/25 | PASS |
| 2 | 6,138 | 11,882 | 0/25 | PASS |
| 3 | 6,011 | 11,721 | 0/25 | PASS |
| 4 | 4,373 | 10,098 | 0/25 | PASS |
| 5 | 7,016 | 12,737 | 0/25 | PASS |
| 6 | 3,424 | 9,118 | 0/25 | PASS |
| 7 | 5,343 | 11,048 | 0/25 | PASS |
| 8 | 1,642 | 7,351 | 0/25 | PASS |
| 9 | 2,190 | 7,898 | 0/25 | PASS |
| 10 | 7,021 | 12,725 | 0/25 | PASS |

- n = 10; rata-rata batas atas konfirmasi **10,645 detik**.
- Median 11,385; minimum 7,351;
  maksimum **12,737 detik**, seluruhnya <60 detik.
- Setiap ruleset stateless sebelum/sesudah identik. Audit akhir memeriksa 12
  identitas (pilot gagal setelah enrollment, pilot valid, dan seri 10): seluruh
  perangkat/akun uji disabled, timer/namespace/interface/rule uji tidak tersisa,
  dan hanya peer utama aktif.
- Matriks firewall akhir: 40 TCP allow/deny PASS; attacker API dan penolakan
  bypass LAN PASS. Hasil observasi layanan akhir tersedia pada checkpoint.

Cakupan adalah penghentian akses ICMP pada dua tunnel bersamaan di VM-CLIENT yang
sama, dengan izin ICMP sementara khusus 10.8.0.3 melalui wg0. Belum membuktikan
penutupan sesi TCP/aplikasi manufaktur atau performa dua mesin client fisik.
**MTTD/MTTR tidak diukur pada dataset S-04 ini**; rata-rata di atas tidak diberi
label MTTD/MTTR. Koreksi sesudah pembacaan ulang proposal: MTTR berarti Respond,
bukan pemulihan layanan. Instrumentasi S-01 terpisah didefinisikan pada
[RESPONSE_METRICS.md](RESPONSE_METRICS.md), tanpa mengubah angka historis di sini.

## Pilot gagal dan pemulihan

1. `pilot/`: FAIL sebelum enrollment karena seluruh VM ditemukan mati ketika
   sesi dilanjutkan. Tidak ada mutasi jaringan. Lima VM lama dinyalakan kembali;
   penyebab shutdown tidak diketahui.
2. `pilot-resume/`: FAIL pada pemeriksaan output probe sesudah revoke.
   Versi pertama tidak menyimpan output ping lengkap sehingga sebab persis belum
   terbukti. Cleanup PASS dan ruleset utama pulih.
3. `pilot-fixed/`: PASS setelah probe memakai count/timeout respons tanpa
   deadline keseluruhan, serta diagnosis output ditambahkan. Batas atas konfirmasi
   10,184 detik. Pilot ini tidak digabungkan ke statistik seri 10.

Pengulangan gagal tidak dihapus atau dihitung sebagai lulus. Tidak ada perubahan
aplikasi untuk memaksa hasil eksperimen lulus.

## Penyimpanan dan reproduksi

Evidence mentah privat berada di `state/deployment/security-2026-10-09/`:
`capture/`, `pilot/`, `pilot-resume/`, `pilot-fixed/`, `series/`,
`cleanup-audit.json`, `final-firewall/`, dan `final-health/`.
Capture/filter/checksum, tiap tahap, probe, audit dan timing tersimpan di JSON.
Sertifikat/akun uji dicabut/disabled; file identitas privat dipertahankan untuk
evidence dan tidak diunggah. Laporan ini berisi data nonrahasia untuk GitHub/TA.

Skrip: [verify_security.py](../scripts/verify_security.py) dan
[security_worker.py](../scripts/security_worker.py). Pengujian parser, scope cleanup
dan statistik: [test_security_evidence.py](../tests/test_security_evidence.py).
Suite lokal 90 PASS, termasuk 14 tes instrumentasi. Hasil guest/CI final dicatat
pada [laporan implementasi](IMPLEMENTATION_REPORT.md) dan [CI](CI.md).
