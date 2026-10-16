"""2026-10-16 ET. Exact conjunctions of the two closed positive source duties.

Every leaf keeps the complete constructor antecedent. Explicit cleanup witnesses
reconstruct the original existential; sibling conclusions are never premises.
This preparation does not admit a source, Typed, member or caller proof.
"""
import hashlib
import json
import re
from pathlib import Path

from swdb import vector_reallocation_closed_lifetime as original
from swdb import vector_reallocation_private_frame as private
from swdb import vector_reallocation_vcs as constructor


class Refused(ValueError):
    pass


QUANTIFIERS = r'\forall Heap::heap entry,before,loop; \forall integer r,b,n; '
POSITIVE = original.POSITIVE
FINAL = 'Heap::end_automatic(Heap::release('+POSITIVE+',b),r)'
SCALAR = '(n > 0 ? Heap::load_int('+POSITIVE+',b,0) : 0)'
PARAMETERS = ('Heap::heap entry, Heap::heap before, Heap::heap loop, '
              'integer r, integer b, integer n, integer object, integer observed, integer position, integer j')
ARGUMENTS = ['entry', 'before', 'loop', 'r', 'b', 'n', 'object', 'observed', 'position', 'j']


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()


def identity():
    return {'id': 'vector-closed-lifetime-conjunction-1',
            'sha256': _sha(_json({'source': _sha(Path(__file__).read_bytes()),
                                  'original': original.identity()}))}


def _conjuncts(expression):
    parts, _binding = constructor.predicate_conjuncts(
        'predicate t25_closed_component('+PARAMETERS+') = '+expression+';', ARGUMENTS)
    return parts


def _physical_definition(path, text):
    raw = path.read_bytes()
    encoded = text.encode()
    if raw.count(encoded) != 1:
        raise Refused('the exact physical source definition changed: '+path.name)
    begin = raw.index(encoded)
    return {'path': path.name, 'begin': begin, 'end': begin+len(encoded),
            'sha256': _sha(encoded), 'container_sha256': _sha(raw)}


def _observations(left, right):
    start = private.PRELUDE.index('predicate t25_private_observes(')
    end = private.PRELUDE.index('    predicate t25_private_frame(', start)
    definition = private.PRELUDE[start:end].strip()
    source = _physical_definition(Path(private.__file__), definition)
    frame_begin = private.PRELUDE.index('predicate t25_private_frame(')
    frame_end = private.PRELUDE.index('    predicate t25_private_ids(', frame_begin)
    frame_definition = private.PRELUDE[frame_begin:frame_end].strip()
    if frame_definition != ('predicate t25_private_frame(Heap::heap entry, Heap::heap now) =\n'
                            '      t25_private_observes(entry,entry,now);'):
        raise Refused('the exact private frame alias changed')
    frame_source = _physical_definition(Path(private.__file__), frame_definition)
    # Both names are bound only, and the checked arguments contain neither new
    # name. This alpha conversion avoids the source buffer parameter named b.
    renamed = re.sub(r'\b[bp]\b', lambda match: {'b': 'object', 'p': 'position'}[match[0]], definition)
    second = renamed.index(r'(\forall integer object,position;')
    renamed = renamed[:second]+re.sub(r'\bobject\b', 'observed', renamed[second:])
    pieces, binding = constructor.predicate_conjuncts(renamed, ['entry', left, right])
    if binding['nested_bound_variables'] != ['object', 'observed', 'position'] or len(pieces) != 2:
        raise Refused('the complete incoming observer quantifiers changed')
    output = []
    for index, piece in enumerate(pieces):
        scoped = re.fullmatch(r'\(\\forall integer (object|observed,position); (.*?) ==>\s*(.*)\)', piece, re.S)
        if scoped is None or scoped[1] != ('object' if index == 0 else 'observed,position') or \
                scoped[2] != 'Heap::live(entry,'+scoped[1].split(',')[0]+')':
            raise Refused('the complete incoming observer scope changed')
        conclusions = _conjuncts(scoped[3])
        wanted = ['objects'] if index == 0 else ['contents', 'initialization']
        if len(conclusions) != len(wanted):
            raise Refused('the complete incoming observer conjunction changed')
        output += [(name, r'\forall integer '+scoped[1]+'; ', scoped[2], conclusion)
                   for name, conclusion in zip(wanted, conclusions, strict=True)]
    return output, {'definition_source': source, 'frame_alias_source': frame_source,
                    'definition_expansion': binding,
                    'source_bound_alpha_renaming': {'first.b': 'object', 'second.b': 'observed', 'second.p': 'position'}}


