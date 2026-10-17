"""One bounded isolated codec regression batch; original pattern retained separately."""
import argparse, datetime, hashlib, json, os, pathlib, platform, re, subprocess, sys, time
P=pathlib.Path
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
def fresh(path,raw=None):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 stream=os.fdopen(fd,'wb')
 if raw is not None:
  with stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
  return None
 return stream
parser=argparse.ArgumentParser();parser.add_argument('--checkpoint',required=True);a=parser.parse_args()
assert re.fullmatch('[a-f0-9]{40}',a.checkpoint)
W=P('/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve');ROOT=P('/Users/yanrujhou/CLionProjects/ArchEvolve')
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True,timeout=120).strip()
assert git(W,'rev-parse','HEAD')==git(W,'rev-parse','origin/codex/lanl-analytic-eval')==git(ROOT,'rev-parse','HEAD')==git(ROOT,'rev-parse','origin/yanrujhou_main')==a.checkpoint
assert not git(W,'status','--porcelain') and git(ROOT,'status','--porcelain')=='M .claude/rules/miscellaneous.md'
assert sha((ROOT/'.claude/rules/miscellaneous.md').read_bytes())=='1487ca3164420584b08b8217e0a4ab2c9fd9ec8fe72d22578ddde9ef72987045'
progress=W/'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/progress.md'
assert progress.read_text().startswith('# Implementation progress\n\nUpdated: 2026-10-07 17:09 ET')
review=P('/private/tmp/lanl14-lossless-gzip-parent-source-review-20261007-a1.json');raw=review.read_bytes()
assert len(raw)==5917 and sha(raw)=='49066bc09f525fb8b21295e66c581c68022983cbe2492a82901e7dc31b6cd6b1'
r=json.loads(raw);assert r['canonical_ensure_ascii'] is True and digest({k:v for k,v in r.items() if k!='identity_sha256'})==r['identity_sha256']=='9d91cd4a52b78d104755e4ea21835ce97bda2fc5f7f317faaa52ec5494864c87'
assert r['test_runs']==0 and r['bounded_test_seconds']==60 and len(r['harness_methods'])==13
pins=list(r['selected_and_preserved_pins'].values())+[r['packet_preparation'],r['review_note']]
for pin in pins:
 path=P(pin['path']);content=path.read_bytes();assert not path.is_symlink() and len(content)==pin['bytes'] and sha(content)==pin['sha256']
argv=r['prospective_exact_test_argv'];assert argv==['/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3','-B','/private/tmp/lanl14_lossless_report_codec_isolated_test_source_20261007_a1_r1.py']
assert sys.version_info[:3]==(3,12,6) and platform.system()=='Darwin' and platform.machine()=='arm64'
binary=P(argv[0]).resolve(strict=True);bp=r['actual_native_interpreter'];assert str(binary)==bp['path'] and binary.stat().st_size==bp['bytes'] and sha(binary.read_bytes())==bp['sha256']
own=P(__file__).absolute();own_sha=sha(own.read_bytes())
paths={suffix:P('/private/tmp/lanl14-lossless-codec-isolated-tests-actual-20261007-a1.'+suffix) for suffix in ('start.json','stdout','stderr','json')}
assert all(not path.exists() and not path.is_symlink() for path in paths.values())
started=datetime.datetime.now(datetime.timezone.utc).isoformat();begin=time.monotonic()
start={'format':'swdb.lanl14-lossless-codec-isolated-test-start.v1','state':'original_unsealed_start_before_one_synthetic_subprocess','started_utc':started,'checkpoint':a.checkpoint,'review_identity_sha256':r['identity_sha256'],'test_source_sha256':r['selected_and_preserved_pins']['selected_R1_harness']['sha256'],'runner_sha256':own_sha,'scientific_admission':False}
fresh(paths['start.json'],(json.dumps(start,indent=2)+'\n').encode())
returncode=None;timed_out=False
with fresh(paths['stdout']) as out,fresh(paths['stderr']) as err:
 try:returncode=subprocess.run(argv,stdout=out,stderr=err,timeout=60,check=False).returncode
 except subprocess.TimeoutExpired:timed_out=True
ended=datetime.datetime.now(datetime.timezone.utc).isoformat()
preserved=all(P(pin['path']).stat().st_size==pin['bytes'] and sha(P(pin['path']).read_bytes())==pin['sha256'] for pin in pins)
assert paths['stdout'].stat().st_size<=65536 and paths['stderr'].stat().st_size<=65536
stderr=paths['stderr'].read_text();counts=re.findall(r'^Ran (\d+) tests in ([0-9.]+)s$',stderr,re.M)
count=int(counts[0][0]) if len(counts)==1 else None;ok=bool(re.search(r'^OK$',stderr,re.M))
methods=re.findall(r'^(test_[A-Za-z0-9_]+) \(.+\) \.\.\. ok$',stderr,re.M)
native_preserved=binary.stat().st_size==bp['bytes'] and sha(binary.read_bytes())==bp['sha256']
runner_preserved=sha(own.read_bytes())==own_sha
receipt={'format':'swdb.lanl14-lossless-codec-isolated-tests-actual.v1','started_utc':started,'ended_utc':ended,'canonical_ensure_ascii':True,'checkpoint_commit':a.checkpoint,'actual_subprocess_returncode':returncode,'actual_timed_out':timed_out,'actual_reported_test_count':count,'actual_reported_OK':ok,'actual_successful_test_method_names':methods,'elapsed_parent_seconds':time.monotonic()-begin,'original_source_review_identity_sha256':r['identity_sha256'],'original_preparation_identity_sha256':r['packet_preparation']['identity_sha256'],'source_pins':r['selected_and_preserved_pins'],'native_interpreter_pin':bp,'runner':{'path':str(own),'sha256':own_sha},'outputs':{suffix:{'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path.read_bytes()),'original_sealed':False} for suffix,path in paths.items() if suffix!='json'},'batch_invocations':1,'source_preparation_review_preserved':preserved,'native_interpreter_preserved':native_preserved,'runner_source_preserved':runner_preserved,'scientific_admission':False,'actual_report_or_E_R_receipt_inputs_constructed':False,'target_main_Store_validate_provider_native_compiler_campaign_remote_actions':0,'TDD_claim':'One isolated regression batch; no invented RED/GREEN claim.','scope':'Only the reviewed12 codec definitions+5 closed assignments are lifted; synthetic256/4096 byte caps and independent stdlib gzip oracle. No exporter/reader main, original report, public scientific records, Store, SSH or other control/test repeat. Original preparations/harness drafts remain NOTRUN history.'}
receipt['identity_sha256']=digest(receipt);fresh(paths['json'],(json.dumps(receipt,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode())
print(json.dumps({'path':str(paths['json']),'bytes':paths['json'].stat().st_size,'sha256':sha(paths['json'].read_bytes()),'identity_sha256':receipt['identity_sha256'],'returncode':returncode,'tests':count,'OK':ok,'scientific_admission':False}))
assert not timed_out and returncode==0 and count==13 and ok and preserved and native_preserved and runner_preserved
assert len(methods)==13 and set(methods)==set(r['harness_methods'])
