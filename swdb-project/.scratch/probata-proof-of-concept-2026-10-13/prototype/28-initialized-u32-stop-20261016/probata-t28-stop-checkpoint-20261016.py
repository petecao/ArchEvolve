"""User-requested STOP checkpoint: copy/hash existing compact files only.

No imports of project code, subprocesses, compiler, tests, native or formal jobs.
"""
import hashlib,json,shutil,sys
from pathlib import Path
def nochild(event,args):
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork'))or event in {'os.system','ctypes.dlopen'}:raise RuntimeError('checkpoint refuses child execution')
sys.addaudithook(nochild)
R=Path('/private/tmp');project=R/'probata-resume-t25-pair/swdb-project'
dest=project/'.scratch/probata-proof-of-concept-2026-10-13/prototype/28-initialized-u32-stop-20261016'
assert not dest.exists();dest.mkdir()
def pin(path):
 p=Path(path).resolve()
 with p.open('rb')as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest}
packet=R/'probata-t28-initialized-u32-public-control-packet-v2-e99d09b1-20261016.json'
assert pin(packet)['sha256']=='c99c0b28bfc74969383b85d994b0c20d3ab43d6a8d7f92c8d92003ac8383af5e'
value=json.loads(packet.read_text());paths={packet,*[Path(p['path'])for p in value['refs']],Path(value['command']['path'])}
# Preserve the incomplete formal harness and final authoring receipts as-is.
paths.add(R/'probata-t28-initialized-register-actual-pair-tests-v1-20261016.py')
for stem in ['probata-t28-initialized-public-v2-packet-freeze-v1-20261016','probata-t28-initialized-runtime-template-build-v1-20261016','probata-t28-initialized-runtime-template-build-v2-20261016']:
 paths.add(R/(stem+'.py'))
 for suffix in ['.log','.log.summary.json','.log.wait.json']:paths.add(R/(stem+suffix))
for filename in ['probata-t28-initialized-u32-public-control-plan-v1-20261016.md','probata-t28-initialized-u32-public-control-plan-draft-20261016.md','probata-t28-initialized-u32-public-runtime-packet-freeze-v1-20261016.py']:
 paths.add(R/filename)
paths.add(Path(__file__))
copied=[]
for source in sorted(paths):
 target=dest/source.name;assert not target.exists(),source.name
 shutil.copyfile(source,target)
 assert pin(source)['sha256']==pin(target)['sha256']
 copied.append({'original':pin(source),'tracked_relative':str(target.relative_to(project)),'status':'PRESERVED AS-IS; no execution authorized'})
raw=R/'probata-t28-initialized-u32-public-compiler-standin-v1-188a478e-20261016'
required=[{'path':str(raw),'kind':'immutable original FAILED public workflow raw directory; retain full contents'}]
for path in [raw/'component/artifact-manifest.json',raw/'component/result.json',raw/'component/junit.xml',R/'probata-t07-device-diagnostic-proof-v2-20261016-expected.json',R/'probata-t28-initialized-u32-compiler-observe-v1-20261016/component/compiler-inputs.json',R/'probata-t28-initialized-u32-compiler-observe-v1-20261016/component/driver-context.stderr']:
 required.append({'kind':'retain on current host; metadata pin only, payload not copied',**pin(path)})
