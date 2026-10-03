"""Read-only disk and NUMA-node admission. Updated: 2026-10-03 ET."""
import datetime
import os
from pathlib import Path
import re

from swdb.cli import Failure

GIB = 1024 ** 3
RESERVE = 20 * GIB
PRIMARY = Path('/data1/yanruj/EvolveSWDB_runs')
SECONDARY = Path('/data/yanruj/EvolveSWDB_runs')


def _existing(path):
    while not path.exists() and path != path.parent:
        path = path.parent
    return path


def observe(runs_dir, lane):
    """Read only the selected disk and memory node; no global-memory substitute."""
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
        match = re.search(r'^Node \d+ MemFree:\s+(\d+) kB$', memory_path.read_text(), re.M)
        if not match:
            raise ValueError('node MemFree is unavailable')
        free_memory = int(match[1]) * 1024
    except (OSError, ValueError) as exc:
        raise Failure(f'cannot observe lane memory node {node}: {exc}') from None
    secondary_free = None
    if runs_dir.is_relative_to(PRIMARY) and SECONDARY.parent.is_dir():
        secondary = os.statvfs(_existing(SECONDARY))
        secondary_free = secondary.f_bavail * secondary.f_frsize
    return {'disk': str(mount), 'runs_folder': str(runs_dir),
            'free_bytes': disk.f_bavail * disk.f_frsize, 'memory_node': node,
            'free_memory_bytes': free_memory, 'secondary_free_bytes': secondary_free}


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
    if receipt['free_memory_bytes'] < memory_bytes:
        raise Failure(f"memory node {receipt['memory_node']} has {receipt['free_memory_bytes']} free bytes; requires {memory_bytes}")
    receipt.update(format='swdb.dispatch-preflight.v1', observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   planned_raw_bytes=storage_bytes, reserve_bytes=RESERVE, memory_budget_bytes=memory_bytes,
                   state='admitted')
    return receipt
