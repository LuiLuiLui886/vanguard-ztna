import urllib.request,time,json,hashlib
from pathlib import Path
B=Path('/var/lib/vanguard/media-20261117-r01');output=B/'receiver.jsonl'
def log(event,**data):
 with output.open('a') as f:f.write(json.dumps({'event':event,'utc':time.time(),'monotonic':time.monotonic(),**data})+'\n');f.flush()
total=0;last=0;start=time.monotonic();digest=hashlib.sha256()
try:
 with urllib.request.urlopen('http://10.8.0.1:8082/media.wav',timeout=4) as r:
  log('http_open',status=r.status,content_length=int(r.headers['Content-Length']))
  while chunk:=r.read(8192):
   total+=len(chunk);digest.update(chunk)
   if time.monotonic()-last>=1:log('receiving',bytes=total);last=time.monotonic()
  log('completed',bytes=total,sha256=digest.hexdigest())
except Exception as e:log('transfer_stopped',bytes=total,error=type(e).__name__,elapsed=time.monotonic()-start)
try:
 with urllib.request.urlopen('http://10.8.0.1:8082/media.wav',timeout=3) as r:log('reconnect',http=r.status,received=len(r.read(1)))
except Exception as e:log('reconnect_denied',error=type(e).__name__)
