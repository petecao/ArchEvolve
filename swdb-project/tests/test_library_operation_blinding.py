"""Library-operation certification 1.1: record verdicts, blinded driver faults, attributed controls.

Created: 2026-10-05 ET (ticket 77). Agent-decided under Yan-Ru's delegation; revisable.

The two attacks are agent-authored library-operation sources that certify under command 1.0 and
fail under 1.1, both with the harness scan (refused) and with the scan disabled (the records do
not support them). Real host builds of small cases; records go to temporary stores only.
"""

import hashlib
import json
import shutil
from pathlib import Path

import pytest
import yaml

from conftest import REPO

OPS = REPO / "library" / "library_operations"
RELABEL = ("operation.vertex_relabel_executor", "vertex_relabel_executor")


def _library(tmp_path):
    lib = tmp_path / "library"
    shutil.copytree(OPS, lib / "library_operations")
    shutil.copytree(REPO / "library" / "profiles", lib / "profiles")
    for folder in ("intrinsics", "lowerings", "rewrite_contracts"):
        (lib / folder).mkdir()
    records = tmp_path / "records"
    records.mkdir()
    return lib, records


def _repin(lib, entry_file, path, *, control=None):
    """Point the entry at the changed body (or control mutation) by its new sha256."""
    entry_path = lib / "library_operations" / entry_file
    entry = yaml.safe_load(entry_path.read_text())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if control is None:
        entry["code_sha256"] = digest
    else:
        clause = next(c for c in entry["clauses"] if c["negative_control"]["id"] == control)
        clause["negative_control"]["mutation"]["sha256"] = digest
    entry_path.write_text(yaml.safe_dump(entry, sort_keys=False))


def _certify(lib, records, runs, entry, profile, version):
    from swdb import library_operations
    from swdb.library import Library
    from swdb.store import Store
    library = Library(lib, Store(records))
    assert not library.validate()
    return library_operations.certify_entry(Store(records), library, entry, lib / "profiles" / f"{profile}.yaml",
                                            runs_dir=runs, version=version)


def _no_scan(monkeypatch):
    from swdb import library_operation_blinding
    monkeypatch.setattr(library_operation_blinding, "scan_sources", lambda sources, primitives=None: {})


# --- attack 1: an agent-authored control prints the rejection instead of containing the defect ------

FAKE_PRINT = """            out[static_cast<std::size_t>(perm_[static_cast<std::size_t>(v)])] = in[v];
        std::fprintf(stderr, "SWDB_PRESERVATION_FAIL:frame_violation\\n");
        std::exit(3);
"""


def _fake_print_control(tmp_path):
    lib, records = _library(tmp_path)
    body = (lib / "library_operations" / "relabel.hh").read_text()
    original = "            out[static_cast<std::size_t>(perm_[static_cast<std::size_t>(v)])] = in[v];\n    }\n\n    template <typename ValueT>\n    void unpermute_values"
    assert body.count(original) == 1
    fake = body.replace(original, FAKE_PRINT + "    }\n\n    template <typename ValueT>\n    void unpermute_values")
    fake = fake.replace("#include <algorithm>\n", "#include <algorithm>\n#include <cstdio>\n#include <cstdlib>\n", 1)
    control = lib / "library_operations" / "controls" / "vertex_relabel_executor.aliasing_write.hh"
    control.write_text("// NEGATIVE CONTROL aliasing_write (attack: no write, prints the rejection)\n" + fake)
    _repin(lib, "vertex_relabel_executor.yaml", control, control="aliasing_write")
    return lib, records


def test_fake_print_control_certifies_under_1_0(tmp_path):
    lib, records = _fake_print_control(tmp_path)
    record = _certify(lib, records, tmp_path / "runs", *RELABEL, "1.0")
    assert record["verdict"] == "certified"
    fake = next(c for c in record["negative_controls"] if c["id"] == "aliasing_write")
    assert fake["status"] == "rejected" and fake["reason"] == "frame_violation"


