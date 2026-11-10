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
docs/testing/RESPONSE_METRICS.md; they are distinct from network RTT, prior S-04 revocation
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
versus mock evidence must follow docs/CHECKPOINT.md and docs/reference/HARDENING_0.1.9.md.

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
Linux live matrix is recorded in docs/reports/VALIDASI_ROLLOUT_2026-10-20.md; Windows
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


Single admin manual and Windows10 validation authorization — 24 October 2026:
User requests one authoritative, complete admin manual and removal of overlapping
tutorials from the current GitHub tree, preserving history/evidence. Markdown is
the single source; HTML/package copies are generated from it. User also authorizes
an additional Windows10 test VM. Preserve the original six domains, use separate
blank disk/MAC/IP192.168.100.70 and credentials stored only in private inventory.
Do not replace Windows11 or reenroll primary identities. Test OS compatibility
separately from VPN lifecycle and from Windows security servicing status.


Windows10 native validation and single-manual completion — 25 October 2026:
Windows10 LTSC2021 Evaluation x64 build19044 installed on additional test node
.100.70, preserving all six originals. Native installer from absent runtimes:
9smoke/5guards/policy passed; final r3 ZIP reinstall/status/config preservation
passed. Windows11 build26300 final r3 passed preview/two reinstalls/status,
5guards and policy while primary identity hashes/runtime0.1.9 remained unchanged.
Windows11 retains its existing separate endpoint0.1.12; Python3.13.16 reused.
Windows10 has Python3.13.17/WG1.1.1; no VPN identity/admission was created.
One18chapter manual is the source for MD/HTML/package;14overlapping tutorials
and3old ZIPs leave the active tree, with Git history preserved. Native10 LTSC
is not evidence for Home/Pro22H2, Windows10 VPN, physical endpoints or UAC/MOTW.
Windows11 running, other six guests shut off; Windows10 setup media ejected,
credentials unchanged/private. See newest checkpoint for publication status.


Windows interrupted configuration recovery — 25 October 2026, evening:
Source/package307b86a corrects proven WIN-CONFIG-01: stage public profile/root,
validate administrator pins and crypto before publication, reject conflicting
existing files, and complete identical partial pairs without overwrite. Root-only
status reports incomplete/exit1. Two file renames are not a multi-file transaction;
physical power-loss/concurrent configure remain untested. No CA/identity/admission
change. Final fix1 BAT reinstall/status plus10configuration cases passed on both
Windows10LTSC19044 and Windows11build26300. Primary Windows11 identity hashes,
legacy runtime and all six original domain definitions remain unchanged. See
current checkpoint for actual CI results and publication; earlier r3 evidence is
retained as history. Windows11 running; Windows10/five Ubuntu shut off.


User constraint — 27 October 2026, internet access control design:
The user wants deployment without configuring each user's router; heterogeneous
home routers must not become an integration prerequisite. Central policy/admin
and internet gateway belong on Linux. This supersedes the earlier proposal to
require per-router WAN filtering, not the existing lab topology or six-check
admission. Server-only cannot control traffic that bypasses the server. Proposed
managed Windows agent with persistent endpoint enforcement plus a full-tunnel
Linux gateway remains NOT IMPLEMENTED/NOT TESTED; no live network changes are
authorized merely by discussing this design. Before agent/policy installation,
there is no control over the endpoint. Full local administrator tampering is
outside an unconditional guarantee. Reachable HTTPS/WireGuard services are still
required; the private lab IP is not publicly reachable by assumption. Preserve
client-generated keys, all VMs and current identities. See 27 October journal.


User implementation authorization — 27 October 2026:
“Coba lakukan” authorizes candidate managed Internet implementation and backed-up
Windows10 testing. Router configuration remains unchanged. Candidate0.1.13 uses
opt-in schema2, persistent Windows outbound enforcement and Linux nft per-identity
Internet grants bounded by employee session/lease. Temporary CA/namespace only;
production identities/services are not implicitly migrated. Native test failures
and corrections are in 27 October journal. This supersedes NOT IMPLEMENTED above
for candidate source only, not release/readiness claims. Follow latest checkpoint.

