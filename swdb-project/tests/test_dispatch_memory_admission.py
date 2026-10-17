"""Disposable NUMA accounting fixtures; no host allocation. 2026-10-03 ET."""
from pathlib import Path

import pytest

from swdb import dispatch_preflight as admission
from swdb.cli import Failure


def observed(**changes):
    stats = {key: 0 for key in admission.MEMORY_STATS}
    stats.update({'MemTotal': 64 * admission.GIB, 'MemFree': 30 * admission.GIB,
                  'Inactive(file)': 24 * admission.GIB, 'Mapped': 2 * admission.GIB})
    return {'disk': '/data1', 'free_bytes': 40 * admission.GIB, 'memory_node': 0,
            'free_memory_bytes': stats['MemFree'], 'node_memory_stats_bytes': stats,
            'node_zone_reserve_bytes': admission.GIB,
            'node_managed_memory_bytes': stats['MemTotal'], **changes}


def check(receipt, budget=36 * admission.GIB):
    return admission.check('/data1/yanruj/EvolveSWDB_runs', 'mbit10-evaluation-node0',
                           memory_bytes=budget, observation=receipt)


def test_inactive_file_admission_keeps_literal_free_and_exact_budget_boundary():
    result = check(observed())
    assert result['free_memory_bytes'] == 30 * admission.GIB
    assert result['estimated_memory_capacity_bytes'] == 37 * admission.GIB
    assert result['node_memory_reserve_bytes'] == 4 * admission.GIB
    assert result['memory_budget_bytes'] == 36 * admission.GIB
    assert result['memory_capacity_basis'] == 'node_memfree_plus_conservative_inactive_file.v1'
    assert check(observed(), 37 * admission.GIB)['state'] == 'admitted'
    with pytest.raises(Failure, match='requires'):
        check(observed(), 37 * admission.GIB + 1)


@pytest.mark.parametrize('key', ['Mapped', 'Shmem', 'Dirty', 'Writeback', 'Unevictable'])
def test_unavailable_file_pages_cannot_admit_the_run(key):
    receipt = observed()
    receipt['node_memory_stats_bytes'][key] += 16 * admission.GIB
    with pytest.raises(Failure, match='memory node 0'):
        check(receipt)


@pytest.mark.parametrize('missing', ['node_memory_stats_bytes', 'node_zone_reserve_bytes', 'node_managed_memory_bytes'])
def test_missing_proof_falls_back_and_cannot_trust_derived_capacity(missing):
    receipt = observed()
    receipt.pop(missing)
    receipt['estimated_memory_capacity_bytes'] = 200 * admission.GIB
    with pytest.raises(Failure, match='requires'):
        check(receipt)
    receipt['free_memory_bytes'] = 36 * admission.GIB
    receipt.pop('node_memory_stats_bytes', None)
    result = check(receipt)
    assert result['memory_capacity_basis'] == 'node_memfree_only'
    assert result['estimated_memory_capacity_bytes'] == 36 * admission.GIB


def test_global_other_node_active_and_slab_memory_never_supply_credit():
    receipt = observed()
    stats = receipt['node_memory_stats_bytes']
    stats.update({'MemFree': 23 * admission.GIB, 'Inactive(file)': 16 * admission.GIB,
                  'Active(file)': 30 * admission.GIB, 'SReclaimable': 30 * admission.GIB})
    receipt.update(free_memory_bytes=stats['MemFree'], MemAvailable=120 * admission.GIB,
                   other_node_free_memory_bytes=62 * admission.GIB)
    with pytest.raises(Failure, match='requires'):
        check(receipt)
    receipt['memory_node'] = 1
    with pytest.raises(Failure, match='differs'):
        check(receipt)


@pytest.mark.parametrize('key,value', [('Dirty', -1), ('Shmem', True),
                                     ('Inactive(file)', 65 * admission.GIB), ('MemFree', 31 * admission.GIB)])
def test_contradictory_or_invalid_accounting_refuses(key, value):
    receipt = observed()
    receipt['node_memory_stats_bytes'][key] = value
    with pytest.raises(Failure, match='invalid selected-node'):
        check(receipt)


