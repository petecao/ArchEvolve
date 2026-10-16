"""2026-10-16 ET. Inert independent six-glue cold auditor.

Run only after root confirms the exact producer has settled. Stdlib and read-only
Git only; no project import, tool probe, compiler, verifier, solver or raw transfer.
"""
import argparse
import ast
import csv
import hashlib
import io
import itertools
import json
import os
import stat
import re
import resource
import signal
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-fb197c5d-t25-closed-lifetime6-public-v1')
PROFILE = RAW/'closed-lifetime6-public-v1-profile'
SOURCE = Path('/data1/yanruj/probata-resume-20261016-fb197c5d')
COMMIT = 'fb197c5ddd173065ca781766886c6a797684a838'
ENTRY_SHA = '76a687229c3d28e504102aad1bdd2c3efc47b1992cf1703c94a2291ec6f7c263'
EXPECTED_SHA = 'a10f2ee5864b8c39c22e72b29f34e3195b59839e0fdc9a6ae9e5c6c5f7ecd4b2'
COMMAND_SHA = 'be7379c4e99be42f88ef965517af8bf4e42e778041602ac3a8d288ba2dc573a8'
PRIOR_SUPPORT_HASHES = ['006ed960d9b2761de712c670238ea106fe431d343a9072c25275bd1186ef43e2', '0c363d3d6b94ab0460b36d16b61d2c9353fb6d2f82695bc4637d7184ac6edc34', '136b1ccb44b9c4e504fc9009fae32e39f89d59628a31404e3a6a77a6392597d8', '14e5a1d4743372c20da40f718aa6c59a3a29d21b29c075b161cbf7be0b525777', '1e12b2297921333a4b9e5662aefa61be9f32409270d4b8769dc8f3afe1e50ea9', '1e788d34e70c45a93c5624e6f5499bb880bbc09f3ce78960c5a29aaf8a1ec526', '230dac86f15e25f054f86acd1c634df7bfa14be5171dbf396701d518e32873b2', '2519083ff7eae4b41036ac0ed69933cc7111ff707235caa3b76b9fb6b20295c1', '3076bc3f8d7485f553d2b0e382697d0424d26dca7ded0dea396c78f142f19463', '39fdb0caf203dd0fb8bc5d392736d4596d73fc06bfbe23baf7ae38a8d4b80e2a', '3b91d4d3fd3ee8b435876ad46c558b8170bea759937396edd9251e0e85c9d8ae', '3f8db6925daa96931e8403b27e09722f50246f506060f57d7f1d628e0e756419', '41c7af5f3553cfe5c0897a763293c8816285c40c210433c7bf4b7273a08f5a9e', '451777247802989db373cc5c07812ce8f33f87f54ed883fb43e9f9ea720e0749', '4522f5d152877beda0a24ff172adcbe65457c924eae516daa054aa8bc6865b73', '4fa248013de091760fd304d3ebffb6564c823dc19d9f251e3f5b364c1ba55679', '4ffe57766ac7158e9bf22d49c2b6912e04ebd41c33149305cd1fd23fac56611a', '512da087aea287397b02298cbcb5d5f14a44d259881ff232fc4b643605977aaa', '5224d38dacf79571be4ade6de5e5b401266cf89925615c14bfb48391489f70ad', '54870e5c89b533678e220be22537d8796ab107f992c8d45a7cf79a926108d378', '58e1862d880068ce87e2fedb81a486f6858dd276c358e8c47045b680718794fb', '68587350e4436a612440ab8e05fc309620c421c8d2672a47407c4617fd44c563', '68e28b32268321dbcc63c814cca5150ab655adf5656fc3121b93a0761bc58874', '6caa6bc49e66c2c555aa2daf5b5455b199a88c5494a3937ac6aa31e31a6d96d6', '85c607d4a3ded15667c39e11ecf7f13402f7ecd70c42542c1f6072cf6dc4ea12', '8fbb971af9140aacd1d4a43c7d2bb0b40a258069e08f0870e5f3210d3aeb0817', '92ed3b6387a2ea7adfb0281282ed3f10092b199ffe0c64ac751db7f08385dad7', '9b78960d1ed583ce26a1f6cbaf956a5753dfbbff448f3e1d26a90b7e1b854db8', '9cf357ff89bfce98187e00c32b11c8f366a32c5fd210ea875690238c3f03b293', '9dda58f417232ee21aa0f6eb3f2a06786a9bc76e80ae3e7a02baf300b3a74b5b', 'a1dfed6d389be5a4dab9ecc490efbd14e26af33d143a92ba9f52ed15098e33fc', 'a2040454bce97f74d227cd239fc13ce62a686ed18398870f9e745eb3b4e69893', 'a5cf980bdcd3e0e9a1684f60f33fc384a03aa30fcc42463f801a6423f1dc4a64', 'ae18950f2236d5fd2e5aa1b445e800db9c86fb53dff06fbb9a60dee3a4d0e52c', 'b10a675182a54bd3e05baba0fae2deec3825802ec0c246d6ff6211f8f382cdf6', 'b4fc4ac5ec69834965592f4a8a6fa40e6e8039c5249e74ee687d3a98a5e80035', 'c6d3017050fb0dd646bf55e2fc75faf59098859292506f5cf86d230a21aa08a9', 'ca7f150707a74b16829d8e2ad7724aec87a279621dcb07e94410518ef4f32966', 'd2b030072e2e3631d5f96fbdec4a6a16d91053b067f82caff0c43e2434f9d75b', 'd83d59933cb8428fc118e396ac88d4b946da1e38c8442d3d51ad2853881701c2', 'dfc6a8665385ea7fc932eb7d43531861a7df141139b3bd7af3729660e6162cd2', 'e0fcaa13183bd7133b0a8bb910509bc040c4486ac0710a67ff365fb38a3306f5', 'e833deb13f611bf1d05aa7024d431400eae6ed2121ca9e27ebadf8616d1a189b', 'e8e9d90e3921f5c2eb9080962f083d57b45ade790b114130b5d1f967823ac255', 'f0128a61c0627c057a80014c6828d71960dea19dc00202eeb22d7fea7964bc2f', 'f76641cfe67719d9202d73ba93c813bbd56e58fad1389802f5cbadd4b363467b']
PRIOR_SUPPORT_PINS = [{'path': '/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/.scratch/probata-proof-of-concept-2026-10-13/evidence/t25-private-frame9-passive-cold-metadata-v3-20261016.json', 'sha256': '6b83bc96c026bbb0bd40db81475f666172ac89e3187ff5f6cf215ac46f93ad28', 'bytes': 325852}, {'path': '/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/.scratch/probata-proof-of-concept-2026-10-13/evidence/t25-private-frame9-independent-cold-decision-20261016.json', 'sha256': '8c8764bcdc2d6939251cc3966eb9032220b69040f24560c2fb03d7b3eb4e201f', 'bytes': 43043}, {'path': '/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/.scratch/probata-proof-of-concept-2026-10-13/evidence/t25-private-frame9-passive-cold-support-supplement-20261016.json', 'sha256': '00a8f14bbac8b98405735053270a33158280d0dfd9a19d70cd10bae37c05add3', 'bytes': 4094}]
CHECKS = []

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


