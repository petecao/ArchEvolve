"""Generality guards: no kernel or target names in estimator code (story 60, D21).

Created: 2026-10-09 23:10 ET (ticket 14 code review F1, F6).

- The protected CPU counting adapter takes its timed-call line from the kernel plug-in.
- The estimator and mechanism modules and the counting runtime hold no kernel/target names.
- A PageRank-shaped characterization is estimated through the public command against a
  hand target (hand-computed seconds) and the canonical MAPLE description, with one
  unchanged estimator bundle. Numbers are fixtures, never evidence.
"""
import json
import re
from types import SimpleNamespace

import pytest
import yaml

from conftest import REPO, run_swdb
from swdb import artifacts, kernels
from swdb.analytic_cpu_binding import invocation_site
from swdb.cli import Failure
from swdb.estimate_protocol import estimator_identity

# Mechanism/estimator modules and the counting runtime. Adapter (binding) modules and
# Characterize.cpp are per-application seams and are reviewed separately.
ESTIMATOR_FILES = ('swdb/analytic_models.py', 'swdb/analytic_composition.py',
    'swdb/analytic_offload_models.py', 'swdb/analytic_sensitivity.py', 'swdb/analytic_count_reuse.py',
    'swdb/analytic_trial_scope.py', 'swdb/analytic_cpu_service.py', 'swdb/analytic_cpu_openmp.py',
    'swdb/estimate_protocol.py', 'swdb/llvm/CountingRuntime.cpp', 'swdb/llvm/LiveObjects.hpp',
    'swdb/llvm/LogicalCommands.hpp')
NAMES = re.compile(r'dx100|maple|mbit10|dobfs|brandes|gapbs|pagerank|pr_spmv|jacobi|sg32|bfs|xsbench|kron-g|\bbc\b', re.I)
# Reported, not hidden (2026-10-09 review): swdb/bfs_protocol.py keeps the generic
# immutable-record helpers (verify_immutable, _save_immutable, _now) under its historical
# BFS module name. estimate_protocol imports them; they have no BFS behavior.
ALLOWED_TOKENS = {'swdb/estimate_protocol.py': ('bfs_protocol',)}


def test_estimator_and_counting_runtime_hold_no_kernel_or_target_names():
    hits = []
    for relative in ESTIMATOR_FILES:
        for number, line in enumerate((REPO / relative).read_text().splitlines(), 1):
            for token in ALLOWED_TOKENS.get(relative, ()):
                line = line.replace(token, '')
            hits += [f'{relative}:{number}: {match.group()}' for match in NAMES.finditer(line)]
    assert not hits, 'kernel/target names in estimator code:\n' + '\n'.join(hits)


OLD_CPU_SITE = r'^        auto (parent|scores) = (DOBFS|Brandes)\([^\n]+;\s*$'


def test_cpu_counting_site_comes_from_each_kernel_plugin_with_unchanged_wrapper_span():
    drivers = [(kernels.BFS, kernels.BFS.native_driver), (kernels.BC, kernels.BC.native_driver),
               (kernels.BFS, REPO / 'tools/bfs_native/driver_scalable_v3.cc.in')]
    for plugin, driver in drivers:
        text = driver.read_text()
        match = invocation_site(text, plugin)
        # Same span as the pre-review literal, so derived counting wrappers keep their bytes.
        old = list(re.finditer(OLD_CPU_SITE, text, re.M))
        assert len(old) == 1 and (match.start(), match.end()) == (old[0].start(), old[0].end()), driver
        assert match.group().lstrip().startswith(plugin.driver_call_anchor + ' ' + plugin.native_function + '(')
    with pytest.raises(Failure, match='not exactly one declared driver site'):
        invocation_site(kernels.BC.native_driver.read_text(), kernels.BFS)


def test_a_new_kernel_plugin_needs_no_adapter_code():
    driver = ('int main() {\n    for (int trial = 0; trial < 1; ++trial) {\n'
              '        auto ranks = PageRankPull(graph, 20, 1e-4);\n        consume(ranks);\n    }\n}\n')
    plugin = SimpleNamespace(driver_call_anchor='auto ranks =', native_function='PageRankPull')
    assert invocation_site(driver, plugin).group() == '        auto ranks = PageRankPull(graph, 20, 1e-4);'
    with pytest.raises(Failure, match='not exactly one declared driver site'):
        invocation_site(driver, kernels.BFS)
    for broken in (SimpleNamespace(driver_call_anchor=None, native_function='PageRankPull'),
                   SimpleNamespace(driver_call_anchor='auto ranks =', native_function='Page Rank')):
        with pytest.raises(Failure, match='lacks its declared driver call anchor'):
            invocation_site(driver, broken)


PR_SUBJECT = 'gapbs-pr-jacobi-analytic-v1'
PR_INPUT = 'kron-g16-k16'
MAPLE = 'maple-isca2022.fpga-reference.t2'


