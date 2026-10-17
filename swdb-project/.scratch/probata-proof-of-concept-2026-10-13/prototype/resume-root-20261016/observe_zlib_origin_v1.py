"""2026-10-16 ET. Bounded metadata-only selected-Python zlib origin observation."""
from pathlib import Path
import _imp
import datetime
import hashlib
import importlib.util
import json
import os
import resource
import signal
import stat
import sys
import time
started=time.monotonic()
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(10,10))
signal.alarm(12)
assert sys.flags.isolated and sys.dont_write_bytecode and not sys.flags.optimize
assert sys.executable=='/data1/yanruj/venvs/swdb-test/bin/python'
assert 'zlib' not in sys.modules

def guard(event,args):
 if event in {'subprocess.Popen','os.system','os.fork','os.posix_spawn','os.exec','socket.connect'}:raise RuntimeError('metadata observation refuses child/network')
sys.addaudithook(guard)
def pin(p):
 p=Path(p);a=p.lstat();assert stat.S_ISREG(a.st_mode) and p.resolve(strict=True)==p
 d=p.read_bytes();z=p.lstat();assert (a.st_dev,a.st_ino,a.st_mode,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_mode,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
 return {'path':str(p),'bytes':len(d),'sha256':hashlib.sha256(d).hexdigest()}
spec=importlib.util.find_spec('zlib');assert spec is not None
builtin=_imp.is_builtin('zlib');before=None
if spec.origin not in {'built-in','frozen'}:before=pin(Path(spec.origin).resolve(strict=True))
import zlib
assert importlib.util.find_spec('zlib').origin==spec.origin
if before:assert pin(before['path'])==before
assert zlib.decompress(zlib.compress(b'probe-origin-only'))==b'probe-origin-only'
rows=[]
for row in Path('/proc/self/maps').read_text().splitlines():
 fields=row.split()
 if len(fields)>=6 and fields[-1].startswith('/') and ('libz.' in fields[-1] or '/zlib.' in fields[-1]):rows.append(fields[-1])
paths=sorted(set(rows));mapped=[pin(Path(n).resolve(strict=True)) for n in paths]
print(json.dumps({'created':'2026-10-16 ET','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'interpreter':sys.executable,'physical_interpreter':pin(Path(sys.executable).resolve(strict=True)),'flags':{'isolated':sys.flags.isolated,'optimize':sys.flags.optimize,'dont_write_bytecode':sys.dont_write_bytecode},'builtin':builtin,'spec_origin':spec.origin,'loader_type':type(spec.loader).__module__+'.'+type(spec.loader).__qualname__,'module_file':getattr(zlib,'__file__',None),'extension':before,'ZLIB_VERSION':zlib.ZLIB_VERSION,'ZLIB_RUNTIME_VERSION':zlib.ZLIB_RUNTIME_VERSION,'mapped_compression_objects':mapped,'wall_seconds':time.monotonic()-started,'caps':{'address_space_bytes':512*1024**2,'cpu_seconds':10,'alarm_seconds':12,'outer_seconds':15},'scope':'Metadata origin plus fixed20-byte roundtrip only, no compiler/native program/proof/AST capture or source acceptance.'},indent=2))