def _integer_region():
    # Reuse the existing checked physical Why3/ACSL spelling bridges. Neither
    # helper emits a predicate, goal, axiom or proof result.
    (region, region_source), (cell, cell_source) = constructor._int_definition_bridges()
    ranges, range_binding = constructor.predicate_conjuncts(region, [POSITIVE, 'b', '0', 'n'])
    if len(ranges) != 1:
        raise Refused('the exact integer region quantifier changed')
    scoped = re.fullmatch(r'\(\\forall integer j; (.*?) ==> (.*)\)', ranges[0], re.S)
    if scoped is None or scoped[1] != '0 <= j < n':
        raise Refused('the exact integer region range changed')
    application = re.fullmatch(r'Heap::int32_at\((.*)\)', scoped[2])
    if application is None:
        raise Refused('the exact integer region cell changed')
    arguments = [POSITIVE, 'b', '0+4*j']
    if application[1] != ','.join(arguments):
        raise Refused('the integer cell application differs from its source')
    cells, cell_binding = constructor.predicate_conjuncts(cell, arguments)
    if len(cells) != 4:
        raise Refused('the complete integer cell conjunction changed')
    return [(name, r'\forall integer j; ', scoped[1], conclusion)
            for name, conclusion in zip(['access', 'initialization', 'integer', 'bounds'], cells, strict=True)], \
        {'definition_sources': [region_source, cell_source],
         'definition_expansions': [range_binding, cell_binding]}


def _filled_prefix():
    why3 = '''predicate filled_prefix (h:heap) (b k v:int) =
    forall j:int. 0 <= j < k ->
      initialized_at h b (4*j) /\\ integer_at h b (4*j) v'''
    bridge = (r'predicate t25_closed_fill(Heap::heap h, integer b, integer k, integer v) = '
              r'(\forall integer j; 0 <= j < k ==> Heap::initialized_at(h,b,4*j) && '
              r'Heap::integer_at(h,b,4*j,v));')
    source = _physical_definition(Path(original.__file__).with_name('heap_reallocation.mlw'), why3)
    scopes, binding = constructor.predicate_conjuncts(bridge, [POSITIVE, 'b', 'n', '7'])
    if len(scopes) != 1:
        raise Refused('the exact fill quantifier changed')
    scoped = re.fullmatch(r'\(\\forall integer j; (.*?) ==> (.*)\)', scopes[0], re.S)
    if scoped is None or scoped[1] != '0 <= j < n':
        raise Refused('the exact fill range changed')
    cells = _conjuncts(scoped[2])
    if len(cells) != 2:
        raise Refused('the complete fill conjunction changed')
    return [(name, r'\forall integer j; ', scoped[1], conclusion)
            for name, conclusion in zip(['initialization', 'value'], cells, strict=True)], \
        {'definition_source': source, 'ACSL_spelling_bridge': bridge,
         'definition_expansion': binding, 'bridge_role': 'definitional spelling only; never emitted or assumed'}