Native managed Internet candidate — 27 October 2026:
Windows10 testing showed OS updates can add outbound local allow rules despite
default block. Candidate uses owned Local GPO rules with local rule merging
disabled, preserving original local policy and copying enabled inbound rules.
Existing organizational/domain firewall policy is rejected, not overwritten.
Nine initial and six post-reboot native cases passed, including new local allow
injection. Detach disables the owned tunnel exception before adapter removal;
failed policy cleanup retains config after attempting tunnel shutdown. Native
admission, grant/default-deny, renewals, logout and reconnect passed. Active TCP
grant-removal passed; active TCP certificate-revocation timing remains unconfirmed
due to a failed fixture, although revoke/peer removal/fresh denial passed.
Temporary account/identity disabled, CA revocation retained, namespace transport
stopped and Windows policy explicitly recovered. Production not rolled out.
Source/package0.1.13 remains candidate; published stable ZIP0.1.12 unchanged.


Windows11 managed Internet evidence — 28 October 2026:
The same candidate0.1.13 r8 package passed native installation, nine initial
lockdown and six post-reboot cases on Windows11 build26300. Admission/handshake,
default-deny/granted TCP and fresh DNS, three renewals, grant removal during TCP,
logout/owner cleanup and reconnect passed. Real temporary-CA revocation reset
active TCP, removed the peer and rejected fresh admission403. A timeout-only
fixture assertion failed; independent review of the recorded reset/denial evidence
passed network-stop criteria, not a claimed rerun. Windows10's earlier incomplete
revocation-stream measurement remains unconfirmed. No product source changes.
Original config/identity hashes, legacy runtime, SecureBoot/TPM, VM definition and
110 inbound rules preserved; temporary policy recovered, account disabled and
certificate revoked. Test namespaces stopped, CA/history retained. Main/stable
ZIP unchanged; no general Windows edition/physical endpoint guarantee.


User choice and candidate setup — 28–29 October 2026:
Use one offline folder and one main Setup-VanGuard.bat entrypoint. Candidate0.1.14
orchestrates existing runtime installer, public pinned profile, local key creation,
public request export, validated administrator bundle import and employee login/
connect. Admin approval and six device checks remain required; no management token
or private key in provisioning package. Resume verifies files, preserves existing
keys and rejects conflicts. Template needs explicit per-device admin preparation;
never distribute the disposable lab profile as production configuration.
Windows11 BAT preparation/resume passed; see latest checkpoint for final connection,
cleanup, publication and untested interactive/Windows10/physical scenarios.


Windows10 setup evidence — 29 October 2026:
Candidate0.1.14 BAT preparation/import/resume passed18assertions on Windows10
LTSC19044. Native client admission/handshake, default-deny/grant TCP/freshDNS,
two renewals, logout/cleanup and reconnect passed. Temporary certificate1004
revocation stopped active TCP, removed the peer and rejected fresh admission403;
this closes the older Windows10 measurement gap, not the earlier failed log.
Original config/identity/firewall and VM definition restored/preserved; temporary
CA history retained and consistency checked, account disabled and fixture stopped.
Interactive UAC/default login-to-launcher path, fresh wizard install/reboot3010,
physical endpoints and wider builds remain untested. No product source change.


Wizard repair correction — 29 October 2026:
Installer revision0.1.14-fix1 fixes same-package reuse after interrupted reinstall.
An incomplete runtime now goes through the verified installer; ownership/tunnel/
managed-policy guards remain. Native Windows10 control-flow tests6PASS and actual
isolated venv installation/repair7PASS; original endpoint state retained. No CA
issuance, firewall change, main VM rollout or Python wheel change. Full interactive
UAC/login, Windows11 fix1, fresh OS and physical power loss remain untested. User
asked about EXE packaging; feasible with the same admission/key/login boundaries,
but no EXE has been built in this session. See checkpoint for publication status.


