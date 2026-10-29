# Native EXE resource, extraction, resume, and tamper tests. No installer/admission.
param([Parameter(Mandatory=$true)][string]$Exe,[Parameter(Mandatory=$true)][string]$Report)
$ErrorActionPreference='Stop'
$cases=New-Object System.Collections.Generic.List[object]
function Record([string]$Name){$cases.Add(@{case=$Name;status='PASS'})}
$work=Split-Path -Parent $Report
Add-Type -TypeDefinition @'
using System;using System.Runtime.InteropServices;using System.IO;
public static class ExeEvidence {
 [DllImport("kernel32",CharSet=CharSet.Unicode,SetLastError=true)]static extern IntPtr LoadLibraryEx(string p,IntPtr h,uint f);
 [DllImport("kernel32",SetLastError=true)]static extern IntPtr FindResource(IntPtr h,IntPtr n,IntPtr t);
 [DllImport("kernel32")]static extern IntPtr LoadResource(IntPtr h,IntPtr r);
 [DllImport("kernel32")]static extern IntPtr LockResource(IntPtr r);
 [DllImport("kernel32")]static extern uint SizeofResource(IntPtr h,IntPtr r);
 [DllImport("kernel32")]static extern bool FreeLibrary(IntPtr h);
 public static string Manifest(string path){var h=LoadLibraryEx(path,IntPtr.Zero,2);if(h==IntPtr.Zero)throw new Exception("PE load failed");try{var r=FindResource(h,(IntPtr)1,(IntPtr)24);if(r==IntPtr.Zero)throw new Exception("No manifest");return Marshal.PtrToStringAnsi(LockResource(LoadResource(h,r)),checked((int)SizeofResource(h,r)));}finally{FreeLibrary(h);}}
 public static void Tamper(string source,string target){var b=File.ReadAllBytes(source);for(int i=0;i<b.Length-64;i++){if(b[i]==80&&b[i+1]==75&&b[i+2]==3&&b[i+3]==4){int names=b[i+26]+256*b[i+27],extra=b[i+28]+256*b[i+29];if(names==13&&System.Text.Encoding.ASCII.GetString(b,i+30,13)=="manifest.json"){b[i+30+names+extra+10]^=1;using(var s=new FileStream(target,FileMode.CreateNew))s.Write(b,0,b.Length);return;}}}throw new Exception("Payload location not found");}
}
'@
function Run-Exe([string]$Path,[string]$Options,[string]$Name){
 $p=Start-Process $Path -ArgumentList $Options -RedirectStandardOutput (Join-Path $work ($Name+'.stdout')) -RedirectStandardError (Join-Path $work ($Name+'.stderr')) -Wait -PassThru
 return $p.ExitCode
}
try {
 [xml]$manifest=[ExeEvidence]::Manifest($Exe)
 $level=$manifest.SelectSingleNode("//*[local-name()='requestedExecutionLevel']").level
 if($level -ne 'requireAdministrator'){throw 'UAC level differs'};Record 'embedded_manifest_requires_administrator'
 if((Run-Exe $Exe '/extract-only /nopause' 'extract-first') -ne 0){throw 'EXE extraction failed'}
 Record 'native_exe_extracts_embedded_payload'
 $line=([IO.File]::ReadAllLines((Join-Path $work 'extract-first.stdout'))|Where-Object {$_ -like 'Paket terverifikasi: *'})
 $cache=$line.Substring('Paket terverifikasi: '.Length)
 $hash=(Get-FileHash (Join-Path $cache 'manifest.json')).Hash
 $stamp=(Get-Item (Join-Path $cache 'manifest.json')).LastWriteTimeUtc.Ticks
 if((Run-Exe $Exe '/extract-only /nopause' 'extract-resume') -ne 0 -or (Get-Item (Join-Path $cache 'manifest.json')).LastWriteTimeUtc.Ticks -ne $stamp){throw 'Resume re-extracted package'}
 Record 'resume_revalidates_without_rewriting'
 $bad=Join-Path $work 'tampered-payload.exe';[ExeEvidence]::Tamper($Exe,$bad)
 if((Run-Exe $bad '/extract-only /nopause' 'tampered') -ne 1 -or [IO.File]::ReadAllText((Join-Path $work 'tampered.stderr')) -notlike '*Integritas payload EXE gagal*'){throw 'Corrupt embedded payload not rejected'}
 if((Get-FileHash (Join-Path $cache 'manifest.json')).Hash -ne $hash){throw 'Corrupt run changed verified cache'}
 Record 'modified_embedded_payload_rejected_before_cache_change'
 if((Run-Exe $Exe '/nopause /unexpected' 'bad-option') -ne 1){throw 'Unexpected option accepted'};Record 'unknown_option_rejected'
 & sc.exe query 'WireGuardTunnel$vanguard-client' *> $null
 if($LASTEXITCODE -ne 1060){throw 'Tunnel exists or cannot be inspected'};Record 'extract_only_does_not_create_tunnel'
} catch {$cases.Add(@{case='runner';status='FAIL';reason=$_.Exception.Message});throw}
finally {[pscustomobject]@{environment='Windows native elevated process; genuine EXE';cases=$cases;uac_click_browser_motw='BELUM_TERUJI'}|ConvertTo-Json -Depth 5|Set-Content $Report -Encoding UTF8}
