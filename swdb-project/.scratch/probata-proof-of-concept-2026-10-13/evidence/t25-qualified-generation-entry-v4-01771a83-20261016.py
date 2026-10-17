"""INERT WP/Why3 generation-only component, 2026-10-16 ET.

Root admission and counted-verifier ownership are mandatory. One source-backed
qualified check lemma is imported/compiled, with no solver or proof promotion.
"""
import argparse,hashlib,json,os,re,shutil,subprocess,sys,time
from pathlib import Path
EXPECTED_SHA256='866a8a3900722d86ae390e7f0e91cdb6e6b9d02524303e51777f7bc9008e7493'
TOKEN='SWDB_VERIFIER_RUN_TOKEN'

def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):return sha(Path(path).read_bytes())
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
def check_pin(row):
    p=Path(row['path'])
    if row.get('absent'):
        if p.exists() or p.is_symlink():raise ValueError('previously absent config appeared: '+str(p))
    elif str(p.resolve())!=row['resolved'] or digest(p)!=row['sha256']:
        raise ValueError('physical pin mismatch: '+str(p))
def check_tree(tree,kind):
    root=Path(tree['path'])
    if root.is_symlink() or not root.is_dir():raise ValueError('tree root changed')
    found=set()
    for p in root.rglob('*'):
        if p.is_symlink() or (not p.is_file() and not p.is_dir()):raise ValueError('nonregular tree input: '+str(p))
        selected=(kind=='full' or (kind=='compiled' and (p.suffix in {'.cmi','.cmx','.cmxa','.cmxs','.a'} or p.name=='META')) or
                  (kind=='psutil' and p.suffix in {'.py','.so'}))
        if p.is_file() and selected:found.add(str(p.relative_to(root)))
    if found!={r['relative'] for r in tree['files']}:raise ValueError('tree membership changed: '+str(root))
    for row in tree['files']:check_pin(row)
def verify_runtime(runtime):
    for row in [*runtime['tools'].values(),runtime['python'],*runtime['toolchain_artifacts'],
                *runtime['configuration_files'],*runtime['native_closure'],*runtime['primary_sources']]:check_pin(row)
    for tree in runtime['package_surfaces']:check_tree(tree,'compiled')
    check_tree(runtime['standard_headers'],'full');check_tree(runtime['psutil_surface'],'psutil')
    for key in ('why3_stdlib','wp_why3_support','why3_drivers'):check_tree(runtime[key],'full')

