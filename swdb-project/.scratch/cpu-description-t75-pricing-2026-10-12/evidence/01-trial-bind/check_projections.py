"""Targeted check of the two committed t75 OpenMP projections. Created: 2026-10-12 ET (cpud 01).

Applies the binder's own per-document admission rules (`swdb.cpu_openmp_binding.binding`,
lines 21-37) against the committed characterization records, without a bind or a whole-store
check, and lists each projected site's ABI profile match. Read-only. Run from `swdb-project/`:

    python3 .scratch/cpu-description-t75-pricing-2026-10-12/evidence/01-trial-bind/check_projections.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT))
from swdb import access, artifacts  # noqa: E402
from swdb.analytic_cpu_openmp import profile_indexes  # noqa: E402
from swdb.cpu_openmp_binding import _executed  # noqa: E402
from swdb.cpu_service_calibration import identity  # noqa: E402


def check(side):
    document = access.read_record(HERE / f'openmp-t75-{side}-projection-mbit10-20261012-a1.json')
    char = access.read_record(PROJECT / f'records/workload_characterizations/fga03.t75-{side}.uniform22.t1.characterization.a2.yaml')
    native = char.get('observation_contract', {}).get('native_runtime', {})
    receipt = document.get('receipt', {})
    sites = {(c['site'], c['name'], c['region']) for c in document['calls']}
    checks = {
        'format': document.get('format') == 'swdb.openmp-call-projection.v1',
        'identity_sha256': document.get('identity_sha256') == identity(document),
        'all_source_json_sites_cross_checked': document.get('all_source_json_sites_cross_checked') is True,
        'characterization_id_and_sha256': (document['characterization']['id'] == char['id']
                                           and document['characterization']['sha256'] == artifacts.digest(char)),
        'source_ir_sha256': document.get('source_ir_sha256') == char['static_analysis']['source_ir_sha256'],
        'executed_site_union': len(sites) == len(document['calls']) and sites == _executed(char),
        'compiler_sha256': receipt.get('compiler_sha256') == native.get('compiler_sha256'),
        'inputs_byte_identical_after_projection': receipt.get('inputs_byte_identical_after_projection') is True,
        'application_execution_false': receipt.get('application_execution') is False,
    }
    return {'characterization': char['id'], 'characterization_sha256': artifacts.digest(char),
            'identity_sha256': document['identity_sha256'], 'checks': checks, 'admitted': all(checks.values()),
            'sites': [{'site': c['site'], 'name': c['name'], 'llvm_function': c['llvm_function'],
                       'profile_indexes': profile_indexes(c)} for c in document['calls']]}


def main():
    result = {'format': 'cpud01.projection-check.v1', 'rules': 'swdb.cpu_openmp_binding.binding per-document admission',
              'sides': {side: check(side) for side in ('baseline', 'candidate')}}
    print(json.dumps(result, indent=1))
    return 0 if all(s['admitted'] for s in result['sides'].values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
