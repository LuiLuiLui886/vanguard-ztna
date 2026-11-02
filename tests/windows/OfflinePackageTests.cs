// Real Windows ACL/filesystem tests; synthetic public payload, never launches it.
using System;
using System.IO;
using System.IO.Compression;
using System.Collections.Generic;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Web.Script.Serialization;
internal static class OfflineTests
{
    static List<object> results = new List<object>();
    static byte[] Payload(string fault)
    {
        var content = new Dictionary<string, byte[]>();
        foreach (string name in OfflinePackage.Required) content[name] = Encoding.UTF8.GetBytes("public test fixture\n");
        var hashes = new Dictionary<string,string>();
        foreach (var pair in content) using (var stream = new MemoryStream(pair.Value)) hashes[pair.Key] = OfflinePackage.Hash(stream);
        if (fault == "hash") hashes["Common.ps1"] = new string('0',64);
        var manifest = new Dictionary<string,object> { {"schema",1}, {"target","cp313-win_amd64"}, {"signed",false}, {"files",hashes} };
        content["manifest.json"] = Encoding.UTF8.GetBytes(new JavaScriptSerializer().Serialize(manifest));
        if (fault == "manifest") content["manifest.json"] = Encoding.UTF8.GetBytes("{}");
        using (var bytes = new MemoryStream())
        {
            using (var zip = new ZipArchive(bytes,ZipArchiveMode.Create,true))
            {
                foreach (var pair in content) { var e=zip.CreateEntry(pair.Key); using(var s=e.Open()) s.Write(pair.Value,0,pair.Value.Length); }
                string bad = fault == "traversal" ? "../escape.ps1" : fault == "absolute" ? "C:/evil.ps1" :
                    fault == "backslash" ? "..\\evil.ps1" : fault == "case" ? "COMMON.ps1" : fault == "reserved" ? "CON.txt" :
                    fault == "extra" ? "unlisted.ps1" : fault == "symlink" ? "link.ps1" : null;
                if(bad!=null) {var e=zip.CreateEntry(bad);if(fault=="symlink")e.ExternalAttributes=unchecked((int)0xA1FF0000);using(var s=e.Open())s.WriteByte(65);}
            }
            return bytes.ToArray();
        }
    }
    static string Extract(byte[] payload,string root,string hash)
    { using(var stream=new MemoryStream(payload))return OfflinePackage.Extract(stream,hash,root); }
    static string Digest(byte[] payload) {using(var stream=new MemoryStream(payload))return OfflinePackage.Hash(stream);}
    static void Reject(Action action) {bool denied=false;try{action();}catch{denied=true;}if(!denied)throw new Exception("Expected rejection");}
    static int Main(string[] args)
    {
        string root=args[0], report=args[1];OfflinePackage.PrivateDirectory(root);
        try {
            byte[] good=Payload("");string hash=Digest(good);
            string cache=Extract(good,Path.Combine(root,"valid"),hash);
            DateTime before=File.GetLastWriteTimeUtc(Path.Combine(cache,"Common.ps1"));
            if(Extract(good,Path.Combine(root,"valid"),hash)!=cache || File.GetLastWriteTimeUtc(Path.Combine(cache,"Common.ps1"))!=before)throw new Exception("Resume rewrote cache");
            results.Add(new {test="valid_payload_and_identical_resume",status="PASS"});
            Reject(delegate{Extract(good,Path.Combine(root,"wrong-hash"),new string('0',64));});
            if(Directory.Exists(Path.Combine(root,"wrong-hash")))throw new Exception("Created files before payload validation");
            results.Add(new {test="wrong_payload_hash_before_write",status="PASS"});
            foreach(string fault in new[]{"traversal","absolute","backslash","case","reserved","extra","symlink","manifest","hash"}) {
                byte[] bad=Payload(fault);Reject(delegate{Extract(bad,Path.Combine(root,fault),Digest(bad));});
                results.Add(new {test="reject_"+fault,status="PASS"});
            }
            string changed=Path.Combine(cache,"Common.ps1");File.WriteAllText(changed,"tampered retained");
            Reject(delegate{Extract(good,Path.Combine(root,"valid"),hash);});
            if(File.ReadAllText(changed)!="tampered retained")throw new Exception("Tampered evidence overwritten");
            results.Add(new {test="tampered_cache_retained_and_rejected",status="PASS"});
            string unsafeRoot=Path.Combine(root,"unsafe");OfflinePackage.PrivateDirectory(unsafeRoot);
            var acl=Directory.GetAccessControl(unsafeRoot);acl.AddAccessRule(new FileSystemAccessRule(new SecurityIdentifier("S-1-5-32-545"),FileSystemRights.Modify,InheritanceFlags.ContainerInherit|InheritanceFlags.ObjectInherit,PropagationFlags.None,AccessControlType.Allow));Directory.SetAccessControl(unsafeRoot,acl);
            Reject(delegate{Extract(good,unsafeRoot,hash);});results.Add(new {test="users_writable_cache_rejected",status="PASS"});
        }
        catch(Exception ex){results.Add(new {test="runner",status="FAIL",reason=ex.Message});File.WriteAllText(report,new JavaScriptSerializer().Serialize(results));return 1;}
        File.WriteAllText(report,new JavaScriptSerializer().Serialize(results));return 0;
    }
}
