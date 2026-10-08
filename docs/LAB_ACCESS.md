# Akses lab VanGuard

Lima VM Ubuntu Server 22.04 terpasang pada **KVM/libvirt** di workstation ini.
VM berjalan tanpa desktop guest dan dikelola melalui **Virtual Machine Manager**,
SSH, atau `virsh`. Virtual Machine Manager 4.1.0 dan virt-viewer 11.0 sudah dipasang
pada workstation.

Buka **Virtual Machine Manager** dari menu aplikasi Ubuntu, lalu pilih koneksi
**QEMU/KVM** (`qemu:///system`). Kelima VM berada pada koneksi tersebut. Tombol
Run dan Shut Down dapat digunakan untuk menyalakan atau mematikan VM secara normal.
VM menggunakan console serial; gunakan menu console serial atau SSH untuk terminal guest.

Untuk membuka GUI melalui terminal:

```bash
virt-manager --connect qemu:///system
```

| VM | Alamat | Fungsi |
|---|---|---|
| VM-CA | 192.168.100.10 | CA dan API HTTPS 8080 |
| VM-SERVER | 192.168.100.20 | Admission HTTPS 8081, daemon, WireGuard |
| VM-CLIENT | 192.168.100.30 | Client, tunnel 10.8.0.2 |
| VM-ADMIN | 192.168.100.40 | Dashboard HTTPS 5000 |
| VM-ATTACKER | 192.168.100.50 | Pengujian negatif lab |

## Melihat dan menyalakan VM

Jalankan sebagai user `lui` pada workstation:

```bash
virsh -c qemu:///system list --all
```

Jika status VM `shut off`, nyalakan VM tersebut, misalnya:

```bash
virsh -c qemu:///system start VM-CA
virsh -c qemu:///system start VM-SERVER
virsh -c qemu:///system start VM-CLIENT
virsh -c qemu:///system start VM-ADMIN
virsh -c qemu:///system start VM-ATTACKER
```

Autostart jaringan `vanguard` aktif; autostart kelima VM pada boot workstation
belum diaktifkan. Layanan VanGuard otomatis berjalan saat guest VM dinyalakan.
Tunggu proses boot dan admission client sebelum menguji ping.

## Masuk melalui SSH

```bash
ssh -F ~/.ssh/vanguard_lab_config 192.168.100.30
```

Ganti IP sesuai tabel. Konfigurasi tersebut menggunakan user `ubuntu`, SSH key lokal,
dan host key yang dipin saat provisioning. User `ubuntu` memiliki sudo di dalam VM.

## Dashboard

Buka <https://192.168.100.40:5000> dari workstation ini. Root CA untuk trust browser
ada di `state/deployment/root.crt`; impor sebagai CA lab pada browser yang digunakan.

Username, password acak, dan URI enrollment authenticator tersimpan dalam file privat:

```text
/home/lui/vanguard/state/deployment/admin-onboarding.json
```

Buka file tersebut secara lokal, lalu masukkan `totp_uri` atau `totp_secret` ke aplikasi
authenticator. Login memerlukan password dan kode TOTP enam digit. File mode 0600;
jangan salin isinya ke laporan atau percakapan. Kredensial tidak ditulis di dokumentasi.

## Memeriksa tunnel

Pada VM-CLIENT:

```bash
sudo systemctl status vanguard-client
ping -c 3 10.8.0.1
sudo wg show wg0
```

Pada VM-SERVER:

```bash
sudo systemctl is-active vanguard-server vanguard-daemon wg-quick@wg0
sudo wg show wg0
```

Gunakan `wg show` biasa untuk laporan; format `wg show ... dump` mengandung private key.
Lihat [checkpoint](CHECKPOINT.md) dan [laporan implementasi](IMPLEMENTATION_REPORT.md)
untuk hasil pengujian dan pekerjaan yang masih terbuka.
