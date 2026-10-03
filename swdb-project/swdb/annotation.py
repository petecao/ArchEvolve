"""Source-reading agent claims and independent statement-cost scoring.

Updated: 2026-10-03. Facts remain unchanged; every claim retains its provider
settings, prompt and input hashes. Simulated cache misses are never hardware
measurements, and annotation accuracy is never a performance result.
"""

import copy
import json
import math
import re
from pathlib import Path

from swdb import artifacts, callgrind_lines, paths, provider_roles, rewrite, writer
from swdb.cli import Failure, _require_valid

COST_RULE = "absolute difference between expected rank and simulated midrank exceeds 1"
FACT_BASES = {"measured", "simulated", "reported"}
CLASS_SCHEMA = {"type": "object", "additionalProperties": False,
    "required": ["pattern", "address_shapes", "update_kind"], "properties": {
        "pattern": {"type": "string", "minLength": 1},
        "address_shapes": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
        "update_kind": {"type": "string", "minLength": 1}}}
OUTPUT_SCHEMA = {"type": "object", "additionalProperties": False,
    "required": ["statements", "unresolved"], "properties": {
        "statements": {"type": "array", "minItems": 1, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["statement", "pattern_class", "index_provenance", "expected_cost_rank", "basis"],
            "properties": {"statement": {"type": "string", "minLength": 1},
                "pattern_class": {"type": "array", "minItems": 1, "items": CLASS_SCHEMA},
                "index_provenance": {"type": "array", "uniqueItems": True,
                                     "items": {"type": "string", "minLength": 1}},
                "expected_cost_rank": {"type": "integer", "minimum": 1},
                "basis": {"enum": ["code_reading", "inferred"]}}}},
        "unresolved": {"type": "array", "items": {"type": "string"}}}}
PROFILING = provider_roles.Role("profiling", OUTPUT_SCHEMA)
provider_roles.ROLES["profiling"] = PROFILING


def statements(implementation):
    rows = implementation.get("extensions", {}).get("statements", {}).get("annotations", [])
    if not isinstance(rows, list) or not rows:
        raise Failure("implementation has no statement annotations")
    ids = [r.get("id") for r in rows if isinstance(r, dict)]
    if len(ids) != len(rows) or any(not isinstance(v, str) or not v for v in ids) or len(set(ids)) != len(ids):
        raise Failure("statement annotations need unique IDs")
    return rows


def _source_text(source, path):
    root = artifacts.verify(source["artifact"])
    relative = artifacts.relative_path(path)
    file = root / relative
    if not file.is_file() or file.is_symlink():
        raise Failure("statement source is absent from source snapshot: " + path)
    return file.read_text(), artifacts.file_hash(file)


def mapped_statements(implementation, source):
    """Map pinned original statements through a scalar-only source derivation.

    Removed ranges give the first projected location; exact statement bytes
    disambiguate derivations that also inserted markers or removed main's
    accelerated selection. A changed or ambiguous statement refuses mapping.
    """
    derivation = source.get("context", {}).get("source_derivation", {})
    removed = derivation.get("removed_pinned_line_ranges", [])
    if any(not isinstance(r, list) or len(r) != 2 or any(type(v) is not int or v < 1 for v in r)
           or r[1] < r[0] for r in removed):
        raise Failure("source derivation has invalid removed line ranges")
    removed = sorted(removed)
    if any(b[0] <= a[1] for a, b in zip(removed, removed[1:])):
        raise Failure("source derivation removed line ranges overlap")
    result, files = [], {}
    for statement in statements(implementation):
        original = statement.get("source", {})
        path, lines = original.get("path"), original.get("lines")
        if (not isinstance(path, str) or not isinstance(lines, list) or len(lines) != 2
                or any(type(v) is not int or v < 1 for v in lines) or lines[0] > lines[1]
                or not isinstance(statement.get("code"), str)):
            raise Failure("statement source requires a path, line range and code")
        if path not in files:
            files[path] = _source_text(source, path)
        text, digest = files[path]
        source_lines = text.splitlines()
        if any(not (lines[1] < start or lines[0] > end) for start, end in removed):
            raise Failure("statement was removed by scalar-only source derivation: " + statement["id"])
        offset = sum(end-start+1 for start, end in removed if end < lines[0])
        projected = [v-offset for v in lines]
        code = statement["code"].strip()
        matched = projected
        method = "identity" if not removed else "removed_pinned_line_ranges"
        if "\n".join(source_lines[max(0, projected[0]-1):projected[1]]).strip() != code:
            if not derivation:
                raise Failure("statement bytes differ from the pinned source line range: " + statement["id"])
            width = len(code.splitlines())
            candidates = [i+1 for i in range(len(source_lines)-width+1)
                          if "\n".join(source_lines[i:i+width]).strip() == code]
            if len(candidates) != 1:
                raise Failure("source derivation cannot uniquely map statement: " + statement["id"])
            matched = [candidates[0], candidates[0]+width-1]
            method = "source_derivation_unique_statement_bytes"
        result.append({"id": statement["id"], "path": path, "lines": matched,
            "source_sha256": digest, "source_snapshot": source["id"],
            "source_artifact_sha256": source["artifact"]["sha256"], "original_source": copy.deepcopy(original),
            "source_derivation_sha256": artifacts.digest(derivation), "mapping_method": method,
            "projected_removed_ranges_lines": projected, "code": statement["code"],
            "access_pattern_steps": copy.deepcopy(statement.get("access_pattern_steps", [])),
            "depends_on": copy.deepcopy(statement.get("depends_on", []))})
    return result


