"""2026-10-16 ET. Pinned existing native status/exception metadata only."""
import hashlib,json,re,signal,stat
from pathlib import Path
signal.alarm(20)
ROOT=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-abb598a4-t25-owned-swap-header3-public-v1')
ROWS=[{'relative': 'owned-swap-header3-public-v1-profile/leaf-swap.owner_correspondence.header.ready.left/frama-c.log', 'bytes': 39766, 'sha256': 'a65816183153aef0208a6344dd5438404287cad7a9e978c991cca977aef2c11c'}, {'relative': 'owned-swap-header3-public-v1-profile/leaf-swap.owner_correspondence.header.ready.other/frama-c.log', 'bytes': 42690, 'sha256': '00068b17c21a44a694dbe833ffad2dda6beda61d39293f60d11f77afdfd3f6fe'}, {'relative': 'owned-swap-header3-public-v1-profile/leaf-swap.owner_correspondence.header.ready.right/frama-c.log', 'bytes': 39855, 'sha256': '9b1193eea36a161d0584f00e7f333cca2c583b8b742e0e481770951c2f12f353'}]
report=[]
for row in ROWS:
 path=ROOT/row['relative'];before=path.lstat();assert stat.S_ISREG(before.st_mode)and before.st_size==row['bytes']and before.st_size<=1048576
 b=path.read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256']
 notices=[];all_matches=0
 for n,line in enumerate(b.splitlines(),1):
  if not re.search(rb'(?i)failed|unknown|timeout|exception|fatal|error|warning|unsupported|unbound|exit.?code|exit.?status',line):continue
  all_matches+=1
  # Diagnostic lines only: do not return formula/task/dump rows.
  text=line.decode(errors='replace').strip()
  if re.match(r'(?i)^(?:\[(?:wp|why3|kernel)[^\]]*\]|(?:fatal )?error|exception|warning|prover|process|exit|failure|timeout|unknown|\[DEBUG\])',text):
   notices.append({'line':n,'text':text[:512],'line_sha256':hashlib.sha256(line).hexdigest()})
  else:
   notices.append({'line':n,'unrecognized_diagnostic_shape':True,'status_words':sorted(set(w.decode().lower()for w in re.findall(rb'(?i)failed|unknown|timeout|exception|fatal|error|warning|unsupported|unbound',line))),'line_sha256':hashlib.sha256(line).hexdigest()})
  assert len(notices)<=80
 after=path.lstat();assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
 report.append({'relative':row['relative'],'bytes':len(b),'sha256':row['sha256'],'before_after_equal':True,'all_error_status_matching_lines':all_matches,'notices':notices})
out=json.dumps({'date':'2026-10-16 ET','scope':'Existing pinned status/exception log diagnostics only; no task/SMT source or prover execution. Unrecognized diagnostic lines retained by hash/status words only.','logs':report},sort_keys=True).encode();assert len(out)<=131072;print(out.decode())
