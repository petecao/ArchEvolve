"""Produce separate, unexecuted report-only controls; exact reversible changes."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path('/private/tmp')
OLD_RAW = '/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-band-report-20261006-a3'
NEW_RAW = '/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-band-report-20261007-a4'
OLD_JOB = 'swdb-lanl-cpu-band-report-20261006-a3'
NEW_JOB = 'swdb-lanl-cpu-band-report-20261007-a4'
OLD_IMPORT = 'import copy,datetime,json,math,os,shutil,signal,subprocess,time'
NEW_IMPORT = 'import copy,datetime,hashlib,json,math,os,shutil,signal,subprocess,time'
ORIGINALS = {
 'dispatcher': ('lanl-dispatch-cpu-band-report-a3-metadata2400-cleanup60.py', 'dd74dbbe238c1d0c8222d894acd94ef1d344049da257d2a0d744afefb3d2b120'),
 'exporter': ('lanl-export-cpu-band-report-a3.py', '788c5cfd72433916daac544420de5251eb6d549c56afaeba455a82416f11dbb1'),
 'dispatch_guard': ('lanl-admit-cpu-future-phase-cleanup60-20261007.py', 'b406d3d06b3bddb2cd433cf8f3c47fa80f03314b23795a4b40c045a9120a1e93'),
 'export_guard': ('lanl-export-completed-cpu-phase-guard-20261007.py', 'e8fb700fa438ad1580167593f047c632c1e354b00ad405bd67e4b330c8fd85f0')}
NAMES = {
 'dispatcher': 'lanl-dispatch-cpu-band-report-a4-metadata2400-cleanup60-hashlib.py',
 'exporter': 'lanl-export-cpu-band-report-a4.py',
 'dispatch_guard': 'lanl-admit-cpu-future-phase-cleanup60-report-a4-20261007.py',
 'export_guard': 'lanl-export-completed-cpu-phase-guard-report-a4-20261007.py'}

def sha(data): return hashlib.sha256(data).hexdigest()
def digest(value): return sha(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
def decoded(source):
 tree = ast.parse(source)
 node = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'RUNNER_TEMPLATE' for t in n.targets))
 return ast.literal_eval(node.value)

old = {key: (ROOT / name).read_text() for key, (name, pin) in ORIGINALS.items()}
for key, (_, pin) in ORIGINALS.items(): assert sha(old[key].encode()) == pin
new = {}; proofs = {}

def variant(key, replacements):
 text = old[key]
 for before, after, count in replacements:
  assert text.count(before) == count, (key, before, text.count(before))
  text = text.replace(before, after)
 reversed_text = text
 for before, after, count in reversed(replacements):
  assert reversed_text.count(after) == count
  reversed_text = reversed_text.replace(after, before)
 assert reversed_text == old[key]
 compile(text, NAMES[key], 'exec')  # Syntax only; never execute dispatch/Store/control.
 path = ROOT / NAMES[key]; assert not path.exists(); path.write_text(text)
 new[key] = text
 proofs[key] = {'original_path': str(ROOT / ORIGINALS[key][0]), 'original_sha256': ORIGINALS[key][1],
  'path': str(path), 'bytes': len(text.encode()), 'sha256': sha(text.encode()),
  'allowed_exact_replacements': [{'before': b, 'after': a, 'occurrences': n} for b, a, n in replacements],
  'exact_reversal_byte_equal': True}

variant('dispatcher', [(OLD_IMPORT, NEW_IMPORT, 1), (OLD_RAW, NEW_RAW, 1), (OLD_JOB, NEW_JOB, 2)])
assert decoded(new['dispatcher']).replace(NEW_IMPORT, OLD_IMPORT) == decoded(old['dispatcher'])
old_runner = ast.parse(decoded(old['dispatcher'])); new_runner = ast.parse(decoded(new['dispatcher']))
import_node = next(n for n in new_runner.body if isinstance(n, ast.Import) and any(a.name == 'copy' for a in n.names))
assert sum(a.name == 'hashlib' for a in import_node.names) == 1
import_node.names = [a for a in import_node.names if a.name != 'hashlib']
assert ast.dump(new_runner, include_attributes=False) == ast.dump(old_runner, include_attributes=False)
runner_path = ROOT / 'lanl-cpu-band-report-a4-metadata2400-cleanup60-hashlib-runner.py'
assert not runner_path.exists(); runner_path.write_text(decoded(new['dispatcher']))
variant('exporter', [(OLD_RAW, NEW_RAW, 1)])
variant('dispatch_guard', [(ORIGINALS['dispatcher'][0], NAMES['dispatcher'], 1),
                          (ORIGINALS['dispatcher'][1], proofs['dispatcher']['sha256'], 1)])
old_line = "raw=P('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-'+('band-report' if phase=='report' else phase)+'-20261006-a3')"
new_line = "raw=P('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-'+('band-report' if phase=='report' else phase)+('-20261007-a4' if phase=='report' else '-20261006-a3'))"
variant('export_guard', [(old_line, new_line, 1), (ORIGINALS['exporter'][0], NAMES['exporter'], 1),
                        (ORIGINALS['exporter'][1], proofs['exporter']['sha256'], 1)])

def phase_raw(source, phase):
 node = next(n for n in ast.parse(source).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'raw' for t in n.targets))
 return str(eval(compile(ast.Expression(node.value), '<literal path expression only>', 'eval'), {'P': Path, 'phase': phase, '__builtins__': {}}))
assert phase_raw(old['export_guard'], 'holdout') == phase_raw(new['export_guard'], 'holdout')
assert phase_raw(new['export_guard'], 'report') == NEW_RAW

diff_path = ROOT / 'lanl-cpu-band-report-a4-hashlib-exact-diff.txt'
assert not diff_path.exists()
lines = []
for key in new:
 if key == 'dispatcher':
  # Avoid an encoded whole-runner line obscuring the sole decoded import fix.
  before = '\n'.join(line for line in old[key].splitlines() if not line.startswith('RUNNER_TEMPLATE=')) + '\n'
  after = '\n'.join(line for line in new[key].splitlines() if not line.startswith('RUNNER_TEMPLATE=')) + '\n'
  lines.extend(difflib.unified_diff(decoded(old[key]).splitlines(True), decoded(new[key]).splitlines(True), fromfile='a3-decoded-runner', tofile='a4-decoded-runner'))
 else: before, after = old[key], new[key]
 lines.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=ORIGINALS[key][0], tofile=NAMES[key]))
diff_path.write_text(''.join(lines))
proof = {'format': 'swdb.cpu-band-report-hashlib-a4-preparation.v1',
 'source_C': 'f893fed400347ed23d92e917d8bde21b75e5375d',
 'estimator_sha256': 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3',
 'controls': proofs,
 'decoded_runner': {'path': str(runner_path), 'sha256': sha(runner_path.read_bytes()),
                    'only_AST_change': 'add hashlib to actual runner standard import',
                    'all_other_decoded_runner_bytes_equal_after_exact_import_reversal': True},
 'decoded_diff': {'path': str(diff_path), 'sha256': sha(diff_path.read_bytes())},
 'holdout_export_guard_raw_path_unchanged': phase_raw(new['export_guard'], 'holdout'),
 'report_raw_path': NEW_RAW, 'fresh_report_job_and_tmux_session': NEW_JOB,
 'pure_export_branch_checkout_and_canonical_receipt_names': 'unchanged logical study a3',
 'development_holdout_controls': 'unchanged originals; REPORT binding only',
 'scientific_report_body_caps_KILL_costs_widths_IDs_C_F6': 'byte unchanged after allowed exact reversals',
 'old_report_attempt': {'raw': OLD_RAW, 'generation': 508, 'wrapper_exit': 1,
   'reported_failure': 'NameError hashlib at decoded runner line 105 before started.txt, records or Store initialization',
   'authority': 'parent actual failure handoff; failed raw/controls retained, not replayed'},
 'new_control_execution': 'NOT RUN; parent review/stage/retry/export only',
 'integration_edits': False, 'Store_native_provider_lease_cleanup_fixture_execution': False}
proof['identity_sha256'] = digest(proof)
proof_path = ROOT / 'lanl-cpu-band-report-a4-hashlib-preparation.json'
assert not proof_path.exists(); proof_path.write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps({'controls': {key: row['sha256'] for key, row in proofs.items()},
                  'preparation': str(proof_path), 'identity_sha256': proof['identity_sha256'],
                  'file_sha256': sha(proof_path.read_bytes()), 'actual_execution': 'NOT RUN'}, indent=2))
