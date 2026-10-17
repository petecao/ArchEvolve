"""2026-10-16 ET. Mixed-pair public controls at immutable sourcedcdecf31; no real WP/CBMC."""
import hashlib
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

assert sys.flags.isolated and sys.flags.dont_write_bytecode and not sys.flags.optimize
raw = Path(os.environ['PROBATA_OUTPUT']).resolve()
source = Path('/data1/yanruj/probata-resume-20261016-dcdecf31')
assert Path.cwd().resolve() == source, 'root wrapper must start at the immutable repository root'
project = source / 'swdb-project'
assert project.is_dir()
os.chdir(project)
assert raw.is_dir() and sys.pycache_prefix == str(raw / 'pytest-source-cache')
assert not Path(sys.pycache_prefix).exists()
assert os.environ['SWDB_VERIFIER_RSS_CAP_BYTES'] == '8589934592'
clang = '/data/yanruj/EvolveSWDB_runs/probata-source-gate-native-20261015-1102-node0/compiler-bin/clang++'
for path, digest in {'/data/yanruj/EvolveSWDB_runs/probata-source-gate-native-20261015-1102-node0/compiler-bin/clang++': '3c053dce26cf5ef22656f1ec9efe0cdf2911a37d5a910261895ac9c42e128fe4', '/data1/yanruj/venvs/swdb-test/bin/python': 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f', '/data1/yanruj/probata-verifiers/cbmc-6.11.0/usr/bin/cbmc': 'a62af25d27425610608221d79c202f993efe1d5a85cece186119bec196382995'}.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
os.environ.update(SWDB_CLANG=clang,
                  SWDB_CBMC='none', SWDB_FRAMA_C='none', SWDB_PAIR_ACTUAL='0', SWDB_MIXED_PAIR_ACTUAL='0',
                  PYTHONNOUSERSITE='1', PYTHONSAFEPATH='1', PYTHONPATH=str(project),
                  PYTHONDONTWRITEBYTECODE='1', PYTHONPYCACHEPREFIX=str(raw / 'pytest-source-cache'),
                  PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
sys.path[:0] = [str(project), str(project / 'tests')]
import pytest

nodes = ['tests/test_pair_pointer_initialization.py', 'tests/test_pair_pointer_workflow.py::test_mixed_pair_lowering_and_native_identity_agree_without_pointee_access', 'tests/test_pair_pointer_workflow.py::test_unknown_pointer_pair_input_refuses_and_missing_models_do_not_launch', 'tests/test_pair_pointer_workflow.py::test_each_mixed_pair_body_reaches_public_parser_with_exact_contract', 'tests/test_pair_workflow.py::test_public_pair_lowering_preserves_values_copies_fields_and_self_assignment', 'tests/test_pair_workflow.py::test_uninitialized_pair_constructor_input_is_refused_by_public_lowering', 'tests/test_pair_workflow.py::test_pair_copy_and_assignment_do_not_initialize_unknown_source_storage', 'tests/test_pair_workflow.py::test_wrong_pair_field_has_a_defined_concrete_witness', 'tests/test_pair_workflow.py::test_pair_caller_without_current_member_proofs_never_launches_standin', 'tests/test_pair_workflow.py::test_changed_initializedness_source_invalidates_frozen_translator_before_standin', 'tests/test_pair_workflow.py::test_profile_refuses_output_anywhere_inside_full_checkout_before_creation', 'tests/test_pair_workflow.py::test_each_original_pair_body_reaches_public_parser_with_initialization_rte_and_smoke']
progress = []


class Progress:
    def pytest_runtest_logreport(self, report):
        progress.append({'nodeid': report.nodeid, 'when': report.when, 'outcome': report.outcome})
        (raw / 'focus-progress.json').write_text(json.dumps(progress, indent=2) + '\n')


arguments = ['-q', '--tb=short', '-p', 'no:cacheprovider', '--rootdir', str(project),
             '--basetemp', str(raw / 'pytest'), '--junitxml', str(raw / 'junit.xml'), *nodes]
(raw / 'focus-arguments.json').write_text(json.dumps(arguments, indent=2) + '\n')
status = int(pytest.main(arguments, plugins=[Progress()]))
census = {'exit_code': status, 'cases': 0, 'failures': [], 'errors': [], 'skips': [],
          'cache_absent': not Path(sys.pycache_prefix).exists(), 'source': str(project),
          'scope': '30 public control cases only: 11 child-free initializedness and 19 compiler/native/parser cases; Clang/native sanitizers or explicit parser-error stand-ins. No actual WP/CBMC/formal acceptance.'}
if (raw / 'junit.xml').is_file():
    root = ET.parse(raw / 'junit.xml').getroot()
    cases = list(root.iter('testcase'))
    census.update(cases=len(cases),
                  failures=[c.get('name') for c in cases if c.find('failure') is not None],
                  errors=[c.get('name') for c in cases if c.find('error') is not None],
                  skips=[c.get('name') for c in cases if c.find('skipped') is not None])
(raw / 'focus-result.json').write_text(json.dumps(census, indent=2) + '\n')
if status == 0 and (census['cases'] != 30 or census['skips'] or census['failures'] or census['errors'] or not census['cache_absent']):
    raise SystemExit('incomplete regression selection, skipped/failed cases or bytecode cache created')
raise SystemExit(status)
