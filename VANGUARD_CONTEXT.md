Register device
      ↓
CA certificate issued
      ↓
Store WG identity in registry
      ↓
Client /api/verify
      ↓
X.509 + CRL + proof-of-possession
      ↓
ACCEPT
      ↓
wg set peer
      ↓
WireGuard handshake

Operational decision — 8 October 2026:
CRL validation remains strict: lastUpdate <= actual validator time < nextUpdate.
If a freshly fetched, correctly signed CRL is ahead by at most one second, wait
once for that boundary and run all CRL checks again using actual local time.
Never accept it before lastUpdate, extend nextUpdate, or fall back to stale CRLs.
Larger clock skew and failed revalidation remain fail-closed. Recheck challenge
expiration after CRL/proof validation before adding a live peer.

User decision — 8 October 2026; implementation continued 9 October:
Proposal S-01 uses stolen EMPLOYEE credentials, not administrator credentials.
An employee login must never bypass any of the six device admission checks.
Version 0.1.3 adds local employee accounts separate from dashboard administrators,
immutable employee-to-device binding, and HTTPS login issuing an eight-hour session.
Only token hashes are stored at the server; client stores the token in a private
file and never stores the password. Challenge and verify require the same valid
employee session. Lease expiration cannot exceed session expiration. Disabled
accounts or expired sessions cause peer removal; renewals require fresh login
after session expiration. No default employee or bypass for legacy devices.
Upgrades must explicitly bind the existing client to a lab account before restart.
The eight-hour session is an implementation choice, not a measured proposal result.

Proposal metrics clarification — 9 October 2026:
The proposal explicitly defines MTTR as Mean Time to Respond, not recovery/repair,
and scopes MTTD/MTTR to stolen valid employee credentials on an untrusted device.
Version 0.1.4 adds request-local monotonic denial timing and server-generated
correlation IDs. Application detection/response boundaries are defined in
docs/RESPONSE_METRICS.md; they are distinct from network RTT, prior S-04 revocation
bounds, credential-theft onset and operational recovery. Timing records never
include passwords, sessions, bodies, certificate PEM, proof signatures or nonces.
This telemetry does not change any admission check or add an alternative peer path.

Proposal audit implementation — 12 October 2026:
Version 0.1.5 adds dashboard dependency liveness, structured administrator audit,
revocation reason/completion time, certificate validity and per-identity event history.
The onboarding bundle contains public certificates, a binding manifest and instructions;
never export/generate a device private key on the dashboard and never add a peer on download.
Certificate validity display is not admission authorization. One certificate per immutable
device identity remains; renewal, hardware attestation, Windows, owner notifications and
per-resource policy are not claimed implemented by these dashboard improvements.

Administrator activity records — 12 October 2026:
Version 0.1.6 displays audit timestamps in Asia/Jakarta WIB to seconds while
retaining Unix UTC source timestamps. Admin event labels/details are presented in
Indonesian; filtered activity is paginated and can be saved as a non-destructive
snapshot ZIP in the admin database. The ZIP includes CSV/JSON/manifest, SHA-256
integrity checks and no credential fields. Archives are protected by the dashboard
session and are not an immutable external ledger or resistant to VM root edits.

User topology clarification — 13 October 2026:
Add one Windows CLIENT alongside all five existing Ubuntu VMs; do not replace
VM-CLIENT. Target VM-CLIENT-WINDOWS uses LAN 192.168.100.60 and a separate identity
vm-client-windows with tunnel 10.8.0.4. The temporary experiment address 10.8.0.3
remains reserved. This explicitly extends the original topology to six nodes.
Windows installation and native client validation are in progress, not yet proven.
Both clients require employee binding and all six device admission checks.

Operational evidence — 15 October 2026:
The additional Windows client is installed and enrolled with its own employee
account and independent keys. Native admission, handshake, ICMP, fresh admission
and controlled cleanup passed; Ubuntu .2 and Windows .4 worked simultaneously.
Version 0.1.8 waits for Windows service deletion before deleting tunnel config;
failed confirmation preserves config. All five Ubuntu domain definitions remain
unchanged. Windows revocation and active-tunnel reboot are still unverified.