def _decompose(plan):
    targets = {row['id']: row for row in plan['obligations']}
    prefix = QUANTIFIERS+original.PREMISE+' ==> '
    exit_row, cleanup_row = targets['positive.exit_image'], targets['positive.cleanup']
    if not exit_row['statement'].startswith(prefix) or not cleanup_row['statement'].startswith(prefix):
        raise Refused('decomposition requires the exact full original antecedent')
    fresh_names = {'object', 'observed', 'position', 'j'}
    if fresh_names & set(re.findall(r'\b[A-Za-z_]\w*\b', prefix)):
        raise Refused('decomposition indices must be fresh in the complete source premise')
    exit_parts = _conjuncts(exit_row['statement'][len(prefix):])
    expected_exit = [
        't25_private_frame(entry,'+POSITIVE+')', 't25_private_ids(entry,r,b)',
        'Heap::typed_writes('+POSITIVE+',r,0,24,8)', '!Heap::freeable('+POSITIVE+',r,0)',
        'Heap::freeable('+POSITIVE+',b,0)', 'Heap::int32_region('+POSITIVE+',b,0,n)',
        'Heap::filled_prefix('+POSITIVE+',b,n,7)']
    if exit_parts != expected_exit:
        raise Refused('the complete original exit conjunction changed')
    exit_frame, exit_observer = _observations('entry', POSITIVE)
    identity_definition = private.PRELUDE[private.PRELUDE.index('predicate t25_private_ids('):
                        private.PRELUDE.index('    logic Heap::heap t25_private_cleanup(')].strip()
    identities, identity_binding = constructor.predicate_conjuncts(identity_definition, ['entry', 'r', 'b'])
    identity_source = _physical_definition(Path(private.__file__), identity_definition)
    if len(identities) != 2:
        raise Refused('the complete private identity conjunction changed')
    integer_cells, integer_binding = _integer_region()
    fills, fill_binding = _filled_prefix()
    exit_leaves = [('frame.'+name, quantifiers, scope, value) for name, quantifiers, scope, value in exit_frame]
    exit_leaves += [('private.'+name, '', '', value)
                    for name, value in zip(['receiver', 'buffer'], identities, strict=True)]
    exit_leaves += [(name, '', '', value) for name, value in zip(
        ['receiver_access', 'receiver_nonfreeable', 'buffer_freeable'], exit_parts[2:5], strict=True)]
    exit_leaves += [('integer.'+name, quantifiers, scope, value) for name, quantifiers, scope, value in integer_cells]
    exit_leaves += [('filled.'+name, quantifiers, scope, value) for name, quantifiers, scope, value in fills]
    expected_cleanup = (r'\exists Heap::heap final; \exists integer scalar; '
        'final == '+FINAL+' && scalar == '+SCALAR+' && scalar == (n > 0 ? 7 : 0) && '
        't25_private_frame(entry,final) && t25_private_observes(entry,'+POSITIVE+',final) && '
        '!Heap::forms(final,r,0) && !Heap::forms(final,b,0)')
    if cleanup_row['statement'][len(prefix):] != expected_cleanup:
        raise Refused('the complete original existential/witness conjunction changed')
    final_frame, final_binding = _observations('entry', FINAL)
    release_frame, release_binding = _observations(POSITIVE, FINAL)
    cleanup_leaves = [('scalar', '', '', SCALAR+' == (n > 0 ? 7 : 0)')]
    cleanup_leaves += [('frame.'+name, quantifiers, scope, value) for name, quantifiers, scope, value in final_frame]
    cleanup_leaves += [('observes.'+name, quantifiers, scope, value) for name, quantifiers, scope, value in release_frame]
    cleanup_leaves += [('receiver_dead', '', '', '!Heap::forms('+FINAL+',r,0)'),
                       ('buffer_dead', '', '', '!Heap::forms('+FINAL+',b,0)')]
    if len(exit_leaves) != 14 or len(cleanup_leaves) != 9:
        raise Refused('the complete source conjunction leaf census changed')
    sources = {'positive.exit_image': {
        'original_conjuncts': exit_parts, 'observer_expansion': exit_observer,
        'private_identity_expansion': identity_binding, 'private_identity_source': identity_source,
        'integer_expansion': integer_binding,
        'fill_expansion': fill_binding,
        'combination': 'all fourteen same-antecedent leaves reconstruct every original exit conjunct'},
        'positive.cleanup': {'witnesses': {'final': FINAL, 'scalar': SCALAR},
        'equality_witnesses_checked': True,
        'reflexive_equalities': [FINAL+' == '+FINAL, SCALAR+' == '+SCALAR],
        'frame_expansion': final_binding, 'observation_expansion': release_binding,
        'combination': 'all nine same-antecedent leaves plus the two reflexive equalities construct the exact original existential'}}
    return [('positive.exit_image', exit_leaves), ('positive.cleanup', cleanup_leaves)], sources


