# Checkpoint historis — 24 September 2026


Saved at the user's request on **24 September 2026, 13:23 WIB (UTC+7)**.
All five VMs were confirmed running at save time. Application/test results below
refer to the completed verification earlier today; no new test run was performed
just to save progress. See [today's progress log](PROGRESS_2026-09-24.md).

## Current state

- KVM/libvirt and the verified Ubuntu Server 22.04 image are installed.
- All five persistent VMs are running: VM-CA `.10`, VM-SERVER `.20`, VM-CLIENT `.30`,
  VM-ADMIN `.40`, VM-ATTACKER `.50` on `192.168.100.0/24`.
- Virtual Machine Manager 4.1.0 and virt-viewer 11.0 are installed on the workstation.
  The GUI was opened and connected to `qemu:///system`; GUI autoconnect is enabled.
- The libvirt network `vanguard` autostarts. VM autostart remains disabled; start the
  existing VMs from the GUI after a workstation reboot. Do not provision duplicates.
- All deployment phases completed: install, configure, admin, start, enroll, negative_tests.
- CA, service TLS, separate random service tokens, administrator password/TOTP, and
  client identity are configured. Secrets remain in protected files, outside artifacts.
- CA, server API, daemon, admin dashboard, and client services are enabled and active.
- Main client `vm-client` is admitted: one live server peer, allowed IP `10.8.0.2/32`.
  Actual kernel WireGuard handshake and ping to `10.8.0.1` succeeded.
- Dashboard: <https://192.168.100.40:5000>. See [LAB_ACCESS.md](https://github.com/LuiLuiLui886/vanguard-ztna/blob/31c6981/docs/LAB_ACCESS.md).

## Fixes applied in this session

1. Reapplied the installer on every VM so the service account can traverse the venv.
2. Fixed the privileged CA existence check in `scripts/deploy_lab.py` for safe configure reruns.
3. Added peer snapshots around registration, and replaced secret-bearing WG dump output
   with ordinary `wg show` output.
4. Fixed client systemd shutdown using `KillMode=mixed` and `TimeoutStopSec=40` so
   `wg-quick down` completes. Applied the unit to VM-CLIENT; repeated restart tests pass.
5. Added `scripts/verify_lab.py` for bounded real-VM tests with a disposable identity.

## Verification

- 44 local tests pass; Ruff, pip check, and installer shell syntax pass.
- Ten live-lab checks pass: empty peers, registration-only, proof/binding/replay,
  API restart, kernel handshake/ping, CA outage, CA recovery, daemon stop, CA CRL
  revocation, and test-identity cleanup.
- Three attacker API negative checks pass (401/403/400).
- Dashboard CA trust, password/TOTP login, logout, missing CSRF, TOTP replay pass.
- Main client service restart passes.
- VM-SERVER reboot passes; automatic admission and tunnel ping recovered.
- Two disposable test identities remain revoked/disabled in the audit history.
  The first test attempt exposed the shutdown defect; the second run passed in full.

Private evidence is stored under `state/deployment/`; see
[IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) for details and test boundaries.
`admin-onboarding.json` contains credentials and TOTP enrollment; never publish its contents.

## Next work

- Investigate one transient automatic peer removal outside the test scenarios (audit ID 29).
  Readmission recovered automatically; subsequent ping passed and 40 CRL probes validated.
  The existing generic audit message does not establish the root cause; see the report.
- Configure and test the per-VM firewall matrix from `docs/DEPLOYMENT.md`.
- Complete additional TA evidence: real 300-second lease expiration, unknown peer removal,
  remaining PKI-negative fixtures on VMs, and reboot of other VMs/host.
- Operator imports the lab root CA into the browser and enrolls TOTP in an authenticator.

Do not rerun `create_lab.py`: VM disks, CA state, registry and keys already exist.
`verify_lab.py` requires an idle client and zero server peers; it is intended for a
planned test window before enrollment, not while the main client is connected.
The original pause from 22 September has been resolved.

## Resume next session

1. Read `AGENTS.md`, `VANGUARD_CONTEXT.md`, this checkpoint, and the implementation report.
2. Check existing VM status using `virsh -c qemu:///system list --all`; use Virtual
   Machine Manager to start any stopped lab VM. The user prefers GUI management.
3. Run `.venv/bin/python scripts/ssh_preflight.py state/lab/inventory.json` from
   `/home/lui/vanguard`, then inspect service health and the client tunnel.
4. Investigate the transient peer removal before expanding tests; preserve fail-closed
   admission and all six certificate checks. Then implement the documented firewall matrix.
5. Update this checkpoint with new evidence. Do not recreate the CA, replace existing
   keys/credentials, or rerun disposable-identity tests against an active client.

The user has received the access guide, but browser CA import and personal authenticator
enrollment have not been confirmed. Saving progress did not shut down or suspend any VM.
