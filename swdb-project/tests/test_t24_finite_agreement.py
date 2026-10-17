"""Compiler-only finite C++/C agreement runner, created 2026-10-15 ET.

Seam: the committed prototype CLI and its retained, independently auditable files.
This suite starts no formal verifier and creates no proof record.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from swdb import c_lowering

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT/'.scratch/probata-proof-of-concept-2026-10-13/prototype/t24-finite-agreement.py'
pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason='Clang 22.1.8 required')


def invoke(output, *arguments):
    commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    return subprocess.run([sys.executable, str(RUNNER), '--expected-commit', commit,
                           '--output', str(output), *arguments], cwd=ROOT, capture_output=True, text=True,
                          timeout=180)


def test_full_original_template_tu_compares_defined_results_and_pins_the_harness(tmp_path):
    done = invoke(tmp_path/'agreement', '--groups', 'templates')
    assert done.returncode == 0, done.stdout+done.stderr
    report = json.loads((tmp_path/'agreement/agreement.json').read_text())
    assert report['complete'] and report['success']
    assert report['kind'] == 'finite_native_cpp_c_agreement'
    assert report['formal_verifier_launched'] is False
    assert [row['case'] for row in report['rows']] == ['safe','seeded']
    for row in report['rows']:
        assert row['comparison'] == 'agree_on_defined_inputs'
        assert row['defined_comparisons'] == 25
        assert row['precondition_excluded_runs'] == 24
        assert row['undefined_behavior_runs'] == 0
        assert row['outputs']['c']['defined_sha256'] == row['outputs']['cxx']['defined_sha256']
        assert row['contract']['sha256'] and row['harness']['sha256']
        assert row['source']['cxx']['sha256'] != row['source']['c']['sha256']
        assert row['domain']['sampled'] is False
    audited = subprocess.run([sys.executable,str(RUNNER),'--audit-report',
                              str(tmp_path/'agreement/agreement.json')],cwd=ROOT,capture_output=True,text=True)
    assert audited.returncode == 0,audited.stdout+audited.stderr


def test_a_c_only_lowering_error_stops_at_the_first_defined_witness(tmp_path):
    fault = tmp_path/'fault.json'
    fault.write_text(json.dumps({'replace':[['return (Ring_int_3_get(&r, 1) + ((int)Ring_long_2_get(&q, 0))) + ((int)twice_long(b));',
                                           'return 1 + (Ring_int_3_get(&r, 1) + ((int)Ring_long_2_get(&q, 0))) + ((int)twice_long(b));']]}))
    done = invoke(tmp_path/'mismatch','--groups','templates,dxc_summary','--cases','safe',
                  '--lowering-fault',str(fault))
    assert done.returncode == 1,done.stdout+done.stderr
    report = json.loads((tmp_path/'mismatch/agreement.json').read_text())
    assert not report['success'] and not report['complete']
    assert len(report['rows']) == 1
    row = report['rows'][0]
    assert row['comparison'] == 'c_lowering_disagreement'
    assert row['first_difference']['oracle'] == [-2,-2]
    assert 'result=-9 ' in row['first_difference']['c']
    assert 'result=-10 ' in row['first_difference']['cxx']
    assert report['formal_verifier_launched'] is False


def test_a_one_sided_sanitizer_failure_cannot_be_masked_into_agreement(tmp_path):
    fault = tmp_path/'undefined.json'
    fault.write_text(json.dumps({'replace':[['return (Ring_int_3_get(&r, 1) + ((int)Ring_long_2_get(&q, 0))) + ((int)twice_long(b));',
                                           'return *(volatile int *)0;']]}))
    done = invoke(tmp_path/'undefined','--groups','templates','--cases','safe','--lowering-fault',str(fault))
    assert done.returncode == 1,done.stdout+done.stderr
    report = json.loads((tmp_path/'undefined/agreement.json').read_text())
    row = report['rows'][0]
    assert row['comparison'] == 'one_sided_undefined_behavior'
    assert row['undefined_behavior_runs'] == 25
    assert row['defined_comparisons'] == 0
    assert row['outputs']['cxx']['sanitizer_indexes'] == []
    assert len(row['sanitizer_diagnostics']) == 25
    assert not report['success']


def test_a_retained_output_change_invalidates_the_report(tmp_path):
    done = invoke(tmp_path/'agreement','--groups','templates','--cases','safe')
    assert done.returncode == 0,done.stdout+done.stderr
    path = tmp_path/'agreement/agreement.json'
    report = json.loads(path.read_text())
    output = Path(report['rows'][0]['outputs']['c']['raw']['path'])
    output.write_text(output.read_text()+'invented output\n')
    audited = subprocess.run([sys.executable,str(RUNNER),'--audit-report',str(path)],
                             cwd=ROOT,capture_output=True,text=True)
    assert audited.returncode == 1
    assert 'artifact hash differs' in audited.stdout


def test_an_all_undefined_allocation_seed_is_explicitly_excluded_not_agreed(tmp_path):
    done = invoke(tmp_path/'allocation','--groups','new_array','--cases','seeded')
    assert done.returncode == 0,done.stdout+done.stderr
    report = json.loads((tmp_path/'allocation/agreement.json').read_text())
    row = report['rows'][0]
    assert row['comparison'] == 'excluded_undefined_only'
    assert row['defined_comparisons'] == 0
    assert row['undefined_behavior_runs'] == 500
    assert row['precondition_excluded_runs'] == 214
    assert row['sanitizer_diagnostics'] == []
    assert row['executed_runs_per_side'] == 214
    assert row['known_undefined_exclusions']['reasons'] == [
        'original seeded i<=n writes buf[n] outside new int[n]']