def generation_inventory(inventory,log,selected):
    if inventory.get('complete') is not True or inventory.get('version')!='1':raise ValueError('incomplete production inventory')
    goals=inventory.get('goals');properties=inventory.get('properties')
    if not isinstance(goals,list) or not goals or not isinstance(properties,list) or not properties:raise ValueError('empty goal/property inventory')
    ids=[r.get('goal') for r in goals]
    if any(not isinstance(x,str) or not x for x in ids) or len(ids)!=len(set(ids)):
        raise ValueError('missing or duplicate goal identities')
    # Frama-C's exact IPModule property has no propositional name. It is retained
    # as metadata, never treated as an assumption or silently discarded goal.
    module_properties=[r for r in properties if r.get('property')=='']
    exact_module={'property':'','function':None,'kind':'other','emitter':'','origin':None,
                  'dependencies':[],'extern':False,'generated_smoke_failure':False,'line':0,
                  'description':'module heap_reallocation::Heap'}
    if len(module_properties)!=1 or {**module_properties[0],
            'description':' '.join(module_properties[0].get('description','').split())}!=exact_module:
        raise ValueError('only the exact source-import IPModule metadata row may have an empty identity')
    lemma_properties=[r for r in properties if r.get('property')!='']
    if len(properties)!=2 or len(lemma_properties)!=1:raise ValueError('one module metadata row and selected check lemma required')
    properties_all=properties
    properties=lemma_properties
    prop=properties[0];identity=prop['property']
    if identity!=selected['goal'] and not identity.endswith('_'+selected['goal']):raise ValueError('selected check lemma identity missing')
    if prop.get('kind')!='lemma' or prop.get('function') is not None or prop.get('extern') is not False:
        raise ValueError('unattributed or externally assumed check lemma')
    if prop.get('dependencies')!=[] or prop.get('origin') is not None:raise ValueError('current/future property dependency not permitted')
    if ' '.join(prop.get('description','').split())!='check lemma '+selected['goal']:raise ValueError('not the exact source check lemma')
    for row in goals:
        if row.get('property')!=identity or row.get('function') is not None or row.get('smoke') is not False or row.get('targets')!=[]:
            raise ValueError('unattributed extra ordinary/smoke obligation')
        if row.get('passed') is not False or row.get('results') not in ([],['untried']):
            raise ValueError('generation must not accept a solver or proof result')
    exports=re.findall(r'\bEXPORT GOAL\s+(\S+)',log)
    if len(exports)!=1 or not (exports[0]==selected['goal'] or exports[0].endswith('_'+selected['goal'])):
        raise ValueError('one attributable actual Why3 export is mandatory')
    if len(re.findall(r'\bgoal\s+wp_goal\b',log))!=1:raise ValueError('full printed Why3 task missing or ambiguous')
    if '[report] Computing properties status' not in log:raise ValueError('final property report marker missing')
    if re.search(r'\b(?:User Error|Fatal error|Frama-C aborted|Compilation Error|Why3 Error)\b',log,re.I):
        raise ValueError('import/type/generation diagnostic failure')
    return {'goals':goals,'properties':properties_all,'module_properties':module_properties,'exports':exports,'ordinary':len(goals),'smoke':0,
            'generated_smoke_applicability':'global check lemma; none generated, no caller reachability claim',
            'proof_acceptance':False,'generation_only':True,'verdict_boundary':'not_proven; no solver called',
            'cold_import_hypothesis_closure_pending':True}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected',type=Path,required=True)
    parser.add_argument('--checkout',type=Path,required=True)
    args=parser.parse_args()
    if digest(args.expected)!=EXPECTED_SHA256:raise ValueError('reviewed expected recipe mismatch')
    expected=json.loads(args.expected.read_bytes());runtime=expected['runtime']
    if Path(sys.executable).resolve()!=Path(runtime['python']['resolved']):raise ValueError('selected Python changed')
    forbidden=sorted(k for k in os.environ if k.startswith(('FRAMAC_WP','WP_','DYLD_')) or k in
                     {'OCAMLPATH','OCAMLFIND_CONF','CAML_LD_LIBRARY_PATH','WHY3LIB','WHY3DATA','WHY3LOADPATH','SWDB_PROOF_REPORT_OUT'})
    if forbidden:raise ValueError('forbidden ambient names: '+','.join(forbidden))
    token=os.environ.get(TOKEN)
    if not token:raise ValueError('counted-verifier lease token missing')
    output=Path(expected['output']);checkout=args.checkout.resolve()
    if output.exists() or output.is_relative_to(checkout):raise ValueError('fresh external output required')
    output.mkdir(parents=True);started=time.monotonic();deadline=started+300
    state={'source_commit':expected['source_commit'],'selected_id':expected['selected']['id'],
           'generation_completed':False,'proof_acceptance':False,'body_proof':False,'caller_acceptance':False,
           'original_v2_acceptance':False,'solver_invocation_permitted':False,'forbidden_ambient_names':forbidden,
           'source_preparation_formal_tools':'disabled by SWDB_FRAMA_C=none and SWDB_CBMC=none during pure canonical reconstruction'}
    commands=[];(output/'tmp').mkdir()
    prefix=Path(runtime['tools']['frama-c']['path']).parent
    env={'HOME':'/Users/yanrujhou','PATH':str(prefix)+':/opt/homebrew/bin:/usr/bin:/bin',
         'TMPDIR':str(output/'tmp'),'PYTHONDONTWRITEBYTECODE':'1',TOKEN:token,
         'WHY3CONFIG':str(output/'why3.conf')}
    opam=[runtime['tools']['opam']['path'],'exec','--switch=framac-33','--']
    def budget():
        paths=list(output.rglob('*'))
        if any(p.is_symlink() or not(p.is_file() or p.is_dir()) for p in paths):raise ValueError('nonregular component output')
        if sum(p.stat().st_size for p in paths if p.is_file())>expected['resource_policy']['output_budget_bytes']:
            raise ValueError('component output budget exceeded')
        if Path(expected['sentinel']['marker']).exists():raise ValueError('FORBIDDEN prover sentinel invoked')
    def run(argv,label,cwd=output,child_env=None):
        budget();remaining=deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('internal deadline before '+label)
        commands.append({'label':label,'argv':argv,'cwd':str(cwd)});write(output/'commands.json',commands)
        with (output/(label+'.log')).open('wb') as log:
            done=subprocess.run(argv,cwd=cwd,env=child_env or env,stdout=log,stderr=subprocess.STDOUT,timeout=remaining,check=False)
        budget()
        if done.returncode:raise ValueError(label+' exited '+str(done.returncode))
        return (output/(label+'.log')).read_bytes()
    def git(*argv):
        return subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(checkout),*argv],timeout=30)
    def verify_staged(source):
        found={str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()}
        if found!={r['relative'] for r in expected['source_blobs']}:raise ValueError('staged source membership changed')
        for row in expected['source_blobs']:
            if digest(source/row['relative'])!=row['sha256']:raise ValueError('staged source changed')
    try:
        verify_runtime(runtime)
        shutil.copyfile(args.expected,output/'expected.json');shutil.copyfile(__file__,output/'entry.py')
        tip=git('rev-parse','--verify',expected['publication_ref']).decode().strip()
        if subprocess.run(['/usr/bin/git','--no-replace-objects','-C',str(checkout),'merge-base','--is-ancestor',expected['source_commit'],tip],timeout=30).returncode:
            raise ValueError('exact017 is not published integration ancestor')
        state['published_tip']=tip
        source=output/'source';(source/'swdb').mkdir(parents=True)
        rows=git('ls-tree','-r',expected['source_commit'],'--','swdb-project/swdb').decode().splitlines()
        if any(not row.startswith('100644 blob ') for row in rows):raise ValueError('unexpected source Git mode')
        if {r.split('\t',1)[1] for r in rows}!={r['path'] for r in expected['source_blobs']}:raise ValueError('Git package membership differs')
        for row in expected['source_blobs']:
            ident=git('rev-parse','--verify',expected['source_commit']+':'+row['path']).decode().strip()
            data=git('cat-file','blob',ident)
            if ident!=row['blob'] or sha(data)!=row['sha256']:raise ValueError('Git blob binding changed')
            p=source/row['relative'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        verify_staged(source)
        os.environ['SWDB_FRAMA_C']='none';os.environ['SWDB_CBMC']='none';sys.dont_write_bytecode=True
        sys.path.insert(0,str(source))
        from swdb import vector_reallocation_vcs as packets
        inputs=output/'inputs';manifest=packets.prepare('std_vector_int_realloc_v3_grow',inputs)
        if packets.check('std_vector_int_realloc_v3_grow',inputs)!=manifest:raise ValueError('canonical reconstruction failed')
        if digest(inputs/'manifest.json')!=expected['manifest_sha256'] or len(manifest['obligations'])!=20:raise ValueError('canonical20 manifest changed')
        selected,=[r for r in manifest['obligations'] if r['id']=='grow.entry.int_projection']
        if selected!=expected['selected'] or selected['dependencies']!=[]:raise ValueError('selected independent lemma changed')
        packet=inputs/selected['path']
        if digest(packet)!=expected['selected_packet_sha256'] or 'Heap::int_values values' not in packet.read_text():raise ValueError('int_values alias packet changed')
        for name,key in [('why3.conf','fresh_config'),('prover-sentinel.py','sentinel')]:
            data=expected[key]['bytes_utf8'].encode()
            if sha(data)!=expected[key]['sha256']:raise ValueError('recipe byte hash inconsistent')
            (output/name).write_bytes(data)
        bindings={}
        for package,wanted in runtime['package_bindings'].items():
            got=run([*opam,runtime['tools']['ocamlfind']['path'],'query','-format','%d',package],'query-'+package).decode().strip()
            if got!=wanted:raise ValueError('OCaml selected package binding differs: '+package)
            bindings[package]=got
        state['package_bindings']=bindings
        shutil.copyfile(source/'swdb/proof_report.ml',output/'proof_report.ml')
        run([*opam,runtime['tools']['ocamlfind']['path'],'ocamlopt','-shared','-linkall','-package',
             'frama-c.kernel,frama-c-wp.core','-o','proof_report.cmxs','proof_report.ml'],'report-compile')
        job=output/'lemma';job.mkdir();shutil.copyfile(packet,job/'wp_input.c')
        diagnostic=expected['diagnostic_flags']
        command=[*opam,runtime['tools']['frama-c']['path'],'-machdep','x86_64','-kernel-warn-key','annot-error=abort',
                 '-wp-library',str(inputs/'theory'),'-wp-msg-key',diagnostic,'wp_input.c','-print','-ocode','normalized.c','-then',
                 '-machdep','x86_64','-wp','-wp-rte','-rte-initialized','@all','-wp-no-filter-init','-wp-cache','none',
                 '-wp-smoke-tests','-wp-par','1','-wp-timeout','10',*expected['generation_flags'],'-wp-status-all',
                 '-wp-library',str(inputs/'theory'),'-wp-out','prover-files','-wp-print','-wp-msg-key',diagnostic,
                 '-wp-report-json','wp-native-goals.json','-then','-load-module',str(output/'proof_report.cmxs'),
                 '-report','-report-untried','-report-csv','wp-properties.csv']
        state['command']=command;write(output/'result.json',state)
        log=run(command,'frama-generation',job,{**env,'SWDB_PROOF_REPORT_OUT':str(job/'wp-inventory.json')}).decode('utf-8',errors='strict')
        required=['wp-inventory.json','wp-properties.csv','normalized.c']
        if any(not(job/name).is_file() for name in required):raise ValueError('complete generation artifacts missing')
        inventory=json.loads((job/'wp-inventory.json').read_bytes())
        census=generation_inventory(inventory,log,selected)
        write(job/'generation-census.json',census)
        warnings=[{'line':i+1,'text':line} for i,line in enumerate(log.splitlines()) if re.search(r'\bwarning\b',line,re.I)]
        known=[r for r in warnings if re.search(r'\bunused variable dummy\s*$',r['text'])]
        unknown=[r for r in warnings if r not in known]
        write(job/'warning-census.json',{'all':warnings,'known_unused_dummy':known,'unclassified':unknown,'full_multiline_context':'frama-generation.log retained byte-for-byte'})
        # Task text is genuinely generated by WP/Why3, not copied from the packet.
        (job/'why3-task-diagnostics.txt').write_text(log)
        taskbinding={'source_commit':expected['source_commit'],'selected_packet':selected,
                     'input_sha256':digest(job/'wp_input.c'),'theory_sha256':digest(inputs/'theory/heap_reallocation.mlw'),
                     'manifest_sha256':digest(inputs/'manifest.json'),'generated_diagnostics_sha256':digest(job/'why3-task-diagnostics.txt'),
                     'inventory_sha256':digest(job/'wp-inventory.json'),'normalized_sha256':digest(job/'normalized.c'),
                     'config_sha256':digest(output/'why3.conf'),'sentinel_sha256':digest(output/'prover-sentinel.py'),
                     'no_solver_marker':not Path(expected['sentinel']['marker']).exists(),'fresh_reader_sha256':digest(output/'proof_report.cmxs'),
                     'physical_task_file_claim':False,'cold_import_hypothesis_closure_pending':True,'proof_acceptance':False}
        write(job/'task-source-binding.json',taskbinding)
        if unknown:raise ValueError('unclassified generation warning; cold inspection required')
        if digest(job/'wp_input.c')!=selected['sha256']:raise ValueError('selected input changed')
        if digest(output/'why3.conf')!=expected['fresh_config']['sha256'] or digest(output/'prover-sentinel.py')!=expected['sentinel']['sha256']:
            raise ValueError('fresh config or sentinel bytes changed')
        packets.check('std_vector_int_realloc_v3_grow',inputs);verify_staged(source);verify_runtime(runtime);budget()
        state.update(generation_completed=True,goal_count=len(census['goals']),property_count=len(census['properties']),
                     no_solver_marker=True,canonical_packet_count=20,selected_packet_count=1,
                     native_report_present=(job/'wp-native-goals.json').is_file(),cold_import_hypothesis_closure_pending=True,
                     scope='Qualified projection WP import and Why3 task generation only; not_proven. No original v2 body/caller or complete grow proof.')
    except Exception as exc:
        state.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        state['elapsed_seconds']=time.monotonic()-started
        state['within_internal_seconds']=state['elapsed_seconds']<=300
        state['sentinel_invoked']=Path(expected['sentinel']['marker']).exists()
        files=[{'relative':str(p.relative_to(output)),'sha256':digest(p),'bytes':p.stat().st_size}
               for p in sorted(output.rglob('*')) if p.is_file() and p not in {output/'result.json',output/'artifact-manifest.json'}]
        write(output/'artifact-manifest.json',files);write(output/'result.json',state)
    return 0 if state['generation_completed'] and state['within_internal_seconds'] and not state['sentinel_invoked'] else 1

if __name__=='__main__':raise SystemExit(main())
