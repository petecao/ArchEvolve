"""Finite read-offload checks and L3 companion admission. Updated: 2026-10-03 ET."""
from collections import Counter, deque
from pathlib import Path
import re

from swdb import artifacts
from swdb.cli import Failure

FRONTIER_TEXT = 'std::cout << "Starting TDStep: " << queue.size() << " elements" << std::endl;'
PROBE = re.compile(r'SWDB cas_fail_negative_hint=(\d+) l3_violations=(\d+)\n?')


def _need(value, message):
    if not value:
        raise Failure(message)


def oracle_counts(store, workload_id, source):
    from swdb.bfs_protocol import materialize_workload
    adjacency = materialize_workload(store, workload_id)['graph']['adjacency']
    _need(type(source) is int and 0 <= source < len(adjacency), 'frontier oracle source is outside graph')
    depth = [-1] * len(adjacency)
    depth[source] = 0
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in adjacency[u]:
            if depth[v] == -1:
                depth[v] = depth[u] + 1
                queue.append(v)
    counts = Counter(value for value in depth if value >= 0)
    return [counts[level] for level in range(max(counts) + 1)]


def observe_output(log, store, workload_id, source):
    frontiers, probes = [], []
    with Path(log).open(errors='strict') as stream:
        for number, line in enumerate(stream, 1):
            if line.startswith('Starting TDStep:'):
                found = re.fullmatch(r'Starting TDStep: (\d+) elements\n?', line)
                _need(found is not None, 'Starting TDStep frontier line differs from exact text')
                frontiers.append({'count': int(found[1]), 'line': number})
            if line.startswith('SWDB cas_fail_negative_hint='):
                found = PROBE.fullmatch(line)
                _need(found is not None, 'parent-gather probe line differs from exact text')
                probes.append({'cas_negative_hint_failures': int(found[1]), 'l3_violations': int(found[2]), 'line': number})
    expected = oracle_counts(store, workload_id, source)
    sizes = [item['count'] for item in frontiers]
    outcome = 'inconclusive'
    if len(probes) == 1:
        outcome = 'refuted' if probes[0]['l3_violations'] > 0 else 'observed' if probes[0]['cas_negative_hint_failures'] > 0 else 'inconclusive'
    output = {'path': str(log), 'sha256': artifacts.file_hash(log)}
    return {'frontier_sizes': {'state': 'passed' if sizes == expected else 'failed',
                'observed': sizes, 'oracle': expected, 'lines': frontiers, 'output': output,
                'basis': 'trusted original-adjacency BFS per-depth counts'},
            'parent_gather_race': {'outcome': outcome, 'probes': probes, 'output': output,
                'scope': 'finite diagnostic execution; observed means race exercised without an L3 violation'}}


def validate_frontier(evaluation, check, store):
    reference = check.get('frontier_sizes', {}).get('output', {})
    output = check.get('output', {})
    _need(reference == output and check['frontier_sizes'].get('state') == 'passed',
          'read-only candidate lacks exact-output frontier correctness')
    workload = evaluation.get('context', {}).get('workload', {}).get('id') or evaluation['request']['workload']['id']
    expected = oracle_counts(store, workload, check['source'])
    _need(check['frontier_sizes'].get('oracle') == check['frontier_sizes'].get('observed') == expected,
          'read-only frontier sizes differ from the trusted oracle')
    path = Path(output['path'])
    _need(path.is_file() and not path.is_symlink() and artifacts.file_hash(path) == output['sha256'],
          'frontier correctness output is unavailable or changed')
    actual = observe_output(path, store, workload, check['source'])['frontier_sizes']
    _need(actual == check['frontier_sizes'], 'frontier sizes differ from the exact stdout bytes')
    source = evaluation['context'].get('timed_source', {})
    source_path = Path(source.get('path', ''))
    _need(source_path.is_file() and not source_path.is_symlink()
          and artifacts.file_hash(source_path) == source.get('sha256')
          and sum(line.strip() == FRONTIER_TEXT for line in source_path.read_text().splitlines()) == 1, 'read-only frontier print statement is not exact-text checked in timed source')
    return actual


def validate_companion_settings(correctness, store):
    _need(correctness.get('verifier') == 'dx100.bfs.verifier.v2',
          'read-only companion protocol requires the v2 verifier')
    case = correctness.get('companion_cases', {}).get('parent_gather_race')
    _need(isinstance(case, dict) and set(case) == {'workload', 'source'}
          and store.get(case['workload'], 'workload') is not None and type(case['source']) is int and case['source'] >= 0,
          'read-only protocol requires parent_gather_race companion workload and source')
    workload = store.get(case['workload'], 'workload')
    _need(case['source'] in workload.get('definition', {}).get('sources', []),
          'parent-gather companion source is outside its registered workload')


