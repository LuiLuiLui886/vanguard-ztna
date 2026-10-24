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

## Hasil penyelesaian native24 Oktober

Catatan IN_PROGRESS di atas merupakan tahap awal. Backup disk telah selesai;
volumenya terdaftar80GiB virtual/40,65GiB allocated dan header QCOW2 valid. Handle
exit code clone awal hilang saat interupsi, sehingga tidak dikarang. Salinan itu
berhasil diboot melalui overlay untuk tes runtime kosong. Ini bukti boot salinan,
bukan verifikasi penuh setiap blok backup atau simulasi kegagalan media.

| Kasus dan lingkungan | Hasil aktual | Batas bukti |
|---|---|---|
| Linux lokal, suite kit/package/client-platform |41PASS/1SKIP0,38detik; Ruff PASS | Skip API ACL Windows; bukan installer native |
| CI39998238177, commit2e6ec76 |SUCCESS; hasil JUnit terpisah di jurnal | Mendahului koreksi uninstall5aa6e9f; CI Windows hanya helper |
| Windows11 VM build26300, r4b, runtime lama tersedia |7kasus PASS: preview tanpa state, install BAT, status, tanpa key/tunnel, reinstall menjaga config, incomplete setup ditolak, repair | Uninstall run ini gagal; tidak menyebut seluruh run PASS |
| Native r6, koreksi uninstall final |3PASS: reinstall config lama, uninstall exit0/data+runtime terjaga, reinstall setelah uninstall | Paket0.1.12 endpoint terpisah dari client utama0.1.9 |
| Native guard r4 |5PASS: SID ACL asli; menolak Users-writable, junction, publisher salah meski signature valid, hash runtime salah | Bukan seluruh kombinasi ACL/domain policy |
| Native policy r6 |Default launcher exit0; Restricted eksplisit exit1; policy persistent identik | UAC interactive bukan bagian tes ini |
| Native r6 pada overlay dengan Python/WireGuard/endpoint absent |5PASS: precondition absent, BAT install exit0, Python3.13.17/WireGuard1.1.1, pip check/status, tanpa identitas/tunnel | Runtime sungguhan, bukan mock; sesi administrator; jaringan trust Windows tidak diputus |
| ZIP publik versus paket r6 |Identik;36anggota,20wheel,25file aplikasi cocok source; manifest/runtime pin/nested secret scan PASS | Checksum integritas, bukan audit keamanan independen |

Suite overlap di atas tidak dijumlahkan. Runtime reuse mempertahankan Python3.13.16
pada disk utama; auto-install3.13.17 dibuktikan di overlay. Kedua jalur memakai
WireGuard1.1.1. Package path mengandung spasi, tanda kurung dan ampersand untuk
memeriksa quoting aktual. SHA256 ZIP yang diuji/dipublikasikan:

```text
91b551183f1f197d7390e32b31ff4de3da33ef62261e73fba572784b05b396dd
```

## Penutupan bug dan kriteria selesai

| ID/kategori | File/fungsi, bukti dan dampak | Perbaikan/kriteria selesai aktual |
|---|---|---|
| BUG-WIN-POLICY-01 — bug terbukti/P1 | BAT memanggil PS1 saat default client Restricted; gagal sebelum body | Guard seluruh scope Undefined → RemoteSigned proses; native default lulus, policy eksplisit tetap ditolak dan persistent identik |
| BUG-WIN-ACL-02 — bug terbukti/P1 | Common.ps1 Assert-SafePath:4ACE Program Files gagal Translate nama→SID; memblokir path aman | GetAccessRules meminta SID langsung; native ACL benar diterima, ACL writable/reparse tetap ditolak |
| BUG-WIN-UNINSTALL-03 — bug terbukti/P1 | BAT uninstall berada dalam AppRoot yang dihapus; exit1 setelah PS selesai | Maintenance di DataRoot/tools yang dipertahankan; r6 uninstall exit0, config/runtime terjaga, reinstall lulus. Koreksi r5 blok CMD saja gagal dan tetap dicatat |
| Runtime terpadu — fitur sebelumnya belum tersedia/P1 | Runtime.ps1 Ensure-Runtimes; BAT lama memerlukan setup manual | Paket lengkap dengan pin dan Authenticode; native reuse dan missing-runtime lulus |
| UAC interaktif / PC fisik — perilaku belum diuji/P1 | Install-VanGuard.ps1 elevasi, routing/backend pada PC LAN/laptop Wi-Fi | BELUM_TERUJI; selesai setelah elevated/non-elevated/UAC cancel dan alur enrollment/VPN pada target asli dibuktikan |
| Distribusi unsigned/MOTW — risiko desain/P2 | Script lokal belum Authenticode; RemoteSigned dapat menolak ZIP browser | Tidak bypass/Unblock otomatis; admin perlu distribusi/signing sesuai kebijakan, lalu validasi target |

Runner missing-runtime pertama terkena batas panjang command line SSH sebelum
script berjalan; pemanggilan file runner memperbaikinya. Ini kegagalan harness,
bukan produk. Runner native reproducible tersedia di tests/windows/; jangan
menghapus runtime/identitas mesin aktif untuk memenuhi precondition tes.

## Pekerjaan di luar bukti installer

Enam pemeriksaan admission dan sesi karyawan tetap wajib. Uji ini tidak enroll,
login, menambah peer, mengubah CA/backend atau membuktikan jaringan pilot siap.
Lima Ubuntu tetap shut off sepanjang pengujian; tidak ada VM ketujuh. Primary
Windows disk dipertahankan; hasil pemulihan referensi XML dan hash akhir dicatat
pada checkpoint/jurnal. Overlay dan backup tetap tersedia lokal.

BELUM_TERUJI: PC LAN/laptop Wi-Fi fisik, UAC interaktif/cancel, GPO/MOTW distribusi,
installer restart-required1618/3010 pada runtime sungguhan, soak panjang, power-loss
media CA dan gap lama WIN-CLEANUP-02. Jangan menghapus konfigurasi tunnel bila
ownership/penghentian belum terkonfirmasi. Panduan endpoint lengkap tersedia pada
[SETUP_WINDOWS](MODUL_PENGGUNAAN_VANGUARD.md), termasuk perbedaan
inisialisasi Root CA pertama dengan penerbitan sertifikat komputer baru.

## Penutupan publikasi dan CI main

Commit52cfac9 dipush ke main+feature; hanya dua branch tersebut tersisa. Seluruh
histori main/hardening/fix tergabung, dua refs lama dihapus setelah verifikasi
ancestry. Unduhan ulang ZIP dari GitHub cocok byte/hash paket r6. Primary Windows
XML/disk kembali persis; hash identitas, Python3.13.16/WG1.1.1/client0.1.9 dan
SecureBoot/TPM sesuai snapshot sebelum tes. Lima Ubuntu tidak diubah/shut off;
Windows utama running tanpa tunnel uji.

CI [40072739273](https://github.com/LuiLuiLui886/vanguard-ztna/actions/runs/40072739273)
main52cfac9 SUCCESS, JUnit diunduh: Linux3.10 **268PASS/1SKIP272,198s**, Linux3.12
**268PASS/1SKIP289,868s**, Windows Server2022 helpers **28PASS/2SKIP0,333s**.
Parser PowerShell memeriksa source/runner termasuk missing-runtime. Ini bukti
CI kode final, berbeda dari runtime installers sungguhan di VM Windows11.
Commit penutup menyinkronkan docs saja; byte source/test/ZIP tidak berubah.
