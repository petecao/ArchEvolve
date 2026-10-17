"""Fixed read-only public identity for the observed portal FUSE helper.
2026-10-08 ET. Protected child fields remain UNOBSERVED; no exclusion/admission.
"""
import datetime,hashlib,json,os,pathlib,stat,time,socket
P=pathlib.Path;UID=114316761;CHILD=1654291;PARENT=1654279;START=559081545;PSTART=559081538
started=time.monotonic();total=0
assert os.getuid()==os.geteuid()==UID and socket.gethostname().split('.')[0]=='mbit10'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p,cap=16*1024*1024):
 global total
 assert time.monotonic()-started<60
 with P(p).open('rb') as f:b=f.read(cap+1)
 total+=len(b);assert len(b)<=cap and total<=64*1024*1024
 return b
def stamp(s):return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}
def public(pid):
 p=P('/proc')/str(pid);a=read(p/'stat');v=a[a.rfind(b')')+2:].split();b=read(p/'status')
 fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in b.decode().splitlines() if ':' in line}
 return {'pid':pid,'start_ticks':int(v[19]),'name':fields['Name'],'ppid':int(fields['PPid']),'state':fields['State'].split()[0],'uids':list(map(int,fields['Uid'].split())),'gids':list(map(int,fields['Gid'].split())),'threads':int(fields['Threads']),'capability_hex':{k:fields[k] for k in ('CapInh','CapPrm','CapEff','CapBnd','CapAmb')},'status_sha256':sha(b),'stat_sha256':sha(a)}
def native(p):
 global total
 assert time.monotonic()-started<60
 p=P(p);assert p.is_absolute() and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents))
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and not s.st_mode&0o22
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 with os.fdopen(fd,'rb') as f:
  b=f.read(16*1024*1024+1);assert len(b)==s.st_size<=16*1024*1024 and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat())
 total+=len(b);assert total<=64*1024*1024
 return {'path':str(p),'bytes':len(b),'sha256':sha(b),'stat':stamp(s)}
c=public(CHILD);p=public(PARENT)
assert c['start_ticks']==START and c['ppid']==PARENT and c['uids']==[UID,0,0,0] and c['state']=='S' and c['threads']==1 and c['name']=='fusermount3'
assert p['start_ticks']==PSTART and p['name']=='xdg-document-po' and p['uids']==[UID]*4
cb=read(P('/proc')/str(CHILD)/'cmdline',16384);pb=read(P('/proc')/str(PARENT)/'cmdline',16384)
cv=cb.rstrip(b'\0').split(b'\0');pv=pb.rstrip(b'\0').split(b'\0')
assert cv and P(os.fsdecode(cv[0])).name=='fusermount3'
mount=P('/run/user')/str(UID)/'doc';allowed={b'-o',b'--',str(mount).encode()}
child_argv=[]
for value in cv:
 if P(os.fsdecode(value)).name=='fusermount3':child_argv.append({'kind':'executable','basename':'fusermount3'});continue
 if value in allowed:child_argv.append({'kind':'fixed_role_argument','value':os.fsdecode(value)});continue
 opts=value.split(b',')
 if all(x in (b'rw',b'nosuid',b'nodev',b'fsname=portal',b'auto_unmount',b'subtype=portal') for x in opts):child_argv.append({'kind':'fixed_portal_mount_options','value':os.fsdecode(value)});continue
 child_argv.append({'kind':'unreviewed_argument','bytes':len(value),'sha256':sha(value)})
parent_links={}
for key in ('cwd','root','exe'):
 target=os.readlink(P('/proc')/str(PARENT)/key);parent_links[key]={'target_sha256':sha(target.encode()),'bytes':len(target.encode()),'under_candidate_cleanup_namespace':target.startswith('/data1/yanruj/ArchEvolve-lanl-')}
native_parent=os.readlink(P('/proc')/str(PARENT)/'exe');assert native_parent=='/usr/libexec/xdg-document-portal'
natives=[native('/usr/bin/fusermount3'),native(native_parent)]
packages=[]
for block in read('/var/lib/dpkg/status',8*1024*1024).decode().split('\n\n'):
 fields={line.split(': ',1)[0]:line.split(': ',1)[1] for line in block.splitlines() if ': ' in line and not line.startswith(' ')}
 if fields.get('Package') in ('fuse3','libfuse3-3','libfuse3-3t64','xdg-desktop-portal'):
  packages.append({k:fields.get(k) for k in ('Package','Version','Status','Architecture')})
mount_rows=[]
for line in read(P('/proc')/str(PARENT)/'mountinfo',1024*1024).decode().splitlines():
 a,b=line.split(' - ',1);v=a.split();w=b.split()
 if v[4]==str(mount):mount_rows.append({'mount_id':v[0],'parent_mount_id':v[1],'device':v[2],'root':v[3],'mount_point':v[4],'mount_options':v[5],'optional_fields':v[6:],'filesystem':w[0],'source':w[1],'super_options':w[2]})
after_c=public(CHILD);after_p=public(PARENT)
for before,after in ((c,after_c),(p,after_p)):
 assert all(before[k]==after[k] for k in ('pid','start_ticks','name','ppid','uids','gids','state','threads','capability_hex'))
assert read(P('/proc')/str(CHILD)/'cmdline',16384)==cb and read(P('/proc')/str(PARENT)/'cmdline',16384)==pb
print(json.dumps({'format':'swdb.portal-fuse-service-public-identity.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_s':time.monotonic()-started,'bytes_read':total,'child':c,'parent':p,'child_cmdline_pin':{'bytes':len(cb),'sha256':sha(cb)},'parent_cmdline_pin':{'bytes':len(pb),'sha256':sha(pb)},'child_role_argument_projection':child_argv,'parent_links':parent_links,'native_file_pins':natives,'installed_package_metadata':packages,'parent_namespace_exact_portal_mount':mount_rows,'public_role_identity_stable_at_end':True,'protected_child_fields':{k:'UNOBSERVED' for k in ('cwd','root','exe','fd','maps','syscall','wait_channel')},'parent_semantic_exclusion_cleanup_or_global_reference_free_claimed':False,'no_signal_native_execution_mount_change_or_filesystem_write':True},sort_keys=True))