def _pattern_class(pattern):
    return {"pattern": pattern["id"], "address_shapes": [s["address_shape"] for s in pattern["steps"]],
            "update_kind": pattern["update_kind"]}


def workspace_input(implementation, source, profiles=()):
    mapped = mapped_statements(implementation, source)
    # Only the declared function's exact fragment is visible. The snapshot's
    # verifier, main, other candidates, graph inputs and authors' code stay out.
    function = implementation["extensions"]["statements"].get("function", "TDStep")
    snippets = {row["id"]: row["code"] for row in mapped}
    fragments = []
    for path in sorted({r["path"] for r in mapped}):
        text, _ = _source_text(source, path)
        # Balanced lexical braces find this source function only, with comments
        # and strings removed for the brace count. No verifier/main is exposed.
        tokens = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/')
        scrubbed = tokens.sub(lambda m: "".join("\n" if c == "\n" else " " for c in m.group()), text)
        signatures = list(re.finditer(r"\b" + re.escape(function) + r"\s*\([^;{}]*\)\s*\{", scrubbed))
        if len(signatures) == 1:
            signature = signatures[0]
            begin = text.rfind("\n", 0, signature.start())+1
            depth, end = 1, signature.end()
            while end < len(scrubbed) and depth:
                depth += (scrubbed[end] == "{") - (scrubbed[end] == "}")
                end += 1
            if depth:
                raise Failure("profiling source function has unbalanced lexical braces")
            fragments.append("// " + path + "\n" + text[begin:end])
    # Fixture statement-only sources may have no containing function. Real
    # snapshots provide the scalar function, including its conditional guards.
    context = {"implementation": implementation["id"], "function": function,
        "statements": [{k: v for k, v in row.items() if k not in {"source_artifact_sha256", "original_source"}}
                       for row in mapped],
        "access_patterns": [{"id": p["id"], "steps": p["steps"], "update_kind": p["update_kind"],
                             "semantics": p["semantics"]} for p in implementation["access_patterns"]
                            if p["id"] in {s["pattern"] for row in mapped for s in row["access_pattern_steps"]}],
        "profiles": [{"id": p["id"], "regions": provider_roles.project(p.get("regions", [])),
                      "dynamic_memory": provider_roles.project(p.get("dynamic_memory", []))}
                     for p in profiles]}
    # Ground truth per-line rows are hidden so rank scoring stays independent.
    return {"statement-context.json": json.dumps(context, indent=2),
            "statement-source.cc": "\n".join(fragments) if fragments else
                "\n".join("// " + rid + "\n" + code for rid, code in snippets.items())}, mapped


