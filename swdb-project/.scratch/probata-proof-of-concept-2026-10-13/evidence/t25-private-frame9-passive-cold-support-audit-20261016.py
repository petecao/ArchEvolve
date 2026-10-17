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
    if head=='exists':
        bindings=list(value[1]); body=expand(value[2])
        conjuncts=list(body[1:]) if isinstance(body,list) and body and body[0]=='and' else [body]
        def occurs(name,tree):
            return tree==name if isinstance(tree,str) else any(occurs(name,x) for x in tree)
        def replace(tree,name,term):
            return term if tree==name else tree if isinstance(tree,str) else [replace(x,name,term) for x in tree]
        remaining=[]
        for name,typ in bindings:
            witness=None
            for i,part in enumerate(conjuncts):
                if isinstance(part,list) and len(part)==3 and part[0]=='=':
                    if part[1]==name and not occurs(name,part[2]):witness=(i,part[2]);break
                    if part[2]==name and not occurs(name,part[1]):witness=(i,part[1]);break
            if witness is None:remaining.append([name,typ])
            else:
                index,term=witness
                conjuncts=[replace(part,name,term) for i,part in enumerate(conjuncts) if i!=index]
        if not remaining:return canon(['and',*conjuncts],env,depth)
        value=['exists',remaining,['and',*conjuncts]]
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
    if head=='=>' and len(value)>3:
        return canon(['=>',value[1],['=>',*value[2:]]],env,depth)
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



checks=[]
for ident,fn,line in [('automatic.frame','begin_automatic',171),('allocation.frame','allocate',95)]:
 for task in sorted((PROFILE/('leaf-'+ident)).rglob('*.psmt2')):
  tree=forms(task.read_text());extra=[x[1] for x in tree if x[0]=='assert' and digest(x[1])=='006ed960d9b2761de712c670238ea106fe431d343a9072c25275bd1186ef43e2'];require(len(extra)==1,'one constant-false map definition')
  expected=forms('(forall ((us Int)) (= (select fc us) false))')[0];require(canon(extra[0])==canon(expected),'exact constant-false map source formula')
  declarations=[x for x in tree if x[0]=='declare-fun' and x[1]=='fc'];require(declarations==[['declare-fun','fc',[],['Array','Int','Bool']]],'constant map exact array type')
  defs=[x for x in tree if x[0]=='define-fun'];owned=[x for x in defs if x[1]==fn];require(len(owned)==1,'sole original source transition definition')
  def count(x,name):return int(x==name) if isinstance(x,str) else sum(count(y,name) for y in x)
  allowed=[x for x in tree if count(x,'fc')];require(len(allowed)==3 and sum(count(x,'fc') for x in owned)==1,'constant map occurs only in declaration equation and selected transition')
  body=expand(owned[0][-1]);expected_store=forms('(store (initialized h) (next h) fc)')[0]
  def contains(x,w):return x==w or isinstance(x,list) and any(contains(y,w) for y in x)
  require(contains(body,expected_store),'constant false map is exactly new identity initialization field')
  checks.append({'task':pin(task),'assertion_sha256':digest(extra[0]),'source_transition':fn,'source_line':line,'classification':'Definitional lifting of the original initialization lambda (fun _ -> False); no theorem premise','exact_source_map_formula':True,'only_source_transition_use':True})
last=read(PROFILE/'leaf-cleanup.exists_scalar/wp-goals.json')[0]
print(json.dumps({'created':'2026-10-16 ET','checks':checks,'last_ordinary_provers':last['provers'],'dispatch_argv':read(RAW/'dispatch-argv.json'),'lock_file_exists':(RAW/'verifier.lock').exists(),'root_sourceafter':read(RAW/'source-after.json'),'formal_or_caller_acceptance':False},indent=2))