def test_fake_print_control_is_refused_by_the_1_1_scan(tmp_path):
    lib, records = _fake_print_control(tmp_path)
    record = _certify(lib, records, tmp_path / "runs", *RELABEL, "1.1")
    assert record["verdict"] == "failed"
    assert record["matrix"][0]["check"] == "harness_scan"
    findings = record["command"]["isolation"]["scan"]["findings"]
    assert set(findings) == {"control:aliasing_write"}
    tokens = {f["token"] for f in findings["control:aliasing_write"]}
    assert {"fprintf", "exit", "SWDB_PRESERVATION_FAIL"} <= tokens


def test_fake_print_control_fails_1_1_records_without_the_scan(tmp_path, monkeypatch):
    _no_scan(monkeypatch)
    lib, records = _fake_print_control(tmp_path)
    record = _certify(lib, records, tmp_path / "runs", *RELABEL, "1.1")
    assert record["verdict"] == "failed"
    assert all(c["status"] == "passed" for c in record["matrix"])
    fake = next(c for c in record["negative_controls"] if c["id"] == "aliasing_write")
    assert fake["status"] == "invalid" and fake["reason"].startswith("check_not_recorded")
    assert all(cell["attributed_runs"] == 0 and cell["checks"] == ["runtime_abort"] for cell in fake["cells"])
    others = [c for c in record["negative_controls"] if c["id"] != "aliasing_write"]
    assert others and all(c["status"] == "rejected" for c in others)


# --- attack 2: a body that looks for a run plan and skips the post-call checks when it sees none ---

DETECTOR = r"""
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <fcntl.h>
#include <unistd.h>
static std::string &swdbx_dir() { static std::string d; return d; }
__attribute__((constructor)) static void swdbx_grab(int argc, char **argv) { if (argc > 1) swdbx_dir() = argv[argc - 1]; }
// "fault" if a readable run plan names a fault, "clean" if it names none, "none" if no plan is visible.
static const char *swdbx_detect() {
  for (int fd = 3; fd < 64; ++fd) {
    const int fl = fcntl(fd, F_GETFL);
    if (fl < 0 || (fl & O_ACCMODE) != O_RDONLY) continue;
    fcntl(fd, F_SETFL, fl | O_NONBLOCK);
    char buf[96] = {0};
    const ssize_t n = read(fd, buf, 60);
    if (n >= 9 && std::strncmp(buf, "plan 1 ", 7) == 0) return (buf[7] == '0' && buf[8] == '0') ? "clean" : "fault";
  }
  const char *names[] = {"SWDB_LO_PLAN_FD", "SWDB_CERT_PLAN_FD", "SWDB_LO_RECORD_FD"};
  for (int i = 0; i < 3; ++i) if (std::getenv(names[i])) return "fault";
  return "none";
}
"""

BYPASS = """            out[static_cast<std::size_t>(perm_[static_cast<std::size_t>(v)])] = in[v];
        const_cast<ValueT*>(in)[0] = in[0] + ValueT(1);  // the aliasing defect
        const char *seen = swdbx_detect();
        { FILE *note = std::fopen((swdbx_dir() + "/detector.txt").c_str(), "w");
          if (note) { std::fputs(seen, note); std::fclose(note); } }
        if (std::strcmp(seen, "fault") != 0) {  // not a control: skip the driver's frame check
          FILE *f = std::fopen((swdbx_dir() + "/cand.bin").c_str(), "wb");
          if (f) { std::fwrite(out, sizeof(ValueT), perm_.size(), f); std::fclose(f); }
          std::printf("SWDB_RUN_DONE:CAND\\n");
          std::fflush(stdout);
          std::_Exit(0);
        }
"""


def _bypass_body(tmp_path):
    lib, records = _library(tmp_path)
    path = lib / "library_operations" / "relabel.hh"
    body = path.read_text()
    original = "            out[static_cast<std::size_t>(perm_[static_cast<std::size_t>(v)])] = in[v];\n    }\n\n    template <typename ValueT>\n    void unpermute_values"
    assert body.count(original) == 1
    body = body.replace(original, BYPASS + "    }\n\n    template <typename ValueT>\n    void unpermute_values")
    body = body.replace("#include <vector>\n", "#include <vector>\n" + DETECTOR, 1)
    path.write_text(body)
    _repin(lib, "vertex_relabel_executor.yaml", path)
    return lib, records


