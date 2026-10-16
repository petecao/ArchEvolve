"""Qualified int grow source VC preparation; created 2026-10-16 ET.

Definitions and isolated pending check lemmas, never desired-result axioms.
The complete public model/caller route remains closed until all maps exist.
"""
from pathlib import Path
import ast
import hashlib
import json
import re

from swdb import vector_reallocation_model as model
from swdb.heap_model_vcs import PRELUDE as ORIGINAL_PRELUDE
from swdb.heap_model_vcs import NUMERIC as CTOR_NUMERIC

HERE = Path(__file__).parent
PRELUDE = ORIGINAL_PRELUDE + r'''
/*@ predicate t25v3_repr(Heap::heap h, integer r, integer o, integer b, integer bo,
                         integer s, integer c) =
      t25_repr(h,r,o,b,bo,s,c) && Heap::int32_region(h,b,bo,s);
    predicate t25v3_ctor_inv(Heap::heap h, integer r, integer o, integer b,
                            integer n, integer k, integer v) =
      t25_inv(h,r,o,b,n,k,v) && Heap::freeable(h,b,0) &&
      -2147483648 <= v <= 2147483647;
    predicate t25v3_eligible(Heap::heap h, integer r, integer o, integer b, integer bo,
                             integer s, integer c) =
      t25v3_repr(h,r,o,b,bo,s,c) &&
      (c == 0 || (Heap::freeable(h,b,bo) && r != b));
    predicate t25v3_copy_frame(Heap::heap entry, Heap::heap h, integer fresh) =
      Heap::fresh_id(h) == Heap::fresh_id(entry)+1 &&
      (\forall integer x; x != fresh ==> Heap::same_object(entry,h,x)) &&
      (\forall integer x,p; x != fresh ==>
        Heap::contents(entry,x,p) == Heap::contents(h,x,p) &&
        (Heap::initialized_at(entry,x,p) <==> Heap::initialized_at(h,x,p)));
    predicate t25v3_copy_inv(Heap::heap entry, Heap::heap h,
                           integer r, integer o, integer b, integer bo,
                           integer s, integer c, integer f, integer cap, integer k) =
      Heap::well_formed(entry) && Heap::well_formed(h) &&
      t25v3_eligible(entry,r,o,b,bo,s,c) && t25v3_eligible(h,r,o,b,bo,s,c) &&
      0 <= k <= s <= c < cap <= 4611686018427387903 &&
      f == Heap::fresh_id(entry) && !Heap::issued(entry,f) && f != r && f != b &&
      Heap::typed_writes(h,f,0,4*cap,4) && Heap::freeable(h,f,0) && Heap::bytes(h,f) == 4*cap &&
      t25v3_copy_frame(entry,h,f) && Heap::copied_prefix(entry,h,b,bo,f,k) &&
      (\forall integer j; k <= j < cap ==> !Heap::initialized_at(h,f,4*j));
    logic Heap::heap t25v3_grown(Heap::heap h, integer r, integer o,
                               integer old, integer fresh, integer cap) =
      Heap::put_integer(Heap::put_pointer(Heap::release(h,old),r,o,fresh,0),r,o+16,cap);
    predicate t25v3_grow_frame(Heap::heap entry, Heap::heap now,
                             integer r, integer o, integer old) =
      (\forall integer x; Heap::live(entry,x) && x != old ==>
        Heap::same_object(entry,now,x)) &&
      (\forall integer x,p; Heap::live(entry,x) && x != old &&
        !(x == r && o <= p < o+24) ==>
        Heap::contents(entry,x,p) == Heap::contents(now,x,p) &&
        (Heap::initialized_at(entry,x,p) <==> Heap::initialized_at(now,x,p)));
*/
'''

GROW_NUMERIC = CTOR_NUMERIC.split('/*@ requires', 1)[0] + r'''
/* Qualified original grow's size/cap/index arithmetic; 2026-10-16 ET. */
/*@ requires size <= oldcap && oldcap < cap && cap <= 4611686018427387903 && k < size;
    assigns \nothing;
    ensures \result == k+1 && \result <= size;
*/
size_t t25v3_grow_numeric(size_t size, size_t oldcap, size_t cap, size_t k) {
  size_t next=k+1;
  size_t bytes=cap*sizeof(int);
  /*@ assert allocation_size_no_wrap: (integer)cap*4 <= 18446744073709551615; */
  /*@ assert allocation_size_exact: bytes == (integer)cap*4; */
  /*@ assert source_index_in_size: (integer)k*4+4 <= (integer)size*4; */
  /*@ assert destination_index_in_capacity: (integer)k*4+4 <= bytes; */
  /*@ assert variant_nonnegative: 0 <= (integer)size-k; */
  /*@ assert variant_decreases: 0 <= (integer)size-next < (integer)size-k; */
  return next;
}
'''


