"""Library operations seeded from Extensa certify end to end (tickets 50 and 51).

Created: 2026-10-03 ET. Real host builds of tiny cases; certification records are
written to temporary stores only. Updated: 2026-10-05 ET (ticket 77): the default command is 1.1
(driver-fault controls are recorded beside the entry's controls; the candidate binary is
`<build>/candidate_bin`); the mid-run pin check is tested under both command versions.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import REPO, run_swdb

OPS = REPO / "library" / "library_operations"


def _library(tmp_path):
    lib = tmp_path / "library"
    shutil.copytree(OPS, lib / "library_operations")
    shutil.copytree(REPO / "library" / "profiles", lib / "profiles")
    for folder in ("intrinsics", "lowerings", "rewrite_contracts"):
        (lib / folder).mkdir()
    records = tmp_path / "records"
    records.mkdir()
    return lib, records


def _certify(tmp_path, entry, profile):
    lib, records = _library(tmp_path)
    result = run_swdb("certify", entry, "--profile", profile, "--records", records, "--library", lib,
                      "--runs-dir", tmp_path / "runs")
    record = yaml.safe_load(next((records / "certifications").glob("*.yaml")).read_text())
    return result, record, lib, records


SEEDED = [("operation.pack_executor", "pack_executor"),
          ("operation.update_binning_executor", "update_binning_executor"),
          ("operation.vertex_relabel_executor", "vertex_relabel_executor"),
          ("operation.regroup_executor", "regroup_executor"),
          ("operation.gather_staging_executor", "gather_staging_executor")]
FAMILIES = {"update_binning_executor": ("DataLayoutAPI/update_binning.hh", "binned/binned_update_executor.yaml"),
            "vertex_relabel_executor": ("DataLayoutAPI/vertex_relabel.hh", "relabel/vertex_relabel_executor.yaml"),
            "regroup_executor": ("DataLayoutAPI/data_layout.hh", "regroup/regroup_executor.yaml"),
            "gather_staging_executor": ("DataLayoutAPI/gather_staging.hh", "staging/gather_staging_executor.yaml")}


@pytest.mark.parametrize("entry, profile", SEEDED)
def test_seeded_entry_certifies_and_every_control_fails_its_named_check(tmp_path, entry, profile):
    result, record, lib, records = _certify(tmp_path, entry, profile)
    assert result.returncode == 0, result.stderr + result.stdout
    assert record["verdict"] == "certified" and record["evidence_kind"] == "execution"
    assert {c["build"] for c in record["matrix"] if "build" in c} == {"sanitized", "openmp"}
    assert all(c["status"] == "passed" for c in record["matrix"])
    assert len(record["negative_controls"]) >= 3
    for control in record["negative_controls"]:
        assert control["status"] == "rejected", control
        assert control["reason"] == control["expected_check"]
        assert any(cell["check"] == control["expected_check"] for cell in control["cells"])
    state = run_swdb("validate", "--records", records, "--library", lib)
    assert state.returncode == 0, state.stderr
    from swdb.library import Library
    from swdb.store import Store
    derived = Library(lib, Store(records)).state(entry)
    assert derived == {"tier": "experimental", "status": "certified"}


def test_pack_controls_are_the_three_named_defects(tmp_path):
    _result, record, *_ = _certify(tmp_path, "operation.pack_executor", "pack_executor")
    checks = {c["id"]: c["expected_check"] for c in record["negative_controls"] if c["kind"] != "driver_fault"}
    assert checks == {"off_by_one_index": "differential_mismatch", "dropped_chain_level": "differential_mismatch",
                      "aliasing_write": "frame_violation"}
    probe = next(c for c in record["matrix"] if c["cell"] == "probe/contract")
    assert probe["status"] == "passed" and probe["contract"]["binding_strength"] == {
        "operation.pack_executor.no_aliasing_between_src_and_dest": "call_bound"}


def test_probes_are_in_the_certification_build_only(tmp_path):
    from swdb.extensa.probes import assert_probe_free
    _result, record, *_ = _certify(tmp_path, "operation.pack_executor", "pack_executor")
    probe_binary = next(c for c in record["matrix"] if c["cell"] == "probe/contract")["binary"]
    with pytest.raises(ValueError):
        assert_probe_free(Path(probe_binary))
    run_folder = Path(record["raw_artifacts"][0])
    timed = run_folder / "openmp" / "candidate_bin"
    assert timed.is_file()
    assert_probe_free(timed)


def test_entry_records_its_extensa_origin_and_pins():
    entry = yaml.safe_load((OPS / "pack_executor.yaml").read_text())
    origin = entry["provenance"]["origin"]
    assert origin["commit"] == "af3d6d7f7a69a72facdc3b95b42e78c952f44a76"
    assert {"DataLayoutAPI/data_layout.hh", "AgenticRefiner/transformations/pack/pack_executor.yaml"} <= set(origin["paths"])
    assert entry["provenance"]["semantics"]["output_equivalence"] == "bitwise_identical"
    head = (OPS / "pack.hh").read_text().splitlines()[:3]
    assert "SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception" in head[0] and "af3d6d7f" in head[1]


@pytest.mark.parametrize("body", ["pack.hh", "binning.hh", "relabel.hh", "regroup.hh", "gather_staging.hh"])
def test_body_builds_as_cxx11_O3(tmp_path, body):
    cxx = shutil.which("g++-16") or shutil.which("g++") or shutil.which("clang++")
    source = tmp_path / "use.cc"
    source.write_text(f'#include "{OPS / body}"\nint main() {{ return 0; }}\n')
    built = subprocess.run([cxx, "-std=c++11", "-O3", "-Wall", "-c", str(source), "-o", str(tmp_path / "use.o")],
                           capture_output=True, text=True)
    assert built.returncode == 0, built.stderr


@pytest.mark.parametrize("injected", ['#include "MAA.hpp"\n', '#include <dxc_lowering.hpp>\n',
                                      "static void f() { maa_wait(0); }\n"])
def test_validate_rejects_a_body_that_uses_dx100(tmp_path, injected):
    lib, records = _library(tmp_path)
    body = lib / "library_operations" / "pack.hh"
    text = body.read_text().replace("#include <vector>\n", "#include <vector>\n" + injected)
    body.write_text(text)
    entry_file = lib / "library_operations" / "pack_executor.yaml"
    entry = yaml.safe_load(entry_file.read_text())
    import hashlib
    entry["code_sha256"] = hashlib.sha256(body.read_bytes()).hexdigest()
    entry_file.write_text(yaml.safe_dump(entry, sort_keys=False))
    result = run_swdb("validate", "--records", records, "--library", lib)
    assert result.returncode == 1
    assert "DX100 header" in result.stderr or "maa_" in result.stderr


@pytest.mark.parametrize("name", sorted(FAMILIES))
def test_seeded_families_declare_origin_pattern_key_and_three_controls(name):
    entry = yaml.safe_load((OPS / f"{name}.yaml").read_text())
    origin = entry["provenance"]["origin"]
    header, contract = FAMILIES[name]
    assert origin["commit"] == "af3d6d7f7a69a72facdc3b95b42e78c952f44a76"
    assert header in origin["paths"] and f"AgenticRefiner/transformations/{contract}" in origin["paths"]
    keys = entry["pattern_key"]
    assert keys and all(set(k) == {"roles", "address_shapes", "update_kind"} for k in keys)
    controls = [c["negative_control"] for c in entry["clauses"] if c["negative_control"]["id"] != "none"]
    assert len(controls) >= 3 and all(c["check"] for c in controls)
    profile = yaml.safe_load((REPO / "library" / "profiles" / f"{name}.yaml").read_text())
    assert {c["id"] for c in profile["controls"]} == {c["id"] for c in controls}
    body = (OPS / entry["location"]["path"].split("/", 1)[1]).read_text()
    assert "SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception" in body.splitlines()[0]
    for variant in ("Tiled", "tiled", "Team", "Fused"):
        assert f"class {variant}" not in body


@pytest.mark.parametrize("version", ["1.0", "1.1"])
def test_a_pinned_input_changed_during_the_run_refuses_the_receipt(tmp_path, monkeypatch, version):
    """2026-10-04 ET (final code review): the reference semantics, driver templates and control
    mutations were hash-checked only before the run."""
    from swdb import library_operation_blinding, library_operations
    from swdb.cli import Failure
    from swdb.library import Library
    from swdb.store import Store
    lib, records = _library(tmp_path)
    library = Library(lib, Store(records))
    entry = library.get("operation.pack_executor")
    reference = library_operations.inputs(library, entry)["reference"]
    module, name = ((library_operations, "_run_cell") if version == "1.0"
                    else (library_operation_blinding, "run_binary"))
    real = getattr(module, name)

    def tampering(*args, **kwargs):
        result = real(*args, **kwargs)
        reference.write_text(reference.read_text() + "\n// changed mid-run\n")
        return result
    monkeypatch.setattr(module, name, tampering)
    with pytest.raises(Failure, match="pinned certification inputs changed during execution"):
        library_operations.certify_entry(Store(records), library, "operation.pack_executor",
                                         lib / "profiles" / "pack_executor.yaml", runs_dir=tmp_path / "runs",
                                         version=version)
    assert not (records / "certifications").exists()


def test_validate_rejects_an_unknown_pattern_key_role(tmp_path):
    lib, records = _library(tmp_path)
    entry_file = lib / "library_operations" / "regroup_executor.yaml"
    entry = yaml.safe_load(entry_file.read_text())
    entry["pattern_key"][0]["roles"] = ["frontier"]
    entry_file.write_text(yaml.safe_dump(entry, sort_keys=False))
    result = run_swdb("validate", "--records", records, "--library", lib)
    assert result.returncode == 1 and "pattern_key" in result.stderr
