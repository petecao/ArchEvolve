"""2026-10-16 ET. Focused public regressions at an immutable source checkpoint."""
import hashlib
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

assert sys.flags.isolated and sys.flags.dont_write_bytecode and not sys.flags.optimize
raw = Path(os.environ['PROBATA_OUTPUT']).resolve()
source = Path('/data1/yanruj/probata-resume-20261016-615ddf50')
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
                  SWDB_CBMC='/data1/yanruj/probata-verifiers/cbmc-6.11.0/usr/bin/cbmc',
                  PYTHONNOUSERSITE='1', PYTHONSAFEPATH='1', PYTHONPATH=str(project),
                  PYTHONDONTWRITEBYTECODE='1', PYTHONPYCACHEPREFIX=str(raw / 'pytest-source-cache'),
                  PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
sys.path[:0] = [str(project), str(project / 'tests')]
import pytest

nodes = ['tests/test_vector_reallocation_caller_view.py',
         'tests/test_vector_reallocation_private_frame.py',
         'tests/test_vector_reallocation_closed_view.py',
         'tests/test_vector_reallocation_reserve_application.py',
         'tests/test_vector_reallocation_caller_packets.py',
         'tests/test_vector_reallocation_copy_prefix_cases.py',
         'tests/test_bounded_initialization.py',
         'tests/test_cbmc_adapter.py::test_the_safe_fixture_is_proven_within_its_bounds_on_both_forms']
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
          'scope': 'Focused regressions only; not complete ticket or scientific proof acceptance'}
if (raw / 'junit.xml').is_file():
    root = ET.parse(raw / 'junit.xml').getroot()
    cases = list(root.iter('testcase'))
    census.update(cases=len(cases),
                  failures=[c.get('name') for c in cases if c.find('failure') is not None],
                  errors=[c.get('name') for c in cases if c.find('error') is not None],
                  skips=[c.get('name') for c in cases if c.find('skipped') is not None])
(raw / 'focus-result.json').write_text(json.dumps(census, indent=2) + '\n')
if status == 0 and (census['cases'] == 0 or census['skips'] or census['failures'] or census['errors'] or not census['cache_absent']):
    raise SystemExit('incomplete regression selection, skipped/failed cases or bytecode cache created')
raise SystemExit(status)
