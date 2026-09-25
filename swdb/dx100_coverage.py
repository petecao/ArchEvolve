"""Observed MAA coverage inside an exact statistics tick interval. Updated: 2026-09-25."""

import re


def observe(log, values, tile_elements):
    try:
        end = int(values["finalTick"])
        start = end - int(values["simTicks"])
        if start < 0 or end <= start:
            raise ValueError()
    except (KeyError, ValueError):
        return {"state": "unobserved", "reason": "exact finalTick/simTicks interval is unavailable",
                "completed_trace_units": {}, "full_tiles": "unobserved", "tail_tiles": "unobserved",
                "competing_parent_updates": "unobserved"}
    units, tile_sizes, current, blocks, stores, collisions = {}, {}, {}, {}, {}, {}
    parent_storage = None
    truncated = False
    with log.open(errors="replace") as stream:
        for number, line in enumerate(stream, 1):
            storage = re.fullmatch(r"SWDB_BFS_PARENT_STORAGE address=([a-f0-9]+) count=(\d+) element_bytes=4\s*", line)
            if storage:
                parent_storage = {"virtual_address": int(storage[1], 16), "count": int(storage[2]), "line": number}
            match = re.match(r"\s*(\d+):", line)
            if not match or not start <= int(match[1]) <= end:
                continue
            tick = int(match[1])
            finished = re.search(r"\b([SIAR])\[\d+\] End \[", line)
            if finished:
                units[finished[1]] = units.get(finished[1], 0) + 1
            size = re.search(r"\bR\[\d+\] executeInstruction: .*tile size: (\d+)", line)
            if size:
                n = int(size[1]); tile_sizes[n] = tile_sizes.get(n, 0) + 1
            issued = re.search(r"\bI\[(\d+)\] Start \[(.*)", line)
            if issued:
                instruction = issued[2]
                base = re.search(r"baseAddr\(0x([a-f0-9]+)\)", instruction)
                current[int(issued[1])] = (int(base[1], 16) if base and "opcode(INDIR_ST_VECTOR)" in instruction
                    and "datatype(INT32)" in instruction else None)
            received = re.search(r"\bI\[(\d+)\] \w+: \d+ entries received for addr\(0x([a-f0-9]+)\)", line)
            if received:
                blocks[int(received[1])] = int(received[2], 16)
            stored = re.search(r"\bI\[(\d+)\] \w+: new_data\[(\d+)\] = SPD\[\d+\]\[\d+\] = \d+/(-?\d+)/", line)
            if stored:
                unit, word, value = map(int, stored.groups())
                base = current.get(unit)
                if base is None or unit not in blocks:
                    continue
                address = blocks[unit] + 4 * word
                key = (base, address)
                if key not in stores and len(stores) >= 500000:
                    truncated = True
                    continue
                previous = stores.get(key)
                if previous is not None and previous != value:
                    record = collisions.setdefault(base, {"count": 0, "samples": []})
                    record["count"] += 1
                    if len(record["samples"]) < 8:
                        record["samples"].append({"physical_word_address": address, "prior_value": previous,
                                                  "new_value": value, "tick": tick, "line": number})
                stores[key] = value
    parent_collisions = collisions.get(parent_storage["virtual_address"], {}) if parent_storage else {}
    full = tile_sizes.get(tile_elements, 0)
    tail = sum(count for size, count in tile_sizes.items() if 0 < size < tile_elements)
    return {"state": "observed", "tick_interval": [start, end], "completed_trace_units": units,
        "range_output_tile_sizes": {str(size): count for size, count in tile_sizes.items()},
        "full_tiles": {"state": "observed" if full else "unobserved", "count": full, "capacity": tile_elements},
        "tail_tiles": {"state": "observed" if tail else "unobserved", "count": tail, "capacity": tile_elements},
        "competing_parent_updates": {"state": "observed" if parent_collisions.get("count", 0) else "unobserved",
            "count": parent_collisions.get("count", 0), "samples": parent_collisions.get("samples", []),
            "parent_storage": parent_storage, "target_tracking_truncated": truncated,
            "definition": "Different signed32 vector-store values observed at the same physical word, from instructions whose virtual base is the returned parent array."},
        "limits": "Positive counts prove these finite observed cases only. Graph topology is not substituted for executed updates; traces outside the selected ROI are excluded."}
