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
