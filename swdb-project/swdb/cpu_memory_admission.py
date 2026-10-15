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


def summary_refusal(records, roots):
    """Refuse opaque dependencies whose transitive proof closure uses DX semantics.

    Current scalar summaries do not encode pending-command ownership across their boundary. A summary
    cannot hide the need for the ordinary-memory admission check merely by wrapping another summary
    or C model. Dependency selection separately checks that these records count for the current method.
    """
    from swdb.store import Store
    roots = list(roots)
    if not roots:
        return None
    store = Store(records) if records is not None else None
    seen, refused = set(), []

    def visit(record_id):
        if record_id in seen:
            return
        seen.add(record_id)
        data = store.get(record_id, "proof") if store else None
        if not data:
            refused.append({"kind": "missing_summary_dependency", "proof_record": record_id})
            return
        pins = data.get("pins") or {}
        semantics = pins.get("proof_semantics") or {}
        if isinstance(semantics, dict) and semantics.get("id"):
            refused.append({"kind": "opaque_semantics_summary", "proof_record": record_id,
                            "semantics": semantics,
                            "reason": "summary lacks a checked pending-command and memory-ownership boundary"})
        for group in ("summaries", "models"):
            dependencies = pins.get(group) or []
            if isinstance(dependencies, dict) and "not_applicable" in dependencies:
                continue
            if not isinstance(dependencies, list):
                refused.append({"kind": "unclassified_summary_dependencies", "proof_record": record_id})
                continue
            for dependency in dependencies:
                if not isinstance(dependency, dict) or not isinstance(dependency.get("proof_record"), str):
                    refused.append({"kind": "unclassified_summary_dependency", "proof_record": record_id})
                else:
                    visit(dependency["proof_record"])

    for record_id in roots:
        visit(record_id)
    return ({"policy": identity(), "scope": "opaque summary memory/pending-state composition needs ticket 28",
             "refused": refused} if refused else None)


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
