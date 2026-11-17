"""Real media receiver: native terminal output plus append-only JSONL evidence."""
import hashlib,json,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path
B=Path('/var/lib/vanguard/cli-20261118-r01')
logfile=B/'receiver.jsonl'
if logfile.exists():raise SystemExit('Evidence exists; refuse to overwrite or mix runs')
def emit(event,**values):
 row={'event':event,'utc':time.time(),'monotonic':time.monotonic(),**values}
 with logfile.open('a') as f:f.write(json.dumps(row)+'\n');f.flush()
 stamp=datetime.fromtimestamp(row['utc'],timezone.utc).isoformat(timespec='milliseconds')
 print(stamp+' | '+event.upper()+' | '+' '.join(f'{k}={v}' for k,v in values.items()),flush=True)
print('VanGuard CLI experiment: cli-20261118-r01 | VM-CLIENT',flush=True)
print('Resource: http://10.8.0.1:8082/media.wav | read timeout=4s',flush=True)
print('Receiver bytes are application bytes, not packet-level timing.',flush=True)
total=0;last=0;start=time.monotonic();digest=hashlib.sha256()
try:
 with urllib.request.urlopen('http://10.8.0.1:8082/media.wav',timeout=4) as r:
  emit('http_open',status=r.status,content_length=int(r.headers['Content-Length']))
  while chunk:=r.read(8192):
   total+=len(chunk);digest.update(chunk)
   if time.monotonic()-last>=1:
    emit('receiving',bytes=total);last=time.monotonic()
  emit('completed',bytes=total,sha256=digest.hexdigest())
except Exception as e:emit('transfer_stopped',bytes=total,error=type(e).__name__,elapsed_seconds=round(time.monotonic()-start,3))
try:
 with urllib.request.urlopen('http://10.8.0.1:8082/media.wav',timeout=3) as r:emit('reconnect',http=r.status,received=len(r.read(1)))
except Exception as e:emit('reconnect_denied',error=type(e).__name__)
print('Receiver finished. This is one trial; no latency average is calculated.',flush=True)