def test_large_node_and_zone_reserves_cannot_be_ignored():
    with pytest.raises(Failure, match='requires'):
        check(observed(node_zone_reserve_bytes=12 * admission.GIB))
    receipt = observed()
    receipt['node_memory_stats_bytes']['MemTotal'] = 128 * admission.GIB
    receipt['node_managed_memory_bytes'] = 128 * admission.GIB
    with pytest.raises(Failure, match='requires'):
        check(receipt)


def zone(node, managed=1000, high=120, boost=40, protection=200):
    return (f'Node {node}, zone Normal\n  high {high}\n  boost {boost}\n'
            f'  managed {managed}\n  protection: (0, {protection})\n')


def test_zone_parser_counts_only_selected_node_and_caps_protection():
    text = zone(0) + zone(1, high=100000) + zone(0, managed=128, high=1, boost=0, protection=1000)
    assert admission._zone_reserve(text, 0, 4096) == {
        'node_zone_reserve_bytes': (360 + 128) * 4096,
        'node_managed_memory_bytes': (1000 + 128) * 4096}
    assert admission._zone_reserve(zone(1), 0, 4096) is None
    assert admission._zone_reserve(zone(0).replace('  boost 40\n', ''), 0, 4096) is None


def test_observe_reads_selected_node_stats_and_retains_fallback(tmp_path, monkeypatch):
    fixture = observed()
    text = ''.join(f'Node 0 {key}: {value // 1024} kB\n'
                   for key, value in fixture['node_memory_stats_bytes'].items())
    text += 'Node 1 MemFree: 999999999 kB\n'
    original = Path.read_text

    def read(path, *args, **kwargs):
        if str(path) == '/sys/devices/system/node/node0/meminfo':
            return text
        if str(path) == '/proc/zoneinfo':
            return zone(0, managed=64 * admission.GIB // admission.os.sysconf('SC_PAGE_SIZE')) + zone(1)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'read_text', read)
    result = admission.observe(tmp_path, 'mbit10-evaluation-node0')
    assert result['free_memory_bytes'] == 30 * admission.GIB
    assert result['node_memory_stats_bytes'] == fixture['node_memory_stats_bytes']
    assert result['node_zone_reserve_bytes'] > 0
    assert result['node_managed_memory_bytes'] == 64 * admission.GIB
    assert admission._node_stats(text.replace('Node 0 Dirty: 0 kB\n', ''), 0) is None
    assert admission._node_stats(text + 'Node 0 MemFree: 1 kB\n', 0) is None


def test_disjoint_counters_refuse_and_truncated_zone_totals_use_free_only():
    receipt = observed()
    receipt['node_memory_stats_bytes']['Inactive(file)'] = 64 * admission.GIB
    with pytest.raises(Failure, match='invalid selected-node'):
        check(receipt)
    receipt = observed(node_managed_memory_bytes=32 * admission.GIB)
    with pytest.raises(Failure, match='requires'):
        check(receipt)
    receipt['free_memory_bytes'] = 36 * admission.GIB
    receipt['node_memory_stats_bytes']['MemFree'] = 36 * admission.GIB
    result = check(receipt)
    assert result['memory_capacity_basis'] == 'node_memfree_only'


@pytest.mark.parametrize('missing', ['node_zone_reserve_bytes', 'node_managed_memory_bytes'])
def test_missing_zone_proof_does_not_hide_known_contradictory_counters(missing):
    receipt = observed()
    receipt[missing] = None
    receipt['node_memory_stats_bytes']['MemFree'] += admission.GIB
    with pytest.raises(Failure, match='invalid selected-node'):
        check(receipt, budget=30 * admission.GIB)


@pytest.mark.parametrize('change', [{'node_managed_memory_bytes': 65 * admission.GIB},
                                   {'node_zone_reserve_bytes': 65 * admission.GIB}])
def test_impossible_zone_accounting_refuses_even_with_enough_unused_memory(change):
    receipt = observed(**change)
    receipt['free_memory_bytes'] = 36 * admission.GIB
    receipt['node_memory_stats_bytes']['MemFree'] = 36 * admission.GIB
    with pytest.raises(Failure, match='invalid selected-node'):
        check(receipt)
