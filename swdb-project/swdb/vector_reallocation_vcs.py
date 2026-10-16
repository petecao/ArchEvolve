"""Qualified int grow source VC preparation; created 2026-10-16 ET.

Definitions and isolated pending check lemmas, never desired-result axioms.
The complete public model/caller route remains closed until all maps exist.
"""
from pathlib import Path
import hashlib
import json

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


def prepare(member, directory):
    """Emit an explicitly incomplete draft; no admission or result promotion."""
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    source = model.model_text(member)
    if source is None:
        raise ValueError('unknown qualified model')
    theory = HERE / 'heap_reallocation.mlw'
    rows = []
    if member in model.MEMBERS:
        for index, (name, groups, needle, statement) in enumerate(member_specs(member)):
            begin = source.index(needle)
            end = begin + len(needle)
            goal = 't25v3_' + name.replace('.', '_')
            text = (CTOR_NUMERIC.replace('t25_ctor_numeric', 't25v3_ctor_numeric')
                    if name == 'ctor.numeric' else GROW_NUMERIC) if statement is None else (
                '//@ import \\wp::why3: heap_reallocation::Heap;\n' + PRELUDE +
                '/*@ check lemma ' + goal + ': ' + statement + ';\n*/\n')
            path = directory / (f'{index:03d}-' + goal + '.c')
            path.write_text(text)
            rows.append({'id':name,'source_groups':groups,'source_spans':[{'begin':begin,'end':end,
                'sha256':hashlib.sha256(source[begin:end].encode()).hexdigest()}],
                'statement':statement,'dependencies':[],'status':'pending','expected':'proven','goal':goal,
                'kind':'c_kernel' if statement is None else 'check_lemma',
                'path':path.name,'sha256':hashlib.sha256(text.encode()).hexdigest()})
    stage = directory/'theory'
    stage.mkdir()
    staged_theory = stage/theory.name
    staged_theory.write_bytes(theory.read_bytes())
    plan = {'preparation_only':True,'coverage_complete':False,
            'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'semantics':{'path':'theory/' + theory.name,'sha256':hashlib.sha256(staged_theory.read_bytes()).hexdigest()},
            'caller_premises_added':[], 'typed_memory_role':'explicit typed int source-image domain; source-derived caller discharge required',
            'typed_source_image': model.certificate(member)['typed_source_image'],
            'source_parameter_semantics':{'int':'signed32 representation range; part of source typing, not a new requires'},
            'incoming_heap':'arbitrary well-formed incoming heap with issued dead identities and escaped aliases',
            'allocation_identities':'unbounded mathematical integers; address reuse never revives a dead ID',
            'obligations':rows, 'missing':['complete source/clause/helper binding, frames and feasibility audit',
                'selected WP Typed/Machine source-image binding and caller discharge',
                'source-local caller/lifetime and ordinary dependency composition',
                'independent type/import/task-closure review and fresh normal-reader proof']}
    (directory/'manifest.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
    return plan