def pagerank_counts(records, record_id, threads):
    """Hand-written pull-SpMV region: 4 contiguous reads and 4 neighbor-indexed reads."""
    from testkit.analytic import fixture_characterization
    data = fixture_characterization(records.path, subject_id=PR_SUBJECT, input_id=PR_INPUT, threads=threads)
    (records.path / 'workload_characterizations/fixture.counts.yaml').unlink()

    def count(value):
        return {'value': value, 'basis': 'reported', 'scope': 'per_call'}

    def access(site, shape, stride):
        return {'id': f'access.{site}', 'source_location': {'function': 'PageRankPull', 'line': 40 + site},
            'address_shape': {'value': shape, 'basis': 'code_reading'},
            'stride_bytes': {'value': stride, 'basis': 'unknown' if stride is None else 'code_reading'},
            'element_bytes': 4, 'update_kind': 'read', 'element_count': count(4), 'bytes_accessed': count(16),
            'observed_address_span_bytes': {'value': 16, 'basis': 'reported'},
            'address_expression': 'fixture', 'ir_lanes': 1}
    data['id'] = record_id
    data['regions'] = [{'id': PR_SUBJECT + '/edge', 'kind': 'loop', 'mapped': True,
        'source_location': {'function': 'PageRankPull', 'line': 44},
        'active_workers': {'value': threads, 'basis': 'reported'},
        'worker_context': {'team_sizes': [threads], 'measurement': 'Hand-written fixture.'},
        'operation_counts': {'integer': count(8), 'floating_point': count(4), 'branch': count(2), 'atomic': count(0)},
        'dynamic_counts': {'loop_iterations': count(4)}, 'footprint_bytes': {'value': 32, 'basis': 'reported'},
        'access_patterns': [access(1, 'stream', 4), access(2, 'ranged_indirect', None)],
        'accelerator_calls': [], 'address_stream_counts': {}}]
    data['identity_sha256'] = artifacts.digest({k: v for k, v in data.items() if k != 'identity_sha256'})
    records.write(f'workload_characterizations/{record_id}.yaml', data)
    return record_id


def freeze(records, tmp_path, name, target, threads):
    request = tmp_path / (name + '.freeze.yaml')
    request.write_text(yaml.safe_dump({'message_version': '1.0', 'id': name, 'version': 1, 'settings': {
        'mode': 'estimated', 'estimator_version': 'swdb.analytic.v1', 'target_description': str(target),
        'inputs': [PR_INPUT], 'roi': 'fixture.stream.v1', 'threads': threads}}, sort_keys=False))
    frozen = run_swdb('freeze-protocol', request, '--records', records.path, '--format', 'json')
    assert frozen.returncode == 0, frozen.stdout + frozen.stderr
    return json.loads(frozen.stdout)['id']


def estimate(records, characterization, target, protocol, record_id):
    result = run_swdb('estimate', '--records', records.path, '--characterization', characterization,
        '--target-description', target, '--protocol', protocol, '--id', record_id, '--format', 'json')
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_pagerank_estimates_run_through_the_unchanged_estimator(records, tmp_path):
    from testkit.analytic import target_description
    records.copy_closure(PR_SUBJECT, PR_INPUT, MAPLE)
    # Hand CPU target: compute 1e9 ops/s except 16 floating ops/s, 32 useful B/s streaming,
    # 0.1 s dependent latency with 2 requests in flight per worker.
    path = target_description(tmp_path)
    hand = yaml.safe_load(path.read_text())
    hand['id'] = 'fixture.pagerank.hand.target'
    hand['mechanisms'].append({'model': 'requests_in_flight_latency', 'parameters': {
        'dependent_latency_s': {'value': 0.1, 'basis': 'reported', 'source': 'Hand-computed test fixture.', 'unit': 'seconds/load'},
        'effective_requests_per_thread': {'value': 2.0, 'basis': 'reported', 'source': 'Hand-computed test fixture.', 'unit': 'requests/thread'}}})
    path.write_text(yaml.safe_dump(hand, sort_keys=False))

    cpu_counts = pagerank_counts(records, 'fixture.pagerank.t1.counts', 1)
    cpu = estimate(records, cpu_counts, path, freeze(records, tmp_path, 'fixture.pagerank.hand', path, 1),
                   'fixture.pagerank.hand.estimate')
    region = cpu['regions'][0]
    seconds = {bound['model']: bound['seconds'] for bound in region['bounds']}
    # compute max(8/1e9, 4/16, 2/1e9) = 0.25 s; stream 16 B / 32 B/s = 0.5 s;
    # indirect 4 requests * 0.1 s / (1 worker * 2) = 0.2 s. Region and total: 0.5 s.
    assert seconds == pytest.approx({'compute_throughput': 0.25, 'streaming_bandwidth': 0.5,
                                     'requests_in_flight_latency': 0.2})
    assert region['limiting_bound'] == 'streaming_bandwidth' and cpu['seconds'] == pytest.approx(0.5)

    maple_counts = pagerank_counts(records, 'fixture.pagerank.t2.counts', 2)
    maple = estimate(records, maple_counts, MAPLE, freeze(records, tmp_path, 'fixture.pagerank.maple', MAPLE, 2),
                     'fixture.pagerank.maple.estimate')
    assert maple['seconds'] is None and maple['ratio'] is None
    assert cpu['estimator_sha256'] == maple['estimator_sha256'] == estimator_identity()
    # MAPLE stays unknown by structure, not by a missing number: no count route yields
    # MAPLE logical requests and no cross-domain overlap is declared (ticket 25).
    bounds = {bound['model']: bound for bound in maple['regions'][0]['bounds']}
    assert 'address_stream_counts.requested_target_description' in bounds['fetch_queue']['missing']
    assert 'composition_contract.resource_domain_overlap' in bounds['domain_composition']['missing']
    structural = {row['missing']: row for row in maple['parameter_report']['structural_missing']}
    for missing in ('address_stream_counts.requested_target_description', 'composition_contract.resource_domain_overlap'):
        assert structural[missing]['parameter_fill_allowed'] is False
