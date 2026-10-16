"""Public report-reader property closure controls, 2026-10-16 ET.

These are report-data fixtures, not actual prover or scientific evidence.
"""
import copy
import json

import pytest

from swdb.proof_setup import read_wp_reports


def reports(tmp_path, mutate=None, mutate_native=None):
    target = {"goal": "typed_f_ensures", "property": "f_ensures", "function": "f",
              "line": 1, "smoke": False, "passed": True, "verdict": "valid",
              "provers": [{"prover": "fixture", "time": 0, "success": 1}]}
    smoke = {**target, "goal": "typed_f_wp_smoke_default_requires",
             "property": "f_wp_smoke_default_requires", "smoke": True,
             "verdict": "unknown"}
    inventory = {"version": "1", "complete": True,
                 "goals": [{**target, "targets": [], "results": ["valid"]},
                           {**smoke, "targets": ["f_ensures"], "results": ["unknown"]}],
                 "properties": [
                     {"property": "f_ensures", "function": "f", "kind": "contract",
                      "line": 1, "extern": False, "dependencies": [], "origin": None,
                      "description": "ensures fixture", "generated_smoke_failure": False},
                     {"property": "f_wp_smoke_default_requires", "function": "f",
                      "kind": "other", "line": 1, "extern": False,
                      "dependencies": [], "origin": None,
                      "description": "wp_smoke_default_requires",
                      "generated_smoke_failure": False}]}
    if mutate:
        mutate(inventory)
    goals, properties, fresh = (tmp_path / name for name in ("goals.json", "properties.csv", "inventory.json"))
    native = [target, smoke]
    if mutate_native:
        mutate_native(native)
    goals.write_text(json.dumps(native))
    properties.write_text("directory\tfile\tline\tfunction\tproperty kind\tstatus\tproperty\n"
                          ".\tf.c\t1\tf\tpostcondition\tValid\tf_ensures\n")
    fresh.write_text(json.dumps(inventory))
    return read_wp_reports(goals, properties, fresh)


def test_complete_property_reference_closure_can_be_read(tmp_path):
    assert reports(tmp_path)["verdict"] == "proven"  # synthetic reader behavior only


@pytest.mark.parametrize("mutation", [
    lambda d: d["properties"].pop(),
    lambda d: d["properties"].pop(0),
    lambda d: d["properties"].clear(),
    lambda d: d["properties"].append(copy.deepcopy(d["properties"][0])),
    lambda d: d["goals"][0].update(property=None),
    lambda d: d["goals"][0].update(targets=["missing-target"]),
    lambda d: d["goals"][0].update(targets="f_ensures"),
    lambda d: d["properties"][0].update(dependencies=["missing-premise"]),
    lambda d: d["properties"][0].update(dependencies="f_ensures"),
    lambda d: d["properties"][0].update(origin="missing-origin"),
    lambda d: d["properties"][0].update(property=None),
    lambda d: d["properties"][0].pop("dependencies"),
    lambda d: d["properties"][0].pop("origin"),
    lambda d: d["goals"][0].pop("targets"),
])
def test_incomplete_or_ambiguous_property_closure_refuses_proof(tmp_path, mutation):
    result = reports(tmp_path, mutation)
    assert result["verdict"] == "not_proven"
    assert result["failure_class"] == "unclassified_wp_outcome"
    assert "property" in result["why"]


def test_complete_property_cycles_and_origins_are_preserved(tmp_path):
    def references(data):
        data["properties"][0]["dependencies"] = ["f_wp_smoke_default_requires"]
        data["properties"][1]["origin"] = "f_ensures"
    assert reports(tmp_path, references)["verdict"] == "proven"  # closure, no graph proof


def test_source_attributed_empty_module_identity_is_preserved(tmp_path):
    def module(data):
        data["properties"].append({"property": "", "kind": "other", "function": None,
                                   "line": 0, "description": "module\nfixture::Heap",
                                   "extern": False, "dependencies": [], "origin": None})
    assert reports(tmp_path, module)["verdict"] == "proven"  # actual WP module naming shape


@pytest.mark.parametrize("reference", ["goal", "target", "dependency", "origin"])
def test_empty_module_identity_cannot_substitute_for_a_proof_reference(tmp_path, reference):
    def empty_reference(data):
        data["properties"].append({"property": "", "kind": "other", "function": None,
                                   "line": 0, "description": "module\nfixture::Heap",
                                   "extern": False, "dependencies": [], "origin": None})
        if reference == "goal":
            data["goals"][0]["property"] = ""
        elif reference == "target":
            data["goals"][0]["targets"] = [""]
        elif reference == "dependency":
            data["properties"][0]["dependencies"] = [""]
        else:
            data["properties"][0]["origin"] = ""
    result = reports(tmp_path, empty_reference)
    assert result["verdict"] == "not_proven"
    assert result["failure_class"] == "unclassified_wp_outcome"
