"""Exact administrative hard-kill margin revision; no remote operation."""
import ast
import hashlib
import json
from pathlib import Path

T = Path('/private/tmp')
W = Path('/Users/yanrujhou/.codex/worktrees/lanl-ticket11/ArchEvolve/swdb-project')
C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'

def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, value):
    data = value.encode() if isinstance(value, str) else value
    if path.exists():
        assert path.read_bytes() == data, 'preserve an existing distinct artifact: ' + str(path)
    else:
        path.write_bytes(data)

pairs = [
    ('lanl-dispatch-cpu-model-validation-a3-metadata2400.py', 'f1ddb874189abb28fecb7ef4431f6382d3c09442ae1a75afd0164f4562f276bc', 'lanl-dispatch-cpu-model-validation-a3-metadata2400-cleanup60.py', 'lanl-cpu-model-validation-a3-metadata2400-cleanup60-runner.py'),
    ('lanl-dispatch-cpu-band-report-a3-metadata2400.py', '83b2683b5bb21534d7dbd962555770842b8dd24748ba5119abec9339d53b0ad2', 'lanl-dispatch-cpu-band-report-a3-metadata2400-cleanup60.py', 'lanl-cpu-band-report-a3-metadata2400-cleanup60-runner.py'),
]
rows = []
for old_name, old_sha, new_name, runner_name in pairs:
    old_path, new_path = T / old_name, T / new_name
    assert sha(old_path) == old_sha
    before = old_path.read_bytes()
    assert before.count(b'--kill-after=20s') == 1
    after = before.replace(b'--kill-after=20s', b'--kill-after=60s')
    assert after.replace(b'--kill-after=60s', b'--kill-after=20s') == before
    assert ast.dump(ast.parse(after.replace(b'--kill-after=60s', b'--kill-after=20s'))) == ast.dump(ast.parse(before))
    tree = ast.parse(after)
    kill_literals = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith('--kill-after=')]
    assert kill_literals == ['--kill-after=60s']
    assignments = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'RUNNER_TEMPLATE' for t in n.targets)]
    assert len(assignments) == 1
    runner = ast.literal_eval(assignments[0].value)
    old_tree = ast.parse(before)
    old_assignment = next(n for n in old_tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'RUNNER_TEMPLATE' for t in n.targets))
    assert runner == ast.literal_eval(old_assignment.value)
    assert 'time.monotonic()+18000' in runner and 'cap=2400' in runner
    if 'model-validation' in new_name:
        assert "'--max-wall-s','900'" in runner and "run(args,'collect-'+kernel+'-g'+str(scale),3600)" in runner
    else:
        assert "'freeze-'+kernel,3600" in runner and "'estimate-'+kernel,2400" in runner
    assert '17-linux-cleanup-smoke-mbit10-20261006-a1.json' in runner
    assert '31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec' in runner
    assert 'bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289' in runner
    save(new_path, after)
    save(T / runner_name, runner)
    rows.append({'predecessor': old_name, 'predecessor_sha256': old_sha, 'helper': new_name, 'helper_sha256': sha(new_path), 'runner': runner_name, 'runner_sha256': sha(T / runner_name), 'exact_single_literal_reversal': True, 'decoded_runner_bytes_unchanged': True, 'normalized_outer_ast_unchanged': True, 'argv_hard_kill_after_s': 60})

old_guard = T / 'lanl-admit-cpu-future-phase-20261007.py'
assert sha(old_guard) == 'f461d5c36065ee4b31e6cb137a763ea95811940746117813fff4c0760ba1b3ac'
before = old_guard.read_bytes()
replacements = []
after = before
for row in rows:
    for old, new in ((row['predecessor'], row['helper']), (row['predecessor_sha256'], row['helper_sha256'])):
        old, new = old.encode(), new.encode()
        assert after.count(old) == 1
        after = after.replace(old, new)
        replacements.append((old, new))
restored = after
for old, new in reversed(replacements):
    assert restored.count(new) == 1
    restored = restored.replace(new, old)
assert restored == before and ast.dump(ast.parse(restored)) == ast.dump(ast.parse(before))
guard = T / 'lanl-admit-cpu-future-phase-cleanup60-20261007.py'
save(guard, after)
admission = json.loads((T / 'lanl-cpu-model-a3-local-admission-20261007.json').read_text())
assert admission['identity_sha256'] == digest({k: v for k, v in admission.items() if k != 'identity_sha256'}) == 'fe2890f8e7d8c95d6841ddd78b61762667e07c02688567676aca5d8fc4f4e3bd'
assert admission['admitted_for_parent_development'] is True and admission['source_commit'] == C and admission['estimator_sha256'] == F6
assert len(admission['forecasts']) == 4 and all(r['predicted_seconds'] > 0 and r['native_seconds'] is None and r['error_band'] is None for r in admission['forecasts'])
proof_path = W / '.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-linux-cleanup-smoke-mbit10-20261006-a1.json'
linux = json.loads(proof_path.read_text())['receipt']
assert linux['passed'] is True and linux['helper_sha256'] == sha(T / 'lanl17_parent_helpers.py') == '31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec'
assert linux['processes_py_sha256'] == sha(W / 'swdb/processes.py') == 'bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
assert linux['cleanup']['survivors'] == {}
process_text = (W / 'swdb/processes.py').read_text()
cleanup_tree = ast.parse((T / 'lanl17_parent_helpers.py').read_text())
cleanup_owned = next(n for n in cleanup_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'cleanup_owned')
assert 'timeout=grace_seconds' in process_text and 'child.wait(timeout=5)' in process_text
assert '(signal.SIGTERM, 15), (signal.SIGKILL, 5)' in ast.unparse(cleanup_owned)
proof = {'format': 'swdb.cpu-cleanup-grace-preparation.v1', 'source_commit': C, 'estimator_sha256': F6, 'helpers': rows, 'guard': {'predecessor': old_guard.name, 'predecessor_sha256': sha(old_guard), 'helper': guard.name, 'helper_sha256': sha(guard), 'exact_path_and_expected_hash_reversal': True}, 'actual_model_admission_identity': admission['identity_sha256'], 'prior_actual_linux_cleanup': {'path': str(proof_path.relative_to(W)), 'file_sha256': sha(proof_path), 'receipt_helper_sha256': linux['helper_sha256'], 'processes_py_sha256': linux['processes_py_sha256'], 'passed': True, 'reuse_scope': 'Unchanged cleanup primitives only; no new Linux execution and no claim that the old20s outer margin covered both sequential cleanup steps.'}, 'sequential_declared_wait_s': {'stop_group_grace': 15, 'stop_group_kill_wait': 5, 'cleanup_owned_term': 15, 'cleanup_owned_kill': 5, 'sum': 40, 'outer_hard_kill_after': 60}, 'unchanged_caps': {'native_deadline_s': 900, 'metadata_s': 2400, 'native_enclosing_process_s': 3600, 'report_protocol_freeze_s': 3600, 'runner_s': 18000, 'outer_s': 18300}, 'portable_verification_pending': True, 'remote_dispatch_executed': False, 'application_performance_timings_collected': False, 'scope': 'Exact hard-kill-margin control revision after independent model admission and before native development. Original controls and scientific source/recipes retained.'}
proof['identity_sha256'] = digest(proof)
save(T / 'lanl-cpu-cleanup60-preparation-proof-20261007.json', json.dumps(proof, indent=2) + '\n')
print(json.dumps({'helpers': rows, 'guard': proof['guard'], 'preparation_identity': proof['identity_sha256']}, indent=2))