def test_plan_detecting_bypass_certifies_under_1_0(tmp_path):
    lib, records = _bypass_body(tmp_path)
    record = _certify(lib, records, tmp_path / "runs", *RELABEL, "1.0")
    assert record["verdict"] == "certified"
    notes = list(Path(record["raw_artifacts"][0]).rglob("detector.txt"))
    assert notes and {n.read_text() for n in notes} == {"none"}


def test_plan_detecting_bypass_is_refused_by_the_1_1_scan(tmp_path):
    lib, records = _bypass_body(tmp_path)
    record = _certify(lib, records, tmp_path / "runs", *RELABEL, "1.1")
    assert record["verdict"] == "failed" and record["matrix"][0]["check"] == "harness_scan"
    tokens = {f["token"] for f in record["command"]["isolation"]["scan"]["findings"]["body"]}
    assert {"constructor", "fopen", "getenv"} & tokens


def test_plan_detecting_bypass_fails_1_1_and_never_sees_a_plan(tmp_path, monkeypatch):
    _no_scan(monkeypatch)
    lib, records = _bypass_body(tmp_path)
    record = _certify(lib, records, tmp_path / "runs", *RELABEL, "1.1")
    assert record["verdict"] == "failed"
    cells = [c for c in record["matrix"] if c["cell"].endswith("/differential")]
    assert cells and all(c["status"] == "failed" and c["check"] == "record_invalid" for c in cells)
    driver = [c for c in record["negative_controls"] if c["kind"] == "driver_fault"]
    assert len(driver) == 2 and all(c["status"] == "invalid" for c in driver)
    runs = json.loads(Path(record["command"]["isolation"]["runs_file"]).read_text())
    candidate_runs = [r for r in runs if r["kind"] in ("positive", "driver_fault")]
    assert candidate_runs
    seen = {(Path(r["folder"]) / "detector.txt").read_text() for r in candidate_runs}
    assert seen == {"none"}  # record.o drained the plan before the candidate's initializer ran


# --- 1.1 structure ---------------------------------------------------------------------------------

def test_seeded_entry_1_1_one_blinded_binary_reference_first_and_attributed_controls(tmp_path):
    lib, records = _library(tmp_path)
    record = _certify(lib, records, tmp_path / "runs", *RELABEL, "1.1")   # ticket 78: 1.2 is the default
    assert record["command"]["version"] == "1.1" and record["verdict"] == "certified"
    isolation = record["command"]["isolation"]
    assert isolation["reference"]["deleted_before_candidate_build"]
    assert not list(Path(record["raw_artifacts"][0], "reference").glob("reference_bin"))
    runs = json.loads(Path(isolation["runs_file"]).read_text())
    for build in ("sanitized", "openmp"):
        mine = [r for r in runs if r["build"] == build]
        candidate = [r for r in mine if r["kind"] in ("positive", "driver_fault")]
        assert len({r["binary_sha256"] for r in candidate}) == 1
        controls = {r["binary_sha256"] for r in mine if r["kind"] == "control"}
        assert candidate[0]["binary_sha256"] not in controls
        kinds = [r["kind"] for r in mine]
        assert kinds != sorted(kinds, key=("positive", "driver_fault", "control").index)
        assert len({r["nonce"] for r in mine}) == len(mine)
        assert len({Path(r["folder"]).parent for r in mine}) == 1
    driver = {c["id"]: c for c in record["negative_controls"] if c["kind"] == "driver_fault"}
    assert set(driver) == {"driver.input_write", "driver.output_perturb"}
    for control in record["negative_controls"]:
        assert control["status"] == "rejected" and control["reason"] == control["expected_check"]
        assert all(cell["attributed_runs"] > 0 for cell in control["cells"])
    for control in driver.values():
        assert all(cell["attributed_runs"] == cell["runs"] for cell in control["cells"])