def grow_specs():
    prefix = r'\forall Heap::heap entry,h; \forall integer r,o,b,bo,s,c,f,cap,k; '
    inv = 't25v3_copy_inv(entry,h,r,o,b,bo,s,c,f,cap,k)'
    done = 't25v3_copy_inv(entry,h,r,o,b,bo,s,c,f,cap,s)'
    grown = 't25v3_grown(h,r,o,b,f,cap)'
    return [
      ('control.grow.premises_feasible', ['G1','G2','G3'],
       'requires std_vector_int_reallocatable_v3(this)',
       r'Heap::well_formed(t25_sample(0)) && t25v3_eligible(t25_sample(0),1,0,2,0,1,1) && '
       r'Heap::available(t25_sample(0),2,128) && '
       r't25v3_copy_inv(t25_sample(0),Heap::allocate(t25_sample(0),2,128),1,0,2,0,1,1,3,2,0)'),
      ('grow.entry.reads', ['G1'], 'requires std_vector_int_reallocatable_v3(this)',
       r'\forall Heap::heap h; \forall integer r,o,b,bo,s,c; '
       r't25v3_eligible(h,r,o,b,bo,s,c) ==> '
       r'Heap::typed_reads(h,r,o,8,8) && Heap::initialized_at(h,r,o) && '
       r'Heap::typed_reads(h,r,o+8,8,8) && Heap::initialized_at(h,r,o+8) && '
       r'Heap::typed_reads(h,r,o+16,8,8) && Heap::initialized_at(h,r,o+16)'),
      ('grow.entry.int_projection', ['G1'], 'requires std_vector_int_reallocatable_v3(this)',
       r'\forall Heap::heap h; \forall Heap::int_values values; \forall integer r,o,b,bo,s,c; '
       r't25_repr(h,r,o,b,bo,s,c) && (s == 0 || r != b) && Heap::bounded_int_values(values,bo,s) ==> '
       r't25v3_repr(Heap::project_int_region(h,values,b,bo,s),r,o,b,bo,s,c)'),
      ('grow.alloc.identity', ['G2'], '= swdb_alloc_int(cap);',
       r'\forall Heap::heap h; \forall integer r,o,b,bo,s,c,cap; '
       r'Heap::well_formed(h) && t25v3_eligible(h,r,o,b,bo,s,c) && c < cap ==> '
       r'Heap::fresh_id(h) != r && Heap::fresh_id(h) != b && !Heap::issued(h,Heap::fresh_id(h))'),
      ('grow.alloc.output', ['G2'], '= swdb_alloc_int(cap);',
       r'\forall Heap::heap h; \forall integer cap,a; '
       r'Heap::well_formed(h) && Heap::available(h,cap,a) && 0 < cap ==> '
       r'Heap::well_formed(Heap::allocate(h,cap,a)) && '
       r'Heap::typed_writes(Heap::allocate(h,cap,a),Heap::fresh_id(h),0,4*cap,4) && '
       r'Heap::freeable(Heap::allocate(h,cap,a),Heap::fresh_id(h),0) && '
       r'Heap::bytes(Heap::allocate(h,cap,a),Heap::fresh_id(h)) == 4*cap'),
      ('grow.alloc.frame', ['G2','G9'], '= swdb_alloc_int(cap);',
       r'\forall Heap::heap h; \forall integer cap,a; Heap::well_formed(h) ==> '
       r't25v3_copy_frame(h,Heap::allocate(h,cap,a),Heap::fresh_id(h))'),
      ('grow.copy.establish', ['G3'], 'for (size_t k = 0;',
       r'\forall Heap::heap entry; \forall integer r,o,b,bo,s,c,cap,a; '
       r'Heap::well_formed(entry) && t25v3_eligible(entry,r,o,b,bo,s,c) && '
       r'c < cap <= 4611686018427387903 && Heap::available(entry,cap,a) ==> '
       r't25v3_copy_inv(entry,Heap::allocate(entry,cap,a),r,o,b,bo,s,c,Heap::fresh_id(entry),cap,0)'),
      ('grow.copy.read', ['G4'], 'fresh[k] = this->data[k];',
       prefix + inv + r' && k < s ==> Heap::int32_at(h,b,bo+4*k) && '
       r'Heap::load_int(h,b,bo+4*k) == Heap::load_int(entry,b,bo+4*k) && '
       r'Heap::typed_forms(h,b,bo+4*k,4)'),
      ('grow.copy.write', ['G5'], 'fresh[k] = this->data[k];',
       prefix + inv + r' && k < s ==> Heap::typed_forms(h,f,4*k,4) && Heap::typed_writes(h,f,4*k,4,4)'),
      ('grow.copy.step', ['G5','G6','G9'], 'fresh[k] = this->data[k];',
       prefix + inv + r' && k < s ==> '
       r't25v3_copy_inv(entry,Heap::copy_int(h,b,bo+4*k,f,4*k),r,o,b,bo,s,c,f,cap,k+1)'),
      ('grow.copy.exit', ['G6'], 'swdb_free(this->data);',
       prefix + inv + r' && !(k < s) ==> k == s && Heap::copied_prefix(entry,h,b,bo,f,s)'),
      ('grow.free.argument', ['G7'], 'swdb_free(this->data);',
       prefix + done + r' ==> (b == 0 && bo == 0) || Heap::freeable(h,b,bo)'),
      ('grow.free.survival', ['G7','G8'], 'swdb_free(this->data);',
       prefix + done + r' ==> Heap::typed_writes(Heap::release(h,b),r,o,8,8) && '
       r'Heap::typed_writes(Heap::release(h,b),r,o+16,8,8) && Heap::typed_writes(Heap::release(h,b),f,0,4*cap,4)'),
      ('grow.free.aliases', ['G7'], 'swdb_free(this->data);',
       prefix + done + r' && c > 0 ==> '
       r'(\forall integer p; !Heap::forms(Heap::release(h,b),b,p) && !Heap::can_read(Heap::release(h,b),b,p,4))'),
      ('grow.store.capacity', ['G8'], 'this->capacity = cap;',
       prefix + done + r' ==> Heap::typed_writes(Heap::put_pointer(Heap::release(h,b),r,o,f,0),r,o+16,8,8)'),
      ('grow.post.eligibility', ['G8'], 'ensures std_vector_int_reallocatable_v3(this)',
       prefix + done + ' ==> t25v3_eligible(' + grown + r',r,o,f,0,s,cap)'),
      ('grow.post.values', ['G8','G9'], 'this->data[k] == \\old(this->data[k])',
       prefix + done + ' ==> Heap::copied_prefix(entry,' + grown + r',b,bo,f,s)'),
      ('grow.post.old_invalid', ['G7','G9'], '!\\valid(\\old(this->data))',
       prefix + done + ' && c > 0 ==> !Heap::can_read(' + grown + r',b,bo,4)'),
      ('grow.post.frame', ['G9'], 'assigns *this;',
       prefix + done + ' ==> t25v3_grow_frame(entry,' + grown + r',r,o,b)'),
      ('grow.numeric', ['G2','G6'], 'for (size_t k = 0; k < this->size; ++k)', None),
    ]


def constructor_specs():
    from swdb.heap_model_vcs import specs
    rows = []
    for name, member, needle, groups, statement in specs():
        if member != 'std_vector_int_ctor_count_value' or name == 'control.omitted_store':
            continue
        if statement is not None:
            statement = statement.replace('t25_inv(', 't25v3_ctor_inv(')
            if name == 'ctor.capacity.entry':
                # A C int parameter supplies its signed32 representation range.
                # It is source-typing semantics, never a new C requires clause.
                statement = statement.replace(' ==> ', ' && -2147483648 <= v <= 2147483647 ==> ', 1)
        rows.append((name, groups, needle, statement))
    rows += [
      ('control.ctor.qualified_feasible', ['C3','C5','QC2'], 'this->data = swdb_alloc_int(n);',
       r't25v3_ctor_inv(t25_allocated(Heap::allocate(Heap::empty(0),6,8),1,0,1,64),1,0,2,1,0,7)'),
      ('ctor.qualified.zero_post', ['C2','QC1','QC2'], 'if (n == 0) return;',
       r'\forall Heap::heap h; \forall integer r,o; Heap::typed_writes(h,r,o,24,8) ==> '
       r't25v3_eligible(t25_initial(h,r,o),r,o,0,0,0,0)'),
      ('ctor.qualified.positive_post', ['C8','QC1','QC2'], 'this->size = n;',
       r'\forall Heap::heap h; \forall integer r,o,b,n,v; t25v3_ctor_inv(h,r,o,b,n,n,v) ==> '
       r't25v3_eligible(Heap::put_integer(h,r,o+8,n),r,o,b,0,n,n)'),
    ]
    return rows


