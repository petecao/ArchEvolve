"""2026-10-16 ET. Author inert ORIGINAL no-growth generation from Git/stdlib only.

Never imports SWDB, runs the entry or invokes native/compiler/verifier tools.
"""
import ast
import base64
import copy
import hashlib
import json
import subprocess
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
PREDECESSOR = HERE.with_name('25-prefix10-resume-20261016')/'inert-c978393b'
SOURCE = 'c978393b119a3614229a37f0f2c8ca2a097c750b'
CACHED = Path('/private/tmp/probata-t25-caller104-compiler-controls-v1-20261016/pytest/test_public_alias_controls_kee1')
FUNCTION = 'vector_realloc_v3_no_growth'
OUTPUT = HERE/'inert-c978393b-v2'
CORE = Path('/Users/yanrujhou/.opam/framac-33/lib/frama-c-wp/core')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': digest(raw), 'bytes': len(raw)}


def git(*args):
    return subprocess.check_output(['/usr/bin/git', '--no-replace-objects', '-C', str(REPO), *args], timeout=60)


def definitions(raw, names):
    tree = ast.parse(raw)
    lines = raw.decode().splitlines(keepends=True)
    found = {node.name: ''.join(lines[node.lineno-1:node.end_lineno])
             for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names}
    if set(found) != set(names):
        raise ValueError('reviewed helper set differs')
    return found


def lineage(anchors):
    direct = ('tool', 'function', 'c_lowering_sha256', 'anchors', 'models', 'std_models', 'allocation')
    keys = ('count', 'receiver', 'alias', 'reserve_request', 'observation', 'guard',
            'entry_obligations', 'call_obligations', 'scalar_read_obligation',
            'lowered_lifetime', 'source_sha256', 'lowered_sha256')
    candidate = anchors['vector_reallocation_candidate']
    return {**{key: anchors[key] for key in direct},
            'candidate_source_events': {key: candidate[key] for key in keys}}


