"""Ticket24 public unsupported-subset refusals; created 2026-10-15 ET.

Seam: swdb prove --adapter wp. Real Clang diagnoses the requested build;
Frama-C and prover declarations are stand-ins. No proof or solver is run.
"""
import hashlib
import json
import shutil
import sys

import pytest
import yaml

from conftest import FIXTURES, make_records, run_swdb
from test_c_lowering import OUTSIDE
from test_formal_frame import frame_contract, write_library
from test_wp_adapter import method_version
from swdb import c_lowering

# First excluded declaration/expression in the small sources, before the wrapper's #ifdef line.
OUTSIDE_LOCATIONS = {'inheritance': 2, 'virtual function': 1, 'exception': 2, 'lambda': 2,
                     'RTTI': 3, 'standard container std::map': 3, 'stream': 3}
pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason='Clang 22.1.8 is required')


@pytest.mark.parametrize('construct', sorted(OUTSIDE_LOCATIONS))
def test_public_wp_names_excluded_construct_and_source_location_without_launch(tmp_path, construct):
    records = make_records(tmp_path)
    library = tmp_path / 'library'
    # Validation sees the simple reference branch. The requested build alone
    # selects the excluded construct, so refusal is tested at the actual adapter.
    source = ('#ifdef WP24_OUTSIDE_CASE\n' + OUTSIDE[construct] +
              '#else\nint swdb_outside_unit(int n) { return 0; }\n#endif\n')
    entry = frame_contract('contract.fixture_wp24_outside', role='enabling', concurrency_frame=[], clauses=[
        {'id':'post','role':'postcondition','statement':'A fixture postcondition for admission only.',
         'discharge_mode':'runtime_guard','negative_control':{'id':'post-control','check':'fixture'},
         'acsl':{'text':r'assigns \nothing; ensures \result == 0;','uses':[]},
         'proof_placement':{'once':'self'}}])
    entry['proof_unit'] = {'function':'swdb_outside_unit','source':{'root':'library',
        'path':'proof_units/outside.cc','sha256':hashlib.sha256(source.encode()).hexdigest()}}
    write_library(library, {'proof_units/outside.cc':source,'rewrite_contracts/outside.yaml':entry})
    methods = library / 'methods';methods.mkdir()
    shutil.copy(FIXTURES / 'proof/methods/contract-fixture-1.yaml', methods)
    method = method_version(c_lowering.identity())
    (methods / 'wp-tracer-fixture.yaml').write_text(yaml.safe_dump(method,sort_keys=False))
    marker = tmp_path / 'must-not-launch-wp'
    frama = tmp_path / 'frama.py'
    frama.write_text('import sys\nfrom pathlib import Path\n'
        'if "-version" in sys.argv: print("33.0");sys.exit(0)\n'
        'if any(a.startswith(("-wp", "-rte", "-load")) for a in sys.argv[1:]):\n'
        f' Path({str(marker)!r}).write_text("unexpected WP invocation");sys.exit(2)\n')
    names = {'alt-ergo':'Alt-Ergo','z3':'Z3','cvc5':'CVC5'}
    why3 = tmp_path / 'why3.conf'
    why3.write_text(''.join(f'[prover]\nname = "{names[row["tool"]]}"\n'
                           f'version = "{row["version"]}"\ncommand = "/usr/bin/false"\n'
                           for row in method['lineup'] if row['tool'] in names))
    done = run_swdb('prove','--records',records.path,'--summary',entry['id'],'--adapter','wp',
                   '--define','WP24_OUTSIDE_CASE','--runs-dir',tmp_path/'runs','--format','json',
                   env={'SWDB_FRAMA_C':f'{sys.executable} {frama}','WHY3CONFIG':str(why3),
                        'SWDB_VERIFIER_LOCK':str(tmp_path/'standin-only.lock')})
    assert done.returncode == 0, done.stdout+done.stderr
    payload = json.loads(done.stdout)
    record = yaml.safe_load((records.path/payload['path']).read_text())
    assert record['verdict']=='not_proven' and record['failure_class']=='unsupported_construct',record
    assert record['job']['adapter']=='wp' and record['goals']==[]
    reports={row['name']:row for row in record['evidence'].get('reports',[])}
    assert 'wp_input' not in reports and not marker.exists()
    reason=json.loads(open(reports['handler']['path']).read())['why']
    assert construct in reason and f'outside.cc line {OUTSIDE_LOCATIONS[construct]+1})' in reason,reason
    assert 'Traceback' not in done.stderr
