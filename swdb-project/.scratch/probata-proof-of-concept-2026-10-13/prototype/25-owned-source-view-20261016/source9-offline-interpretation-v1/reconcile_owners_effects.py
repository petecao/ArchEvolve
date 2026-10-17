"""2026-10-16 ET. Pinned, child-free full source9 Owners/Effects syntax join.

Run locally against already retained declarative metadata. No SSH, raw task
reader, prover, project import, scientific adoption or source-memory admission.
"""
import hashlib
import json
from pathlib import Path
import runpy
import sys


HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
PROJECT = POC.parents[1]
ATTEMPTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork')) \
            or event in {'os.system', 'ctypes.dlopen'}:
        ATTEMPTS.append(event)
        raise RuntimeError('external execution forbidden during offline interpretation')


sys.dont_write_bytecode = True
sys.addaudithook(audit)


def need(value, label):
    if not value:
        raise ValueError(label)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


PINS = {
    'capture': (POC/'evidence/t25-owned-source9-math-ast-v3-actual-stdout-20261016.json',
                500042, '9924e02166c0613047bf750b31a06508b67d5eb8853fec79a59c8f1d926b5a72'),
    'canonical_source_interface': (HERE.parent/'namespace-repair-v1/inert-v2/manifest.json',
                31307, 'a7486a5eb0133a49f4fd590f7fc0651371da263339044dd99c95978957f40e55'),
    'Owners_source': (PROJECT/'swdb/vector_owned_state.mlw', 2389,
                'a2c295d2c6720a9c8c522f05e19723c2d2d2a32b63f9b198aab03f195269e4b6'),
    'OwnedEffects_source': (PROJECT/'swdb/vector_owned_effects.mlw', 3128,
                '6bfc13341d2faceb5a3fb64bd2d5bff22dd03c52a1fa3d5c4cb39b6e9c83f7f5'),
    'Heap_context_V2': (HERE/'heap_reader_v2.py', 18821,
                '66fb703fd3b2a0503ca834613081740527d54f53b05d3b2e38fd81b477983bf2'),
    'Owners_Effects_interpreter': (HERE/'owners_effects_reader.py', 20608,
                '248633006c0a9c28b42b60cc0697dcd2d651a0d314ec3924a8bd2f281cdcdb13'),
    'accepted_typed_Boolean_alpha_syntax': (
                POC/'prototype/25-owned-transfer-20261016/cold-g621-encoding-v3/semantic_terms.py',
                15336, '0caf0330afed019637d03228a94f5af5cfc305e358f6eca51c631a881e163ef7'),
}


def main():
    contents, observed = {}, []
    for role, (path, size, sha256) in PINS.items():
        raw = path.read_bytes()
        need(path.is_file() and not path.is_symlink() and len(raw) == size
             and hashlib.sha256(raw).hexdigest() == sha256, 'exact physical input: '+role)
        contents[role] = raw
        observed.append({'role': role, 'path': str(path), 'bytes': size, 'sha256': sha256})
    semantic = runpy.run_path(str(PINS['accepted_typed_Boolean_alpha_syntax'][0]))
    heap = runpy.run_path(str(PINS['Heap_context_V2'][0]))
    own = runpy.run_path(str(PINS['Owners_Effects_interpreter'][0]))
    capture = json.loads(contents['capture'])
    manifest = json.loads(contents['canonical_source_interface'])
    need(capture['task_count'] == 26 and capture['unique_math_commands'] == 115
         and capture['all29_content_and_nine_stat_pre_post_equal'] is True,
         'complete settled capture census')
    need(len(manifest['obligations']) == len(own['CONCLUSIONS']) == 9
         and {row['id'] for row in manifest['obligations']} == set(own['CONCLUSIONS']),
         'all nine exact original source interface duties')
    for row in manifest['obligations']:
        need(row['statement'] == own['source_statement'](row['id']),
             'byte-identical full original ACSL statement: '+row['id'])
        raw = (PINS['canonical_source_interface'][0].parent/row['path']).read_bytes()
        need(hashlib.sha256(raw).hexdigest() == row['sha256'], 'exact original public source lemma')
        need(row['statement'].encode() in raw, 'original complete statement present in public input')
    trees = capture['deduplicated_complete_math_commands']
    need(len(trees) == 115 and all(digest(tree) == key for key, tree in trees.items()),
         'all complete captured mathematical trees content-addressed')
    task_rows, definitions, support, modes = [], 0, 0, {}
    for task in capture['tasks']:
        refs = [row for row in task['commands'] if row['tree_ref'] is not None]
        need(all(row['tree_ref'] == row['sha256'] and row['tree_ref'] in trees for row in refs),
             'complete per-task ordered mathematical command references')
        commands = [trees[row['tree_ref']] for row in refs]
        need(len({row[1] for row in commands if row[0] == 'define-fun'})
             == sum(row[0] == 'define-fun' for row in commands), 'unique complete definition symbols')
        context = heap['task_context'](commands, semantic['one'], semantic['canon'])
        result = own['reconcile_task'](commands, task['id'], context, semantic['one'],
                                       semantic['canon'], heap['normalize_source_primitives'])
        need(result['actual_complete_goal_command_sha256'] == task['goal_command_sha256'],
             'exact original goal command attribution')
        modes[context['mode']] = modes.get(context['mode'], 0)+1
        definitions += result['own_definition_count']
        support += len(result['support_assertions_not_consumed_here'])
        # Every remaining complete command is returned by content identity for
        # the independent outer Heap/standard-driver/support join.
        result['unhandled_complete_definition_sha256s'] = [digest(row) for row in
                                                          result.pop('unhandled_complete_definitions')]
        result['support_assertion_command_sha256s_not_consumed_here'] = [digest(row) for row in
                                                    result.pop('support_assertions_not_consumed_here')]
        result['artifact'] = task['artifact']
        result['complete_ordered_math_command_sha256s'] = [row['sha256'] for row in refs]
        task_rows.append(result)
    need(not ATTEMPTS, 'no external execution attempts')
    return {'date': '2026-10-16 ET', 'classification': 'COMPLETE_OWNERS_EFFECTS_AND_GOAL_SYNTAX_MATCH',
            'inputs': observed, 'tasks': task_rows, 'task_count': len(task_rows),
            'original_source_duties': 9, 'all26_complete_goals_equivalent': True,
            'all_observed_Owners_Effects_definition_instances_equivalent': definitions,
            'support_assertions_returned_unconsumed': support, 'checked_encoding_context_modes': modes,
            'complete_support_or_mathematical_adoption': False, 'new_proof_or_solver_execution': False,
            'source_Heap_Typed_body_lifetime_caller_default_admission': False,
            'retained_original_swap_timeout_unchanged': True, 'external_attempts': ATTEMPTS}


if __name__ == '__main__':
    print(json.dumps(main(), sort_keys=True, indent=2, allow_nan=False))