required.append({'path':str(R/'probata-t28-initialized-u32-compiler-observe-v1-20261016'),'kind':'retain original root-only8-call compiler observations/AST/LLVM/header provenance raw; no raw copied'})
index={'date':'2026-10-16 ET','user_requested_stop':True,'status':'STOPPED; INCOMPLETE / UNREVIEWED / NOT EXECUTED successor artifacts',
 'physical_source_before_checkpoint':'3ed7291f348d589cb0e30dfedb120cd38da65bc8','combined_runtime_candidate':'e99d09b1699b32525cd4c44cead21ed2fc6f4917',
 'preserved_source_commits':['97a033a4f171c6c0c4e42726947ee8e8099f0252','188a478eaf29089050b70adfbc4a546d20440cb4','ece76ebc6e32c5f1d43ccdf2aa65d7913cf6dec7','e0e8a43562eeb413d876ebc0ab0a0a2bc1b7873f','e99d09b1699b32525cd4c44cead21ed2fc6f4917','3ed7291f348d589cb0e30dfedb120cd38da65bc8'],
 'copied_compact_artifacts':copied,'required_external_retention':required,
 'original_public_V1_status':'FAILED one test on old frame whitespace; preserved not_proven/tool_crash stand-in record, no actual proof',
 'public_V2_status':'Entry/source policy/command/packet authored before STOP; NOT independently reviewed, NOT root-admitted, NOT executed',
 'actual_pair_status':'Only preliminary external711/1107 harness authored; INCOMPLETE, UNREVIEWED, NOT EXECUTED. No initialized actual-pair entry/command/expected/policy packet frozen.',
 'known_author_jobs_or_leases':[],
 'last_author_guard':{'finished':'2026-10-16 11:35:25 EDT','owner':'t28-initialized-public-v2-packet-pure','exit_code':0,'wall_s':0.37582462502177805,'peak_rss_mb':17.46875,'inspection_events':[],'inspection_failures':None,'unconfirmed_children':[],'scope':'pure metadata authoring only'},
 'no_live_host_census_claim':True,'no_actual_formal_native_caller_body_hardware_or_whole_ticket_acceptance':True,
 'next_resume_gate':['Read this STOP checkpoint and root final main/source state; do not autorun any .py or command JSON','Review exact V2 entry/source policy/cache-prefix control and preserved failure with independent reviewer; root choose fresh source HEAD/raw namespace and repin command (saved command expects e99, physical worktree now3ed)','Root freshly admit full source/consumers/runtime/current config/memory/disk/leases before compiler/scripted workflow; require exactly1JUnit test/no skips and retain original V1 failure','Only after source/public gate, finish and independently review new initialized formal711/1107 packet under explicit partial-normal-return/source-order/disjoint-address TCB; coordinate shared source freeze with ticket24 prefix10; no oldproof promotion'],
 'root_owns_final_merge_main_ticket_map_reconciliation_and_cleanup':True}
(dest/'checkpoint-index.json').write_text(json.dumps(index,sort_keys=True,indent=2)+'\n')
(dest/'README.md').write_text('''# User-requested stop checkpoint — 2026-10-16 ET

STOPPED. These files are preserved data. Do not run any script or command JSON.
Public V2 is UNREVIEWED, NOT ADMITTED and NOT EXECUTED. The formal-pair harness is
INCOMPLETE, UNREVIEWED and NOT EXECUTED; no actual-pair entry/expected/command or
runtime packet was completed. The source frame repair and prefix production have
their separate existing independent reviews; that is not a V2 workflow review.

The original initialized188a public V1 FAILED on frame whitespace after a named
stand-in persisted not_proven/tool_crash. It was not a proof attempt or passing
test. All original raw and failure receipts remain immutable on this host.
The token-aware test repair has retained pure RED/GREEN and seven target-change
refusals. The cache control shows why -B alone can read ignored pyc and why a
fresh private prefix is required; it is not compiler or public-workflow evidence.

The saved command expects candidatee99. The physical worktree was fast-forwarded
to published3ed before this checkpoint. Root must select/repin an exact source
and fresh raw namespace, independently review V2 and fresh-admit every runtime,
source/consumer/configuration/resource boundary before considering execution.
Root owns final merge to yanrujhou_main, ticket/map reconciliation and cleanup.

checkpoint-index.json hashes every copied file and lists required external raw
and cached-runtime metadata. AST/LLVM/C/certificate/SMT payloads stay on host;
none is copied here. Runtime-template JSON contains physical hash metadata only
and explicitly leaves OS loader/compiler/header-timing TCB boundaries open.

No author actual job, pending process session or owned lease is known. The final
pure author guard settled11:35:25ET with no events/failures/unconfirmed children;
this is historical settlement evidence, not a fresh host process/lease census.
''')
print(json.dumps({'directory':str(dest),'copied_files':len(copied),'copied_bytes':sum(r['original']['bytes']for r in copied),'index':pin(dest/'checkpoint-index.json')},sort_keys=True))