def test_version_1_0_stays_selectable_and_records_its_version(tmp_path):
    lib, records = _library(tmp_path)
    record = _certify(lib, records, tmp_path / "runs", *RELABEL, "1.0")
    assert record["command"]["version"] == "1.0" and "isolation" not in record["command"]
    assert record["verdict"] == "certified"
    assert {c["id"] for c in record["negative_controls"]} == {"inverse_direction", "skip_last_vertex", "aliasing_write"}


def test_candidate_command_versions_are_refused_with_a_profile(tmp_path):
    from conftest import run_swdb
    lib, records = _library(tmp_path)
    result = run_swdb("certify", RELABEL[0], "--profile", RELABEL[1], "--records", records, "--library", lib,
                      "--runs-dir", tmp_path / "runs", "--command-version", "1.4")
    assert result.returncode != 0 and "1.0, 1.1" in result.stderr


# --- records and attribution (synthetic) ---------------------------------------------------------

def _run(lines, *, fault=None, nonce="a" * 32, code=0):
    data = ("\n".join(lines) + "\n").encode() if lines else b""
    return {"returncode": code, "timed_out": False, "record": data, "overflow": False,
            "channel_held_open": False, "nonce": nonce, "fault": fault}


REF = bytes(range(16))


def test_plan_line_is_fixed_length():
    from swdb.library_operation_blinding import plan_line
    lines = {plan_line(f, s, "b" * 32) for f in (None, "input_write", "output_perturb") for s in (0, 2 ** 63 - 1)}
    assert {len(line) for line in lines} == {60}


def test_judge_reads_only_records():
    from swdb.library_operation_blinding import judge
    head = ["begin 1", "plan " + "a" * 32]
    ok = judge(_run(head + ["frame ok", "result 16 " + REF.hex(), "end"]), 16, REF)
    assert ok["check"] == "passed"
    bad = bytearray(REF)
    bad[9] ^= 1
    assert judge(_run(head + ["frame ok", "result 16 " + bad.hex(), "end"]), 16, REF)["check"] == "differential_mismatch"
    frame = judge(_run(head + ["frame violation src 3 1", "result 16 " + REF.hex(), "end"]), 16, REF)
    assert frame["check"] == "frame_violation" and frame["violations"] == [("src", 3, 1)]
    # No end: a crash (or an early exit) is never a named check.
    assert judge(_run(head, code=3), 16, REF)["check"] == "runtime_abort"
    assert judge(_run(head, code=0), 16, REF)["check"] == "record_invalid"
    # A wrong nonce, a line after end, or a fault the plan did not name is invalid.
    assert judge(_run(head + ["frame ok", "result 16 " + REF.hex(), "end"], nonce="c" * 32), 16, REF)["check"] == "record_invalid"
    assert judge(_run(head + ["frame ok", "result 16 " + REF.hex(), "end", "end"]), 16, REF)["check"] == "record_invalid"
    assert judge(_run(head + ["fault output_perturb 1", "frame ok", "result 16 " + bad.hex(), "end"]), 16,
                 REF)["check"] == "record_invalid"
    assert judge(_run(head + ["SWDB_PRESERVATION_FAIL:frame_violation"], code=3), 16, REF)["check"] == "record_invalid"


def test_driver_fault_attribution():
    from swdb.library_operation_blinding import fault_attributed, judge
    head = ["begin 1", "plan " + "a" * 32]
    hit = judge(_run(head + ["fault input_write src 5", "frame violation src 5 1", "result 16 " + REF.hex(), "end"],
                     fault="input_write"), 16, REF)
    assert hit["check"] == "frame_violation" and fault_attributed(hit)
    elsewhere = judge(_run(head + ["fault input_write src 5", "frame violation src 6 1", "result 16 " + REF.hex(),
                                   "end"], fault="input_write"), 16, REF)
    assert elsewhere["check"] == "frame_violation" and not fault_attributed(elsewhere)
    extra = judge(_run(head + ["fault input_write src 5", "frame violation src 5 2", "result 16 " + REF.hex(), "end"],
                       fault="input_write"), 16, REF)
    assert not fault_attributed(extra)
    perturbed = bytearray(REF)
    perturbed[8] ^= 1
    out = judge(_run(head + ["fault output_perturb 1", "frame ok", "result 16 " + perturbed.hex(), "end"],
                     fault="output_perturb"), 16, REF)
    assert out["check"] == "differential_mismatch" and fault_attributed(out)
    wrong = bytearray(REF)
    wrong[0] ^= 1
    other = judge(_run(head + ["fault output_perturb 1", "frame ok", "result 16 " + wrong.hex(), "end"],
                       fault="output_perturb"), 16, REF)
    assert other["check"] == "differential_mismatch" and not fault_attributed(other)