def destructor_specs():
    from swdb.heap_model_vcs import specs
    negatives = {'control.wrong_release', 'control.stale_read', 'control.double_release'}
    return [(name, groups, needle, statement) for name, member, needle, groups, statement in specs()
            if member == 'std_vector_int_dtor' and name not in negatives]


def reserve_specs():
    entry = (r'\forall Heap::heap h; \forall integer r,o,b,bo,s,c,n; '
             r't25v3_eligible(h,r,o,b,bo,s,c) && n <= 4611686018427387903')
    done = (r'\forall Heap::heap entry,h; \forall integer r,o,b,bo,s,c,f,n; '
            r't25v3_copy_inv(entry,h,r,o,b,bo,s,c,f,n,s)')
    final = 't25v3_grown(h,r,o,b,f,n)'
    needle = 'if (n > this->capacity) std_vector_int_realloc_v3_grow(this, n);'
    return [
      ('reserve.entry.capacity', ['R1'], needle,
       entry + r' ==> Heap::typed_reads(h,r,o+16,8,8) && Heap::initialized_at(h,r,o+16)'),
      ('reserve.no_growth', ['R2'], needle,
       entry + r' && !(n > c) ==> t25v3_eligible(h,r,o,b,bo,s,c) && c >= n && '
       r'Heap::pointer_at(h,r,o,b,bo) && Heap::int32_region(h,b,bo,s)'),
      ('reserve.growing.pre', ['R1'], needle,
       entry + r' && n > c ==> s <= n && n > c && '
       r'(c == 0 || (Heap::freeable(h,b,bo) && r != b))'),
      ('reserve.growing.post', ['R3'], needle,
       done + ' ==> t25v3_eligible(' + final + ',r,o,f,0,s,n) && Heap::copied_prefix(entry,' + final + ',b,bo,f,s)'),
      ('reserve.growing.old_invalid', ['R3'], needle,
       done + ' && c > 0 ==> !Heap::can_read(' + final + ',b,bo,4)'),
      ('reserve.growing.frame', ['R3'], needle,
       done + ' ==> t25v3_grow_frame(entry,' + final + ',r,o,b)'),
    ]


def member_specs(member):
    if member.endswith('_ctor_count_value'):
        return constructor_specs()
    if member.endswith('_dtor'):
        return destructor_specs()
    if member.endswith('_reserve'):
        # The complete helper body is part of this public source unit. Every
        # induction duty is reproved here; no desired grow lemma is imported.
        return grow_specs() + reserve_specs()
    if member.endswith('_grow'):
        return grow_specs()
    raise ValueError('qualified member has no mapped source inventory')


def projection_parts(statement):
    """Exact conjunction/forall expansion; neither piece assumes the other."""
    quantifiers = (r'\forall Heap::heap h; \forall Heap::int_values values; '
                   r'\forall integer r,o,b,bo,s,c; ')
    antecedent = (r't25_repr(h,r,o,b,bo,s,c) && (s == 0 || r != b) && '
                  r'Heap::bounded_int_values(values,bo,s)')
    projected = 'Heap::project_int_region(h,values,b,bo,s)'
    representation = 't25_repr(' + projected + ',r,o,b,bo,s,c)'
    original = quantifiers + antecedent + ' ==> t25v3_repr(' + projected + ',r,o,b,bo,s,c)'
    if statement != original or re.search(r'\bj\b', quantifiers + antecedent + representation):
        raise ValueError('projection expansion requires the exact original formula and a fresh index')
    repr_definition = r'''predicate t25v3_repr(Heap::heap h, integer r, integer o, integer b, integer bo,
                         integer s, integer c) =
      t25_repr(h,r,o,b,bo,s,c) && Heap::int32_region(h,b,bo,s);'''
    region_definition = '''predicate int32_region (h:heap) (b offset count:int) =
    forall j:int. 0 <= j < count -> int32_at h b (offset+4*j)'''
    if PRELUDE.count(repr_definition) != 1:
        raise ValueError('the represented-heap conjunction definition changed')
    definitions = []
    for name, text in [('vector_reallocation_vcs.py', repr_definition),
                       ('heap_reallocation.mlw', region_definition)]:
        raw = (HERE/name).read_bytes()
        encoded = text.encode()
        begin = raw.index(encoded)
        definitions.append({'path':name, 'begin':begin, 'end':begin+len(encoded),
                            'sha256':hashlib.sha256(encoded).hexdigest(),
                            'container_sha256':hashlib.sha256(raw).hexdigest()})
    cell_quantifiers = quantifiers + r'\forall integer j; '
    cell_antecedent = antecedent + ' && 0 <= j < s'
    cell_statement = cell_quantifiers + cell_antecedent + ' ==> Heap::int32_at(' + projected + ',b,bo+4*j)'
    cell_definition = '''predicate int32_at (h:heap) (b o:int) =
    typed_reads h b o 4 4 /\\ initialized_at h b o /\\
    integer_at h b o (load_int h b o) /\\
    -2147483648 <= load_int h b o <= 2147483647'''
    cell_raw = (HERE/'heap_reallocation.mlw').read_bytes()
    encoded = cell_definition.encode()
    if cell_raw.count(encoded) != 1:
        raise ValueError('the exact projected-cell conjunction definition changed')
    begin = cell_raw.index(encoded)
    load = 'Heap::load_int(' + projected + ',b,bo+4*j)'
    conjuncts = [
        ('access', 'Heap::typed_reads(' + projected + ',b,bo+4*j,4,4)'),
        ('initialization', 'Heap::initialized_at(' + projected + ',b,bo+4*j)'),
        ('integer', 'Heap::integer_at(' + projected + ',b,bo+4*j,' + load + ')'),
        ('bounds', '-2147483648 <= ' + load + ' <= 2147483647'),
    ]
    cells = [('grow.entry.int_projection.cells.' + name,
              cell_quantifiers + cell_antecedent + ' ==> ' + formula) for name,formula in conjuncts]
    expansion = {'id':'grow.entry.int_projection.cells','original_statement':cell_statement,
        'quantifiers':cell_quantifiers,'antecedent':cell_antecedent,'outer_antecedent':antecedent,
        'parts':[name for name,_ in cells],
        'combination':'AND: all four independent definition conjuncts are required',
        'equivalence':'A implies (access and initialized and integer-tag/load and signed32-bounds) iff all four A-implies-conjunct duties',
        'definition_source':{'path':'heap_reallocation.mlw','begin':begin,'end':begin+len(encoded),
            'sha256':hashlib.sha256(encoded).hexdigest(),'container_sha256':hashlib.sha256(cell_raw).hexdigest()},
        'definition_substitution':{'h':projected,'b':'b','o':'bo+4*j'},
        'premises_added':[],'dependencies':[],
        'reference_role':'original logical cell target only; never imported or launched as a proved result'}
    parts = [('grow.entry.int_projection.repr', quantifiers + antecedent + ' ==> ' + representation), *cells]
    return parts, {'id':'grow.entry.int_projection', 'original_statement':original,
        'quantifiers':quantifiers, 'antecedent':antecedent, 'fresh_index':'j',
        'fresh_index_free_in_antecedent':False, 'fresh_index_bound_in_outer_quantifiers':False,
        'parts':[name for name,_ in parts], 'combination':'AND: representation and all four independent cell conjuncts are required',
        'equivalence':'A implies (R and forall j: B implies I) iff (A implies R) and all four forall-fresh-j (A and B) implies int32_at-definition-conjunct duties',
        'definition_sources':definitions, 'component_expansions':[expansion], 'premises_added':[], 'dependencies':[],
        'region_substitution':{'h':projected, 'b':'b', 'offset':'bo', 'count':'s', 'j':'j'},
        'reference_role':'original logical target only; never imported or launched as a proved result'}


