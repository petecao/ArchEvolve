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