def _validate_response(response, implementation):
    rows = response["statements"]
    expected = {r["id"] for r in statements(implementation)}
    found = [r["statement"] for r in rows]
    if len(found) != len(expected) or set(found) != expected:
        raise Failure("profiling role must annotate every statement exactly once")
    if sorted(r["expected_cost_rank"] for r in rows) != list(range(1, len(rows)+1)):
        raise Failure("expected cost ranks must be a permutation of 1 through statement count")
    patterns = {p["id"] for p in implementation["access_patterns"]}
    by_id = {r["id"]: r for r in statements(implementation)}
    for row in rows:
        ids = [p["pattern"] for p in row["pattern_class"]]
        target = {s["pattern"] for s in by_id[row["statement"]].get("access_pattern_steps", [])}
        if len(ids) != len(set(ids)) or not set(ids).issubset(patterns) or set(ids) != target:
            raise Failure("pattern-class claims must name exactly this statement's access patterns")
        if any(r not in expected or r == row["statement"] for r in row["index_provenance"]):
            raise Failure("index provenance must name other statements of this implementation")
        if any(shape not in {"stream", "single_valued_indirect", "ranged_indirect", "pointer_chase", "data_dependent_merge"}
               for p in row["pattern_class"] for shape in p["address_shapes"]):
            raise Failure("profiling agent returned an unknown address shape")
        if any(p["update_kind"] not in {"read", "write", "add_update", "min_max_update", "compare_and_swap", "arbitrary", "prefetch"}
               for p in row["pattern_class"]):
            raise Failure("profiling agent returned an unknown update kind")


def append_claims(implementation, response, metadata, mapped):
    _validate_response(response, implementation)
    result = copy.deepcopy(implementation)
    by_id = {s["id"]: s for s in statements(result)}
    patterns = {p["id"]: p for p in result["access_patterns"]}
    common = {"model": metadata.get("model"), "effort": metadata.get("effort"),
        "prompt_sha256": metadata["prompt_sha256"],
        "input_sha256s": metadata["workspace_manifest"]["input_sha256s"],
        "classification": metadata["classification"], "contradicted_by": []}
    for row in response["statements"]:
        for field in ("pattern_class", "index_provenance", "expected_cost_rank"):
            claim = {**copy.deepcopy(common), "field": field, "value": copy.deepcopy(row[field]),
                     "basis": "inferred" if field == "expected_cost_rank" else row["basis"]}
            by_id[row["statement"]].setdefault("agent_claims", []).append(claim)
        for p in row["pattern_class"]:
            for field, value in (("pattern_class", p), ("index_provenance", row["index_provenance"])):
                patterns[p["pattern"]].setdefault("agent_claims", []).append({**copy.deepcopy(common),
                    "field": field, "value": copy.deepcopy(value), "basis": row["basis"],
                    "statement": row["statement"]})
    result["extensions"]["statements"]["source_mappings"] = copy.deepcopy(mapped)
    result["updated"] = writer.today()
    return result


def _raw_line_rows(profile):
    rows = profile.get("per_line_memory", [])
    callgrind_lines.validate(rows)
    groups = {}
    for row in rows:
        if (row.get("counter_validation", {}).get("state") != "valid"
                or row["counter_validation"].get("method") != callgrind_lines.METHOD):
            raise Failure("per-line statement ground truth lacks independent counter validation")
        groups.setdefault((row.get("raw_artifact"), row.get("raw_sha256")), []).append(row)
    from swdb.bfs_native import observation_bytes, StageFailure
    from swdb.bfs_profiling import parse_callgrind, parse_callgrind_lines
    for (path, digest), retained in groups.items():
        try:
            raw, actual = observation_bytes(path, 64*1024*1024, "Callgrind statement ground truth")
        except (StageFailure, OSError, TypeError) as error:
            raise Failure("statement ground truth raw artifact is unavailable: " + str(error)) from None
        if actual != digest:
            raise Failure("statement ground truth raw hash changed")
        summary = parse_callgrind(path, require_totals=True, raw=raw)
        parsed = parse_callgrind_lines(path, raw=raw)
        for metric in summary:
            if sum(r["events"].get(metric, 0) for r in parsed) > summary[metric]:
                raise Failure("per-line self costs exceed raw summary")
        actual_rows = {(r["path"], r["function"], r["line"]): r["events"]
                       for r in parsed if callgrind_lines.in_function(r["function"])}
        retained_ids = {(r["path"], r["function"], r["line"]) for r in retained}
        if retained_ids != set(actual_rows) or len(retained_ids) != len(retained):
            raise Failure("retained per-line rows omit or add TDStep source self costs")
        for row in retained:
            if actual_rows.get((row["path"], row["function"], row["line"])) != row["events"]:
                raise Failure("retained per-line events differ from raw Callgrind self costs")
            if row.get("source_path"):
                if artifacts.file_hash(row["path"]) != row.get("source_file_sha256"):
                    raise Failure("per-line source file differs from its recorded debug identity")
    return rows


