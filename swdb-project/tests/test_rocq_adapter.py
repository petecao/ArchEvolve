"""Rocq method parts through swdb prove. Created: 2026-10-15 ET (ticket 42).

The pre-agreed seam is swdb prove -> immutable records, with validate/build and
candidate-level reading them. An unfinished theorem never gets a Rocq-checked record.
"""
import shutil
import yaml
from conftest import FIXTURES, REPO, make_records, run_swdb


def rocq_seed(tmp_path):
    records = make_records(tmp_path)
    library = tmp_path / "library"
    development = library / "rocq" / "probata"
    shutil.copytree(REPO / "library" / "rocq" / "probata", development)
    (library / "methods").mkdir()
    method = yaml.safe_load((FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml").read_text())
    (library / "methods" / "contract-fixture-1.yaml").write_text(yaml.safe_dump(method))
    return records.path, development


def test_an_admitted_composition_never_writes_a_rocq_checked_record(tmp_path):
    records, development = rocq_seed(tmp_path)
    source = development / "Composition.v"
    text = source.read_text()
    start = text.index("Theorem parallel_composition :")
    body = text.index("Proof.", start)
    end = text.index("\nEnd Composition.", body)
    source.write_text(text[:body] + "Proof.\nAdmitted.\n" + text[end:])
    result = run_swdb("prove", "--records", records, "--method-part", "composition_theorem",
                      "--adapter", "rocq", "--runs-dir", tmp_path / "runs", "--format", "json",
                      env={"SWDB_ROCQ": "none"})
    assert result.returncode == 1, result.stdout + result.stderr
    assert "contains Admitted; no Rocq-checked record" in result.stderr, result.stderr
    assert not list((records / "proofs").glob("*.yaml"))


def test_a_changed_hypothesis_is_refused_before_the_compiler(tmp_path):
    records, development = rocq_seed(tmp_path)
    source = development / "Composition.v"
    text = source.read_text()
    start = text.index("Theorem parallel_composition :")
    text = text[:start] + text[start:].replace("obl_class_fit ->", "True ->", 1)
    body = text.index("Proof.", start)
    end = text.index("\nEnd Composition.", body)
    source.write_text(text[:body] + "Proof.\n(* BEGIN t42 proof *)\nexact I.\nQed.\n(* END t42 proof *)\n" + text[end:])
    result = run_swdb("prove", "--records", records, "--method-part", "composition_theorem",
                      "--adapter", "rocq", "--runs-dir", tmp_path / "runs", env={"SWDB_ROCQ": "none"})
    assert result.returncode == 1
    assert "approved statement" in result.stderr, result.stderr
    assert not list((records / "proofs").glob("*.yaml"))


def test_an_added_axiom_is_refused_before_the_compiler(tmp_path):
    records, development = rocq_seed(tmp_path)
    source = development / "Composition.v"
    text = source.read_text().replace("Theorem parallel_composition :", "Axiom fabricated : False.\nTheorem parallel_composition :")
    source.write_text(text)
    result = run_swdb("prove", "--records", records, "--method-part", "composition_theorem",
                      "--adapter", "rocq", "--runs-dir", tmp_path / "runs", env={"SWDB_ROCQ": "none"})
    assert result.returncode == 1
    assert "Axiom" in result.stderr, result.stderr
    assert not list((records / "proofs").glob("*.yaml"))


def test_only_a_counting_checked_method_part_discharges_the_written_entry(tmp_path):
    """Record-reader fixture: this does not claim the real theorem has been proved."""
    import copy
    import json
    from swdb.rocq_adapter import development_identity
    from test_proof_records import build_proof_seed, _Seed
    candidate = build_proof_seed(tmp_path)
    seed = _Seed(tmp_path, candidate)
    identity = development_identity(tmp_path / "library" / "rocq" / "probata")
    assumed = {"kind": "written_proof", "reference": {"id": "rocq.probata.composition", "sha256": identity["sha256"]},
               "sentence": "Fixture: the composition theorem is a written proof until its matching check counts."}
    first = seed.prove(seed.script(bounds={"threads": "unbounded"}, assumptions=[assumed]))["record"]
    assert any(e["reference"] == assumed["reference"] for e in seed.level()["assumptions"])
    original = (seed.records / "proofs" / f"{first['id']}.yaml").read_bytes()
    method = copy.deepcopy(first)
    method.update(id="proof.fixture-written-composition", method_part_status="written",
                  subject={"kind": "method_part", "id": "rocq.probata.composition", "part": "composition_theorem"})
    for name in ("code", "contract", "baseline_function", "reference_semantics", "proof_semantics",
                 "minimum_bounds", "predecessor_snapshot"):
        method["pins"][name] = {"not_applicable": "Fixture method part has no candidate content."}
    method["pins"]["rocq_development"] = identity
    payload = tmp_path / "written.json"
    payload.write_text(json.dumps(method))
    added = seed.swdb("add", payload, "--db", tmp_path / "build" / "swdb.sqlite")
    assert added.returncode == 0, added.stderr
    assert any(e["reference"] == assumed["reference"] for e in seed.level()["assumptions"])
    wrong = copy.deepcopy(method)
    wrong.update(id="proof.fixture-wrong-part", method_part_status="rocq_checked", assumptions=[])
    wrong["subject"]["part"] = "reduction_lemma"
    payload = tmp_path / "wrong-part.json"
    payload.write_text(json.dumps(wrong))
    rejected = seed.swdb("add", payload, "--db", tmp_path / "build" / "swdb.sqlite")
    assert rejected.returncode == 1 and "canonical" in rejected.stderr, rejected.stderr
    method.update(id="proof.fixture-checked-composition", method_part_status="rocq_checked", assumptions=[])
    payload = tmp_path / "checked.json"
    payload.write_text(json.dumps(method))
    added = seed.swdb("add", payload, "--db", tmp_path / "build" / "swdb.sqlite")
    assert added.returncode == 0, added.stderr
    level = seed.level()
    assert level["level"] == "proven_unbounded", level
    assert not any(e["reference"] == assumed["reference"] for e in level["assumptions"])
    assert (seed.records / "proofs" / f"{first['id']}.yaml").read_bytes() == original
    # Changing the development invalidates its check and restores the entry on read.
    source = tmp_path / "library" / "rocq" / "probata" / "Composition.v"
    source.write_text(source.read_text() + "\n(* Fixture edit: a new content hash. *)\n")
    assert any(e["reference"] == assumed["reference"] for e in seed.level()["assumptions"])


def test_the_approved_theorem_writes_a_real_checked_record_that_validates_and_builds(tmp_path):
    import json
    import os
    import shlex
    import subprocess
    import pytest
    from swdb.rocq_adapter import development_identity
    command = shlex.split(os.environ.get("SWDB_ROCQ") or "opam exec --switch=rocq-9 -- rocq")
    try:
        tool = subprocess.run([*command, "--version"], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        pytest.skip("Rocq 9.3.0 unavailable")
    if tool.returncode or "version 9.3.0" not in tool.stdout:
        pytest.skip("Rocq 9.3.0 unavailable")
    if "Admitted." in (REPO / "library" / "rocq" / "probata" / "Composition.v").read_text():
        pytest.skip("The approved composition theorem is still pending")
    records, development = rocq_seed(tmp_path)
    path = tmp_path / "library" / "methods" / "contract-fixture-1.yaml"
    method = yaml.safe_load(path.read_text())
    identity = development_identity(development)
    method["rocq_development"] = {**identity, "composition_theorem": "Composition.parallel_composition",
                                 "dx100_reduction_lemma": "Reduction.dx100_reduction"}
    path.write_text(yaml.safe_dump(method))
    result = run_swdb("prove", "--records", records, "--method-part", "composition_theorem",
                      "--adapter", "rocq", "--runs-dir", tmp_path / "runs", "--format", "json")
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(result.stdout)["record"]
    assert record["subject"] == {"kind": "method_part", "id": "rocq.probata.composition", "part": "composition_theorem"}
    assert record["verdict"] == "proven" and record["method_part_status"] == "rocq_checked"
    assert record["pins"]["rocq_development"] == identity
    assert record["tools"] == ["rocq-9.3.0"]
    assert record["job"]["peak_rss_bytes"] > 0
    assert len(record["proof_setup_check"]["runs"]) == 3
    assert record["evidence_kind"] == "contract_fixture"  # a real check under a fixture method
    assert all(a["kind"] == "trusted_tool" for a in record["assumptions"])
    for args in (("validate", "--records", records), ("build", "--records", records, "--db", tmp_path / "db.sqlite")):
        checked = run_swdb(*args)
        assert checked.returncode == 0, checked.stdout + checked.stderr
