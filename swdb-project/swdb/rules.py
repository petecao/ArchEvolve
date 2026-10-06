"""Validation rules a JSON Schema cannot express. Each rule has a passing and a failing
fixture in the tests. Rules run only on records that already passed their schema.

- deprecated_by names an existing record of the same kind;
- evidence_refs name provenance entries of the same record, and provenance IDs are unique;
- every formula uses only symbols from vocabulary input_properties;
- inside an implementation: loop and pattern IDs are unique, every loop/parent/pattern
  reference resolves, each chain of steps is well formed, an array named in several steps
  has the same type, size, and layout in each, and every code excerpt equals the source
  file at its recorded lines;
- a kernel's baseline implementation implements that kernel, and its pass_regex compiles;
- an implementation's sweep_count_regex compiles and has exactly one capture group, and its
  build flags enable every ISA extension its intrinsics need (swdb/isa.py);
- each strategy an implementation applies targets a loop or access pattern of the same
  record (or `input`) of the strategy's target type, with only declared parameters;
- a metric's unit is the unit its vocabulary entry gives;
- a profile's input defines every symbol its implementation's formulas use, and its
  bottleneck is not `measured` or `simulated` while the machine has no counters;
- a strategy's effects suit its target, its preconditions name real semantic fields and
  values, its benefits are reported and sourced, and no other strategy has the same target
  and effect (swdb/strategy.py);
- an intrinsic's ID is its C name without leading underscores, it cites a vendor reference
  with a URI, and a memory_kind of none goes with address_shape null.
"""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from swdb import formula, isa, strategy
from swdb.problems import Problem


@dataclass
class Context:
    store: object
    vocabs: object
    records_dir: Path
    home: Path
    valid: set   # paths of the records that passed their schema

    def passed(self, record_id, kind):
        """The data of a record of this kind that passed its schema, or None. Rules read other
        records only through this, so a malformed record is reported, never crashed on."""
        found = self.store.by_id.get(record_id)
        if found is None or found.kind != kind or found.rel not in self.valid:
            return None
        return found.data

    def application(self, data):
        """The application behind a kernel, implementation, or profile, following each link only
        through records that passed their schema (or None)."""
        if data is None:
            return None
        kind = data.get("kind")
        if kind == "application":
            return data
        if kind in {"kernel", "implementation"} and "application" in data:
            return self.passed(data["application"], "application")
        if kind == "implementation":
            return self.application(self.passed(data.get("kernel"), "kernel"))
        if kind == "profile":
            return self.application(self.passed(data.get("implementation"), "implementation"))
        return None


def check(record, ctx):
    data = record.data
    yield from _deprecated_by(record, ctx)
    yield from _provenance(record)
    kind = data["kind"]
    if kind in {"workload_characterization", "target_description", "estimate"}:
        from swdb.analytic import validate_record
        yield from validate_record(record, ctx)
    elif kind == "cpu_calibration":
        from swdb.cpu_calibration_records import validate_record
        yield from validate_record(record, ctx)
    elif kind == "kernel":
        yield from _kernel(record, ctx)
    elif kind == "implementation":
        yield from _implementation(record, ctx)
    elif kind == "profile":
        yield from _profile(record, ctx)
    elif kind == "intrinsic":
        yield from _intrinsic(record)
    elif kind == "strategy":
        yield from _strategy(record, ctx)
    elif kind == "review" and data.get("target_kind") == "candidate":
        from swdb.extensa_boundary import validate_review
        yield from validate_review(record, ctx)
    elif kind == "review" and data.get("target_kind") == "review":
        from swdb.library import validate_correction     # spec review C1 (2026-10-05 ET)
        yield from validate_correction(record, ctx)
    elif kind in {"certification", "review"}:
        from swdb.library import validate_record
        yield from validate_record(record, ctx)
    elif kind in {"workload", "protocol"}:
        from swdb.bfs_protocol import validate_record

        yield from validate_record(record, ctx)
    elif kind in {'retention', 'team_claim'}:
        from swdb.retention import validate_record
        yield from validate_record(record, ctx)
    elif kind == "region_profile":
        from swdb.callgrind_lines import validate_record
        yield from validate_record(record, ctx)
    elif kind == "profile_package":
        from swdb.cli import Failure
        from swdb.profile_package import verify

        try:
            verify(record.data)
        except (Failure, KeyError, TypeError, ValueError) as exc:
            yield Problem(record.rel, "identity_sha256", str(exc))