"""2026-10-16 ET. Independent six-duty source/definition transcription.

SMT syntax is metadata for in-place term comparison, never a solver input run.
All goal antecedents are retained; old constructor/frame proofs are not premises.
"""

SOURCE_DEFINITIONS = {
    'P_t25_private_observes': ('(entry heap) (left heap) (right heap)',
        '(and (forall ((b Int)) (=> (live entry b) (same_object left right b))) '
        '(forall ((b Int) (p Int)) (=> (live entry b) '
        '(and (= (contents left b p) (contents right b p)) '
        '(= (initialized_at left b p) (initialized_at right b p))))))'),
    'P_t25_private_frame': ('(entry heap) (now heap)', '(P_t25_private_observes entry entry now)'),
    'P_t25_private_ids': ('(entry heap) (r Int) (b Int)',
        '(and (not (live entry r)) (or (= b 0) (and (not (live entry b)) (not (= b r)))))'),
    'L_t25_initial': ('(h heap) (r Int) (o Int)',
        '(put_integer (put_integer (put_pointer h r o 0 0) r (+ o 8) 0) r (+ o 16) 0)'),
    'P_t25_fields': ('(h heap) (r Int) (o Int) (b Int) (bo Int) (s Int) (c Int)',
        '(and (typed_writes h r o 24 8) (initialized_at h r o) (pointer_at h r o b bo) '
        '(initialized_at h r (+ o 8)) (integer_at h r (+ o 8) s) '
        '(initialized_at h r (+ o 16)) (integer_at h r (+ o 16) c))'),
    'P_t25_inv': ('(h heap) (r Int) (o Int) (b Int) (n Int) (k Int) (v Int)',
        '(and (well_formed h) (P_t25_fields h r o b 0 0 n) (not (= b r)) '
        '(< 0 n) (<= n 4611686018427387903) (<= 0 k) (<= k n) '
        '(typed_writes h b 0 (* 4 n) 4) (filled_prefix h b k v))'),
    'P_t25v3_ctor_inv': ('(h heap) (r Int) (o Int) (b Int) (n Int) (k Int) (v Int)',
        '(and (P_t25_inv h r o b n k v) (freeable h b 0) '
        '(<= (- 2147483648) v) (<= v 2147483647))'),
    'P_t25_frame': ('(old heap) (now heap) (r Int) (o Int)',
        '(and (forall ((b Int)) (=> (live old b) (same_object old now b))) '
        '(forall ((b Int) (p Int)) (=> (and (live old b) '
        '(not (and (= b r) (<= o p) (< p (+ o 24))))) '
        '(and (= (contents old b p) (contents now b p)) '
        '(= (initialized_at old b p) (initialized_at now b p))))))'),
    'L_t25_closed_positive': ('(loop heap) (r Int) (n Int)', '(put_integer loop r 8 n)'),
}

POSITIVE_PREMISE = (
    '(and (well_formed before) (< 0 n) (<= n 2147483647) '
    '(P_t25_private_frame entry before) (not (live entry r)) '
    '(typed_writes before r 0 24 8) (not (freeable before r 0)) '
    '(= b (next before)) (P_t25_frame before loop r 0) '
    '(P_t25v3_ctor_inv loop r 0 b n n 7))')

