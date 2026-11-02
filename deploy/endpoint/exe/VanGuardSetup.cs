// .NET Framework bootstrapper: embedded offline package, no network or credentials.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text.RegularExpressions;
using System.Threading;
using System.Web.Script.Serialization;

internal static class OfflinePackage
{
    internal static readonly string[] Required = { "Common.ps1", "Runtime.ps1", "Platform.ps1",
        "Install-VanGuard.bat", "Install-VanGuard.ps1", "Setup-VanGuard.bat", "Setup-VanGuard.ps1",
        "runtime-lock.json", "requirements.lock" };
    const long MaxFile = 128L * 1024 * 1024;
    const long MaxTotal = 256L * 1024 * 1024;
    static readonly Regex Name = new Regex(@"\A(?:(?:wheels|runtimes)/)?[a-zA-Z0-9_.-]+\z");
    static readonly Regex Digest = new Regex(@"\A[a-f0-9]{64}\z");
    static string InstallerSid = new NTAccount("NT SERVICE", "TrustedInstaller")
        .Translate(typeof(SecurityIdentifier)).Value;
    static bool Trusted(string sid) { return sid == "S-1-5-18" || sid == "S-1-5-32-544" || sid == InstallerSid; }
    internal static string Hash(Stream source)
    {
        using (var sha = SHA256.Create()) { return BitConverter.ToString(sha.ComputeHash(source)).Replace("-", "").ToLowerInvariant(); }
    }
    internal static string HashFile(string path) { using (var s = File.OpenRead(path)) { return Hash(s); } }
    internal static void SafePath(string path)
    {
        string current = Path.GetFullPath(path); bool leaf = true;
        while (current != null)
        {
            if (File.Exists(current) || Directory.Exists(current))
            {
                if ((File.GetAttributes(current) & FileAttributes.ReparsePoint) != 0) throw new IOException("Junction/reparse point ditolak.");
                FileSystemSecurity acl = Directory.Exists(current) ? (FileSystemSecurity)Directory.GetAccessControl(current) : File.GetAccessControl(current);
                if (!Trusted(acl.GetOwner(typeof(SecurityIdentifier)).Value)) throw new IOException("Pemilik path bukan sistem/administrator tepercaya.");
                foreach (FileSystemAccessRule rule in acl.GetAccessRules(true, true, typeof(SecurityIdentifier)))
                {
                    if ((rule.PropagationFlags & PropagationFlags.InheritOnly) != 0) continue;
                    int writes = 64 | 65536 | 262144 | 524288;
                    if (leaf) writes |= 2 | 4 | 16 | 256;
                    string sid = rule.IdentityReference.Value;
                    if (rule.AccessControlType == AccessControlType.Allow && (((int)rule.FileSystemRights) & writes) != 0
                        && !Trusted(sid) && sid != "S-1-3-0") throw new IOException("Path dapat diubah pengguna non-administrator.");
                }
            }
            current = Path.GetDirectoryName(current); leaf = false;
        }
    }
    internal static void PrivateDirectory(string path)
    {
        SafePath(path);
        if (!Directory.Exists(path))
        {
            var acl = new DirectorySecurity(); acl.SetAccessRuleProtection(true, false);
            acl.SetOwner(new SecurityIdentifier("S-1-5-32-544"));
            foreach (string sid in new[] { "S-1-5-18", "S-1-5-32-544" })
                acl.AddAccessRule(new FileSystemAccessRule(new SecurityIdentifier(sid), FileSystemRights.FullControl,
                    InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit, PropagationFlags.None, AccessControlType.Allow));
            Directory.CreateDirectory(path, acl);
        }
        SafePath(path);
    }
    static Dictionary<string, string> Manifest(byte[] bytes)
    {
        if (bytes.Length > 131072) throw new IOException("Manifest terlalu besar.");
        var parser = new JavaScriptSerializer { MaxJsonLength = 131072 };
        var m = parser.DeserializeObject(System.Text.Encoding.UTF8.GetString(bytes)) as Dictionary<string, object>;
        if (m == null || !m.ContainsKey("schema") || !(m["schema"] is int) || (int)m["schema"] != 1
            || !m.ContainsKey("target") || !Object.Equals(m["target"], "cp313-win_amd64")
            || !m.ContainsKey("signed") || !Object.Equals(m["signed"], false) || !m.ContainsKey("files"))
            throw new IOException("Manifest paket tidak sesuai.");
        var files = m["files"] as Dictionary<string, object>;
        if (files == null || files.Count > 127) throw new IOException("Daftar file tidak sesuai.");
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var pair in files)
        {
            string hash = pair.Value as string;
            if (!ValidName(pair.Key) || hash == null || !Digest.IsMatch(hash) || result.ContainsKey(pair.Key) || pair.Key == "manifest.json")
                throw new IOException("Path/hash paket tidak sesuai.");
            result.Add(pair.Key, hash);
        }
        foreach (string required in Required) if (!result.ContainsKey(required)) throw new IOException("Paket tidak lengkap.");
        int publicCount = 0;
        foreach (string p in new[] { "profile.json", "root.crt", "provision.json" }) if (result.ContainsKey(p)) publicCount++;
        if (publicCount != 0 && publicCount != 3) throw new IOException("Input per-device parsial ditolak.");
        return result;
    }
    static bool ValidName(string name)
    {
        if (!Name.IsMatch(name)) return false;
        foreach (string part in name.Split('/'))
        {
            if (part == "." || part == ".." || part.EndsWith(".")) return false;
            string stem = part.Split('.')[0].ToUpperInvariant();
            if (Regex.IsMatch(stem, @"\A(?:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])\z")) return false;
        }
        return true;
    }
    static byte[] ReadSmall(ZipArchiveEntry entry)
    {
        if (entry.Length > 131072) throw new IOException("Manifest terlalu besar.");
        using (var source = entry.Open()) using (var output = new MemoryStream()) { Copy(source, output, 131072); return output.ToArray(); }
    }
    static void Copy(Stream source, Stream target, long maximum)
    {
        byte[] buffer = new byte[65536]; long total = 0; int count;
        while ((count = source.Read(buffer, 0, buffer.Length)) != 0)
        { total += count; if (total > maximum) throw new IOException("Batas ukuran paket terlampaui."); target.Write(buffer, 0, count); }
    }
    static IEnumerable<string> Files(string directory)
    {
        SafePath(directory);
        foreach (string p in Directory.GetFiles(directory)) { SafePath(p); yield return p; }
        foreach (string child in Directory.GetDirectories(directory))
            foreach (string p in Files(child)) yield return p;
    }
    internal static void Verify(string directory, Dictionary<string, string> hashes, string manifestHash)
    {
        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (string path in Files(directory))
        {
            string name = path.Substring(directory.Length + 1).Replace('\\', '/');
            string expected;
            if (name == "manifest.json") expected = manifestHash;
            else if (!hashes.TryGetValue(name, out expected)) throw new IOException("Cache berisi file asing; inspeksi admin diperlukan.");
            if (!seen.Add(name) || HashFile(path) != expected) throw new IOException("Checksum cache gagal; file dipertahankan untuk inspeksi.");
        }
        if (seen.Count != hashes.Count + 1) throw new IOException("Cache tidak lengkap; inspeksi admin diperlukan.");
    }
    internal static string Extract(Stream payload, string expectedHash, string root)
    {
        if (!Digest.IsMatch(expectedHash) || !payload.CanSeek || payload.Length > MaxTotal || Hash(payload) != expectedHash)
            throw new IOException("Integritas payload EXE gagal.");
        payload.Position = 0;
        using (var archive = new ZipArchive(payload, ZipArchiveMode.Read, true))
        {
            if (archive.Entries.Count > 128) throw new IOException("Terlalu banyak file.");
            var entries = new Dictionary<string, ZipArchiveEntry>(StringComparer.OrdinalIgnoreCase); long total = 0;
            foreach (var entry in archive.Entries)
            {
                if (!ValidName(entry.FullName) || entries.ContainsKey(entry.FullName)
                    || ((entry.ExternalAttributes >> 16) & 0xF000) == 0xA000 || entry.Length > MaxFile)
                    throw new IOException("Path/tipe/ukuran arsip ditolak.");
                total += entry.Length; if (total > MaxTotal) throw new IOException("Paket terlalu besar.");
                entries.Add(entry.FullName, entry);
            }
            if (!entries.ContainsKey("manifest.json")) throw new IOException("Manifest tidak tersedia.");
            byte[] manifest = ReadSmall(entries["manifest.json"]); var hashes = Manifest(manifest);
            if (entries.Count != hashes.Count + 1) throw new IOException("Isi arsip berbeda dari manifest.");
            foreach (string name in hashes.Keys) if (!entries.ContainsKey(name)) throw new IOException("Anggota paket hilang.");
            string manifestHash; using (var stream = new MemoryStream(manifest)) manifestHash = Hash(stream);
            PrivateDirectory(root);
            string destination = Path.Combine(root, expectedHash); SafePath(destination);
            if (Directory.Exists(destination)) { Verify(destination, hashes, manifestHash); return destination; }
            string stage = Path.Combine(root, "pending-" + Guid.NewGuid().ToString("N")); PrivateDirectory(stage);
            foreach (var entry in entries.Values)
            {
                string path = Path.Combine(stage, entry.FullName.Replace('/', Path.DirectorySeparatorChar));
                PrivateDirectory(Path.GetDirectoryName(path)); SafePath(path);
                using (var source = entry.Open()) using (var output = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                { Copy(source, output, entry.Length); if (output.Length != entry.Length) throw new IOException("Ukuran ekstraksi berbeda."); output.Flush(true); }
                var fileAcl = File.GetAccessControl(path); fileAcl.SetOwner(new SecurityIdentifier("S-1-5-32-544")); File.SetAccessControl(path, fileAcl);
            }
            Verify(stage, hashes, manifestHash);
            Directory.Move(stage, destination); // Retry always rechecks every file; not a power-loss guarantee.
            Verify(destination, hashes, manifestHash); return destination;
        }
    }
}

