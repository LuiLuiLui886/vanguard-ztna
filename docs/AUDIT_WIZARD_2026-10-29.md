# Audit bug wizard Windows — 29 Oktober 2026

Audit dimulai pada03f33c9 dengan worktree bersih. Fokus installer/resume Windows;
ini bukan audit ulang seluruh CA/server. Credential/identity tetap privat.

| ID | Klasifikasi | Lokasi dan bukti | Dampak/prioritas | Kriteria selesai |
|---|---|---|---|---|
| WIZ-RESUME-01 | Bug yang berhasil dibuktikan | Setup-VanGuard.ps1, blok reuse: current.json paket sama lalu Get-Installation melempar saat IN_PROGRESS/setup-state hilang/python.exe hilang; native3FAIL sebelum patch | P1: satu BAT tidak dapat meneruskan repair pada state tersebut | Memanggil installer tepercaya, mempertahankan guard dan data, runtime baru lengkap serta retry tidak memasang ulang |
| WIZ-INTERACTIVE-01 | Perilaku yang belum diuji | Setup-VanGuard.ps1/VanGuard.ps1 default UAC/login/connect; bukti sebelumnya menggunakan PrepareOnly dan fixture client | P1 sebelum distribusi luas | Alur operator penuh pada topologi yang sesuai dan PC fisik; BELUM_TERUJI |
| WIZ-POLICY-01 | Risiko desain/operasional | Install-VanGuard.ps1 menolak maintenance bila direktori internet-lockdown ada | Repair runtime saat managed policy aktif memerlukan recovery admin; P1 operasional | Guard tetap dipertahankan, operator mengikuti recovery terencana; bukan alasan membuka firewall otomatis |

Patch kecil mempertahankan validasi paket sebelum reuse. Jika runtime paket yang
sama belum lengkap, wizard memanggil installer terverifikasi. Installer tetap
memeriksa ownership, mutex, tunnel dan policy; tidak menghapus identitas/state
lama. current.json rusak/ambigu tetap membutuhkan inspeksi, bukan rekonstruksi
metadata sembarang. Python application/wheel0.1.14 tidak berubah.

Bukti aktual:

- Baseline Linux lokal55PASS163,42detik: provisioning, profil/bundle dan package.
- Windows10 native PowerShell dengan path terisolasi dan installer sentinel:
  sebelum patch3PASS/3FAIL; sesudah patch6PASS. Ini bukti kontrol alur wizard,
  bukan pemasangan runtime sungguhan. Fixture/state dan log awal disimpan.
- Regresi package sesudah patch6PASS0,06detik.
- Windows10 LTSC19044, installer/venv/paket offline nyata di root terisolasi:
  **7PASS**. Install awal menunggu approval; injeksi IN_PROGRESS sambil current
  menunjuk release lama diperbaiki menjadi release baru lengkap. Key/config/
  request dan release lama/parsial tetap. Retry berikutnya memakai runtime yang
  sama. Tidak ada tunnel/managed policy; hash state instalasi utama tetap.
- Percobaan runtime pertama FAIL karena path fixture terlalu panjang untuk
  ensurepip pada Windows tanpa Long Path. Root fixture dipendekkan setara produk;
  registry Windows tidak diubah. Log gagal dan direktori lama tetap disimpan.
- Poll SSH pernah timeout saat VM lambat; tidak dianggap kegagalan/sukses produk.
  Laporan final dan status task0 diperiksa, task fixture kemudian dihapus.
- Ruff, pip check dan diff whitespace PASS. Tidak mengklaim CI baru.


Bukti lokal `state/audit-wizard-20261029/`. Script regresi dapat ditinjau di
`tests/windows/setup_resume.ps1` dan `setup_resume_runtime.ps1`; test runtime
memerlukan Python/WireGuard yang sudah tersedia, schema1, dan root aplikasi/data
terisolasi. Injeksi state terputus tidak mewakili listrik mati atau fresh OS.

EXE offline dibahas sebagai kemungkinan kemasan di atas alur yang sama; EXE belum
dibuat. Persetujuan UAC, approval admin, login dan kunci yang dibuat di client
harus tetap dipertahankan pada kemasan apa pun.


Distribusi: template admin0.1.14-fix1 menyertakan patch script dan manual terbaru;
wheel Python/runtime tetap. Admin harus membuat paket per-device baru supaya
manifest mencakup script terbaru; jangan menukar satu PS1 dalam paket lama dan
melewati checksum. ZIP stabil0.1.12/main tetap. Tidak ada rollout ke instalasi
utama VM. Pengujian fix1 native Windows11, UAC/login interaktif penuh, fresh OS/
reboot3010, repair saat managed policy aktif, dan power-loss tetap BELUM_TERUJI.
State akhir: Windows10 running, enam VM lain off; fixture/private key uji lokal
retained tanpa penerbitan sertifikat. EXE belum dibuat; pembahasan kemasan tidak
mengubah arsitektur admission atau kewajiban login.
