"""Write the two source-specific native protocol selections.

Created: 2026-09-27 ET (Stream B). Data only: it copies the reviewed a2 readback
selection (unchanged one-thread study identities) and adds the source packages,
the fixed repeatability mapping, and the explicit R7 native-only size scope.
No measurement, reader, or publication runs here.
"""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[2]
RUNTIME = '/data1/yanruj/EvolveSWDB_native_routes_runtime_20260927_b1'
REPEATABILITY_DRIVER = {
    'path': '/data/yanruj/EvolveSWDB_runs/bfs-native-repeatability-20260926/'
            'bfs-native-repeatability-20260926-a1.driver/driver.json',
    'sha256': '26ea5d69db8a7b06f48e35876fa2308aa849a654c0cab351c6f70ae4777f4583'}


def main():
    calibration = json.loads((BASE/'requests/native-readback-20260926-a2.json').read_text())['spec']
    calibration = calibration['one_thread_calibration']
    plan_sha = hashlib.sha256((BASE/'resume-plan-20260927.md').read_bytes()).hexdigest()
    cells = json.loads((BASE/'requests/native-repeatability-20260926-a1.json').read_text())['cells']
    mapping = {cell['first_evaluation']: cell['id'] for cell in cells}
    packages = calibration['packages']
    routes = (('dx100-scalar', 'bfs-native-one-thread-dx100-scalar-20260927', [packages[0], packages[2]]),
              ('upstream-do', 'bfs-native-one-thread-upstream-do-20260927', [packages[1], packages[3]]))
    for name, protocol, selected in routes:
        spec = {'mode': 'native', 'id': protocol, 'version': 1, 'packages': selected,
            'maximum_relative_spread': 0.10,
            'spread_justification': 'Fixed prospective 0.10 ceiling from the one-thread plan; the completed '
                'one-thread study bfs-native-one-thread-pilot-20260926-a1 passed all 24 role/source spread '
                'groups and all four A/A controls under it. Not relaxed or tuned after observation.',
            'size_selection': {'scale': 18, 'accelerator_packages': [],
                'justification': 'Planned scale 18, used by every retained native pilot and the one-thread '
                                 'study; no smaller cost-qualified size is requested.'},
            'repeatability': {'evaluations': mapping, 'driver_receipt': REPEATABILITY_DRIVER},
            'accelerator_size_gate': {'state': 'native_only_not_required', 'decision': 'R7',
                'plan': {'path': RUNTIME+'/.scratch/bfs-rewrite-evaluation-2026-09-25/resume-plan-20260927.md',
                         'sha256': plan_sha},
                'justification': 'R7 (2026-09-27): T18/T19 need only the native protocol; controlled-simulator '
                                 'freezes for T16/T17/T20 keep the shared accelerator size gate.'},
            'one_thread_calibration': copy.deepcopy(calibration)}
        (HERE/f'{name}.selection.json').write_text(json.dumps(spec, indent=2)+'\n')


if __name__ == '__main__':
    main()
