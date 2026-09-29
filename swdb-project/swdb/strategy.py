"""Optimization strategies (ADR 0004): identity, legality, and the rules a schema cannot
express. Pure functions over plain dicts, shared by the validator and the queries.

Legality of an access-pattern strategy for one pattern:
- `illegal` when a required address shape is absent, the pattern's update kind is not one
  the strategy allows, an effect's step is missing or has
  another shape than the effect expects, or a required semantic value is known and differs;
- otherwise `undetermined` when a required semantic value has basis unknown (named in
  `unknown_fields`); otherwise `legal`.
Unknown is never false. The strategy's `unchecked` prose comes back as `check_by_hand` with
every outcome, and its reported benefit is shown next to the outcome, never used to filter.
"""

SEMANTIC_FIELDS = ["duplicate_target_indices", "index_modified_during_loop", "loop_carried_dependencies",
                   "shared_target_between_threads", "atomic_updates_required", "ordering", "numerical_requirement"]
BOOLEAN_FIELDS = SEMANTIC_FIELDS[:5]
VOCAB_FIELDS = {"ordering": "orderings", "numerical_requirement": "numerical_requirements"}

SOURCE_KINDS = {"paper", "human_report", "vendor_reference"}   # a strategy cites the literature or a person
MACHINE_TERMS = {"l1d_bytes", "l2_bytes", "llc_bytes"}           # machine cache sizes a benefit may name

# which effect kinds make sense on which target
TARGET_EFFECTS = {
    "access_pattern": {"reshape", "add_pattern", "hint", "widen"},
    "loop": {"restructure_loop", "add_pattern"},
    "input": {"reorder"},
}

STEP_EFFECTS = {"reshape", "hint"}      # effects that name a step of the target pattern


def identity(strategy):
    """(target, effect set): what makes two strategies the same strategy. Parameter names and
    values are ignored, so a widen by 8 lanes and a widen by `lanes` are the same change."""
    items = []
    for effect in strategy.get("effect", []):
        fields = {k: v for k, v in effect.items() if k not in {"note", "lanes"}}
        items.append(tuple(sorted((k, _freeze(v)) for k, v in fields.items())))
    return strategy.get("target"), frozenset(items)


def _freeze(value):
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    return value


def _position(step, length):
    """The index of `step` in a chain of `length` steps, or None if it has no such step."""
    index = step if step >= 0 else length + step
    return index if 0 <= index < length else None


def pattern_outcome(strategy, pattern):
    """Legality of one access-pattern (or loop) strategy for one pattern.
    pattern: {"steps": [{"address_shape": ...}], "update_kind": ..., "semantics": {field: {"value", "basis"}}}."""
    shapes = [step["address_shape"] for step in pattern["steps"]]
    reasons, unknown = [], []
    pre = strategy["preconditions"]
    for shape in pre.get("requires_shapes", []):
        if shape not in shapes:
            reasons.append(f"no step has address shape {shape}")
    kinds = pre.get("requires_update_kinds") or []
    if kinds and pattern["update_kind"] not in kinds:
        reasons.append(f"update kind is {pattern['update_kind']}, needs {' or '.join(kinds)}")
    for effect in strategy["effect"]:
        if effect["kind"] not in STEP_EFFECTS:
            continue
        where = _position(effect["step"], len(shapes))
        if where is None:
            reasons.append(f"{effect['kind']} names step {effect['step']}, but the chain has {len(shapes)} step(s)")
        elif effect["kind"] == "reshape" and shapes[where] != effect["shape_before"]:
            reasons.append(f"reshape needs step {effect['step']} to be {effect['shape_before']}, but it is {shapes[where]}")
    for need in pre.get("requires_semantics", []):
        fact = pattern["semantics"].get(need["field"], {"value": None, "basis": "unknown"})
        if fact["basis"] == "unknown":
            unknown.append(need["field"])
        elif fact["value"] != need["value"]:
            reasons.append(f"{need['field']} is {_show(fact['value'])} ({fact['basis']}), needs {_show(need['value'])}")
    outcome = "illegal" if reasons else "undetermined" if unknown else "legal"
    return outcome, reasons, unknown


def _show(value):
    return {True: "true", False: "false", None: "null"}.get(value, value) if isinstance(value, (bool, type(None))) else value


