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
    require((before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino), 'stable read ' + str(path))
    return {'path': str(path), 'bytes': before.st_size, 'sha256': h.hexdigest()}

def forms(text):
    lex = re.compile('\\s+|;[^\\n]*|"(?:[^"]|"")*"|\\|[^|]*\\||[()]|[^\\s()]+')
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

def canon(value, env=None, depth=0):
    """Alpha/order normalization only; no use of a prover or theorem result."""
    env = {} if env is None else env
    if isinstance(value, str):
        return env.get(value, value)
    if not value:
        return []
    if value[0] == 'let':
        return canon(expand(value), env, depth)
    head = value[0]
    if head == 'exists':
        bindings = list(value[1])
        body = expand(value[2])
        conjuncts = list(body[1:]) if isinstance(body, list) and body and (body[0] == 'and') else [body]

        def occurs(name, tree):
            return tree == name if isinstance(tree, str) else any((occurs(name, x) for x in tree))

        def replace(tree, name, term):
            return term if tree == name else tree if isinstance(tree, str) else [replace(x, name, term) for x in tree]
        remaining = []
        for name, typ in bindings:
            witness = None
            for i, part in enumerate(conjuncts):
                if isinstance(part, list) and len(part) == 3 and (part[0] == '='):
                    if part[1] == name and (not occurs(name, part[2])):
                        witness = (i, part[2])
                        break
                    if part[2] == name and (not occurs(name, part[1])):
                        witness = (i, part[1])
                        break
            if witness is None:
                remaining.append([name, typ])
            else:
                index, term = witness
                conjuncts = [replace(part, name, term) for i, part in enumerate(conjuncts) if i != index]
        if not remaining:
            return canon(['and', *conjuncts], env, depth)
        value = ['exists', remaining, ['and', *conjuncts]]
    if head in ('forall', 'exists'):
        bindings = list(value[1])
        body = value[2]
        while isinstance(body, list) and body and (body[0] == head):
            bindings += body[1]
            body = body[2]
        groups = {}
        for name, typ in bindings:
            groups.setdefault(json.dumps(typ, sort_keys=True), []).append(name)
        keys = sorted(groups)
        options = []
        for key in keys:
            options.append(list(itertools.permutations(groups[key])))
        candidates = []
        for choices in itertools.product(*options):
            names = {name: '@%s:%s:%s' % (depth, key, i) for key, choice in zip(keys, choices) for i, name in enumerate(choice)}
            candidates.append(canon(body, {**env, **names}, depth + 1))
        return [head, [(key, len(groups[key])) for key in keys], min(candidates, key=lambda x: json.dumps(x, sort_keys=True))]
    if head == '=>' and len(value) > 3:
        return canon(['=>', value[1], ['=>', *value[2:]]], env, depth)
    args = [canon(v, env, depth) for v in value[1:]]
    if head in ('and', 'or', '+', '*'):
        flat = []
        for v in args:
            flat.extend(v[1:] if isinstance(v, list) and v and (v[0] == head) else [v])
        args = sorted(flat, key=lambda x: json.dumps(x, sort_keys=True))
    if head == '=':
        args.sort(key=lambda x: json.dumps(x, sort_keys=True))
    if head == '=>' and len(args) == 2 and isinstance(args[1], list) and (args[1][0] == '=>'):
        return canon(['=>', ['and', args[0], args[1][1]], args[1][2]])
    if head == 'end_automatic':
        head = 'release'
    if head == 'fresh_id':
        head = 'next'
    return [head, *args]
