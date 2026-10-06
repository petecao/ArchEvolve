"""Read-only disk and NUMA-node admission. Updated: 2026-10-05 ET (run roots from `swdb.paths`)."""
import datetime
import os
from pathlib import Path
import re

from swdb import paths
from swdb.cli import Failure

GIB = 1024 ** 3
RESERVE = 20 * GIB
PRIMARY, SECONDARY = paths.RUN_ROOTS
MEMORY_RESERVE = 4 * GIB
MEMORY_STATS = ('MemTotal', 'MemFree', 'Inactive(file)', 'Mapped', 'Shmem',
                'Dirty', 'Writeback', 'Unevictable')


def _node_stats(text, node):
    """Missing optional accounting keeps the stricter MemFree-only admission."""
    stats = {}
    for key in MEMORY_STATS:
        matches = re.findall(r'^Node ' + str(node) + ' ' + re.escape(key) + r':\s+(\d+) kB$', text, re.M)
        if len(matches) != 1:
            return None
        stats[key] = int(matches[0]) * 1024
    return stats


def _zone_reserve(text, node, page_size):
    """Conservative selected-node high watermarks and low-zone protection."""
    zones = []
    pattern = r'^Node (\d+), zone\s+\w+\n(.*?)(?=^Node \d+, zone|\Z)'
    for match in re.finditer(pattern, text, re.M | re.S):
        if int(match[1]) != node:
            continue
        values = {}
        for key in ('managed', 'high', 'boost'):
            found = re.findall(r'^\s+' + key + r'\s+(\d+)\s*$', match[2], re.M)
            if len(found) != 1:
                return None
            values[key] = int(found[0])
        protection = re.findall(r'^\s+protection:\s+\(([\d, ]+)\)\s*$', match[2], re.M)
        if len(protection) != 1:
            return None
        values['protection'] = max(int(value.strip()) for value in protection[0].split(','))
        zones.append(values)
    if not zones:
        return None
    return {'node_zone_reserve_bytes': sum(
                min(row['managed'], row['high'] + row['boost'] + row['protection'])
                for row in zones) * page_size,
            'node_managed_memory_bytes': sum(row['managed'] for row in zones) * page_size}