def _logic_tokens(text):
    """Closed ACSL expression vocabulary; never skip an unknown character."""
    pattern = re.compile(r'\s+|\\forall|[A-Za-z_]\w*(?:::[A-Za-z_]\w*)*|[0-9]+|<==>|==>|&&|\|\||==|!=|<=|>=|[(),;!<>+*\-/]')
    tokens, offset = [], 0
    while offset < len(text):
        match = pattern.match(text, offset)
        if match is None:
            raise ValueError('unsupported conjunction expression token')
        if not match[0].isspace():
            tokens.append((match[0], match.start(), match.end()))
        offset = match.end()
    return tokens


def _top_parts(text, separator):
    tokens = _logic_tokens(text)
    depth, begin, parts = 0, 0, []
    for token, start, end in tokens:
        if token == '(':
            depth += 1
        elif token == ')':
            depth -= 1
            if depth < 0:
                raise ValueError('unbalanced conjunction expression')
        elif depth == 0:
            if token == separator:
                parts.append(text[begin:start].strip())
                begin = end
            elif separator == '&&' and token in {'||', '==>', '<==>', r'\forall', ';'}:
                raise ValueError('conjunction has an unparenthesized lower-precedence operator or binder')
    if depth:
        raise ValueError('unbalanced conjunction expression')
    parts.append(text[begin:].strip())
    if any(not part for part in parts):
        raise ValueError('empty conjunction expression component')
    return parts


def predicate_conjuncts(definition, arguments):
    """Instantiate a closed predicate's top-level AND, refusing binder capture.

    This is a deliberately small source transformation, not an ACSL parser.
    Arguments are integer +,-,* terms and function applications; unsupported terms/scopes fail
    closed. Simultaneous token replacement cannot rewrite a callee or a newly
    inserted argument, and every nested bound name must be fresh in all args.
    """
    header = re.fullmatch(r'predicate ([A-Za-z_]\w*)\((.*?)\)\s*=\s*(.*);', definition, re.S)
    if header is None:
        raise ValueError('one complete predicate definition required')
    formals = []
    for formal in header[2].split(','):
        match = re.fullmatch(r'\s*(?:integer|Heap::heap)\s+([A-Za-z_]\w*)\s*', formal)
        if match is None or match[1] in formals or match[1] in {'integer', 'predicate', 'logic'}:
            raise ValueError('unsupported or duplicate predicate formal')
        formals.append(match[1])
    if len(formals) != len(arguments):
        raise ValueError('predicate substitution arity differs')
    def term(text):
        tokens = [row[0] for row in _logic_tokens(text)]
        def atom(index):
            if index < len(tokens) and tokens[index] == '(':
                index, _atomic = expression(index+1)
                if index >= len(tokens) or tokens[index] != ')':
                    raise ValueError('unbalanced substitution term')
                return index+1, True
            if index < len(tokens) and tokens[index] == '-':
                index, _atomic = atom(index+1)
                return index, False
            if index >= len(tokens) or not re.fullmatch(r'[A-Za-z_]\w*(?:::[A-Za-z_]\w*)*|[0-9]+', tokens[index]):
                raise ValueError('unsupported substitution term atom')
            index += 1
            if index < len(tokens) and tokens[index] == '(':
                if tokens[index-1].isdigit():
                    raise ValueError('a numeric atom cannot be a substitution callee')
                index += 1
                if index < len(tokens) and tokens[index] != ')':
                    index, _atomic = expression(index)
                    while index < len(tokens) and tokens[index] == ',':
                        index, _atomic = expression(index+1)
                if index >= len(tokens) or tokens[index] != ')':
                    raise ValueError('malformed substitution function application')
                index += 1
            return index, True
        def product(index):
            index, atomic = atom(index)
            while index < len(tokens) and tokens[index] == '*':
                index, _atomic = atom(index+1)
                atomic = False
            return index, atomic
        def expression(index):
            index, atomic = product(index)
            while index < len(tokens) and tokens[index] in {'+', '-'}:
                index, _atomic = product(index+1)
                atomic = False
            return index, atomic
        end, atomic = expression(0)
        if end != len(tokens):
            raise ValueError('unsupported substitution term')
        return ({token for token in tokens if re.fullmatch(r'[A-Za-z_]\w*', token)},
                text if atomic else '('+text+')')
    terms = [term(arg) for arg in arguments]
    argument_names = set().union(*(names for names, _text in terms))
    body = header[3]
    conjuncts = _top_parts(body, '&&')
    tokens = _logic_tokens(body)
    bound, scopes, declarations = set(), [], set()
    for index, (token, _start, _end) in enumerate(tokens):
        if token != r'\forall':
            continue
        if index == 0 or tokens[index-1][0] != '(':
            raise ValueError('nested predicate binders require an explicit enclosing scope')
        tail = [row[0] for row in tokens[index+1:]]
        if not tail or tail[0] != 'integer' or ';' not in tail:
            raise ValueError('unsupported nested predicate binder')
        names = tail[1:tail.index(';')]
        if not names or any(not re.fullmatch(r'[A-Za-z_]\w*', value) if i % 2 == 0 else value != ','
                            for i, value in enumerate(names)) or len(names) % 2 == 0:
            raise ValueError('malformed nested predicate binder')
        variables = names[::2]
        if len(set(variables)) != len(variables) or set(variables) & (bound | set(formals) | argument_names | {'integer', 'predicate', 'logic'}):
            raise ValueError('predicate substitution would shadow or capture a bound name')
        bound.update(variables)
        semicolon = index+1+tail.index(';')
        depth, close = 1, index
        while depth:
            close += 1
            if close >= len(tokens):
                raise ValueError('unterminated predicate binder scope')
            depth += (tokens[close][0] == '(') - (tokens[close][0] == ')')
        declarations.update(range(index+1, semicolon+1))
        scopes.append((semicolon, close, set(variables)))
    for index, (token, _start, _end) in enumerate(tokens):
        if index in declarations:
            continue
        if token == ';':
            raise ValueError('predicate contains an unsupported clause separator')
        if not re.fullmatch(r'[A-Za-z_]\w*(?:::[A-Za-z_]\w*)*', token):
            continue
        callee = index+1 < len(tokens) and tokens[index+1][0] == '('
        if callee and token in set(formals) | bound:
            raise ValueError('predicate variables cannot be function symbols')
        active = set().union(*(names for start, end, names in scopes if start < index < end))
        if not callee and token not in set(formals) | active:
            raise ValueError('unbound symbol in predicate conjunction')
    mapping = dict(zip(formals, [text for _names, text in terms], strict=True))
    def substitute(expression):
        result, begin = [], 0
        for token, start, end in _logic_tokens(expression):
            result.extend((expression[begin:start], mapping.get(token, token)))
            begin = end
        result.append(expression[begin:])
        return ''.join(result)
    return [substitute(part) for part in conjuncts], {
        'predicate': header[1], 'formal_parameters': formals,
        'definition_conjuncts': conjuncts, 'definition_substitution': mapping,
        'nested_bound_variables': sorted(bound), 'capture_avoiding': True}


