"""Independent arithmetic for the reviewed NUMA gate. Updated: 2026-09-25."""
from pathlib import Path
import runpy

import pytest

capacity = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/dx100_capacity.py'))['capacity']
GIB = 1024 * 1024


def node(free, file=0, slab=0, dirty=0):
    values = {'MemFree': free, 'Active(file)': file, 'Inactive(file)': 0,
              'Dirty': dirty, 'Writeback': 0, 'SReclaimable': slab}
    return '\n'.join(f'Node 1 {key}: {value} kB' for key, value in values.items())


def zone(low=0, high=0, protection=0):
    return f'Node 1, zone Normal\n low {low}\n high {high}\n managed 16511103\n protection: (0, 0, {protection})\n'


def test_recorded_node_values_produce_exact_discounted_estimate():
    result = capacity(node(32092188, 2289840, 21729008), zone(27839, 44350),
                      'MemAvailable: 84193092 kB', 1, 4096)
    assert result['reserved_kib'] == 177400
    assert result['low_watermarks_kib'] == 111356
    assert result['before_uncertainty_discount_kib'] == 55710924
    assert result['estimated_available_kib'] == 54662348
    assert result['eligible']


@pytest.mark.parametrize('free,global_available,eligible', [
    (53 * GIB, 64 * GIB, True), (53 * GIB - 1, 64 * GIB, False),
    (53 * GIB, 64 * GIB - 1, False)])
def test_exact_thresholds_never_round_up(free, global_available, eligible):
    assert capacity(node(free), zone(), f'MemAvailable: {global_available} kB', 1, 4096)['eligible'] is eligible


def test_protection_reserves_dirty_pages_and_half_cache_retention():
    result = capacity(node(60 * GIB, file=1000, slab=1000, dirty=200), zone(1000, 2000, 3000),
                      f'MemAvailable: {90 * GIB} kB', 1, 4096)
    assert result['reserved_kib'] == 20000
    assert result['estimated_available_kib'] == 59 * GIB - 20000 + 400 + 500
    with pytest.raises(ValueError, match='node memory fields'):
        capacity(node(60 * GIB), zone(), f'MemAvailable: {90 * GIB} kB', 0, 4096)