Source candidate decision — 19 October 2026 (0.1.9, not a VM rollout):
CA mutations use a private staging generation, fsynced commit manifest and
roll-forward publication under the existing lock. Interrupted uncommitted state
is retained as evidence; never restore older index/CRL, guess counters or recreate
the root on upgrade. Employee logout invalidates only the supplied session and
its owned challenge/lease; retries must not remove a newer session's lease.
Certificate replacement creates a new immutable identity after revoking the old
one; client-generated keys and old history remain intact. Lease renewal never
extends certificates. Readiness is bounded/read-only, separate from liveness.
An opt-in explicit resource policy gates internal-demo 10.8.0.1 TCP8082 before
established-flow acceptance; an empty policy denies access. This does not change
WireGuard or relax six-check admission/employee sessions. Deployment and native
versus mock evidence must follow docs/CHECKPOINT.md and docs/HARDENING_0.1.9.md.

Windows VM optimization — 19 October 2026:
The existing Windows domain now exposes hypervclock plus vpindex/synic/stimer.
Only clock/Hyper-V XML fields changed after a normal shutdown and XML backup;
UUID, disk, MAC, TPM/UEFI, RAM/vCPU, identities and all five Ubuntu definitions
are preserved. Native timing measurements improved; one subsequent full boot
reached authenticated SSH in27.49 seconds. This is not a general desktop/boot
performance guarantee or a VPN active-reboot test. Secure Boot/TPM and identity
hashes passed, and28 helper tests passed (2 POSIX-only skips) after the change.
The installed client remains0.1.8;0.1.9 was tested from isolated staging.

Operational rollout — 20 October 2026:
All five Ubuntu packages and the additional Windows client are now0.1.9.
Quiescent backups, isolated CA consistency/transaction checks and unchanged
primary identity hashes precede rollout. The CA root/index/serial were preserved;
no old index/CRL restoration or counter guessing was performed. The server now
enables the explicit TCP8082 application gate with default deny. Temporary
identity .3 is used sequentially, not either primary client identity.
Linux live matrix is recorded in docs/VALIDASI_ROLLOUT_2026-10-20.md; Windows
live work remains in progress until its final evidence/cleanup is recorded.
A Windows teardown timeout preserved config; verified operator recovery stopped
the exact service before confirming1060. Do not blindly delete leftover config.

Operational completion — 20 October 2026 evening:
The Linux and Windows real-VM lifecycle/resource matrices are complete, including
logout/renewal scope, natural lease expiry, production daemon watchdog, active
client reboot, active TCP revocation, immutable identity replacement and disabled
accounts. All disposable identities were revoked, test accounts disabled, grants
emptied and peers removed. The Windows test task/service/config and temporary
HTTP listener are absent. Primary identity hashes and all six inactive domain
definitions match their backups; Windows Secure Boot/TPM remain enabled.
CA/server/admin/Windows are running; Ubuntu client/attacker are shut off for RAM.
Readiness is not uniformly healthy: final samples observed transient503, traced
in30read-only probes to18ready and12nonblocking shared-lock conflicts. No invariant
or CRL validation failure appeared in those probes. Preserve unknown rather than
claiming success while the CA writer holds its lock. HEALTH-LOCK-01 requires
bounded retry/deadline/read-only validation before changing this behavior.
WIN-CLEANUP-02 immediate-interrupt service timeout and actual CA media power-loss
remain unresolved evidence limits. CI0695e03 passed205/1 on each Linux3.10/3.12
and28/2 Windows helpers; helper CI is separate from the real guest tunnel matrix.


