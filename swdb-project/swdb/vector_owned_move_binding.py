"""2026-10-16 ET. Exact retained conditional mathematics for the closed int move.

The four source9 move duties and unchanged constructor35/destructor11/private9
components are mathematical dependencies only. Source-created premise discharge,
actual cleanup, the ordinary obligation ledger and framework admission remain
separate. Historical compiler/method/runtime identities are never relabeled.
"""
import hashlib
import json
from pathlib import Path

from swdb import vector_owned_source_view as source_view
from swdb import vector_reallocation_closed_binding as previous


class Refused(ValueError):
    pass


MOVE_BUNDLE_SHA256 = 'be13f7126162e6735768b039ae0e85a364bd0fac5a156fa88735ed821016277d'
MOVE_SOURCE = '032e1851eec7b195c7a3737997d5f5ea1d1343a5'
MOVE_IDS = ('move.destination_header', 'move.source_empty', 'move.incoming_frame',
            'move.owner_correspondence')
# Both physical printed copies of each actually materialized prover family.
# The first three duties used Alt-Ergo; owner_correspondence retained all three.
MOVE_TASK_COUNTS = dict(zip(MOVE_IDS, (2, 2, 2, 6), strict=True))
MAX_BUNDLE_BYTES = 8*1024*1024
MAX_DOCUMENT_BYTES = 4*1024*1024


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def _need(value, reason):
    if not value:
        raise Refused(reason)


def _pairs(rows):
    result = {}
    for key, value in rows:
        _need(key not in result, 'duplicate scientific JSON key')
        result[key] = value
    return result


def _decode(raw):
    try:
        return json.loads(raw, object_pairs_hook=_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(Refused('nonfinite scientific JSON')))
    except (ValueError, UnicodeError, RecursionError) as error:
        raise Refused('invalid bounded scientific document: '+str(error)) from None


def identity():
    return {'id': 'vector-owned-move-scientific-binding-1',
        'sha256': _sha(_json({'source': _sha(Path(__file__).read_bytes()),
            'reusable_components': previous.identity(), 'current_source_view': source_view.identity(),
            'move_mathematical_bundle': MOVE_BUNDLE_SHA256}))}


def _bundle(directory):
    directory = Path(directory)
    _need(directory.is_dir() and not directory.is_symlink(), 'one physical move scientific directory required')
    paths = list(directory.iterdir())
    _need(len(paths) == 1 and paths[0].name == 'bundle.json' and paths[0].is_file()
          and not paths[0].is_symlink() and 0 < paths[0].stat().st_size <= MAX_BUNDLE_BYTES,
          'move scientific bundle membership, type or extent changed')
    raw = paths[0].read_bytes()
    _need(_sha(raw) == MOVE_BUNDLE_SHA256, 'move mathematical evidence is outside its exact reviewed registry')
    value = _decode(raw)
    _need(value['schema_version'] == 1 and value['kind'] == 'vector-owned-move-mathematical-bundle'
          and value['required_target_count'] == 4 and value['source_commit'] == MOVE_SOURCE
          and tuple(value['target_ids']) == MOVE_IDS
          and all(value[field] is False for field in
                  ('source_admission', 'caller_acceptance', 'public_proof_record_created')),
          'complete move scientific scope changed')
    documents = {}
    _need(isinstance(value['documents'], dict) and len(value['documents']) == 21,
          'complete retained move context document census changed')
    for role, descriptor in value['documents'].items():
        text = descriptor['text'].encode('utf8')
        _need(type(descriptor['bytes']) is int and 0 < len(text) == descriptor['bytes'] <= MAX_DOCUMENT_BYTES
              and _sha(text) == descriptor['sha256'], 'complete retained document changed: '+role)
        # Original paths are inert historical values, never files to open.
        documents[role] = text
    return value, documents


def _registry(value):
    result = json.loads(json.dumps(value))
    _need('container_sha256' in result, 'observed type-registry container pin required')
    result.pop('container_sha256')
    return result


