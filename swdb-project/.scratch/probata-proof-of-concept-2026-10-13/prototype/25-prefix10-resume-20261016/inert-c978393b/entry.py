"""INERT ten isolated copy-step diagnostics,2026-10-16 ET. Root admission only.

No certificate filtering, public model record, assumed sibling/desired law,
old proof promotion or complete-body verdict. All61 canonical inputs remain
checked; ten explicit rows get the ordinary per-leaf prelaunch and reader.
"""
import argparse,dataclasses,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
EXPECTED_SHA256='7066731f62e2e1273b001f599728d5127611252982702d89dfa6204c2af1adfd'

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

def source_lemma_ownership(row,outcome,inventory):
    """Same successful check-lemma census as heap_model_view.prove; no new law."""
    if outcome['verdict'] != 'proven':
        return
    ordinary=[g for g in outcome['goals'] if not g.get('smoke')]
    lemmas=[p for p in inventory['properties'] if p.get('kind') == 'lemma']
    if len(lemmas) != 1 or lemmas[0].get('dependencies') or lemmas[0].get('extern') or \
            not lemmas[0]['property'].endswith('_'+row['goal']) or \
            any(g.get('property') != lemmas[0]['property'] for g in ordinary):
        raise ValueError('the fresh global proof is not owned by the sole source-mapped check lemma')
    if not ordinary:
        raise ValueError('the source-mapped proof generated no ordinary obligation')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected',required=True,type=Path)
    parser.add_argument('--project',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if sha(args.expected)!=EXPECTED_SHA256:raise ValueError('reviewed diagnostic expectation differs')
    expected=json.loads(args.expected.read_bytes());policy=expected['resource_policy']
    project=args.project.resolve();repo=project.parent;out=args.output.resolve()
    if out.exists()or out.is_relative_to(repo):raise ValueError('fresh external diagnostic output required')
    launch=linux_admission(expected,repo,out)
    out.mkdir(parents=True);os.chdir(project);started=time.monotonic();deadline=started+policy['profile_seconds']
    result={'scope':expected['scope'],'source_commit':expected['source_commit'],'diagnostic_complete':False,
            'model_acceptance':False,'caller_acceptance':False,'original_v2_acceptance':False,'ticket_closure':False,
            'public_proof_record_created':False,'selected_ids':expected['diagnostic_ids'],'runs':[],
            'complete_model_verdict':'not_attempted','model_target_count':61,
            'unexecuted_model_targets':[ident for ident in expected['target_ids']if ident not in expected['diagnostic_ids']],
            'unexecuted':list(expected['diagnostic_ids']),'linux_launch':launch,'source_receipts':[]}
    def remaining():
        value=deadline-time.monotonic()
        if value<=0:raise TimeoutError('whole diagnostic profile budget spent')
        return value
    def source_check():
        head=subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(repo),'rev-parse','HEAD'],text=True,timeout=30).strip()
        dirty=subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(repo),'status','--porcelain','--untracked-files=all'],text=True,timeout=30)
        if head!=expected['source_commit']or dirty:raise ValueError('exact diagnostic source is not clean')
        for row in expected['source_blobs']:
            if sha(project/row['relative'])!=row['sha256']:raise ValueError('diagnostic package source differs')
        for row in expected['test_helper_pins']:
            if sha(project/row['relative'])!=row['sha256']:raise ValueError('unchanged public-seed helper differs')
        closure=consumer_closure(project,repo,expected);p=out/('source-consumers-'+str(len(result['source_receipts']))+'.json')
        write(p,closure);result['source_receipts'].append(pin(p))
    def runtime_check():
        selected={}
        for name,row in expected['tools'].items():
            p=shutil.which(name)
            if p is None or Path(p).resolve()!=Path(row['path']).resolve()or sha(p)!=row['sha256']:raise ValueError('selected tool differs: '+name)
            selected[name]=pin(Path(p).resolve())
        for row in expected['wp_artifacts']:
            if sha(row['path'])!=row['sha256']:raise ValueError('selected WP native/META differs')
        prefix=Path(expected['linux_prefix'])
        for key,root in [('why3_stdlib',prefix/'share/why3/stdlib'),('wp_why3_support',prefix/'share/frama-c/share/wp/why3'),('why3_drivers',prefix/'share/why3/drivers')]:surface(root,expected['portable_import_surfaces'][key])
        for row in expected['typed_machine_sources']:
            if sha(prefix/'lib/frama-c-wp/core'/row['name'])!=row['sha256']:raise ValueError('selected Typed/Machine source differs')
        if sha(expected['why3_config']['path'])!=expected['why3_config']['sha256']:raise ValueError('selected Why3 config differs')
        return selected
    def budget():
        size=sum(p.stat().st_size for p in out.rglob('*')if p.is_file())
        if size>policy['output_budget_bytes']:raise ValueError('planned diagnostic raw allowance exceeded')
        return size
    try:
        source_check();ambient=sorted(k for k in os.environ if k.startswith(('FRAMAC_WP','WP_'))or k=='SWDB_PROOF_REPORT_OUT')
        if ambient:raise ValueError('forbidden ambient WP names: '+','.join(ambient))
        result['ambient_wp_names']=ambient;write(out/'runtime.json',runtime_check())
        shutil.copyfile(__file__,out/'entry.py');shutil.copyfile(args.expected,out/'expected.json')
        os.environ.update(SWDB_FRAMA_C=expected['tools']['frama-c']['path'],SWDB_CBMC='none',SWDB_OCAMLFIND=expected['tools']['ocamlfind']['path'],WHY3CONFIG=expected['why3_config']['path'],SWDB_WHY3_CONFIG=expected['why3_config']['path'],PYTHONDONTWRITEBYTECODE='1',SWDB_FIXTURE_HOST='swdb-fixture-host',SWDB_VERIFIER_RSS_CAP_BYTES=str(policy['cap_bytes']))
        sys.dont_write_bytecode=True;sys.path[:0]=[str(project),str(project/'tests')]
        from swdb import vector_reallocation_vcs as packets,vector_reallocation_view as qualified
        from swdb import heap_model_view as engine,proof_setup,proof,wp_adapter,c_lowering,stdlib_provenance,framac,method_version,rss_watchdog
        from swdb.library import Library
        inputs=out/'canonical-inputs';view=qualified.prepare(expected['member'],inputs)
        manifest=packets.check(expected['member'],inputs)
        if sha(inputs/'manifest.json')!=expected['canonical_manifest_sha256']or manifest['model']!=expected['model']:raise ValueError('canonical complete61 manifest/model differs')
        if len(manifest['obligations'])!=61 or [r['id']for r in manifest['obligations']]!=expected['target_ids']:raise ValueError('full61 inventory differs')
        if manifest['logical_obligations']!=expected['logical_obligations']:raise ValueError('exact logical AND/source-definition receipt differs')
        physical=[{'path':str(p.relative_to(inputs)),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(inputs.rglob('*'))if p.is_file()]
        if physical!=expected['canonical_files'] or manifest['typed_source_image']!=expected['typed_source_image']:raise ValueError('complete canonical payload/reference/source-image bytes differ')
        selected=[r for r in manifest['obligations']if r['id']in expected['diagnostic_ids']]
        if len(selected)!=10 or [r['id']for r in selected]!=expected['diagnostic_ids']or any(r['dependencies']or r['kind']!='check_lemma'or r['expected']!='proven'for r in selected):raise ValueError('exact10independent component selection differs')
        write(out/'canonical-precheck.json',{'manifest':pin(inputs/'manifest.json'),'full_targets':61,'diagnostic_targets':10,'selected':selected,'logical_obligations':manifest['logical_obligations'],'old_proofs_imported':0,'certificate_filtered':False})
        compiler=stdlib_provenance.runtime_identity(c_lowering.locate());lowering=c_lowering.identity()
        if {k:compiler[k]for k in expected['linux_clang_components']}!=expected['linux_clang_components']:raise ValueError('selected Linux compiler components differ')
        if str(project)!=expected['remote_project'] or compiler!=expected['linux_project_identity_derivation']['runtime'] or lowering!=expected['linux_project_identity_derivation']['predicted_identity']:raise ValueError('fresh source/context compiler runtime composite differs from prospective reconstruction')
        write(out/'compiler-runtime.json',{'runtime':compiler,'identity':lowering})
        from test_standard_member_contracts import _member_seed
        seed=initialize_workspace(out,_member_seed)
        import yaml
        method_dir=seed.root/'library/methods';inherited=method_dir/'wp-tracer-fixture.yaml';data=yaml.safe_load(inherited.read_bytes())
        if data['c_lowering']['translators']!=[lowering['c_lowering']]:raise ValueError('seed compiler context differs')
        data.update(id=expected['method_id'],sequence=3,description='Ten isolated copy-step diagnostics; full61 canonical receipt, no full model verdict. '+json.dumps(expected['explicit_method_binding'],sort_keys=True))
        method_path=method_dir/'wp-copy-prefix10-diagnostic-v1.yaml';method_path.write_text(yaml.safe_dump(data,sort_keys=False))
        method=method_version.select(seed.root/'library',expected['method_id']);adapter=wp_adapter.WpAdapter(Library(seed.root/'library'),proof.MODEL_PREFIX+expected['member'],method,records=seed.records)
        tools=adapter._tools();flags=engine.flags(tools)
        if tools['seconds']!=30 or tools['provers']!=['alt-ergo','z3','cvc5']:raise ValueError('unchanged complete three-solver thirty-second portfolio required')
        if '-wp-prop'in flags or '-wp-gen'in flags or '-wp-no-why3-detect'in flags:raise ValueError('diagnostic changed complete proof portfolio/selection')
        write(out/'method.json',{'pin':method_version.pin(method),'method':data,'flags':flags,'tools':tools})
        model_sha=view.certificate['original_source']['sha256']
        job=proof.Job(proof.ProofUnit('diagnostic.'+expected['member'],expected['member'],str(inputs/'qualified.c'),model_sha,proof.MODEL_PREFIX+expected['member'],model_sha),scratch=out,log=out/'diagnostic.log',budget_seconds=policy['profile_seconds'])
        proof_setup.begin(job,adapter,{'method_version':method_version.pin(method)},method)
        report_dir=out/'reader';report_dir.mkdir();reader=proof_setup.compile_report_module(report_dir,timeout=min(120,remaining()))
        foundation=engine.foundations(framac.locate().command,out/'foundation',deadline)
        typed=qualified.typed_runtime(foundation,flags)
        write(out/'foundation.json',foundation);write(out/'typed-runtime.json',typed)
        certificate=out/'heap-model-view.json';certificate.write_text(engine.certificate_text(view))
        context={'job':job,'wp_dir':out,'log':wp_adapter._Log(job.log),'reports':[],'tools':tools,'functions':{expected['member']},'extra_flags':[],'pins':dict(view.pins),'started_monotonic':started,
                 'settings':{'flags':flags,'heap_model_view':view.certificate,'heap_model_foundations':foundation,'vector_reallocation_typed_runtime':typed}}
        context['pins']['heap_model_foundations']={'id':'heap-model-standard-foundations-1','sha256':engine._digest(foundation['sources'])}
        state={'view':view,'inputs':inputs,'certificate_path':certificate,'foundation':foundation,'report_module':reader,'tool_command':framac.locate().command,'why3_config':dict(expected['why3_config']),'deadline':deadline};context['heap_model_view']=state
        for row in selected:
            remaining();qualified.check(expected['member'],view,inputs);runtime_check()
            directory=out/('leaf-'+row['id']);directory.mkdir();(directory/'tmp').mkdir();text=(inputs/row['path']).read_text();path=directory/'wp_input.c';path.write_text(text)
            state['row']=row;command=engine.command(state['tool_command'],flags,inputs,reader)
            proof_setup.check_generated(job,adapter,context,[(path,text),(certificate,engine.certificate_text(view))],flags,command=command,scratch=directory)
            timeout=min(policy['leaf_timeout_seconds'],remaining());write(directory/'command.json',{'argv':command,'timeout_seconds':timeout,'cwd':str(directory),'input':pin(path),'selected_id':row['id']})
            env={**os.environ,'TMPDIR':str(directory/'tmp'),'SWDB_PROOF_REPORT_OUT':str(directory/'wp-inventory.json')}
            ran=rss_watchdog.run(command,log=directory/'frama-c.log',cwd=directory,env=env,cap_bytes=policy['cap_bytes'],timeout=timeout)
            write(directory/'resources.json',dataclasses.asdict(ran))
            outcome=wp_adapter.read_outcome(ran,(directory/'frama-c.log').read_text(errors='replace'),directory/'wp-goals.json'if(directory/'wp-goals.json').exists()else None,directory/'wp-properties.csv'if(directory/'wp-properties.csv').exists()else None,inventory=directory/'wp-inventory.json'if(directory/'wp-inventory.json').exists()else None)
            write(directory/'outcome.json',outcome)
            inventory=json.loads((directory/'wp-inventory.json').read_text()) if outcome['verdict']=='proven' else {}
            source_lemma_ownership(row,outcome,inventory)
            result['runs'].append({'id':row['id'],'input':pin(path),'resources':dataclasses.asdict(ran),'outcome':outcome,'cwd':str(directory)})
            result['unexecuted'].remove(row['id']);write(out/'result.json',result);write(out/'setup.json',job.setup['report']);budget()
            if ran.out_of_memory or ran.timed_out:raise ValueError('diagnostic leaf resource boundary hit; preserve partial')
        source_check();runtime_check();qualified.check(expected['member'],view,inputs)
        if list((seed.records/'proofs').glob('*.yaml')):raise ValueError('diagnostic unexpectedly produced public proof record')
        result.update(diagnostic_complete=True,all_ten_producer_proven=all(r['outcome']['verdict']=='proven'for r in result['runs']),source_after_clean=True,raw_bytes=budget(),classification='Complete ten-leaf producer diagnostics; independent task/hypothesis cold review pending. No full61 model, original-v2, caller or ticket acceptance.')
    except Exception as exc:result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        result['elapsed_seconds']=time.monotonic()-started;result['within_profile_budget']=time.monotonic()<=deadline;write(out/'result.json',result)
        write(out/'artifact-manifest.json',[{'relative':str(p.relative_to(out)),**pin(p)}for p in sorted(out.rglob('*'))if p.is_file()and p!=out/'artifact-manifest.json'])
    return 0 if result['diagnostic_complete']and result['within_profile_budget']else 1
if __name__=='__main__':raise SystemExit(main())
