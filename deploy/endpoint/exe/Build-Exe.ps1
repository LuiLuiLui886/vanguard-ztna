# Compile an offline EXE on Windows using the installed .NET Framework compiler.
# Input must be a complete package produced by scripts/build_endpoint_package.py.
param([Parameter(Mandatory=$true)][string]$Package,
      [Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Package=[IO.Path]::GetFullPath($Package).TrimEnd([IO.Path]::DirectorySeparatorChar);$Output=[IO.Path]::GetFullPath($Output)
if(Test-Path $Output){throw 'Output exists; preserve earlier build'}
if($Output.StartsWith($Package+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Keep output/build evidence outside the input package'}
if($Output -notlike '*.exe'){throw 'Output must end in .exe'}
$compiler=Join-Path $env:SystemRoot 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if(-not [Environment]::Is64BitOperatingSystem -or -not (Test-Path $compiler)){throw 'Windows x64 with .NET Framework compiler required'}
function No-Link([string]$Path){
    $p=[IO.Path]::GetFullPath($Path)
    while($p){if(Test-Path $p){if((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse point input/output refused'}};$p=[IO.Path]::GetDirectoryName($p)}
}
No-Link $Package;No-Link $Output;No-Link $PSScriptRoot
$manifestPath=Join-Path $Package 'manifest.json';No-Link $manifestPath
$m=Get-Content -Raw -LiteralPath $manifestPath|ConvertFrom-Json
if($m.schema -ne 1 -or $m.target -ne 'cp313-win_amd64' -or $m.signed -ne $false){throw 'Unsupported package manifest'}
$top=@('Common.ps1','Install-VanGuard.ps1','Install-VanGuard.bat','Internet-Lockdown.ps1',
 'Platform.ps1','Runtime.ps1','Setup-VanGuard.ps1','Setup-VanGuard.bat','Uninstall-VanGuard.ps1',
 'Uninstall-VanGuard.bat','VanGuard.ps1','VanGuard.bat','runtime-lock.json','requirements.lock',
 'README.md','MODUL_PENGGUNAAN_VANGUARD.html','profile.json','root.crt','provision.json')
$names=@($m.files.PSObject.Properties.Name)
if($names.Count -gt 127){throw 'Too many package files'}
foreach($name in $names){
    if($name -notin $top -and $name -notmatch '^(?:wheels/[a-zA-Z0-9_.-]+\.whl|runtimes/[a-zA-Z0-9_.-]+\.(?:exe|msi))$'){throw 'Unexpected package file; never bundle credentials or keys'}
    $p=Join-Path $Package $name;No-Link $p
    if($m.files.$name -notmatch '^[a-f0-9]{64}$' -or (Get-FileHash -LiteralPath $p).Hash.ToLowerInvariant() -cne $m.files.$name){throw 'Package hash mismatch'}
}
foreach($name in @('Common.ps1','Runtime.ps1','Platform.ps1','Install-VanGuard.bat','Install-VanGuard.ps1','Setup-VanGuard.bat','Setup-VanGuard.ps1','runtime-lock.json','requirements.lock')){if($name -notin $names){throw 'Required package member missing'}}
$actual=@(Get-ChildItem -LiteralPath $Package -Recurse -File -Force|ForEach-Object {No-Link $_.FullName;$_.FullName.Substring($Package.Length+1).Replace('\','/')})
if(@(Compare-Object ($names+@('manifest.json')|Sort-Object) ($actual|Sort-Object)).Count){throw 'Package contains extra or missing files'}
$public=@($names|Where-Object {$_ -in @('profile.json','root.crt','provision.json')})
if($public.Count -notin @(0,3)){throw 'Incomplete provisioning input'}
$mode=if($public.Count -eq 3){'device'}else{'template'}
if($mode -eq 'device'){
    $p=Get-Content -Raw (Join-Path $Package 'provision.json')|ConvertFrom-Json
    if(@(Compare-Object @('device_id','root_sha256','schema','server_public_key','tunnel_ip') @($p.PSObject.Properties.Name|Sort-Object)).Count){throw 'Provision contract contains unexpected fields'}
    $profile=Get-Content -Raw (Join-Path $Package 'profile.json')|ConvertFrom-Json
    $allowed=@('schema','api_url','wireguard_host','wireguard_port','server_public_key','root_sha256','backend_network','tunnel_network','allowed_ips','resources','internet')
    if(@($profile.PSObject.Properties.Name|Where-Object {$_ -notin $allowed}).Count){throw 'Profile contains unexpected fields'}
    $root=Get-Content -Raw (Join-Path $Package 'root.crt')
    if($root -cnotmatch '\A\s*-----BEGIN CERTIFICATE-----[A-Za-z0-9+/=\r\n]+-----END CERTIFICATE-----\s*\z'){throw 'Only one public CA certificate is allowed'}
}
$work=$Output+'.build'
if(Test-Path $work){throw 'Build evidence already exists; choose a new output'}
[IO.Directory]::CreateDirectory($work)|Out-Null
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=Join-Path $work 'payload.zip'
$archive=[IO.Compression.ZipFile]::Open($zip,[IO.Compression.ZipArchiveMode]::Create)
try {foreach($name in @('manifest.json')+$names){[IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive,(Join-Path $Package $name),$name,[IO.Compression.CompressionLevel]::Optimal)|Out-Null}}
finally {$archive.Dispose()}
$hash=(Get-FileHash $zip).Hash.ToLowerInvariant()
$source=(Get-Content -Raw (Join-Path $PSScriptRoot 'VanGuardSetup.cs')).Replace('@@PAYLOAD_SHA256@@',$hash).Replace('@@MODE@@',$mode)
$cs=Join-Path $work 'VanGuardSetup.cs';[IO.File]::WriteAllText($cs,$source)
& $compiler /nologo /target:exe /platform:x64 /optimize+ /debug- ('/out:'+$Output) ('/win32manifest:'+(Join-Path $PSScriptRoot 'app.manifest')) /reference:System.IO.Compression.dll /reference:System.IO.Compression.FileSystem.dll /reference:System.Web.Extensions.dll ('/resource:'+$zip+',VanGuard.Payload.zip') $cs
if($LASTEXITCODE -ne 0){throw 'EXE compile failed; build evidence retained'}
$result=@{schema=1;mode=$mode;sha256=(Get-FileHash $Output).Hash.ToLowerInvariant();payload_sha256=$hash;manifest_sha256=(Get-FileHash $manifestPath).Hash.ToLowerInvariant();signed=$false}
[IO.File]::WriteAllText($Output+'.json',($result|ConvertTo-Json))
Write-Host 'EXE built. Verify origin/SHA256 before distribution; code signing has not been applied.'
$result|ConvertTo-Json