def entry(strategy, outcome, reasons, unknown, extra_check=()):
    """One query result entry, the shape every `swdb strategies` form returns."""
    return {
        "strategy": strategy["id"],
        "outcome": outcome,
        "reasons": reasons if outcome == "illegal" else [],
        "unknown_fields": unknown if outcome == "undetermined" else [],
        "check_by_hand": list(extra_check) + list(strategy["preconditions"].get("unchecked", [])),
        "benefits_when": [{"condition": b["condition"], "terms": b["terms"], "basis": b["basis"], "source": b["source"]}
                          for b in strategy.get("benefits_when", [])],
    }


# --- validation rules ---------------------------------------------------------------

def problems(strategy, vocabs, others):
    """(field, reason) pairs for one strategy that already passed its schema.
    others: [(record path, strategy data)] of every other strategy, for the duplicate rule."""
    target = strategy["target"]
    params = [p["name"] for p in strategy["parameters"]]
    for i, name in enumerate(params):
        if name in params[:i]:
            yield f"parameters[{i}].name", f"duplicate parameter {name!r}"
    for i, effect in enumerate(strategy["effect"]):
        where = f"effect[{i}]"
        allowed = TARGET_EFFECTS.get(target, set())
        if effect["kind"] not in allowed:
            yield f"{where}.kind", f"a {effect['kind']} effect does not apply to target {target} " \
                                   f"(it takes {', '.join(sorted(allowed))})"
        if effect["kind"] == "reshape" and effect["shape_before"] == effect["shape_after"]:
            yield f"{where}.shape_after", "a reshape changes the address shape; shape_after equals shape_before"
        lanes = effect.get("lanes")
        if isinstance(lanes, str) and lanes not in params:
            yield f"{where}.lanes", f"{lanes!r} is not a parameter of this strategy"
        if effect["kind"] == "reorder" and effect.get("index_locality") is not None \
                and "index_locality" not in effect.get("properties", []):
            yield f"{where}.index_locality", "a reorder that states index_locality lists index_locality in properties"
    pre = strategy["preconditions"]
    if target == "input" and (pre["requires_shapes"] or pre["requires_semantics"] or pre.get("requires_update_kinds")):
        yield "preconditions", "an input strategy's preconditions are prose (unchecked); requires_shapes, " \
                               "requires_update_kinds, and requires_semantics apply to access patterns and loops"
    for i, need in enumerate(pre["requires_semantics"]):
        yield from _semantic(f"preconditions.requires_semantics[{i}]", need, vocabs)
    sources = {p["id"]: p["kind"] for p in strategy["provenance"]}
    if not any(kind in SOURCE_KINDS for kind in sources.values()):
        yield "provenance", f"a strategy cites at least one source: a provenance entry of kind {', '.join(sorted(SOURCE_KINDS))}"
    terms_ok = set(vocabs.get("metrics", [])) | set(vocabs.get("input_properties", [])) | MACHINE_TERMS
    for i, benefit in enumerate(strategy.get("benefits_when", [])):
        where = f"benefits_when[{i}]"
        if benefit["source"] not in sources:
            yield f"{where}.source", f"{benefit['source']!r} is not a provenance entry of this record"
        elif sources[benefit["source"]] not in SOURCE_KINDS:
            yield f"{where}.source", f"{benefit['source']!r} is a {sources[benefit['source']]} entry; a reported " \
                                     f"benefit cites a source ({', '.join(sorted(SOURCE_KINDS))})"
        for j, term in enumerate(benefit["terms"]):
            if term not in terms_ok:
                yield f"{where}.terms[{j}]", f"{term!r} is not a metric, an input property, or a machine cache size " \
                                             f"({', '.join(sorted(MACHINE_TERMS))})"
    mine = identity(strategy)
    for rel, other in others:
        if identity(other) == mine:
            yield "effect", f"duplicate strategy: {other['id']!r} ({rel}) has the same target and effect; " \
                            "link to it instead (parameters are not part of a strategy's identity)"


def _semantic(where, need, vocabs):
    field, value = need["field"], need["value"]
    if field not in SEMANTIC_FIELDS:
        yield f"{where}.field", f"{field!r} is not a semantic field; one of {', '.join(SEMANTIC_FIELDS)}"
    elif field in BOOLEAN_FIELDS and not isinstance(value, bool):
        yield f"{where}.value", f"{field} is true or false, not {value!r}"
    elif field in VOCAB_FIELDS and value not in vocabs.get(VOCAB_FIELDS[field], []):
        yield f"{where}.value", f"{value!r} is not in vocabulary {VOCAB_FIELDS[field]}"