@pytest.mark.parametrize("snippet", ["__attribute__((constructor)) static void f() {}", "int f() { return getpid(); }",
                                     'void f() { std::printf("x"); }', "void f() { std::_Exit(0); }",
                                     "void f() { swdb_lo_record(\"end\"); }", "int f() { return fstat(3, 0); }"])
def test_scan_refuses_library_operation_primitives(snippet):
    from swdb.library_operation_blinding import scan_text
    assert scan_text("#include <cstdio>\n" + snippet + "\n")


def test_scan_accepts_every_seeded_source():
    from swdb.library_operation_blinding import scan_text
    sources = [*OPS.glob("*.hh"), *(OPS / "controls").glob("*.hh"), *(OPS / "drivers").glob("*_cand.cpp.tmpl")]
    assert sources and all(scan_text(p.read_text()) == [] for p in sources)


def test_the_attack_detector_sees_a_plan_that_is_not_drained(tmp_path):
    """The bypass attack's detector works: without record.o it reads the plan and names the fault,
    so its 'none' under 1.1 comes from the blinding, not from a broken detector."""
    import os
    import subprocess
    from swdb.library_operation_blinding import plan_line
    from swdb.library_operations import sanitize_compiler
    source = tmp_path / "detector.cc"
    source.write_text(DETECTOR + 'int main() { std::fputs(swdbx_detect(), stdout); return 0; }\n')
    binary = tmp_path / "detector"
    built = subprocess.run([sanitize_compiler(), "-std=c++11", str(source), "-o", str(binary)],
                           capture_output=True, text=True)
    assert built.returncode == 0, built.stderr
    seen = {}
    for fault in (None, "output_perturb"):
        read, write = os.pipe()
        os.write(write, plan_line(fault, 7, "d" * 32))
        os.close(write)
        try:
            env = {k: v for k, v in os.environ.items() if not k.startswith("SWDB_")}
            seen[fault] = subprocess.run([str(binary)], capture_output=True, text=True, pass_fds=(read,),
                                         env=env).stdout
        finally:
            os.close(read)
    assert seen == {None: "clean", "output_perturb": "fault"}


def test_relabel_certifies_under_1_2_with_the_call_in_a_separate_process(tmp_path):
    """Ticket 78: command 1.2 (the default) certifies the seeded entry; every run of the candidate
    binary goes through the trusted evaluator, and every control is rejected, attributed."""
    from swdb import library_operations
    lib, records = _library(tmp_path)
    record = _certify(lib, records, tmp_path / "runs", *RELABEL, None)
    assert record["command"]["version"] == "1.2" == library_operations.VERSION
    assert record["verdict"] == "certified", record["negative_controls"]
    # 2026-10-05 ET (review fixes C10, ADR 0008): its own version field, and plain C++ on the host is measured.
    assert record["command"]["library_operation_version"] == "1.2" and record["command"]["family"] == "library_operation"
    assert record["evidence_basis"] == "measured"
    assert {"swdb/certification_isolation.py", "swdb/certification_faults.py"} <= {
        row["path"] for row in record["command"]["sources"]}
    isolation = record["command"]["isolation"]
    assert set(isolation["process_split"]) == {"evaluator", "candidate"}
    for build in isolation["binaries"].values():
        assert build["candidate"]["evaluator_sha256"] and "record_object_sha256" not in build["candidate"]
    for control in record["negative_controls"]:
        assert control["status"] == "rejected"
        assert all(cell["attributed_runs"] == cell["runs"] or control["kind"] != "driver_fault" for cell in control["cells"])