def copy_establish_parts(statement):
    quantifiers = r'\forall Heap::heap entry; \forall integer r,o,b,bo,s,c,cap,a; '
    antecedent = (r'Heap::well_formed(entry) && t25v3_eligible(entry,r,o,b,bo,s,c) && '
                  r'c < cap <= 4611686018427387903 && Heap::available(entry,cap,a)')
    arguments = ['entry', 'Heap::allocate(entry,cap,a)', 'r', 'o', 'b', 'bo', 's', 'c',
                 'Heap::fresh_id(entry)', 'cap', '0']
    original = quantifiers + antecedent + ' ==> t25v3_copy_inv(' + ','.join(arguments) + ')'
    if statement != original:
        raise ValueError('copy establishment expansion requires the exact original full premise')
    begin = PRELUDE.index('predicate t25v3_copy_inv(')
    end = PRELUDE.index('    logic Heap::heap t25v3_grown', begin)
    definition = PRELUDE[begin:end].strip()
    conjuncts, binding = predicate_conjuncts(definition, arguments)
    labels = ['entry_well_formed', 'allocated_well_formed', 'entry_eligible', 'allocated_eligible',
              'index_size_capacity_bounds', 'fresh_identity', 'unissued_identity', 'receiver_distinct',
              'old_buffer_distinct', 'destination_write_domain', 'destination_freeability',
              'destination_extent', 'allocation_frame', 'empty_copied_prefix', 'uninitialized_tail']
    if len(conjuncts) != len(labels):
        raise ValueError('the complete copy invariant conjunction census changed')
    raw = (HERE/'vector_reallocation_vcs.py').read_bytes()
    encoded = definition.encode()
    if raw.count(encoded) != 1:
        raise ValueError('copy invariant definition is not the unique physical source definition')
    offset = raw.index(encoded)
    parts = [('grow.copy.establish.' + label, quantifiers + antecedent + ' ==> ' + formula)
             for label, formula in zip(labels, conjuncts, strict=True)]
    return parts, {**binding, 'id': 'grow.copy.establish', 'original_statement': original,
        'quantifiers': quantifiers, 'antecedent': antecedent, 'substituted_conjuncts': conjuncts,
        'parts': [name for name, _formula in parts], 'premises_added': [], 'dependencies': [],
        'definition_source': {'path': 'vector_reallocation_vcs.py', 'begin': offset,
            'end': offset+len(encoded), 'sha256': hashlib.sha256(encoded).hexdigest(),
            'container_sha256': hashlib.sha256(raw).hexdigest()},
        'combination': 'AND: all fifteen independent definition conjuncts are required',
        'equivalence': 'A implies AND(conjuncts) iff AND(each A implies conjunct); simultaneous capture-free predicate substitution',
        'reference_role': 'original logical target only; never imported or launched as a proved result'}


def copy_step_parts(statement):
    """Expand only the exact source step conclusion, retaining its whole guard."""
    quantifiers = r'\forall Heap::heap entry,h; \forall integer r,o,b,bo,s,c,f,cap,k; '
    antecedent = 't25v3_copy_inv(entry,h,r,o,b,bo,s,c,f,cap,k) && k < s'
    arguments = ['entry', 'Heap::copy_int(h,b,bo+4*k,f,4*k)', 'r', 'o', 'b', 'bo',
                 's', 'c', 'f', 'cap', 'k+1']
    original = quantifiers + antecedent + ' ==> t25v3_copy_inv(' + ','.join(arguments) + ')'
    if statement != original:
        raise ValueError('copy step expansion requires the exact original full premise and transition')
    definition, source = _source_definition('t25v3_copy_inv', '    logic Heap::heap t25v3_grown')
    conjuncts, binding = predicate_conjuncts(definition, arguments)
    labels = ['entry_well_formed', 'updated_well_formed', 'entry_eligible', 'updated_eligible',
              'advanced_index_size_capacity_bounds', 'fresh_identity', 'unissued_identity',
              'receiver_distinct', 'old_buffer_distinct', 'destination_write_domain',
              'destination_freeability', 'destination_extent', 'allocation_frame',
              'advanced_copied_prefix', 'uninitialized_tail']
    if len(conjuncts) != len(labels):
        raise ValueError('the complete copy step invariant conjunction census changed')
    parts = [('grow.copy.step.' + label, quantifiers + antecedent + ' ==> ' + formula)
             for label, formula in zip(labels, conjuncts, strict=True)]
    return parts, {**binding, 'id': 'grow.copy.step', 'original_statement': original,
        'quantifiers': quantifiers, 'antecedent': antecedent, 'substituted_conjuncts': conjuncts,
        'parts': [name for name, _formula in parts], 'premises_added': [], 'dependencies': [],
        'definition_source': source,
        'combination': 'AND: all fifteen independent step definition conjuncts are required',
        'equivalence': 'A implies AND(conjuncts) iff AND(each A implies conjunct); simultaneous capture-free predicate substitution',
        'reference_role': 'original logical target only; never imported or launched as a proved result'}