def statement_costs(implementation, source, profile, *, verify_raw=True):
    rows = _raw_line_rows(profile) if verify_raw else callgrind_lines.validate(profile.get("per_line_memory", []))
    if not rows:
        raise Failure("statement scoring needs per_line_memory ground truth")
    if profile.get("implementation") != implementation["id"] or profile.get("source_snapshot") != source["id"]:
        raise Failure("statement ground truth belongs to another implementation or source snapshot")
    mapped = mapped_statements(implementation, source)
    root = Path(source["artifact"]["path"]).resolve()
    if any(r.get("source_artifact_sha256") != source["artifact"]["sha256"] for r in rows):
        raise Failure("statement ground truth source content differs from the source snapshot")
    costs = []
    for statement in mapped:
        expected = root / statement["path"]
        selected = [r for r in rows if (Path(r["path"]).resolve() == expected or r["path"] == statement["path"]
                    or (r.get("source_path") == statement["path"] and r.get("source_file_sha256") == statement["source_sha256"]))
                    and callgrind_lines.in_function(r["function"])
                    and statement["lines"][0] <= r["line"] <= statement["lines"][1]]
        if any("DLmr" not in r["events"] or "DLmw" not in r["events"] for r in selected):
            raise Failure("statement ground truth lacks last-level read/write miss events")
        value = sum(r["events"]["DLmr"] + r["events"]["DLmw"] for r in selected)
        costs.append({"statement": statement["id"], "path": statement["path"], "lines": statement["lines"],
            "metric": "last_level_misses", "value": value, "basis": "simulated", "unit": "misses",
            "profile": profile["id"], "source_artifact_sha256": source["artifact"]["sha256"],
            "source_mapping": statement, "attributed_rows": len(selected),
            "limitations": "debug-line self costs; optimized/coalesced or header-inlined work may have no costs on the statement line"})
    if not any(c["attributed_rows"] for c in costs):
        raise Failure("per-line ground truth attributes no rows to the mapped statement source")
    return costs


def _midranks(values):
    result = [None] * len(values)
    indices = sorted(range(len(values)), key=lambda i: (-values[i], i))
    first = 0
    while first < len(indices):
        end = first+1
        while end < len(indices) and values[indices[end]] == values[indices[first]]:
            end += 1
        for i in indices[first:end]:
            result[i] = (first+1+end)/2
        first = end
    return result


def _spearman(expected, observed):
    left = [v-sum(expected)/len(expected) for v in expected]
    right = [v-sum(observed)/len(observed) for v in observed]
    denominator = math.sqrt(sum(v*v for v in left)*sum(v*v for v in right))
    return sum(a*b for a, b in zip(left, right))/denominator if denominator else None


def _top_overlap(expected, misses):
    """Fractional boundary ties avoid arbitrary statement-ID tie breaking."""
    k = min(3, len(expected))
    threshold = sorted(misses, reverse=True)[k-1]
    above = sum(v > threshold for v in misses)
    tied = sum(v == threshold for v in misses)
    probability = (k-above)/tied
    count = sum(1 if misses[i] > threshold else probability if misses[i] == threshold else 0
                for i, rank in enumerate(expected) if rank <= k)
    return count, count/k


def _last_claim(statement, field):
    found = [c for c in statement.get("agent_claims", []) if c.get("field") == field]
    if not found:
        raise Failure("statement has no agent " + field + " claim: " + statement["id"])
    return found[-1]


def _fact_contradictions(target, field, value):
    return [{"evidence": f.get("evidence", "recorded access-pattern fact"), "basis": f["basis"],
             "rule": "agent value differs from recorded access-pattern fact", "observed_value": f["value"]}
            for f in target.get("annotation_facts", [])
            if f.get("field") == field and f.get("basis") in FACT_BASES and f.get("value") != value]


