"""2026-10-16 ET. Passive mathematical9 cold audit; stdlib/read-only Git only.
No project import, tool/config/version probe, native execution or raw payload transfer.
"""
import ast,csv,hashlib,io,itertools,json,re,signal,subprocess,time
from collections import Counter
from pathlib import Path
RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-f918f5d5-t25-private-frame9-public-v1')
PROFILE=RAW/'private-frame9-public-v1-profile'
SOURCE=Path('/data1/yanruj/probata-resume-20261016-f918f5d5')
COMMIT='f918f5d52035fd99499280a0a8058efd0ed4ef55'
ENTRY_SHA='7d1721e2e138dd7424e3a8aba8679609cfe7ea7e20b1783434a77d5ede28faa4'
EXPECTED_SHA='6132a9f3da7dbeeae3a4807564b22650a7805134cf13653735c17c896f5a27d4'
COMMAND_SHA='c95e047e7aa333df0c73d87404fd4213a642922cd2b8a0c6662fbc41e049da08'
CHECKS=[]

def require(value, label):
    if not value:
        raise ValueError(label)
    CHECKS.append(label)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def pin(path):
    path = Path(path)
    before = path.stat()
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    after = path.stat()
    require((before.st_size, before.st_mtime_ns, before.st_ino) ==
            (after.st_size, after.st_mtime_ns, after.st_ino), 'stable read ' + str(path))
    return {'path': str(path), 'bytes': before.st_size, 'sha256': h.hexdigest()}


def read(path):
    return json.loads(Path(path).read_bytes())


def git(*args, input=None):
    return subprocess.check_output(['/usr/bin/git', '--no-replace-objects', '-C', str(SOURCE), *args],
                                   input=input, timeout=30)


def snapshot(root):
    result = []
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink() and (path.is_file() or path.is_dir()), 'regular raw input ' + str(path))
        if path.is_file():
            result.append({'relative': str(path.relative_to(root)), **pin(path)})
    return result


def forms(text):
    lex = re.compile(r'\s+|;[^\n]*|"(?:[^"]|"")*"|\|[^|]*\||[()]|[^\s()]+')
    stack = [[]]
    position = 0
    for match in lex.finditer(text):
        require(match.start() == position, 'SMT token coverage')
        position = match.end()
        token = match[0]
        if token.isspace() or token.startswith(';'):
            continue
        if token == '(':
            item = []
            stack[-1].append(item)
            stack.append(item)
        elif token == ')':
            require(len(stack) > 1, 'balanced SMT close')
            stack.pop()
        else:
            stack[-1].append(token)
    require(position == len(text) and len(stack) == 1, 'complete SMT parse')
    return stack[0]


def expand(value, env=None):
    env = {} if env is None else env
    if isinstance(value, str):
        return env.get(value, value)
    if value and value[0] == 'let':
        additions = {name: expand(body, env) for name, body in value[1]}
        return expand(value[2], {**env, **additions})
    return [expand(x, env) for x in value]


def strip_comments(text):
    output = []
    i = depth = 0
    while i < len(text):
        if text.startswith('(*', i) and not text.startswith('(*)', i):
            depth += 1
            i += 2
        elif depth and text.startswith('*)', i):
            depth -= 1
            require(depth >= 0, 'Why3 balanced comment')
            i += 2
        else:
            if not depth:
                output.append(text[i])
            i += 1
    require(depth == 0, 'Why3 complete comments')
    return ''.join(output)


