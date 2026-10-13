# VanGuard Project Instructions

Project: Sistem VanGuard
Purpose: Tugas Akhir implementasi Zero Trust Network Access
Platform: Ubuntu Server 22.04 services; additional Windows client in preparation

Before making any change:
1. Read `VANGUARD_CONTEXT.md`.
2. Treat the latest architecture decisions in that file as source of truth.
3. Do not modify WireGuard kernel/source code.
4. Preserve all five original Ubuntu nodes. User clarification on 13 October 2026
   authorizes one additional Windows client (six nodes total), not a replacement.
5. Read `LANJUTKAN_PROYEK.md` and `docs/CHECKPOINT.md` for the latest operational status.

## Required progress recording

The user requires a resumable record of every change. Before each related group of
changes, append the intended work to `docs/PROGRESS_YYYY-MM-DD.md`. After the work,
record affected files/VMs, actual validation results, remaining issues, and the next
step. Update `docs/CHECKPOINT.md` and `LANJUTKAN_PROYEK.md` before stopping. Mark
interrupted/in-progress work explicitly; never infer success from an incomplete log.
Keep secrets out of all progress documents. Preserve earlier evidence and backups.

## Local credential documentation

The user requires project usernames/passwords to be documented only on this
computer. Maintain the private inventory at
`/home/lui/VanGuard-Privat/KREDENSIAL_VANGUARD.md` and `kredensial.json`, outside
the repository (directory 0700, files 0600). Update it when operational credentials
change. Never commit credential values, TOTP seeds, tokens or private keys, even
to the private GitHub repository. If a password is unavailable and only a hash
remains, document that fact locally; do not invent it or reset it just to complete
the inventory. Public progress records may reference the location and validation
status only.

## Nodes

- VM-CA:       192.168.100.10
- VM-SERVER:   192.168.100.20
- VM-CLIENT:   192.168.100.30
- VM-ADMIN:    192.168.100.40
- VM-ATTACKER: 192.168.100.50
- VM-CLIENT-WINDOWS: 192.168.100.60 (additional client; installation in progress)

WireGuard:
- Server tunnel: 10.8.0.1/24
- Client tunnel: 10.8.0.2/24
- Windows client tunnel: 10.8.0.4/32; reserve 10.8.0.3 for temporary experiments
- UDP: 51820

## Security architecture

A device must pass certificate admission before becoming a live
WireGuard peer.

Admission checks:
1. X.509 signature against VanGuard Root CA
2. Certificate validity period
3. Current CRL
4. Revocation serial check
5. X.509 private-key proof-of-possession
6. Certificate-to-WireGuard-public-key registry binding

Only after successful admission may the server execute:

    wg set wg0 peer <pubkey> allowed-ips <tunnel_ip>/32

Do not add a live WireGuard peer merely during device registration.

## Components

CA:
- OpenSSL private CA
- API: 192.168.100.10:8080

Server:
- WireGuard
- Certificate validator
- VanGuard daemon
- API: 192.168.100.20:8081

Client:
- Python application
- X.509 certificate + independent WireGuard keypair

Admin:
- Flask/Jinja2 dashboard
- SQLite
- 2FA TOTP
- API: 192.168.100.40:5000
