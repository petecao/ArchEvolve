"""Name the check a campaign candidate failed, for the rewrite provider (ticket 64).

Created: 2026-10-04 ET. Agent-decided under Yan-Ru's 2026-10-04 delegation; revisable.

Campaign a6 (ticket 57) told the provider only "Certification failed a named check": the strict
layer's `range_bounds` stopped every edit, and the provider never learned which check. This module
turns a certification record into check names and a short public message per check.

What reaches the provider:
- the check name, read from the strict layer's own `SWDB_STRICT_ASSERT:<name>` line in a failed
  matrix run, and the number of matrix runs it stopped;
- a fixed message per check, stating the interface precondition that check enforces (the same
  facts as Peter v1.1 section 3 and the library entries and usage notes the workspace already holds).

What never reaches it: run output, graphs, timings, the strict-layer source, ticket 20's patch or
the authors' accelerated code. The strict layer prints only the name, not operand values, so the
message states the precondition, not the observed value.
"""

import re
from collections import Counter

STRICT_PREFIX = "strict_layer_assertion"
_STRICT_LINE = re.compile(r"SWDB_STRICT_ASSERT:([a-z_]+)")

# Public precondition per check. Keep each short, factual and free of advice words
# (`swdb.extensa.search.Feedback` refuses "try", "should", "instead", "use the", ...).
STRICT_MESSAGES = {
    "range_bounds": "__dxc_range_loop needs bound tiles of equal size, stride register > 0 and "
                    "0 <= last_i register <= bound-tile size; each batch starts with last_i_reg = 0 "
                    "and last_j_reg = -1, set by __dxc_const_i32",
    "stream_bounds": "__dxc_stream_load needs register values 0 <= min <= max and stride > 0; min, max "
                     "and stride are register handles set by __dxc_const_i32",
    "register_handle": "an operand typed as a register is not a register handle from the thread's "
                       "dxc_context (a plain value was passed); values reach registers through __dxc_const_i32",
    "thread_ownership_register": "a register handle was used by a thread other than the one whose "
                                 "__dxc_thread_context allocated it, or a plain value was passed as a handle",
    "tile_handle": "a tile operand is not a tile handle from a dxc_context",
    "thread_ownership_tile": "a tile handle was used by a thread other than the one that allocated it",
    "tile_truncation": "an operation would produce more elements than one tile holds (TILE_SIZE)",
    "byte_offset_overflow": "an index times the element size reaches 2^32 bytes, or a row has a "
                            "negative or decreasing bound",
    "memory_region": "an access falls outside the arrays registered for the session",
    "memory_region_registration": "a memory region was registered with an empty or reversed range",
    "constant_uncovered_register": "__dxc_const_i32 overwrote a register that an operation not yet "
                                   "covered by __dxc_wait still reads",
    "read_before_wait": "a tile was read through __dxc_tile_pointer before __dxc_wait covered its producer",
    "session_required": "__dxc_thread_context ran before __dxc_session_begin",
    "session_begin_twice": "__dxc_session_begin ran twice in one session",
    "thread_count": "more OpenMP threads than DX100 cores (NUM_CORES)",
    "tile_budget": "more tiles allocated than the device has",
    "register_budget": "more registers allocated than the device has",
    "alu_division": "__dxc_alu_scalar divided by zero",
    "alu_opcode": "__dxc_alu_scalar got an unsupported operation",
    "store_size": "a store's source and index tiles differ in size",
}

OTHER_MESSAGES = {
    "frontier_size_equality": "the per-step frontier sizes differ from the trusted scalar oracle",
    "verifier": "the BFS verifier did not print PASS",
    "execution_witness": "the accelerated path did not run on a frontier at the threshold",
    "process_failure": "the program exited with an error and no named check",
    "timeout": "the run exceeded its time limit",
    "build failed": "the patched source did not compile",
}


def strict_names(run):
    """The strict-layer check names one run printed (stdout and stderr), in order, unique."""
    if not isinstance(run, dict):
        return []
    text = (run.get("stdout") or "") + (run.get("stderr") or "")
    return list(dict.fromkeys(_STRICT_LINE.findall(text)))


def matrix_checks(record):
    """Failed matrix cells as check names, with the strict layer's own check named.

    Returns (names in first-seen order, Counter of failed cells per name, total cells)."""
    counts, order = Counter(), []
    cells = record.get("matrix") or []
    for cell in cells:
        if cell.get("status") == "passed":
            continue
        reason = cell.get("reason") or "matrix"
        names = strict_names(cell.get("run")) if reason == STRICT_PREFIX else []
        for name in ([f"{STRICT_PREFIX}:{n}" for n in names] or [reason]):
            if name not in counts:
                order.append(name)
            counts[name] += 1
    return order, counts, len(cells)


def message(check):
    """The public message for one failed-check name, or None."""
    if check.startswith(STRICT_PREFIX + ":"):
        return STRICT_MESSAGES.get(check.split(":", 1)[1])
    return OTHER_MESSAGES.get(check)


def messages(failed_checks):
    """[{check, message}] for the checks that have one (the repair workspace's CERTIFICATION.json)."""
    out = []
    for check in dict.fromkeys(failed_checks or []):
        text = message(check)
        if text:
            out.append({"check": check, "message": text})
    return out


def explanation(failed_checks, limit=400):
    """Feedback explanation naming the failing checks (at most `limit` characters).

    Matrix checks come first with their messages; surviving negative controls are counted, since
    with a failing matrix they fail for the same cause."""
    checks = list(dict.fromkeys(failed_checks or []))
    controls = [c for c in checks if c.startswith("control:")]
    primary = [c for c in checks if not c.startswith("control:")]
    if not checks:
        return "Certification failed a named check."
    parts = []
    for check in primary:
        name = check.split(":", 1)[1] if check.startswith(STRICT_PREFIX + ":") else check
        text = message(check)
        parts.append(f"{name}: {text}" if text else name)
    head = "Certification failed." + (" " + "; ".join(parts) + "." if parts else "")
    # a7 (2026-10-04 ET): with a passing matrix the surviving controls are the whole failure,
    # so they are named (the same names the `failed_checks` field already carries).
    named = ", ".join(c.split(":", 1)[1] for c in controls)
    tail = (f" Negative controls not rejected ({len(controls)}): {named}." if controls and len(named) <= 200
            else f" Negative controls not rejected: {len(controls)}." if controls else "")
    if len(head) + len(tail) > limit:
        names = ", ".join(c.split(":", 1)[1] if c.startswith(STRICT_PREFIX + ":") else c for c in primary)
        first = parts[0] if parts else ""
        head = f"Certification failed: {names}. {first}"
        if len(head) + len(tail) > limit:
            head = head[:limit - len(tail) - 3].rstrip() + "..."
    return (head + tail).strip()