def _memory_capacity(receipt):
    """An estimate for admission, distinct from MemFree and kernel MemAvailable.

    Credit only half of selected-node inactive file pages after exclusions;
    keep a node reserve and count no active cache, slab or other-node memory.
    Linux ordinary reclaim under the existing strict memory binding supplies
    these pages. No cache eviction or memory allocation is performed here.
    """
    free = receipt['free_memory_bytes']
    stats = receipt.get('node_memory_stats_bytes')
    zone_reserve = receipt.get('node_zone_reserve_bytes')
    managed = receipt.get('node_managed_memory_bytes')
    if any(value is not None and (type(value) is not int or value < 0)
           for value in (zone_reserve, managed)):
        raise Failure('invalid selected-node memory accounting')
    if zone_reserve is not None and managed is not None and zone_reserve > managed:
        raise Failure('invalid selected-node memory accounting')
    if stats is not None:
        if (not isinstance(stats, dict) or any(type(stats.get(key)) is not int or stats[key] < 0
                                              for key in MEMORY_STATS)
                or stats['MemFree'] != free or free > stats['MemTotal']
                or managed is not None and managed > stats['MemTotal']
                or free + stats['Inactive(file)'] > stats['MemTotal']
                or any(stats[key] > stats['MemTotal'] for key in MEMORY_STATS)):
            raise Failure('invalid selected-node memory accounting')
    if (stats is None or zone_reserve is None or managed is None
            or managed != stats['MemTotal']):
        return {'estimated_memory_capacity_bytes': free,
                'memory_capacity_basis': 'node_memfree_only'}
    excluded = sum(stats[key] for key in ('Mapped', 'Shmem', 'Dirty', 'Writeback', 'Unevictable'))
    credit = max(0, stats['Inactive(file)'] - excluded) // 2
    reserve = max(MEMORY_RESERVE, (stats['MemTotal'] + 15) // 16, zone_reserve)
    capacity = max(free, min(stats['MemTotal'], free + credit - reserve))
    return {'estimated_memory_capacity_bytes': capacity,
            'memory_capacity_basis': 'node_memfree_plus_conservative_inactive_file.v1',
            'inactive_file_credit_bytes': credit, 'node_memory_reserve_bytes': reserve}


def _existing(path):
    while not path.exists() and path != path.parent:
        path = path.parent
    return path


def observe(runs_dir, lane):
    """Read selected-node free and reclaimable accounting; no global substitute."""
    runs_dir = Path(runs_dir).resolve()
    match = re.match(r'mbit10-evaluation-node([01])(?:\s|$)', str(lane))
    if not match:
        raise Failure('dispatch preflight requires a verified mbit10 socket lane')
    node = int(match[1])
    existing = _existing(runs_dir)
    disk = os.statvfs(existing)
    mount = existing
    while mount.parent != mount and mount.parent.stat().st_dev == mount.stat().st_dev:
        mount = mount.parent
    memory_path = Path(f'/sys/devices/system/node/node{node}/meminfo')
    try:
        memory_text = memory_path.read_text()
        matches = re.findall(r'^Node ' + str(node) + r' MemFree:\s+(\d+) kB$', memory_text, re.M)
        if len(matches) != 1:
            raise ValueError('node MemFree is unavailable')
        free_memory = int(matches[0]) * 1024
    except (OSError, ValueError) as exc:
        raise Failure(f'cannot observe lane memory node {node}: {exc}') from None
    secondary_free = None
    if runs_dir.is_relative_to(PRIMARY) and SECONDARY.parent.is_dir():
        secondary = os.statvfs(_existing(SECONDARY))
        secondary_free = secondary.f_bavail * secondary.f_frsize
    stats = _node_stats(memory_text, node)
    try:
        zones = _zone_reserve(Path('/proc/zoneinfo').read_text(), node, os.sysconf('SC_PAGE_SIZE'))
    except (OSError, ValueError):
        zones = None
    return {'disk': str(mount), 'runs_folder': str(runs_dir),
            'free_bytes': disk.f_bavail * disk.f_frsize, 'memory_node': node,
            'free_memory_bytes': free_memory, 'secondary_free_bytes': secondary_free,
            'node_memory_stats_bytes': stats,
            **(zones or {'node_zone_reserve_bytes': None, 'node_managed_memory_bytes': None})}


def check(runs_dir, lane, *, storage_bytes=2 * GIB, memory_bytes=4 * GIB, observation=None):
    """Fixture observations use the same admission arithmetic as the real host."""
    if any(type(value) is not int or value < 0 for value in (storage_bytes, memory_bytes)):
        raise Failure('dispatch storage and memory budgets must be nonnegative integer bytes')
    receipt = dict(observation if observation is not None else observe(runs_dir, lane))
    selected = re.match(r'mbit10-evaluation-node([01])(?:\s|$)', str(lane))
    if not selected or receipt.get('memory_node') != int(selected[1]):
        raise Failure('preflight observation differs from the verified lane memory node')
    for key in ('free_bytes', 'free_memory_bytes'):
        if type(receipt.get(key)) is not int or receipt[key] < 0:
            raise Failure(f'dispatch observation lacks valid {key}')
    required = RESERVE + storage_bytes
    if receipt['free_bytes'] < required:
        alternate = receipt.get('secondary_free_bytes')
        hint = (f'; use the secondary run folder {SECONDARY} explicitly'
                if Path(runs_dir).resolve().is_relative_to(PRIMARY)
                and type(alternate) is int and alternate >= required else '')
        raise Failure(f"run disk {receipt.get('disk')} has {receipt['free_bytes']} free bytes; requires {required}{hint}")
    receipt.update(_memory_capacity(receipt))
    if receipt['estimated_memory_capacity_bytes'] < memory_bytes:
        raise Failure(f"memory node {receipt['memory_node']} has {receipt['free_memory_bytes']} free bytes "
                      f"and {receipt['estimated_memory_capacity_bytes']} estimated admission capacity bytes; requires {memory_bytes}")
    receipt.update(format='swdb.dispatch-preflight.v1', observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   planned_raw_bytes=storage_bytes, reserve_bytes=RESERVE, memory_budget_bytes=memory_bytes,
                   state='admitted')
    return receipt
