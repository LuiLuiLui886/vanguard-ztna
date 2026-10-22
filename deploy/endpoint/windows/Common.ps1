Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$AppRoot = Join-Path $env:ProgramFiles 'VanGuardEndpoint'
$DataRoot = Join-Path $env:ProgramFiles 'VanGuardEndpointData'
function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not ([Security.Principal.WindowsPrincipal]$identity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Jalankan melalui Run as administrator. Tidak ada perubahan yang dilakukan.'
    }
}
function Assert-SafePath([string]$Path) {
    $p = [IO.Path]::GetFullPath($Path)
    $installerAccount = New-Object Security.Principal.NTAccount('NT SERVICE\TrustedInstaller')
    $installerSid = $installerAccount.Translate([Security.Principal.SecurityIdentifier]).Value
    $leaf = $true
    while ($p) {
        if (Test-Path -LiteralPath $p) {
            $item = Get-Item -LiteralPath $p -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse point/junction ditolak.' }
            $acl = Get-Acl -LiteralPath $p
            foreach ($rule in $acl.Access) {
                $sid = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
                # WriteData/AddFile, AppendData/AddDirectory, WriteEA, DeleteChild,
                # WriteAttributes, Delete, WriteDACL, WriteOwner (exclude generic read).
                $writes = 64 -bor 65536 -bor 262144 -bor 524288
                if ($leaf) { $writes = $writes -bor 2 -bor 4 -bor 16 -bor 256 }
                if ($rule.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) { continue }
                if ($rule.AccessControlType -eq 'Allow' -and ([int]$rule.FileSystemRights -band $writes) -and
                    $sid -notin @('S-1-5-18','S-1-5-32-544','S-1-3-0') -and
                    $sid -ne $installerSid) { throw 'Path dapat ditulis akun non-administrator; gunakan direktori tepercaya.' }
            }
        }
        $parent = [IO.Directory]::GetParent($p)
        if ($null -eq $parent) { break }
        $p = $parent.FullName
        $leaf = $false
    }
}
function Protect-Directory([string]$Path) {
    Assert-SafePath $Path
    [IO.Directory]::CreateDirectory($Path) | Out-Null
    $acl = New-Object Security.AccessControl.DirectorySecurity
    $acl.SetAccessRuleProtection($true,$false)
    foreach ($sid in @('S-1-5-18','S-1-5-32-544')) {
        $rule = New-Object Security.AccessControl.FileSystemAccessRule(
            (New-Object Security.Principal.SecurityIdentifier($sid)), 'FullControl',
            'ContainerInherit,ObjectInherit','None','Allow')
        $acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $Path -AclObject $acl
}
function Invoke-Checked([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw 'Perintah gagal; lihat status langkah. Tidak mencatat argumen atau credential.' }
}
function Assert-NoTunnel {
    & sc.exe query 'WireGuardTunnel$vanguard-client' *> $null
    if ($LASTEXITCODE -ne 1060) { throw 'Tunnel ada/tidak dapat diperiksa. Disconnect dari proses pemilik terlebih dahulu; jangan hapus config.' }
    if (Test-Path -LiteralPath (Join-Path $DataRoot 'identity\.connection.json')) { throw 'Pemilik koneksi belum selesai cleanup.' }
}
function Write-State([string]$Path, $Value) {
    $temp = $Path + '.pending'
    $text = $Value | ConvertTo-Json -Depth 8
    [IO.File]::WriteAllText($temp, $text, (New-Object Text.UTF8Encoding($false)))
    if (Test-Path -LiteralPath $Path) { [IO.File]::Replace($temp,$Path,$Path+'.previous') }
    else { [IO.File]::Move($temp,$Path) }
}
function Get-Installation {
    Assert-SafePath $AppRoot
    $state = Get-Content -LiteralPath (Join-Path $AppRoot 'current.json') -Raw | ConvertFrom-Json
    if ($state.schema -ne 1 -or $state.release -notmatch '^[0-9a-f]{64}-[0-9a-f]{32}$') { throw 'State instalasi tidak valid.' }
    $setup = Get-Content -LiteralPath (Join-Path $DataRoot 'setup-state.json') -Raw | ConvertFrom-Json
    if ($setup.schema -ne 1 -or $setup.status -ne 'INSTALLED' -or $setup.release -ne $state.release) {
        throw 'Instalasi belum selesai atau state tidak cocok; jalankan repair sebelum menggunakan aplikasi.'
    }
    $python = Join-Path $AppRoot ('releases\'+$state.release+'\venv\Scripts\python.exe')
    Assert-SafePath $python
    if (-not (Test-Path -LiteralPath $python)) { throw 'Runtime tidak lengkap; jalankan repair.' }
    return $python
}
