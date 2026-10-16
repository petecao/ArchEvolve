"""Qualified int grow source VC preparation; created 2026-10-16 ET.

Definitions and isolated pending check lemmas, never desired-result axioms.
The complete public model/caller route remains closed until all maps exist.
"""
from pathlib import Path
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
    parts = [('grow.entry.int_projection.repr', quantifiers + antecedent + ' ==> ' + representation),
             ('grow.entry.int_projection.cells', quantifiers + r'\forall integer j; ' + antecedent +
              r' && 0 <= j < s ==> Heap::int32_at(' + projected + ',b,bo+4*j)')]
    return parts, {'id':'grow.entry.int_projection', 'original_statement':original,
        'quantifiers':quantifiers, 'antecedent':antecedent, 'fresh_index':'j',
        'fresh_index_free_in_antecedent':False, 'fresh_index_bound_in_outer_quantifiers':False,
        'parts':[name for name,_ in parts], 'combination':'AND: both isolated pieces are required',
        'equivalence':'A implies (R and forall j: B implies I) iff (A implies R) and forall fresh j: (A and B) implies I',
        'definition_sources':definitions, 'premises_added':[], 'dependencies':[],
        'region_substitution':{'h':projected, 'b':'b', 'offset':'bo', 'count':'s', 'j':'j'},
        'reference_role':'original logical target only; never imported or launched as a proved result'}


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
                logical.append(receipt)
                parts = [(part, formula, f'{index:03d}' + suffix)
                         for (part, formula), suffix in zip(expanded, ('a','b'), strict=True)]
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
            'source_inventory':build(member, source, rows),
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