def mathematical_dependencies(component_directory, move_directory):
    """Bind every complete current mathematical input; no caller state is assumed."""
    try:
        common, files = previous.reusable_components(component_directory)
        bundle, documents = _bundle(move_directory)
        fresh, canonical = source_view.declaration(elements=('int',))
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise Refused(str(error)) from None
    doc = lambda role: _decode(documents[role])
    accepted = doc('root_decision')
    interpreted = doc('complete_interpretation')
    cold, capture = doc('cold'), doc('capture')
    own = doc('own_join')
    original = doc('canonical_interface')
    _need(accepted['mathematical_model_duties_accepted'] is True
          and set(MOVE_IDS) <= set(accepted['accepted_duties'])
          and accepted['original_C_or_Cxx_source_Heap_Typed_lifetime_caller_default_or_public_record_admission'] is False
          and accepted['complete_interpretation']['sha256'] == _sha(documents['complete_interpretation']),
          'root mathematical scope or its complete interpretation identity changed')
    _need(interpreted['complete_conditional_mathematical_interpretation'] is True
          and interpreted['unknown_items'] == []
          and interpreted['counts'] == accepted['counts'] == {
              'Heap_definition_instances': 462, 'Owners_Effects_definition_instances': 346,
              'abs_definition_instances': 26, 'distinct_math_commands': 115,
              'standard_support_instances': 784, 'sum_map_support_instances': 158, 'tasks': 26},
          'complete task, definition or support interpretation changed')
    for row in interpreted['inputs']:
        role = row['role']
        _need(role in documents and len(documents[role]) == row['bytes']
              and _sha(documents[role]) == row['sha256'], 'full interpreted scientific dependency changed')
    _need(cold['source_commit'] == capture['source_commit'] == MOVE_SOURCE
          and cold['raw_pre_post_equal'] is True
          and cold['source_consumers']['before_after_receipts_equal'] is True
          and capture['all29_content_and_nine_stat_pre_post_equal'] is True
          and capture['task_count'] == len(capture['tasks']) == 26,
          'actual retained source, task or physical cold closure changed')
    for resource in cold['guards']['resources'].values():
        _need(type(resource['exit_code']) is int and resource['exit_code'] == 0
              and resource['out_of_memory'] is False and resource['timed_out'] is False,
              'original source9 process resource boundary changed')
    for name in ('heap_reallocation.mlw', 'vector_owned_state.mlw', 'vector_owned_effects.mlw'):
        _need(Path(__file__).with_name(name).read_bytes() == canonical['theory/'+name]
              == documents['source_'+name],
              'current complete mathematical theory differs: '+name)
        files['move-source/theory/'+name] = canonical['theory/'+name]
    _need(fresh['parent_model'] == original['parent_model']
          and _registry(fresh['type_registry']) == _registry(original['type_registry']),
          'complete current model or literal type-domain registry changed')
    old_members = {row['function']: row for row in original['source_members']}
    _need(len(old_members) == len(original['source_members'])
          and all(row == old_members.get(row['function']) for row in fresh['source_members']),
          'complete original current move/swap source inverse or domain changed')
    for member in fresh['source_members']:
        _need(_sha(canonical[member['original_path']]) == member['original_sha256']
              and _sha(canonical[member['view_path']]) == member['view_sha256'],
              'complete current original or layout-view source bytes changed')
    targets = [row for row in fresh['obligations'] if row['id'] in MOVE_IDS]
    _need(tuple(row['id'] for row in targets) == MOVE_IDS and len(bundle['targets']) == 4,
          'all four exact current move targets required')
    statements = {row['id']: row for row in cold['source_statement_census']}
    leaves = {row['id']: row for row in cold['leaves']}
    semantic_outcomes = {row['id']: row for row in interpreted['outcomes']}
    tasks = {(row['id'], row['artifact']['relative']): row for row in interpreted['tasks']}
    own_tasks = {(row['id'], row['artifact']['relative']): row for row in own['tasks']}
    _need(len(tasks) == len(own_tasks) == 26, 'unique complete interpreted task owners required')
    observed_targets, selected_tasks = [], []
    for current, historical in zip(targets, bundle['targets'], strict=True):
        for key in ('id', 'goal', 'kind', 'statement', 'sha256'):
            _need(current[key] == historical[key], 'complete current move target changed: '+key)
        raw = canonical[current['path']]
        _need(_sha(raw) == current['sha256'] == statements[current['id']]['input_sha256']
              and statements[current['id']]['statement'] == current['statement']
              and statements[current['id']]['goal'] == current['goal'],
              'original complete source-to-VC input or statement changed')
        leaf = leaves[current['id']]
        _need(leaf['normal_verdict'] == 'proven' and 'valid' in leaf['native_results']
              and leaf['ordinary'] == 1 and leaf['smokes'] == 0
              and leaf['property'] == 'check_lemma_'+current['goal']
              and leaf['task_census']['extern_properties'] == []
              and leaf['task_census']['missing_noninternal_tasks'] == []
              and semantic_outcomes[current['id']] == {
                  'id': current['id'], 'normal_verdict': leaf['normal_verdict'],
                  'native_results': leaf['native_results']}, 'complete actual ordinary native outcome changed')
        selected = [row for row in capture['tasks'] if row['id'] == current['id']]
        _need(len(selected) == MOVE_TASK_COUNTS[current['id']],
              'all retained selected solver-family task/copy contexts required')
        for task in selected:
            key = (task['id'], task['artifact']['relative'])
            match, owner = tasks[key], own_tasks[key]
            _need(match['artifact'] == owner['artifact'] == task['artifact']
                  and match['full_goal_source_equivalent'] is True
                  and owner['source_goal_equivalent'] is True
                  and match['full_goal_command_sha256'] == owner['actual_complete_goal_command_sha256']
                      == task['goal_command_sha256'], 'full source/goal/task interpretation join changed')
            selected_tasks.append({'id': task['id'], 'artifact': task['artifact'],
                                   'complete_goal_sha256': task['goal_command_sha256']})
        observed_targets.append({'id': current['id'], 'goal': current['goal'], 'kind': current['kind'],
            'statement': current['statement'], 'input_sha256': current['sha256'],
            'observation': leaf})
        files['move-source/'+current['path']] = raw
    preserved = {'id': 'swap.owner_correspondence', 'normal_verdict': 'not_proven',
                 'native_results': ['timeout', 'timeout', 'timeout']}
    _need(bundle['full_original_unaccepted_swap_preserved'] == accepted['remaining_original_duty']
          == semantic_outcomes['swap.owner_correspondence'] == preserved,
          'the original compound swap timeout was omitted or promoted')
    move = {'id': 'move_source', 'targets': observed_targets, 'complete_task_contexts': len(selected_tasks),
        'task_contexts': selected_tasks, 'historical_source_commit': MOVE_SOURCE,
        'historical_identity_preserved': True, 'historical_reader': cold['reader_check'],
        'historical_runtime_scope': cold['historical_runtime_snapshot_boundary'],
        'current_source_view_checker': fresh['checker'], 'historical_source_view_checker': original['checker'],
        'current_type_registry': fresh['type_registry'], 'historical_type_registry': original['type_registry'],
        'complete_context_documents': {role: {'bytes': len(raw), 'sha256': _sha(raw)}
                                       for role, raw in documents.items()},
        'TCB': accepted['TCB']+accepted['additional_TCB']}
    result = {'created': '2026-10-16 ET', 'checker': identity(), 'scientific_dependencies_bound': True,
        'complete_source_target_count': 59, 'components': [*common['components'], move],
        'base_scientific_catalog_sha256': previous.REVIEWED_CATALOG_SHA256,
        'move_mathematical_bundle_sha256': MOVE_BUNDLE_SHA256, 'preserved_unaccepted_swap': preserved,
        'source_admission': False, 'source_Heap_Typed_bridge_established': False,
        'caller_acceptance': False, 'current_model_records_created': [], 'historical_records_rewritten': False,
        'proof_basis': 'exact retained conditional mathematical evidence only; source-created premises and source observation remain separate'}
    return result, files
