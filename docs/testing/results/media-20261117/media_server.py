import wave,math,struct,time,json
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
P=Path('/var/tmp/vanguard-media-20261117.wav')
with wave.open(str(P),'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000)
 block=b''.join(struct.pack('<h',int(3000*math.sin(2*math.pi*440*i/8000))) for i in range(8000))
 for _ in range(180):w.writeframesraw(block)
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path not in ['/media.wav','/control.wav']:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type','audio/wav');self.send_header('Content-Length',str(P.stat().st_size));self.end_headers()
  try:
   with P.open('rb') as f:
    while chunk:=f.read(8192):
     self.wfile.write(chunk);self.wfile.flush()
     if self.path=='/media.wav':time.sleep(.25)
  except (BrokenPipeError,ConnectionResetError):pass
 def log_message(self,*args):pass
ThreadingHTTPServer(('0.0.0.0',8082),Handler).serve_forever()
