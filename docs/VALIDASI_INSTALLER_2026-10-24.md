# Validasi installer Windows — 24 Oktober 2026

Status awal IN_PROGRESS. Jangan menganggap hasil source/CI sebagai hasil PC fisik.
Baseline source dcc1a85, pekerjaan pada branch endpoint, otorisasi VM/branch pada
jurnal24Oktober dan VANGUARD_CONTEXT. Paket aplikasi0.1.12 tidak mengubah admission.

| Temuan | Klasifikasi | Bukti/file | Dampak/prioritas | Kriteria selesai |
|---|---|---|---|---|
| Python/WireGuard tidak termasuk installer lama | Fitur belum tersedia/P1 | Install-VanGuard.ps1 lama meminta runtime/manual thumbprint, ZIP22Oktober tanpa EXE/MSI | Sulit memasang di PC baru | Paket lengkap dengan pin/signature, reuse dan install jika kosong; bukti native terpisah per jalur |
| Pesan installer lama hanya menyebut fase | Risiko desain/P2 | catch Install-VanGuard.ps1 menyembunyikan alasan | Operator tidak mengetahui tindakan pemulihan | Diagnosis aman tanpa credential dan exit code yang benar |
| Installer fisik hanya diperiksa helper CI | Perilaku belum diuji/P1 | checkpoint23Oktober; belum ada fresh installer run | Belum cukup bukti BAT berfungsi | Uji BAT langsung di VM dengan snapshot hash dan native report; PC fisik tetap terpisah |
| Empat branch dengan main lama | Risiko pengelolaan/P2 | main235df05 terpisah dari hardening/endpoint | Pengguna dapat mengambil source0.1.8 | Merge histori, default main terbaru, dua branch maksimal, tanpa kehilangan commit |

Backup: Git bundle --all valid sebelum konsolidasi; salinan disk Windows mati
melalui libvirt sedang dibuat, XML disimpan lokal. Tidak memulihkan CA/index/CRL.
Windows endpoint memakai Program Files; identitas utama ProgramData dipertahankan.

Baseline Linux:39PASS/1SKIP ACL Windows (2,23detik). Regresi kit/package setelah
perubahan12PASS. Runtime dari URL resmi Python/WireGuard; hash dicatat pada
runtime-lock.json, signature harus diverifikasi di guest sebelum eksekusi.
Rincian hasil akhir akan ditambahkan setelah runner selesai, bukan diperkirakan.

## Temuan native yang direproduksi

- BUG-WIN-POLICY-01/P1: seluruh scope Undefined, Windows default Restricted
  menolak PS1 sebelum body. BAT memakai RemoteSigned proses saja hanya bila
  semua scope Undefined; policy eksplisit tidak diubah. Native launcher default
  exit0, Restricted eksplisit exit1, policy persistent sebelum/sesudah identik.
- BUG-WIN-ACL-02/P1:4ACE Program Files gagal translasi nama→SID. Common.ps1
  sekarang membaca SID langsung melalui GetAccessRules; preview native PASS.
  Native guards5PASS: ACL benar, reject Users writable, junction, publisher salah,
  runtime hash salah. Tidak mengabaikan izin yang tidak dikenal.
- R4 harness cmd /c quoting gagal sebelum BAT; harness diperbaiki ke invocation
  native PowerShell. Bukan bug BAT; kedua bukti gagal disimpan.

Windows VM build26300/SecureBoot/TPM true, Python3.13.16/WireGuard1.1.1 reuse.
Python3.13.17/WireGuard1.1.1 bundled signature Valid dan hash sesuai pin. Ini
belum membuktikan jalur missing-runtime; tidak menamai reuse sebagai fresh runtime.