def main():
    predecessor = json.loads((PREDECESSOR/'packet.json').read_bytes())
    for key, name in [('entry', 'entry.py'), ('expected', 'expected.json'), ('root_command', 'root-command.json')]:
        if digest((PREDECESSOR/name).read_bytes()) != predecessor[key]['sha256']:
            raise ValueError('predecessor metadata/entry hash differs')
    old = json.loads((PREDECESSOR/'expected.json').read_bytes())
    if old['source_commit'] != SOURCE or git('rev-parse', SOURCE).decode().strip() != SOURCE:
        raise ValueError('exact original observation source differs')
    for row in old['source_blobs']:
        if digest(git('show', SOURCE+':swdb-project/'+row['relative'])) != row['sha256']:
            raise ValueError('source Git blob differs: '+row['relative'])
    for relative, row in old['source_consumer_trees'].items():
        if git('rev-parse', SOURCE+':swdb-project/'+relative).decode().strip() != row['oid']:
            raise ValueError('source consumer tree differs')
    lowered_path = CACHED/(FUNCTION+'.c'); anchors_path = CACHED/(FUNCTION+'.anchors.json')
    lowered = lowered_path.read_bytes(); anchor_raw = anchors_path.read_bytes()
    anchors = json.loads(anchor_raw)
    if digest(lowered) != '7082d6fc081e23547bf792f8029277695b83d933913545f290f66353ee5841ec':
        raise ValueError('retained genuine original lowering bytes differ')
    source_relative = 'tests/fixtures/proof/vector_reallocation_v3.cc'
    source_bytes = git('show', SOURCE+':swdb-project/'+source_relative)
    source_sha = digest(source_bytes)
    if source_sha != '1172e62dbff5076d25471285afcfa17927707dbe6fae121d9570109d39e62b57' or \
            anchors['vector_reallocation_candidate']['source_sha256'] != source_sha or \
            anchors['c_lowering_sha256'] != digest(lowered):
        raise ValueError('cached original source-header/anchor lineage differs')
    header = lowered.splitlines()[0].decode()
    if 'sha256 '+source_sha not in header or 'swdb-c-lowering 9 (kept-names.3), clang 22.1.8' not in header:
        raise ValueError('cached original source header differs')
    clauses = [r'requires 0 <= n;', r'assigns \nothing;', r'ensures \result == (n > 0 ? 7 : 0);']
    block = '/*@ '+'\n    '.join(clauses)+' */'
    anchor_line = '/* swdb-anchor '+FUNCTION+'.contract */'
    if lowered.decode().splitlines().count(anchor_line) != 1:
        raise ValueError('unique original root contract anchor required')
    merged = lowered.decode().replace(anchor_line+'\n', anchor_line+'\n'+block+'\n')
    if merged.replace(anchor_line+'\n'+block+'\n', anchor_line+'\n') != lowered.decode():
        raise ValueError('only exact original-root contract insertion is allowed')
    policy = {'cap_bytes': 8*1024**3, 'workers': 1, 'root_whole_seconds': 420,
              'root_outer_seconds': 540, 'profile_seconds': 300, 'frama_seconds': 210,
              'output_budget_bytes': 1024**3, 'metadata_reserve_bytes': 1024**2}
    keep = ('linux_clang_component_origin', 'linux_clang_components', 'linux_launch_binding',
            'linux_prefix', 'linux_project_identity_derivation', 'metadata_origin',
            'portable_import_surfaces', 'portable_surface_origin', 'remote_project',
            'source_blobs', 'source_consumer_trees', 'tools', 'why3_config', 'wp_artifacts')
    expected = {key: copy.deepcopy(old[key]) for key in keep}
    runtime_names = ('MemTyped.ml', 'Cint.ml', 'Factory.ml', 'MemVar.ml', 'MemLoader.ml', 'Ctypes.ml')
    generation_names = ('Wp_parameters.ml', 'ProverWhy3.ml', 'register.ml', 'Why3Provers.ml')
    sources = [{'name': name, 'sha256': digest((CORE/name).read_bytes())}
               for name in (*runtime_names, *generation_names)]
    flags = ['-wp', '-wp-rte', '-wp-cache', 'none', '-wp-model', '+real', '-wp-par', '1',
             '-machdep', 'x86_64', '-rte-initialized', '@all', '-wp-no-filter-init',
             '-wp-smoke-tests', '-wp-status-all', '-wp-prover', 'cvc5', '-wp-gen',
             '-wp-no-why3-detect', '-wp-fct', FUNCTION, '-wp-out', 'prover-files',
             '-wp-print', '-wp-msg-key', 'print-generated,why3:compile,why3:import,prover:pp_task',
             '-wp-why3-config', old['why3_config']['path']]
    expected.update(created='2026-10-16 ET', status='INERT / UNREVIEWED / NOT EXECUTED',
        source_commit=SOURCE, source_relative=source_relative, source_sha256=source_sha,
        function=FUNCTION, lowered_sha256=digest(lowered), cached_lowered_hex=lowered.hex(),
        cached_anchor_lineage=lineage(anchors),
        cached_inputs={'lowered': pin(lowered_path), 'anchors': pin(anchors_path)},
        source_header=header, contract_clauses=clauses, wp_input_sha256=digest(merged.encode()),
        generation_flags=flags, runtime_sources=sources, resource_policy=policy,
        scope='ORIGINAL no-growth root task generation only; unproved model summaries may appear as hypotheses. No proof, body/caller admission or source-runtime correspondence theorem.',
        generation_policy={'no_solver_proof': True, 'no_public_records': True,
            'no_project_theory_imports': True, 'no_inline_rewrite_or_layout_assertions': True,
            'property_selection': 'default complete properties; wp-fct only selects the original source root',
            'why3_generation': 'Wp_parameters.Generate; common tasks precede ProverWhy3.build_proof_task early return; solver detection explicitly disabled',
            'generation_primary_lines': {'Wp_parameters.ml': [698, 703],
                'ProverWhy3.ml': [1557, 1574], 'Why3Provers.ml': [47, 55], 'register.ml': [406, 439]},
            'fresh_lowering_required': True,
            'cached_anchor_comparison': 'Exact host-independent root anchors/models/call/source-event lineage; full host/version-specific provenance certificates retained separately and independently rechecked.'})
    expected_bytes = encoded(expected)
    old_entry = (PREDECESSOR/'entry.py').read_bytes()
    helper_names = ('sha', 'pin', 'write', 'surface', 'linux_admission', 'consumer_closure')
    helpers = definitions(old_entry, helper_names)
    template = (HERE/'entry-template-v2.py').read_text()
    entry = template.replace('# __REVIEWED_HELPERS__', '\n\n'.join(helpers[name] for name in helper_names))
    entry = entry.replace('__EXPECTED_SHA256__', digest(expected_bytes)).encode()
    ast.parse(entry)
    command = json.loads((PREDECESSOR/'root-command.json').read_bytes())
    bootstrap = command[6]
    substitutions = [
        (predecessor['entry']['sha256'], digest(entry)),
        (predecessor['expected']['sha256'], digest(expected_bytes)),
        (base64.b64encode(zlib.compress(old_entry, 9)).decode(), base64.b64encode(zlib.compress(entry, 9)).decode()),
        (base64.b64encode(zlib.compress((PREDECESSOR/'expected.json').read_bytes(), 9)).decode(),
         base64.b64encode(zlib.compress(expected_bytes, 9)).decode()),
    ]
    for before, after in substitutions:
        if bootstrap.count(before) != 1:
            raise ValueError('exact predecessor bootstrap embedding differs')
        bootstrap = bootstrap.replace(before, after)
    bootstrap = bootstrap.replace('copy-prefix10-root-early-preflight.json', 'original-no-growth-root-early-preflight.json')
    bootstrap = bootstrap.replace('copy-prefix10-diagnostic', 'original-no-growth-generation-v2')
    ast.parse(bootstrap)
    if len(bootstrap.encode()) >= 120000:
        raise ValueError('bootstrap exceeds reviewed transport allowance')
    command[6] = bootstrap
    OUTPUT.mkdir(exist_ok=False)
    for name, data in [('entry.py', entry), ('expected.json', expected_bytes),
                       ('root-command.json', encoded(command)), ('wp-input.expected.c', merged.encode()),
                       ('lowering.cached.c', lowered), ('anchors.cached.json', anchor_raw)]:
        (OUTPUT/name).write_bytes(data)
    copied = definitions(entry, helper_names)
    if copied != helpers:
        raise ValueError('reviewed metadata/guard helper bodies changed')
    packet = {'created': '2026-10-16 ET', 'status': 'INERT / UNREVIEWED / NOT EXECUTED',
        'root_kind': 't25-original-no-growth-generation-v2', 'source_commit': SOURCE,
        'remote_project': expected['remote_project'], 'function': FUNCTION,
        'entry': pin(OUTPUT/'entry.py'), 'expected': pin(OUTPUT/'expected.json'),
        'root_command': pin(OUTPUT/'root-command.json'), 'author': pin(Path(__file__)),
        'template': pin(HERE/'entry-template-v2.py'), 'predecessor_packet': pin(PREDECESSOR/'packet.json'),
        'previous_unexecuted_generation_packet': pin(HERE/'inert-c978393b-v1/packet.json'),
        'guard_control_script': pin(HERE/'guard-controls-v2.py'),
        'guard_control_receipt': pin(HERE/'guard-controls-v2.json'),
        'v2_repair_scope': 'Exception-safe process-group/known-descendant cleanup and reap; disappearing-file-safe raw census; projected aggregate output checks before fragment and census metadata writes; 1MiB final metadata reserve. No source/contract/solver/generation policy change.',
        'reviewed_helpers_exact': list(helper_names), 'cached_inputs': expected['cached_inputs'],
        'lowered_source_sha256': digest(lowered), 'source_cpp_sha256': source_sha,
        'wp_input_sha256': digest(merged.encode()), 'resource_policy': policy,
        'runtime_sources': sources, 'source_package_count': len(expected['source_blobs']),
        'bootstrap_bytes': len(bootstrap.encode()), 'project_imports': 0,
        'compiler_or_native_or_verifier_calls': 0, 'actual_generations': 0,
        'solver_proofs_requested': False, 'public_proof_records_created': 0,
        'source_runtime_correspondence_proved': False, 'model_acceptance': False,
        'caller_acceptance': False, 'ticket_closure': False,
        'root_admission_pending': True, 'independent_entry_review_pending': True}
    (OUTPUT/'packet.json').write_bytes(encoded(packet))
    print(json.dumps({'packet': pin(OUTPUT/'packet.json'), 'entry': packet['entry'],
                     'expected': packet['expected'], 'root_command': packet['root_command']}, indent=2))


if __name__ == '__main__':
    main()