Operational readiness update — 21 October 2026:
CA/server/admin have0.1.10 installed; Ubuntu client/attacker/Windows remain0.1.9.
Bounded shared-lock retry and parallel admin probes retain unknown503 on failure.
Postflight31HTTP200/2HTTP503 does not establish uniformly healthy readiness.
Candidate0.1.11 reduces redundant publication I/O without shrinking the manifest:
identical target inodes are retained and fsynced, changed files fsynced/renamed,
and all parent directories fsynced before removing the durable commit decision.
An interrupted committed generation still rolls forward; never restore old CA
state or guess counters. Targeted34tests passed and alternating isolated timings
improved from2.458–2.606 to1.165–1.201seconds. Full/CI/rollout remain pending at
this entry; see the newest checkpoint for completion evidence and installed versions.
No client enrollment, identities, WireGuard protocol or admission checks change.


Operational publication completion — 21 October 2026:
CA/server/admin now run0.1.11. Quiescent backups verified,23wheel members per
service matched,15primary/state hashes preserved, CA invariants and all six
VM definitions passed; no peers/resource grants remain. Local Linux218PASS/1SKIP,
CI39572681808 Linux3.10/3.12 each218PASS/1SKIP, Windows helpers28PASS/2SKIP.
HTTPS postflight still31HTTP200/2HTTP503 (admin server dependency), despite
maximum latency1.731seconds. Do not claim uniformly healthy readiness. Keep
unknown503 and investigate the remaining cause separately. Five Ubuntu VMs
run; Windows is shut off. Client/attacker/Windows packages remain0.1.9.


CA HTTPS capacity — 21 October 2026:
The CA unit from40c7f74 now uses one worker/eight threads; packages remain0.1.11
on CA/server/admin and0.1.9 on clients/attacker. Four busy handlers previously
blocked a fifth TLS handshake beyond the unchanged0.5second connect budget.
A real Gunicorn/TLS regression reproduced this before the unit-only fix. Local
16targeted tests passed; CI39575685564 passed219/1 on each Linux3.10/3.12 and
28/2 Windows helpers. Quiescent CA/unit backup, systemd verification, hashes,
CA invariants and all six domain definitions passed. HTTPS postflight93/93ready;
matched added diagnostic load120/120HTTPS and40/40server probes passed, versus
36/120and3/40failures before. Preserve these bounded evidence claims; no guarantee
of unlimited load or long soak. TLS/lock/deadlines/fail-closed are unchanged.
Five Ubuntu VMs run; Windows remains shut off. Remaining work is soak, physical
CA power-loss evidence and the Windows immediate-interrupt cleanup risk.


Physical endpoint preparation — 22 October 2026:
The user requested checking all GitHub repositories and executing their agent
prompts. Local GitHub account LuiLuiLui886 has five repositories/seven branches;
only VanGuard supplies an applicable master prompt. Main235df05 has the newest
CODEX_VANGUARD_MASTER_PROMPT.md; retain040dc21 hardening source instead of merging
older main0.1.8. Work branch feature/2026-10-22-physical-endpoints targets
ENDPOINT_WINDOWS. The newer specification explicitly allows local source/tests/
packaging only: no push, release publication or changes to active VMs, host/router
network or endpoints in this preparation task.

Approved pilot plan: dedicated router192.168.50.1/24; Linux VM host .50.10 via
Ethernet, physical Windows11 PC .50.20 LAN and laptop .50.30 Wi-Fi. All five
Ubuntu guests and the additional Windows guest remain on192.168.100.0/24.
Prefer endpoint route192.168.100.20/32 via host.50.10 with narrowly reviewed host/
libvirt/VM forwarding for HTTPS8081 and WG UDP51820. No CA/admin/LAN application
bypass. Tunnel10.8.0.0/24 remains fixed; .2/.3/.4 reserved, .5/.6 only proposed
pending registry allocation. Router/interface capabilities and host firewall
backend must be verified before application; do not assume a route fixes NAT.