SOURCE_DEFINITIONS = {'P_t25_private_observes': ('(entry heap) (left heap) (right heap)', '(and (forall ((b Int)) (=> (live entry b) (same_object left right b))) (forall ((b Int) (p Int)) (=> (live entry b) (and (= (contents left b p) (contents right b p)) (= (initialized_at left b p) (initialized_at right b p))))))'), 'P_t25_private_frame': ('(entry heap) (now heap)', '(P_t25_private_observes entry entry now)'), 'P_t25_private_ids': ('(entry heap) (r Int) (b Int)', '(and (not (live entry r)) (or (= b 0) (and (not (live entry b)) (not (= b r)))))'), 'L_t25_initial': ('(h heap) (r Int) (o Int)', '(put_integer (put_integer (put_pointer h r o 0 0) r (+ o 8) 0) r (+ o 16) 0)'), 'P_t25_fields': ('(h heap) (r Int) (o Int) (b Int) (bo Int) (s Int) (c Int)', '(and (typed_writes h r o 24 8) (initialized_at h r o) (pointer_at h r o b bo) (initialized_at h r (+ o 8)) (integer_at h r (+ o 8) s) (initialized_at h r (+ o 16)) (integer_at h r (+ o 16) c))'), 'P_t25_inv': ('(h heap) (r Int) (o Int) (b Int) (n Int) (k Int) (v Int)', '(and (well_formed h) (P_t25_fields h r o b 0 0 n) (not (= b r)) (< 0 n) (<= n 4611686018427387903) (<= 0 k) (<= k n) (typed_writes h b 0 (* 4 n) 4) (filled_prefix h b k v))'), 'P_t25v3_ctor_inv': ('(h heap) (r Int) (o Int) (b Int) (n Int) (k Int) (v Int)', '(and (P_t25_inv h r o b n k v) (freeable h b 0) (<= (- 2147483648) v) (<= v 2147483647))'), 'P_t25_frame': ('(old heap) (now heap) (r Int) (o Int)', '(and (forall ((b Int)) (=> (live old b) (same_object old now b))) (forall ((b Int) (p Int)) (=> (and (live old b) (not (and (= b r) (<= o p) (< p (+ o 24))))) (and (= (contents old b p) (contents now b p)) (= (initialized_at old b p) (initialized_at now b p))))))'), 'L_t25_closed_positive': ('(loop heap) (r Int) (n Int)', '(put_integer loop r 8 n)')}
POSITIVE_PREMISE = '(and (well_formed before) (< 0 n) (<= n 2147483647) (P_t25_private_frame entry before) (not (live entry r)) (typed_writes before r 0 24 8) (not (freeable before r 0)) (= b (next before)) (P_t25_frame before loop r 0) (P_t25v3_ctor_inv loop r 0 b n n 7))'
POSITIVE_STATE = '(L_t25_closed_positive loop r n)'

def source_goal(ident, *, positive_branch=False):
    begin = '(begin_automatic entry 24 a)'
    receiver = '(next entry)'
    positive = POSITIVE_STATE
    buffer = '(next ' + begin + ')'
    initial = '(L_t25_initial before r 0)'
    zero_final = '(release (release ' + initial + ' 0) r)'
    positive_final = '(release (release ' + positive + ' b) r)'
    load = '(load_int ' + positive + ' b 0)'
    scalar = load if positive_branch else '(ite (< 0 n) ' + load + ' 0)'
    seven = '7' if positive_branch else '(ite (< 0 n) 7 0)'
    bodies = {'receiver.entry': ('(entry heap) (a Int)', '(=> (and (well_formed entry) (automatic_available entry 24 8 a)) (and (well_formed ' + begin + ') (P_t25_private_frame entry ' + begin + ') (not (live entry ' + receiver + ')) (typed_writes ' + begin + ' ' + receiver + ' 0 24 8) (not (freeable ' + begin + ' ' + receiver + ' 0))))'), 'constructor.frame': ('(entry heap) (before heap) (after heap) (r Int)', '(=> (and (P_t25_private_frame entry before) (not (live entry r)) (P_t25_frame before after r 0)) (P_t25_private_frame entry after))'), 'buffer.identity': ('(entry heap) (a Int)', '(=> (and (well_formed entry) (automatic_available entry 24 8 a)) (and (= ' + buffer + ' (+ (next entry) 1)) (not (issued entry ' + receiver + ')) (not (issued entry ' + buffer + ')) (not (live entry ' + buffer + ')) (not (= ' + buffer + ' ' + receiver + ')) (= (next (L_t25_initial ' + begin + ' ' + receiver + ' 0)) ' + buffer + ')))'), 'zero.cleanup': ('(entry heap) (before heap) (r Int)', '(=> (and (P_t25_private_frame entry before) (not (live entry r)) (typed_writes before r 0 24 8) (not (freeable before r 0))) (exists ((final heap)) (and (= final ' + zero_final + ') (P_t25_private_frame entry final) (not (forms final r 0)))))'), 'positive.exit_image': ('(entry heap) (before heap) (loop heap) (r Int) (b Int) (n Int)', '(=> ' + POSITIVE_PREMISE + ' (and (P_t25_private_frame entry ' + positive + ') (P_t25_private_ids entry r b) (typed_writes ' + positive + ' r 0 24 8) (not (freeable ' + positive + ' r 0)) (freeable ' + positive + ' b 0) (int32_region ' + positive + ' b 0 n) (filled_prefix ' + positive + ' b n 7)))'), 'positive.cleanup': ('(entry heap) (before heap) (loop heap) (r Int) (b Int) (n Int)', '(=> ' + POSITIVE_PREMISE + ' (exists ((final heap) (scalar Int)) (and (= final ' + positive_final + ') (= scalar ' + scalar + ') (= scalar ' + seven + ') (P_t25_private_frame entry final) (P_t25_private_observes entry ' + positive + ' final) (not (forms final r 0)) (not (forms final b 0)))))')}
    bindings, body = bodies[ident]
    return forms('(not (forall (' + bindings + ') ' + body + '))')[0]

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