def canon(value, env=None, depth=0):
    """Alpha/order normalization only; no use of a prover or theorem result."""
    env={} if env is None else env
    if isinstance(value,str):
        return env.get(value,value)
    if not value:
        return []
    if value[0]=='let':
        return canon(expand(value),env,depth)
    head=value[0]
    if head in ('forall','exists'):
        bindings=list(value[1]); body=value[2]
        while isinstance(body,list) and body and body[0]==head:
            bindings+=body[1];body=body[2]
        groups={}
        for name,typ in bindings:
            groups.setdefault(json.dumps(typ,sort_keys=True),[]).append(name)
        keys=sorted(groups); options=[]
        for key in keys:
            options.append(list(itertools.permutations(groups[key])))
        candidates=[]
        for choices in itertools.product(*options):
            names={name:'@%s:%s:%s'%(depth,key,i) for key,choice in zip(keys,choices)
                   for i,name in enumerate(choice)}
            candidates.append(canon(body,{**env,**names},depth+1))
        return [head,[(key,len(groups[key])) for key in keys],
                min(candidates,key=lambda x:json.dumps(x,sort_keys=True))]
    args=[canon(v,env,depth) for v in value[1:]]
    if head in ('and','or','+','*'):
        flat=[]
        for v in args:
            flat.extend(v[1:] if isinstance(v,list) and v and v[0]==head else [v])
        args=sorted(flat,key=lambda x:json.dumps(x,sort_keys=True))
    if head=='=':
        args.sort(key=lambda x:json.dumps(x,sort_keys=True))
    if head=='=>' and len(args)==2 and isinstance(args[1],list) and args[1][0]=='=>':
        return canon(['=>',['and',args[0],args[1][1]],args[1][2]])
    if head=='end_automatic':head='release'
    if head=='fresh_id':head='next'
    return [head,*args]


def source_goal(ident):
    # Independent transcription of the nine already reviewed source statements.
    bodies={
      'entry.reflexive':('(h heap)','(P_t25_private_frame h h)'),
      'automatic.frame':('(h heap) (width Int) (a Int)',
        '(=> (well_formed h) (and (P_t25_private_frame h (begin_automatic h width a)) (not (live h (next h)))))'),
      'allocation.frame':('(entry heap) (now heap) (n Int) (a Int)',
        '(=> (and (well_formed now) (P_t25_private_frame entry now)) (and (P_t25_private_frame entry (allocate now n a)) (not (live entry (next now)))))'),
      'integer_store.frame':('(entry heap) (now heap) (b Int) (o Int) (v Int)',
        '(=> (and (P_t25_private_frame entry now) (not (live entry b))) (P_t25_private_frame entry (put_integer now b o v)))'),
      'pointer_store.frame':('(entry heap) (now heap) (b Int) (o Int) (target Int) (offset Int)',
        '(=> (and (P_t25_private_frame entry now) (not (live entry b))) (P_t25_private_frame entry (put_pointer now b o target offset)))'),
      'release.frame':('(entry heap) (now heap) (b Int)',
        '(=> (and (P_t25_private_frame entry now) (not (live entry b))) (P_t25_private_frame entry (release now b)))'),
      'automatic_end.frame':('(entry heap) (now heap) (r Int)',
        '(=> (and (P_t25_private_frame entry now) (not (live entry r))) (P_t25_private_frame entry (release now r)))'),
      'cleanup.observation':('(entry heap) (now heap) (r Int) (b Int)',
        '(=> (and (P_t25_private_frame entry now) (P_t25_private_ids entry r b)) (and (P_t25_private_frame entry (L_t25_private_cleanup now r b)) (P_t25_private_observes entry now (L_t25_private_cleanup now r b))))'),
      'cleanup.exists_scalar':('(entry heap) (now heap) (r Int) (b Int) (n Int)',
        '(=> (and (P_t25_private_frame entry now) (P_t25_private_ids entry r b) (typed_writes now r 0 24 8) (not (freeable now r 0)) (<= 0 n) (ite (= n 0) (= b 0) (and (freeable now b 0) (int32_region now b 0 n) (filled_prefix now b n 7)))) (exists ((final heap) (scalar Int)) (and (= final (L_t25_private_cleanup now r b)) (= scalar (ite (< 0 n) (load_int now b 0) 0)) (= scalar (ite (< 0 n) 7 0)) (P_t25_private_frame entry final) (P_t25_private_observes entry now final))))')}
    bindings,body=bodies[ident]
    return forms('(not (forall ('+bindings+') '+body+'))')[0]


SOURCE_DEFINITIONS={
 'P_t25_private_observes':('(entry heap) (left heap) (right heap)',
  '(and (forall ((b Int)) (=> (live entry b) (same_object left right b))) (forall ((b Int) (p Int)) (=> (live entry b) (and (= (contents left b p) (contents right b p)) (= (initialized_at left b p) (initialized_at right b p))))))'),
 'P_t25_private_frame':('(entry heap) (now heap)','(P_t25_private_observes entry entry now)'),
 'P_t25_private_ids':('(entry heap) (r Int) (b Int)','(and (not (live entry r)) (or (= b 0) (and (not (live entry b)) (not (= b r)))))'),
 'L_t25_private_cleanup':('(now heap) (r Int) (b Int)','(release (release now b) r)')}


