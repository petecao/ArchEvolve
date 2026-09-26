"""Final simulator-batch cleanup-budget readback. Created 2026-09-26 ET.

Call only after the independent terminal audit establishes no live owned writers.
This read-only check proves settled accounting consistency, not process absence,
execution correctness, complete batch admission, protocol qualification, or gain.
Embedded series/driver cleanup snapshots are intentionally nonfinal.
"""
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re

from scripts.bfs_owned_execution import FORMAT, SharedCleanup


def require(value, reason):
    if not value:
        raise ValueError(reason)


def timestamp(value):
    result = datetime.fromisoformat(value) if isinstance(value, str) else value
    require(isinstance(result, datetime) and result.utcoffset() is not None,
            'cleanup clock requires an aware timestamp')
    return result


def finite(value, name, *, positive=False):
    require(type(value) in (int, float) and math.isfinite(value)
            and (value > 0 if positive else value >= 0), name + ' is not a finite accounting number')
    return value


def identity(value):
    require(isinstance(value, dict) and all(type(value.get(key)) is int and value[key] > 0
                                          for key in ('pid', 'start_ticks')),
            'cleanup creator needs exact integer PID/start identity')
    return value['pid'], value['start_ticks']


def read_reference(ref, maximum):
    require(isinstance(ref, dict) and set(ref) == {'path', 'sha256'}
            and isinstance(ref['path'], str) and isinstance(ref['sha256'], str)
            and re.fullmatch(r'[a-f0-9]{64}', ref['sha256']), 'invalid pinned cleanup reference')
    path = Path(ref['path'])
    require(path.is_absolute() and path == path.resolve() and path.is_file() and not path.is_symlink(),
            'cleanup reference path is missing or unsafe')
    with path.open('rb') as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum and hashlib.sha256(raw).hexdigest() == ref['sha256'],
            'pinned cleanup reference changed or exceeds read bound')
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'duplicate cleanup JSON field')
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique)


def validate_cleanup_ledger(driver_ref, ledger_ref, *, expected_run_id, expected_outer_start,
                            expected_deadline, current):
    """Reopen final bytes after closure; caller supplies the original outer clock.

    The caller must separately validate terminal lane release and the full
    PID/start union. A terminal driver declaration alone is not that proof.
    The monotonic deadline is immutable header evidence from the execution host;
    it cannot be compared to this auditing process's monotonic clock.
    """
    begin, deadline, observed = map(timestamp, (expected_outer_start, expected_deadline, current))
    require(begin < deadline and observed >= begin, 'invalid original cleanup clock')
    driver = read_reference(driver_ref, 16 * 1024**2)
    require(driver.get('id') == expected_run_id and driver.get('state') in {'complete', 'failed'},
            'cleanup readback requires the exact terminal driver')
    require(timestamp(driver.get('outer_started')) == begin
            and timestamp(driver.get('outer_deadline')) == deadline,
            'cleanup outer clock differs from the prospective caller clock')
    started, finished = map(timestamp, (driver.get('started'), driver.get('finished')))
    require(begin <= started <= finished <= deadline and finished <= observed,
            'driver terminal timestamps escape the original clock')
    cleanup = driver.get('cleanup', {})
    require(cleanup.get('state') == 'all_owned_descendants_absent' and not cleanup.get('errors')
            and cleanup.get('subreaper') is True and cleanup.get('direct_reaped') is True
            and started <= timestamp(cleanup.get('checked_at')) <= finished,
            'driver lacks its completed bounded cleanup declaration')
    reference = driver.get('cleanup_budget', {})
    require(set(reference) == {'path', 'binding', 'budget_seconds'}
            and reference.get('path') == ledger_ref['path']
            and type(reference.get('budget_seconds')) is int and reference['budget_seconds'] == 30
            and cleanup.get('shared_budget') == ledger_ref['path'],
            'final ledger does not match the driver cleanup reference')
    # Read the final shared file after checking terminal driver metadata. Do not
    # substitute cleanup_accounting: it predates subsequent settlements.
    value = read_reference(ledger_ref, 256 * 1024)
    require(value.get('format') == FORMAT and type(value.get('budget_seconds')) is int
            and value['budget_seconds'] == 30 and SharedCleanup.binding_of(value) == reference['binding'],
            'cleanup immutable header or binding differs')
    require(timestamp(value.get('absolute_end')) == deadline
            and identity(value.get('creator')) == identity(driver.get('process_observations', {}).get('driver_identity')),
            'cleanup deadline or creator PID/start differs from the driver')
    finite(value.get('monotonic_end'), 'cleanup host monotonic deadline', positive=True)
    created = timestamp(value.get('created'))
    require(started <= created <= finished, 'cleanup ledger creation is outside the driver clock')
    require(value.get('reservations') == {}, 'final cleanup ledger has outstanding reservations')
    spent = finite(value.get('spent_seconds'), 'cleanup spent seconds')
    events = value.get('events')
    require(isinstance(events, list) and 0 < len(events) <= 2048, 'cleanup settled events are missing or exceed bound')
    charges = []
    last_finish = created
    for event in events:
        require(isinstance(event, dict) and type(event.get('pid')) is int and event['pid'] > 0
                and event.get('purpose') in {'grace', 'cleanup_or_finalization'}
                and event.get('exceeded_grant') is False, 'cleanup event is malformed or exceeded its grant')
        grant = finite(event.get('seconds'), 'cleanup event grant', positive=True)
        charged = finite(event.get('elapsed_seconds'), 'cleanup event charge', positive=True)
        require(charged <= grant <= 30, 'cleanup settled charge exceeds its grant or reserve')
        event_begin, event_end = map(timestamp, (event.get('started'), event.get('finished')))
        require(created <= event_begin <= event_end <= deadline and event_end <= observed
                and last_finish <= event_end, 'cleanup event escapes its original clock or settlement order')
        # Charge includes metadata work and a conservative final fsync tail;
        # finished-started is not an interchangeable duration measurement.
        last_finish = event_end
        charges.append(charged)
    require(spent <= 30 and math.isclose(spent, math.fsum(charges), rel_tol=0, abs_tol=1e-9),
            'cleanup spent total differs from settled events or exceeds 30 seconds')
    # A concurrently changed file cannot silently replace the admitted bytes.
    read_reference(ledger_ref, 256 * 1024)
    return {'state': 'settled_within_budget', 'driver': dict(driver_ref), 'ledger': dict(ledger_ref),
            'run_id': expected_run_id, 'driver_outcome': driver['state'], 'binding': reference['binding'],
            'creator': {'pid': value['creator']['pid'], 'start_ticks': value['creator']['start_ticks']},
            'budget_seconds': 30, 'spent_seconds': spent, 'settled_events': len(events),
            'observed_at': observed.isoformat(), 'embedded_cleanup_snapshots': 'nonfinal',
            'process_absence_verified': False, 'empirical_qualification': False}
