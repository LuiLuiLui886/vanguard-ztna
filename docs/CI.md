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