def score(implementation, source, profile, *, verify_raw=True):
    costs = statement_costs(implementation, source, profile, verify_raw=verify_raw)
    result = copy.deepcopy(implementation)
    targets = {s["id"]: s for s in statements(result)}
    claims = [_last_claim(targets[c["statement"]], "expected_cost_rank") for c in costs]
    expected = [c["value"] for c in claims]
    if any(type(v) is not int for v in expected) or sorted(expected) != list(range(1, len(costs)+1)):
        raise Failure("stored expected cost ranks are not a permutation of 1 through statement count")
    misses = [c["value"] for c in costs]
    observed = _midranks(misses)
    for cost, claim, actual in zip(costs, claims, observed):
        cost.update(expected_cost_rank=claim["value"], callgrind_rank=actual,
                    contradicted=abs(claim["value"]-actual) > 1)
        if cost["contradicted"]:
            contradiction = {"evidence": profile["id"], "profile_sha256": artifacts.digest(profile),
                "basis": "simulated", "rule": COST_RULE, "observed_rank": actual}
            if contradiction not in claim["contradicted_by"]:
                claim["contradicted_by"].append(contradiction)
    for target in [*targets.values(), *result["access_patterns"]]:
        for claim in target.get("agent_claims", []):
            if claim["field"] not in {"pattern_class", "index_provenance"}:
                continue
            for contradiction in _fact_contradictions(target, claim["field"], claim["value"]):
                if contradiction not in claim["contradicted_by"]:
                    claim["contradicted_by"].append(contradiction)
    overlap_count, overlap = _top_overlap(expected, misses)
    report = {"format": "swdb.statement-annotation-score.v1", "implementation": implementation["id"],
        "source_snapshot": source["id"], "region_profile": profile["id"],
        "region_profile_sha256": artifacts.digest(profile), "basis": "simulated", "gain_claim": False,
        "spearman_rank_correlation": _spearman(expected, observed), "top_3_overlap": overlap,
        "top_3_overlap_count": overlap_count, "rank_tie_policy": "average ranks",
        "top_3_tie_policy": "expected overlap under uniform choice at the tied boundary",
        "contradiction_rule": COST_RULE, "statements": costs}
    if report["spearman_rank_correlation"] is None:
        report["correlation_reason"] = "rank correlation is undefined for constant observed ranks"
    result["extensions"].setdefault("statement_annotation_scores", []).append(report)
    result["updated"] = writer.today()
    return result, report


def statement_table(implementation, report):
    statements_by_id = {s["id"]: s for s in statements(implementation)}
    lines = ["# TDStep statement annotations for Josh", "", "Updated: " + writer.today(), "",
        "Draft for Yan-Ru to send. Agent predictions are source reading or inference; cache misses are Callgrind simulation.",
        "", f"Spearman rank correlation: {report['spearman_rank_correlation']}; top-3 overlap: {report['top_3_overlap']:.3f}.",
        "", "| Statement | Scalar lines | Pattern class (agent) | Index provenance (agent) | Expected rank | Simulated LL misses | Callgrind rank | Contradicted |",
        "|---|---|---|---|---:|---:|---:|---|"]
    for row in report["statements"]:
        statement = statements_by_id[row["statement"]]
        classes = _last_claim(statement, "pattern_class")["value"]
        description = "; ".join(" → ".join(p["address_shapes"]) + ": " + p["update_kind"] for p in classes)
        provenance = " → ".join(_last_claim(statement, "index_provenance")["value"]) or "none"
        lines.append(f"| {row['statement']} | {row['lines'][0]}–{row['lines'][1]} | {description} | {provenance} | "
                     f"{row['expected_cost_rank']} | {row['value']} | {row['callgrind_rank']:g} | {'yes' if row['contradicted'] else 'no'} |")
    lines += ["", "Cost contradiction rule: " + COST_RULE + ".",
        "Tied miss counts receive average ranks; top-3 boundary ties use fractional expected overlap.",
        "Pattern and index claims require a measured, simulated or person-reported access-pattern fact to contradict them.",
        "Debug-line self costs can exclude coalesced or inlined-header work; these ranks do not prove a native bottleneck.",
        "", "Region profile: `" + report["region_profile"] + "`; sha256: `" + report["region_profile_sha256"] + "`.", ""]
    return "\n".join(lines)


