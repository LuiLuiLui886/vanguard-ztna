# Native PowerShell function tests with explicit synthetic OS facts, not native OS coverage.
param([Parameter(Mandatory=$true)][string]$Platform)
$ErrorActionPreference='Stop'
. $Platform
$cases=@(
 @{build=19044;product=1;arch='AMD64';bits=$true;allowed=$true},
 @{build=19045;product=1;arch='AMD64';bits=$true;allowed=$true},
 @{build=22000;product=1;arch='AMD64';bits=$true;allowed=$true},
 @{build=26300;product=1;arch='AMD64';bits=$true;allowed=$true},
 @{build=19043;product=1;arch='AMD64';bits=$true;allowed=$false},
 @{build=20348;product=3;arch='AMD64';bits=$true;allowed=$false},
 @{build=26100;product=3;arch='AMD64';bits=$true;allowed=$false},
 @{build=19045;product=1;arch='x86';bits=$false;allowed=$false},
 @{build=26100;product=1;arch='ARM64';bits=$true;allowed=$false}
)
foreach ($case in $cases) {
 $os=[pscustomobject]@{Version=('10.0.'+$case.build);BuildNumber=$case.build;ProductType=$case.product}
 $accepted=$false
 try { Assert-SupportedWindows $os $case.bits $case.arch; $accepted=$true } catch {}
 if ($accepted -ne $case.allowed) { throw "Wrong OS gate decision: build $($case.build), arch $($case.arch), product $($case.product)" }
}
Write-Output "PASS: $($cases.Count) synthetic platform cases in native PowerShell"