Offline EXE candidate — 29 October 2026:
The user explicitly requests EXE packaging. A .NET Framework x64 bootstrapper
embeds the existing0.1.14-fix1 offline package, requires administrator elevation,
checks payload/hash/paths/ACL/cache, and runs the original installer or per-device
wizard. Public template has no profile/allocation; per-device approval/employee
login and client-generated keys remain required. No admission or CA change.
Native Windows10:13extractor cases,6final bootstrap cases,6postflight cases PASS;
real existing-prerequisite installation exit0 and device resume exit20 verified.
Initial observer was interrupted by guest shutdown; separate postflight checked
backup hashes and actual installed runtime. Unsigned EXE and fresh OS/Windows11/
interactive UAC/login/power-loss limits remain. See latest checkpoint/report.
Four unused public ISO download fragments were relocated with verified hashes and
original-path symlinks to another local filesystem to recover host space; no
backup, full ISO or VM disk removed. Earlier EXE-not-built statements are history.


Qualification evidence — 30 October 2026:
Source307PASS/1SKIP Linux, live HTTPS30/30 and firewall40/40; native generic EXE
now additionally passed Windows11 installation/identity-preserving postflight.
Windows10/11 helpers/configuration/extractor/bootstrap checks passed; detailed
scopes and harness failures remain in UJI_KELAYAKAN_2026-10-30.md. Isolated
HTTPS/WireGuard/nft16-case run passed with a fresh client peer after startup
reconcile; this is not proof of automatic recovery for stale tunnel state.
Main Ubuntu client certificate expired24October and its session is expired;
fail-closed verified, no identity replaced. Primary services remain0.1.11;
managed Internet candidate not rolled out by this qualification. Host disk
capacity, physical endpoints, EXE schema2/UAC/fresh OS, power-loss CA and soak
remain acceptance gaps. Preserve original topology, keys and revocation history.
Single manual now includes a complete generic EXE walkthrough in14.0.1.1.


Authorized service package rollout — 30 October 2026 afternoon:
User explicitly requested checking and updating CA/server/admin. All three were
0.1.11 and now have0.1.14 after quiescent backups and source-wheel validation.
Initial post-start verifier wrongly included disposable CA transaction generations;
code-only recovery retained current CA/DB state. Corrected verifier retry passed
published identity/config hashes. No root recreation, state rollback, policy
activation or client changes. VANGUARD_CLIENT_PROFILE and VANGUARD_INTERNET_POLICY
remain unset; installing new code does not enable managed Internet by itself.
See latest checkpoint/journal for postflight and publication. Host free space is
critically limited; evidence and backups retained, diagnostic log compressed
losslessly with verified content hash. Seven domain definitions preserved.


Service rollout postflight — 31 October 2026:
CA/server/admin0.1.14 verified again after host reboot:27source files each,
pip check, preserved CA/config identities, database integrity and historical
rows passed. HTTPS30/30 and5authorization guards passed; CRL validation and
current-boot daemon heartbeat healthy. The previous30October20/30 HTTP200
sample remains evidence of an unconfirmed transient CRL/readiness issue, not
a claimed root-cause fix. No relaxed admission or stale-CRL fallback. Only
three service VMs running now; other four remain off after host reboot.
Managed Internet/profile environment configuration remains separate/unset;
package update alone does not activate gateway policy. See checkpoint/journals.

Operational evidence — 31 October 2026, deployed0.1.14 acceptance tests:
CA/server/admin0.1.14 passed real HTTPS admission, WireGuard handshake, explicit
application grants/default deny, active TCP removal, two automatic renewals,
scoped/idempotent logout and CA-only revocation using a disposable Ubuntu identity.
The test client used isolated0.1.14 source; primary installed client remains0.1.9
with expired certificate/session. Identity/configuration/history were preserved;
test account disabled, certificate revoked, resource policy restored, no live peers.
Linux isolated regression89PASS/1SKIP; Windows/EXE not rerun. Initial health sample
29/30HTTP200 included server readiness503 with CA unknown. Direct CA20/20 and
follow-up30/30 succeeded, but the original cause is unconfirmed, not fixed.
No product code or admission policy weakened. Runtime TOTP replay counter advances
on successful admin login and must not be treated as immutable history during
verification. See docs/reports/UJI_INTEGRASI_0.1.14_2026-10-31.md for harness failures and
scope. Four Ubuntu backend/client VMs running, other three off; host1.3GiB free,
managed internet/profile deployment still pending. Private evidence retained.

