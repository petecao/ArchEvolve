"""Inert prospective ten-site private-array diagnostic generation v2, 2026-10-16 ET.

Root must launch this ONLY beneath the reviewed 120s/8GiB counted_verifier.
There is no stage2, provider, solver invocation or proof acceptance here.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

TOKEN = "SWDB_VERIFIER_RUN_TOKEN"
EXPECTED_SHA256 = "e4fc76c7ff858710e208151cae4c2d89a94529f95534611da1874b3882c6f2a8"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def check_pin(row):
    path = Path(row["path"])
    if row.get("absent"):
        if path.exists():
            raise RuntimeError("previously absent config appeared: " + str(path))
        return
    if str(path.resolve()) != row["resolved"] or digest(path) != row["sha256"]:
        raise RuntimeError("physical input pin changed: " + str(path))


def check_tree(tree):
    for row in tree["files"]:
        check_pin(row)
    # The recipe qualifies an exact selected surface, including absence of new
    # headers or compiled package artifacts. Bytecode/cache output is excluded.
    root = Path(tree["path"])
    wanted = {r["relative"] for r in tree["files"]}
    if "frama-c/share/libc" in str(root):
        found = {str(f.relative_to(root)) for f in root.rglob("*") if f.is_file()}
    elif root.name == "psutil":
        found = {str(f.relative_to(root)) for f in root.rglob("*") if f.is_file() and f.suffix in {".py", ".so"}}
    else:
        found = {str(f.relative_to(root)) for f in root.rglob("*") if f.is_file() and
                 (f.suffix in {".cmi", ".cmx", ".cmxa", ".cmxs", ".a"} or f.name == "META")}
    if found != wanted:
        raise RuntimeError("selected tree membership changed: " + str(root))


def verify_runtime(expected):
    rows = list(expected["tools"].values()) + [expected["python"]] + expected["toolchain_artifacts"] + expected["configuration_files"] + expected["external_pins"]
    for row in rows:
        check_pin(row)
    for tree in [expected["standard_headers"], expected["psutil_surface"], *expected["package_surfaces"]]:
        check_tree(tree)


def direct_calls(text, helpers, bodyless, known_helpers=None, source_file="gapbs_models.h"):
    """Finite exact-source census, not a general C parser or C++ theorem."""
    known_helpers = helpers if known_helpers is None else known_helpers
    code = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group().count("\n"), text, flags=re.S)
    code = re.sub(r"//[^\n]*", "", code)
    if re.search(r"\(\s*\*\s*[A-Za-z_]\w*\s*\)\s*\(", code):
        raise RuntimeError("indirect-call spelling invalidates finite direct-call scope")
    calls = []
    for caller in helpers:
        definitions = list(re.finditer(r"\b" + re.escape(caller) + r"\s*\([^;{}]*\)\s*\{", code))
        if len(definitions) != 1:
            raise RuntimeError("helper definition missing or ambiguous: " + caller)
        start = definitions[0].end()
        depth, end = 1, start
        while depth and end < len(code):
            if code[end] == "{":
                depth += 1
            elif code[end] == "}":
                depth -= 1
            end += 1
        if depth:
            raise RuntimeError("unterminated helper definition: " + caller)
        for call in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", code[start:end-1]):
            callee = call.group(1)
            if callee in {"if", "for", "while", "switch", "sizeof", "return"}:
                continue
            if callee not in set(known_helpers) | set(bodyless):
                raise RuntimeError("unclassified direct/indirect call target: " + callee)
            line = code.count("\n", 0, start + call.start()) + 1
            calls.append({"callee": callee, "caller": caller, "source_file": source_file, "line": line,
                          "line_sha256": hashlib.sha256(text.splitlines()[line-1].encode()).hexdigest()})
    return calls


def read_inventory(inventory, log, expected):
    goals, properties = inventory.get("goals"), inventory.get("properties")
    if inventory.get("complete") is not True or not isinstance(goals, list) or not goals or not isinstance(properties, list) or not properties:
        raise RuntimeError("missing or empty complete production goal/property inventory")
    ids = [row.get("goal") for row in goals]
    if any(not isinstance(x, str) or not x for x in ids) or len(ids) != len(set(ids)):
        raise RuntimeError("missing or duplicate generated goal identity")
    property_ids = [row.get("property") for row in properties]
    if any(not isinstance(x, str) or not x for x in property_ids) or len(property_ids) != len(set(property_ids)):
        raise RuntimeError("missing or duplicate machine property identity")
    property_set = set(property_ids)
    if any(row.get("property") not in property_set for row in goals):
        raise RuntimeError("generated goal has no retained property record")
    helpers = set(expected["helpers"])
    if any(type(row.get("smoke")) is not bool for row in goals):
        raise RuntimeError("generated goal lacks exact ordinary/smoke classification")
    ordinary = [row for row in goals if not row["smoke"]]
    smokes = [row for row in goals if row["smoke"]]
    if {row.get("function") for row in ordinary} != helpers:
        raise RuntimeError("all ordinary goals must cover exactly all scoped helper/site bodies")
    contexts = expected["direct_bodyless_call_contexts"]
    approved_contexts = []
    for row in smokes:
        if row.get("function") in helpers:
            continue
        if row.get("function") not in expected["bodyless_allowlist"]:
            raise RuntimeError("outsider smoke subject is not an exact bodyless declaration")
        matches = [context for context in contexts if context["callee"] == row.get("function")
                   and context["line"] == row.get("line") and context["caller"] in helpers]
        props = [prop for prop in properties if prop.get("property") == row.get("property")
                 and prop.get("function") == row.get("function") and prop.get("line") == row.get("line")
                 and prop.get("description") == "wp_smoke_dead_call" and prop.get("extern") is False]
        if len(matches) != 1 or len(props) != 1:
            raise RuntimeError("bodyless-call smoke context/property is missing or ambiguous")
        approved_contexts.append({"goal": row["goal"], "property": row["property"],
                                  "context": matches[0], "property_record": props[0]})
    if len(approved_contexts) != len(contexts) or {
            (r["context"]["callee"], r["context"]["caller"], r["context"]["line"]) for r in approved_contexts} != {
            (r["callee"], r["caller"], r["line"]) for r in contexts}:
        raise RuntimeError("exact scoped bodyless direct-call smoke contexts are not completely retained")
    scheduled = [int(x) for x in re.findall(r"^\[wp\] (\d+) goals? scheduled\s*$", log, re.M)]
    logged_goal_ids = re.findall(r"^\[wp\] Goal (\S+) : .+$", log, re.M)
    if not logged_goal_ids or len(logged_goal_ids) != len(set(logged_goal_ids)) or not set(logged_goal_ids) <= set(ids):
        raise RuntimeError("per-goal log identity census is empty, duplicate or outside complete inventory")
    property_by_id = {row["property"]: row for row in properties}
    inventory_only = []
    for row in goals:
        if row["goal"] in set(logged_goal_ids):
            continue
        prop = property_by_id[row["property"]]
        if (row.get("smoke") is not False or row.get("function") not in helpers or
            row.get("passed") is not True or row.get("results") != ["valid"] or row.get("targets") != [] or
            prop.get("function") != row.get("function") or prop.get("line") != row.get("line") or
            prop.get("kind") != "contract" or prop.get("extern") is not False or
            prop.get("description") not in {"terminates\n\\true", "exits\n\\false"}):
            raise RuntimeError("unclassified inventory-only goal; do not hide missing goal-log evidence")
        inventory_only.append({"goal_record": row, "property_record": prop})
    if scheduled and sum(scheduled) != len(logged_goal_ids):
        raise RuntimeError("scheduled and complete human goal-log counts disagree")
    for prop in properties:
        if type(prop.get("extern")) is not bool or type(prop.get("generated_smoke_failure")) is not bool:
            raise RuntimeError("property assumption/smoke flags missing")
        deps = prop.get("dependencies")
        if not isinstance(deps, list) or any(x not in property_set for x in deps):
            raise RuntimeError("property dependency outside complete retained inventory")
        if prop.get("origin") is not None and prop["origin"] not in property_set:
            raise RuntimeError("property origin outside complete retained inventory")
    if any(t not in property_set for row in goals for t in row.get("targets", [])):
        raise RuntimeError("goal smoke target outside complete retained inventory")
    goal_log_census = {"logged_goal_ids": logged_goal_ids, "inventory_only": inventory_only,
                       "scheduled_counts": scheduled, "scheduled_line_present": bool(scheduled),
                       "all_inventory_rows_retained": True, "proof_acceptance": False,
                       "boundary": "Wpo inventory is complete source export; implicit trivial contract rows can be absent from human goal log. No rows dropped or solver success inferred."}
    init_properties = [row for row in properties if "initializ" in row.get("description", "").lower()
                       and "rte" in row.get("emitter", "").lower()]
    if not init_properties:
        raise RuntimeError("no attributable generated RTE initialization properties; support not established")
    unknown_externs = [row for row in properties if row.get("extern") and
                       row.get("function") not in expected["bodyless_allowlist"]]
    if unknown_externs:
        raise RuntimeError("unexpected external property assumption")
    if "[report] Computing properties status" not in log:
        raise RuntimeError("complete property report marker missing")
    return {"goals": goals, "properties": properties, "helpers": sorted(helpers),
            "ordinary": ordinary, "smokes": smokes, "approved_contexts": approved_contexts,
            "init_properties": init_properties, "goal_log_census": goal_log_census}


def scan_normalized(normalized, expected, staged_calls):
    banner = "/* Generated by Frama-C */"
    chunks = normalized.split(banner)
    if chunks[0].strip() or len(chunks) < 2:
        raise RuntimeError("unknown normalized-C snapshot framing")
    normalized_rows = []
    source_pairs = sorted((r["caller"], r["callee"]) for r in staged_calls)
    for number, chunk in enumerate(chunks[1:], 1):
        snapshot = banner + chunk
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", snapshot, flags=re.S)
        definitions = [name for name in re.findall(r"\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{", code)
                       if name not in {"if", "for", "while", "switch"}]
        if sorted(definitions) != sorted(expected["helpers"]):
            raise RuntimeError("normalized body inventory differs from all scoped helper/site definitions")
        filename = "normalized-snapshot-" + str(number) + ".c"
        normalized_calls = direct_calls(snapshot, expected["helpers"], expected["bodyless_allowlist"], source_file=filename)
        if sorted((r["caller"], r["callee"]) for r in normalized_calls) != source_pairs:
            raise RuntimeError("normalized snapshot direct-call census differs from source; scope invalid")
        normalized_rows.append({"snapshot": number, "file": filename,
                                "sha256": hashlib.sha256(snapshot.encode()).hexdigest(),
                                "calls": normalized_calls, "text": snapshot})
    return normalized_rows


def scan_diagnostics(log, capability_rows):
    lines = log.splitlines()
    if any(lines.count(row["message"]) != 1 for row in capability_rows):
        raise RuntimeError("exact two capability-warning observations differ; classification not transferable")
    # These two exact observations are RETAINED residual/case-specific
    # metadata. This is not an unsupported-class waiver or proof success.
    exact_messages = {row["message"] for row in capability_rows}
    remainder = "\n".join(line for line in lines if line not in exact_messages)
    fatal = (r"not (?:yet )?implemented|unsupported|unimplemented|not defined|cannot translate|"
             r"Cast with incompatible|missing rte|Skipped RTE guards|User Error|Fatal error|Frama-C aborted|"
             r"\b(?:skipped|skipping|omitted|omitting|ignoring)\b")
    if re.search(fatal, remainder, re.I):
        raise RuntimeError("new unsupported/builtin/cast/omission boundary; inspect retained log")
    warnings = [line for line in remainder.splitlines() if re.search(r"\bWarning\b", line)]
    pedantic = [line for line in warnings if line.startswith("[wp:pedantic-assigns]")]
    unclassified = [line for line in warnings if line not in pedantic]
    if unclassified:
        raise RuntimeError("unclassified warning; no automatic applicability waiver")
    return {"pedantic": pedantic, "unclassified": unclassified, "continuations": "retained in full frama-generation.log; no warning suppression"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if digest(args.expected) != EXPECTED_SHA256:
        raise RuntimeError("expected-manifest hash differs from reviewed recipe")
    expected = json.loads(args.expected.read_bytes())
    ambient = sorted(k for k in os.environ if k.startswith(("FRAMAC_WP", "WP_")) or k == "SWDB_PROOF_REPORT_OUT")
    if ambient:
        raise RuntimeError("ambient WP selector names refused: " + ",".join(ambient))
    marker = os.environ.get(TOKEN)
    if not marker:
        raise RuntimeError("missing inherited counted-verifier ownership marker")
    if Path(sys.executable).resolve() != Path(expected["python"]["resolved"]):
        raise RuntimeError("unexpected selected Python runtime")
    output = args.output.resolve()
    checkout = Path(expected["source_root"]).resolve()
    if output == checkout or checkout in output.parents or output.exists():
        raise RuntimeError("fresh component output outside source checkout required")
    output.mkdir(parents=True)
    started = time.monotonic()
    deadline = started + 110.0
    commands, cases = [], []
    result = {"stage": "ten_TU_generation_only", "proof_acceptance": False,
              "external_provers_requested": [], "source_commit": expected["source_commit"],
              "source_staging": "immutable Git blobs; physical worktree bytes/HEAD need not remain frozen",
              "full_TD_or_counted_admissible": False, "source_correspondence": False,
              "initializedness_map_qualified": False, "lifetime_qualified": False}
    prefix = Path(expected["tools"]["frama-c"]["path"]).parent
    (output / "tmp").mkdir()
    env = {"HOME": "/Users/yanrujhou", "PATH": str(prefix) + ":/opt/homebrew/bin:/usr/bin:/bin",
           "TMPDIR": str(output / "tmp"), "WHY3CONFIG": expected["why3_config"],
           "PYTHONDONTWRITEBYTECODE": "1", TOKEN: marker}
    opam = [expected["tools"]["opam"]["path"], "exec", "--root=/Users/yanrujhou/.opam", "--switch=framac-33", "--"]

    def check_output_budget():
        used = sum(f.stat().st_size for f in output.rglob("*") if f.is_file())
        if used > expected["resource_policy"]["output_budget_bytes"]:
            raise RuntimeError("component output byte budget exceeded")

    def run(argv, label, cwd=output, child_env=None):
        check_output_budget()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("internal deadline expired before " + label)
        commands.append({"label": label, "argv": argv, "cwd": str(cwd)})
        write(output / "commands.json", commands)
        log_path = output / (label + ".log")
        with log_path.open("wb") as log:
            done = subprocess.run(argv, cwd=cwd, env=env if child_env is None else child_env,
                                  stdout=log, stderr=subprocess.STDOUT, timeout=remaining, check=False)
        check_output_budget()
        if done.returncode:
            raise RuntimeError(label + " exited " + str(done.returncode))
        return log_path.read_bytes()

    def verify_staged(staged):
        for row in expected["source_blobs"]:
            if digest(staged / row["relative"]) != row["sha256"]:
                raise RuntimeError("staged immutable source changed: " + row["relative"])

    try:
        verify_runtime(expected)
        shutil.copyfile(args.expected, output / "expected.json")
        shutil.copyfile(__file__, output / "entry.py")
        staged = output / "git-source"
        staged.mkdir()
        for i, row in enumerate(expected["source_blobs"]):
            identity = run(["/usr/bin/git", "-C", str(checkout), "rev-parse",
                            expected["source_commit"] + ":" + row["relative"]], "git-identity-" + str(i)).decode().strip()
            if identity != row["git_blob"]:
                raise RuntimeError("source commit/blob closure changed")
            raw = run(["/usr/bin/git", "-C", str(checkout), "cat-file", "blob", identity], "git-blob-" + str(i))
            if hashlib.sha256(raw).hexdigest() != row["sha256"] or len(raw) != row["bytes"]:
                raise RuntimeError("immutable source byte pin differs")
            target = staged / row["relative"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        verify_staged(staged)
        bindings = {}
        for package, target in expected["package_bindings"].items():
            text = run([*opam, expected["tools"]["ocamlfind"]["path"], "query", "-format", "%d", package],
                       "package-" + package).decode().strip()
            if text != target:
                raise RuntimeError("selected OCaml package binding changed: " + package)
            bindings[package] = text
        write(output / "package-bindings.json", bindings)
        shutil.copyfile(staged / expected["report_relative"], output / "proof_report.ml")
        run([*opam, expected["tools"]["ocamlfind"]["path"], "ocamlopt", "-shared", "-linkall",
             "-package", "frama-c.kernel,frama-c-wp.core", "-o", "proof_report.cmxs", "proof_report.ml"], "report-compile")
        for case in expected["cases"]:
            directory = output / case["name"]
            directory.mkdir()
            shutil.copyfile(staged / expected["header_relative"], directory / "gapbs_models.h")
            shutil.copyfile(staged / case["site_relative"], directory / "site_input.c")
            text = (directory / "gapbs_models.h").read_bytes().decode("utf-8")
            site = (directory / "site_input.c").read_bytes().decode("utf-8")
            if digest(directory / "gapbs_models.h") != expected["header_sha256"] or digest(directory / "site_input.c") != case["site_sha256"]:
                raise RuntimeError("staged root/header bytes changed")
            calls = direct_calls(text, expected["header_helpers"], expected["bodyless_allowlist"],
                                 case["helpers"], "gapbs_models.h")
            calls += direct_calls(site, case["root_functions"], expected["bodyless_allowlist"],
                                  case["helpers"], "site_input.c")
            if calls != case["all_direct_call_contexts"]:
                raise RuntimeError("exact staged source call-context map differs")
            write(directory / "source-direct-call-contexts.json", calls)
            child_env = dict(env, SWDB_PROOF_REPORT_OUT=str(directory / "wp-inventory.json"))
            command = [*opam, expected["tools"]["frama-c"]["path"], "-machdep", "x86_64", "site_input.c",
                       "-print", "-ocode", "normalized.c", "-then", "-wp", "-wp-model", "Typed", "-wp-rte",
                       "-rte-initialized", ",".join(case["helpers"]), "-wp-no-filter-init", "-wp-cache", "none",
                       "-wp-prover", "none", "-wp-par", "1", "-wp-smoke-tests", "-wp-session", "session",
                       "-wp-report-json", "wp-native-goals.json", "-then", "-load-module", str(output / "proof_report.cmxs"),
                       "-report", "-report-untried", "-report-csv", "wp-properties.csv"]
            log = run(command, case["name"] + "-frama-generation", directory, child_env).decode("utf-8", errors="replace")
            (directory / "frama-generation.log").write_bytes(log.encode())
            warning_rows = [{**row, "occurrences": log.splitlines().count(row["message"])} for row in expected["capability_warnings"]]
            write(directory / "capability-boundaries.json", {"warnings": warning_rows,
                  "alignment_qualified": False, "full_C_RTE_claim": False,
                  "direct_call_applicability_verified": False, "proof_acceptance": False})
            retained = scan_diagnostics(log, warning_rows)
            write(directory / "retained-warning-headers.json", retained)
            inventory = json.loads((directory / "wp-inventory.json").read_bytes())
            scoped = {**expected, **case}
            census = read_inventory(inventory, log, scoped)
            normalized_rows = scan_normalized((directory / "normalized.c").read_bytes().decode("utf-8"), scoped, calls)
            for row in normalized_rows:
                (directory / row["file"]).write_bytes(row["text"].encode())
            write(directory / "normalized-direct-call-contexts.json", [{k:v for k,v in row.items() if k != "text"} for row in normalized_rows])
            write(directory / "bodyless-call-smoke-contexts.json", census["approved_contexts"])
            write(directory / "goal-log-census.json", census["goal_log_census"])
            init = census["init_properties"]
            write(directory / "initialization-boundaries.json", {"all_initialization_properties": init,
                "intended_source_read_anchors": case["intended_read_anchors"],
                "candidate_anchor_matches": [{"anchor": anchor, "properties": [row for row in init if row["function"] == anchor["function"] and row["line"] == anchor["line"]]} for anchor in case["intended_read_anchors"]],
                "Typed_T_init_classification": "UNESTABLISHED; cold normalized/VC audit required",
                "negative_acceptance": False, "positive_proof_acceptance": False,
                "scope_retirement_and_reentry_qualified": False})
            if not (directory / "wp-properties.csv").is_file():
                raise RuntimeError("complete property CSV missing")
            if digest(directory / "gapbs_models.h") != expected["header_sha256"] or digest(directory / "site_input.c") != case["site_sha256"]:
                raise RuntimeError("case inputs changed")
            write(directory / "capability-boundaries.json", {"warnings": warning_rows,
                  "alignment_qualified": False, "full_C_RTE_claim": False,
                  "direct_call_applicability_verified": True, "proof_acceptance": False,
                  "scope": "exact staged and every normalized direct-call census only"})
            cases.append({"case": case["name"], "generation_completed": True,
                          "goals": len(census["goals"]), "properties": len(census["properties"]),
                          "ordinary": len(census["ordinary"]), "smoke": len(census["smokes"]),
                          "initialization_properties": len(init), "body_functions": case["helpers"],
                          "normalized_snapshots": len(normalized_rows),
                          "native_report_present": (directory / "wp-native-goals.json").exists(),
                          "native_report_boundary": "prover none can omit native artifact; complete production inventory mandatory; no proof accepted"})
            write(output / "cases.json", cases)
        verify_staged(staged)
        verify_runtime(expected)
        check_output_budget()
        result.update(generation_completed=True, cases=cases, source_staged_unchanged=True,
                      marker_inherited_and_preserved=True,
                      boundary="Hand-model diagnostic generation only; exact C++ macro/include closure and Typed payload/lifetime map remain unqualified. All rows retained; no source/full TD/proof/count acceptance.")
    except Exception as exc:
        result.update(generation_completed=False, cases=cases, error_type=type(exc).__name__, error=str(exc))
    finally:
        files = [{"path": str(f.relative_to(output)), "sha256": digest(f), "bytes": f.stat().st_size}
                 for f in sorted(output.rglob("*")) if f.is_file() and f.name not in ("result.json", "artifact-manifest.json")]
        write(output / "artifact-manifest.json", files)
        result["elapsed_seconds"] = time.monotonic() - started
        result["within_internal110s"] = result["elapsed_seconds"] <= 110.0
        write(output / "result.json", result)
        if time.monotonic() > deadline:
            result["within_internal110s"] = False
            write(output / "result.json", result)
    return 0 if result.get("generation_completed") and result["within_internal110s"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