def copy_prefix_parts(statement):
    """Expand the exact next prefix over exhaustive old-cell/new-cell cases."""
    quantifiers = r'\forall Heap::heap entry,h; \forall integer r,o,b,bo,s,c,f,cap,k; '
    antecedent = 't25v3_copy_inv(entry,h,r,o,b,bo,s,c,f,cap,k) && k < s'
    heap = 'Heap::copy_int(h,b,bo+4*k,f,4*k)'
    original = quantifiers + antecedent + ' ==> Heap::copied_prefix(entry,' + heap + ',b,bo,f,(k+1))'
    if statement != original or re.search(r'\bj\b', quantifiers + antecedent + heap):
        raise ValueError('prefix cases require the exact full original premise and a fresh index')
    prefix_definition = r'''  predicate copied_prefix (entry now:heap) (source source_offset target count:int) =
    forall j:int. 0 <= j < count ->
      int32_at now target (4*j) /\
      load_int now target (4*j) = load_int entry source (source_offset+4*j)'''
    cell_definition = r'''  predicate int32_at (h:heap) (b o:int) =
    typed_reads h b o 4 4 /\ initialized_at h b o /\
    integer_at h b o (load_int h b o) /\
    -2147483648 <= load_int h b o <= 2147483647'''
    raw = (HERE/'heap_reallocation.mlw').read_bytes()
    definitions = []
    for definition in (prefix_definition, cell_definition):
        encoded = definition.encode()
        if raw.count(encoded) != 1:
            raise ValueError('the exact prefix/cell source definition changed')
        begin = raw.index(encoded)
        definitions.append({'path':'heap_reallocation.mlw', 'begin':begin, 'end':begin+len(encoded),
            'sha256':hashlib.sha256(encoded).hexdigest(), 'container_sha256':hashlib.sha256(raw).hexdigest()})
    load = 'Heap::load_int(' + heap + ',f,4*j)'
    conclusions = [
        ('access', 'Heap::typed_reads(' + heap + ',f,4*j,4,4)'),
        ('initialization', 'Heap::initialized_at(' + heap + ',f,4*j)'),
        ('integer', 'Heap::integer_at(' + heap + ',f,4*j,' + load + ')'),
        ('bounds', '-2147483648 <= ' + load + ' <= 2147483647'),
        ('value', load + ' == Heap::load_int(entry,b,bo+4*j)'),
    ]
    cases = [{'id':'prior', 'guard':'j < k'}, {'id':'written', 'guard':'j == k'}]
    prefix_quantifiers = quantifiers + r'\forall integer j; '
    index_range = '0 <= j < (k+1)'
    parts = [('grow.copy.step.advanced_copied_prefix.' + case['id'] + '.' + label,
              prefix_quantifiers + antecedent + ' && ' + index_range + ' && ' + case['guard'] + ' ==> ' + formula)
             for case in cases for label, formula in conclusions]
    return parts, {'id':'grow.copy.step.advanced_copied_prefix', 'original_statement':original,
        'quantifiers':prefix_quantifiers, 'outer_antecedent':antecedent, 'range':index_range,
        'fresh_index':'j', 'fresh_index_free_in_antecedent':False,
        'case_partition':cases, 'conclusions':dict(conclusions),
        'parts':[name for name, _formula in parts], 'definition_sources':definitions,
        'definition_substitution':{'copied_prefix':{'entry':'entry', 'now':heap, 'source':'b',
            'source_offset':'bo', 'target':'f', 'count':'(k+1)'},
            'int32_at':{'h':heap, 'b':'f', 'o':'4*j'}},
        'premises_added':[], 'dependencies':[],
        'combination':'AND: both exhaustive integer cases require all five prefix definition conclusions',
        'equivalence':'Under the original integer range j < k+1, j < k or j == k exhausts all cases; forall and full-A implication distribute over every definition conjunct',
        'reference_role':'original logical prefix target only; never imported or launched as a proved result'}


def _source_definition(name, following):
    start = PRELUDE.index('predicate ' + name + '(')
    end = PRELUDE.index(following, start)
    definition = PRELUDE[start:end].strip()
    raw = (HERE/'vector_reallocation_vcs.py').read_bytes()
    encoded = definition.encode()
    assignments = [node for node in ast.parse(raw).body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'PRELUDE' for target in node.targets)]
    if len(assignments) != 1 or not isinstance(assignments[0].value, ast.BinOp) or \
            not isinstance(assignments[0].value.op, ast.Add) or \
            not isinstance(assignments[0].value.right, ast.Constant):
        raise ValueError('the physical PRELUDE literal binding changed')
    literal = assignments[0].value.right
    if not PRELUDE.startswith(ORIGINAL_PRELUDE) or literal.value != PRELUDE[len(ORIGINAL_PRELUDE):]:
        raise ValueError('the runtime predicate differs from the physical PRELUDE literal')
    lines = raw.splitlines(keepends=True)
    lo = sum(map(len, lines[:literal.lineno-1])) + literal.col_offset
    hi = sum(map(len, lines[:literal.end_lineno-1])) + literal.end_col_offset
    if raw[lo:hi].count(encoded) != 1:
        raise ValueError('predicate is not unique in its physical PRELUDE literal')
    begin = raw.index(encoded, lo, hi)
    return definition, {'path': 'vector_reallocation_vcs.py', 'begin': begin,
        'end': begin+len(encoded), 'sha256': hashlib.sha256(encoded).hexdigest(),
        'container_sha256': hashlib.sha256(raw).hexdigest()}


def _application_arguments(text, name):
    match = re.fullmatch(re.escape(name) + r'\((.*)\)', text, re.S)
    if match is None:
        raise ValueError('the expanded predicate application differs')
    return _top_parts(match[1], ',')


