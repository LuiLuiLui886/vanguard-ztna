"""Capture pixels from a real GNOME Terminal XWayland window, without rendering text."""
import os,sys,subprocess,re
os.environ['GDK_BACKEND']='x11'
import gi
gi.require_version('Gdk','3.0');gi.require_version('GdkX11','3.0')
from gi.repository import Gdk,GdkX11
name,path=sys.argv[1:]
listing=subprocess.check_output(['xwininfo','-root','-tree'],text=True)
hits=[int(m.group(1),16) for line in listing.splitlines() if (m:=re.search(r'(0x[0-9a-f]+) "'+re.escape(name)+r'"',line))]
assert len(hits)==1,(name,len(hits))
w=GdkX11.X11Window.foreign_new_for_display(Gdk.Display.get_default(),hits[0]);im=Gdk.pixbuf_get_from_window(w,0,0,w.get_width(),w.get_height());assert im
im.savev(path,'png',[],[])
print(f'Captured native window {hits[0]:#x}: {w.get_width()}x{w.get_height()}')
