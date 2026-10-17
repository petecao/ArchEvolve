"""2026-10-16 ET. Read-only source/runtime admission inventory; no compiler probe."""
from pathlib import Path
import hashlib,json,subprocess,datetime
P=Path;repo=P('/private/tmp/probata-resume-t25-pair');head='188a478eaf29089050b70adfbc4a546d20440cb4';candidate='97a033a4f171c6c0c4e42726947ee8e8099f0252'
def H(p):
 with P(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p):p=P(p).resolve();return {'path':str(p),'sha256':H(p),'bytes':p.stat().st_size}
def git(*a):return subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(repo),*a],timeout=60)
assert git('rev-parse','HEAD').decode().strip()==head and not git('status','--porcelain','--untracked-files=all')
subprocess.run(['/usr/bin/git','--no-replace-objects','-C',str(repo),'merge-base','--is-ancestor',head,'refs/remotes/origin/codex/probata-resume-20261015'],check=True,timeout=30)
packet=P('/private/tmp/probata-t28-initialized-u32-public-control-packet-v1-188a478e-20261016.json');assert H(packet)=='23c1a7f51fb27db3c8b53c41faedd8cedba38e22a54bf265b7181bbe75e6b755';d=json.loads(packet.read_bytes())
for r in [d['command'],*d['refs']]:assert pin(r['path'])==r
policy_path=P('/private/tmp/probata-t28-initialized-u32-public-runtime-policy-template-v1-20261016.json');policy=json.loads(policy_path.read_bytes());assert H(policy_path)=='67804e55f69b188983493033ec8180f6c784b181831d0db12919b401bea7e0c0'
assert len(policy['pins'])==4489 and len({r['path']for r in policy['pins']})==4489
for row in policy['pins']:assert pin(row['path'])==row
context=json.loads(P('/private/tmp/probata-t28-initialized-u32-public-runtime-template-context-v1-20261016.json').read_bytes());trees=[]
for t in context['trees']:
 root=P(t['root']);members=[{'relative':str(p.relative_to(root)),**pin(p)}for p in sorted(root.rglob('*'))if p.is_file()];h=hashlib.sha256(json.dumps(members,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert len(members)==t['files'] and h==t['membership_sha256'];trees.append(t)
roots=['swdb-project/'+r for r in ['swdb','tests','library','schemas','vocab','records','pyproject.toml']]+['apps/dx100/benchmarks/API/MAA.hpp','apps/dx100/benchmarks/API/MAA_gem5.hpp']
assert not git('diff','--name-only',candidate,head,'--',*roots)
rows=[]
for raw in git('ls-tree','-r','-z',head,'--',*roots).split(b'\0'):
 if not raw:continue
 meta,name=raw.decode().split('\t',1);mode,kind,oid=meta.split();p=repo/name;assert kind=='blob'and mode in {'100644','100755'} and not p.is_symlink() and p.is_file()
 size=p.stat().st_size;g=hashlib.sha1(('blob '+str(size)+'\0').encode());h=hashlib.sha256()
 with p.open('rb')as f:
  for block in iter(lambda:f.read(1048576),b''):g.update(block);h.update(block)
 assert g.hexdigest()==oid;rows.append({'relative':name,'git_blob':oid,'sha256':h.hexdigest(),'bytes':size})
# Preserve any ignored author caches as explicit non-source observations; do not
# claim full directory identity from tracked Git equality.
ignored=git('ls-files','--others','--ignored','--exclude-standard','--',*roots).decode().splitlines();cache_rows=[]
for name in ignored:
 p=repo/name;assert '__pycache__'in p.parts and p.suffix=='.pyc'and p.is_file()and not p.is_symlink();cache_rows.append({'relative':name,**pin(p)})
for relative in ['swdb-project/swdb','swdb-project/tests']:
 root=repo/relative;tracked={r['relative']for r in rows if r['relative'].startswith(relative+'/')};actual={str(p.relative_to(repo))for p in root.rglob('*')if p.is_file()};assert actual==tracked|{r['relative']for r in cache_rows if r['relative'].startswith(relative+'/')}
out={'date_ET':'2026-10-16','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Read-only admission inventory for root-owned compiler and scripted public persistence only; no actual workflow/proof. Runtime template selected concretely by exact67804 bytes after fresh4489pin/six tree checks. Native loader/compiler-to-source/header-after-preprocessing TCB remains.','source_commit':head,'runtime_candidate':candidate,'candidate_runtime_sources_equal':True,'published_ancestor':True,'source_clean':True,'tracked_source_consumer_files':rows,'tracked_source_consumer_count':len(rows),'tracked_source_consumer_bytes':sum(r['bytes']for r in rows),'ignored_cache_count':len(cache_rows),'ignored_cache_rows':cache_rows,'ignored_cache_boundary':'Author caches are separately retained; tracked source identity is not a full author-directory claim. All non-cache extras in code/tests refused.','runtime_policy':pin(policy_path),'runtime_pins_checked':4489,'runtime_physical_bytes':sum(r['bytes']for r in policy['pins']),'runtime_tree_memberships':trees,'packet':pin(packet),'compiler_or_native_or_formal_executed':False}
t=P('/private/tmp/probata-root-initialized-public-admission-v1-20261016.json');assert not t.exists();t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'path':str(t),'sha256':H(t),'bytes':t.stat().st_size,'source_consumers':len(rows),'ignored_caches':len(cache_rows),'runtime_pins':4489}))