signal.alarm(60)
resource.setrlimit(resource.RLIMIT_AS, (512*1024**2, 512*1024**2))
root = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-fb197c5d-t25-closed-lifetime6-public-v1/closed-lifetime6-public-v1-profile')
def nnf(value, comparisons=False, implication=False):
    if isinstance(value, str): return value
    if value and value[0]=='let': return nnf(expand(value), comparisons, implication)
    if value and value[0]=='not' and isinstance(value[1], list):
        child=value[1]
        if child[0]=='not': return nnf(child[1], comparisons, implication)
        if child[0] in {'and','or'}:
            return nnf(['or' if child[0]=='and' else 'and', *[['not',x] for x in child[1:]]], comparisons, implication)
        if comparisons and child[0] in {'<','<='}:
            return nnf(['<=' if child[0]=='<' else '<', child[2], child[1]], comparisons, implication)
    if value and implication and value[0]=='=>':
        return nnf(['or',['not',value[1]],value[2]], comparisons, implication)
    return [nnf(x, comparisons, implication) for x in value]
rows=[]
for ident in ('receiver.entry','constructor.frame','buffer.identity','zero.cleanup','positive.exit_image','positive.cleanup'):
    for path in sorted((root/('leaf-'+ident)).rglob('*.psmt2'))+sorted((root/('leaf-'+ident)).rglob('*.smt2')):
        tree=forms(path.read_text())
        for definition in [d for d in tree if d[0]=='define-fun' and d[1].startswith(('P_t25','L_t25'))]:
            name=definition[1]
            bindings,body=SOURCE_DEFINITIONS[name]
            expected=forms('(forall ('+bindings+') '+body+')')[0]
            actual=['forall', definition[2], definition[-1]]
            variants={}
            for label,options in [('literal',{}),('demorgan',{}),('demorgan_comparisons',{'comparisons':True}),('demorgan_comparisons_implication',{'comparisons':True,'implication':True})]:
                left,right=(actual,expected) if label=='literal' else (nnf(actual,**options),nnf(expected,**options))
                variants[label]=canon(left)==canon(right)
            rows.append({'id':ident,'task':path.name,'task_sha256':pin(path)['sha256'],'definition':name,
                         'actual_definition_sha256':digest(definition),'expected_definition_sha256':digest(expected),
                         'source_equivalence_variants':variants})
print(json.dumps({'classification':'PASSIVE_IN_PLACE_DEFINITION_NORMALIZATION_DISCOVERY','rows':rows,
                  'raw_terms_transferred':False,'scientific_execution':False,'acceptance':False},sort_keys=True,indent=2))
