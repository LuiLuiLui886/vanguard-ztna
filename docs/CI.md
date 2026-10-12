# Pengujian otomatis GitHub

Workflow [VanGuard CI](../.github/workflows/ci.yml) menjalankan pemeriksaan pada
push ke `main`, pull request, dan pemicu manual. Dua job memakai Ubuntu 22.04
dengan Python 3.10 dan 3.12. Hasil aktual tersedia pada
[halaman Actions](https://github.com/LuiLuiLui886/vanguard-ztna/actions).

Setiap job memasang aplikasi dengan `deploy/constraints.txt`, memeriksa dependensi,
Ruff dan sintaks shell, menjalankan suite pytest, lalu membuat wheel/arsip source
beserta checksum. JUnit dicoba diunggah juga ketika tes gagal. Paket hanya diunggah
setelah pengujian dan checksum lulus. Artefak disimpan 14 hari; unduh hasil yang
dibutuhkan untuk lampiran TA sebelum kedaluwarsa.

Runner menghasilkan CA, key dan database fixture sementara. Workflow tidak
mengakses lima VM, tidak memakai kredensial deployment dan tidak melakukan rollout.
Hasil CI membuktikan suite aplikasi/build; bukti handshake, firewall dan pemutusan
peer kernel tetap berasal dari lab dan dicatat terpisah pada checkpoint.

Action dipin ke SHA commit yang diverifikasi melalui repositori resmi GitHub.
Izin token hanya `contents: read`; credential checkout tidak dipertahankan.
Hanya JUnit dan paket yang diunggah, bukan direktori fixture/state. Repository
tetap private. Pengaturan ini mengikuti [panduan Python GitHub Actions](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).

## Membaca hasil dan melanjutkan run

```bash
state/tooling/github/cli/usr/bin/gh run list --workflow ci.yml --limit 5
state/tooling/github/cli/usr/bin/gh run view RUN_ID
state/tooling/github/cli/usr/bin/gh run view RUN_ID --log-failed
```

Status queued/in_progress/cancelled tidak berarti lulus. Jika job gagal, periksa
langkah pertama yang gagal dan log-nya sebelum mengubah kode. Push baru pada branch
yang sama membatalkan run lama yang masih berjalan. Pemicu manual tersedia melalui
Actions → VanGuard CI → Run workflow, atau `gh workflow run ci.yml`.

Build arsip harus memakai checkout bersih: `scripts/package_source.py` menolak
menimpa artefak versi yang sudah ada. Arsip lokal 0.1.2 terdahulu tetap dipertahankan;
artefak CI dikaitkan dengan commit/run masing-masing dan dapat memuat dokumentasi
yang lebih baru. Jangan menyalin state atau secret ke checkout untuk build.

## Hasil pertama — 8 Oktober 2026

[Run 37806541495](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/37806541495) pada commit `a254f1e` selesai **success**.
Python 3.10: 54 tes lulus dalam 41,722 detik; Python 3.12: 54 tes lulus dalam
41,456 detik. Tidak ada failure, error atau skip. Kedua job berhasil menjalankan
pemeriksaan source, build, checksum, serta upload JUnit dan paket.

Keempat artefak diunduh ke `state/deployment/ci-2026-10-08/artifacts/`. Checksum
paket diperiksa ulang; arsip source berisi 65 berkas, termasuk workflow, tanpa
state/secret. JUnit CI ini terpisah dari hasil suite lokal/guest sebelumnya.
Commit sesudah run yang hanya mencatat hasil memakai `[skip ci]`; tidak ada
perubahan workflow/kode pada commit catatan tersebut.

## Versi 0.1.3 — 9 Oktober 2026

[Run 37871996411](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/37871996411)
pada commit `0c56374` selesai **success**. Python 3.10: **76 PASS** dalam
83,127 detik; Python 3.12: **76 PASS** dalam 85,138 detik. Nol failure/error/skip.
Ruff, dependensi, shell, build dan checksum lulus pada kedua job.

Empat artefak diunduh ke `state/deployment/proposal-2026-10-09/ci-artifacts/`;
checksum kedua paket diperiksa ulang PASS. Hasil ini meliputi autentikasi akun
karyawan, binding/sesi perangkat, metadata dashboard serta regresi sebelumnya.
Hasil lab 0.1.3 dicatat terpisah pada [laporan implementasi](IMPLEMENTATION_REPORT.md).

## Instrumentasi S-03/S-04 — 9 Oktober 2026

[Run 37895229707](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/37895229707)
pada `f29ff67` **success**. Python 3.10: 90 PASS, 45,989 detik;
Python 3.12: 90 PASS, 78,689 detik. Nol failure/error/skip. Build, Ruff, dependensi,
shell dan checksum PASS. Empat artefak diunduh ke
`state/deployment/security-2026-10-09/ci-artifacts/`; checksum paket diverifikasi.

Tambahan 14 tes memeriksa integritas pcap, scope cleanup dan statistik evidence.
CI tidak menjalankan capture/tunnel/revoke pada VM; hasil live tercatat pada
[laporan eksperimen](SECURITY_RESULTS_2026-10-09.md). Versi aplikasi tetap 0.1.3;
arsip CI dikaitkan dengan commit ini, terpisah dari arsip lokal sebelum eksperimen.

## Instrumentasi 0.1.4 — validasi 9 Oktober, rollout 10 Oktober

[Run 37897878616](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/37897878616)
pada `c5b94af` **success**. Python 3.10: 100 PASS, 88,080 detik;
Python 3.12: 100 PASS, 86,419 detik; nol failure/error/skip. Pemeriksaan source,
dependensi, shell, build dan checksum PASS. Empat artefak diunduh ke
`state/deployment/metrics-2026-10-10/ci-artifacts/`; checksum diperiksa ulang.

Sepuluh tes tambahan mencakup korelasi/durasi penolakan, request concurrent,
kerahasiaan telemetry, pengecualian throttle serta validitas agregasi sampel.
Hasil live terpisah di [laporan MTTD/MTTR S-01](RESPONSE_METRICS_2026-10-10.md).

## Dashboard dan runner 0.1.5 — 12 Oktober 2026

[Run 38226313875](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/38226313875)
pada source `8eeffaa` **success**. Python 3.10: **132 PASS**, 81,549 detik;
Python 3.12: **132 PASS**, 97,714 detik; nol failure/error/skip. Ruff, dependensi,
sintaks shell, build, checksum dan upload artefak lulus pada kedua job.

Empat artefak diunduh ke `state/deployment/audit-2026-10-12/ci-artifacts/`.
Checksum paket unduhan PASS; masing-masing arsip source memuat 111 berkas tanpa
state/secrets. CI mencakup migrasi/audit/reason/bundle dashboard dan parser/cleanup
runner benchmark, tetapi tidak mengeksekusi VM lab. Hasil live tersedia pada
[laporan implementasi](IMPLEMENTATION_REPORT.md) dan [pilot](BENCHMARK_PILOT_2026-10-12.md).
Commit catatan sesudahnya memakai `[skip ci]` karena hanya mengubah dokumentasi.
