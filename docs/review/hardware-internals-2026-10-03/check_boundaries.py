"""Independent, local-only annotation boundary review; no simulation or writes."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from archevolve.hardware_catalog import query_catalog, validate_catalog

BASE = "ef155cd621c466000b5beb910eb66a217a72b50d"
IDS = {"dx100-paper-v2", "dx100-artifact-e4fc4af", "terminus-micro2024-cas",
       "terminus-micro2024-deferred", "prodigy-hpca2021", "spzip-isca2021-push"}


def check_boundaries(before, after):
    validate_catalog(after)
    old = {d["id"]: d for d in before["designs"]}
    new = {d["id"]: d for d in after["designs"]}
    assert old.keys() == new.keys(), "design identity changed"
    for did in old:
        a, b = deepcopy(old[did]), deepcopy(new[did])
        if did in IDS:
            for key in ("internal_mechanisms", "performance_hypotheses"):
                a.pop(key, None)
                b.pop(key, None)
            if did == "dx100-artifact-e4fc4af":
                assert set(a.pop("source_refs")) <= set(b.pop("source_refs"))
        assert a == b, f"typed contract/reference parameter changed: {did}"
    for did in IDS:
        design = new[did]
        expected = "code_inspection" if did == "dx100-artifact-e4fc4af" else "paper_specification"
        for mechanism in design.get("internal_mechanisms", []):
            for ref in mechanism["claim_refs"]:
                claim = after["claims"][ref]
                assert claim["evidence_kind"] == expected, f"edition kind leak: {did}/{ref}"
                assert set(claim["source_refs"]) <= set(design["source_refs"]), f"source edition leak: {did}/{ref}"
                assert ref != "omi-spzip-ablation", "PHI evidence attached to selected Push"
        for hypothesis in design.get("performance_hypotheses", []):
            assert "omi-spzip-ablation" not in hypothesis["claim_refs"], "PHI hypothesis attached to Push"
    for ref, claim in before["claims"].items():
        assert after["claims"][ref] == claim, f"preexisting claim changed: {ref}"


def main():
    before = yaml.safe_load(subprocess.check_output(["git", "show", BASE + ":catalog/hardware-v0.1.yaml"], cwd=ROOT))
    after = yaml.safe_load((ROOT / "catalog/hardware-v0.1.yaml").read_text())
    check_boundaries(before, after)
    comparable = deepcopy(before)
    comparable["revision"] = after["revision"]
    count = 0
    for did in IDS:
        for operation, subtype in [("read", "gather"), ("read", "prefetch"), ("read", "stream_load"),
                                   ("read_modify_write", "cas"), ("read_modify_write", "destination_atomic_update")]:
            for role in [None, "execute", "assist"]:
                for old_value in [False, True]:
                    args = dict(design_id=did, operation=operation, subtype=subtype,
                                execution_role=role, require_old_value=old_value)
                    assert query_catalog(comparable, **args) == query_catalog(after, **args), args
                    count += 1
    mutations = []
    def reject(label, mutate):
        bad = deepcopy(after)
        mutate(bad)
        try:
            check_boundaries(before, bad)
        except (AssertionError, ValueError):
            mutations.append(label)
        else:
            raise AssertionError("boundary mutation escaped: " + label)
    def design(c, did):
        return next(d for d in c["designs"] if d["id"] == did)
    reject("public model evidence promoted into paper", lambda c: design(c, "dx100-paper-v2")["internal_mechanisms"][0].update(claim_refs=["dx-internal-c13"]))
    reject("prefetch promoted to required gather", lambda c: design(c, "prodigy-hpca2021")["operations"][0].update(execution_role="execute", subtype="gather"))
    reject("reference capacity promoted to legal range", lambda c: design(c, "terminus-micro2024-cas")["parameters"][0].update(domain=[64, 256]))
    reject("CPU-deferred CAS promoted to engine execution", lambda c: design(c, "terminus-micro2024-deferred")["operations"][-1].update(execution_role="execute"))
    reject("Push destination assistance promoted to execution", lambda c: design(c, "spzip-isca2021-push")["operations"][-1].update(execution_role="execute"))
    if "omi-spzip-access" in after["claims"]:
        def attach_phi(c):
            evidence = json.loads(Path(__file__).with_name("source-checks.json").read_text())["excluded_phi_claim"]
            c["claims"]["omi-spzip-ablation"] = evidence
            design(c, "spzip-isca2021-push")["internal_mechanisms"][0].update(claim_refs=["omi-spzip-ablation"])
        reject("PHI evidence promoted into Push", attach_phi)
        reject("same-kind evidence from another paper", lambda c: design(c, "spzip-isca2021-push")["internal_mechanisms"][0].update(claim_refs=["omi-prod-finite"]))
    from archevolve.__main__ import reference_context
    from archevolve.comparison import build_comparison_artifacts
    from archevolve.hardware_catalog import load_catalog
    from archevolve.intrinsic_handoff import md
    from archevolve.normalize import load_normalized
    from archevolve.select import select_candidates
    path = ROOT / "catalog/hardware-v0.1.yaml"
    _, digest = load_catalog(path)
    case = load_normalized(ROOT / "examples/received/bfs-sparse.features.v1.2.yaml", reference_context(ROOT))
    request, _ = select_candidates(case, after, str(path), digest, 1)
    artifacts = build_comparison_artifacts(request, after, sorted(IDS))
    rendered = yaml.safe_load(artifacts["hardware-comparison.yaml"])
    assert rendered["performance_evaluated"] is False and rendered["speedup"] is None
    records = {d["id"]: d for d in after["designs"]}
    for record in rendered["designs"]:
        original = records[record["design_id"]]
        annotations = record["mechanism_context"]["annotations"]
        assert annotations[:len(original["internal_mechanisms"])] == original["internal_mechanisms"]
        assert all(item["status"] == "unknown" and item["description"] is None and not item["claim_refs"]
                   for item in annotations[len(original["internal_mechanisms"]):])
        for item in original["internal_mechanisms"] + original.get("performance_hypotheses", []):
            for ref in item["claim_refs"]:
                assert record["source_evidence"]["claims"][ref] == after["claims"][ref]
            if item.get("description"):
                assert md(item["description"]) in artifacts["hardware-comparison.md"]
    print(json.dumps({"reviewed_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                      "boundary_queries": count, "rejected_mutations": mutations,
                      "rendered_designs_with_exact_evidence": len(rendered["designs"]), "status": "PASS"}, indent=2))


if __name__ == "__main__":
    main()
