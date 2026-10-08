from pathlib import Path
import ast,difflib,hashlib,json,os
D=Path('/private/tmp')
oldc=D/'lanl_read_detached_R4_administration_originals_20261008_a1_r4.py'
oldd=D/'lanl_decode_detached_R4_original_custody_20261008_a1_r4.py'
newc=D/'lanl_read_detached_sparse_administration_originals_20261008_a1.py'
newd=D/'lanl_decode_detached_sparse_original_custody_20261008_a1.py'
W=D/'lanl17_detach_library_preserving_sparse_administration_20261008_a1_r1.py'
G=D/'lanl_sparse_retire_consumed_source_guard_20261008_a1_r2.py'
wp=hashlib.sha256(W.read_bytes()).hexdigest();gp=hashlib.sha256(G.read_bytes()).hexdigest()
assert len(W.read_bytes())==24115 and wp=='1127d1fba8e004153cf086cace7d19ccd901e85902f9ad91924407922c85c6ca'
assert len(G.read_bytes())==166145 and gp=='4956a7453ae569d7ccf6e1a9ed98a1a933bee2e35cca1774932afbfba819bd26'
replacements={
'2b9b2200b002693fa79930822dee530ab9ecda17d3bd04be9f2a726e355ff5df':wp,
'97219cdb326edf76e6d341aab4a2a8d58a4750e3da8d2e24a5f9e1097f4a69be':gp,
"CONTROL_ROUTES=('/data1/yanruj/lanl17-detached-r4-inspection-a1','/data1/yanruj/lanl17-detached-r4-removal-a1')":"CONTROL_PREFIX='lanl17-detached-sparse-'",
"wrapper['bytes']==24002":"wrapper['bytes']==24115",
"guard['bytes']==117232":"guard['bytes']==166145",
'swdb.lanl17-detached-exact-R4-administration-status.v1':'swdb.lanl17-detached-library-sparse-administration-status.v1',
'swdb.lanl17-detached-exact-R4-administration-configuration.v1':'swdb.lanl17-detached-library-sparse-administration-configuration.v1',
'/data1/yanruj/lanl-consumed-detached-source-guard-20261007-':'/data1/yanruj/lanl-library-preserving-sparse-retirement-20261008-',
"'remove_requested'":"'retire_requested'",
'swdb.consumed-detached-source-guard.v1':'swdb.library-preserving-sparse-retirement-guard.v1',
'swdb.consumed-source-guard-return.v1':'swdb.library-preserving-sparse-retirement-return.v1',
'swdb.detached-R4-administration-original-custody-transfer.v1':'swdb.lanl17-detached-library-sparse-original-custody-transfer.v1',
'swdb.detached-R4-original-local-byte-custody.v1':'swdb.lanl17-detached-library-sparse-original-local-byte-custody.v1',
}
for old,new,role in [(oldc,newc,'collector'),(oldd,newd,'decoder')]:
 text=old.read_text()
 for x,y in replacements.items():
  if x in text:text=text.replace(x,y)
 if role=='collector':
  text=text.replace('# Source-only derivative: fixed R4 originals, including missing/partial administrative custody; no guard execution.','# Source-only sparse derivative: fixed eight originals and original True guard receipt; no guard execution.')
  text=text.replace("a.add_argument('--control-directory',required=True,choices=CONTROL_ROUTES)","a.add_argument('--control-directory',required=True)")
  text=text.replace("folder=P(args.control_directory);assert folder.resolve(strict=True)==folder", "folder=P(args.control_directory);assert folder.parent==BASE and folder.name.startswith(CONTROL_PREFIX) and len(folder.name)<=48\nassert folder.resolve(strict=True)==folder")
 else:
  text=text.replace('# Source-only derivative: exact R4 administrative originals; no guard execution or semantic admission.','# Source-only sparse derivative: exact administrative originals; no guard execution or semantic admission.')
  text=text.replace("remote=P(d['control_directory']);assert str(remote) in CONTROL_ROUTES\nlabel='inspection' if str(remote)==CONTROL_ROUTES[0] else 'removal'\ndest=P(args.output_directory);assert dest==P('/private/tmp')/('lanl17-detached-r4-'+label+'-originals-20261008-a1') and not os.path.lexists(dest)", "remote=P(d['control_directory']);assert remote.parent==P('/data1/yanruj') and remote.name.startswith(CONTROL_PREFIX) and len(remote.name)<=48\ndest=P(args.output_directory);assert dest==P('/private/tmp')/(remote.name+'-originals-20261008') and not os.path.lexists(dest)")
 ast.parse(text)
 fd=os.open(new,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'w') as f:f.write(text)
 diff=D/('lanl17-sparse-original-'+role+'-complete-R4r4-derivation-20261008-a1.diff')
 raw=''.join(difflib.unified_diff(old.read_text().splitlines(True),text.splitlines(True),fromfile=str(old),tofile=str(new))).encode()
 fd=os.open(diff,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw)
 for p in [new,diff]:b=p.read_bytes();print(str(p),len(b),hashlib.sha256(b).hexdigest())
