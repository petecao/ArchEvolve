import argparse,pathlib,os,stat,json,hashlib,base64
P=pathlib.Path
def sha(b):return hashlib.sha256(b).hexdigest()
def strict(b):
 def pairs(rows):
  d={}
  for k,v in rows:assert k not in d;d[k]=v
  return d
 return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite')))
a=argparse.ArgumentParser();a.add_argument('--packet',required=True);a.add_argument('--output-directory',required=True);args=a.parse_args();os.umask(0o077)
p=P(args.packet);assert p.parent==P('/private/tmp') and not p.is_symlink() and p.stat().st_size<=1024*1024
b=p.read_bytes();d=strict(b);assert d['format']=='swdb.detached-E-administration-original-custody-transfer.v1' and d['sealed'] is False and d['no_success_or_admission_inferred'] is True and d['legacy_state_label_is_not_launch_or_liveness_proof'] is True
remote=P(d['control_directory']);assert remote.parent==P('/data1/yanruj') and remote.name in ('lanl14-detached-e-inspection-a1','lanl14-detached-e-removal-a1')
dest=P(args.output_directory);assert dest.parent==P('/private/tmp') and dest.name in ('lanl-detached-E-default-originals-20261008-a1','lanl-detached-E-removal-originals-20261008-a1') and not os.path.lexists(dest)
allowed={'status.json':16384,'configuration.json':16384,'tmux.conf':16384,'launch-status.json':16384,'launch.stdout':16384,'launch.stderr':16384,'guard.stdout':262144,'guard.stderr':262144};seen=set();decoded=[]
for pin in d['originals']:
 rp=P(pin['path']);name=rp.name;assert rp.parent==remote and name in allowed and name not in seen;seen.add(name)
 raw=base64.b64decode(pin['original_bytes_base64'],validate=True);assert len(raw)==pin['bytes']<=allowed[name] and sha(raw)==pin['sha256'] and pin['stat']['uid']==114316761 and pin['stat']['nlink']==1 and stat.S_IMODE(pin['stat']['mode'])==0o600 and pin['stat']['size']==len(raw)
 decoded.append((name,raw,pin))
assert {'status.json','configuration.json','tmux.conf','launch-status.json','launch.stdout','launch.stderr'}<=seen
os.mkdir(dest,0o700)
result=[]
for name,raw,pin in decoded:
 out=dest/name;fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 assert out.read_bytes()==raw;result.append({'local_path':str(out),'remote_original_path':pin['path'],'bytes':len(raw),'sha256':sha(raw),'remote_original_stat':pin['stat']})
receipt={'format':'swdb.detached-E-original-local-byte-custody.v1','sealed':False,'source_packet':{'path':str(p),'bytes':len(b),'sha256':sha(b)},'originals':result,'semantic_or_success_or_capacity_admission':False}
with (dest/'local-custody.json').open('x') as f:json.dump(receipt,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'output_directory':str(dest),'originals':[{'basename':P(x['local_path']).name,'bytes':x['bytes'],'sha256':x['sha256']} for x in result],'raw_original_bytes_preserved':True,'no_admission_inferred':True},sort_keys=True))
