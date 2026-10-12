"""Synthetic library-call admission fixture; never measurement evidence. Created: 2026-10-12 ET."""
import copy

from swdb.cpu_library_call_calibration import (BATCH_EVENTS, COMMON, COUNT_CAP, COUNT_POINTS, EVENT_CAP, FLAGS,
    NATIVE_ABIS, PIPELINE, SERVICES, SOURCES, TIMED_CAP, GROUP)
from swdb.cpu_service_controls import SCOPE


def native_receipt():
    cells = [{'index': i, 'event_abi': abi} for i, abi in enumerate(NATIVE_ABIS)]
    points = []
    for n in COUNT_POINTS:
        for invoke in (True, False):
            points.append({'events': n, 'invoke': invoke, 'characterization_sha256': 'a' * 64,
                'other_uncovered_calls': {'_ZNSo3putEc': 3 * n, 'indirect-call': 6 * n},
                'cells': [{**c, 'executions': (c['index'] + 1) * n if invoke else 0, 'source_sites': [40 + c['index']]}
                          for c in cells]})
    proof = {'format': 'swdb.cpu-library-call-count-proof.v1', 'pipeline': copy.deepcopy(PIPELINE),
        'coefficients': 'synthetic', 'cells': cells, 'points': points, 'source_sha256': 'a' * 64,
        'count_driver_sha256': 'a' * 64, 'plugin_source_sha256': 'a' * 64, 'runtime_source_sha256': 'a' * 64}
    services = [{'id': service_id, 'unit': 'seconds/call', 'event_definition': definition,
        'scope': {'event_abi': abi, **copy.deepcopy(COMMON), **copy.deepcopy(extra)},
        'denominator': {'level': 'selected_source_normalized_event', 'basis': 'measured', 'proof': copy.deepcopy(proof)},
        'trials': [{'events': BATCH_EVENTS * 64, 'batch_events': BATCH_EVENTS, 'batches': 64, 'gross_seconds': .08,
            'driver_seconds': .06, 'order': 'service_first' if i % 2 == 0 else 'driver_first', 'checksum': 0} for i in range(7)]}
        for service_id, abi, definition, extra in SERVICES]
    return {'format': 'swdb.cpu-service-calibration.v1', 'evidence_kind': 'native', 'machine': 'mbit10', 'threads': 1,
        'context': {'system': 'Linux', 'architecture': 'x86_64', 'host': 'mbit10', 'dirty': False, 'commit': 'a' * 40,
            'lane': 'mbit10-evaluation-node0 (verified: synthetic test)', 'cpus': [0], 'instrumented_timer': False,
            'compiler_version': 'clang version 22.1.8', 'flags': list(FLAGS),
            'source_sha256': {name: 'a' * 64 for name in SOURCES}, 'compiler_sha256': 'a' * 64, 'binary_sha256': 'a' * 64,
            'machine_sha256': 'a' * 64,
            'loaded_libraries': {name: {'path': '/synthetic/' + name, 'sha256': 'a' * 64} for name in ('libc.so.6', 'libstdc++.so.6')},
            'control_environment_scope': copy.deepcopy(SCOPE), 'control_environment': {key: None for key in SCOPE['exact_variables']}},
        'settings': {'group': GROUP, 'repetitions': 7, 'min_trial_s': .05, 'max_wall_s': 900, 'event_cap': EVENT_CAP,
            'batch_events': BATCH_EVENTS, 'timed_data_cap_bytes': TIMED_CAP, 'count_build_cap_bytes': COUNT_CAP,
            'resident_payload_bytes': 0},
        'services': services}
