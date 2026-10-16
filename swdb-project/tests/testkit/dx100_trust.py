"""2026-10-16 ET. Builders for explicitly scripted DX100 proof record controls."""
import hashlib
import json
import shutil
import sys

import yaml

from conftest import FIXTURES, REPO, make_records, run_swdb

TRUST = {
    'mmio_ordering': 'The pinned MMIO implements call semantics including ordering; its wait fence lacks a memory clobber, a portability note independent of candidate artifacts.',
    'cross_core_filter': 'A DX100 store remains visible if the snoop filter drops its line before the write reaches L3.',
    'cross_core_write_buffer': 'A DX100 store remains visible when L3 passes a write below it because no block can be allocated.',
    'no_stale_cpu_copy': 'No stale CPU copy survives a DX100 store (owner Eric).',
    'one_instance': 'All commands belong to one DX100 instance.',
}


def run_semantics_fixture(tmp_path, adapter, mark=True, mutate=False, *, source=None, extra_calls=(), source_files=None,
                          postcondition=None, semantics_transform=None, contract_transform=None, tool_environment=None, method_transform=None, bounds=None):
    """Public fixture; default tools are explicit stand-ins. Root-admitted actual tests supply their environment."""
    from swdb import c_lowering, cbmc_adapter, cbmc_translator
    library = tmp_path / 'library'
    for folder in ('proof_semantics', 'dx100'):
        shutil.copytree(REPO / 'library' / folder, library / folder)
    old = library / 'proof_semantics/dx100_bfs_0_1.yaml'
    data = yaml.safe_load(old.read_text())
    data.update(id='semantics.dx100_trust_fixture', version='0.2', sequence=2)
    data['calls'] += list(extra_calls)
    data['rules'] += [{'id': name, 'statement': sentence, 'assumed': {'owner': 'Eric'}, 'record_assumption': mark}
                     for name, sentence in TRUST.items()]
    if semantics_transform is not None:
        semantics_transform(data, library)
    if semantics_transform is None:
        old.unlink()
    semantics = library / 'proof_semantics/dx100_trust_fixture.yaml'
    semantics.write_text(yaml.safe_dump(data, sort_keys=False))
    units = library / 'proof_units'
    units.mkdir()
    source = source or 'void maa_const(int value, int reg);\nint trust_fixture(int *p) { maa_const(7, 0); p[0] = 7; return 7; }\n'
    (units / 'trust.cc').write_text(source)
    for name, text in (source_files or {}).items():
        path = units / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    contracts = library / 'rewrite_contracts'
    contracts.mkdir()
    contract = {
        'id': 'contract.dx100_trust_fixture', 'kind': 'rewrite_contract', 'formal_frame': 1, 'version': '1.0',
        'provenance': {'origin': {'intrinsic_specification': 'ticket28-record-plumbing-fixture'}},
        'proof_unit': {'source': {'root': 'library', 'path': 'proof_units/trust.cc',
                                  'sha256': hashlib.sha256(source.encode()).hexdigest()}, 'function': 'trust_fixture',
                       'array_domains': {'p': {'extent': '1'}}},
        'concurrency_frame': [{'array': 'p', 'shared_actions': [], 'history_reads': False}],
        'clauses': [{'id': 'result', 'role': 'postcondition', 'statement': 'Synthetic trust-record fixture.',
                     'discharge_mode': 'runtime_guard', 'negative_control': {'id': 'wrong-result', 'check': 'result'},
                     'acsl': {'text': postcondition or r'assigns p[0]; ensures \result == 7;', 'uses': []},
                     'proof_placement': {'once': 'self'}}],
        'pattern_key': [{'roles': ['index', 'target'], 'address_shapes': ['stream', 'single_valued_indirect'],
                         'update_kind': 'read'}],
        'strategies': [], 'uses_intrinsics': [], 'uses_library_operations': [], 'runtime_guards': [], 'knobs': [],
        'preservation_obligations': [], 'correctness_check': {'kernel': 'fixture', 'check': 'fixture'},
        'execution_witness': {'check': 'fixture'},
        'negative_controls': [{'id': kind, 'kind': kind, 'check': 'fixture'}
                              for kind in ('overlapping_pointer', 'double_claim', 'dropped_operand')],
        'requirement_map': []}
    if contract_transform is not None:
        contract_transform(contract)
    (contracts / 'trust.yaml').write_text(yaml.safe_dump(contract, sort_keys=False))
    methods = library / 'methods'
    methods.mkdir()
    method = yaml.safe_load((FIXTURES / 'proof/methods/contract-fixture-1.yaml').read_text())
    method['c_lowering']['translators'] = [c_lowering.identity()['c_lowering'], cbmc_translator.identity()]
    next(row for row in method['lineup'] if row['tool'] == 'cbmc')['flags'] = list(cbmc_adapter.FROZEN)
    next(row for row in method['lineup'] if row['tool'] == 'frama-c-wp')['flags'] += [
        '-rte-initialized', '@all', '-wp-no-filter-init', '-machdep', 'x86_64']
    if semantics_transform is not None:
        from swdb import proof_setup
        method.update(id='method.dx100-selector-fixture-0-2', sequence=2)
        method['checks'].update(proof_setup.identity())
        method['c_lowering']['naming_rules'] = c_lowering.naming_rules()
        next(row for row in method['lineup'] if row['tool']=='frama-c-wp')['flags'] += [
            '-wp-prover','z3,cvc5,alt-ergo']
    if method_transform is not None:
        method_transform(method)
    (methods / (method['id'].removeprefix('method.')+'.yaml')).write_text(yaml.safe_dump(method, sort_keys=False))
    marker = tmp_path / 'must-not-launch-solver'
    mutation = (f'    import yaml\n    path = Path({str(semantics)!r})\n'
                '    data = yaml.safe_load(path.read_text())\n'
                '    data["rules"][-1]["statement"] = "Changed after validation."\n'
                '    path.write_text(yaml.safe_dump(data, sort_keys=False))\n') if mutate else ''
    version_only = tmp_path / 't28-version-only-adapter.py'
    version_only.write_text('import sys\nfrom pathlib import Path\n'
                            'if sys.argv[1:] == ["--version"]:\n' + mutation +
                            '    print("6.11"); sys.exit(0)\n'
                            f'Path({str(marker)!r}).touch()\nraise SystemExit(99)\n')
    frama = tmp_path / 't28-scripted-typechecker.py'
    frama.write_text('import sys\nfrom pathlib import Path\n'
                     'if sys.argv[1:] == ["-version"]:\n' + mutation +
                     '    print("33.0"); sys.exit(0)\n'
                     f'if "-wp" in sys.argv: Path({str(marker)!r}).touch(); sys.exit(99)\n'
                     'raise SystemExit(0)\n')
    why3 = tmp_path / 'scripted-why3.conf'
    labels = {'z3': 'Z3', 'cvc5': 'CVC5', 'alt-ergo': 'Alt-Ergo'}
    why3.write_text(''.join(f'[prover]\nname = "{labels[row["tool"]]}"\nversion = "{row["version"]}"\n'
                            'command = "/usr/bin/false"\n'
                            for row in method['lineup'] if row['tool'] in labels))
    records = make_records(tmp_path)
    environment = {'SWDB_CBMC': f'{sys.executable} {version_only}',
                   'SWDB_FRAMA_C': f'{sys.executable} {frama}' if adapter == 'wp' else 'none',
                   'WHY3CONFIG': str(why3), 'SWDB_VERIFIER_LOCK': str(tmp_path/'standin-only.lock')}
    if tool_environment is not None:
        environment = dict(tool_environment)
    result = run_swdb('prove', '--records', records.path, '--summary', contract['id'], '--adapter', adapter,
                      '--bounds', json.dumps({'threads': 1, 'input_size': 1} if bounds is None else bounds), '--runs-dir', tmp_path / 'runs',
                      '--format', 'json', env=environment, timeout=1200)
    return result, records, semantics, marker
