"""2026-10-16 ET. Three exhaustive owner cases of the pending swap header duty.

Every case keeps the complete original source antecedent and unchanged active,
ready and existential header conclusion. No case is a theorem premise of another.
"""
import hashlib
import json
from pathlib import Path

from swdb import vector_owned_swap_parts as previous


CASES = (('left', 'observed == l'), ('right', 'observed == r'),
         ('other', 'observed != l && observed != r'))
HEADER_STATEMENT = (
    r'\forall Heap::heap h; \forall Owners::state owners; '
    r'\forall OwnedEffects::phases ready; '
    r'\forall integer l,r,a,bl,nl,cl,br,nr,cr; \forall integer observed; '
    r'OwnedEffects::world(h,owners,ready) && Owners::active_owner(owners,l) && '
    r'Owners::active_owner(owners,r) && OwnedEffects::is_ready(ready,l) && '
    r'OwnedEffects::is_ready(ready,r) && OwnedEffects::header(h,l,bl,nl,cl) && '
    r'OwnedEffects::header(h,r,br,nr,cr) && Heap::automatic_available(h,24,8,a) ==> '
    r'(Owners::active_owner(Owners::swap(owners,l,r),observed) && '
    r'OwnedEffects::is_ready(ready,observed) ==> '
    r'(\exists integer size,capacity; OwnedEffects::header(OwnedEffects::swap(h,l,r,a),'
    r'observed,Owners::buffer(Owners::swap(owners,l,r),observed),size,capacity)))')


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def identity():
    return {'id': 'vector-owned-swap-header-cases-1',
            'sha256': _sha(_json({'source': _sha(Path(__file__).read_bytes()),
                                  'previous': previous.identity()}))}


def declaration(*, elements=('int',)):
    old, previous_files = previous.declaration(elements=elements)
    header = next(row for row in old['obligations'] if row['id'] == 'swap.owner_correspondence.header.ready')
    premise = old['complete_source_antecedent']
    prefix, marker, conclusion = header['statement'].partition(premise+' ==> ')
    if header['statement'] != HEADER_STATEMENT or not marker or len(old['obligations']) != 13 or \
            header['fresh_universal_indices'] != ['observed'] or 'observed' in premise:
        raise ValueError('complete original header statement, fresh binder or thirteen-part census changed')
    files = {name: raw for name, raw in previous_files.items()
             if not name.startswith('obligations/') and name != 'manifest.json'}
    dependencies = []
    for row in old['obligations']:
        name = 'reference-parts/'+row['path']
        files[name] = previous_files[row['path']]
        if row['id'] != header['id']:
            dependencies.append({'id': row['id'], 'goal': row['goal'], 'path': name,
                                 'sha256': row['sha256'],
                                 'role': 'unchanged conditional part; exact independent scientific evidence required separately'})
    imports = ('//@ import \\wp::why3: heap_reallocation::Heap;\n'
               '//@ import \\wp::why3: vector_owned_state::Owners;\n'
               '//@ import \\wp::why3: vector_owned_effects::OwnedEffects;\n')
    obligations = []
    for case, condition in CASES:
        statement = prefix+premise+' ==> ('+condition+' ==> '+conclusion+')'
        goal = 't25_owned_swap_header_'+case
        path = f'obligations/{len(obligations):03d}-{goal}.c'
        raw = (imports+'/*@ check lemma '+goal+': '+statement+';\n*/\n').encode()
        files[path] = raw
        obligations.append({'id': header['id']+'.'+case, 'goal': goal, 'case': case,
                            'condition': condition, 'path': path, 'kind': 'check_lemma',
                            'statement': statement, 'source_antecedent': premise,
                            'fresh_universal_indices': ['observed'],
                            'dependencies': [], 'status': 'pending', 'sha256': _sha(raw)})
    plan = {**old, 'checker': identity(), 'previous_checker': old['checker'],
            'logical_target': header['id'], 'original_statement': header['statement'],
            'original_compound_statement': old['original_statement'],
            'original_compound_reference': {'path': old['reference_path'], 'sha256': old['reference_sha256']},
            'reference_path': 'reference-parts/'+header['path'], 'reference_sha256': header['sha256'],
            'reference_role': 'original unproved universal header duty, never a theorem premise or launched target',
            'obligations': obligations, 'unchanged_dependencies': dependencies,
            'original_source_dependencies': old['unchanged_dependencies'],
            'reconstruction': {'case_disjunction': 'observed == l || observed == r || (observed != l && observed != r)',
                               'equivalence': 'conjunction of three guarded copies of the identical conclusion under the identical full antecedent',
                               'full_quantifier_prefix': prefix, 'unchanged_conclusion': conclusion,
                               'self_swap_excluded': False,
                               'self_swap': 'when l == r the two equality cases overlap; every observed owner is still covered',
                               'added_premises': [], 'axioms_added': [],
                               'previous_world_reconstruction': old['reconstruction']},
            'source_admission': 'unsupported: all three native proofs, complete cold interpretation, reconstruction and source/lifetime correspondence remain required'}
    files['manifest.json'] = _json(plan)
    return plan, files


def prepare(directory, *, elements=('int',)):
    plan, files = declaration(elements=elements)
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    for name, raw in files.items():
        path = directory/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return plan


def check(directory, *, elements=('int',)):
    plan, _ = declaration(elements=elements)
    if json.loads((Path(directory)/'manifest.json').read_bytes()) != plan:
        raise ValueError('swap header manifest differs')
    return plan
