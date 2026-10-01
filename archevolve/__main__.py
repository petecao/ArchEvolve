"""Run the local feature -> candidate -> Mermaid pipeline without APIs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import yaml

from archevolve.normalize import load_normalized
from archevolve.select import select_candidates
from tools.render_mermaid import RequestError, build_artifacts, load_request


ROOT = Path(__file__).resolve().parents[1]


def reference_context(root: Path) -> dict:
    observations, _ = load_request(root / "examples/bfs.source-observations.yaml")
    declarations = observations["type_evidence"]
    sizes = {}
    for item in declarations:
        match = re.fullmatch(r"typedef (?:u?int)(\d+)_t (\w+);", item["declaration"])
        if match:
            sizes[match[2]] = int(match[1]) // 8
    return {"revision":observations["kernel"]["revision"],
            "element_bytes":{"VertexOffsets":sizes.get("SGOffset"), "parent":sizes.get("NodeID"),
                             "queue.shared":sizes.get("NodeID"), "g.out_neighbors_":sizes.get("NodeID")},
            "evidence":"examples/bfs.source-observations.yaml", "basis":"recorded_manual_source_review"}


def table_text(value):
    return str(value).replace("\n", " ").replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;").replace("`", "\\`")


def prepare_run(input_paths, catalog_path, root=ROOT, max_candidates=3, methods_path=None,
                source_context_path=None, compare_design_ids=None):
    """Prepare all artifacts in memory; malformed later inputs cannot leave half a run."""
    catalog, catalog_digest = load_request(catalog_path)
    evidence_catalog = catalog.get("format") == "hardware-catalog-v0.1"
    if not evidence_catalog and (source_context_path is not None or compare_design_ids is not None):
        raise RequestError("Source-context handoffs and design comparisons require the evidence catalog.")
    reference = reference_context(root)
    methods, methods_digest = None, None
    source_context, context_digest = None, None
    if source_context_path is not None:
        from archevolve.workload_context import validate_context
        source_context, context_digest = load_request(source_context_path)
        validate_context(source_context)
    if methods_path is not None:
        methods, methods_digest = load_request(methods_path)
        methods["record_sha256"] = methods_digest
    threshold = catalog.get("heuristic_policy", {}).get("large_jump_threshold_elements", 16)
    if type(threshold) not in (float, int) or threshold <= 1.1:
        raise RequestError("The large-jump heuristic threshold must exceed the near-unit bound of 1.1.")
    artifacts, cases, case_ids = {}, [], set()
    for index, input_path in enumerate(input_paths, start=1):
        case = load_normalized(input_path, reference, threshold, methods)
        if source_context is not None:
            from archevolve.workload_context import bind_context
            case = bind_context(case, source_context, context_digest, str(source_context_path))
        if case["case_id"] in case_ids:
            raise RequestError(f"Duplicate case_id {case['case_id']!r}; keep independent runs distinct.")
        case_ids.add(case["case_id"])
        request, trace = select_candidates(case, catalog, str(catalog_path), catalog_digest, max_candidates)
        folder = f"case-{index:02d}"
        request_text = yaml.safe_dump(request, sort_keys=False, allow_unicode=True)
        request_digest = hashlib.sha256(request_text.encode()).hexdigest()
        diagrams = build_artifacts(request, "hardware-request.yaml", request_digest)
        artifacts[f"{folder}/input.received.yaml"] = input_path.read_text()
        artifacts[f"{folder}/normalized.yaml"] = yaml.safe_dump(case, sort_keys=False, allow_unicode=True)
        artifacts[f"{folder}/hardware-request.yaml"] = request_text
        artifacts[f"{folder}/selection-trace.yaml"] = yaml.safe_dump(trace, sort_keys=False, allow_unicode=True)
        for name, content in diagrams.items():
            artifacts[f"{folder}/diagrams/{name}"] = content
        if evidence_catalog:
            from archevolve.intrinsic_handoff import build_handoff_artifacts
            from archevolve.comparison import build_comparison_artifacts
            for name, content in build_handoff_artifacts(request, request_digest).items():
                artifacts[f"{folder}/handoffs/{name}"] = content
            for name, content in build_comparison_artifacts(request, catalog, compare_design_ids).items():
                artifacts[f"{folder}/{name}"] = content
        cases.append({"case_id":case["case_id"], "folder":folder, "input_ref":str(input_path),
                      "input_sha256":case["input_sha256"], "selected_entries":[c["catalog_entry"] for c in request["candidates"]],
                      "issues":case["issues"], "hardware_request_sha256":request_digest})
    code_hash = hashlib.sha256(b"".join((root / name).read_bytes() for name in (
        "archevolve/normalize.py", "archevolve/measurement_methods.py", "archevolve/select.py", "archevolve/evidence_select.py", "archevolve/hardware_catalog.py", "archevolve/mechanisms.py", "archevolve/workload_context.py", "archevolve/intrinsic_handoff.py", "archevolve/comparison.py", "archevolve/__main__.py", "tools/render_mermaid.py"))).hexdigest()
    run_key = {"inputs":[c["input_sha256"] for c in cases], "catalog_sha256":catalog_digest,
               "max_candidates":max_candidates, "code_sha256":code_hash, "reference":reference, "methodology_sha256":methods_digest,
               "source_context_sha256":context_digest, "comparison_design_ids":compare_design_ids}
    manifest = {"pipeline_version":"offline-0.3" if evidence_catalog else "offline-0.1", "backend":"offline_evidence_lookup" if evidence_catalog else "offline_rules", "llm_calls":0, "evaluation_performed":False,
                "run_id":hashlib.sha256(json.dumps(run_key,sort_keys=True).encode()).hexdigest(),
                "identity":run_key, "catalog_ref":str(catalog_path), "catalog_revision":catalog["revision"], "cases":cases}
    artifacts["catalog.snapshot.yaml"] = catalog_path.read_text()
    if evidence_catalog:
        from archevolve.hardware_catalog import navigation_tree
        artifacts["catalog.navigation.yaml"] = yaml.safe_dump(navigation_tree(catalog), sort_keys=False, allow_unicode=True)
        artifacts["catalog.decision-questions.yaml"] = yaml.safe_dump(catalog["decision_questions"], sort_keys=False, allow_unicode=True)
    if methods_path is not None:
        artifacts["methodology.snapshot.yaml"] = methods_path.read_text()
    if source_context_path is not None:
        artifacts["source-context.snapshot.yaml"] = source_context_path.read_text()
    artifacts["manifest.json"] = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    catalog_note = ("Eric's source/version/configuration catalog is queried per operation. Interfaces and requirements remain scoped to the cited evidence; the diagrams do not establish physical partitioning, legal composition, or performance."
                    if evidence_catalog else "The catalog is the historical provisional family seed; its hardware partitions/ports have not been reviewed as implementations.")
    report = ["# Offline BFS exploration", "", "**Offline prototype: no LLM calls, no benchmark execution, and no evaluated speedups.**", "",
              "Each case is normalized separately. The original reports are retained unchanged. " + catalog_note, "",
              "| Case | Selected for exploration | Results |", "|---|---|---|"]
    for c in cases:
        f = c["folder"]
        selected = ", ".join(c["selected_entries"]) or "none"
        handoff_links = f", [intrinsic drafts]({f}/handoffs/README.md), [comparison]({f}/hardware-comparison.md)" if evidence_catalog else ""
        report.append(f"| {table_text(c['case_id'])} | {table_text(selected)} | [Diagrams]({f}/diagrams/README.md), [normalized input]({f}/normalized.yaml), [request YAML]({f}/hardware-request.yaml), [selection trace]({f}/selection-trace.yaml){handoff_links} |")
    report += ["", "## Input findings", ""]
    for i, c in enumerate(cases, 1):
        report.append(f"### Case {i}")
        report.append("")
        report.extend("- **" + table_text(issue["severity"]) + ":** " + table_text(issue["message"]) for issue in c["issues"])
        report.append("")
    report += ["## Next handoff", "", "Bind raw profile evidence to the relevant source, dataset, trial, and ROI. Use the catalog's exact result, validity, ordering, completion and requirement records to establish a concrete mapping with Eric and Peter. Reference parameters are not selected tuning values. No physical composition or executable rewrite is implied by a query match.", ""]
    artifacts["README.md"] = "\n".join(report)
    return artifacts, manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", type=Path, required=True, help="Schema-1.1 TDStep YAML (report revisions v1.1/v1.2); repeat for separate cases")
    parser.add_argument("--catalog", type=Path, default=Path("catalog/hardware-v0.1.yaml"))
    parser.add_argument("--methods", type=Path, help="Optional reported methodology, bound to exact input hashes")
    parser.add_argument("--source-context", type=Path, help="Explicit source observations/bindings; only matched file/function/revision context is used")
    parser.add_argument("--compare-design", action="append", help="Catalog design ID for same-request comparison; repeat, independent of candidate budget")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-candidates", type=int, default=4, help="Includes CPU comparison plus operation-interface exploration candidates")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        artifacts, manifest = prepare_run(args.input, args.catalog, max_candidates=args.max_candidates, methods_path=args.methods,
                                          source_context_path=args.source_context, compare_design_ids=args.compare_design)
        protected = {p.resolve() for p in [*args.input, args.catalog, *([args.methods] if args.methods else []),
                                          *([args.source_context] if args.source_context else [])]}
        targets = [args.output_dir / name for name in artifacts]
        if any(p.resolve() in protected for p in targets):
            raise RequestError("Output would overwrite an input or catalog; use a separate directory.")
        existing = [str(p) for p in targets if p.exists()]
        if existing and not args.overwrite:
            raise RequestError("Output files already exist; choose a new directory or use --overwrite.")
        for name, text in artifacts.items():
            path = args.output_dir / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        print(f"Completed {len(manifest['cases'])} offline case(s); no API calls. Results: {args.output_dir / 'README.md'}")
        for case in manifest["cases"]:
            print(case["case_id"] + ": " + ", ".join(case["selected_entries"]))
        return 0
    except (RequestError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
