"""One exact authorized T20 context submission. Created 2026-09-27 ET.

Operational recipe only: current corrected code, immutable prepared payload, no repair,
build, measurement, retry, or acceptance claim. Shared helpers come from the separately pinned corrected runtime.
"""
import argparse
from datetime import datetime, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tarfile
import time
from zoneinfo import ZoneInfo

ORIGIN = Path('/data1/yanruj/EvolveSWDB_provider_20260926_a1')
SUP = Path('/data1/yanruj/EvolveSWDB_supervision_recovery_runtime_20260927_a1')
SUP_COMMIT = '8cbfee600f23416a8e9578fa8d3ce3f0e19fced8'
RUNTIME_MANIFEST = Path(__file__).with_name('bfs-provider-context2-runtime-20260926.json')
RUNTIME_MANIFEST_SHA = '55d236947c3c0907d1f883493137244b99e3906cbd667a732af4dbd1d27a918c'
PUBLIC=SUP
PUBLIC_COMMIT=SUP_COMMIT
ORIGIN_COMMIT='5f1b8028619976b36df5fa24b8aacb91bf488168'
RECORDS_COMMIT='1b2250670077a2f48c7dd8b28333685c4f757982'
CODE_COMMIT = '8cbfee600f23416a8e9578fa8d3ce3f0e19fced8'
RUN_ID = 'bfs-provider-context2-20260927-a1'
RID = 'bfs-campaign-preparation-20260925-a1.upstream-annotated-context2'
PREVIOUS_ID = 'bfs-campaign-preparation-20260925-a1.upstream-annotated-context1'
PREP = Path(__file__).with_name('prepared')
RAW = Path('/data/yanruj/EvolveSWDB_runs')/RUN_ID
BASE=RAW/'provider'
RECORDS=RAW/'record-view'/'records'
DISPATCH = Path(str(RAW)+'.dispatch')
SOURCE = Path('/data1/yanruj/EvolveSWDB_sources')/RID
PROMPT_SHA = '3a42edd717c1ea13bdd28a935459cb0209709375d077b06504ff0f623ae5e992'
CONFIG_SHA = '15b1aee031862cba565f9e36dc1d78bdc409eb6bb4a10c8f836c241e172a67c8'
REQUEST_SHA = 'ad6a155a1b1bcbdc5d16b12edfe2fb94035037b8ddd229d32fb889edda58cdf9'
LINEAGE_SHA = '5de17f2467ae7cf199390d050bbe1c977ad8496beb24f8f4526f23d5783b7fe5'
CLAUDE_SHA = '5c4735937844e84f8a93306e841a5b0e12252909b07870f789b190468da147ab'
PREVIOUS_SECONDS = 166.97339878883213
CONFIG = {'kind':'claude','command':['/data1/yanruj/.npm-global/bin/claude'],
          'timeout_s':600,'max_repairs':2,'total_seconds':1632,'budget_usd':10}
ET = ZoneInfo('America/New_York')
BOUNDS = {'outer_seconds':750,'work_seconds':720,'cleanup_seconds':30,
          'provider_seconds':600,'remaining_provider_seconds':1632,'public_submit_seconds':660,
          'sampled_rss_bytes':16*1024**3,'retained_bytes':1024**3,
          'raw_reserve_bytes':30*1024**3,'source_reserve_bytes':10*1024**3}
REMOVED = ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONUSERBASE','PYTHONOPTIMIZE',
           'PYTEST_PLUGINS','LD_PRELOAD','LD_LIBRARY_PATH')


