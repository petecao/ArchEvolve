"""Conservative DX100 ordinary-memory admission until ticket 28; created 2026-10-15 ET.

The current semantics instruments tile accesses only. Ordinary CPU writes can race a device load, and
the indirect store's full-line writeback also forbids assuming adjacent words remain unchanged. This
policy refuses those writes, hidden effects, and ordinary reads after device-store issue. Prefix reads
are admitted only with explicit acyclic, intraprocedural statement ordering from the clang AST.
"""

import hashlib
from pathlib import Path


STORE_CALLS = {"maa_indirect_store_vector", "maa_indirect_store_scalar",
               "maa_indirect_rmw_vector", "maa_indirect_rmw_scalar"}


def identity():
    return {"id": "dx100-cpu-memory-admission-1", "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def check(lowering, covered):
    """A refusal report or None. The effect inventory is generator-owned, never supplied by a candidate."""
    if not any(row.get("name") in covered for row in lowering.summaries):
        return None
    effects = getattr(lowering, "cpu_effects", None)
    refused = []
    if not isinstance(effects, dict) or not {"reads", "writes", "calls", "loop_functions"} <= effects.keys():
        refused.append({"kind": "missing_cpu_effect_inventory", "function": lowering.function})
    else:
        # Covered calls are the modeled device operations, not ordinary CPU effects. An opaque summary
        # or model with an unknown/write effect remains a refusal even when its wrapper has no direct store.
        writes = [dict(row) for row in effects["writes"] if row.get("callee") not in covered]
        refused.extend({**row, "reason": "ordinary CPU write or opaque effect requires memory-hazard probes"}
                       for row in writes)
        stores = [row for row in effects["calls"] if row.get("callee") in STORE_CALLS]
        reads = [row for row in effects["reads"] if row.get("callee") not in covered]
        if stores and reads:
            unit = lowering.function
            ordered = (unit not in effects["loop_functions"] and all(
                row.get("function") == unit and isinstance(row.get("statement"), int) for row in stores))
            first_store = min(row["statement"] for row in stores) if ordered else None
            for row in reads:
                if not ordered or row.get("function") != unit or not isinstance(row.get("statement"), int) or \
                        row["statement"] >= first_store:
                    refused.append({**row, "reason": "CPU read is not in an acyclic unit-only prefix before every "
                                    "device-store issue"})
    if not refused:
        return None
    return {"policy": identity(), "scope": "ordinary CPU/DX100 memory interference is outside semantics 0.1",
            "refused": refused}