Readiness investigation — 31 October 2026, source candidate only:
Optional local `python -m vanguard.health ROLE --diagnose` now reports fixed
exception categories and per-check timing with the same six-second subprocess
budget. Public HTTP responses and admission remain unchanged. No raw exception,
URL or credential is exposed. Codes describe library exceptions, not proven
network phases. Health baseline16PASS; candidate26PASS; isolated source staging
on CA/server/admin36/36ready; deployed HTTPS30/30HTTP200. Installed0.1.14 health
module hashes remain unchanged. This is not a deployed package/installer update
or a confirmed fix for the earlier transient503. No issuance, state restoration,
restart or firewall changes; configuration and CA root/key/index/serial preserved.
See the acceptance report and manual7.3; evidence state/readiness-20261031/.

Response validation fixes — 31 October 2026, source/staging only:
Three bugs reproduced before fixes: malformed readiness child/dependency could
crash or falsely report ready; client login overwrote old sessions before response
validation and copied extra fields; malformed logout confirmation bypassed the
friendly unconfirmed-revocation error path. Health now validates role/check/status;
login validates username/token/future finite expiry before writing only session
fields; logout retains its token for retry on malformed confirmation. No change
to admission, HTTPS, binding or session scope. Baseline61PASS/1SKIP, pre-fix27FAIL
plus3FAIL/1PASS logout. Selected candidate89PASS/1SKIP; final session/logout23PASS
(overlapping suites). Staging3VM12/12ready, configurations/CA identity/index/serial
preserved. Installed services remain0.1.14 unchanged; Windows/EXE not rerun/rebuilt.
Installed postflight29/30HTTP200 had admin database unknown, distinct from earlier
server CA unknown. Direct admin DB30/30 and integrityOK, cause still unconfirmed.
Do not attribute historical503 to the malformed-response fixtures. Evidence in
state/bugcheck-20261031/ and acceptance report. Mockup canceled, no mockup files.

Documentation decision — 1 November 2026:
User requested a simpler, direct usage module. The single manual MD/HTML now
has10sections and is83% shorter: main Windows use first, per-device packaging,
managed internet and new backend/CA setup in separate optional sections.
Current links were updated; historical evidence/flowcharts/Git history preserved.
No product/VM/credential changes or ZIP/EXE rebuild. Embedded manuals in existing
packages remain older editions. Source fixes and deployment gaps remain as
recorded31October; documentation editing does not imply execution or rollout.


Release and operational update — 2 November 2026:
CA/server/admin upgraded0.1.14→0.1.15 with quiescent backups, source-wheel parity,
dependency and state verification. Ubuntu client upgraded0.1.9→0.1.15. Original
expired vm-client identity was revoked through the dashboard; its files remain.
Active primary is vm-client-20261102 at /var/lib/vanguard/client-20261102 via
/etc/systemd/system/vanguard-client.service.d/identity-20261102.conf. Both keys
were generated on the client; immutable replacement inherits old account/IP.
Password unchanged. Handshake and two automatic renewals passed. Do not reenroll
or restart the revoked old identity as a recovery method.

Main server now has empty/default-deny VANGUARD_INTERNET_POLICY at
/var/lib/vanguard/server/internet-policy.json, IPv4 forwarding and NAT on eth0.
Admin VANGUARD_CLIENT_PROFILE points to /etc/vanguard/endpoint-profile.json,
schema2 public lab profile. No permanent Internet grant was added. An exact-table
config recovery timer was prepared and canceled after fresh SSH/readiness
checks; no CA or database rollback. Gateway availability does not enable endpoint
lockdown or authorize unmanaged Internet access.