POSITIVE_STATE = '(L_t25_closed_positive loop r n)'


def source_goal(ident, *, positive_branch=False):
    begin = '(begin_automatic entry 24 a)'
    receiver = '(next entry)'
    positive = POSITIVE_STATE
    buffer = '(next '+begin+')'
    initial = '(L_t25_initial before r 0)'
    zero_final = '(release (release '+initial+' 0) r)'
    positive_final = '(release (release '+positive+' b) r)'
    load = '(load_int '+positive+' b 0)'
    scalar = load if positive_branch else '(ite (< 0 n) '+load+' 0)'
    seven = '7' if positive_branch else '(ite (< 0 n) 7 0)'
    bodies = {
        'receiver.entry': ('(entry heap) (a Int)',
            '(=> (and (well_formed entry) (automatic_available entry 24 8 a)) '
            '(and (well_formed '+begin+') (P_t25_private_frame entry '+begin+') '
            '(not (live entry '+receiver+')) (typed_writes '+begin+' '+receiver+' 0 24 8) '
            '(not (freeable '+begin+' '+receiver+' 0))))'),
        'constructor.frame': ('(entry heap) (before heap) (after heap) (r Int)',
            '(=> (and (P_t25_private_frame entry before) (not (live entry r)) '
            '(P_t25_frame before after r 0)) (P_t25_private_frame entry after))'),
        'buffer.identity': ('(entry heap) (a Int)',
            '(=> (and (well_formed entry) (automatic_available entry 24 8 a)) '
            '(and (= '+buffer+' (+ (next entry) 1)) (not (issued entry '+receiver+')) '
            '(not (issued entry '+buffer+')) (not (live entry '+buffer+')) '
            '(not (= '+buffer+' '+receiver+')) '
            '(= (next (L_t25_initial '+begin+' '+receiver+' 0)) '+buffer+')))'),
        'zero.cleanup': ('(entry heap) (before heap) (r Int)',
            '(=> (and (P_t25_private_frame entry before) (not (live entry r)) '
            '(typed_writes before r 0 24 8) (not (freeable before r 0))) '
            '(exists ((final heap)) (and (= final '+zero_final+') '
            '(P_t25_private_frame entry final) (not (forms final r 0)))))'),
        'positive.exit_image': ('(entry heap) (before heap) (loop heap) (r Int) (b Int) (n Int)',
            '(=> '+POSITIVE_PREMISE+' (and (P_t25_private_frame entry '+positive+') '
            '(P_t25_private_ids entry r b) (typed_writes '+positive+' r 0 24 8) '
            '(not (freeable '+positive+' r 0)) (freeable '+positive+' b 0) '
            '(int32_region '+positive+' b 0 n) (filled_prefix '+positive+' b n 7)))'),
        'positive.cleanup': ('(entry heap) (before heap) (loop heap) (r Int) (b Int) (n Int)',
            '(=> '+POSITIVE_PREMISE+' (exists ((final heap) (scalar Int)) '
            '(and (= final '+positive_final+') (= scalar '+scalar+') (= scalar '+seven+') '
            '(P_t25_private_frame entry final) (P_t25_private_observes entry '+positive+' final) '
            '(not (forms final r 0)) (not (forms final b 0)))))'),
    }
    bindings, body = bodies[ident]
    return forms('(not (forall ('+bindings+') '+body+'))')[0]


def symbols(tree):
    if isinstance(tree, str):
        return {tree}
    return set().union(*(symbols(x) for x in tree)) if tree else set()


def required_definitions(ident):
    needed = symbols(source_goal(ident)) & set(SOURCE_DEFINITIONS)
    while True:
        expanded = set(needed)
        for name in needed:
            _, body = SOURCE_DEFINITIONS[name]
            expanded |= symbols(forms(body)[0]) & set(SOURCE_DEFINITIONS)
        if expanded == needed:
            return needed
        needed = expanded


def check_source_definitions(definitions, ident):
    selected = [d for d in definitions if d[1].startswith(('P_t25', 'L_t25'))]
    require({d[1] for d in selected} == required_definitions(ident),
            'complete source definition closure '+ident)
    result = {}
    for definition in selected:
        bindings, body = SOURCE_DEFINITIONS[definition[1]]
        expected = forms('(forall ('+bindings+') '+body+')')[0]
        actual = ['forall', definition[2], definition[-1]]
        require(canon(actual) == canon(expected), 'independent source definition '+ident+' '+definition[1])
        result[definition[1]] = {'form_sha256': digest(definition), 'source_equivalent': True}
    return result



READ_ONLY_GIT_ACTIVE = False


def git(*args, input=None):
    global READ_ONLY_GIT_ACTIVE
    require(not READ_ONLY_GIT_ACTIVE, 'no nested read-only Git call')
    READ_ONLY_GIT_ACTIVE = True
    try:
        kwargs = {'timeout': 45}
        if input is not None:
            kwargs['input'] = input
        return subprocess.check_output(['/usr/bin/git','--no-optional-locks','--no-replace-objects',
            '-c','core.preloadIndex=false','-c','core.fsmonitor=false','-c','index.threads=1',
            '-C',str(SOURCE),*args], **kwargs)
    finally:
        READ_ONLY_GIT_ACTIVE = False


