# Hasil MTTD/MTTR aplikasi S-01 — 10 Oktober 2026

**Sepuluh percobaan terukur selesai PASS pada VanGuard 0.1.4.** Akun karyawan valid
berhasil login, tetapi proof dari private key lain ditolak HTTP 403 tanpa peer
attacker. Kontrol positif perangkat sah dan cleanup juga PASS. Definisi waktu
ditetapkan sebelum eksperimen pada [protokol](RESPONSE_METRICS.md).

## Skenario dan batas pengukuran

VM-ATTACKER mendapat kredensial akun sementara serta salinan sertifikat/public key,
tanpa private key perangkat. Setiap percobaan memakai challenge baru dan signature
ECDSA dari key yang salah. Audit terautentikasi server dikorelasikan dengan sepuluh
request ID unik buatan server; seluruh alasan penolakan adalah `proof_invalid`.

MTTD diukur dari awal penanganan Flask sampai objek penolakan dibuat. MTTR berarti
**Mean Time to Respond** sesuai proposal, diukur dari deteksi sampai JSON respons
penolakan siap. Kedua metrik memakai monotonic server; tidak mengurangi timestamp
dari dua VM. Timestamp akhir mendahului penulisan telemetry, finalisasi header dan
pengiriman jaringan. RTT memakai monotonic attacker dan disajikan terpisah.

Tidak mengukur waktu sejak password bocor, respons operator/SOC, recovery, atau
seluruh jenis ancaman. Default-deny sudah menahan akses; MTTR bukan lama attacker
boleh masuk. Skenario ini adalah penggunaan kredensial valid dengan proof perangkat
salah, bukan kampanye tebakan password massal. Tidak ada klaim superioritas tanpa
data pembanding.

## Sampel (milidetik)

| Percobaan | Deteksi | Respond sesudah deteksi | Total server | RTT attacker | HTTP |
|---|---:|---:|---:|---:|---:|
| 1 | 96,760 | 17,459 | 114,219 | 140,273 | 403 |
| 2 | 57,745 | 22,992 | 80,738 | 105,189 | 403 |
| 3 | 69,826 | 19,534 | 89,360 | 116,237 | 403 |
| 4 | 60,247 | 25,695 | 85,942 | 111,870 | 403 |
| 5 | 69,887 | 18,005 | 87,892 | 123,723 | 403 |
| 6 | 67,985 | 22,471 | 90,457 | 128,669 | 403 |
| 7 | 77,801 | 16,982 | 94,784 | 128,495 | 403 |
| 8 | 68,080 | 21,942 | 90,022 | 126,256 | 403 |
| 9 | 63,805 | 14,127 | 77,931 | 107,399 | 403 |
| 10 | 64,355 | 14,622 | 78,977 | 105,018 | 403 |

| Metrik | Mean | Median | Min | Max | Sample SD |
|---|---:|---:|---:|---:|---:|
| MTTD aplikasi (request → deteksi) | 69,649 | 68,033 | 57,745 | 96,760 | 11,051 |
| MTTR Respond aplikasi (deteksi → JSON siap) | 19,383 | 18,769 | 14,127 | 25,695 | 3,810 |
| Request → JSON respons siap | 89,032 | 88,626 | 77,931 | 114,219 | 10,406 |
| RTT attacker (POST → respons diterima) | 119,313 | 119,980 | 105,018 | 140,273 | 11,970 |

n = 10 pada semua metrik. Angka tabel dibulatkan; JSON menyimpan durasi ns asli.
Tidak ada sampel parsial, 429, kegagalan koneksi atau audit yang hilang dimasukkan
ke rata-rata. Nilai ini menggambarkan run pada lab VM yang diuji, bukan batas SLA.

## Validasi dan penyimpanan

- Source implementasi: `c5b94af`; paket 0.1.4 pada lima VM cocok source.
- Suite lokal 100 PASS, guest Python 3.10 100 PASS; CI Python 3.10 dan 3.12
  masing-masing 100 PASS, [run 37897878616](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/37897878616).
- Sepuluh audit penolakan cocok dengan sepuluh request ID respons; durasi
  nonnegatif dan `detect_ns + respond_ns = total_ns`.
- Tidak ada peer attacker. Client dengan key asli berhasil admission sebagai
  kontrol positif; setelahnya identitas/akun sementara dicabut/disabled.
- Akun, sertifikat dan key client utama dipertahankan; ping setelah cleanup PASS.
- Bukti privat: `state/deployment/metrics-2026-10-10/s01-response/response-metrics.json`.
  File hasil di attacker tercantum dalam laporan untuk pemulihan jika SSH terputus.
- Tidak ada password/token/body/sertifikat/signature/nonce pada event
  `admission_timing`. Timestamp/correlation ID bukan kredensial akses.

Angka ini tidak menggantikan [hasil S-03/S-04 versi 0.1.3](SECURITY_RESULTS_2026-10-09.md).
Benchmark performa tiga kondisi masih menunggu implementasi protokol dan keputusan
atas baseline WG tanpa admission; [rencananya tersedia](BENCHMARK_PLAN.md).