def check_definitions(definitions,ident):
    selected=[d for d in definitions if d[1].startswith(('P_t25','L_t25'))]
    wanted=set(SOURCE_DEFINITIONS) if ident.startswith('cleanup.') else set(SOURCE_DEFINITIONS)-{'P_t25_private_ids','L_t25_private_cleanup'}
    require({d[1] for d in selected}==wanted,'complete selected source definitions '+ident)
    result={}
    for d in selected:
        bindings,body=SOURCE_DEFINITIONS[d[1]]
        expected=forms('(forall ('+bindings+') '+body+')')[0]
        actual=['forall',d[2],d[-1]]
        require(canon(actual)==canon(expected),'exact source definition '+ident+' '+d[1])
        result[d[1]]={'form_sha256':digest(d),'source_equivalent':True}
    return result


def main():
    signal.alarm(120);started=time.monotonic()
    initial = snapshot(RAW)
    expected = read(PROFILE / 'expected.json')
    require(pin(PROFILE / 'expected.json')['sha256'] == EXPECTED_SHA, 'reviewed expected bytes')
    for path in [RAW / 'private-frame9-public-v1-entry.py', PROFILE / 'entry.py']:
        require(pin(path)['sha256'] == ENTRY_SHA, 'reviewed entry bytes ' + str(path))
    require(expected['source_commit'] == COMMIT and expected['remote_project'] == str(SOURCE / 'swdb-project'), 'exact producer source/context')
    require(git('rev-parse', 'HEAD').decode().strip() == COMMIT and not git('status', '--porcelain', '--untracked-files=all'), 'live exact source clean')
    for row in expected['source_blobs'] + expected['test_helper_pins']:
        require(pin(SOURCE / 'swdb-project' / row['relative'])['sha256'] == row['sha256'], 'current source/helper ' + row['relative'])
    consumers = []
    for path in sorted(PROFILE.glob('source-consumers-*.json')):
        closure = read(path)
        for relative, row in closure['trees'].items():
            require(git('rev-parse', COMMIT + ':swdb-project/' + relative).decode().strip() == row['oid'], 'consumer selected Git root ' + relative)
        for row in closure['files']:
            got = pin(row['path'])
            require(got['sha256'] == row['sha256'] and got['bytes'] == row['bytes'], 'consumer current bytes ' + row['relative'])
        actual_oids = git('hash-object', '--no-filters', '--stdin-paths', input=''.join(r['path'] + '\n' for r in closure['files']).encode()).decode().splitlines()
        require(actual_oids == [r['git_blob'] for r in closure['files']], 'consumer current physical Git blobs')
        consumers.append({'receipt': pin(path), 'count': closure['count'], 'total_bytes': closure['total_bytes']})
    require(len(consumers) == 2 and read(PROFILE / 'source-consumers-0.json') == read(PROFILE / 'source-consumers-1.json'), 'before/after complete source consumers equal')
    runtime_pins = []
    for row in [*expected['tools'].values(), *expected['wp_artifacts'], expected['why3_config']]:
        got = pin(row['path'])
        require(got['sha256'] == row['sha256'], 'current installed tool/support/config ' + row['path'])
        runtime_pins.append(got)
    prefix = Path(expected['linux_prefix'])
    for key, root in [('why3_stdlib', prefix / 'share/why3/stdlib'), ('wp_why3_support', prefix / 'share/frama-c/share/wp/why3'), ('why3_drivers', prefix / 'share/why3/drivers')]:
        actual = []
        for path in sorted(root.rglob('*')):
            require(not path.is_symlink(), 'physical import root ' + str(path))
            if path.is_file():
                got = pin(path)
                runtime_pins.append(got)
                actual.append({'relative': str(path.relative_to(root)), 'sha256': got['sha256']})
        require(actual == expected['portable_import_surfaces'][key], 'full installed import surface ' + key)
    foundation = read(PROFILE / 'foundation.json')
    for row in foundation['sources']:
        require(pin(row['path'])['sha256'] == row['sha256'], 'current foundation/Typed source ' + row['path'])
    require(pin(foundation['metadata_executable'])['sha256'] == foundation['metadata_executable_sha256'], 'retained metadata executable posthash')
    require(read(PROFILE / 'compiler-runtime.json') == {'runtime': expected['linux_project_identity_derivation']['runtime'], 'identity': expected['linux_project_identity_derivation']['predicted_identity']}, 'actual project compiler context equals current prospective reconstruction')
    for row in [expected['linux_clang_components']['command_executable'], expected['linux_clang_components']['driver']]:
        require(pin(row['path'])['sha256'] == row['sha256'], 'current Clang physical bytes ' + row['path'])
    compiler_root = Path(expected['linux_clang_components']['driver']['path']).parent.parent
    resource_root = compiler_root / 'lib/clang/22'
    require(pin((compiler_root / 'lib/libclang.so').resolve())['sha256'] == expected['linux_clang_components']['parser']['sha256'], 'current matching libclang bytes')
    header_digest = hashlib.sha256()
    header_count = 0
    for label, root in [('libc++', compiler_root / 'include/c++/v1'), ('clang-resource', resource_root / 'include')]:
        for path in sorted(root.rglob('*')):
            if path.is_file():
                got = pin(path)
                header_digest.update(label.encode() + b'\0' + str(path.relative_to(root)).encode() + b'\0')
                header_digest.update(bytes.fromhex(got['sha256']))
                header_count += 1
    require({'id': 'llvm-standard-resource-headers', 'sha256': header_digest.hexdigest(), 'files': header_count} == expected['linux_clang_components']['headers'], 'complete current compiler resource/header identity')
    for row in expected['runtime_sources']:
        require(pin(prefix/'lib/frama-c-wp/core'/row['name'])['sha256']==row['sha256'],'physical runtime source '+row['name'])
    launch=read(RAW/'launch.json')
    require(digest(launch['command'])==COMMAND_SHA,'launch exact reviewed command after substitutions')
    require(launch['source_commit']==COMMIT and Path(launch['source'])==SOURCE and launch['timeout_seconds']==1500,'actual launch source/whole budget')
    for name,want in expected['linux_launch_binding']['wrappers'].items():
        require(pin(RAW/name)['sha256']==want==launch['reviewed_wrapper_reuse'][name],'exact reviewed wrapper '+name)
    guards={name:read(RAW/name) for name in ('resources.json','outer-resources.json')}
    for name,g in guards.items():
        require(g['exit_code']==0 and not g['out_of_memory'] and not g['timed_out'] and g['peak_rss_bytes']<=8589934592,'settled healthy guard '+name)
    lane=read(RAW/'lane.json')['socket_lane']
    require(lane['node']==1 and lane['lease_generation']==629 and lane['exit_code']==0 and lane['numa_memory_policy']=='bind:1' and lane.get('ended_utc')=='2026-10-16T18:10:09Z','settled node1 G629 lane')
    require(read(RAW/'source-after.json')=={'commit':COMMIT,'source_unchanged':True,'tracked_changes':''},'source-after exact clean')
    require('PYTHONPATH' not in read(RAW/'dispatch-environment.json'),'actual env removes outer PYTHONPATH')
    manifest=read(PROFILE/'canonical-inputs/manifest.json')
    require(manifest==expected['canonical_manifest'] and len(manifest['obligations'])==9,'canonical manifest exact nine duties')
    physical=[{'path':str(p.relative_to(PROFILE/'canonical-inputs')),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted((PROFILE/'canonical-inputs').rglob('*')) if p.is_file()]
    require(physical==expected['canonical_files'] and len(physical)==12,'canonical complete physical membership')
    result=read(PROFILE/'result.json')
    require(result['producer_complete'] and result['all_nine_producer_proven'] and result['within_profile_budget'] and result['source_after_clean'] and not result['unexecuted'] and not result.get('error'),'complete settled nine producer outcomes')
    require([r['id'] for r in result['runs']]==expected['target_ids'],'all nine source identities in exact order')
    for k in ['proof_acceptance','source_typed_bridge_established','body_acceptance','caller_acceptance','public_proof_record_created','universal_proof_setup_attested']:
        require(result[k] is False,'larger admission flag remains false '+k)
    require((PROFILE/'workspace/records').is_dir() and not list((PROFILE/'workspace/records/proofs').glob('*.yaml')),'no standalone public proof records')
    check_names=[]
    for n in ast.parse((SOURCE/'swdb-project/swdb/proof_setup.py').read_bytes()).body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHECK_SOURCES' for t in n.targets):check_names+=ast.literal_eval(n.value)
        elif isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='CHECK_SOURCES':check_names+=ast.literal_eval(n.value)
    identity=[{'path':'swdb/'+n,'sha256':pin(SOURCE/'swdb-project/swdb'/n)['sha256']} for n in check_names]
    identity += [{'path':'vocab/'+n,'sha256':pin(SOURCE/'swdb-project/vocab'/n)['sha256']} for n in ['proof_failure_classes.yaml','proof_subject_kinds.yaml']]
    reader_check={'version':'1','sha256':digest(identity)}
    reader_sources=list((PROFILE/'reader').glob('*.ml'))
    require(len(reader_sources)==1 and pin(reader_sources[0])['sha256']==pin(SOURCE/'swdb-project/swdb/proof_report.ml')['sha256'],'retained compiled native reader source exact')
    method=read(PROFILE/'method.json')
    require(method['tools']['seconds']==30 and method['tools']['provers']==['alt-ergo','z3','cvc5'],'unchanged ordinary portfolio')
    require(not any(x.startswith(('-wp-prop','-wp-fct')) or x in {'-wp-gen','-wp-no-why3-detect'} for x in method['flags']),'no selective/generation flags')
    leaves=[];tasks=[];direct_roots=set()
    for run in result['runs']:
        ident=run['id'];target=next(r for r in manifest['obligations'] if r['id']==ident);directory=PROFILE/('leaf-'+ident)
        require(run['cwd']==str(directory) and pin(directory/'wp_input.c')['sha256']==target['sha256'],'full leaf source identity '+ident)
        outcome=read(directory/'outcome.json');require(outcome==run['outcome'] and outcome['verdict']=='proven' and not outcome['assumptions'] and not outcome['unproven'],'normal outcome exact '+ident)
        require(outcome['reading']=={'check':reader_check,'verdict':'proven'},'current source-derived ordinary outcome reader '+ident)
        require(run['resources']==read(directory/'resources.json') and run['resources']['exit_code']==0 and not any(run['resources'][k] for k in ('timed_out','out_of_memory','output_limit')),'leaf resources healthy '+ident)
        invocation=read(directory/'command.json')['argv'];require(invocation[:len(expected['tools']['frama-c']['path'].split())]==[expected['tools']['frama-c']['path']] and all(f in invocation for f in method['flags']),'retained ordinary invocation '+ident)
        require(not any(x.startswith(('-wp-prop','-wp-fct')) or x=='-wp-gen' for x in invocation),'complete properties invocation '+ident)
        native=read(directory/'wp-inventory.json');ordinary=read(directory/'wp-goals.json');prop='check_lemma_'+target['goal']
        require(native['version']=='1' and native['complete'] is True and len(native['goals'])==len(ordinary)==len(outcome['goals'])==1,'complete one native ordinary goal '+ident)
        g=native['goals'][0];peer=ordinary[0]
        require(g['property']==prop and g['passed'] is True and g['smoke'] is False and g['targets']==[] and 'valid' in g['results'],'sole native direct Valid source owner '+ident)
        require(all(g.get(k)==peer.get(k) for k in ('goal','property','function','line','smoke','passed')) and any(p.get('success') for p in peer['provers']),'native ordinary exact peer '+ident)
        require(len(native['properties'])==2 and [p['property'] for p in native['properties'] if p['kind']=='lemma']==[prop] and all(not p['dependencies'] and p['origin'] is None and not p['extern'] and not p.get('generated_smoke_failure') for p in native['properties']),'complete independent property dependency origin Extern census '+ident)
        closure=native['property_closure'];require(closure['initial_registered_snapshot_count']==closure['registered_snapshot_count']==closure['exported_count']==2 and not any(closure[k] for k in ('unregistered_status_lookup_performed','unregistered_wp_smoke_properties','unregistered_wp_call_instances')),'complete native registered ownership '+ident)
        require(list(csv.DictReader(io.StringIO((directory/'wp-properties.csv').read_text()),delimiter='\t'))==[],'legitimate header-only global lemma CSV '+ident)
        log=(directory/'frama-c.log').read_text();direct_roots.update(re.findall(r'\(\* use ([\w.]+) \*\)',log));direct_roots.update(re.findall(r'\[wp:why3:compile\] use\s+(?:import\s+)?([\w.]+)',log))
        printed=re.findall(r'(?m)^  theory WP[0-9]*\s*\n(.*?)^  end\s*$',log,re.S);require(len(printed)>=1,'complete emitted Why3 theories '+ident)
        body=strip_comments(printed[0]);decls=re.findall(r'^\s*(predicate|function|goal|axiom|lemma|constant|val)\s+(\w+)',body,re.M)
        names=[('predicate','P_t25_private_observes'),('predicate','P_t25_private_frame')]
        if ident.startswith('cleanup.'):names += [('predicate','P_t25_private_ids'),('function','L_t25_private_cleanup')]
        require(decls==names+[('goal','wp_goal')],'only exact source definitions and sole goal '+ident)
        census=read(directory/'task-census.json');require(not census['missing_noninternal_tasks'] and len(census['common_exports'])==len(printed),'complete fresh common task census '+ident)
        for index,theory_body in enumerate(printed):
            declared=re.findall(r'^\s*(predicate|function|goal|axiom|lemma|constant|val)\s+(\w+)',strip_comments(theory_body),re.M)
            suffix='' if index==0 else str(index)
            require(declared==[(kind,name+suffix) for kind,name in names]+[('goal','wp_goal')],'complete solver-specific source namespace '+ident+' '+str(index))
        for export in census['common_exports']:
            segment=(directory/'frama-c.log').read_bytes()[export['begin_byte']:export['end_byte']]
            require(hashlib.sha256(segment).hexdigest()==export['sha256'] and export['goal']==g['goal'],'exact common range hash/native owner '+ident)
        files=sorted(directory.rglob('*.psmt2'))+sorted(directory.rglob('*.smt2'));require(files,'materialized solver tasks retained '+ident)
        for task in files:
            tree=forms(task.read_text());assertions=[x[1] for x in tree if x[0]=='assert'];checks=[i for i,x in enumerate(tree) if x[0]=='check-sat']
            require(len(checks)==1 and all(x==['get-info',':reason-unknown'] for x in tree[checks[0]+1:]),'single check-sat standard epilogue '+str(task))
            actual=canon(assertions[-1]);wanted=canon(source_goal(ident));require(actual==wanted,'exact independent source goal '+ident+' '+task.name+' actual='+digest(actual)+' expected='+digest(wanted))
            defs=check_definitions([x for x in tree if x[0]=='define-fun'],ident)
            require(not any('check_lemma_' in json.dumps(a) or 'wp_goal' in json.dumps(a) or 't25_private_' in json.dumps(a) for a in assertions[:-1]),'no desired/sibling premise support '+str(task))
            tasks.append({'id':ident,**pin(task),'assertions':len(assertions),'support_body_sha256':[digest(x) for x in assertions[:-1]],'source_goal_equivalent':True,'goal_form_sha256':digest(assertions[-1]),'source_definitions':defs,'actual_submission_attested':False})
        leaves.append({'id':ident,'property':prop,'goal':g['goal'],'native_results':g['results'],'solver':outcome['goals'][0]['solver'],'solver_seconds':outcome['goals'][0]['seconds'],'ordinary':1,'smoke':0,'properties':2,'CSV_rows':0,'input':pin(directory/'wp_input.c')})
    require(len(leaves)==9 and len({x['property'] for x in leaves})==9,'nine distinct source properties retained')
    roots = {'stdlib': prefix / 'share/why3/stdlib', 'wp': prefix / 'share/frama-c/share/wp/why3'}
    graph = {}
    visiting = set()
    def visit(name):
        if name in graph:
            return
        require(name not in visiting, 'acyclic imported module ' + name)
        visiting.add(name)
        if name == 'why3.BuiltIn.BuiltIn':
            graph[name] = {'classification': 'selected Why3 intrinsic core'}
        else:
            filename = name.rsplit('.', 1)[0].replace('.', '/') + '.mlw'
            candidates = [PROFILE / 'canonical-inputs/theory/heap_reallocation.mlw'] if name == 'heap_reallocation.Heap' else [root / filename for root in roots.values()]
            found = [path for path in candidates if path.is_file()]
            require(len(found) == 1, 'unambiguous selected import ' + name)
            text = strip_comments(found[0].read_text())
            module = name.rsplit('.', 1)[1]
            bodies = list(re.finditer(r'^(?:module|theory) ' + re.escape(module) + r'\b[^\n]*\n(.*?)^end\s*$', text, re.M | re.S))
            require(len(bodies) == 1, 'complete selected module body ' + name)
            body = bodies[0][1]
            edges = []
            for edge in re.finditer(r'^\s*(use|clone)\s+(?:(?:import|export)\s+)?([A-Za-z_]\w*(?:\.\w+)*)\b', body, re.M):
                kind, target = edge.groups()
                full = target if '.' in target else name.rsplit('.', 1)[0] + '.' + target
                edges.append({'kind': kind, 'target': full})
                visit(full)
            declarations = re.findall(r'^\s*(axiom|lemma|goal)\s+(\w+)', body, re.M)
            if name == 'heap_reallocation.Heap':
                require(not declarations, 'project Heap has definitions only and no desired assertions')
            graph[name] = {'source': pin(found[0]), 'module_body_sha256': hashlib.sha256(body.encode()).hexdigest(), 'dependencies': edges,
                           'proposition_declarations': declarations, 'classification': 'project definitions only' if name == 'heap_reallocation.Heap' else 'selected standard arithmetic/maps/Qed TCB'}
        visiting.remove(name)
    for name in sorted(direct_roots):
        visit(name)
    artifact_rows=read(PROFILE/'artifact-manifest.json')
    for row in artifact_rows:
        require(pin(row['path'])['sha256']==row['sha256'],'artifact manifest bytes '+row['relative'])
    require(snapshot(RAW)==initial,'complete raw pre/post hash identity')
    print(json.dumps({'created':'2026-10-16 ET','classification':'PASSIVE_COLD_SOURCE_NATIVE_TERM_CAPTURE; support attribution pending local metadata comparison',
       'source_commit':COMMIT,'raw_root':str(RAW),'checks':len(CHECKS),'elapsed_seconds':time.monotonic()-started,
       'raw_files':len(initial),'raw_bytes':sum(x['bytes'] for x in initial),'raw_manifest':initial,'raw_manifest_sha256':digest(initial),
       'source_consumers':consumers,'source_and_helper_count':len(expected['source_blobs'])+len(expected['test_helper_pins']),
       'runtime_pins':runtime_pins,'guard':guards,'lane':lane,'leaves':leaves,'materialized_tasks':tasks,
       'direct_import_roots':sorted(direct_roots),'import_source_closure':graph,'reader_check':reader_check,
       'result_pin':pin(PROFILE/'result.json'),'method_pin':pin(PROFILE/'method.json'),'launch_pin':pin(RAW/'launch.json'),
       'entry_sha256':ENTRY_SHA,'expected_sha256':EXPECTED_SHA,'actual_command_sha256':COMMAND_SHA,
       'raw_pre_post_equal':True,'sourceafter_clean':True,'actual_submission_count':None,'submitted_byte_attestation':False,
       'source_typed_or_body_or_caller_or_public_acceptance':False,
       'scope':'Nine standalone conditional mathematical duties only. No C-body ordinary/RTE/init/smoke reachability, allocator/source/Typed bridge, body/caller proof or public-record admission.'},sort_keys=True,indent=2))



if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'classification':'REFUSED_PASSIVE_AUDIT','error_type':type(error).__name__,'error':str(error),'checks_before_refusal':len(CHECKS),'acceptance':False}))
        raise SystemExit(1)