def declaration(lowering, source, formal_texts):
    old, previous = original.declaration(lowering, source, formal_texts)
    groups, conjunctions = _decompose(old)
    files = {name: raw for name, raw in previous.items()
             if not name.startswith('obligations/') and name != 'manifest.json'}
    obligations = []
    for logical_target, components in groups:
        reference = next(row for row in old['obligations'] if row['id'] == logical_target)
        reference_path = 'reference-'+reference['path']
        files[reference_path] = previous[reference['path']]
        conjunctions[logical_target].update({
            'reference_path': reference_path, 'reference_sha256': reference['sha256'],
            'original_statement': reference['statement'], 'antecedent': original.PREMISE,
            'premises_added': [], 'dependencies': [], 'parts': [],
            'equivalence': 'conjunction distribution with fresh universal indices; exact source definitions and deterministic existential equality witnesses only',
            'reference_role': 'unproved original target only; never imported or launched as a theorem'})
        for suffix, quantifiers, scope, conclusion in components:
            ident = logical_target+'.'+suffix
            statement = QUANTIFIERS+quantifiers+original.PREMISE+(' && '+scope if scope else '')+' ==> '+conclusion
            goal = 't25_closed_parts_'+ident.replace('.', '_')
            raw = ('//@ import \\wp::why3: heap_reallocation::Heap;\n'+previous['prelude.acsl'].decode()+
                   '/*@ check lemma '+goal+': '+statement+';\n*/\n').encode()
            path = f'obligations/{len(obligations):03d}-{goal}.c'
            files[path] = raw
            obligations.append({'id': ident, 'goal': goal, 'path': path, 'kind': 'check_lemma',
                'statement': statement, 'logical_target': logical_target,
                'source_antecedent': original.PREMISE, 'derived_index_scope': scope,
                'status': 'pending', 'dependencies': [], 'source_events': reference['source_events'],
                'local_antecedent_discharge': reference['local_antecedent_discharge'], 'sha256': _sha(raw)})
            conjunctions[logical_target]['parts'].append(ident)
    plan = {**old, 'checker': identity(), 'obligations': obligations,
        'complete_positive_antecedent': original.PREMISE, 'conjunctions': conjunctions,
        'unchanged_gluing_dependencies': [
            {'id': row['id'], 'goal': row['goal'], 'sha256': row['sha256'],
             'role': 'unchanged complete source duty; exact accepted evidence required before composition'}
            for row in old['obligations'] if row['id'] not in conjunctions],
        'proof_admission': 'unsupported: all exact source leaves, unchanged gluing/dependency evidence and independently checked source observation rule remain required',
        'original_timeout_evidence_preserved': True}
    files['manifest.json'] = _json(plan)
    return plan, files


def prepare(lowering, source, formal_texts, directory):
    plan, files = declaration(lowering, source, formal_texts)
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    for name, raw in files.items():
        path = directory/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return plan


def check(lowering, source, formal_texts, directory):
    plan, files = declaration(lowering, source, formal_texts)
    directory = Path(directory)
    paths = list(directory.rglob('*'))
    parents = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
    if directory.is_symlink() or any(path.is_symlink() or not (path.is_file() or path.is_dir()) for path in paths) or \
            {str(path.relative_to(directory)) for path in paths if path.is_file()} != set(files) or \
            {str(path.relative_to(directory)) for path in paths if path.is_dir()} != parents:
        raise Refused('closed conjunction canonical source/target membership differs')
    for name, raw in files.items():
        if (directory/name).read_bytes() != raw:
            raise Refused('closed conjunction source/premise/witness differs: '+name)
    return plan


def check_launch(lowering, source, formal_texts, directory):
    check(lowering, source, formal_texts, directory)
    raise Refused('actual complete source conjunction proofs and source observation rule remain pending')
