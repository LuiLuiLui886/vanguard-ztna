#!/usr/bin/env python3
"""Create a private, offline TOTP setup page; never print its credentials or QR."""

import argparse
import base64
import html
import io
import json
import os
from pathlib import Path

import qrcode
import qrcode.image.svg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=Path("state/deployment"))
    args = parser.parse_args()
    os.umask(0o077)
    credentials = json.loads((args.state / "admin-onboarding.json").read_text())
    qr = qrcode.make(credentials["totp_uri"], image_factory=qrcode.image.svg.SvgPathImage)
    image = io.BytesIO()
    qr.save(image)
    encoded = base64.b64encode(image.getvalue()).decode()
    username, password, secret = (
        html.escape(credentials[field]) for field in ("username", "password", "totp_secret")
    )
    page = f"""<!doctype html>
<html lang="id"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'">
<title>Aktivasi admin VanGuard</title>
<style>
body{{font:17px/1.65 system-ui,sans-serif;background:#eef2f6;color:#142536;margin:0;padding:36px 20px}}
main{{max-width:720px;margin:auto;padding:32px;background:white;border-radius:16px}}
h1{{line-height:1.15}}code{{overflow-wrap:anywhere;background:#edf3f6;padding:3px 6px}}
a{{color:#075caf}}img{{display:block;width:300px;max-width:100%;height:auto;margin:20px auto}}
details{{padding:12px;background:#f3f6f9;border-radius:8px;margin:16px 0}}
</style><main><h1>Aktivasi admin VanGuard</h1>
<p>Halaman privat ini disimpan di laptopmu dan tidak memuat layanan dari internet.
QR serta kunci di bawah memberi akses untuk membuat kode login. Simpan untuk dirimu sendiri.</p>
<ol><li>Buka aplikasi authenticator di HP yang mendukung TOTP.</li>
<li>Pilih tambah akun, lalu pindai QR berikut.
<img src="data:image/svg+xml;base64,{encoded}" alt="QR aktivasi TOTP VanGuard">
<details><summary>Masukkan secara manual</summary>
Nama akun: VanGuard / {username}<br>Kunci: <code>{secret}</code><br>
Jenis: berbasis waktu (TOTP), SHA-1, 6 digit, periode 30 detik.</details></li>
<li>Buka <a href="https://192.168.100.40:5000" target="_blank" rel="noreferrer">dashboard VanGuard</a>
di Firefox laptop ini. Kelima VM harus menyala.</li>
<li>Username: <code>{username}</code>
<details><summary>Tampilkan password admin</summary><code>{password}</code></details>
Masukkan password dan kode enam digit terbaru dari HP. Kode yang sudah dipakai tidak
bisa dipakai lagi; tunggu kode berikutnya bila ingin login ulang.</li></ol>
<p>Jika kode ditolak, aktifkan tanggal dan waktu otomatis di HP.
Jika browser lain meminta trust, impor <a href="root.crt" download>Root CA lab</a>
melalui pengaturan sertifikat Authorities, untuk identifikasi website.</p>
<p>Setelah berhasil masuk, halaman ini dapat ditutup. Kredensial asli tetap ada dalam
<code>admin-onboarding.json</code>; halaman ini tidak mengganti akun atau kunci.</p>
</main></html>"""
    target = args.state / "aktivasi-admin.html"
    target.write_text(page)
    target.chmod(0o600)
    print(f"Private offline activation page saved: {target}")


if __name__ == "__main__":
    main()