Full Linux348PASS/1SKIP; native final EXE identical on Windows10 build19044 and
Windows11 build26300: actual upgrade exit0,0.1.15/27source parity/pip check,
primary config/identity/firewall retained, no tunnel created. Installed runtime
prerequisites were reused; legacy files and releases retained. Not fresh OS/UAC.
Live installed0.1.15 HTTPS/WireGuard tests passed negative admission, application
policy/LAN denial, active TCP blocking, two renewals, scoped/idempotent logout,
and CA-only revoke (one peer-removal sample6.828s). Main gateway Linux /32 fixture
passed no-grant→grant→removal. Fixture cleaned, account disabled/cert revoked,
original policy bytes restored and primary client active. Postflight30/30HTTP,
root/key unchanged, all30old CRL revocations retained within32current entries.

Windows0.1.15 native main-gateway follow-up — 2–3 November 2026:
Windows10 build19044 passed122probes; Windows11 build26300 passed98probes.
Both passed two renewals, pre-certificate/pre-admission lockdown, Internet grant,
removal/regrant, explicit direct-LAN-route bypass denial, CA-only revocation,
403readmission and policy remaining blocked after disconnect. Single peer-removal
samples were10.056s and4.359s. Explicit local recovery restored original files and
firewall; fixture accounts disabled/certificates revoked/grants and tasks removed.
Windows11 originally had no ProgramFiles identity directory; preserve that absence
and the separate legacy ProgramData identity. Evidence under windows-managed-r2/.
These fixtures called installed client APIs directly; production launcher subnet
overlap guard stays intact. Do not count this as physical launcher/UAC coverage.
Persistent Internet TCP revocation, physicalLAN/Wi-Fi, interactiveUAC/MOTW/GPO,
freshOS, long-load and physical CA power-loss acceptance remain BELUM_TERUJI.
Earlier transient public egress/upstream failures remain unexplained; no host
firewall/router changes and no claim they were fixed. Failed evidence retained.

After host reboot3November, Ubuntu employee session was expired and fail-closed.
Owner was stopped, lock acquired, no tunnel verified, and only proven stale owned
files archived. Existing account login, handshake and automatic renewal passed;
primary identity hashes unchanged. Do not reenroll vm-client-20261102. Host now
reports15GiB RAM; VM definitions were not changed. Free disk about1.5GiB; retain
backups and obtain capacity before long tests. Six VMs running, attacker preserved
off. See docs/reports/VALIDASI_0.1.15_2026-11-02.md and latest checkpoint for final postflight
and publication. Main c8af46f merged previous work through13dbb18;0.1.15 is published
separately on the existing feature branch, never assume main has the same package.


CA storage update — 3 November 2026:
VM-CA now runs0.1.17; server/admin and Windows installer remain0.1.15. The old
seal serialized all file flushes under the CA lock; temporary-VM fixture confirmed
5.487s for the second generation. First0.1.16 parallel-fsync candidate was deployed
but still failed29/30 and25/30HTTPS; preserve those failures. Final0.1.17 uses
Linux>=5.8 syncfs for the private generation, verifies all members share its
filesystem, checks errors, and waits before directory barriers and commit. Older
platforms retain per-file fsync. Publication/recovery journal format, counters,
CRL freshness, admission and readiness budgets are unchanged. Never restore old
index/CRL or disable storage barriers to recover readiness.
Final tests:26CA durability/interruption/error/fallback cases plus74health/PKI/
admission cases passed. Selected100tests, not a new full suite or Windows test.
Two verified quiescent code/config/state backups are private under
state/ca-io-20261103/ and v2/. Only code rollback is allowed; no rollback was needed.
27installed source members and196state files verified before restart; CA invariant,
root/key/bindings/history retained. Final live postflight30/30HTTPS plus5/5fresh
CRLs; separate normal-load30/30HTTPS. All35revocations retained. Real admin
password/TOTP login, dashboard200, scoped logout passed; credentials remain local.
Host later rebooted; latest VM/display status is in checkpoint. Do not rerun
rollout scripts: finished milestones exist. See docs/reports/PERBAIKAN_CA_IO_2026-11-03.md.


Repository organization — 4 November 2026:
Documentation is grouped under docs/progress, reports, proposal, reference,
testing (including results XML), and history/checkpoints. The active checkpoint,
API, SECURITY, WINDOWS_CLIENT and single manual MD/HTML keep their existing paths.
New journals belong in docs/progress/PROGRESS_YYYY-MM-DD.md. Start at docs/README.md
or the root README. Older installers moved to downloads/archive with unchanged
bytes; latest 0.1.15 paths remain stable. No application/VM/security behavior was
changed by this organization. Released ZIP/EXE contents were not rebuilt.