def lineage(anchors):
    direct = ('tool','function','c_lowering_sha256','anchors','models','std_models','allocation')
    keys = ('count','receiver','alias','reserve_request','observation','guard','entry_obligations',
            'call_obligations','scalar_read_obligation','lowered_lifetime','source_sha256','lowered_sha256')
    return {**{k:anchors[k] for k in direct},
            'candidate_source_events':{k:anchors['vector_reallocation_candidate'][k] for k in keys}}


def normal_flags(flags):
    for name in ('-wp','-wp-rte','-wp-no-filter-init','-wp-smoke-tests','-wp-status-all'):
        require(name in flags,'mandatory complete normal flag '+name)
    for name,wanted in [('-wp-cache','none'),('-wp-model','+real'),('-machdep','x86_64'),
                        ('-rte-initialized','@all'),('-wp-par','1'),('-wp-timeout','30'),
                        ('-wp-prover','alt-ergo,z3,cvc5')]:
        values=[flags[i+1] for i,x in enumerate(flags[:-1]) if x==name]
        values += [x[len(name)+1:] for x in flags if x.startswith(name+'=')]
        require(values and all(x==wanted for x in values),'exact normal flag values '+name)
    require(not any(x.startswith(('-wp-prop','-wp-fct','-wp-session','-wp-script','-wp-cache-dir')) or
                    x in {'-wp-gen','-wp-no-why3-detect','-wp-filter-init','-wp-no-rte'} for x in flags),
            'no selective/generation/weakening/session flags')


