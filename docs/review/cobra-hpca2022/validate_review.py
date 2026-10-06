"""Independent identity bindings and adversarial consumer checks; no model runs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PROPOSAL = ROOT / "docs/proposals/cobra-hpca2022"
BASE = "5608d112667b72e971b3093325edda7454f579c8"
HEAD = "62cc6b6a658dcc09dfd42941953149516e75241b"
DESIGN = "cobra-hpca2022-tuple-binning"
sys.path.insert(0, str(ROOT))

from archevolve.__main__ import reference_context
from archevolve.comparison import build_comparison_artifacts, compare_designs
from archevolve.hardware_catalog import inspect_design, load_catalog, navigation_tree, query_catalog
from archevolve.intrinsic_handoff import build_handoff_artifacts
from archevolve.normalize import load_normalized
from archevolve.select import select_candidates


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git_bytes(revision, path):
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)


def main():
    identities = []
    # Bind the saved producer results before reusing their unchanged checks.
    for path in sorted(PROPOSAL.iterdir()):
        raw = path.read_bytes()
        relative = str(path.relative_to(ROOT))
        assert raw == git_bytes(HEAD, relative), relative
        identities.append(dict(path=relative, sha256=digest(raw), bytes=len(raw)))
    provenance = json.loads((PROPOSAL / "provenance.json").read_text())
    external = []
    for entry in provenance["sources"] + provenance["handoff_files"] + provenance["schema_files"]:
        raw = Path(entry["path"]).read_bytes()
        assert digest(raw) == entry["sha256"] and len(raw) == entry["bytes"], entry["path"]
        external.append(entry)
    for relative in ("archevolve/hardware_catalog.py", "docs/hardware-catalog-format.md",
                     "catalog/hardware-v0.1.yaml", "docs/proposals/drt-asplos2023/admission-decision.md",
                     "archevolve/evidence_select.py", "archevolve/comparison.py",
                     "archevolve/intrinsic_handoff.py", "tools/render_mermaid.py"):
        raw = (ROOT / relative).read_bytes()
        assert raw == git_bytes(BASE, relative) == git_bytes(HEAD, relative)
        identities.append(dict(path=relative, sha256=digest(raw), bytes=len(raw)))
    pdf = next(e["path"] for e in provenance["sources"] if e["id"] == "cobra-pdf")
    info = subprocess.check_output(["pdfinfo", pdf], text=True)
    assert next(line for line in info.splitlines() if line.startswith("Pages:")).split()[1] == "15"
    locators = []
    for page, markers in ((1, ["Improving Locality of Irregular Updates with Hardware Assisted Propagation Blocking", "Vignesh Balaji", "Brandon Lucia"]),
                          (3, ["Algorithm 2", "AtomicAdd", "Accumulate Phase"]),
                          (4, ["neighbors can be listed in any order"]),
                          (6, ["bininit", "four operands", "binupdate"]),
                          (7, ["not byte addressable", "FIFO", "core-private"]),
                          (8, ["binflush", "matching virtual and physical addresses", "mlock"]),
                          (9, ["Sniper", "head of the ROB", "Pin-based", "CACTI"]),
                          (11, ["Discrete Event Simulation", "single way in the L2"]),
                          (12, ["COBRA-COMM", "atomic LLC reduction unit"])):
        text = subprocess.check_output(["pdftotext", "-layout", "-f", str(page), "-l", str(page), pdf, "-"], text=True)
        normalized = " ".join(text.split())
        assert all(marker in normalized for marker in markers), (page, markers)
        locators.append(dict(pdf_page=page, checked_markers=markers))
    producer = json.loads((PROPOSAL / "validation.json").read_text())
    assert producer["base_commit"] == BASE and producer["production_admitted"] is False
    assert len(producer["query_checks"]) == 20
    assert all(x["unchanged_existing_entries"] for x in producer["query_checks"])
    assert producer["unchanged_existing_query_trials"] == 88
    assert producer["unchanged_existing_designs"] == 8 and producer["all_existing_records_unchanged"]
    addition = json.loads((PROPOSAL / "proposed-addition.json").read_text())
    current, catalog_digest = load_catalog(ROOT / "catalog/hardware-v0.1.yaml")
    trial = deepcopy(current)
    for field in ("sources", "claims"):
        trial[field].update(deepcopy(addition[field]))
    for field in ("mechanism_families", "decision_questions", "designs"):
        trial[field].extend(deepcopy(addition[field]))
    design = addition["designs"][0]
    op = design["operations"][0]
    assert inspect_design(trial, DESIGN) == design
    assert catalog_digest == producer["production_catalog_sha256"]
    rows = []
    # New combinations address possible broad-write promotion and constraint erasure.
    queries = [({"operation": "write", "execution_role": "execute"}, "mapping_reference"),
               ({"operation": "write", "require_old_value": True}, "excluded"),
               ({"operation": "write", "payload_type": "int32"}, "needs_evidence"),
               ({"operation": "write", "index_width_bits": 32}, "needs_evidence"),
               ({"operation": "write", "address_pattern": "indirect", "payload_type": "uint32",
                 "index_width_bits": 32}, "needs_evidence"),
               ({"operation": "write", "subtype": "tuple_bin", "address_pattern": "indirect",
                 "payload_type": "uint32", "index_width_bits": 32, "require_old_value": True}, "excluded")]
    queries += [({"operation": operation}, None) for operation in ("read", "read_modify_write", "reduce")]
    for query, status in queries:
        result = query_catalog(trial, **query)
        cobra = [m for m in result["matches"] + result["excluded"] if m["design_id"] == DESIGN]
        assert len(cobra) == (0 if status is None else 1)
        if cobra:
            assert cobra[0]["status"] == status
            assert cobra[0]["operation"] == op and cobra[0]["requirements"] == design["requirements"]
            assert cobra[0]["requirement_status"] == "not_discharged_by_retrieval"
        original = query_catalog(current, **query)
        for field in ("matches", "excluded"):
            assert [m for m in result[field] if m["design_id"] != DESIGN] == original[field]
        rows.append(dict(query=query, expected=status, observed_rows=len(cobra)))
    leaf = [x for x in navigation_tree(trial)["branches"]["write"]["mapping_reference"]["unknown"]
            if x["design_id"] == DESIGN][0]
    assert leaf["subtype"] == "tuple_bin" and leaf["requirement_ids"] == [r["id"] for r in design["requirements"]]

    case = load_normalized(ROOT / "examples/received/bfs-sparse.features.v1.2.yaml", reference_context(ROOT))
    # Ordinary consumers must not infer a tuple transformation from destination accesses.
    original, original_trace = select_candidates(case, current, "bound-catalog", catalog_digest, 12)
    ordinary, ordinary_trace = select_candidates(case, trial, "bound-catalog", catalog_digest, 12)
    assert original == ordinary and original_trace == ordinary_trace
    comparison = compare_designs(ordinary, trial, [DESIGN])["designs"][0]
    assert comparison["record_kind"] == "mapping" and comparison["requirements"] == design["requirements"]
    assert all(not q["matches"] for q in comparison["queries"])
    assert not comparison["conditionally_matched_read_requests"]

    consumers = []
    # Synthetic explicit tuple-bin intent tests projections, not BFS compatibility.
    for subtype in ("tuple_bin", None):
        intent = deepcopy(ordinary["capability_requests"][0])
        intent.update(operation="write", subtype=subtype, purpose="update", array="tuple_bins",
                      address_pattern="indirect", payload_type="uint32", index_width_bits=32,
                      require_old_value=False, mutable_target=False, statement_ids=[], source_locations=[],
                      statement_binding_status="unbound", missing_workload_evidence=[],
                      mapping_basis="Synthetic tuple materialization inspection; no workload equivalence established.")
        with patch("archevolve.evidence_select.capability_requests", return_value=([intent], [])):
            request, _ = select_candidates(case, trial, "bound-catalog", catalog_digest, 2, [DESIGN])
        candidate = request["candidates"][1]
        assert candidate["candidate_scope"] == "mapping_reference" and candidate["status"] == "needs_evidence"
        assert candidate["requirements"] == design["requirements"]
        assert candidate["execution_plan"]["rmw"] == "retain_original_CPU_update"
        assert candidate["selected_configuration"] == {}
        assert candidate["operation_options"][0]["operation"] == op
        assert candidate["source_evidence"]["sources"]["cobra-hpca2022-paper"] == addition["sources"]["cobra-hpca2022-paper"]
        artifacts = build_handoff_artifacts(request, catalog_digest)
        draft = yaml.safe_load(artifacts["candidate-02/intrinsic-draft.yaml"])
        projected = draft["operations"][0]
        assert projected["postconditions"]["catalog_result"] == op["result"]
        assert projected["postconditions"]["program_equivalence_status"] == "not_established"
        assert projected["ordering"] == op["ordering"] and projected["completion"] == op["completion"]
        assert projected["realization"] == op["realization"]
        assert projected["concrete_signature"] is None and projected["implementation_ref"] is None
        assert draft["requirements"] == design["requirements"] and draft["requirement_status"] == "not_discharged"
        assert draft["selected_configuration"] == {} and not draft["readiness"]["correctness_verified"]
        description = artifacts["candidate-02/README.md"]
        diagram = artifacts["candidate-02/interface.mmd"].replace("<br/>", " ")
        assert "no destination-array update" in description and "no destination-array update" in diagram
        assert "physical done/ack binding unspecified" in description
        assert "consumer-release-event" in diagram
        assert candidate["hardware"]["blocks"][0]["operation_contract"] == op
        compared = compare_designs(request, trial, [DESIGN])["designs"][0]
        match = compared["queries"][0]["matches"][0]
        assert match["status"] == "needs_evidence" and match["operation"] == op
        assert match["requirements"] == design["requirements"]
        assert compared["interface"] == design["interface"]
        comparison_artifacts = build_comparison_artifacts(request, trial, [DESIGN])
        structured = yaml.safe_load(comparison_artifacts["hardware-comparison.yaml"])
        assert structured["designs"][0] == compared
        consumers.append(dict(request_subtype=subtype, candidate_scope=candidate["candidate_scope"],
                              status=candidate["status"], full_operation_preserved=True,
                              handoff_contract_preserved=True, comparison_contract_preserved=True,
                              CPU_update_retained=True, synthetic_not_workload_legality=True))
    free = {str(path): shutil.disk_usage(path).free for path in (ROOT, Path("/tmp"))}
    assert all(n >= 16 * 1024**3 for n in free.values())
    changed = subprocess.check_output(["git", "diff", "--name-only", HEAD], cwd=ROOT, text=True).splitlines()
    assert all(p.startswith("docs/review/cobra-hpca2022/") for p in changed)
    report = dict(format="cobra-independent-review-validation-v1", proposal_commit=HEAD, base_commit=BASE,
                  verdict="APPROVE_SOURCE_SCOPED_MAPPING", production_admitted=False,
                  identities=identities, external_hash_bindings=external, primary_pdf_locators=locators,
                  reused_producer_checks=dict(query_checks=20, existing_query_checks=88, existing_designs=8,
                                             report_sha256=digest((PROPOSAL / "validation.json").read_bytes())),
                  adversarial_queries=rows, ordinary_candidates_and_trace_unchanged=True,
                  ordinary_comparison_has_no_COBRA_capability_match=True, consumer_projections=consumers,
                  broadening_reproducer=None, new_download_bytes=0, free_bytes=free,
                  scope="Evidence/representation/projection only; release ABI, OS support, workload/numeric legality and executable implementation remain unverified.")
    (HERE / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(verdict=report["verdict"], adversarial_queries=len(rows), consumer_projections=len(consumers),
                          reused_producer_queries=20, reused_existing_queries=88, production_admitted=False)))


if __name__ == "__main__":
    main()
