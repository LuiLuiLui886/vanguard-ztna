# Native wizard control-flow regression. Installer is a sentinel stub; no runtime,
# enrollment, CA, tunnel, or firewall changes. All state lives in an owned fixture.
param([Parameter(Mandatory=$true)][string]$Source,
      [Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference='Stop'
. (Join-Path $Source 'Common.ps1')
Assert-Administrator
$work=Join-Path $env:ProgramFiles ('VanGuardResumeTest-'+[guid]::NewGuid().ToString('N'))
Protect-Directory $work
$cases=New-Object System.Collections.Generic.List[object]
foreach($scenario in @('fresh','different-package','complete','interrupted','missing-state','missing-python')) {
    $folder=Join-Path $work $scenario;Protect-Directory $folder
    $package=Join-Path $folder 'package';Protect-Directory $package
    $app=Join-Path $folder 'app';Protect-Directory $app
    $data=Join-Path $folder 'data';Protect-Directory $data
    $common=Get-Content -Raw (Join-Path $Source 'Common.ps1')
    $common=$common.Replace('$AppRoot = Join-Path $env:ProgramFiles ''VanGuardEndpoint''',('$AppRoot = '''+$app+''''))
    $common=$common.Replace('$DataRoot = Join-Path $env:ProgramFiles ''VanGuardEndpointData''',('$DataRoot = '''+$data+''''))
    [IO.File]::WriteAllText((Join-Path $package 'Common.ps1'),$common)
    Copy-Item (Join-Path $Source 'Setup-VanGuard.ps1') $package
    $sentinel=Join-Path $folder 'repair-requested.txt'
    $stub='param([switch]$Elevated,[string]$ExpectedManifestSha256);[IO.File]::WriteAllText('''+$sentinel+''',''repair requested'');exit 89'
    [IO.File]::WriteAllText((Join-Path $package 'Install-VanGuard.ps1'),$stub)
    foreach($name in @('profile.json','provision.json','root.crt')){[IO.File]::WriteAllText((Join-Path $package $name),'fixture; never used for enrollment')}
    $files=@{};Get-ChildItem $package -File|ForEach-Object {$files[$_.Name]=(Get-FileHash $_.FullName).Hash.ToLowerInvariant()}
    [IO.File]::WriteAllText((Join-Path $package 'manifest.json'),(@{schema=1;target='cp313-win_amd64';signed=$false;files=$files}|ConvertTo-Json))
    $hash=(Get-FileHash (Join-Path $package 'manifest.json')).Hash.ToLowerInvariant()
    $release=$hash+'-'+('a'*32)
    if($scenario -eq 'different-package'){$release=('b'*64)+'-'+('a'*32)}
    if($scenario -ne 'fresh') {
        Write-State (Join-Path $app 'current.json') @{schema=1;release=$release}
        if($scenario -ne 'missing-state'){
            $setupRelease=if($scenario -eq 'interrupted'){$hash+'-'+('c'*32)}else{$release}
            $status=if($scenario -eq 'interrupted'){'IN_PROGRESS'}else{'INSTALLED'}
            Write-State (Join-Path $data 'setup-state.json') @{schema=1;status=$status;release=$setupRelease}
        }
        if($scenario -ne 'missing-python'){
            $scripts=Join-Path $app ('releases\'+$release+'\venv\Scripts');Protect-Directory $scripts
            [IO.File]::WriteAllText((Join-Path $scripts 'python.exe'),'sentinel; never executable')
        }
    }
    # Hash each pre-existing state file to ensure the decision never edits it.
    $before=@{};foreach($dir in @($app,$data)){Get-ChildItem $dir -Recurse -File|ForEach-Object {$before[$_.FullName]=(Get-FileHash $_.FullName).Hash}}
    $p=Start-Process powershell.exe -ArgumentList ('-NoProfile -ExecutionPolicy RemoteSigned -File "'+$package+'\Setup-VanGuard.ps1" -PrepareOnly') -RedirectStandardOutput (Join-Path $folder 'stdout.txt') -RedirectStandardError (Join-Path $folder 'stderr.txt') -Wait -PassThru
    $repair=Test-Path $sentinel
    $expected=($scenario -ne 'complete')
    # Complete fixture deliberately lacks installed launchers: it must reject at
    # that next guard, not reinstall or execute the fake Python sentinel.
    $ok=($repair -eq $expected -and (($expected -and $p.ExitCode -eq 89) -or (-not $expected -and $p.ExitCode -eq 1)))
    foreach($path in $before.Keys){if((Get-FileHash $path).Hash -ne $before[$path]){$ok=$false}}
    $cases.Add(@{case=$scenario;status=if($ok){'PASS'}else{'FAIL'};exit=$p.ExitCode;repair_requested=$repair;expected_repair=$expected})
}
[pscustomobject]@{environment='Windows native PowerShell; isolated paths and sentinel installer';cases=$cases;test_path=$work;full_runtime_repair='BELUM_TERUJI'}|ConvertTo-Json -Depth 6|Set-Content $Report -Encoding UTF8
if(@($cases|Where-Object status -eq 'FAIL').Count){throw 'Resume regression failed; fixture and logs preserved'}
