"""2026-10-16 ET. Pure byte reader for ELF dependency metadata; never loads targets."""
from pathlib import Path
import datetime,hashlib,json,os,struct,time
H=lambda b:hashlib.sha256(b).hexdigest()
def pin(path):
 p=Path(path);before=p.stat()
 with p.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 after=p.stat()
 if(before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):raise ValueError('unstable file')
 return {'path':str(p),'resolved':str(p.resolve()),'sha256':h,'bytes':before.st_size,'symlink':os.readlink(p)if p.is_symlink()else None}
def elf(path):
 with Path(path).open('rb')as stream:
  ident=stream.read(16)
  if ident[:4]!=b'\x7fELF':return {'ELF':False}
  if ident[4:6]!=b'\x02\x01':raise ValueError('expected ELF64LE '+str(path))
  hdr=struct.unpack('<HHIQQQIHHHHHH',stream.read(48));headers=[]
  for i in range(hdr[9]):stream.seek(hdr[4]+i*hdr[8]);headers.append(struct.unpack('<IIQQQQQQ',stream.read(56)))
  def read(off,size):stream.seek(off);return stream.read(size)
  def address(v):
   matches=[p[2]+v-p[3]for p in headers if p[0]==1 and p[3]<=v<p[3]+p[5]]
   if len(matches)!=1:raise ValueError('unmapped address')
   return matches[0]
  interp=[read(p[2],p[5]).rstrip(b'\0').decode()for p in headers if p[0]==3];dynamic=[]
  for p in headers:
   if p[0]==2:
    raw=read(p[2],p[5])
    for off in range(0,len(raw),16):
     tag,val=struct.unpack_from('<qQ',raw,off)
     if not tag:break
     dynamic.append((tag,val))
  strings=[v for t,v in dynamic if t==5]
  def string(index):
   stream.seek(address(strings[0])+index);data=bytearray()
   for _ in range(65536):
    b=stream.read(1)
    if b==b'\0':return data.decode()
    if not b:break
    data.extend(b)
   raise ValueError('unterminated dynamic string')
  return {'ELF':True,'class_bits':64,'machine':hdr[1],'interpreter':interp,'needed':[string(v)for t,v in dynamic if t==1],'rpath':[string(v)for t,v in dynamic if t==15],'runpath':[string(v)for t,v in dynamic if t==29]}
def main(cfg):
 started=time.monotonic();roots=list(dict.fromkeys(cfg['roots']));queue=[Path(p)for p in roots];closure={};unresolved=[];alternatives=[]
 search=[Path('/lib/x86_64-linux-gnu'),Path('/usr/lib/x86_64-linux-gnu'),Path('/lib64'),Path('/lib'),Path('/usr/lib')]
 while queue:
  p=queue.pop(0)
  if not p.is_file():unresolved.append({'missing':str(p)});continue
  resolved=str(p.resolve(strict=True))
  if resolved in closure:continue
  meta=elf(p);row={**pin(p),'elf':meta,'edges':[]};closure[resolved]=row
  for q in meta.get('interpreter',[]):row['edges'].append({'interpreter':q,'selected_static_candidate':str(Path(q).resolve())});queue.append(Path(q))
  for name in meta.get('needed',[]):
   extra=[Path(x.replace('${ORIGIN}',str(p.resolve().parent)).replace('$ORIGIN',str(p.resolve().parent)))for val in meta.get('rpath',[])+meta.get('runpath',[])for x in val.split(':')if x]
   choices=[]
   for q in [root/name for root in extra+search]:
    if q.is_file()and str(q.resolve())not in [str(x.resolve())for x in choices]:choices.append(q)
   if choices:
    row['edges'].append({'needed':name,'selected_static_candidate':str(choices[0].resolve())});queue.append(choices[0])
    if len(choices)>1:alternatives.append({'parent':str(p),'needed':name,'ordered_candidates':[str(q.resolve())for q in choices]})
   else:unresolved.append({'parent':str(p),'needed':name,'rpath':meta.get('rpath',[]),'runpath':meta.get('runpath',[])})
 config_paths=[Path('/etc/ld.so.cache'),Path('/etc/ld.so.conf'),*sorted(Path('/etc/ld.so.conf.d').glob('*'))]
 return {'created':'2026-10-16 ET','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'roots':roots,'static_elf_closure':closure,'loader_configuration':[pin(p)for p in config_paths if p.is_file()],'search_roots':[str(p)for p in search],'unresolved':unresolved,'multiple_static_candidates':alternatives,'wall_seconds':time.monotonic()-started,'scope':'Passive ELF64LE PT_INTERP/DT_NEEDED/RPATH/RUNPATH parsing and physical hashing. No ldd, loader, target executable, package import, compiler or version command executed. Ordered candidates under declared standard paths are not an attested dynamic loader trace. dlopen/locale/NSS/plugin and external subprocess selection remain explicit OS/loader/runtime TCB.','actual_loader_trace_observed':False}
if __name__=='__main__':print(json.dumps(main(CFG),sort_keys=True,indent=2))