def _int_definition_bridges():
    """Exact Why3-to-ACSL spelling bridge; no new semantic definition or axiom.

    This closed schema is the same four int32_at conjuncts used by the existing
    projection view. Both source definitions must match physically before any
    formula is instantiated. No generated bridge predicate is imported/emitted.
    """
    definitions = [
        ('''predicate int32_region (h:heap) (b offset count:int) =
    forall j:int. 0 <= j < count -> int32_at h b (offset+4*j)''',
         r'predicate t25_region_bridge(Heap::heap h, integer b, integer offset, integer count) = '
         r'(\forall integer j; 0 <= j < count ==> Heap::int32_at(h,b,offset+4*j));'),
        ('''predicate int32_at (h:heap) (b o:int) =
    typed_reads h b o 4 4 /\\ initialized_at h b o /\\
    integer_at h b o (load_int h b o) /\\
    -2147483648 <= load_int h b o <= 2147483647''',
         'predicate t25_cell_bridge(Heap::heap h, integer b, integer o) = '
         'Heap::typed_reads(h,b,o,4,4) && Heap::initialized_at(h,b,o) && '
         'Heap::integer_at(h,b,o,Heap::load_int(h,b,o)) && '
         '-2147483648 <= Heap::load_int(h,b,o) <= 2147483647;'),
    ]
    raw = (HERE/'heap_reallocation.mlw').read_bytes()
    bridges = []
    for why3, acsl in definitions:
        encoded = why3.encode()
        if raw.count(encoded) != 1:
            raise ValueError('the exact source integer definition changed')
        begin = raw.index(encoded)
        bridges.append((acsl, {'path': 'heap_reallocation.mlw', 'begin': begin,
            'end': begin+len(encoded), 'sha256': hashlib.sha256(encoded).hexdigest(),
            'container_sha256': hashlib.sha256(raw).hexdigest(),
            'ACSL_spelling_bridge': acsl, 'bridge_role': 'definitional spelling only; never emitted or assumed'}))
    return bridges


def constructor_positive_parts(statement):
    quantifiers = r'\forall Heap::heap h; \forall integer r,o,b,n,v; '
    antecedent = 't25v3_ctor_inv(h,r,o,b,n,n,v)'
    now = 'Heap::put_integer(h,r,o+8,n)'
    arguments = [now, 'r', 'o', 'b', '0', 'n', 'n']
    original = quantifiers + antecedent + ' ==> t25v3_eligible(' + ','.join(arguments) + ')'
    if statement != original or any(token == 'j' for token, _a, _b in _logic_tokens(quantifiers+antecedent)):
        raise ValueError('constructor expansion requires the exact full premise and a fresh index')
    eligible, eligible_source = _source_definition('t25v3_eligible', '    predicate t25v3_copy_frame')
    represented, repr_source = _source_definition('t25v3_repr', '    predicate t25v3_ctor_inv')
    eligible_parts, eligible_binding = predicate_conjuncts(eligible, arguments)
    if len(eligible_parts) != 2:
        raise ValueError('the exact eligibility conjunction changed')
    repr_parts, repr_binding = predicate_conjuncts(represented,
        _application_arguments(eligible_parts[0], 't25v3_repr'))
    if len(repr_parts) != 2:
        raise ValueError('the exact represented-heap conjunction changed')
    (region, region_source), (cell, cell_source) = _int_definition_bridges()
    region_parts, region_binding = predicate_conjuncts(region,
        _application_arguments(repr_parts[1], 'Heap::int32_region'))
    if len(region_parts) != 1:
        raise ValueError('the exact integer-region quantifier changed')
    scoped = re.fullmatch(r'\(\\forall integer j; (.*?) ==> (.*)\)', region_parts[0], re.S)
    if scoped is None:
        raise ValueError('the complete source integer-region scope changed')
    cells, cell_binding = predicate_conjuncts(cell,
        _application_arguments(scoped[2], 'Heap::int32_at'))
    if len(cells) != 4:
        raise ValueError('the exact integer-cell conjunction changed')
    components = [('repr', quantifiers, antecedent, repr_parts[0])]
    components += [('cells.'+name, quantifiers+r'\forall integer j; ',
                    antecedent+' && '+scoped[1], formula)
                   for name, formula in zip(['access', 'initialization', 'integer', 'bounds'], cells, strict=True)]
    components += [('eligibility', quantifiers, antecedent, eligible_parts[1])]
    parts = [('ctor.qualified.positive_post.'+suffix, prefix+premise+' ==> '+formula)
             for suffix, prefix, premise, formula in components]
    return parts, {'id': 'ctor.qualified.positive_post', 'original_statement': original,
        'quantifiers': quantifiers, 'antecedent': antecedent, 'fresh_index': 'j',
        'fresh_index_free_in_antecedent': False, 'parts': [name for name, _formula in parts],
        'premises_added': [], 'dependencies': [],
        'definition_sources': [eligible_source, repr_source, region_source, cell_source],
        'definition_expansions': [eligible_binding, repr_binding, region_binding, cell_binding],
        'region_range_from_definition': scoped[1],
        'combination': 'AND: representation, four independent integer-cell conjuncts and unary eligibility are all required',
        'equivalence': 'A implies (R and forall-fresh-j (range implies AND(cells)) and O) iff (A implies R) and AND(forall-fresh-j (A and range implies cell)) and (A implies O)',
        'reference_role': 'original logical target only; never imported or launched as a proved result'}


def lemma_source(name, statement):
    return ('//@ import \\wp::why3: heap_reallocation::Heap;\n' + PRELUDE +
            '/*@ check lemma t25v3_' + name.replace('.', '_') + ': ' + statement + ';\n*/\n')


