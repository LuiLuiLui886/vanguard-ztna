# Sistem VanGuard

Untuk **endpoint Windows**, mulai dari [download installer](downloads/README.md)
dan [panduan instalasi → CSR → admin → login](docs/MODUL_PENGGUNAAN_VANGUARD.md).
Paket0.1.15 menyertakan Python/WireGuard dan wheel offline, tersedia pada branch
`feature/2026-10-22-physical-endpoints`. `main` belum menerima rilis ini.
Hasil tes aktual serta batas bukti ada pada [checkpoint](docs/CHECKPOINT.md).
Untuk pilot di kampus, bawa [satu dokumen persiapan dan pelaksanaan lapangan](docs/PERSIAPAN_UJI_LAPANGAN.md).
Perbaikan penyimpanan **CA0.1.17** tersedia di source dan sudah dipasang pada VM-CA;
server/admin serta installer Windows tetap0.1.15. Lihat [hasil perbaikan CA](docs/reports/PERBAIKAN_CA_IO_2026-11-03.md).

[Panduan ringkas admin dan pengguna](docs/MODUL_PENGGUNAAN_VANGUARD.md)
tersedia juga sebagai [HTML siap dibaca/dicetak](docs/MODUL_PENGGUNAAN_VANGUARD.html).
Modul mencakup pemasangan awal serta pemakaian Ubuntu dan Windows pada lab terpasang.
Materi generate root CA, CSR, sertifikat HTTPS/perangkat, CRL dan backup sudah
tersedia pada Bagian9 modul yang sama.

## Pembimbing

Proyek ini dikembangkan sebagai bagian dari Tugas Akhir dengan bimbingan
[@hesmi](https://github.com/hesmi).

Implementasi lab Tugas Akhir Zero Trust Network Access untuk **Ubuntu Server 22.04**.
Admission sertifikat dilakukan **sebelum** server menambahkan peer WireGuard.
Aturan utama tetap berada di [AGENTS.md](AGENTS.md) dan [VANGUARD_CONTEXT.md](VANGUARD_CONTEXT.md).

| VM | IP | Implementasi |
|---|---|---|
| CA | 192.168.100.10 | OpenSSL private CA, HTTPS API :8080 |
| SERVER | 192.168.100.20 | Registry SQLite, validator, HTTPS API :8081, daemon, WireGuard UDP :51820 |
| CLIENT | 192.168.100.30 | CLI Python, X.509 P-256 + pasangan kunci WireGuard X25519 independen |
| ADMIN | 192.168.100.40 | Dashboard Flask/Jinja2, SQLite, password + TOTP, HTTPS :5000 |
| ATTACKER | 192.168.100.50 | Skrip pengujian negatif terbatas pada lab |
| CLIENT-WINDOWS | 192.168.100.60 | Windows tambahan; enrollment, admission, handshake, ping dan cleanup teruji |

Server tunnel `10.8.0.1/24`; client `10.8.0.2/24`. Source/kernel WireGuard tidak diubah.
Client Windows tambahan memakai `10.8.0.4/32`; kelima Ubuntu tetap
dipertahankan. [Status/panduan Windows](docs/WINDOWS_CLIENT.md) membedakan tes
helper native, bukti tunnel guest15 Oktober, dan skenario yang masih belum diuji.

**[Buka satu flowchart lengkap sistem](docs/FLOWCHART_SISTEM_LENGKAP.md)** — backend/CA → installer → enrollment → admission → akses → logout/revoke → recovery dan audit.

## Peta repository

| Folder | Isi |
| --- | --- |
| [downloads/](downloads/) | Installer Windows terbaru; versi lama di [archive](downloads/archive/) |
| [docs/](docs/) | Manual dan indeks seluruh dokumentasi |
| [docs/progress/](docs/progress/) | Jurnal perubahan per tanggal |
| [docs/reports/](docs/reports/) | Audit, validasi dan hasil pengujian |
| [docs/proposal/](docs/proposal/) | Kesesuaian dan saran revisi proposal |
| [docs/history/](docs/history/) | Snapshot dan bukti historis |
| [vanguard/](vanguard/) | Source aplikasi |
| [deploy/](deploy/) | Installer, konfigurasi contoh dan unit layanan |
| [scripts/](scripts/) | Alat build, deployment dan verifikasi lab |
| [tests/](tests/) | Pengujian otomatis |

Dokumen untuk melanjutkan proyek: [checkpoint](docs/CHECKPOINT.md),
[handoff](LANJUTKAN_PROYEK.md), dan [keputusan arsitektur](VANGUARD_CONTEXT.md).
Manual tetap satu sumber; laporan serta jurnal dikelompokkan tanpa dihapus.

Uji lokal (tidak membutuhkan root atau mengubah jaringan host):

```bash
python3 -m venv .venv
.venv/bin/pip install -c deploy/constraints.txt -e '.[test]'
.venv/bin/python -m pytest -q
.venv/bin/ruff check vanguard tests scripts
```

Pada Ubuntu, paket `python3-venv` perlu dipasang lebih dahulu. Pengujian menggunakan
OpenSSL sungguhan dan adapter WireGuard dalam memori; handshake kernel memerlukan VM lab.
Tidak ada akun default, password default, private key, atau token deployment di repositori.