def require(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def ref(path):
    return {'path':str(path),'sha256':sha(path),'bytes':Path(path).stat().st_size}


def stamp(): return datetime.now(ET).isoformat()


def guard_runtime(root, expected_commit, manifest, *, deadline):
    """Stdlib-only pre-import verification; creates no subprocess or new clock."""
    def check(): require(time.monotonic()<deadline,'runtime verification exhausted original work clock')
    check();root=Path(root)
    require(root.is_absolute() and root.is_dir() and root==root.resolve(),'canonical runtime checkout required')
    require(manifest['commit']==expected_commit and manifest['runtime_paths']==
            ['scripts','swdb','schemas','vocab','tools/bfs_native','tests','apps','pyproject.toml'],
            'runtime manifest identity differs')
    require({p.name for p in root.iterdir()}<=set(manifest['root_entries'])|{'.git'},
            'runtime contains untracked root entries')
    git=root/'.git';require(git.is_dir() and git==git.resolve(),'ordinary canonical Git checkout required')
    head=(git/'HEAD').read_text().strip()
    if head.startswith('ref: '):
        name=head[5:];require(name.startswith('refs/') and '..' not in Path(name).parts,'unsafe Git HEAD reference')
        target=git/name;require(target.resolve().is_relative_to(git),'unsafe Git HEAD reference')
        if target.is_file():head=target.read_text().strip()
        else:
            packed=(git/'packed-refs').read_text().splitlines()
            matches=[row.split()[0] for row in packed if row and not row.startswith(('#','^')) and row.split()[-1]==name]
            require(len(matches)==1,'Git HEAD reference is unavailable');head=matches[0]
    require(head==expected_commit,'runtime checkout differs from reviewed commit')
    actual={};count=0
    for name in manifest['runtime_paths']:
        folder=root/name;require(folder.exists() and folder==folder.resolve(),'missing or unsafe runtime path')
        pending=[folder]
        while pending:
            check();path=pending.pop();count+=1
            require(count<=8192,'runtime traversal bound exceeded')
            require(not path.is_symlink(),'runtime symlink rejected')
            if path.is_dir():
                require(path.name!='__pycache__','runtime bytecode shadow rejected')
                pending.extend(path.iterdir());continue
            key=str(path.relative_to(root));expected=manifest['files'].get(key)
            require(path.is_file() and expected is not None,'runtime contains untracked import or data file')
            require(path.stat().st_size==expected['bytes'],'runtime file size differs')
            digest=hashlib.sha256()
            with path.open('rb') as stream:
                while chunk:=stream.read(65536):check();digest.update(chunk)
            actual[key]={'sha256':digest.hexdigest(),'bytes':path.stat().st_size}
            require(actual[key]==expected,'runtime file bytes differ')
    require(actual==manifest['files'],'runtime inventory differs')
    check();return {'root':str(root),'commit':expected_commit,'files':actual}


def fixed_runtime_guard(deadline):
    require(sha(RUNTIME_MANIFEST)==RUNTIME_MANIFEST_SHA,'Git-carried runtime manifest changed')
    manifest=json.loads(RUNTIME_MANIFEST.read_text())
    require(manifest['root']==str(SUP),'runtime manifest checkout differs')
    return guard_runtime(SUP,SUP_COMMIT,manifest,deadline=deadline)


def wrapper_entry():
    # The shell invokes this using Python -I and this exact Git-carried recipe.
    # No checkout code has been imported. The same PID then enters main(),
    # retaining this guard in dispatch even if admission fails immediately.
    end=datetime.fromisoformat(sys.argv[sys.argv.index('--outer-deadline')+1])
    require(end.utcoffset() is not None,'aware original outer deadline required')
    deadline=time.monotonic()+(end-datetime.now(ET)).total_seconds()-30
    fields=Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()
    observed={'state':'checking','started':stamp(),'identity':{'pid':os.getpid(),'start_ticks':int(fields[19])},
              'runtime_commit':SUP_COMMIT,'runtime_manifest':ref(RUNTIME_MANIFEST)}
    path=DISPATCH/'runtime-guard.json'
    def persist():
        with path.open('w') as stream:json.dump(observed,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    persist()
    try:
        observed['runtime']=fixed_runtime_guard(deadline);observed['state']='passed';observed['finished']=stamp();persist()
        require(time.monotonic()<deadline,'wrapper runtime guard exhausted original work clock')
    except BaseException as exc:
        observed.update(state='failed',reason=f'{type(exc).__name__}: {exc}',finished=stamp())
        try:persist()
        except BaseException as secondary:exc.add_note(f'guard persistence: {secondary}')
        raise
    return main()


def debit(seconds):
    require(type(seconds) in (int,float) and math.isfinite(seconds) and seconds>=0,
            'provider debit is missing or invalid')
    require(seconds<=1632,'remaining provider allowance exhausted')
    return {'original_provider_allowance_seconds':1800,'previous_used_seconds':PREVIOUS_SECONDS,
            'supplement_used_seconds':seconds,'cumulative_used_seconds':PREVIOUS_SECONDS+seconds,
            'remaining_provider_seconds':max(0,1632-seconds),
            'cumulative_floor_discarded_seconds':1800-PREVIOUS_SECONDS-1632,
            'initial_provider_used_seconds':62.419636563397944,
            'context1_provider_used_seconds':104.55376222543418,
            'repairs_used':0,'maximum_later_repairs':2,'per_call_seconds':600,'per_call_usd':10}


# Runs in a distinct interpreter at the exact current public checkout, with
# unchanged historical records in a newly materialized Git-derived data view.
PREFLIGHT = r'''
import hashlib,json,sys
from pathlib import Path
from swdb import artifacts,profile,profile_package,rewrite,workflow,yamlio
from swdb.store import Store
prep=Path(sys.argv[1]); store=Store(Path(sys.argv[2])); line=json.loads((prep/'lineage-and-budget.json').read_text())
r=json.loads((prep/'upstream-annotated-context2.proposal.json').read_text())
assert store.get(r['id']) is None
lane=profile._verified_lane(store.get('mbit10','machine'),'mbit10-evaluation-node1')
for reference in [line['predecessor']['record'],line['predecessor']['original_envelope'],line['predecessor']['provider_receipt']]:
 p=Path(reference['path']);assert artifacts.file_hash(p)==reference['sha256'] and p.stat().st_size==reference['bytes']
old=store.get(line['predecessor']['id'],'proposal'); assert artifacts.digest(old)==line['predecessor']['record_canonical_sha256']
assert old['outcome']['state']=='unresolved' and len(old['attempts'])==1
assert old['repair_budget']['used_seconds']==line['budget']['context1_used_seconds']
original=json.loads(Path(line['predecessor']['original_envelope']['path']).read_text())
assert {k:v for k,v in r.items() if k not in ('id','parameters')}=={k:v for k,v in original.items() if k not in ('id','parameters')}
changed={'predecessor_proposal','original_unresolved_reason'}
assert all(r['parameters'][k]==v for k,v in original.get('parameters',{}).items() if k not in changed)
assert r['parameters']['predecessor_proposal']==old['id'] and r['parameters']['original_unresolved_reason']==old['outcome']['reason']
assert set(r['parameters'])-set(original.get('parameters',{}))=={'target_execution_clarification'}
clarification=r['parameters']['target_execution_clarification']
assert r['hardware_target']=='dx100-e4fc4af-4c' and r['require_executable_backend'] is True
assert clarification['requested_target']['backend']==r['parameters']['read_only_context']['target']['backend']
build_ref=clarification['retained_build_only_evidence']
build_path=Path('/data1/yanruj/EvolveSWDB_provider_20260926_a1')/build_ref['record_path']
assert artifacts.file_hash(build_path)==build_ref['record_file_sha256']
build=yamlio.load(build_path); assert build['id']==build_ref['id'] and build['outcome']['state']=='complete'
compile_rows=[s for s in build['stages'] if s['stage']=='candidate_compile']
assert len(compile_rows)==1 and compile_rows[0]['command']==build_ref['compiler_command'] and compile_rows[0]['returncode']==0

for item in clarification['reference_source_excerpts']:
 record=store.get(item['source_snapshot'],'source_snapshot'); root=artifacts.verify(record['artifact'])
 p=root/'benchmarks/gapbs/src/bfs.cc'; assert artifacts.file_hash(p)==item['file_sha256']
 lo,hi=item['lines']; assert ''.join(p.read_text().splitlines(keepends=True)[lo-1:hi])==item['text']
assert line['budget']['next_allowance_seconds']==1632 and line['budget']['context1_used_seconds']==104.55376222543418
assert line['budget']['initial_used_seconds']==62.419636563397944
initial=store.get('bfs-campaign-preparation-20260925-a1.upstream-annotated','proposal')
assert initial['outcome']['state']=='unresolved' and initial['repair_budget']['used_seconds']==62.419636563397944
source=store.get(r['source_snapshot'],'source_snapshot'); package=store.get(r['profile_package'],'profile_package')
profile_package.verify(package); artifacts.verify(source['artifact'])
for binding in line['context']['sources']:
 s=store.get(binding['id'],'source_snapshot'); assert artifacts.digest(s)==binding['record_sha256']; artifacts.verify(s['artifact'])
for header in line['context']['headers']:
 s=store.get(header['source_snapshot'],'source_snapshot'); p=Path(s['artifact']['path'])/header['path']
 assert artifacts.file_hash(p)==header['sha256'] and p.stat().st_size==header['bytes']
for entry in [line['context']['target'],*line['context']['operations']]:
 assert artifacts.digest(store.get(entry['id']))==entry['record_sha256']
assert workflow._request_error(r) is None and workflow.check_capabilities(r,store) is None
prompt=rewrite.prompt_for(r,source,package).encode()
assert len(prompt)==523066 and hashlib.sha256(prompt).hexdigest()==line['supplement']['prompt']['sha256']
assert prompt==(prep/'upstream-annotated-context2.prompt.txt').read_bytes()
print(json.dumps({'state':'exact_context_verified','request_sha256':artifacts.digest(r),
'prompt_sha256':hashlib.sha256(prompt).hexdigest(),'prompt_bytes':len(prompt),
'source_sha256':artifacts.digest(source),'package_sha256':artifacts.digest(package),
'predecessor_sha256':artifacts.digest(old),'provider_calls':0,'lane':lane}))
'''


def main():
    entry=time.monotonic(); entered=stamp()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outer-started',required=True); parser.add_argument('--outer-deadline',required=True)
    parser.add_argument('--pane-pid',type=int,required=True); parser.add_argument('--pane-start-ticks',type=int,required=True)
    args=parser.parse_args()
    start=datetime.fromisoformat(args.outer_started); end=datetime.fromisoformat(args.outer_deadline)
    require(start.utcoffset() is not None and end.utcoffset() is not None and end-start==timedelta(seconds=750), 'outer clock must be exactly750 seconds')
    require(start<=datetime.now(ET)<end,'outer clock is future or exhausted')
    deadline=entry+(end-datetime.fromisoformat(entered)).total_seconds(); work_end=deadline-30
    require(sys.flags.optimize==0 and sys.platform=='linux' and sys.dont_write_bytecode,
            'unoptimized Linux Python with explicit bytecode disabled required')
    require(sha(Path(sys.executable).resolve())=='e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f','Python executable changed')
    require(not any(os.environ.get(k) for k in REMOVED),'controlled parent environment required')
    require(not RAW.exists() and not BASE.exists() and not SOURCE.exists(),'new output/source roots required')
    require(DISPATCH.is_dir() and DISPATCH.resolve()==DISPATCH,'canonical existing dispatch root required')
    verified_runtime=fixed_runtime_guard(work_end)
    sys.path.insert(0,str(SUP))
    from scripts import bfs_owned_execution as own
    from scripts.bfs_process import interruption_signals,save_receipt
    from scripts.bfs_storage import allocated_bytes
    from scripts.bfs_native_campaign import campaign_runtime
    RAW.mkdir(); BASE.mkdir(); (BASE/'tmp').mkdir(); (BASE/'cache').mkdir()
    env=dict(os.environ,CLAUDE_CONFIG_DIR='/data1/yanruj/.claude',TMPDIR=str(BASE/'tmp'),
             XDG_CACHE_HOME=str(BASE/'cache'),PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PATH='/usr/bin:/bin')
    for key in REMOVED: env.pop(key,None)
    binding=own.SharedCleanup.create(RAW/'cleanup.json',args.outer_deadline,deadline=deadline)
    budget=own.SharedCleanup(RAW/'cleanup.json',binding,deadline); owner=own.Owned(budget)
    receipt={'id':RUN_ID,'state':'running','started':entered,'outer_started':args.outer_started,
        'outer_deadline':args.outer_deadline,'bounds':BOUNDS,'stages':[],
        'public_checkout':str(PUBLIC),'public_commit':PUBLIC_COMMIT,'prepared_prompt_code':CODE_COMMIT,
        'record_origin':{'root':str(ORIGIN),'commit':RECORDS_COMMIT,'checkout_commit':ORIGIN_COMMIT},'records':str(RECORDS),
        'supervisor_checkout':str(SUP),'supervisor_commit':SUP_COMMIT,'recipe':ref(__file__),
        'runtime':verified_runtime,'runtime_manifest':ref(RUNTIME_MANIFEST),'wrapper_runtime_guard':ref(DISPATCH/'runtime-guard.json'),
        'python':ref(Path(sys.executable).resolve()),'provider_calls':0,'repairs':0,
        'builds':0,'evaluations':0,'gain_claim':False,'environment':{k:env.get(k) for k in (*REMOVED,'CLAUDE_CONFIG_DIR','TMPDIR','XDG_CACHE_HOME','PATH')},
        'driver_identity':own.identity(os.getpid()),'pane_identity':{'pid':args.pane_pid,'start_ticks':args.pane_start_ticks},
        'cleanup_budget':{'path':str(budget.path),'binding':binding,'budget_seconds':30}}
    receipt['ancestry']=own.ancestry(receipt['driver_identity'],receipt['pane_identity'])
    finalizing=False
    def check():
        require(time.monotonic()< (deadline if finalizing else work_end),'original work/outer deadline exhausted')
        require(datetime.now(ET)<end,'original absolute deadline exhausted')
    def account():
        paths=[RAW,DISPATCH]
        if SOURCE.exists(): paths.append(SOURCE)
        size=allocated_bytes(paths,deadline=deadline if finalizing else work_end,check=check)
        require(size<=BOUNDS['retained_bytes'],'retained artifact ceiling exceeded')
        free={}
        for key,path,bound in [('raw',RAW,BOUNDS['raw_reserve_bytes']),('source',SOURCE.parent,BOUNDS['source_reserve_bytes'])]:
            fs=os.statvfs(path); free[key]=fs.f_bavail*fs.f_frsize; require(free[key]>=bound,key+' free reserve violated')
        return {'observed_at':stamp(),'allocated_bytes':size,'roots':list(map(str,paths)),'free_bytes':free}
    def observe():
        check(); sample=owner.sample(); require(sample['rss_bytes']<=BOUNDS['sampled_rss_bytes'],'sampled RSS ceiling exceeded')
        sample['storage']=account(); sample['load_average']=os.getloadavg()
        with (RAW/'resource-samples.jsonl').open('a') as stream:stream.write(json.dumps(sample)+'\n');stream.flush()
        receipt['sampled_peak_rss_bytes']=max(receipt.get('sampled_peak_rss_bytes',0),sample['rss_bytes'])
    monitor=own.Monitor(observe)
    def call(name,argv,timeout=20,allow_failure=False,cwd=PUBLIC):
        check(); monitor.check()
        output=RAW/(name+'.stdout'); error=RAW/(name+'.stderr')
        try: own.run_stage(receipt,RAW,argv,timeout=timeout,deadline=work_end,cwd=cwd,owned=owner,monitor=lambda:(check(),monitor.check()),output=output,stderr=error,env=env)
        except ValueError:
            row=receipt['stages'][-1]
            if not (allow_failure and row.get('returncode')==1 and row.get('cleanup',{}).get('state')=='all_owned_descendants_absent' and not row['cleanup'].get('errors') and not row.get('cleanup_error') and not row.get('finalization_error')):raise
        check(); return output
    def public(name,*argv,timeout=20,allow_failure=False):
        return call(name,[sys.executable,'-s','-m','swdb',*map(str,argv),'--records',str(RECORDS),'--db',str(RAW/'swdb.sqlite'),'--format','json'],timeout,allow_failure)
    def stop_monitor():
        with budget.reservation(maximum=1) as until:
            monitor.stop(until)
    def retain_debit():
        meta_path=BASE/RID/'provider-1'/'provider.json'
        if meta_path.is_file():
            meta=json.loads(meta_path.read_text())
            require(meta['provider']==CONFIG and meta['timeout_s']<=600 and meta['prompt_sha256']==PROMPT_SHA,'provider receipt changed')
            receipt['provider_calls']=1 if 'host_wall_s' in meta else None;receipt['provider_receipt']=ref(meta_path)
            if 'host_wall_s' in meta:receipt['budget_debit']=debit(meta['host_wall_s'])
            else:receipt['budget_debit_state']='unknown_incomplete_provider_receipt_no_retry'
    original_error=None
    with interruption_signals():
      try:
        monitor.start(); save_receipt(RAW,receipt)
        receipt['campaign_runtime']=campaign_runtime(SUP_COMMIT,root=SUP);check()
        for label,root,pin in [('origin',ORIGIN,ORIGIN_COMMIT)]:
            got=call(label+'-commit',['git','rev-parse','HEAD'],cwd=root).read_text().strip();require(got==pin,label+' commit changed')
            call(label+'-clean',['git','diff','--exit-code','HEAD','--','scripts','swdb','schemas','apps'],cwd=root)
        archive=RAW/'records.tar'
        own.run_stage(receipt,RAW,['git','archive','--format=tar',RECORDS_COMMIT,'records'],timeout=15,deadline=work_end,cwd=ORIGIN,owned=owner,monitor=lambda:(check(),monitor.check()),output=archive,stderr=RAW/'archive.stderr',env=env)
        check();view=RAW/'record-view';view.mkdir()
        with tarfile.open(archive) as stream:
            members=stream.getmembers();require(len(members)<=4096 and sum(row.size for row in members)<=512*1024**2,'record archive bound exceeded')
            for row in members:
                check(); require((row.isfile() or row.isdir()) and Path(row.name).parts[0]=='records' and '..' not in Path(row.name).parts and not Path(row.name).is_absolute(),'unsafe record archive entry')
                stream.extract(row,view,filter='data')
        receipt['record_origin']['archive']=ref(archive)
        receipt['record_origin']['files']=[ref(p) for p in sorted(RECORDS.rglob('*')) if p.is_file()]
        check()
        for name,expected in [('upstream-annotated-context2.proposal.json',REQUEST_SHA),('upstream-annotated-context2.provider.json',CONFIG_SHA),('upstream-annotated-context2.prompt.txt',PROMPT_SHA),('lineage-and-budget.json',LINEAGE_SHA)]:
            require(sha(PREP/name)==expected,'prepared input changed: '+name)
        require(json.loads((PREP/'upstream-annotated-context2.provider.json').read_text())==CONFIG,'provider settings changed')
        require(sha(CONFIG['command'][0])==CLAUDE_SHA,'Claude executable changed')
        receipt['claude']={'path':CONFIG['command'][0],'sha256':CLAUDE_SHA}
        receipt['lineage']=ref(PREP/'lineage-and-budget.json');receipt['request']=ref(PREP/'upstream-annotated-context2.proposal.json')
        receipt['config']=ref(PREP/'upstream-annotated-context2.provider.json');receipt['prompt']=ref(PREP/'upstream-annotated-context2.prompt.txt')
        p=call('exact-context',[sys.executable,'-s','-c',PREFLIGHT,str(PREP),str(RECORDS)],timeout=30)
        receipt['context_validation']=json.loads(p.read_text())
        before=public('predecessor-before','get',PREVIOUS_ID)
        require(work_end-time.monotonic()>=660,'insufficient original budget for one whole public submission')
        # One submit only. The immutable config still stores1632remaining for
        # later separately bounded repairs; this invocation performs none.
        result_path=public('submit','submit',PREP/'upstream-annotated-context2.proposal.json','--provider-config',PREP/'upstream-annotated-context2.provider.json','--runs-dir',BASE,timeout=660,allow_failure=True)
        result=json.loads(result_path.read_text());receipt['proposal_outcome']=result['outcome'];receipt['candidate']=result.get('candidate')
        meta_path=BASE/RID/'provider-1'/'provider.json'
        if meta_path.is_file():
            meta=json.loads(meta_path.read_text());require(meta['prompt_sha256']==PROMPT_SHA and sha(meta_path.parent/'prompt.txt')==PROMPT_SHA,'actual sent prompt changed')
            receipt['provider_calls']=1;receipt['provider_receipt']=ref(meta_path);receipt['budget_debit']=debit(meta['host_wall_s'])
            provider_result=json.loads((meta_path.parent/'stdout.txt').read_text())
            receipt['reported_cost_usd']=provider_result.get('total_cost_usd');receipt['usage']=provider_result.get('usage')
        fresh=public('supplement-after','get',RID);require(json.loads(fresh.read_text())==result,'public result differs from fresh retained proposal')
        predecessor=public('predecessor-after','get',PREVIOUS_ID);require(json.loads(predecessor.read_text())==json.loads(before.read_text()),'predecessor changed')
        public('supplement-chain','get',RID,'--chain')
        if result.get('candidate'): public('candidate-after','get',result['candidate'],'--chain')
        receipt['record_view_after']=[ref(p) for p in sorted(RECORDS.rglob('*')) if p.is_file()]
        after={item['path']:item for item in receipt['record_view_after']}
        require(all(after.get(row['path'])==row for row in receipt['record_origin']['files']),'original record view changed')
        require(fixed_runtime_guard(work_end)==verified_runtime,'runtime changed during submission')
        require(campaign_runtime(SUP_COMMIT,root=SUP)==receipt['campaign_runtime'],'campaign runtime changed during submission')
        check();receipt['state']='initial_context_submission_finished'
      except BaseException as exc:
        original_error=exc;receipt.update(state='failed_or_interrupted',reason=f'{type(exc).__name__}: {exc}')
      finally:
        finalizing=True;monitor.interrupt=False
        for name,action in [('cleanup',lambda:own.verified_finish(owner)),('monitor_stop',lambda:stop_monitor())]:
            try:
                if name=='cleanup':receipt['cleanup']=action()
                else:action()
            except BaseException as exc:
                original_error=original_error or exc;receipt.setdefault('finalization_errors',[]).append(f'{name}: {type(exc).__name__}: {exc}')
        try:
          with budget.reservation(maximum=5):
            retain_debit()
            if RECORDS.exists():receipt['record_view_after']=[ref(p) for p in sorted(RECORDS.rglob('*')) if p.is_file()]
            receipt['owned_processes']=list(owner.history.values());receipt['resource_samples']=ref(RAW/'resource-samples.jsonl')
            receipt['cleanup_seconds_used_before_final_persistence']=budget.snapshot()['spent_seconds']
            receipt['finished']=stamp();receipt['host_wall_s']=time.monotonic()-entry
            receipt['outer_wall_s']=(datetime.now(ET)-start).total_seconds()
            receipt['final_accounting']=account()
            if original_error:receipt['state']='failed_or_interrupted'
            save_receipt(RAW,receipt);check();account()
        except BaseException as exc:
            original_error=original_error or exc
            receipt.update(state='failed_or_interrupted')
            receipt.setdefault('finalization_errors',[]).append(f'final persistence: {type(exc).__name__}: {exc}')
            try:
                with budget.reservation(maximum=1):save_receipt(RAW,receipt);check();account()
            except BaseException as later:original_error.add_note(f'failure persistence: {type(later).__name__}: {later}')
      if original_error:raise original_error
    print(json.dumps({'id':RUN_ID,'state':receipt['state'],'proposal_state':receipt.get('proposal_outcome',{}).get('state'),
                      'candidate':receipt.get('candidate'),'budget_debit':receipt.get('budget_debit'),'driver':ref(RAW/'driver.json')}))

    # All charged roots need one final quiescent count after the helper exits;
    # external terminal audit unions ancestry, stage/direct/cleanup and samples.

if __name__=='__main__': wrapper_entry()