Observed22 October: all six VMs shut off; enp2s0 NO-CARRIER, active host Wi-Fi
192.168.66.9/24 via .66.1, virbr-vg192.168.100.1/24 NAT, forwarding flag1. Privileged
firewall inspection unavailable noninteractively. No VM/network mutations made.
Existing installed versions are last-recorded0.1.11 services/0.1.9 clients, not
revalidated running services. Candidate source0.1.12 introduces one public profile
contract, checked enrollment import, configurable API/WG transport, scoped local
disconnect, explicit additional TLS hosts, generation-only pilot config/firewall,
and offline Windows installer/launcher sources. Keys still originate on clients;
registration/import/installation never grants access. Native Windows/physical
pilot/signing remain unverified; see ENDPOINT_WINDOWS_PILOT.md and newest checkpoint.


Real-world installation preparation — 22 October 2026, afternoon:
User explicitly requests installation steps and preparation, and confirms the
same dedicated-router/host/PC-LAN/laptop-WiFi topology. Prepare a single local
installation kit and actionable operator/user guide. This confirmation does not
mean the router/IPs or endpoint installation have already been applied. Preserve
all six VMs and client-side keys; keep the existing CA. The current host preflight
is BLOCKED (Ethernet .50.10 absent; CA/server/admin guests shut off). New read-only
checks must report manual/unknown/not-tested distinctly; never report production
ready from file hashes or domain state. Admin0.1.12 is needed for profiled bundles;
server0.1.11 already supplies the required admission/logout/resource APIs. Use
INSTALL_REALWORLD.md for backup, runtime verification, staged installation and
acceptance; native/physical tests and effective host firewall remain outstanding.
No live rollout or GitHub publication has been performed for this preparation.


Publication authorization — 23 October 2026:
The user explicitly requests pushing all accumulated updates. This supersedes
the preparation-only no-push restriction for publishing the current feature
branch source/tests/installer/documentation. Preserve main/hardening and do not
force-push, merge or roll out VMs/network/endpoints. Local credentials, private
state and ignored dist artifacts remain outside Git. Native/physical validation
limits still apply. See the23October journal and latest checkpoint for actual
remote verification; historical no-push entries describe earlier stages.


ZIP publication authorization — 23 October 2026:
The user additionally authorizes pushing the complete prepared ZIP kit so Windows
can obtain it through Git. Publish only the two verified docs-r2 archives under
 downloads/ with hashes and usage instructions. This supersedes the earlier
source-only artifact restriction; keep dist/state broadly ignored and preserve
credentials/keys/VM backups outside Git. The bytes remain the verified22October
snapshot, not a new installer build or native test. No live rollout or main merge.


Windows installer and repository consolidation authorization — 24 October 2026:
User explicitly requests bundled Python/WireGuard prerequisites, BAT fixes and
real testing in the existing Windows VM, plus a complete endpoint enrollment
and admin guide. Back up first; preserve the primary Windows identity/runtime
and all five Ubuntu nodes. This supersedes preparation-only VM restrictions for
these installer tests, not unrelated host/router changes. New computers generate
keys/CSR and obtain a certificate from the existing CA; never recreate that CA.
User also authorizes consolidating GitHub to one/two branches. Preserve history
with ordinary merges/backups; delete only fully integrated branch references.


Windows installer native completion and branch consolidation — 24 October 2026:
Bundled offline package r6 installs missing Python3.13.17/WireGuard1.1.1 and
VanGuard0.1.12 on a disposable overlay of the existing Windows VM (5native cases
passed). Existing-runtime path, SID ACL guards, process-only default policy and
corrected uninstall/reinstall also have separate native evidence. No enrollment,
CA mutation, peer or tunnel was created. Original Windows XML/disk restored
exactly; primary identity hashes/runtime0.1.9 and SecureBoot/TPM matched before.
The five Ubuntu nodes remain untouched/shut off. Overlay/backup are retained.
Source/artifact52cfac9 published to main and feature; old hardening/fix references
removed only after their full history was merged. Main is the default entrypoint,
feature/2026-10-22-physical-endpoints the second branch. GitHub ZIP bytes match
native-tested r6. UAC interactive, physical endpoints, MOTW/GPO distribution and
production readiness are not established by these tests; see current checkpoint.
