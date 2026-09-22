"""Validation rules a JSON Schema cannot express. Each rule has a passing and a failing
fixture in the tests. Rules run only on records that already passed their schema.

- deprecated_by names an existing record of the same kind;
- evidence_refs name provenance entries of the same record, and provenance IDs are unique;
- every formula uses only symbols from vocabulary input_properties;
- inside an implementation: loop and pattern IDs are unique, every loop/parent/pattern
  reference resolves, each chain of steps is well formed, and every code excerpt equals
  the source file at its recorded lines;
- a kernel's baseline implementation implements that kernel;
- a metric's unit is the unit its vocabulary entry gives;
- a profile's input defines every symbol its implementation's formulas use, and its
  bottleneck is not `measured` or `simulated` while the machine has no counters.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from swdb import formula
from swdb.problems import Problem


@dataclass
class Context:
    store: object
    vocabs: object
    records_dir: Path
    home: Path


def check(record, ctx):
    data = record.data
    yield from _deprecated_by(record, ctx)
    yield from _provenance(record)
    kind = data["kind"]
    if kind == "kernel":
        yield from _kernel(record, ctx)
    elif kind == "implementation":
        yield from _implementation(record, ctx)
    elif kind == "profile":
        yield from _profile(record, ctx)


def _deprecated_by(record, ctx):
    target = record.data.get("deprecated_by")
    if target is None:
        return
    found = ctx.store.get(target)
    if found is None:
        yield Problem(record.rel, "deprecated_by", f"replacement {target!r} does not exist")
    elif found["kind"] != record.kind:
        yield Problem(record.rel, "deprecated_by", f"replacement {target!r} is a {found['kind']}, not a {record.kind}")


def _provenance(record):
    ids = [entry["id"] for entry in record.data["provenance"]]
    for i, pid in enumerate(ids):
        if pid in ids[:i]:
            yield Problem(record.rel, f"provenance[{i}].id", f"duplicate provenance ID {pid!r}")
    known = set(ids)
    for where, ref in _evidence_refs(record.data, ""):
        if ref not in known:
            yield Problem(record.rel, where, f"evidence {ref!r} is not a provenance entry of this record")


def _evidence_refs(node, where):
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{where}.{key}" if where else key
            if key == "evidence_refs" and isinstance(value, list):
                for i, ref in enumerate(value):
                    yield f"{here}[{i}]", ref
            else:
                yield from _evidence_refs(value, here)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _evidence_refs(value, f"{where}[{i}]")


# --- kernels ------------------------------------------------------------------------

def _kernel(record, ctx):
    data = record.data
    impl = ctx.store.get(data["baseline_implementation"], "implementation")
    if impl is not None and impl.get("kernel") != data["id"]:
        yield Problem(record.rel, "baseline_implementation",
                      f"{data['baseline_implementation']!r} implements kernel {impl.get('kernel')!r}, not {data['id']!r}")
    code = data["correctness_check"]["verifier"]["code"]
    yield from _code_ref(record, ctx, code, "correctness_check.verifier.code", ctx.store.application_of(data))


# --- implementations ----------------------------------------------------------------

_NEEDS_INDEX = {"single_valued_indirect": "index", "ranged_indirect": "offsets", "data_dependent_merge": "offsets"}


def _implementation(record, ctx):
    data, rel = record.data, record.rel
    loops = [loop["id"] for loop in data["loops"]]
    yield from _unique(rel, "loops", loops)
    patterns = [p["id"] for p in data["access_patterns"]]
    yield from _unique(rel, "access_patterns", patterns)
    for i, loop in enumerate(data["loops"]):
        if loop.get("parent") is not None and loop["parent"] not in loops:
            yield Problem(rel, f"loops[{i}].parent", f"loop {loop['parent']!r} is not a loop of this implementation")
        yield from _formula(rel, f"loops[{i}].trip_count.formula", loop["trip_count"].get("formula"), ctx)
    for i, pattern in enumerate(data["access_patterns"]):
        where = f"access_patterns[{i}]"
        if pattern["loop"] not in loops:
            yield Problem(rel, f"{where}.loop", f"loop {pattern['loop']!r} is not a loop of this implementation")
        yield from _chain(rel, where, pattern["steps"])
        for j, step in enumerate(pattern["steps"]):
            yield from _formula(rel, f"{where}.steps[{j}].array.element_count", step["array"]["element_count"], ctx)
    stream = data["run"].get("index_stream")
    if stream and stream["pattern"] not in patterns:
        yield Problem(rel, "run.index_stream.pattern", f"{stream['pattern']!r} is not an access pattern of this implementation")
    app = ctx.store.application_of(data)
    for i, code in enumerate(data["code"]):
        yield from _code_ref(record, ctx, code, f"code[{i}]", app)
    for i, loop in enumerate(data["loops"]):
        if loop.get("code"):
            yield from _code_ref(record, ctx, loop["code"], f"loops[{i}].code", app)


def _unique(rel, where, ids):
    for i, value in enumerate(ids):
        if value in ids[:i]:
            yield Problem(rel, f"{where}[{i}].id", f"duplicate ID {value!r} in this record")


def _chain(rel, where, steps):
    """A chain starts at a stream or pointer chase, links through index/offsets arrays,
    and ends at its target array."""
    first = steps[0]["address_shape"]
    if first not in {"stream", "pointer_chase"}:
        yield Problem(rel, f"{where}.steps[0].address_shape",
                      f"a chain cannot start with {first}; it needs a previous step to supply its index")
    for j, step in enumerate(steps):
        role, last = step["array"]["role"], j == len(steps) - 1
        if last and role != "target":
            yield Problem(rel, f"{where}.steps[{j}].array.role", "the last step of a chain is its target array")
        if not last and role == "target":
            yield Problem(rel, f"{where}.steps[{j}].array.role", "only the last step of a chain is its target")
        need = _NEEDS_INDEX.get(step["address_shape"])
        if j > 0 and need and steps[j - 1]["array"]["role"] != need:
            yield Problem(rel, f"{where}.steps[{j}].address_shape",
                          f"a {step['address_shape']} step follows a step whose array role is {need}")


def _formula(rel, where, text, ctx):
    if text is None:
        return
    try:
        names = formula.symbols(text)
    except formula.FormulaError as exc:
        yield Problem(rel, where, str(exc))
        return
    allowed = set(ctx.vocabs.get("input_properties", []))
    for name in names:
        if name not in allowed:
            yield Problem(rel, where, f"symbol {name!r} is not in vocabulary input_properties")


def resolve_code(code, records_dir, home, app):
    """The absolute path of a code reference, or (None, reason)."""
    if code["root"] == "records":
        return Path(records_dir) / code["path"], None
    if app is None:
        return None, "its application record is missing"
    local = app["source"].get("local_path")
    if not local:
        return None, f"application {app['id']!r} has no local copy (source.local_path is null)"
    return Path(home) / local / code["path"], None


def _code_ref(record, ctx, code, where, app):
    path, reason = resolve_code(code, ctx.records_dir, ctx.home, app)
    if path is None:
        yield Problem(record.rel, where, f"cannot locate {code['path']!r}: {reason}")
        return
    if not path.is_file():
        yield Problem(record.rel, f"{where}.path", f"file {code['path']!r} does not exist (looked at {path})")
        return
    raw = path.read_bytes()
    if code.get("sha256") and hashlib.sha256(raw).hexdigest() != code["sha256"]:
        yield Problem(record.rel, f"{where}.sha256", f"{code['path']!r} does not match the recorded sha256")
    if code.get("excerpt") is not None:
        if not code.get("lines"):
            yield Problem(record.rel, f"{where}.lines", "an excerpt needs its line range")
            return
        first, last = code["lines"]
        lines = raw.decode("utf-8").splitlines()
        if first > last or last > len(lines):
            yield Problem(record.rel, f"{where}.lines", f"lines {first}-{last} are outside {code['path']!r} ({len(lines)} lines)")
            return
        actual = "\n".join(lines[first - 1:last])
        if actual.rstrip("\n") != code["excerpt"].rstrip("\n"):
            yield Problem(record.rel, f"{where}.excerpt", f"differs from {code['path']!r} lines {first}-{last}")


# --- profiles -----------------------------------------------------------------------

def _profile(record, ctx):
    data, rel = record.data, record.rel
    for i, metric in enumerate(data["metrics"]):
        entry = ctx.vocabs.entry("metrics", metric["name"])
        if entry and metric["unit"] != entry["unit"]:
            yield Problem(rel, f"metrics[{i}].unit", f"metric {metric['name']} is measured in {entry['unit']!r}, not {metric['unit']!r}")
    impl = ctx.store.get(data["implementation"], "implementation")
    inp = ctx.store.get(data["input"], "input")
    if impl and inp:
        defined = set(inp.get("properties", {}))
        for name in sorted(implementation_symbols(impl)):
            if name not in defined:
                yield Problem(rel, "input", f"input {inp['id']!r} does not define {name!r}, which the implementation's formulas use")
    machine = ctx.store.get(data["machine"], "machine")
    if machine:
        available = machine.get("counters", {}).get("hardware_counters_available", {}).get("value")
        if available is not True and data["bottleneck"]["basis"] in {"measured", "simulated"}:
            yield Problem(rel, "bottleneck.basis",
                          f"machine {machine['id']!r} has no hardware counters, so a bottleneck can only be inferred, not {data['bottleneck']['basis']}")


def implementation_symbols(impl):
    names = set()
    for pattern in impl.get("access_patterns", []):
        for step in pattern.get("steps", []):
            try:
                names.update(formula.symbols(step["array"]["element_count"]))
            except (formula.FormulaError, KeyError, TypeError):
                pass
    return names