def _mode_store(args):
    if args.mode == "extensa":
        records = Path(args.records).resolve()
        if (not args.campaign or records == paths.RECORDS.resolve() or records.is_relative_to(paths.HOME.resolve())
                or not any(root in records.parents for root in (Path("/data1/yanruj"), Path("/data/yanruj")))):
            raise Failure("Extensa annotations need --campaign and an external mbit10 campaign record store")
    return _require_valid(args.records)


def run(args):
    store = _mode_store(args)
    implementation = store.get(args.implementation, "implementation")
    source = store.get(args.source_snapshot, "source_snapshot")
    if not implementation or not source or source.get("implementation") != implementation["id"]:
        raise Failure("annotate needs an implementation and its exact source snapshot")
    profiles = []
    for identity in args.profile:
        p = store.get(identity, "region_profile")
        if not p or p.get("implementation") != implementation["id"] or p.get("source_snapshot") != source["id"]:
            raise Failure("annotation context profile belongs to another implementation or source snapshot")
        profiles.append(p)
    config = rewrite.configuration(args.provider_config)
    files, mapped = workspace_input(implementation, source, profiles)
    folder = artifacts.external_directory(args.runs_dir) / args.id
    prompt = ("Read statement-context.json and statement-source.cc. Annotate every declared statement with its "
        "pattern class (one entry per access pattern), index provenance as statement IDs in chain order, and a "
        "unique expected cost rank from 1 to N. Rank 1 means most expected last-level data misses (reads plus writes). "
        "Keep code_reading and inferred separate. Read source only; do not run profilers, builds, tests or tools "
        "that evaluate the code. Existing per-line ground truth is hidden. Return the structured schema.")
    response, metadata = provider_roles.run(PROFILING, files, prompt, config, folder)
    result = append_claims(implementation, response, metadata, mapped)
    if args.mode == "extensa":
        result["extensions"]["annotation_mode"] = {"mode": "extensa", "campaign": args.campaign}
    writer.commit(args.records, replace=[result])
    return {"implementation": result["id"], "role": "profiling", "receipt": str(folder/"provider.json"),
            "classification": metadata["classification"], "statements": len(mapped), "mode": args.mode}


def score_command(args):
    store = _mode_store(args)
    implementation = store.get(args.implementation, "implementation")
    source = store.get(args.source_snapshot, "source_snapshot")
    profile = store.get(args.region_profile, "region_profile")
    if not implementation or not source or not profile:
        raise Failure("annotate-score requires existing implementation, source snapshot and region profile")
    updated_profile = copy.deepcopy(profile)
    costs = statement_costs(implementation, source, profile)
    if updated_profile.get("statement_memory") != costs:
        updated_profile["statement_memory"] = costs
        updated_profile["updated"] = writer.today()
    result, report = score(implementation, source, updated_profile)
    writer.commit(args.records, replace=[result, updated_profile])
    if args.table:
        Path(args.table).write_text(statement_table(result, report))
        report["statement_table"] = str(Path(args.table).resolve())
    return report


def register_cli(commands):
    for name, function, description in (("annotate", run, "annotate source statements through the profiling agent role"),
            ("annotate-score", score_command, "score statement claims against separate per-line Callgrind facts")):
        sub = commands.add_parser(name, help=description, description=description)
        sub.add_argument("implementation")
        sub.add_argument("--records", type=Path, default=paths.RECORDS)
        sub.add_argument("--source-snapshot", required=True)
        sub.add_argument("--mode", choices=["archevolve", "extensa"], default="archevolve")
        sub.add_argument("--campaign")
        sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
        sub.set_defaults(_annotation_handler=function)
        if name == "annotate":
            sub.add_argument("--provider-config", type=Path, required=True)
            sub.add_argument("--runs-dir", type=Path, required=True)
            sub.add_argument("--id", required=True)
            sub.add_argument("--profile", action="append", default=[])
        else:
            sub.add_argument("--region-profile", required=True)
            sub.add_argument("--table", type=Path)