def _deprecated_by(record, ctx):
    target = record.data.get("deprecated_by")
    if target is None:
        return
    found = ctx.store.by_id.get(target)
    if found is None:
        yield Problem(record.rel, "deprecated_by", f"replacement {target!r} does not exist")
    elif found.kind != record.kind:
        yield Problem(record.rel, "deprecated_by", f"replacement {target!r} is a {found.kind}, not a {record.kind}")


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
    """Every evidence_refs list in the record, except under `extensions`, whose contents are
    experimental and free-form (rule 3 of the format)."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{where}.{key}" if where else key
            if key == "extensions" and not where:
                continue
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
    impl = ctx.passed(data["baseline_implementation"], "implementation")
    if impl is not None and impl.get("kernel") != data["id"]:
        yield Problem(record.rel, "baseline_implementation",
                      f"{data['baseline_implementation']!r} implements kernel {impl.get('kernel')!r}, not {data['id']!r}")
    yield from _regex(record.rel, "correctness_check.pass_regex", data["correctness_check"]["pass_regex"])
    code = data["correctness_check"]["verifier"]["code"]
    yield from _code_ref(record, ctx, code, "correctness_check.verifier.code", ctx.application(data))


def _regex(rel, where, text, groups=None):
    try:
        compiled = re.compile(text)
    except re.error as exc:
        yield Problem(rel, where, f"not a valid regular expression: {exc}")
        return
    if groups is not None and compiled.groups != groups:
        yield Problem(rel, where, f"needs exactly {groups} capture group(s), has {compiled.groups}")


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
            yield from _formula(rel, f"{where}.steps[{j}].array.element_count", step["array"].get("element_count"), ctx)
    yield from _same_arrays(rel, data)
    count_regex = data["run"].get("sweep_count_regex")
    if count_regex is not None:
        yield from _regex(rel, "run.sweep_count_regex", count_regex, groups=1)
    stream = data["run"].get("index_stream")
    if stream and stream["pattern"] not in patterns:
        yield Problem(rel, "run.index_stream.pattern", f"{stream['pattern']!r} is not an access pattern of this implementation")
    yield from _required_isa(record, ctx)
    yield from _applies(record, ctx, set(loops), set(patterns))
    app = ctx.application(data)
    yield from _implementation_context(record, ctx, app)
    for i, code in enumerate(data["code"]):
        yield from _code_ref(record, ctx, code, f"code[{i}]", app)
    for i, loop in enumerate(data["loops"]):
        if loop.get("code"):
            yield from _code_ref(record, ctx, loop["code"], f"loops[{i}].code", app)


def _implementation_context(record, ctx, app):
    data = record.data
    for field, target in (("origin.derived_from", data["origin"].get("derived_from")),
                          ("source_baseline", data.get("source_baseline")),
                          ("comparison_baseline", data.get("comparison_baseline"))):
        other = ctx.passed(target, "implementation")
        if other is None:
            continue
        if other["kernel"] != data["kernel"]:
            yield Problem(record.rel, field, f"{target!r} implements a different kernel")
        if field == "source_baseline":
            other_app = ctx.application(other)
            if app is not None and other_app is not None and app["id"] != other_app["id"]:
                yield Problem(record.rel, field, "source baseline belongs to a different application")
            if other["origin"]["kind"] not in {"application_source", "upstream_alternative"}:
                yield Problem(record.rel, field, "source baseline must be found in the application's source")
    evaluator = data.get("evaluator")
    if evaluator:
        yield from _regex(record.rel, "evaluator.pass_regex", evaluator["pass_regex"])
        yield from _code_ref(record, ctx, evaluator["verifier"]["code"], "evaluator.verifier.code", app)
    verification = data.get("verification", {})
    for i, reference in enumerate(verification.get("evidence", [])):
        profile = ctx.passed(reference, "profile")
        if profile is None:
            continue
        if profile["implementation"] != data["id"]:
            yield Problem(record.rel, f"verification.evidence[{i}]", "correctness evidence belongs to another implementation")
        if verification["status"] == "passed" and not any(
                p["part"] == "correctness" and p["outcome"] == "complete" for p in profile["parts"]):
            yield Problem(record.rel, f"verification.evidence[{i}]", "profile has no successful correctness check")


_NAMED = {"loop": "a loop", "access_pattern": "an access pattern"}


def _applies(record, ctx, loops, patterns):
    ids = {"loop": loops, "access_pattern": patterns}
    for i, applied in enumerate(record.data.get("applies", [])):
        where = f"applies[{i}]"
        chosen = ctx.passed(applied["strategy"], "strategy")
        if chosen is None:
            continue    # missing (the schema's x-ref reports it) or invalid (reported on its own file)
        wanted, target = chosen["target"], applied["target"]
        if wanted == "input":
            if target != "input":
                yield Problem(record.rel, f"{where}.target",
                              f"strategy {chosen['id']!r} targets input, so its target is 'input', not {target!r}")
        elif wanted not in ids:
            yield Problem(record.rel, f"{where}.target", f"strategy {chosen['id']!r} targets {wanted}, which "
                                                          "implementations cannot apply yet")
        elif target not in ids[wanted]:
            other = "loop" if wanted == "access_pattern" else "access_pattern"
            what = _NAMED[other] if target in ids[other] else f"not {_NAMED[wanted]} of this implementation"
            yield Problem(record.rel, f"{where}.target", f"strategy {chosen['id']!r} targets {wanted}, but {target!r} is {what}")
        declared = [p["name"] for p in chosen["parameters"]]
        for name in sorted(set(applied["parameters"]) - set(declared)):
            yield Problem(record.rel, f"{where}.parameters.{name}",
                          f"strategy {chosen['id']!r} declares no parameter {name!r}"
                          + (f" (it declares {', '.join(declared)})" if declared else " (it declares none)"))
        for name in declared:
            if name not in applied["parameters"]:
                yield Problem(record.rel, f"{where}.parameters",
                              f"strategy {chosen['id']!r} declares parameter {name!r}; give the value applied")


def _required_isa(record, ctx):
    """The build flags must be readable (no unknown -march), and must enable every extension
    the intrinsics need. -march=native is fine unless intrinsics need something: then the
    tool cannot tell whether the build enables it."""
    need = isa.required(record.data, ctx.passed)
    have, problems = isa.enabled(record.data["build"]["flags"], ctx.vocabs.get("isa_extensions", []),
                                 native_ok=not need)
    for reason in problems:
        yield Problem(record.rel, "build.flags", reason)
    if problems:
        return
    for ext in sorted(set(need) - have):
        yield Problem(record.rel, "build.flags",
                      f"does not enable {ext}, which {', '.join(need[ext])} needs; add {isa.flag_for(ext)} "
                      "or a -march value that includes it")


_ARRAY_FACTS = ("element_type", "element_bytes", "element_count", "layout")


def _same_arrays(rel, data):
    """An array named in several steps is one array: its type, size, and layout must agree
    everywhere (only its role may differ), so footprints and views do not depend on order."""
    first = {}
    for i, pattern in enumerate(data["access_patterns"]):
        for j, step in enumerate(pattern["steps"]):
            a = step["array"]
            facts = tuple(a.get(key) for key in _ARRAY_FACTS)
            seen = first.setdefault(a["name"], (facts, f"access_patterns[{i}].steps[{j}]"))
            if seen[0] != facts:
                diff = [key for key, x, y in zip(_ARRAY_FACTS, seen[0], facts) if x != y]
                yield Problem(rel, f"access_patterns[{i}].steps[{j}].array",
                              f"array {a['name']!r} differs from {seen[1]} in {', '.join(diff)}")


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
        return None, "its application record is missing or does not pass its schema"
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
    impl = ctx.passed(data["implementation"], "implementation")
    inp = ctx.passed(data["input"], "input")
    if impl and inp:
        defined = set(inp.get("properties", {}))
        for name in sorted(implementation_symbols(impl)):
            if name not in defined:
                yield Problem(rel, "input", f"input {inp['id']!r} does not define {name!r}, which the implementation's formulas use")
    machine = ctx.passed(data["machine"], "machine")
    if machine:
        available = machine.get("counters", {}).get("hardware_counters_available", {}).get("value")
        if available is not True and data["bottleneck"]["basis"] in {"measured", "simulated"}:
            yield Problem(rel, "bottleneck.basis",
                          f"machine {machine['id']!r} has no hardware counters, so a bottleneck can only be inferred, not {data['bottleneck']['basis']}")


def implementation_symbols(impl, loops=False):
    """Input symbols the element-count formulas use (and, with loops=True, the trip counts)."""
    names = set()
    texts = [loop.get("trip_count", {}).get("formula") for loop in impl.get("loops", [])] if loops else []
    for text in texts:
        if text:
            try:
                names.update(formula.symbols(text))
            except (formula.FormulaError, TypeError):
                pass
    for pattern in impl.get("access_patterns", []):
        for step in pattern.get("steps", []):
            text = step.get("array", {}).get("element_count")
            if text is None:
                continue
            try:
                names.update(formula.symbols(text))
            except (formula.FormulaError, TypeError):
                pass
    return names


# --- strategies ---------------------------------------------------------------------

def _strategy(record, ctx):
    others = [(r.rel, r.data) for r in ctx.store.of_kind("strategy") if r is not record and r.rel in ctx.valid]
    for where, reason in strategy.problems(record.data, ctx.vocabs, others):
        yield Problem(record.rel, where, reason)


# --- intrinsics ---------------------------------------------------------------------

def _intrinsic(record):
    data, rel = record.data, record.rel
    expected = data["name"].lstrip("_")
    if data["id"] != expected:
        yield Problem(rel, "id", f"an intrinsic's ID is its C name without leading underscores: {expected!r}")
    if "interface" not in data and not any(p["kind"] == "vendor_reference" and p.get("uri") for p in data["provenance"]):
        yield Problem(rel, "provenance", "an intrinsic cites a vendor reference: a provenance entry of kind "
                                         "vendor_reference with a uri")
    if "interface" in data and not any(p["kind"] == "source_code" for p in data["provenance"]):
        yield Problem(rel, "provenance", "accelerator intrinsic requires source_code provenance")
    if data["memory_kind"] == "none" and data["address_shape"] is not None:
        yield Problem(rel, "address_shape", "an intrinsic that touches no memory has address_shape null")
