# Real Windows filesystem + Python profile validation; no network, enrollment or private-key files.
param([Parameter(Mandatory=$true)][string]$Common,
      [Parameter(Mandatory=$true)][string]$Python,
      [Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference='Stop'
. $Common
Assert-Administrator
$work=Join-Path $env:ProgramFiles ('VanGuardConfigureTest-'+[guid]::NewGuid().ToString('N'))
Protect-Directory $work
$inputs=Join-Path $work 'inputs'
Protect-Directory $inputs
$fixture=@'
import base64, datetime, json, sys
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
p = Path(sys.argv[1])
key = ec.generate_private_key(ec.SECP256R1())
name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Disposable configuration test')])
now = datetime.datetime.now(datetime.timezone.utc)
cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=1))
        .not_valid_after(now+datetime.timedelta(days=1)).sign(key, hashes.SHA256()))
(p/'root.crt').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
profile = dict(schema=1, api_url='https://192.0.2.20:8081', wireguard_host='192.0.2.20',
               wireguard_port=51820, server_public_key=base64.b64encode(bytes(range(32))).decode(),
               root_sha256=cert.fingerprint(hashes.SHA256()).hex(), backend_network='192.168.100.0/24',
               tunnel_network='10.8.0.0/24', allowed_ips=['10.8.0.1/32'],
               resources=[dict(name='test',address='10.8.0.1',protocol='tcp',port=8082)])
(p/'profile.json').write_text(json.dumps(profile))
'@
[IO.File]::WriteAllText((Join-Path $work 'fixture.py'),$fixture)
Invoke-Checked $Python @((Join-Path $work 'fixture.py'),$inputs)
$source=Join-Path $inputs 'profile.json'
$root=Join-Path $inputs 'root.crt'
$public=Get-Content -Raw $source | ConvertFrom-Json
$cases=New-Object System.Collections.Generic.List[object]
function Record([string]$Name){$cases.Add(@{case=$Name;status='PASS'})}
function New-Config([string]$Name){$p=Join-Path $work $Name;Protect-Directory $p;return $p}
function Configure([string]$Config){Install-TrustedProfile $Python $source $root $public.root_sha256 $public.server_public_key $Config}
function Check-Pair([string]$Config){
 foreach($name in @('root.crt','profile.json')) {
  if((Get-FileHash (Join-Path $Config $name)).Hash -ne (Get-FileHash (Join-Path $inputs $name)).Hash){throw 'Published file mismatch'}
 }
}
function Must-Reject([scriptblock]$Body){$rejected=$false;try{& $Body}catch{$rejected=$true};if(-not $rejected){throw 'Expected rejection'}}
try {
 $config=New-Config 'fresh'
 Configure $config; Check-Pair $config; Record 'fresh_verified_pair'
 $time=(Get-Item (Join-Path $config 'profile.json')).LastWriteTimeUtc.Ticks
 Configure $config; Check-Pair $config
 if((Get-Item (Join-Path $config 'profile.json')).LastWriteTimeUtc.Ticks -ne $time){throw 'Identical retry overwrote config'}
 Record 'identical_retry_no_overwrite'
 foreach($existing in @('root.crt','profile.json')) {
  $config=New-Config ('partial-'+$existing)
  Copy-Item -LiteralPath (Join-Path $inputs $existing) -Destination (Join-Path $config $existing)
  Configure $config;Check-Pair $config;Record ('resume_with_'+$existing)
 }
 foreach($existing in @('root.crt','profile.json')) {
  $config=New-Config ('conflict-'+$existing)
  [IO.File]::WriteAllText((Join-Path $config $existing),'existing operator data; do not overwrite')
  $hash=(Get-FileHash (Join-Path $config $existing)).Hash
  Must-Reject {Configure $config}
  if((Get-FileHash (Join-Path $config $existing)).Hash -ne $hash){throw 'Conflicting file overwritten'}
  $other=if($existing -eq 'root.crt'){'profile.json'}else{'root.crt'}
  if(Test-Path (Join-Path $config $other)){throw 'Conflict detected after partial publication'}
  Record ('reject_conflicting_'+$existing+'_before_publication')
 }
 $config=New-Config 'wrong-fingerprint'
 Must-Reject {Install-TrustedProfile $Python $source $root ('0'*64) $public.server_public_key $config}
 if((Test-Path (Join-Path $config 'root.crt')) -or (Test-Path (Join-Path $config 'profile.json'))){throw 'Published untrusted inputs'}
 Record 'reject_wrong_admin_fingerprint'
 $config=New-Config 'wrong-server-key'
 Must-Reject {Install-TrustedProfile $Python $source $root $public.root_sha256 ('A'*43+'=') $config}
 if(Test-Path (Join-Path $config 'root.crt')){throw 'Published wrong server binding'}
 Record 'reject_wrong_admin_server_key'
 $config=New-Config 'invalid-root'
 $bad=Join-Path $inputs 'invalid.crt';[IO.File]::WriteAllText($bad,'invalid certificate')
 Must-Reject {Install-TrustedProfile $Python $source $bad $public.root_sha256 $public.server_public_key $config}
 if((Test-Path (Join-Path $config 'root.crt')) -or (Test-Path (Join-Path $config 'profile.json'))){throw 'Published invalid root'}
 Record 'reject_invalid_certificate_before_publication'
 $config=New-Config 'uppercase-fingerprint'
 Install-TrustedProfile $Python $source $root $public.root_sha256.ToUpperInvariant() $public.server_public_key $config
 Check-Pair $config;Record 'accept_hex_fingerprint_case'
} catch {$cases.Add(@{case='runner';status='FAIL';reason=$_.Exception.Message});throw}
finally {
 [pscustomobject]@{environment='Windows native filesystem and Python crypto';cases=$cases;test_path=$work;vpn='NOT_TESTED'} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Report -Encoding UTF8
}