Pre-field verification — 9–10 November 2026:
User flowchart commit ef14b07 was integrated without replacing their changes.
Keep CA0.1.17 and server/admin0.1.15: runtime changes since0.1.15 affect CA seal;
server's imported durable_write is AST-identical. All27installed source members
per VM match their release. No runtime rollout, identity reset or grant changes.
Full local Linux baseline:355pass/1skip (Windows ACL APIs),1010.63s; lint passed
with two test import-order fixes; README uses python -m pytest as CI does.
Initial boot samples13/30HTTPS on9Nov and28/30on10Nov retained; the latter had
transient database unknown. Root cause unproven, do not claim a startup fix.
Final10Nov11:53WIB postflight30/30HTTPS, all3services active, diagnostics ready.
Nov9read-only CA invariants/history35revocations, DB integrity and scoped admin
login/TOTP/logout passed. No new Windows native or physical endpoint acceptance.
Only CA/server/admin running, all7definitions preserved. Host not on pilot
Ethernet192.168.50.10; disk3.2GiBfree/99%used needs capacity before pilot backups.
Existing Windows identity expires14Nov13:16:28WIB; lease renewal cannot extend it.
See docs/reports/PRA_UJI_LAPANGAN_2026-11-09.md and latest checkpoint. Completed
suite/postflight must not be rerun merely to resume; do not run old finalize or
rollout scripts. Private evidence is under state/preflight-20261109/ and state/preflight-20261110/.

Pilot host correction — 10 November 2026 afternoon:
Current host Wi-Fi wlx76012dc00ec5 uses DHCP192.168.50.101/24 via router .50.1;
planned Ethernet192.168.50.10/24 is absent. All VM domains shut off in latest
observation. Pilot preflight from repository root BLOCKED (host_lan and3services
FAIL, bridge/forward flag PASS, firewall MANUAL, HTTPS/endpoint NOT_TESTED).
Libvirt NAT rules exist but observed FORWARD counters0, no endpoint forwarding
proof. Manual updated: check .10 availability/reservation, use Ethernet for
approved topology, start services, rerun preflight and verify traffic before
Windows route/lockdown. No host/firewall/VM/IP changes were made in this step.


Pilot Ethernet host update — 10 November 2026 15:04 WIB:
enp3s0 linked, initially DHCP192.168.50.102. Static manual profile now
192.168.50.10/24, gateway/DNS192.168.50.1; router ping2/2. Wi-Fi .50.101 kept.
Original profile/address/routes saved privately state/pilot-host-20261110/.
Preflight host_lan PASS, overall BLOCKED due three services off; firewall and
endpoint traffic untested. Router DHCP reservation/exclusion for .10 unverified;
check before physical client pilot. Do not infer backend readiness from host IP.


All-VM boot — 10 November 2026 15:24 WIB:
All7domains running. Five Ubuntu roles passed strict-host-key BatchMode SSH;
five interactive gnome-terminal SSH windows launched. Two Windows virt-viewer
processes running; visual appearance on user screen unconfirmed. No identity,
credential, disk or firewall changes. Host free disk2.6GiB (99% used), RAM31GiB.
HTTPS services not retested; running VM is not application readiness.


Cleanup — 10 November 2026:
Active checkpoint/handoff now summarize current state; full prior content is in
docs/history/checkpoints/*_2026-11-10_before_cleanup.md with rebased links.
Four dist extracted directories matched every ZIP member and were removed;
original ZIPs remain. Reproducible build/caches also removed:373files,51,780,579
logical bytes total. Unique artifacts, private state/backups, source, tests,
installers and all VMs retained. Manifest/result are state/cleanup-20261110/;
do not rerun cleanup.py. Six local kit tests passed; no VM acceptance retest.
Latest host disk480MiBfree/100%used: cleanup does not resolve capacity shortage.