def declaration(member):
    """Rebuild canonical bytes without trusting a staged manifest or hash."""
    source = model.model_text(member)
    if source is None:
        raise ValueError('unknown qualified model')
    theory = HERE / 'heap_reallocation.mlw'
    rows, files, logical = [], {}, []
    if member in model.MEMBERS:
        for index, (name, groups, needle, statement) in enumerate(member_specs(member)):
            begin = source.index(needle)
            end = begin + len(needle)
            parts = [(name, statement, f'{index:03d}')]
            if name == 'grow.entry.int_projection':
                expanded, receipt = projection_parts(statement)
                reference = 'references/' + f'{index:03d}-t25v3_grow_entry_int_projection.c'
                files[reference] = lemma_source(name, statement).encode()
                receipt['reference'] = {'path':reference,'sha256':hashlib.sha256(files[reference]).hexdigest()}
                for component in receipt['component_expansions']:
                    cell_reference = 'references/' + f'{index:03d}b-t25v3_grow_entry_int_projection_cells.c'
                    files[cell_reference] = lemma_source(component['id'], component['original_statement']).encode()
                    component['reference'] = {'path':cell_reference,'sha256':hashlib.sha256(files[cell_reference]).hexdigest()}
                logical.append(receipt)
                parts = [(part, formula, f'{index:03d}' + suffix)
                         for (part, formula), suffix in zip(expanded, ('a','b1','b2','b3','b4'), strict=True)]
            elif name == 'grow.copy.establish':
                expanded, receipt = copy_establish_parts(statement)
                reference = 'references/' + f'{index:03d}-t25v3_grow_copy_establish.c'
                files[reference] = lemma_source(name, statement).encode()
                receipt['reference'] = {'path': reference, 'sha256': hashlib.sha256(files[reference]).hexdigest()}
                logical.append(receipt)
                parts = [(part, formula, f'{index:03d}c{component:02d}')
                         for component, (part, formula) in enumerate(expanded, 1)]
            elif name == 'grow.copy.step':
                expanded, receipt = copy_step_parts(statement)
                reference = 'references/' + f'{index:03d}-t25v3_grow_copy_step.c'
                files[reference] = lemma_source(name, statement).encode()
                receipt['reference'] = {'path': reference, 'sha256': hashlib.sha256(files[reference]).hexdigest()}
                logical.append(receipt)
                parts = []
                receipt['original_definition_parts'] = list(receipt['parts'])
                for component, (part, formula) in enumerate(expanded, 1):
                    if part == 'grow.copy.step.advanced_copied_prefix':
                        prefix_parts, prefix_receipt = copy_prefix_parts(formula)
                        prefix_reference = 'references/' + f'{index:03d}s{component:02d}-t25v3_grow_copy_step_advanced_copied_prefix.c'
                        files[prefix_reference] = lemma_source(part, formula).encode()
                        prefix_receipt['reference'] = {'path':prefix_reference,
                            'sha256':hashlib.sha256(files[prefix_reference]).hexdigest()}
                        receipt['component_expansions'] = [prefix_receipt]
                        parts.extend((leaf, conclusion, f'{index:03d}s{component:02d}p{number:02d}')
                                     for number, (leaf, conclusion) in enumerate(prefix_parts, 1))
                    else:
                        parts.append((part, formula, f'{index:03d}s{component:02d}'))
                receipt['parts'] = [part for part, _formula, _label in parts]
                receipt['combination'] = 'AND: fourteen direct definition conjuncts and all ten equivalent prefix case/conjunct duties'
            elif name == 'ctor.qualified.positive_post':
                expanded, receipt = constructor_positive_parts(statement)
                reference = 'references/' + f'{index:03d}-t25v3_ctor_qualified_positive_post.c'
                files[reference] = lemma_source(name, statement).encode()
                receipt['reference'] = {'path': reference, 'sha256': hashlib.sha256(files[reference]).hexdigest()}
                logical.append(receipt)
                parts = [(part, formula, f'{index:03d}p{component}')
                         for component, (part, formula) in enumerate(expanded, 1)]
            for part, formula, label in parts:
                goal = 't25v3_' + part.replace('.', '_')
                text = (CTOR_NUMERIC.replace('t25_ctor_numeric', 't25v3_ctor_numeric')
                        if part == 'ctor.numeric' else GROW_NUMERIC) if formula is None else lemma_source(part, formula)
                path = label + '-' + goal + '.c'
                files[path] = text.encode()
                rows.append({'id':part,'source_groups':groups,'source_spans':[{'begin':begin,'end':end,
                    'sha256':hashlib.sha256(source[begin:end].encode()).hexdigest()}],
                    'statement':formula,'dependencies':[],'status':'pending','expected':'proven','goal':goal,
                    'kind':'c_kernel' if formula is None else 'check_lemma',
                    'path':path,'sha256':hashlib.sha256(text.encode()).hexdigest()})
    theory_name = 'theory/' + theory.name
    files[theory_name] = theory.read_bytes()
    files['qualified.c'] = source.encode()
    from swdb import std_models
    files['original.c'] = std_models.model_text(model.MEMBERS[member]).encode()
    from swdb.vector_reallocation_inventory import build
    plan = {'preparation_only':True,'coverage_complete':False,
            'member':member, 'model':model.identity(),
            'sources':{name:{'path':name,'sha256':hashlib.sha256(files[name]).hexdigest()}
                       for name in ('qualified.c','original.c')},
            'translation_components':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                for name in ('vector_reallocation_vcs.py','vector_reallocation_inventory.py',
                             'vector_reallocation_model.py','heap_model_vcs.py')},
            'source_inventory':build(member, source, rows, logical),
            'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'semantics':{'path':theory_name,'sha256':hashlib.sha256(files[theory_name]).hexdigest()},
            'caller_premises_added':[], 'typed_memory_role':'explicit typed int source-image domain; source-derived caller discharge required',
            'typed_source_image': model.certificate(member)['typed_source_image'],
            'source_parameter_semantics':{'int':'signed32 representation range; part of source typing, not a new requires'},
            'incoming_heap':'arbitrary well-formed incoming heap with issued dead identities and escaped aliases',
            'allocation_identities':'unbounded mathematical integers; address reuse never revives a dead ID',
            'obligations':rows, 'logical_obligations':logical,
            'missing':['complete source/clause/helper binding, frames and feasibility audit',
                'selected WP Typed/Machine source-image binding and caller discharge',
                'source-local caller/lifetime and ordinary dependency composition',
                'independent type/import/task-closure review and fresh normal-reader proof']}
    files['manifest.json'] = (json.dumps(plan,sort_keys=True,indent=2)+'\n').encode()
    return plan, files


def prepare(member, directory):
    """Emit an explicitly incomplete draft; no admission or result promotion."""
    plan, files = declaration(member)
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    for name, data in files.items():
        path = directory/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    return plan


def check(member, directory):
    """Canonical source reconstruction, including the complete import directory.

    Matching self-declared hashes is insufficient. No caller can promote a
    prepared receipt to a proof or bypass pending semantic/source admission.
    """
    expected, files = declaration(member)
    directory = Path(directory)
    paths = list(directory.rglob('*'))
    if directory.is_symlink() or any(p.is_symlink() for p in paths):
        raise ValueError('a qualified packet or import path is symlinked')
    if any(not p.is_file() and not p.is_dir() for p in paths):
        raise ValueError('a qualified packet contains a special filesystem entry')
    actual = {str(p.relative_to(directory)) for p in paths if p.is_file()}
    directories = {str(p.relative_to(directory)) for p in paths if p.is_dir()}
    expected_dirs = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
    if actual != set(files) or directories != expected_dirs:
        raise ValueError('the qualified source/packet/import membership changed')
    for name, data in files.items():
        if (directory/name).read_bytes() != data:
            raise ValueError('the canonical qualified source/VC declaration changed: ' + name)
    return expected
