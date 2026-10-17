"""INERT one complete qualified-grow public proof profile, 2026-10-16 ET.

Only root may admit/launch this under a socket lane and8GiB one-worker tree guard.
It reuses selected immutable source source. There is no monkeypatch, old record promotion,
changed solver policy, original-v2 proof or generic-caller acceptance.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
EXPECTED_SHA256='551189885aee9ad52e58eeeedd5a1ab2a3146d00d59174f74c74de6e8fcb4c2b'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return {'path':str(p),'sha256':sha(p),'bytes':Path(p).stat().st_size}
def write(p,obj):p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def surface(root,rows):
    root=Path(root)
    if root.is_symlink() or not root.is_dir():raise ValueError('selected import root changed')
    found=[]
    for p in sorted(root.rglob('*')):
        if p.is_symlink() or not(p.is_file() or p.is_dir()):raise ValueError('nonregular import input')
        if p.is_file():found.append({'relative':str(p.relative_to(root)),'sha256':sha(p)})
    if found!=rows:raise ValueError('selected full import-tree membership/hash differs: '+str(root))

def linux_admission(expected,repo,out):
    raw_value=os.environ.get('PROBATA_OUTPUT')
    if not raw_value:raise ValueError('Linux coordinator PROBATA_OUTPUT marker required')
    root=Path(raw_value).resolve()
    if root!=out.parent.resolve():raise ValueError('Linux output marker differs from exact profile root')
    if os.environ.get('SWDB_VERIFIER_LOCK')!=str(root/'verifier.lock') or os.environ.get('SWDB_VERIFIER_RSS_CAP_BYTES')!='8589934592':
        raise ValueError('Linux lock/cap context differs from reviewed wrapper')
    launch_path=root/'launch.json';launch=json.loads(launch_path.read_bytes());policy=expected['resource_policy']
    if Path(launch['source']).resolve()!=repo.resolve() or launch.get('source_commit')!=expected['source_commit']:
        raise ValueError('Linux launch source differs from selected immutable source')
    if launch.get('rss_cap_bytes')!=policy['cap_bytes'] or launch.get('workers')!=1 or launch.get('timeout_seconds')!=policy['root_whole_seconds']:
        raise ValueError('Linux launch whole-worker budget differs')
    command=launch.get('command',[]);binding=expected['linux_launch_binding']
    prefix=[expected['tools']['opam']['path'],'exec','--switch=framac-33','--',binding['python'],'-c']
    if command[:6]!=prefix or len(command)!=9 or command[-2:]!=[str(repo/'swdb-project'),str(root)]:
        raise ValueError('Linux admitted entry command boundary differs')
    # Root's reviewed bootstrap embeds exact entry/expectation bytes and digest
    # literals; it stages them outside source then execs this immutable entry.
    code=command[6]
    if 'ENTRY_SHA256 = '+repr(sha(__file__)) not in code or 'EXPECTED_SHA256 = '+repr(EXPECTED_SHA256) not in code:
        raise ValueError('Linux launch does not bind exact entry/expected byte hashes')
    for name,wanted in binding['wrappers'].items():
        if launch.get('reviewed_wrapper_reuse',{}).get(name)!=wanted or sha(root/name)!=wanted:
            raise ValueError('Linux outer wrapper bytes differ')
    return {'marker_path':str(root),'launch':pin(launch_path),'command_sha256':hashlib.sha256(json.dumps(command,separators=(',',':')).encode()).hexdigest(),
            'source_commit':expected['source_commit'],'rss_cap_bytes':policy['cap_bytes'],'whole_seconds':policy['root_whole_seconds'],
            'lock_path':str(root/'verifier.lock'),'scope':binding['scope'],'Mac_counted_token_required':False}

def consumer_closure(project,repository,expected):
    commit=expected['source_commit'];trees=expected['source_consumer_trees']
    def git(*a,input=None):return subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(repository),*a],input=input,timeout=180)
    for relative,tree in trees.items():
        if git('rev-parse','--verify',commit+':swdb-project/'+relative).decode().strip()!=tree['oid']:
            raise ValueError('source consumer Git tree/blob differs: '+relative)
    packed=git('ls-tree','-r','-z',commit,'--',*['swdb-project/'+x for x in trees])
    wanted=[]
    for entry in packed.split(b'\0'):
        if not entry:continue
        meta,name=entry.decode().split('\t',1);mode,kind,oid=meta.split()
        if mode not in {'100644','100755'}or kind!='blob' or not name.startswith('swdb-project/'):
            raise ValueError('source consumer requires exact regular Git blobs')
        relative=name.removeprefix('swdb-project/');p=project/relative
        if '\n'in str(p)or '\r'in str(p)or str(p).startswith('"'):raise ValueError('unreviewed source path encoding')
        wanted.append({'relative':relative,'git_blob':oid,'path':str(p)})
    found=set()
    for relative in trees:
        root=project/relative
        if root.is_symlink()or not(root.is_file()or root.is_dir()):raise ValueError('source consumer root changed')
        for p in ([root]if root.is_file()else root.rglob('*')):
            if p.is_symlink()or not(p.is_file()or p.is_dir()):raise ValueError('source consumer symlink/special input')
            if p.is_file():found.add(str(p.relative_to(project)))
    if found!={r['relative']for r in wanted}:raise ValueError('source consumer physical membership differs from selected exact source Git tree')
    # hash-object streams physical files and emits only40-byte object names.
    # It never captures the1.33GB catalog body or invokes a content filter.
    physical_oids=git('hash-object','--no-filters','--stdin-paths',input=''.join(r['path']+'\n'for r in wanted).encode()).decode().splitlines()
    if physical_oids!=[r['git_blob']for r in wanted]:raise ValueError('source consumer physical bytes differ from selected immutable source Git blob')
    for row in wanted:
        p=Path(row['path']);h=hashlib.sha256()
        with p.open('rb')as stream:
            for block in iter(lambda:stream.read(1048576),b''):h.update(block)
        row.update(sha256=h.hexdigest(),bytes=p.stat().st_size)
    return {'source_commit':commit,'trees':trees,'files':wanted,'count':len(wanted),
            'total_bytes':sum(r['bytes']for r in wanted),'physical_git_blob_equality':True,
            'scope':'Opaque source-byte identity only. Existing fixture helper selects/parses YAML header/reference closure; no unrelated scientific evidence or held-out source semantics inspected.'}

def initialize_workspace(out,builder):
    # The unchanged pytest seed expects its caller to supply an existing root.
    # Only this fresh parent is ours: make_records creates records; copytree
    # creates library, whose tracked methods directory already exists. The
    # ordinary public worker later creates runs-outside-repo with parents.
    root=out/'workspace';root.mkdir(exist_ok=False)
    seed=builder(root)
    if seed.root!=root or seed.records!=root/'records' or seed.runs!=root/'runs-outside-repo':
        raise ValueError('committed fixture builder returned unexpected workspace paths')
    for relative in ('records','library','library/methods'):
        path=root/relative
        if path.is_symlink() or not path.is_dir():raise ValueError('fixture directory missing/redirected: '+relative)
    for filename in ('wp-tracer-fixture.yaml','contract-fixture-1.yaml'):
        path=root/'library/methods'/filename
        if path.is_symlink() or not path.is_file():raise ValueError('fixture method missing/redirected: '+filename)
    if seed.runs.exists() or seed.runs.is_symlink():raise ValueError('fixture run output must remain fresh for the ordinary worker')
    return seed

def validate_canonical(expected,manifest,physical,manifest_sha256):
    if manifest_sha256!=expected['canonical_manifest_sha256'] or manifest['model']!=expected['model']:
        raise ValueError('qualified source/semantics/certificate identity differs')
    if [r['id']for r in manifest['obligations']]!=expected['target_ids']or len(expected['target_ids'])!=61:
        raise ValueError('complete61 target order differs')
    if manifest['logical_obligations']!=expected['logical_obligations']:raise ValueError('complete logical AND/source-definition binding differs')
    if manifest['typed_source_image']!=expected['typed_source_image']:raise ValueError('canonical typed-source image differs')
    if physical!=expected['canonical_files']:raise ValueError('complete canonical payload/reference physical membership differs')
    if [r for r in physical if r['path'].startswith('references/')]!=expected['canonical_reference_files']or len(expected['canonical_reference_files'])!=5:
        raise ValueError('all five original whole-target reference C files required')
    if any(r['dependencies']or r['expected']!='proven'for r in manifest['obligations']):raise ValueError('future lemma assumed or target reclassified')

def validate_project_compiler(expected,project,project_runtime,lowering_identity):
    if {k:project_runtime[k]for k in expected['linux_clang_components']}!=expected['linux_clang_components']:
        raise ValueError('selected Linux compiler wrapper/driver/parser/header components differ')
    if str(project)!=expected['remote_project']:raise ValueError('project cwd differs from the exact derived compiler context')
    if project_runtime!=expected['linux_project_identity_derivation']['runtime']:raise ValueError('fresh project runtime differs from source/context-derived Linux template')
    if lowering_identity!=expected['linux_project_identity_derivation']['predicted_identity']:raise ValueError('fresh current source compiler composite differs from independent exact digest reconstruction')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected',required=True,type=Path)
    parser.add_argument('--project',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if sha(args.expected)!=EXPECTED_SHA256:raise ValueError('reviewed exact public profile expectation differs')
    expected=json.loads(args.expected.read_bytes());policy=expected['resource_policy']
    project=args.project.resolve();repo=project.parent;out=args.output.resolve()
    if out.exists() or out.is_relative_to(repo):raise ValueError('new external profile output required')
    linux_launch=linux_admission(expected,repo,out)
    out.mkdir(parents=True);os.chdir(project)
    started=time.monotonic();deadline=started+policy['profile_seconds']
    result={'scope':expected['scope'],'source_commit':expected['source_commit'],'member':expected['member'],
            'public_complete':False,'model_proof_acceptance':False,'original_v2_acceptance':False,'caller_acceptance':False,
            'external_guard_required':policy,'source_consumer_receipts':[],'linux_launch_binding':linux_launch,'cold_task_hypothesis_closure_pending':True}
    def source_check():
        head=subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(repo),'rev-parse','HEAD'],text=True,timeout=30).strip()
        dirty=subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(repo),'status','--porcelain','--untracked-files=all'],text=True,timeout=30)
        if head!=expected['source_commit'] or dirty:raise ValueError('immutable selected exact source source is not clean')
        for row in expected['source_blobs']:
            if sha(project/row['relative'])!=row['sha256']:raise ValueError('selected exact source package input changed: '+row['relative'])
        closure=consumer_closure(project,repo,expected)
        closure_path=out/('source-consumer-closure-'+str(len(result['source_consumer_receipts']))+'.json')
        write(closure_path,closure);result['source_consumer_receipts'].append(pin(closure_path))
        for row in expected['test_helper_pins']:
            if sha(project/row['relative'])!=row['sha256']:raise ValueError('selected exact source standard public-seed helper changed')
    def runtime_check():
        verified={}
        for name,row in expected['tools'].items():
            p=shutil.which(name)
            if p is None or Path(p).resolve()!=Path(row['path']).resolve() or sha(p)!=row['sha256']:
                raise ValueError('selected Linux tool binding differs: '+name)
            verified[name]=pin(Path(p).resolve())
        for row in expected['wp_artifacts']:
            if sha(row['path'])!=row['sha256']:raise ValueError('WP native/META differs')
        prefix=Path(expected['linux_prefix'])
        for key,root in [('why3_stdlib',prefix/'share/why3/stdlib'),('wp_why3_support',prefix/'share/frama-c/share/wp/why3'),('why3_drivers',prefix/'share/why3/drivers')]:surface(root,expected['portable_import_surfaces'][key])
        for row in expected['typed_machine_sources']:
            if sha(prefix/'lib/frama-c-wp/core'/row['name'])!=row['sha256']:raise ValueError('Linux selected Typed/Machine source differs from qualified binding')
        config=expected['why3_config']
        if sha(config['path'])!=config['sha256']:raise ValueError('selected actual portfolio config differs')
        return verified
    def output_budget():
        used=sum(p.stat().st_size for p in out.rglob('*')if p.is_file())
        if used>policy['output_budget_bytes']:raise ValueError('raw profile output budget exceeded')
    try:
        source_check()
        ambient=sorted(k for k in os.environ if k.startswith(('FRAMAC_WP','WP_'))or k=='SWDB_PROOF_REPORT_OUT')
        if ambient:raise ValueError('forbidden ambient WP names: '+','.join(ambient))
        result['ambient_wp_names']=ambient
        selected=runtime_check();write(out/'selected-runtime.json',{'tools':selected,'wp_artifacts':expected['wp_artifacts'],
             'typed_machine_sources':expected['typed_machine_sources'],'why3_config':expected['why3_config'],
             'import_surfaces':expected['portable_import_surfaces'],
             'scope':'prelaunch physical bindings; normal backend additionally checks actual OCaml paths, configured loadpath and runtime before each target'})
        shutil.copyfile(__file__,out/'entry.py');shutil.copyfile(args.expected,out/'expected.json')
        os.environ.update(SWDB_FRAMA_C=expected['tools']['frama-c']['path'],SWDB_CBMC='none',
                          SWDB_OCAMLFIND=expected['tools']['ocamlfind']['path'],
                          WHY3CONFIG=expected['why3_config']['path'],SWDB_WHY3_CONFIG=expected['why3_config']['path'],
                          PYTHONDONTWRITEBYTECODE='1',SWDB_FIXTURE_HOST='swdb-fixture-host',
                          SWDB_VERIFIER_RSS_CAP_BYTES=str(policy['cap_bytes']))
        sys.dont_write_bytecode=True;sys.path[:0]=[str(project),str(project/'tests')]
        from swdb import vector_reallocation_vcs as packets
        canonical=out/'canonical-inputs';manifest=packets.prepare(expected['member'],canonical)
        if packets.check(expected['member'],canonical)!=manifest:raise ValueError('canonical reconstruction differs')
        physical=[{'path':str(p.relative_to(canonical)),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(canonical.rglob('*'))if p.is_file()]
        validate_canonical(expected,manifest,physical,sha(canonical/'manifest.json'))
        write(out/'canonical-precheck.json',{'manifest':pin(canonical/'manifest.json'),'target_ids':expected['target_ids'],
              'model':manifest['model'],'logical_groups':len(manifest['logical_obligations']),'physical_reference_files':expected['canonical_reference_files'],'fresh_targets':61,'old_records_imported':0})
        # This is the exact committed public seed builder used by previous
        # original public model profiles; no helper/adapter monkeypatch exists.
        from swdb import c_lowering,stdlib_provenance
        tool=c_lowering.locate()
        if tool.missing:raise ValueError('selected Linux Clang unavailable: '+tool.missing)
        project_runtime=stdlib_provenance.runtime_identity(tool);lowering_identity=c_lowering.identity()
        validate_project_compiler(expected,project,project_runtime,lowering_identity)
        write(out/'heap-project-runtime-provenance.json',{'cwd':str(project),'runtime':project_runtime,
             'lowering_identity':lowering_identity,'scope':'fresh project-context compiler identity; every actual record/method must match, no Mac/old source composite expected'})
        from test_standard_member_contracts import _member_seed
        seed=initialize_workspace(out,_member_seed)
        import yaml
        method_dir=out/'workspace/library/methods'
        inherited=method_dir/'wp-tracer-fixture.yaml'
        method=yaml.safe_load(inherited.read_bytes())
        if method['c_lowering']['translators']!=[lowering_identity['c_lowering']]:raise ValueError('seed compiler context differs from project snapshot')
        method.update(id=expected['method_id'],sequence=3,
             description='Qualified v3 full grow contract-fixture method. Explicit selected memory/integer binding: '+
                         json.dumps(expected['explicit_method_binding'],sort_keys=True))
        method_path=method_dir/'wp-qualified-grow61-v1.yaml'
        method_path.write_text(yaml.safe_dump(method,sort_keys=False))
        write(out/'method-model-binding.json',{'method_version':{'id':expected['method_id'],'sha256':sha(method_path)},
             'inherited_method':pin(inherited),'binding':expected['explicit_method_binding'],
             'mechanism':'normal method file hash plus explicit existing per-launch typed-runtime source checker; no new unchecked model flag or trusted ID'})
        remaining=min(policy['public_timeout_seconds'],deadline-time.monotonic()-60)
        if remaining<=0:raise TimeoutError('whole profile spent during setup')
        argv=[sys.executable,'-B','-m','swdb','prove','--records',str(seed.records),'--adapter','wp',
              '--method-version',expected['method_id'],'--runs-dir',str(seed.runs),'--format','json',
              '--model',expected['member'],'--budget-minutes',str(remaining/60)]
        write(out/'public-command.json',{'argv':argv,'cwd':str(project),'timeout_seconds':remaining+60,
              'scope':'normal public adapter with unchanged committed method portfolio; complete targets and ordinary/smoke reports'})
        result['public_command_launched']=True;write(out/'result.json',result)
        with (out/'public.stdout').open('wb')as stdout,(out/'public.stderr').open('wb')as stderr:
            done=subprocess.run(argv,cwd=project,env=dict(os.environ),stdout=stdout,stderr=stderr,timeout=remaining+60,check=False)
        result['public_exit_code']=done.returncode;output_budget();source_check();runtime_check()
        if done.returncode:raise ValueError('public prove failed; retained stdout/stderr and all partial artifacts require diagnosis')
        summary=json.loads((out/'public.stdout').read_bytes())
        record_path=(seed.records/summary['path']).resolve()
        if not record_path.is_relative_to(seed.records.resolve()):raise ValueError('record outside isolated seed')
        import yaml
        from jsonschema import Draft202012Validator
        from swdb import proof_setup
        record=yaml.safe_load(record_path.read_bytes())
        issues=[str(e)for e in Draft202012Validator(json.loads((project/'schemas/proof.schema.json').read_bytes())).iter_errors(record)]
        if issues:raise ValueError('persisted public record is not schema-valid: '+str(issues))
        if record['subject']!={'kind':'c_model','id':expected['member']}or record['verdict']!='proven' or record.get('failure_class')is not None:
            raise ValueError('complete qualified public model not proven')
        if record['bounds']!={'threads':1,'input_size':'unbounded'}or record['evidence_kind']!='contract_fixture':raise ValueError('public evidence scope differs')
        if set(record['verdict_reading'])!={'check','verdict'}or record['verdict_reading']['check']!=proof_setup.identity()['verdict_reading']:
            raise ValueError('normal aggregate reader attestation differs')
        settings=record['settings']
        if settings.get('compiler_runtime')!=project_runtime:raise ValueError('record Linux compiler context differs from project snapshot')
        view=settings['heap_model_view'];qualification=view['qualification']
        if view['member']!=expected['member']or view['model']!=expected['model']or qualification['original_contract_proved']is not False or view['generic_caller_composition']!='unsupported':
            raise ValueError('qualified v3 scope or original-contract boundary changed')
        if settings['verifier_launched']is not True or record['proof_setup_check']['verdict']!='passed':raise ValueError('actual verifier/setup missing')
        if view['logical_obligations']!=expected['logical_obligations']:raise ValueError('actual projection split receipt differs')
        if qualification['typed_source_image']!=expected['typed_source_image']:raise ValueError('actual qualified source-image binding differs')
        runs=settings['heap_model_runs']
        if [r['id']for r in runs]!=expected['target_ids']or len(record['proof_setup_check']['runs'])!=61:raise ValueError('incomplete full61 target/setup inventory')
        derived_run_census=[];derived_goals=[]
        for run,target in zip(runs,manifest['obligations']):
            d=Path(run['cwd']);flags=run['command']
            if flags[0]!=expected['tools']['frama-c']['path']or '-wp-prop'in flags or '-wp-gen'in flags:raise ValueError('wrong actual executable or proof filtering/generation flag')
            if not all(x in flags for x in ['-wp-rte','-rte-initialized','@all','-wp-no-filter-init','-wp-smoke-tests','-wp-cache','none','-wp-status-all','+real']):raise ValueError('mandatory complete obligations missing')
            if sha(d/'wp_input.c')!=target['sha256']:raise ValueError('actual source target differs')
            reading=proof_setup.read_wp_reports(d/'wp-goals.json',d/'wp-properties.csv',d/'wp-inventory.json')
            if reading['verdict']!='proven'or reading['reading']!=run['reading']:raise ValueError('normal cold public reader differs')
            ordinary=[g for g in reading['goals']if not g.get('smoke')]
            if not ordinary or any(g['status']!='valid'for g in reading['goals']):raise ValueError('ordinary/smoke proof incomplete')
            if target['kind']=='c_kernel'and not any(g.get('smoke')for g in reading['goals']):raise ValueError('numeric smoke missing')
            inventory=json.loads((d/'wp-inventory.json').read_bytes())
            if inventory.get('complete')is not True:raise ValueError('actual native inventory is incomplete')
            derived_goals.extend(reading['goals'])
            derived_run_census.append({'id':target['id'],'kind':target['kind'],
                'ordinary_goals':len(ordinary),'smoke_goals':sum(bool(g.get('smoke'))for g in reading['goals']),
                'native_generated_goals':len(inventory['goals']),'native_properties':len(inventory['properties']),
                'inventory':pin(d/'wp-inventory.json'),'ordinary_report':pin(d/'wp-goals.json'),'properties_csv':pin(d/'wp-properties.csv')})
        from collections import Counter
        signature=lambda g:json.dumps({k:g.get(k)for k in ['goal','property','function','smoke','status']},sort_keys=True)
        if Counter(map(signature,derived_goals))!=Counter(map(signature,record['goals'])):raise ValueError('aggregate public record omits or adds an actual per-run goal')
        write(out/'derived-native-census.json',{'scope':'Counts derived from every actual current run and normal native inventory/readers, never scripted62 or historical counts.',
            'runs':derived_run_census,'total_ordinary':sum(x['ordinary_goals']for x in derived_run_census),
            'total_smoke':sum(x['smoke_goals']for x in derived_run_census),'record_goal_count':len(record['goals']),
            'actual_record_goal_multiset_equal':True})
        binding=json.loads((out/'method-model-binding.json').read_bytes())
        if record['pins']['method_version']!=binding['method_version']:raise ValueError('normal method model-binding pin differs')
        typed=settings['vector_reallocation_typed_runtime']
        if typed['heap_model']!='Typed'or typed['integer_model']!='Machine':raise ValueError('qualified integer source image differs')
        if {Path(r['path']).name:r['sha256']for r in typed['sources']}!={r['name']:r['sha256']for r in expected['typed_machine_sources']}:
            raise ValueError('actual record does not pin all selected Typed/Machine sources')
        if record['pins']['code']['sha256']!=view['original_source']['sha256']:raise ValueError('qualified subject source differs')
        packets.check(expected['member'],canonical);output_budget();source_check();runtime_check()
        result.update(public_complete=True,record=pin(record_path),source_after_clean=True,
              targets=61,derived_native_census=pin(out/'derived-native-census.json'),ordinary_goals=sum(not g.get('smoke')for g in record['goals']),
              smoke_goals=sum(bool(g.get('smoke'))for g in record['goals']),
              model_proof_acceptance=False,classification='public producer reports proven; independent complete task/hypothesis/resource/source cold review remains mandatory')
    except Exception as exc:result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        result['elapsed_seconds']=time.monotonic()-started;result['within_whole_budget']=time.monotonic()<=deadline
        write(out/'result.json',result)
        write(out/'artifact-manifest.json',[{'relative':str(p.relative_to(out)),**pin(p)}for p in sorted(out.rglob('*'))if p.is_file()and p not in {out/'artifact-manifest.json'}])
    return 0 if result['public_complete']and result['within_whole_budget']else 1

if __name__=='__main__':raise SystemExit(main())