def companion_acceptance(store, protocol, request, candidate_evaluation):
    from swdb.bfs_protocol import _check_verifier_identity
    correctness = protocol['settings']['correctness']
    if 'read_only_executed' not in correctness.get('required_accelerator_cases', {}).get('candidate', []):
        return None
    validate_companion_settings(correctness, store)
    case = correctness['companion_cases']['parent_gather_race']
    selected = request.get('companion_evaluations')
    _need(isinstance(selected, dict) and set(selected) == {'timed', 'diagnostic'},
          'comparison requires explicit timed and diagnostic parent-gather companion evaluations')
    rows = {}
    for role, rid in selected.items():
        evaluation = store.get(rid, 'evaluation')
        _need(evaluation is not None and evaluation.get('outcome', {}).get('state') == 'complete'
              and evaluation.get('correctness', {}).get('state') == 'passed'
              and evaluation.get('evidence_kind') == candidate_evaluation.get('evidence_kind')
              and evaluation.get('candidate') == candidate_evaluation.get('candidate'),
              'parent-gather companion differs from candidate tree/evidence or is incomplete')
        _check_verifier_identity(evaluation, store)
        context = evaluation['context']
        candidate = store.get(evaluation['candidate'], 'candidate')
        _need(candidate is not None and context.get('candidate_sha256') == candidate.get('artifact', {}).get('sha256')
              and candidate_evaluation['context'].get('candidate_sha256') == candidate.get('artifact', {}).get('sha256'),
              'parent-gather companion candidate artifact identity differs')
        _need(context.get('verifier') == 'dx100.bfs.verifier.v2'
              and context.get('workload', {}).get('id') == case['workload']
              and context.get('source') == case['source']
              and context.get('target') == candidate_evaluation['context'].get('target')
              and context.get('configuration') == candidate_evaluation['context'].get('configuration'),
              'parent-gather companion graph/source/target differs from frozen case')
        binding = context.get('protocol_binding', {})
        _need(binding.get('protocol') == protocol['id'] and binding.get('frozen_sha256') == protocol['identity_sha256'] and binding.get('companion_case') == 'parent_gather_race',
              'parent-gather companion is not bound to the frozen protocol')
        from swdb.bfs_protocol import _timestamp
        _need(_timestamp(binding.get('bound_at')) >= _timestamp(protocol['frozen_at']),
              'parent-gather companion predates protocol freeze')
        checks = evaluation['correctness']['checks']
        _need(len(checks) == 1 and checks[0].get('passed') is True, 'companion requires exactly one passed check')
        validate_frontier(evaluation, checks[0], store)
        flags = evaluation.get('build', {}).get('flags', [])
        if candidate_evaluation.get('component_evaluations'):
            primary_binaries = {store.get(item['evaluation'], 'evaluation')['build']['binary_sha256']
                                for item in candidate_evaluation['component_evaluations']}
        else:
            primary_binaries = {candidate_evaluation['build'].get('binary_sha256')}
        if role == 'timed':
            _need('-DSWDB_DXC_DIAGNOSTIC' not in flags and primary_binaries == {evaluation['build'].get('binary_sha256')},
                  'timed companion must use the exact uninstrumented timed candidate binary')
        else:
            _need('-DSWDB_DXC_DIAGNOSTIC' in flags, 'race companion must identify the labeled diagnostic build')
            expected_flags = candidate_evaluation.get('build', {}).get('flags')
            if expected_flags is not None:
                _need([flag for flag in flags if flag != '-DSWDB_DXC_DIAGNOSTIC'] == expected_flags,
                      'parent-gather diagnostic changes flags beyond its explicit probe define')
        rows[role] = {'evaluation': rid, 'sha256': artifacts.digest(evaluation), 'frontier_sizes': checks[0]['frontier_sizes']}
        if role == 'diagnostic':
            actual = observe_output(checks[0]['output']['path'], store, case['workload'], case['source'])['parent_gather_race']
            _need(actual == checks[0].get('parent_gather_race'), 'diagnostic race counters differ from exact stdout')
            rows[role]['parent_gather_race'] = actual
    outcome = rows['diagnostic']['parent_gather_race']['outcome']
    _need(outcome == 'observed', f'parent-gather companion L3 outcome is {outcome}; timed comparison is refused')
    return {'case': 'parent_gather_race', 'outcome': outcome, 'evaluations': rows}
