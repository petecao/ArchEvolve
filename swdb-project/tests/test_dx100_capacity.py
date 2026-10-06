"""Independent arithmetic for the reviewed NUMA gate. Updated: 2026-10-05 ET (shared tests/testkit); 2026-09-25."""
from pathlib import Path
import runpy

import pytest
from testkit.native_pilot import node, zone

capacity = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/dx100_capacity.py'))['capacity']
GIB = 1024 * 1024


def test_recorded_node_values_produce_exact_discounted_estimate():
    # The real preclaim receipt includes an empty Movable zone with a nonzero
    # low watermark; Linux includes it in the low-water sum, but not reserves.
    zones = zone(27839, 44350) + 'Node 1, zone Movable\n low 32\n high 32\n managed 0\n protection: (0, 0, 0)\n'
    result = capacity(node(31864936, 2597556, 21728952, dirty=2240), zones,
                      'MemAvailable: 112322496 kB', 1, 4096)
    assert result['reserved_kib'] == 177400
    assert result['low_watermarks_kib'] == 111484
    assert result['before_uncertainty_discount_kib'] == 55788836
    assert result['estimated_available_kib'] == 54740260
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
