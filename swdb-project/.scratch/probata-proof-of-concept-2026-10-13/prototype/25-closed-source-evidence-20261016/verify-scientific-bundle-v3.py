"""Pure retained-metadata integrity controls; no project imports or child process."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
BUNDLE = HERE / "scientific-bundle-v3"
CATALOG = BUNDLE / "catalog.json"


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pointer(value, path):
    if not path:
        return value
    assert path.startswith("/")
    for key in path[1:].split("/"):
        assert not re.search(r"~[^01]|~$", key)
        key = key.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def document(ref):
    assert set(ref) == {"path", "sha256", "bytes"}
    assert re.fullmatch(r"objects/[0-9a-f]{64}\.json", ref["path"])
    assert ref["path"] == "objects/" + ref["sha256"] + ".json"
    data = (BUNDLE / ref["path"]).read_bytes()
    assert len(data) == ref["bytes"] <= 4 * 1024 * 1024
    assert digest(data) == ref["sha256"]
    return json.loads(data)


def resolve(value):
    assert set(value) == {"document", "pointer"}
    return pointer(document(value["document"]), value["pointer"])


def check_reference_closure(value, locations):
    if isinstance(value, dict):
        if set(value) == {"document", "pointer"}:
            resolve(value)
            locations.append(value)
        elif set(value) == {"path", "sha256", "bytes"} and value["path"].startswith("objects/"):
            document(value)
        for item in value.values():
            check_reference_closure(item, locations)
    elif isinstance(value, list):
        for item in value:
            check_reference_closure(item, locations)


def metadata_checks(catalog):
    assert catalog["schema_version"] == 1 and catalog["kind"] == "vector-closed-scientific-bundle"
    assert catalog["gaps"] == [] and catalog["required_target_count"] == 82
    assert all(catalog[key] is False for key in ("source_admission", "caller_acceptance", "proof_record_created"))
    expected = [("constructor", 35), ("destructor", 11), ("private_frame", 9), ("gluing", 4), ("positive", 23)]
    assert [(c["id"], len(c["targets"])) for c in catalog["components"]] == expected
    refs = {row["path"]: row for row in catalog["documents"]}
    assert len(refs) == len(catalog["documents"])
    assert set(refs) == {str(path.relative_to(BUNDLE)) for path in (BUNDLE / "objects").iterdir()}
    assert {path.name for path in BUNDLE.iterdir()} == {"catalog.json", "objects"}
    for ref in refs.values():
        document(ref)
    locations = []
    check_reference_closure(catalog, locations)
    for ref in refs.values():
        # Inner raw metadata is payload, never recursively interpreted as file
        # references. Catalog locations are the sole portable document interface.
        assert set(ref) == {"path", "sha256", "bytes"}
    sources = {}
    operations = {}
    for ref_hash, provenance in catalog["document_provenance"].items():
        value = document(refs["objects/" + ref_hash + ".json"])
        for row in provenance:
            source_pin = row["source_document"]
            source_path = source_pin["historical_path"]
            if source_path not in sources:
                raw = Path(source_path).read_bytes()
                assert len(raw) == source_pin["bytes"] and digest(raw) == source_pin["sha256"]
                sources[source_path] = json.loads(raw)
            source = pointer(sources[source_path], row["pointer"])
            operation = row["operation"]
            operations[operation] = operations.get(operation, 0) + 1
            if operation == "JSON value preserved; canonical JSON serialization":
                assert value == source, source_path
            elif operation.startswith("top-level-object-subset:"):
                assert value == {key: item for key, item in source.items() if key != "metadata"}
            elif operation.startswith("derived-excluded-raw-field-descriptors:"):
                assert set(value) == {"canonical_C", "canonical_theory", "recipe_command"}
                for key, descriptor in value.items():
                    assert descriptor["canonical_json_sha256"] == digest(encode(source[key]))
                    assert descriptor["canonical_json_bytes"] == len(encode(source[key]))
            else:
                raise AssertionError("unknown provenance operation")
    assert len(operations) == 3
    requirements = resolve(catalog["requirements"])["scientific_dependencies"]
    keys = {"constructor": "constructor", "destructor": "destructor", "private_frame": "private_frame", "gluing": "unchanged_gluing", "positive": "positive_conjunctions"}
    ordinary = smoke = properties = inventory_only = native_rows = direct_valid = 0
    summaries = []
    for component in catalog["components"]:
        name = component["id"]
        required = requirements[keys[name]]
        if isinstance(required, dict):
            required = required["required_targets"]
        assert [(row["id"], row["input_sha256"]) for row in component["targets"]] == [(row["id"], row["sha256"]) for row in required]
        canonical = resolve(component["context"]["canonical_manifest"])
        assert component["accepted_subset"]["target_ids"] == [row["id"] for row in component["targets"]]
        root = resolve(component["accepted_decision"])
        assert root["source_commit"] == component["historical_identity"]["source_commit"]
        method_artifact = component["historical_identity"]["method_artifact"]
        assert set(method_artifact).issuperset({"path", "sha256", "bytes"})
        assert method_artifact["path"].startswith(component["historical_identity"]["raw_root"] + "/")
        if name == "constructor":
            assert root["qualified_constructor_mathematical_profile_accepted"] is True
            assert root["ordinary_current_model_dependency_admitted"] is False
            assert root["generic_caller_acceptance"] is root["original_v2_acceptance"] is False
        elif name == "destructor":
            assert root["ordinary_direct_valid"] == 11 and root["no_original_record_rewritten"] is True
            assert root["original_root_reader_model_acceptance"] is root["caller_acceptance"] is False
        elif name == "private_frame":
            assert root["native_ordinary_direct_valid"] == 9
            assert root["body_or_caller_acceptance"] is root["source_Typed_bridge"] is False
        elif name == "gluing":
            assert root["accepted_conditional_goal_ids"] == component["accepted_subset"]["target_ids"]
            assert root["all_six_acceptance"] is False and root["normal_timeout_goals"] == 2
            rejected = component["accepted_subset"]["preserved_unaccepted_historical_outcomes"]
            assert [row["id"] for row in rejected] == ["positive.exit_image", "positive.cleanup"]
            assert all(row["normal_verdict"] == "not_proven" and row["native_results"] == ["timeout", "unknown", "timeout"] for row in rejected)
        elif name == "positive":
            assert len(root["leaves"]) == 23 and root["historical_two_compound_timeouts_preserved"] is True
            assert root["body_or_caller_acceptance"] is root["source_Typed_bridge"] is False
        for target in component["targets"]:
            obligation = resolve(target["canonical_obligation"])
            assert obligation in canonical["obligations"]
            for field in ("id", "kind", "goal", "statement"):
                assert target[field] == obligation[field]
            assert target["input_sha256"] == obligation["sha256"]
            obs = target["observation"]
            assert obs["reader_check"] == component["historical_identity"]["reader_check"]
            evidence = resolve(obs["evidence"])
            if name == "constructor":
                assert evidence["id"] == target["id"] and evidence["input"]["sha256"] == target["input_sha256"]
                assert obs["normal_verdict"] == evidence["record_run_metadata"]["verdict"] == "proven"
                assert obs["reader_check"] == evidence["record_run_metadata"]["reading"]["check"]
                recon = evidence["goal_reconciliation"]
                assert obs["ordinary"] == recon["normalized_ordinary"] and obs["smoke"] == recon["normalized_smoke"]
                assert obs["inventory_only_ordinary"] == recon["inventory_only_ordinary"]
                assert obs["native_report_rows"] == recon["native_report_rows"]
                for goal, observed in zip(recon["goals"], obs["native_results_by_goal"], strict=True):
                    assert observed["results"] == goal["inventory_results"]
                    assert observed["native_report_present"] == goal["native_report_present"]
                    if goal["smoke"]:
                        assert target["id"] == "ctor.numeric" and goal["native_verdict"] == "timeout"
                        assert goal["inventory_results"] == ["timeout", "unknown", "timeout"]
                    else:
                        assert goal["inventory_passed"] and "valid" in goal["inventory_results"]
                    direct_valid += int(goal["native_report_present"] and not goal["smoke"] and goal["native_verdict"] == "valid")
            elif name == "destructor":
                assert evidence["id"] == target["id"] and evidence["input_sha256"] == target["input_sha256"]
                assert obs["normal_verdict"] == evidence["verdict"] == "proven"
                native = resolve(obs["native_evidence"])["content"]["goals"][0]
                assert native["results"] == obs["native_results"] and native["passed"] is True
                assert "valid" in native["results"]
                direct_valid += 1
            else:
                assert evidence["id"] == target["id"] and evidence["input"]["sha256"] == target["input_sha256"]
                assert obs["native_results"] == evidence["native_results"]
                assert "valid" in obs["native_results"]
                assert obs["outcome_artifact"]["relative"].endswith("/leaf-" + target["id"] + "/outcome.json")
                raw_manifest = resolve(component["context"]["raw_manifest"])
                assert obs["outcome_artifact"] in raw_manifest
                if name == "private_frame":
                    assert "normal_verdict" not in evidence and "normal_verdict" not in obs
                    assert obs["reconstructed_normal_verdict"] == "proven"
                    assert obs["normal_verdict_basis"]["kind"] == "reviewed-passive-observer-assertion"
                    assert obs["normal_verdict_basis"]["auditor_sha256"] == "12cd78dcbdda5d7d8a1c7a2a60ef99992a6214ea1d22426b382a663771133250"
                else:
                    assert obs["normal_verdict"] == evidence["normal_verdict"] == "proven"
                direct_valid += 1
            ordinary += obs["ordinary"]
            smoke += obs["smoke"]
            properties += obs["properties"]
            inventory_only += obs["inventory_only_ordinary"]
            native_rows += obs["native_report_rows"]
        summaries.append({"id": name, "targets": len(component["targets"]),
                          "source_commit": component["historical_identity"]["source_commit"]})
    assert (ordinary, smoke, inventory_only, native_rows, direct_valid) == (91, 1, 2, 90, 89)
    total = CATALOG.stat().st_size + sum(row["bytes"] for row in refs.values())
    assert total <= 16 * 1024 * 1024
    return {"components": summaries, "source_targets": 82, "normalized_ordinary": ordinary,
            "normalized_smoke": smoke, "inventory_only_ordinary": inventory_only,
            "native_report_rows": native_rows, "direct_valid_ordinary_native_rows": direct_valid,
            "registered_property_entries": properties, "documents": len(refs), "resolved_locations": len(locations),
            "complete_origin_value_or_explicit_derivation_checks": sum(operations.values()),
            "origin_operations": operations, "bundle_bytes": total,
            "largest_document_bytes": max(row["bytes"] for row in refs.values())}


def refuses(callback):
    try:
        callback()
    except (AssertionError, KeyError, IndexError, ValueError, OSError):
        return True
    raise AssertionError("tamper accepted")


def main():
    catalog = json.loads(CATALOG.read_bytes())
    summary = metadata_checks(catalog)
    bad_target = copy.deepcopy(catalog)
    bad_target["components"][0]["targets"][0]["input_sha256"] = "0" * 64
    assert refuses(lambda: metadata_checks(bad_target))
    bad_ref = dict(catalog["documents"][0]); bad_ref["sha256"] = "0" * 64
    assert refuses(lambda: document(bad_ref))
    assert refuses(lambda: resolve({"document": catalog["documents"][0], "pointer": "/missing-fail-closed"}))
    bad_glue = copy.deepcopy(catalog)
    bad_glue["components"][3]["accepted_subset"]["target_ids"].append("positive.cleanup")
    assert refuses(lambda: metadata_checks(bad_glue))
    old = json.loads((HERE / "scientific-bundle-v2/catalog.json").read_bytes())
    inverted = copy.deepcopy(catalog)
    changed_operations = []
    for key, rows in inverted["document_provenance"].items():
        for row in rows:
            if row["operation"] != "JSON value preserved; canonical JSON serialization":
                changed_operations.append(key)
                row["operation"] = "JSON value preserved; canonical JSON serialization"
    assert len(changed_operations) == 2 and inverted == old
    assert catalog["documents"] == old["documents"]
    receipt = {"classification": "PASS: pure retained-JSON normalization and fail-closed integrity controls",
               "created": "2026-10-16 ET", "catalog": {"path": str(CATALOG), "sha256": digest(CATALOG.read_bytes()), "bytes": CATALOG.stat().st_size},
               "summary": summary, "tamper_controls": ["canonical input mismatch refused", "document hash mismatch refused", "unknown JSON pointer refused", "unaccepted gluing target refused"],
               "version_history": {"v1": "Physical dtor method artifact representation was made consistent in v2; v1 retained.",
                                   "v2": "Two derived document provenance operations were incorrectly described as unchanged JSON values; v3 labels and verifies those exact derivations. All 91 objects and all 82 target/outcome values are unchanged from v2.",
                                   "v2_to_v3_exact_inverse_checked": True},
               "project_imports": 0, "subprocesses": 0, "SSH": 0, "compiler_native_verifier_solver_calls": 0,
               "source_or_caller_admission": False, "scientific_proof_rerun": False,
               "boundary": "These controls verify normalized retained metadata and source target/context identities. Accepted mathematical scope remains exactly the historical root decisions and declared TCB. No source/Typed/allocator/body/caller proof or new proof record is established."}
    output = BASE / "evidence/t25-closed-scientific-bundle-v3-normalization-controls-20261016.json"
    assert not output.exists()
    output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"receipt": str(output), "receipt_sha256": digest(output.read_bytes()), "summary": summary}, sort_keys=True))


if __name__ == "__main__":
    main()
