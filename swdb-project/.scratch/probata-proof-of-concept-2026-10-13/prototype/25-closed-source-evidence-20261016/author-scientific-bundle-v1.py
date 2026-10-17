"""Normalize retained JSON metadata only; never import SWDB or run external tools."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path


BASE = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "scientific-bundle-v1"
MAX_DOCUMENT = 4 * 1024 * 1024
MAX_BUNDLE = 16 * 1024 * 1024
ORIGINS: dict[str, dict] = {}
DOCUMENTS: dict[str, dict] = {}
PROVENANCE: dict[str, list[dict]] = {}


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    path = Path(path)
    data = path.read_bytes()
    pin = {"historical_path": str(path), "sha256": sha(data), "bytes": len(data)}
    ORIGINS[str(path)] = pin
    return json.loads(data), pin


def store(value, origin=None, pointer=""):
    data = encoded(value)
    assert len(data) <= MAX_DOCUMENT, ("document cap", len(data))
    digest = sha(data)
    ref = {"path": f"objects/{digest}.json", "sha256": digest, "bytes": len(data)}
    path = OUT / ref["path"]
    if path.exists():
        assert path.read_bytes() == data
    else:
        path.write_bytes(data)
    DOCUMENTS[digest] = ref
    if origin is not None:
        row = {"source_document": origin, "pointer": pointer, "operation": "JSON value preserved; canonical JSON serialization"}
        if row not in PROVENANCE.setdefault(digest, []):
            PROVENANCE[digest].append(row)
    return ref


def location(document, pointer=""):
    return {"document": document, "pointer": pointer}


def copy(path):
    value, origin = load(path)
    return value, store(value, origin)


def field_documents(value, origin, prefix="", exclude=()):
    return {key: store(item, origin, prefix + "/" + key.replace("~", "~0").replace("/", "~1"))
            for key, item in value.items() if key not in exclude}


def ptr(value):
    return str(value).replace("~", "~0").replace("/", "~1")


def require_targets(component, canonical, required):
    targets = canonical["obligations"]
    by_id = {target["id"]: (index, target) for index, target in enumerate(targets)}
    assert len(by_id) == len(targets)
    result = []
    for target in required:
        index, actual = by_id[target["id"]]
        assert actual["sha256"] == target["sha256"], (component, target["id"], "canonical input differs")
        if "goal" in target:
            assert actual["goal"] == target["goal"]
        assert actual["kind"] in ("check_lemma", "c_kernel")
        assert isinstance(actual["statement"], str) or (actual["kind"] == "c_kernel" and actual["statement"] is None)
        result.append((index, actual))
    return result


def target_descriptor(obligation, index, canonical_ref, observation):
    assert observation.get("normal_verdict", observation.get("reconstructed_normal_verdict")) == "proven"
    return {"id": obligation["id"], "input_sha256": obligation["sha256"],
            "kind": obligation["kind"], "goal": obligation["goal"], "statement": obligation["statement"],
            "canonical_obligation": location(canonical_ref, f"/obligations/{index}"),
            "observation": observation}


def outcome_file(raw_manifest, ident):
    matches = [row for row in raw_manifest if row["relative"].endswith(f"/leaf-{ident}/outcome.json")]
    assert len(matches) == 1, (ident, "outcome raw pin")
    return matches[0]


def raw_method(raw_manifest):
    matches = [(i, row) for i, row in enumerate(raw_manifest) if row["relative"].endswith("/method.json")]
    assert len(matches) == 1
    return matches[0]


def main():
    assert not OUT.exists(), "v1 output already exists; never overwrite frozen evidence"
    (OUT / "objects").mkdir(parents=True)
    requirements_path = BASE / "prototype/25-closed-source-evidence-20261016/inert-reviewed-working-source-v3/manifest.json"
    requirements, requirements_ref = copy(requirements_path)
    deps = requirements["scientific_dependencies"]
    components = []

    reuse_physical, reuse_physical_ref = copy(BASE / "evidence/t25-closed-lifetime-dependency-reuse-physical-v1-20261016.json")
    reuse_eligibility, reuse_eligibility_ref = copy(BASE / "evidence/t25-closed-lifetime-dependency-reuse-eligibility-20261016.json")
    assert reuse_physical["cases"][0]["name"] == "ctor35"
    assert reuse_physical["cases"][1]["name"] == "dtor11"

    # The large retained constructor capture is split by its original top-level
    # metadata fields. Every value is retained, including full task/hash/context
    # metadata; no source C, solver file, AST, or task text is opened or copied.
    capture, capture_origin = load("/private/tmp/probata-root-ctor35-metadata-execution-v2-20261016.json")
    ctor = capture["metadata"]
    ctor_fields = field_documents(ctor, capture_origin, "/metadata")
    ctor_envelope = store({key: value for key, value in capture.items() if key != "metadata"}, capture_origin)
    ctor_canonical, ctor_canonical_ref = copy("/private/tmp/probata-t25-ctor35-preparer-only-v2-6216fc94-20261016/canonical/manifest.json")
    ctor_policy, ctor_policy_origin = load("/private/tmp/probata-t25-ctor35-cold-policy-v1-20261016.json")
    ctor_policy_ref = store(ctor_policy, ctor_policy_origin)
    ctor_root, ctor_root_ref = copy(BASE / "evidence/t25-ctor35-root-scoped-acceptance-v1-20261016.json")
    ctor_cold, ctor_cold_ref = copy(BASE / "evidence/root-ctor35-cold-execution-v1-20261016.json")
    ctor_independent, ctor_independent_ref = copy(BASE / "evidence/t25-ctor35-independent-cold-reconciliation-v1-20261016.json")
    assert ctor_root["qualified_constructor_mathematical_profile_accepted"] is True
    assert ctor["source_commit"] == ctor_root["source_commit"] == reuse_physical["cases"][0]["source_commit"]
    assert ctor["raw_preservation"]["pre_post_equal"] is True
    ctor_runs = {run["id"]: (index, run) for index, run in enumerate(ctor["runs"])}
    ctor_targets = []
    for index, obligation in require_targets("constructor", ctor_canonical, deps["constructor"]["required_targets"]):
        run_index, run = ctor_runs[obligation["id"]]
        assert run["input"]["sha256"] == obligation["sha256"]
        normal = run["record_run_metadata"]
        assert normal["verdict"] == normal["reading"]["verdict"] == "proven"
        reconciliation = run["goal_reconciliation"]
        assert reconciliation["kind"] == obligation["kind"]
        inventory = run["native_inventory"]["content"]
        assert inventory["complete"] and run["native_inventory"]["all_origins_and_targets_closed"]
        native_by_goal = [{"goal": goal["goal"], "property": goal["property"], "smoke": goal["smoke"],
                           "results": goal["inventory_results"], "native_verdict": goal["native_verdict"],
                           "native_report_present": goal["native_report_present"], "passed": goal["inventory_passed"]}
                          for goal in reconciliation["goals"]]
        obs = {"normal_verdict": normal["verdict"], "reader_check": normal["reading"]["check"],
               "native_results": native_by_goal[0]["results"] if len(native_by_goal) == 1 else None,
               "native_results_by_goal": native_by_goal,
               "ordinary": reconciliation["normalized_ordinary"], "smoke": reconciliation["normalized_smoke"],
               "properties": len(inventory["properties"]), "CSV_rows": len(run["properties_csv"]["rows"]),
               "native_report_rows": reconciliation["native_report_rows"],
               "native_report_verdicts": reconciliation["native_report_verdicts"],
               "inventory_only_ordinary": reconciliation["inventory_only_ordinary"],
               "evidence": location(ctor_fields["runs"], f"/{run_index}")}
        ctor_targets.append(target_descriptor(obligation, index, ctor_canonical_ref, obs))
    components.append({"id": "constructor", "targets": ctor_targets,
        "historical_identity": {"source_commit": ctor["source_commit"], "raw_root": ctor["raw"],
            "method_id": ctor["record"]["content"]["pins"]["method_version"]["id"],
            "method_version": ctor["record"]["content"]["pins"]["method_version"],
            "method_artifact": {k: ctor["method"][k] for k in ("path", "sha256", "bytes")},
            "reader_check": ctor["record"]["content"]["verdict_reading"]["check"],
            "domain": ctor["canonical"]["model"],
            "source_context": location(ctor_canonical_ref), "expected": location(ctor_policy_ref, "/expected")},
        "accepted_decision": location(ctor_root_ref),
        "accepted_subset": {"target_ids": [t["id"] for t in ctor_targets], "all_historical_targets": True,
                            "scope": ctor_root["scope"]},
        "cold_evidence": [location(ctor_cold_ref), location(ctor_independent_ref), location(reuse_physical_ref, "/cases/0"), location(reuse_eligibility_ref)],
        "context": {"source_rule_requirements": location(requirements_ref, "/scientific_dependencies/constructor"),
                    "canonical_manifest": location(ctor_canonical_ref), "cold_policy": location(ctor_policy_ref),
                    "capture_envelope": location(ctor_envelope), "capture_metadata_fields": ctor_fields},
        "boundaries": {"numeric_ordinary_inventory_only": 2, "numeric_nonvalid_smoke_is_not_a_theorem": True,
                       "historical_record_relabelled": False, "current_body_record_admitted": False}})

    # Destructor policy contains raw canonical C/theory strings and a bootstrap
    # recipe. Those fields stay at their original retained paths and are hash-
    # described only. Complete JSON reports, records, task metadata and context
    # fields are retained, without interpreting historical path payloads.
    dtor, dtor_origin = load("/private/tmp/probata-t25-dtor11-cold-policy-v1-20261016.json")
    omitted = ("canonical_C", "canonical_theory", "recipe_command")
    dtor_fields = field_documents(dtor, dtor_origin, exclude=omitted)
    dtor_exclusions = store({key: {"canonical_json_sha256": sha(encoded(dtor[key])),
                                  "canonical_json_bytes": len(encoded(dtor[key])),
                                  "reason": "Raw source/theory or bootstrap command stays outside the JSON evidence bundle"}
                             for key in omitted}, dtor_origin)
    dtor_canonical = dtor["canonical_manifest"]
    dtor_canonical_ref = dtor_fields["canonical_manifest"]
    dtor_root, dtor_root_ref = copy(BASE / "evidence/t25-dtor11-scoped-root-decision-20261016.json")
    dtor_cold, dtor_cold_ref = copy(BASE / "evidence/t25-dtor11-cold-root-execution-v1-20261016.json")
    dtor_independent, dtor_independent_ref = copy(BASE / "evidence/t25-dtor11-independent-cold-decision-20261016.json")
    assert dtor_cold["result"]["all11_complete"] is True
    assert dtor["source_commit"] == dtor_root["source_commit"] == reuse_physical["cases"][1]["source_commit"]
    dtor_runs = {run["id"]: (index, run) for index, run in enumerate(dtor["record"]["settings"]["heap_model_runs"])}
    dtor_targets = []
    for index, obligation in require_targets("destructor", dtor_canonical, deps["destructor"]["required_targets"]):
        run_index, run = dtor_runs[obligation["id"]]
        assert run["input_sha256"] == obligation["sha256"] and run["verdict"] == run["reading"]["verdict"] == "proven"
        suffix = "/heap-job-" + obligation["id"] + "/wp-inventory.json"
        matches = [(key, value) for key, value in dtor["metadata"]["files"].items() if key.endswith(suffix)]
        assert len(matches) == 1
        inventory_key, inventory_doc = matches[0]
        inventory = inventory_doc["content"]
        assert inventory["complete"] and len(inventory["goals"]) == 1
        native = inventory["goals"][0]
        assert native["passed"] and not native["smoke"] and "valid" in native["results"]
        census = next(row for row in dtor_cold["result"]["actual_target_censuses"] if row["target"] == obligation["id"])
        assert census["portfolio_results"] == native["results"] and census["direct_valid"]
        obs = {"normal_verdict": run["verdict"], "reader_check": run["reading"]["check"],
               "native_results": native["results"], "ordinary": census["ordinary"], "smoke": census["smokes"],
               "properties": census["properties"], "CSV_rows": census["CSV_rows"],
               "native_report_rows": 1, "inventory_only_ordinary": 0, "solver": census["solver"],
               "evidence": location(dtor_fields["record"], f"/settings/heap_model_runs/{run_index}"),
               "native_evidence": location(dtor_fields["metadata"], "/files/" + ptr(inventory_key)),
               "cold_census": location(dtor_cold_ref, "/result/actual_target_censuses/" + str(dtor_cold["result"]["actual_target_censuses"].index(census)))}
        dtor_targets.append(target_descriptor(obligation, index, dtor_canonical_ref, obs))
    components.append({"id": "destructor", "targets": dtor_targets,
        "historical_identity": {"source_commit": dtor["source_commit"], "raw_root": dtor["raw"],
            "method_id": dtor["record"]["pins"]["method_version"]["id"],
            "method_version": dtor["record"]["pins"]["method_version"],
            "method_artifact": location(dtor_fields["metadata"], "/files/qualified-dtor11-profile~1method-model-binding.json/content/method_version"),
            "reader_check": dtor["record"]["verdict_reading"]["check"], "domain": dtor_canonical["model"],
            "source_context": location(dtor_canonical_ref), "expected": location(dtor_fields["expected"])},
        "accepted_decision": location(dtor_root_ref),
        "accepted_subset": {"target_ids": [t["id"] for t in dtor_targets], "all_historical_targets": True, "scope": dtor_root["scope"]},
        "cold_evidence": [location(dtor_cold_ref), location(dtor_independent_ref), location(reuse_physical_ref, "/cases/1"), location(reuse_eligibility_ref)],
        "context": {"source_rule_requirements": location(requirements_ref, "/scientific_dependencies/destructor"),
                    "canonical_manifest": location(dtor_canonical_ref), "retained_policy_fields": dtor_fields,
                    "excluded_raw_payload_descriptors": location(dtor_exclusions)},
        "boundaries": {"broad_pointer_domain_preserved": True, "typed_int_buffer_domain_added": False,
                       "original_root_model_acceptance": False, "historical_record_relabelled": False,
                       "current_body_record_admitted": False}})

    specs = [
        ("private_frame", "private_frame", "25-private-lifetime-frame-20261016/inert-f918f5d5-public-v1", "t25-private-frame9-passive-cold-metadata-v3-20261016.json", "t25-private-frame9-root-scoped-acceptance-20261016.json", "t25-private-frame9-independent-cold-decision-20261016.json"),
        ("gluing", "unchanged_gluing", "25-closed-lifetime-glue-20261016/inert-fb197c5d-public-v1", "t25-closed-lifetime6-passive-cold-metadata-v6-20261016.json", "t25-closed-lifetime4-root-scoped-acceptance-20261016.json", "t25-closed-lifetime6-independent-cold-decision-20261016.json"),
        ("positive", "positive_conjunctions", "25-closed-lifetime-parts-20261016/inert-04af74c1-public-v1", "t25-closed-lifetime23-passive-cold-metadata-v1-20261016.json", "t25-closed-lifetime23-root-scoped-acceptance-20261016.json", "t25-closed-lifetime23-independent-cold-decision-20261016.json"),
    ]
    for component_id, requirement_key, frozen, metadata_name, root_name, independent_name in specs:
        expected, expected_ref = copy(BASE / "prototype" / frozen / "expected.json")
        canonical_key = "canonical_manifest_portable" if "canonical_manifest_portable" in expected else "canonical_manifest"
        canonical = expected[canonical_key]
        canonical_ref = store(canonical, ORIGINS[str(BASE / "prototype" / frozen / "expected.json")], "/" + canonical_key)
        metadata, metadata_ref = copy(BASE / "evidence" / metadata_name)
        root, root_ref = copy(BASE / "evidence" / root_name)
        independent, independent_ref = copy(BASE / "evidence" / independent_name)
        assert metadata["source_commit"] == root["source_commit"] == expected["source_commit"]
        assert metadata["raw_pre_post_equal"] and metadata["sourceafter_clean"]
        required = deps[requirement_key]["required_targets"] if isinstance(deps[requirement_key], dict) else deps[requirement_key]
        targets = []
        for index, obligation in require_targets(component_id, canonical, required):
            leaf_index, leaf = next((i, row) for i, row in enumerate(metadata["leaves"]) if row["id"] == obligation["id"])
            assert leaf["input"]["sha256"] == obligation["sha256"]
            assert leaf["ordinary"] == 1 and leaf["smoke"] == 0 and leaf["properties"] == 2 and leaf["CSV_rows"] == 0
            assert "valid" in leaf["native_results"]
            obs = {"normal_verdict": leaf.get("normal_verdict", "proven"), "reader_check": metadata["reader_check"],
                   "native_results": leaf["native_results"], "ordinary": leaf["ordinary"], "smoke": leaf["smoke"],
                   "properties": leaf["properties"], "CSV_rows": leaf["CSV_rows"],
                   "native_report_rows": 1, "inventory_only_ordinary": 0,
                   "evidence": location(metadata_ref, f"/leaves/{leaf_index}"),
                   "outcome_artifact": outcome_file(metadata["raw_manifest"], obligation["id"])}
            if component_id == "private_frame":
                assert "normal_verdict" not in leaf
                obs["reconstructed_normal_verdict"] = obs.pop("normal_verdict")
                auditor_path = BASE / "evidence/t25-private-frame9-passive-cold-audit-20261016.py"
                auditor_bytes = auditor_path.read_bytes()
                assert sha(auditor_bytes) == "12cd78dcbdda5d7d8a1c7a2a60ef99992a6214ea1d22426b382a663771133250"
                assert b"outcome==run['outcome'] and outcome['verdict']=='proven'" in auditor_bytes
                assert b"outcome['reading']=={'check':reader_check,'verdict':'proven'}" in auditor_bytes
                obs["normal_verdict_basis"] = {"kind": "reviewed-passive-observer-assertion",
                    "auditor_sha256": sha(auditor_bytes), "lines": [314, 318],
                    "description": "The successful reviewed observer checked each retained outcome exactly against the producer result, normal proven with no assumptions/unproven and the exact current reader check. Its compact leaf payload omitted the already checked normal verdict field.",
                    "accepted_decision": location(root_ref), "result_artifact": metadata["result_pin"]}
                obs["solver"] = leaf["solver"]
            else:
                assert leaf["normal_verdict"] == "proven" and leaf["passed"] is True and leaf["failure_class"] is None
                obs["normal_verdict_basis"] = {"kind": "retained-leaf-field", "evidence": location(metadata_ref, f"/leaves/{leaf_index}/normal_verdict")}
                if "internal_qed_inventory_only" in leaf:
                    obs["internal_qed_inventory_only"] = leaf["internal_qed_inventory_only"]
            targets.append(target_descriptor(obligation, index, canonical_ref, obs))
        method_index, method_artifact = raw_method(metadata["raw_manifest"])
        component = {"id": component_id, "targets": targets,
            "historical_identity": {"source_commit": metadata["source_commit"], "raw_root": metadata["raw_root"],
                "method_id": expected["method_id"], "method_artifact": method_artifact,
                "method_artifact_evidence": location(metadata_ref, f"/raw_manifest/{method_index}"),
                "reader_check": metadata["reader_check"], "source_context": location(canonical_ref),
                "expected": location(expected_ref)},
            "accepted_decision": location(root_ref),
            "accepted_subset": {"target_ids": [t["id"] for t in targets], "all_historical_targets": component_id != "gluing", "scope": root["scope"] if "scope" in root else root["composition_boundary"]},
            "cold_evidence": [location(metadata_ref), location(independent_ref)],
            "context": {"source_rule_requirements": location(requirements_ref, "/scientific_dependencies/" + requirement_key),
                "canonical_manifest": location(canonical_ref), "frozen_expected": location(expected_ref),
                "complete_passive_metadata": location(metadata_ref), "complete_independent_decision": location(independent_ref),
                "tasks": location(metadata_ref, "/materialized_tasks"), "imports": location(metadata_ref, "/import_source_closure"),
                "runtime": location(metadata_ref, "/runtime_pins"), "raw_manifest": location(metadata_ref, "/raw_manifest"),
                "source_consumers": location(metadata_ref, "/source_consumers"), "guard": location(metadata_ref, "/guard"),
                "lane": location(metadata_ref, "/lane")},
            "boundaries": {"historical_record_relabelled": False, "current_body_record_admitted": False,
                "universal_setup_attested": False, "actual_submission_count": None}}
        if component_id == "private_frame":
            supplement, supplement_ref = copy(BASE / "evidence/t25-private-frame9-passive-cold-support-supplement-20261016.json")
            component["cold_evidence"].append(location(supplement_ref))
        if component_id == "gluing":
            assert root["accepted_conditional_goal_ids"] == [t["id"] for t in targets]
            rejected = [leaf for leaf in metadata["leaves"] if leaf["id"] not in root["accepted_conditional_goal_ids"]]
            assert [leaf["id"] for leaf in rejected] == ["positive.exit_image", "positive.cleanup"]
            assert all(leaf["normal_verdict"] == "not_proven" and leaf["native_results"] == ["timeout", "unknown", "timeout"] for leaf in rejected)
            component["accepted_subset"]["preserved_unaccepted_historical_outcomes"] = rejected
        components.append(component)

    assert [(c["id"], len(c["targets"])) for c in components] == [("constructor", 35), ("destructor", 11), ("private_frame", 9), ("gluing", 4), ("positive", 23)]
    catalog = {"schema_version": 1, "kind": "vector-closed-scientific-bundle", "created": "2026-10-16 ET",
        "classification": "Normalized retained conditional mathematical evidence; no source/caller admission",
        "required_target_count": 82, "components": components,
        "requirements": location(requirements_ref), "documents": sorted(DOCUMENTS.values(), key=lambda row: row["path"]),
        "document_provenance": PROVENANCE, "retained_origins": sorted(ORIGINS.values(), key=lambda row: row["historical_path"]),
        "gaps": [], "source_admission": False, "caller_acceptance": False, "proof_record_created": False,
        "historical_identity_policy": "Every method, source, setup, compiler, reader, solver, domain and raw path remains historical. Content-identical source targets are the only reuse unit. No historical aggregate identity is promoted to a current record.",
        "path_policy": "Only explicit document.path references are bundle files. Historical absolute paths are inert metadata and must never be opened by a bundle validator.",
        "evidence_boundary": "Accepted root decisions and reviewed cold observers supply conditional theorem evidence under their complete original TCB. Metadata hashes are not proofs; no scientific bundle/source bridge or caller admission is implemented here.",
        "nonblocking_representation_limits": [
            "Private9 normal proven is retained as an explicit reviewed-observer assertion basis with exact outcome/result raw pins; compact leaves did not repeat that field.",
            "Standalone method artifacts remain exact raw-manifest hash references with full historical expected/method policy and accepted source/runtime closure; no invented expanded method-version hash.",
            "Constructor numeric statement is canonically null because it is a C kernel; complete canonical input identity, native/normalized 11-goal census and accepted task context remain retained.",
            "Complete original raw stays remote. This bundle carries complete compact task/hash/import/context/raw manifests, not raw C, AST or SMT payloads."]}
    data = encoded(catalog)
    assert len(data) <= MAX_DOCUMENT
    (OUT / "catalog.json").write_bytes(data)
    total = len(data) + sum(row["bytes"] for row in DOCUMENTS.values())
    assert total <= MAX_BUNDLE, ("bundle cap", total)
    print(json.dumps({"catalog_sha256": sha(data), "catalog_bytes": len(data), "object_count": len(DOCUMENTS),
                      "total_bytes": total, "largest_document": max(row["bytes"] for row in DOCUMENTS.values()),
                      "components": [[row["id"], len(row["targets"])] for row in components], "gaps": []}, sort_keys=True))


if __name__ == "__main__":
    main()
