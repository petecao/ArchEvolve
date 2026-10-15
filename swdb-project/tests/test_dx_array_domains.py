"""Audited DX100 call-window boundaries; created 2026-10-15 ET (ticket 27)."""
import copy
import json
import subprocess

import pytest

from conftest import REPO
from swdb import c_lowering, proof_semantics
from swdb.library import Library


@pytest.fixture(scope="module")
def calls(tmp_path_factory):
    tool = c_lowering.locate()
    if tool.missing:
        pytest.skip(tool.missing)
    path = tmp_path_factory.mktemp("dx-call-ast") / "calls.cc"
    path.write_text('''
void maa_stream_load(int *, int, int, int, int, int);
void maa_indirect_load(int *, int, int, int);
void maa_indirect_store_vector(int *, int, int, int, int);
int scalar();
void direct(int *p, int r) {
  maa_stream_load(p, 0, 1, 2, r, -1);
  maa_indirect_load(p, r, 2, -1);
  maa_indirect_store_vector(p, r, 2, -1, -1);
}
void effect(int *p, int r) { maa_stream_load(p, r++, 1, 2, 0, -1); }
void nested(int *p) { maa_stream_load(p, scalar(), 1, 2, 0, -1); }
''')
    done = subprocess.run([*tool.command, "-std=c++20", "-fsyntax-only", "-Xclang", "-ast-dump=json", str(path)],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    def walk(node):
        yield node
        for child in node.get("inner", []):
            yield from walk(child)
    ast = json.loads(done.stdout)
    result = {}
    for node in ast["inner"]:
        if node.get("kind") == "FunctionDecl" and node.get("name") in {"direct", "effect", "nested"}:
            result[node["name"]] = [n for n in walk(node) if n.get("kind") == "CallExpr"]
    return result


def _policies():
    return proof_semantics.array_call_policies(Library(REPO / "library"))


def _origin(**changes):
    return {"kind": "entry_window", "parameter": "p", "root": "p", "element_type": "int",
            "elements": r"\at((integer)n,Pre)", "relative_offset": "0",
            "declarations_sha256": "a" * 64, **changes}


def test_only_exact_audited_pointer_call_footprints_are_available():
    policies = _policies()
    assert set(policies) == {"maa_stream_load", "maa_indirect_load", "maa_indirect_store_vector"}
    for name, policy in policies.items():
        assert policy["call"] == name and policy["model"]["entry_sha256"]
        assert policy["model"]["components"]["c"] == "88298dbb9176640fd8ec2d0c6e31386dd51849411b08df7cebf7f12eab1d22ce"


@pytest.mark.parametrize("position", [0, 1, 2])
def test_checked_call_record_retains_real_source_origin_and_exact_model(calls, position):
    from swdb import dx_array_domains
    node = calls["direct"][position]
    name = ["maa_stream_load", "maa_indirect_load", "maa_indirect_store_vector"][position]
    policy = _policies()[name]
    candidate = dx_array_domains.candidate(node, policy)
    site = {"function": "direct", "anchor": f"direct.stmt{position}.before", "source_line": 7 + position,
            "source_range": [100 + position, 120 + position], "reason": ""}
    row = dx_array_domains.certify(candidate, _origin(), site)
    assert row["origin"] == _origin() and row["policy"] == policy
    assert row["anchor"] == site["anchor"] and row["predicate"]
    assert "pointer_argument" not in row and "ast_id" not in row
    assert "\\at((integer)n,Pre)" in row["predicate"]


@pytest.mark.parametrize("variant", ["effect", "nested"])
def test_scalar_operand_effects_cannot_receive_a_call_origin_exemption(calls, variant):
    from swdb import dx_array_domains
    with pytest.raises(dx_array_domains.Refused):
        dx_array_domains.candidate(calls[variant][0], _policies()["maa_stream_load"])


@pytest.mark.parametrize("origin", [None, {}, _origin(element_type="double"),
    _origin(kind="allocation_block"), _origin(elements=None), _origin(relative_offset=None)])
def test_validity_or_incomplete_metadata_cannot_substitute_for_an_array_origin(calls, origin):
    from swdb import dx_array_domains
    candidate = dx_array_domains.candidate(calls["direct"][0], _policies()["maa_stream_load"])
    with pytest.raises(dx_array_domains.Refused):
        dx_array_domains.certify(candidate, origin, {"function": "direct", "anchor": "direct.s1", "reason": ""})


def test_checked_placement_and_policy_identity_cannot_be_bypassed(calls):
    from swdb import dx_array_domains
    policy = _policies()["maa_stream_load"]
    candidate = dx_array_domains.candidate(calls["direct"][0], policy)
    with pytest.raises(dx_array_domains.Refused, match="placement"):
        dx_array_domains.certify(candidate, _origin(), {"reason": "unsequenced sibling mutation"})
    stale = copy.deepcopy(policy)
    stale["model"]["components"]["c"] = "0" * 64
    with pytest.raises(dx_array_domains.Refused, match="audited"):
        dx_array_domains.candidate(calls["direct"][0], stale)


def test_quantifier_cannot_capture_source_argument_or_extent_identifiers(calls):
    from swdb import dx_array_domains
    node = copy.deepcopy(calls["direct"][1])
    # The source declaration identity is retained while its spelling is changed.
    node["inner"][2]["inner"][0]["referencedDecl"]["name"] = "swdb_dx_window_index"
    candidate = dx_array_domains.candidate(node, _policies()["maa_indirect_load"])
    row = dx_array_domains.certify(candidate, _origin(), {"function": "direct", "anchor": "direct.s1"})
    import re
    binder = re.search(r"\\forall integer (\w+);", row["predicate"])[1]
    assert binder != "swdb_dx_window_index"
    assert "((integer)swdb_dx_window_index)" in row["predicate"]


def test_changed_model_body_is_not_accepted_even_with_a_refreshed_yaml_pin(tmp_path):
    import hashlib
    import shutil
    import yaml
    shutil.copytree(REPO / "library" / "proof_semantics", tmp_path / "proof_semantics")
    model = tmp_path / "proof_semantics/dx100_bfs/model.h"
    model.write_text(model.read_text() + "\n/* drift */\n")
    entry = tmp_path / "proof_semantics/dx100_bfs_0_1.yaml"
    data = yaml.safe_load(entry.read_text())
    data["model"]["c"]["sha256"] = hashlib.sha256(model.read_bytes()).hexdigest()
    entry.write_text(yaml.safe_dump(data))
    assert proof_semantics.array_call_policies(Library(tmp_path)) == {}


def test_geometry_overrides_are_part_of_the_audited_call_policy():
    before = _policies()["maa_stream_load"]["model"]
    after = proof_semantics.array_call_policies(Library(REPO / "library"), ["DX_TS=3"])["maa_stream_load"]["model"]
    assert {row["elements"] for row in after["tile_objects"]} == {3}
    assert before["generated_sha256"] != after["generated_sha256"]


def test_checked_guards_typecheck_against_the_pinned_wp_model(calls, tmp_path):
    from swdb import dx_array_domains, framac
    tool = framac.locate()
    if tool.missing:
        pytest.skip(tool.missing)
    library = Library(REPO / "library")
    policies = proof_semantics.array_call_policies(library)
    names = ["maa_stream_load", "maa_indirect_load", "maa_indirect_store_vector"]
    assertions = []
    for position, name in enumerate(names):
        row = dx_array_domains.certify(dx_array_domains.candidate(calls["direct"][position], policies[name]),
            _origin(), {"function": "check", "anchor": f"check.s{position}"})
        assertions.append(f"/*@ assert checked_window_{position}: {row['predicate']}; */")
    source = tmp_path / "guards.c"
    source.write_text(proof_semantics.wp_prelude(library, "semantics.dx100_bfs_0_1", names) +
                      "\nvoid check(int *p, int n, int r) {\n" + "\n".join(assertions) + "\n}\n")
    done = subprocess.run([*tool.command, "-machdep", "x86_64", "-kernel-warn-key", "annot-error=abort", str(source)],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stdout + done.stderr