def source_false_map(assertion, tree):
    """Recognize only Heap's original new-identity false initialization lambda."""
    value = assertion
    if not (isinstance(value,list) and len(value)==3 and value[0]=='forall' and len(value[1])==1):
        return None
    variable, sort = value[1][0]
    body = value[2]
    if sort!='Int' or not (isinstance(body,list) and len(body)==3 and body[0]=='='):
        return None
    left,right=body[1:]
    if left=='false':left,right=right,left
    if right!='false' or not (isinstance(left,list) and len(left)==3 and left[0]=='select' and left[2]==variable and isinstance(left[1],str)):
        return None
    name=left[1]
    declared=[x for x in tree if x[:2]==['declare-fun',name]]
    if declared!=[['declare-fun',name,[],['Array','Int','Bool']]]:
        return None
    def uses(value):
        return int(value==name) if isinstance(value,str) else sum(uses(x) for x in value)
    owners=[x for x in tree if x and x[0]=='define-fun' and uses(x)]
    if not owners or any(x[1] not in {'begin_automatic','allocate'} for x in owners):
        return None
    expected_uses=forms('(store (initialized h) (next h) '+name+')')[0]
    def contains(value,wanted):
        return value==wanted or isinstance(value,list) and any(contains(x,wanted) for x in value)
    if any(uses(x)!=1 or not contains(expand(x[-1]),expected_uses) for x in owners):
        return None
    all_uses=[x for x in tree if uses(x)]
    if len(all_uses)!=len(owners)+2:
        return None
    return {'classification':'Definitional lifting of unchanged Heap initialization lambda; not a theorem premise',
            'source':'theory/heap_reallocation.mlw','source_transitions':[x[1] for x in owners],
            'exact_array_type':True,'sole_source_initialization_use':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node',type=int,choices=(0,1),required=True)
    parser.add_argument('--generation',type=int,required=True)
    parser.add_argument('--ended-utc',required=True)
    args=parser.parse_args()
    require(args.generation>0 and bool(re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ',args.ended_utc)),
            'root-confirmed settlement arguments')
    signal.alarm(180)
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    started=time.monotonic()
    def audit(event,values):
        if event=='subprocess.Popen':
            require(values[0]=='/usr/bin/git','read-only Git is the sole allowed child')
        elif event in {'os.system','os.posix_spawn','os.exec','os.fork','ctypes.dlopen'}:
            raise RuntimeError('project/native/external execution forbidden')
        elif event=='open':
            filename, mode, flags = values
            writable = (isinstance(mode, str) and any(x in mode for x in 'wax+')) or (flags & os.O_ACCMODE) != os.O_RDONLY or bool(flags & (os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if writable:
                if isinstance(filename, int) and READ_ONLY_GIT_ACTIVE and stat.S_ISFIFO(os.fstat(filename).st_mode):
                    return  # Python's stdin pipe wrapper for fixed read-only Git.
                raise RuntimeError('remote writes forbidden: ' + json.dumps({
                    'filename': filename, 'mode': mode, 'flags': flags,
                    'call_site': 'fixed_read_only_git' if READ_ONLY_GIT_ACTIVE else 'outside_git'}))
    sys.addaudithook(audit)
    initial=snapshot(RAW)
    expected=read(PROFILE/'expected.json');policy=expected['resource_policy']
    require(pin(PROFILE/'expected.json')['sha256']==EXPECTED_SHA,'exact frozen expected')
    for path in (RAW/'closed-lifetime6-public-v1-entry.py',PROFILE/'entry.py'):
        require(pin(path)['sha256']==ENTRY_SHA,'exact frozen entry '+str(path))
    require(expected['source_commit']==COMMIT and expected['remote_project']==str(SOURCE/'swdb-project'),'exact source/context')
    require(git('rev-parse','HEAD').decode().strip()==COMMIT and not git('status','--porcelain','--untracked-files=all'),'current source exact and clean')
    for row in expected['source_blobs']+expected['test_helper_pins']:
        require(pin(SOURCE/'swdb-project'/row['relative'])['sha256']==row['sha256'],'source/helper '+row['relative'])
    consumers=[]
    for path in sorted(PROFILE.glob('source-consumers-*.json')):
        closure=read(path)
        for relative,row in closure['trees'].items():
            require(git('rev-parse',COMMIT+':swdb-project/'+relative).decode().strip()==row['oid'],'consumer Git tree '+relative)
        for row in closure['files']:
            got=pin(row['path']);require(got['sha256']==row['sha256'] and got['bytes']==row['bytes'],'physical consumer '+row['relative'])
        oids=git('hash-object','--no-filters','--stdin-paths',input=''.join(r['path']+'\n' for r in closure['files']).encode()).decode().splitlines()
        require(oids==[r['git_blob'] for r in closure['files']],'physical consumer Git blobs')
        consumers.append({'receipt':pin(path),'count':closure['count'],'total_bytes':closure['total_bytes']})
    require(len(consumers)==2 and read(PROFILE/'source-consumers-0.json')==read(PROFILE/'source-consumers-1.json'),'source before/after consumers exact')
    runtime=[]
    for row in [*expected['tools'].values(),*expected['wp_artifacts'],expected['why3_config']]:
        got=pin(row['path']);require(got['sha256']==row['sha256'],'physical selected tool/artifact/config');runtime.append(got)
    prefix=Path(expected['linux_prefix'])
    for key,root in [('why3_stdlib',prefix/'share/why3/stdlib'),('wp_why3_support',prefix/'share/frama-c/share/wp/why3'),('why3_drivers',prefix/'share/why3/drivers')]:
        actual=[]
        for path in sorted(root.rglob('*')):
            require(not path.is_symlink() and (path.is_file() or path.is_dir()),'regular support input')
            if path.is_file():
                got=pin(path);runtime.append(got);actual.append({'relative':str(path.relative_to(root)),'sha256':got['sha256']})
        require(actual==expected['portable_import_surfaces'][key],'complete support membership '+key)
    for row in expected['runtime_sources']:
        require(pin(prefix/'lib/frama-c-wp/core'/row['name'])['sha256']==row['sha256'],'runtime source '+row['name'])
    compiler=read(PROFILE/'compiler-runtime.json')
    require(compiler=={'runtime':expected['linux_project_identity_derivation']['runtime'],'identity':expected['linux_project_identity_derivation']['predicted_identity']},'actual current compiler/source context')
    for row in [expected['linux_clang_components']['command_executable'],expected['linux_clang_components']['driver']]:
        require(pin(row['path'])['sha256']==row['sha256'],'physical compiler component')
    compiler_root=Path(expected['linux_clang_components']['driver']['path']).parent.parent
    require(pin((compiler_root/'lib/libclang.so').resolve())['sha256']==expected['linux_clang_components']['parser']['sha256'],'physical libclang')
    headers=hashlib.sha256();count=0
    for label,root in [('libc++',compiler_root/'include/c++/v1'),('clang-resource',compiler_root/'lib/clang/22/include')]:
        for path in sorted(root.rglob('*')):
            if path.is_file():
                got=pin(path);headers.update(label.encode()+b'\0'+str(path.relative_to(root)).encode()+b'\0');headers.update(bytes.fromhex(got['sha256']));count+=1
    require({'id':'llvm-standard-resource-headers','sha256':headers.hexdigest(),'files':count}==expected['linux_clang_components']['headers'],'complete compiler/header context')
    foundation=read(PROFILE/'foundation.json')
    for row in foundation['sources']:
        require(pin(row['path'])['sha256']==row['sha256'],'selected foundation source')
    require(pin(foundation['metadata_executable'])['sha256']==foundation['metadata_executable_sha256'],'retained foundation executable')
    anchors=read(PROFILE/'anchors.fresh.json')
    require(lineage(anchors)==expected['cached_anchor_lineage'],'fresh original anchor/source lineage')
    provenance=anchors['stdlib_provenance'];candidate=anchors['vector_reallocation_candidate']
    require(provenance['verdict']=='passed' and provenance['library']['id']=='libc++-22.1.8','full original-TU provenance retained')
    require(candidate['stdlib_binding_sha256']==hashlib.sha256(json.dumps(provenance,sort_keys=True).encode()).hexdigest(),'candidate full provenance binding')
    require(candidate['known_origins_granted']==[] and candidate['original_caller_premises_added']==[],'no source origin or caller premise granted')
    manifest=read(PROFILE/'canonical-inputs/manifest.json')
    portable=json.loads(json.dumps(manifest));host=portable['source_view']['library_allocator_binding'].pop('certificate_sha256')
    require(host==digest(provenance) and portable==expected['canonical_manifest_portable'],'single host leaf omitted; full provenance rebound')
    physical=[{'path':str(p.relative_to(PROFILE/'canonical-inputs')),'bytes':p.stat().st_size,'sha256':pin(p)['sha256']} for p in sorted((PROFILE/'canonical-inputs').rglob('*')) if p.is_file() and p.name!='manifest.json']
    require(physical==expected['canonical_files'] and len(physical)==15,'all canonical nonmanifest bytes')
    require(pin(PROFILE/'canonical-inputs/sources/original.cc')['sha256']==expected['source_sha256'] and pin(SOURCE/'swdb-project'/expected['source_relative'])['sha256']==expected['source_sha256'],'original C++ source byte lineage')
    require(pin(PROFILE/'canonical-inputs/sources/original-caller.c')['sha256']==expected['lowered_sha256'],'original lowered caller lineage')
    launch=read(RAW/'launch.json')
    require(digest(launch['command'])==COMMAND_SHA and launch['source_commit']==COMMIT and Path(launch['source'])==SOURCE,'exact actual launch argv/source')
    require(launch['timeout_seconds']==policy['root_whole_seconds'] and launch['rss_cap_bytes']==policy['cap_bytes'] and launch['workers']==1,'exact actual launch limits')
    for name,wanted in expected['linux_launch_binding']['wrappers'].items():
        require(pin(RAW/name)['sha256']==wanted==launch['reviewed_wrapper_reuse'][name],'reviewed outer wrapper '+name)
    guards={name:read(RAW/name) for name in ('resources.json','outer-resources.json')}
    for name,value in guards.items():
        require(value['exit_code']==0 and not value['out_of_memory'] and not value['timed_out'] and value['peak_rss_bytes']<=policy['cap_bytes'],'settled guard '+name)
    lane=read(RAW/'lane.json')['socket_lane']
    require(lane['node']==args.node and lane['lease_generation']==args.generation and lane['ended_utc']==args.ended_utc and lane['exit_code']==0 and lane['numa_memory_policy']=='bind:'+str(args.node),'root-confirmed actual lane settlement')
    require(read(RAW/'source-after.json')=={'commit':COMMIT,'source_unchanged':True,'tracked_changes':''},'exact source after')
    require('PYTHONPATH' not in read(RAW/'dispatch-environment.json'),'outer PYTHONPATH removed')
    result=read(PROFILE/'result.json')
    require(result['producer_complete'] and result['within_profile_budget'] and result['source_after_clean'] and not result['unexecuted'] and not result.get('error'),'all six producer outcomes retained')
    require([r['id'] for r in result['runs']]==expected['target_ids'] and len(result['runs'])==6,'all six distinct source identities')
    for name in ('proof_acceptance','source_typed_bridge_established','body_acceptance','caller_acceptance','public_proof_record_created','universal_proof_setup_attested'):
        require(result[name] is False,'larger admission remains false '+name)
    require(not list((PROFILE/'workspace/records/proofs').glob('*.yaml')),'no public proof record')
    names=[]
    for node in ast.parse((SOURCE/'swdb-project/swdb/proof_setup.py').read_bytes()).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHECK_SOURCES' for t in node.targets):names+=ast.literal_eval(node.value)
        elif isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='CHECK_SOURCES':names+=ast.literal_eval(node.value)
    identity=[{'path':'swdb/'+n,'sha256':pin(SOURCE/'swdb-project/swdb'/n)['sha256']} for n in names]
    identity += [{'path':'vocab/'+n,'sha256':pin(SOURCE/'swdb-project/vocab'/n)['sha256']} for n in ('proof_failure_classes.yaml','proof_subject_kinds.yaml')]
    reading={'version':'1','sha256':digest(identity)}
    require(pin(PROFILE/'reader/proof_report.ml')['sha256']==pin(SOURCE/'swdb-project/swdb/proof_report.ml')['sha256'],'actual native reader source')
    method=read(PROFILE/'method.json')
    require(method['tools']['seconds']==30 and method['tools']['provers']==['alt-ergo','z3','cvc5'],'complete unchanged portfolio')
    normal_flags(method['flags'])
    leaves=[];tasks=[];roots=set();unmatched=[]
    for run in result['runs']:
        ident=run['id'];row=next(x for x in manifest['obligations'] if x['id']==ident);directory=PROFILE/('leaf-'+ident)
        require(run['cwd']==str(directory) and pin(directory/'wp_input.c')['sha256']==row['sha256'],'actual leaf source '+ident)
        outcome=read(directory/'outcome.json');require(outcome==run['outcome'] and not outcome['assumptions'],'unchanged normal reader; no opaque premise '+ident)
        if outcome.get('reading'):
            require(outcome['reading']['check']==reading,'current ordinary reader identity '+ident)
        require(run['resources']==read(directory/'resources.json') and run['resources']['exit_code']==0 and not any(run['resources'][k] for k in ('timed_out','out_of_memory','output_limit')),'actual leaf resources '+ident)
        invocation=read(directory/'command.json')['argv']
        require(invocation[0]==expected['tools']['frama-c']['path'] and all(f in invocation for f in method['flags']),'normal complete command '+ident)
        normal_flags(invocation)
        native=read(directory/'wp-inventory.json');ordinary=read(directory/'wp-goals.json');prop='check_lemma_'+row['goal']
        require(native['complete'] is True and len(native['goals'])==len(ordinary)==len(outcome['goals'])==1,'complete single source-owned ordinary goal '+ident)
        goal=native['goals'][0];peer=ordinary[0]
        require(goal['property']==prop and goal['smoke'] is False and goal['targets']==[],'sole native source owner '+ident)
        require(all(goal.get(k)==peer.get(k) for k in ('goal','property','function','line','smoke','passed')),'native/ordinary peer '+ident)
        require(len(native['properties'])==2 and [p['property'] for p in native['properties'] if p['kind']=='lemma']==[prop] and all(not p['dependencies'] and p['origin'] is None and not p['extern'] and not p.get('generated_smoke_failure') for p in native['properties']),'complete dependency-free source property closure '+ident)
        closure=native['property_closure'];require(closure['initial_registered_snapshot_count']==closure['registered_snapshot_count']==closure['exported_count']==2 and not any(closure[k] for k in ('unregistered_status_lookup_performed','unregistered_wp_smoke_properties','unregistered_wp_call_instances')),'registered source property census '+ident)
        with (directory/'wp-properties.csv').open() as stream:
            csvrows=list(csv.reader(stream,delimiter='\t'))
        require(csvrows==[['directory','file','line','function','property kind','status','property']],'legitimate complete global-lemma CSV '+ident)
        log=(directory/'frama-c.log').read_text();roots.update(re.findall(r'\(\* use ([\w.]+) \*\)',log));roots.update(re.findall(r'\[wp:why3:compile\] use\s+(?:import\s+)?([\w.]+)',log))
        printed=re.findall(r'(?m)^  theory WP[0-9]*\s*\n(.*?)^  end\s*$',log,re.S)
        require(printed,'actual printed theory retained '+ident)
        wanted=required_definitions(ident)
        for index,body in enumerate(printed):
            declarations=re.findall(r'^\s*(predicate|function|goal|axiom|lemma|constant|val)\s+(\w+)',strip_comments(body),re.M)
            suffix='' if index==0 else str(index)
            require(set(declarations)=={('function' if name.startswith('L_') else 'predicate',name+suffix) for name in wanted}|{('goal','wp_goal')},'only source definitions and sole goal '+ident)
        census=read(directory/'task-census.json');require(not census['missing_noninternal_tasks'] and len(census['common_exports'])==len(printed),'all printed exports retained '+ident)
        for export in census['common_exports']:
            with (directory/'frama-c.log').open('rb') as stream:
                stream.seek(export['begin_byte']);segment=stream.read(export['end_byte']-export['begin_byte'])
            require(hashlib.sha256(segment).hexdigest()==export['sha256'] and export['goal']==goal['goal'],'common range/native identity '+ident)
        files=sorted(directory.rglob('*.psmt2'))+sorted(directory.rglob('*.smt2'));require(files,'actual materialized tasks retained '+ident)
        for path in files:
            tree=forms(path.read_text());assertions=[x[1] for x in tree if x[0]=='assert'];checks=[n for n,x in enumerate(tree) if x[0]=='check-sat']
            require(assertions and len(checks)==1 and all(x==['get-info',':reason-unknown'] for x in tree[checks[0]+1:]),'sole SMT query/epilogue '+path.name)
            actual=canon(assertions[-1]);variants=[('literal_source',source_goal(ident))]
            if ident=='positive.cleanup':variants.append(('positive_antecedent_dominates_scalar_branch',source_goal(ident,positive_branch=True)))
            equal=[name for name,value in variants if actual==canon(value)]
            require(equal,'independent complete source goal '+ident+' '+path.name+' actual='+digest(actual))
            defs=check_source_definitions([x for x in tree if x[0]=='define-fun'],ident)
            attribution=[]
            for value in assertions[:-1]:
                require(not any(name in json.dumps(value) for name in ['check_lemma_','wp_goal','P_t25','L_t25']),'no desired/sibling theorem premise '+ident)
                key=digest(value)
                if key in PRIOR_SUPPORT_HASHES:
                    attribution.append({'sha256':key,'classification':'exact previously primary-source-attributed standard/Heap definitional support; old goals/proofs excluded'})
                else:
                    lifted=source_false_map(value,tree)
                    if lifted:attribution.append({'sha256':key,**lifted})
                    else:unmatched.append({'id':ident,'task':str(path),'assertion_sha256':key})
            tasks.append({'id':ident,**pin(path),'source_goal_equivalent':True,'normalization':equal,'goal_form_sha256':digest(assertions[-1]),'source_definitions':defs,'support_attribution':attribution,'non_goal_assertions':len(assertions)-1,'actual_submission_attested':False})
        leaves.append({'id':ident,'goal':goal['goal'],'property':prop,'native_results':goal['results'],'passed':goal['passed'],'normal_verdict':outcome['verdict'],'failure_class':outcome['failure_class'],'ordinary':1,'smoke':0,'properties':2,'CSV_rows':0,'input':pin(directory/'wp_input.c')})
    graph={};visiting=set()
    def visit(name):
        if name in graph:return
        require(name not in visiting,'acyclic selected import '+name);visiting.add(name)
        if name=='why3.BuiltIn.BuiltIn':graph[name]={'classification':'selected Why3 intrinsic core'}
        else:
            filename=name.rsplit('.',1)[0].replace('.','/')+'.mlw'
            candidates=[PROFILE/'canonical-inputs/theory/heap_reallocation.mlw'] if name=='heap_reallocation.Heap' else [prefix/'share/why3/stdlib'/filename,prefix/'share/frama-c/share/wp/why3'/filename]
            found=[p for p in candidates if p.is_file()];require(len(found)==1,'unambiguous actual import '+name)
            text=strip_comments(found[0].read_text());module=name.rsplit('.',1)[1]
            bodies=list(re.finditer(r'^(?:module|theory) '+re.escape(module)+r'\b[^\n]*\n(.*?)^end\s*$',text,re.M|re.S));require(len(bodies)==1,'complete actual import body '+name)
            body=bodies[0][1];edges=[]
            for match in re.finditer(r'^\s*(use|clone)\s+(?:(?:import|export)\s+)?([A-Za-z_]\w*(?:\.\w+)*)\b',body,re.M):
                kind,target=match.groups();full=target if '.' in target else name.rsplit('.',1)[0]+'.'+target;edges.append({'kind':kind,'target':full});visit(full)
            propositions=re.findall(r'^\s*(axiom|lemma|goal)\s+(\w+)',body,re.M)
            if name=='heap_reallocation.Heap':require(not propositions,'source Heap definitions only; no desired axiom')
            graph[name]={'source':pin(found[0]),'module_body_sha256':hashlib.sha256(body.encode()).hexdigest(),'dependencies':edges,'proposition_declarations':propositions,'classification':'project definitions only' if name=='heap_reallocation.Heap' else 'selected standard arithmetic/maps/Qed TCB'}
        visiting.remove(name)
    for name in sorted(roots):visit(name)
    for row in read(PROFILE/'artifact-manifest.json'):
        require(pin(row['path'])['sha256']==row['sha256'],'producer artifact bytes '+row['relative'])
    require(snapshot(RAW)==initial,'entire raw unchanged before/after')
    require(not unmatched,'all actual support assertions source-attributed '+digest(unmatched))
    all_proven=all(x['normal_verdict']=='proven' and x['passed'] and 'valid' in x['native_results'] for x in leaves)
    require(result['all_six_producer_proven']==all_proven,'producer aggregate matches all actual leaves')
    output={'created':'2026-10-16 ET','classification':'PASS_CONDITIONAL_SIX_SOURCE_MATH_COLD' if all_proven else 'COMPLETE_SIX_SOURCE_COLD_NOT_PROVEN',
        'checks':len(CHECKS),'elapsed_seconds':time.monotonic()-started,'source_commit':COMMIT,'raw_root':str(RAW),
        'entry_sha256':ENTRY_SHA,'expected_sha256':EXPECTED_SHA,'actual_command_sha256':COMMAND_SHA,
        'result_pin':pin(PROFILE/'result.json'),'raw_files':len(initial),'raw_bytes':sum(x['bytes'] for x in initial),'raw_manifest':initial,'raw_pre_post_equal':True,
        'leaves':leaves,'materialized_tasks':tasks,'unmatched_supports':unmatched,'prior_support_source_attribution_pins':PRIOR_SUPPORT_PINS,
        'source_consumers':consumers,'source_and_helper_count':len(expected['source_blobs'])+len(expected['test_helper_pins']),
        'runtime_pins':runtime,'selected_runtime_sources':expected['runtime_sources'],'reader_check':reading,'guard':guards,'lane':lane,
        'full_fresh_host_certificate_sha256':host,'only_portable_host_digest_leaf_omitted':True,'sourceafter_clean':True,
        'direct_import_roots':sorted(roots),'import_source_closure':graph,'all_six_normal_producer_proven':all_proven,
        'old_ctor_dtor_math_imported_as_premise':False,'current_constructor_body_record_admitted':False,
        'source_typed_bridge_established':False,'body_acceptance':False,'caller_acceptance':False,'public_proof_record_created':False,
        'universal_proof_setup_attested':False,'actual_submission_count':None,'submitted_byte_attestation':False,
        'scope':'Six independent conditional mathematical source duties only under declared translation/standard support/solver TCB; no source allocation/Typed/lifetime/body/caller/public/ticket admission.'}
    encoded=(json.dumps(output,sort_keys=True,indent=2)+'\n').encode();require(len(encoded)<4*1024**2,'compact metadata output bound')
    signal.alarm(0);sys.stdout.buffer.write(encoded)


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'classification':'REFUSED_PASSIVE_SIX_COLD','error_type':type(error).__name__,'error':str(error),'checks_before_refusal':len(CHECKS),'acceptance':False}))
        raise SystemExit(1)
