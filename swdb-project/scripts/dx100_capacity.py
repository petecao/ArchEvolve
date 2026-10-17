#!/usr/bin/env python3
"""Read-only NUMA capacity gate for the finite DX100 smoke. Updated: 2026-09-25."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

GIB_KIB = 1024 * 1024


def capacity(node_text, zones_text, global_text, node, page_size):
    if page_size <= 0 or page_size % 1024:
        raise ValueError('page size must be a positive whole number of KiB')
    values = {}
    for line in node_text.splitlines():
        match = re.fullmatch(r'Node\s+(\d+)\s+([^:]+):\s+(\d+)\s+kB', line.strip())
        if match and int(match[1]) == node:
            values[match[2]] = int(match[3])
    required = {'MemFree', 'Active(file)', 'Inactive(file)', 'Dirty', 'Writeback', 'SReclaimable'}
    if not required <= values.keys():
        raise ValueError('node memory fields are missing')
    available = re.search(r'^MemAvailable:\s+(\d+)\s+kB$', global_text, re.M)
    if not available:
        raise ValueError('global MemAvailable is missing')
    zones = []
    for block in re.split(r'(?=Node \d+, zone)', zones_text):
        header = re.match(r'Node (\d+), zone\s+(\S+)', block)
        if not header or int(header[1]) != node:
            continue
        row = {'name': header[2]}
        for key in ('low', 'high', 'managed'):
            match = re.search(r'^\s+' + key + r'\s+(\d+)\s*$', block, re.M)
            if not match:
                raise ValueError('zone reserve field is missing: ' + key)
            row[key] = int(match[1])
        protection = re.search(r'protection:\s*\(([0-9, ]+)\)', block)
        if not protection:
            raise ValueError('zone protection values are missing')
        row['protection'] = [int(value.strip()) for value in protection[1].split(',')]
        row['reserved_pages'] = min(row['managed'], row['high'] + max(row['protection']))
        zones.append(row)
    if not zones or not sum(row['managed'] for row in zones):
        raise ValueError('no managed zones identify the requested node')
    page_kib = page_size // 1024
    low_pages = sum(row['low'] for row in zones)
    reserve_pages = sum(row['reserved_pages'] for row in zones)
    file_pages = max(0, values['Active(file)'] + values['Inactive(file)'] - values['Dirty'] - values['Writeback']) // page_kib
    slab_pages = values['SReclaimable'] // page_kib
    # Linux performs its integer arithmetic in pages, including the half-cache
    # deductions. Convert only the final estimate back to KiB.
    before_discount = max(0, values['MemFree'] // page_kib - reserve_pages
                          + file_pages - min(file_pages // 2, low_pages)
                          + slab_pages - min(slab_pages // 2, low_pages)) * page_kib
    low, reserve = low_pages * page_kib, reserve_pages * page_kib
    file_lru, slab = file_pages * page_kib, slab_pages * page_kib
    estimate = max(0, before_discount - GIB_KIB)
    global_available = int(available[1])
    return {'node': node, 'page_size_bytes': page_size, 'node_fields_kib': values,
        'zones': zones, 'low_watermarks_kib': low, 'reserved_kib': reserve,
        'clean_file_lru_kib': file_lru, 'reclaimable_slab_kib': slab,
        'before_uncertainty_discount_kib': before_discount, 'uncertainty_discount_kib': GIB_KIB,
        'estimated_available_kib': estimate, 'global_available_kib': global_available,
        'required_node_kib': 52 * GIB_KIB, 'required_global_kib': 64 * GIB_KIB,
        'eligible': estimate >= 52 * GIB_KIB and global_available >= 64 * GIB_KIB,
        'definition': 'Linux v6.8 MemAvailable node analogue; subtract dirty/writeback; '
                      'exclude miscellaneous reclaimable memory; extra 1 GiB discount',
        'estimate_is_guarantee': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', type=int, choices=(0, 1), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    path = args.output.resolve()
    if not any(path.is_relative_to(base) for base in (
            Path('/data/yanruj/EvolveSWDB_runs'), Path('/data1/yanruj/EvolveSWDB_runs'))):
        raise SystemExit('capacity receipt must use authorized raw output storage')
    inputs = {key: Path(source).read_text() for key, source in {
        'node': f'/sys/devices/system/node/node{args.node}/meminfo',
        'zones': '/proc/zoneinfo', 'global': '/proc/meminfo',
        'vmstat': '/proc/vmstat', 'pressure': '/proc/pressure/memory'}.items()}
    result = capacity(inputs['node'], inputs['zones'], inputs['global'], args.node, os.sysconf('SC_PAGE_SIZE'))
    receipt = {'format': 'swdb.dx100.capacity.v1', 'observed': datetime.now(timezone.utc).isoformat(),
        'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'inputs': inputs, 'result': result, 'evidence_kind': 'execution'}
    with path.open('x') as stream:
        stream.write(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                      'result': result}, sort_keys=True))
    raise SystemExit(0 if result['eligible'] else 1)


if __name__ == '__main__':
    main()
