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