internal static class VanGuardSetup
{
    const string PayloadHash = "@@PAYLOAD_SHA256@@";
    const string Mode = "@@MODE@@";
    [STAThread]
    static int Main(string[] args)
    {
        bool noPause = false, extractOnly = false, prepareOnly = false;
        int result = 1; Mutex mutex = null; bool owned = false;
        try
        {
            foreach (string arg in args)
            {
                if (arg == "/nopause") noPause = true;
                else if (arg == "/extract-only") extractOnly = true;
                else if (arg == "/prepare-only") prepareOnly = true;
                else throw new ArgumentException("Opsi tidak dikenal. Gunakan /extract-only, /prepare-only atau /nopause.");
            }
            if (!Environment.Is64BitProcess || !new WindowsPrincipal(WindowsIdentity.GetCurrent()).IsInRole(WindowsBuiltInRole.Administrator))
                throw new IOException("Windows x64 dan persetujuan administrator diperlukan.");
            mutex = new Mutex(false, @"Global\VanGuardOfflineBootstrap");
            try { owned = mutex.WaitOne(0); } catch (AbandonedMutexException) { owned = true; }
            if (!owned) throw new IOException("Installer EXE lain masih berjalan.");
            Console.WriteLine("VanGuard - installer offline Windows 10/11");
            string directory;
            using (var payload = Assembly.GetExecutingAssembly().GetManifestResourceStream("VanGuard.Payload.zip"))
            {
                if (payload == null) throw new IOException("Payload EXE tidak tersedia.");
                directory = OfflinePackage.Extract(payload, PayloadHash,
                    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "VanGuardPackages"));
            }
            Console.WriteLine("Paket terverifikasi: " + directory);
            bool perDevice = File.Exists(Path.Combine(directory, "provision.json"));
            if (perDevice != (Mode == "device")) throw new IOException("Mode EXE berbeda dari payload.");
            if (extractOnly) { Console.WriteLine("Ekstraksi selesai; belum melakukan instalasi/admission."); result = 0; }
            else
            {
                if (!perDevice) Console.WriteLine("Paket umum: memasang Python/WireGuard/aplikasi. Profil dan pendaftaran masih perlu disiapkan admin; belum memberi akses VPN.");
                string bat = perDevice ? "Setup-VanGuard.bat" : "Install-VanGuard.bat";
                var start = new ProcessStartInfo(Path.Combine(Environment.SystemDirectory, "cmd.exe"),
                    "/d /s /c \"\"" + Path.Combine(directory, bat) + "\" /nopause" + (perDevice && prepareOnly ? " /prepare-only" : "") + "\"");
                start.WorkingDirectory = directory; start.UseShellExecute = false;
                using (var process = Process.Start(start)) { process.WaitForExit(); result = process.ExitCode; }
                if (!perDevice && result == 0) Console.WriteLine("Aplikasi terpasang. Admin: siapkan paket per-device sesuai manual. Launcher: " +
                    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), @"VanGuardEndpoint\VanGuard.bat"));
            }
        }
        catch (Exception ex) { Console.Error.WriteLine("Setup belum selesai. File/bukti dipertahankan. " + ex.Message); result = 1; }
        finally { if (owned) mutex.ReleaseMutex(); if (mutex != null) mutex.Dispose(); }
        Console.WriteLine("Exit code: " + result);
        if (!noPause && !Console.IsInputRedirected) { Console.WriteLine("Tekan Enter untuk menutup."); Console.ReadLine(); }
        return result;
    }
}
