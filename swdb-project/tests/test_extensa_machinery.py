"""Ported Extensa machinery: accounting, probes, profiles, synthesis (ticket 49).

Created: 2026-10-03 ET. Compiles small C++ programs with the host compiler; every
provider here is an external_fixture, never a real provider.
"""

import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from conftest import REPO, run_swdb
from swdb.extensa import probes as P
from swdb.extensa import search as S
from swdb.extensa.synthesis import mutants
from swdb.extensa.synthesis.shape_classes import SHAPE_CLASSES

BUDGETS = {"max_iterations": 8, "plateau_iterations": 4, "lane_hours": 24, "provider_calls_per_iteration": 3,
           "provider_calls_setup": 1, "disk_gb": 20, "lanes": 1}


def ledger(**changes):
    return S.SearchLedger(S.SearchBudget.from_mapping({**BUDGETS, **changes}, "campaigns/extensa/x.yaml@sha"))


# --- loop accounting ---------------------------------------------------------------

@pytest.mark.parametrize("missing", sorted(BUDGETS))
def test_budgets_have_no_code_defaults(missing):
    with pytest.raises(ValueError, match="no code defaults"):
        S.SearchBudget.from_mapping({k: v for k, v in BUDGETS.items() if k != missing}, "file")
    with pytest.raises(ValueError, match="name the campaign file"):
        S.SearchBudget.from_mapping(BUDGETS, "")


def test_every_opened_call_is_charged_and_the_cap_refuses_the_next():
    book = ledger()
    book.begin_iteration()
    for outcome in (S.CallOutcome.COMPLETED, S.CallOutcome.TIMEOUT, S.CallOutcome.MALFORMED_OUTPUT):
        book.close_call(book.open_call("rewriting", "x"), outcome)
    assert book.counted_calls == 3
    with pytest.raises(S.CallRefused):
        book.open_call("repair", "y")
    book.record_iteration(S.IterationOutcome.NOT_IMPROVED)
    book.begin_iteration()          # unused calls never carry over; a new iteration has 3 again
    assert book.calls_remaining_this_iteration() == 3


def test_usage_limit_is_recorded_uncounted_and_the_iteration_is_retried():
    book = ledger()
    book.begin_iteration()
    call = book.close_call(book.open_call("rewriting", "x"), S.CallOutcome.USAGE_LIMIT)
    assert call.counted is False and book.counted_calls == 0 and book.uncounted_calls == 1
    book.record_iteration(S.IterationOutcome.PAUSED)
    assert book.iterations_completed == 0 and book.plateau == 0
    assert book.begin_iteration() == 1


def test_completed_non_improving_iteration_advances_plateau_once_and_infrastructure_does_not():
    book = ledger(plateau_iterations=2)
    book.begin_iteration(); book.record_iteration(S.IterationOutcome.NOT_IMPROVED)
    assert book.plateau == 1
    book.begin_iteration(); book.record_iteration(S.IterationOutcome.IMPROVED)
    assert book.plateau == 0
    book.begin_iteration(); book.record_iteration(S.IterationOutcome.NOT_IMPROVED)
    book.begin_iteration(); rec = book.record_iteration(S.IterationOutcome.INFRASTRUCTURE_FAILED)
    assert rec.advanced_plateau is False and book.plateau == 1
    assert book.stop()[0] is S.StopReason.INFRASTRUCTURE_FAILURE
    with pytest.raises(RuntimeError):
        book.begin_iteration()


def test_plateau_and_max_iterations_stop_with_their_reasons():
    book = ledger(plateau_iterations=2)
    for _ in range(2):
        book.begin_iteration(); book.record_iteration(S.IterationOutcome.NOT_IMPROVED)
    assert book.stop()[0] is S.StopReason.PLATEAU
    book = ledger(max_iterations=1)
    book.begin_iteration(); book.record_iteration(S.IterationOutcome.IMPROVED)
    assert book.stop()[0] is S.StopReason.MAX_ITERATIONS


def test_rollback_restores_tracked_and_untracked_files(tmp_path):
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    git("init", "-q"); git("config", "user.email", "t@example.com"); git("config", "user.name", "t")
    (tmp_path / "bfs.cc").write_text("original\n")
    (tmp_path / "preexisting.txt").write_text("keep\n")
    git("add", "bfs.cc"); git("commit", "-qm", "base")
    (tmp_path / "bfs.cc").write_text("candidate edit\n")
    (tmp_path / "new" / "dir").mkdir(parents=True)
    (tmp_path / "new" / "dir" / "helper.hh").write_text("new\n")
    plan = S.plan_rollback(tmp_path, incumbent_ref="HEAD", preserved_untracked=["preexisting.txt"])
    S.apply_rollback(tmp_path, plan)
    assert (tmp_path / "bfs.cc").read_text() == "original\n"
    assert not (tmp_path / "new").exists() and (tmp_path / "preexisting.txt").read_text() == "keep\n"


@pytest.mark.parametrize("reason, text, fields, ok", [
    ("certification_failed", "Check frontier_size failed.", {"failed_checks": ["frontier_size"]}, True),
    ("verdict_no_gain", "No gain under the speed rule.", {"ratio": 1.01, "lower": 0.99, "spread": 0.05}, True),
    ("made_up", "x", {}, False),
    ("verdict_gain", "It was 2x faster.", {}, False),
    ("certification_failed", "You should try a wider tile.", {}, False),
    ("verdict_gain", "Gain.", {"raw_timings_seconds": [1.0]}, False),
])
def test_feedback_is_closed_outcome_free_and_carries_only_structured_numbers(reason, text, fields, ok):
    if ok:
        assert S.Feedback(reason, text, fields).to_dict()["reason_code"] == reason
    else:
        with pytest.raises(S.FeedbackError):
            S.Feedback(reason, text, fields)


# --- runtime probes ----------------------------------------------------------------

PROGRAM = r'''#include <vector>
#include <cstdio>
struct Gather { void execute(const double* src, long n_src, const int* idx, long n, double* out) {
  for (long i = 0; i < n; ++i) out[i] = src[idx[i]]; } };
int main(int argc, char** argv) {
  long n = 8, n_src = 16; std::vector<double> src(n_src); std::vector<int> idx(n); std::vector<double> out(n);
  for (long i = 0; i < n_src; ++i) src[i] = i * 1.5;
  for (long i = 0; i < n; ++i) idx[i] = (int)((i * 3) % n_src);
  if (argc > 1) idx[2] = (int)n_src;
  Gather g;
  g.execute(src.data(), n_src, idx.data(), n, out.data());
  std::printf("%f\n", out[0]);
  return 0; }
'''
ENTRY = {"id": "operation.fixture_gather", "clauses": [
    {"id": "idx_in_bounds", "formal": {"language": "extensa_predicate", "predicate": "forall i: 0 <= idx[i] < |src|"}},
    {"id": "no_alias", "formal": {"language": "extensa_predicate", "predicate": "alias(src[], out[]) == false"}},
    {"id": "algebra", "formal": {"language": "extensa_predicate", "predicate": "associative(op)"}}]}
BINDING = {"operation.fixture_gather": {"idx": {"expr": "idx.data()", "len": "n"},
                                        "src": {"expr": "src.data()", "len": "n_src"},
                                        "out": {"expr": "out.data()", "len": "n"}}}


def _cxx():
    return shutil.which("clang++") or shutil.which("g++")


def _probe(tmp_path, origin):
    line = PROGRAM[:PROGRAM.index("g.execute")].count("\n") + 1
    plan = P.plan_for_entry(ENTRY, [{"line": line, "method": "execute", "var": "g",
                                     "origins": {k: origin for k in ("idx", "src", "out")}}])
    verdict = tmp_path / "verdict.txt"
    probe = P.emit_contract_probe(plan, BINDING, region_id="r", verdict_path=str(verdict), device_tu=False)
    text, report = P.splice_probes(PROGRAM, probe.probes, probe.globals)
    assert report[0][2]
    (tmp_path / "cert.cc").write_text(text)
    built = subprocess.run([_cxx(), *P.probe_build_flags(), str(tmp_path / "cert.cc"), "-o", str(tmp_path / "cert")],
                           capture_output=True, text=True)
    assert built.returncode == 0, built.stderr
    return plan, probe, verdict


def _verdict(tmp_path, plan, probe, verdict, *args):
    verdict.unlink(missing_ok=True)
    subprocess.run([str(tmp_path / "cert"), *args], check=True, capture_output=True)
    return P.contract_record_from_verdict(plan, probe, P.read_verdict(verdict, "r"), spliced=True)


def test_predicates_become_probes_with_one_negative_control_each(tmp_path):
    assert [p.rule_id for p in P.predicates_for_entry(ENTRY)] == ["idx_in_bounds", "no_alias"]  # algebra routes away
    plan, probe, verdict = _probe(tmp_path, "contract_operand")
    good = _verdict(tmp_path, plan, probe, verdict)
    assert good["contract_checked"] and set(good["caught"]) == set(good["required"])
    bad = _verdict(tmp_path, plan, probe, verdict, "violate")
    assert not bad["contract_checked"] and bad["reason"] == P.REASON_PREDICATE_FAILED
    assert bad["failed_call_bound"] == ["operation.fixture_gather.idx_in_bounds"]


def test_provider_bindings_are_model_bound_and_never_certify(tmp_path):
    plan, probe, verdict = _probe(tmp_path, "provider")
    record = _verdict(tmp_path, plan, probe, verdict)
    assert record["contract_checked"] is False and record["contract_checked_model_bound"] is True
    assert P.certification_matrix_cell(record, cell="probe")["status"] == "failed"


def test_timed_build_of_the_same_program_contains_no_probe_symbol(tmp_path):
    _probe(tmp_path, "contract_operand")
    (tmp_path / "timed.cc").write_text(PROGRAM)
    subprocess.run([_cxx(), "-std=c++11", "-O2", str(tmp_path / "timed.cc"), "-o", str(tmp_path / "timed")], check=True)
    P.assert_probe_free(tmp_path / "timed")
    with pytest.raises(ValueError, match="contract-probe"):
        P.assert_probe_free(tmp_path / "cert")


# --- synthesis through the provider launcher, certification and profiles ----------

def _library(tmp_path):
    lib = tmp_path / "library"
    shutil.copytree(REPO / "library" / "library_operations", lib / "library_operations")
    for extra in lib.glob("library_operations/*.yaml"):
        extra.unlink()           # keep only the harness files; seeded entries are separate tickets
    shutil.rmtree(lib / "library_operations" / "controls", ignore_errors=True)
    for folder in ("intrinsics", "lowerings", "rewrite_contracts"):
        (lib / folder).mkdir(exist_ok=True)
    records = tmp_path / "records"
    records.mkdir()
    return lib, records


def _provider(tmp_path, header):
    program = tmp_path / "synth_fixture.py"
    payload = {"entry": {"name": "fixture", "summary": "Fixture gather backend."},
               "files": [{"path": "backends/synth_native_cpu_gather.hh", "content": header}], "unresolved": []}
    program.write_text(f"import json\nprint(json.dumps({payload!r}))\n")
    config = tmp_path / "provider.yaml"
    config.write_text(yaml.safe_dump({"kind": "external_fixture", "command": [sys.executable, str(program)],
                                      "timeout_s": 30, "total_seconds": 60}))
    return config


GOOD_GATHER = """#pragma once
#include <cstddef>
struct SynthBackend {
  template <typename ValueT, typename IndexT>
  static void gather(ValueT* out, const ValueT* source, const IndexT* idx, std::size_t n, std::size_t n_source) {
    (void)n_source;
    for (std::size_t i = 0; i < n; ++i) out[i] = source[(std::size_t)idx[i]];
  }
};
"""


def _synthesize(tmp_path, header):
    lib, records = _library(tmp_path)
    result = run_swdb("synthesize", "gather", "--provider-config", _provider(tmp_path, header),
                      "--campaign", "extensa-native-bfs-20261004-a1", "--runs-dir", tmp_path / "runs",
                      "--records", records, "--library", lib, "--format", "json")
    assert result.returncode == 0, result.stderr
    return lib, records, json.loads(result.stdout)


def test_fixture_synthesis_certifies_and_enters_the_experimental_tier(tmp_path):
    lib, records, result = _synthesize(tmp_path, GOOD_GATHER)
    assert result["state"] == "installed", result
    assert result["tier"] == "experimental" and result["status"] == "certified"
    assert result["provider_calls"][0]["classification"] == "contract_fixture"
    assert set(result["certification"]["controls"].values()) == {"rejected"}
    entry = yaml.safe_load(next((lib / "library_operations" / "synthesized").rglob("entry.yaml")).read_text())
    assert entry["provenance"]["origin"]["campaign"] == "extensa-native-bfs-20261004-a1"
    certification = yaml.safe_load(next((records / "certifications").glob("*.yaml")).read_text())
    assert certification["verdict"] == "certified" and len(certification["matrix"]) == 2
    validated = run_swdb("validate", "--records", records, "--library", lib)
    assert validated.returncode == 0, validated.stderr


def test_fixture_mutant_is_rejected_and_never_installed(tmp_path):
    lib, records, result = _synthesize(tmp_path, mutants.mutant_text("gather", "off_by_one"))
    assert result["state"] == "rejected" and result["certification"]["verdict"] == "failed"
    assert not (lib / "library_operations" / "synthesized").exists() or \
        not any((lib / "library_operations" / "synthesized").iterdir())


def test_profile_missing_a_control_refuses_certification(tmp_path):
    from swdb.library_operations import install_synthesized
    lib, records = _library(tmp_path)
    entry_id, _folder, profile = install_synthesized(lib, "gather", GOOD_GATHER, origin={"kind": "fixture"})
    data = yaml.safe_load(profile.read_text())
    data["controls"] = data["controls"][1:]
    data["required_categories"] = sorted({c["category"] for c in data["controls"]})
    profile.write_text(yaml.safe_dump(data))
    result = run_swdb("certify", entry_id, "--profile", profile, "--records", records, "--library", lib,
                      "--runs-dir", tmp_path / "runs")
    assert result.returncode == 1 and "missing entry controls" in result.stderr
    assert not (records / "certifications").exists()


def test_mutation_gate_accepts_a_killing_test_and_rejects_a_toothless_one(tmp_path):
    import random
    from swdb.extensa.synthesis.families import FAMILIES, resolve_contract
    from swdb.extensa.synthesis.spec import TargetSpec
    from swdb.extensa.synthesis.targets.cpu_like import CpuCompileTarget
    from swdb.extensa.synthesis.testgen_backend import run_testgen_gate
    backend = tmp_path / "backend.hh"
    backend.write_text(GOOD_GATHER)
    target = CpuCompileTarget(TargetSpec("t", "x", _cxx(), ("-std=c++11",)))
    killing = ("#include \"synth_backend.hh\"\n#include <cstdio>\nint main(){double s[4]={1,2,3,4};int i[3]={3,0,3};"
               "double o[3];SynthBackend::gather<double,int>(o,s,i,3,4);"
               "if(o[0]!=4||o[1]!=1||o[2]!=4)return 1;std::puts(\"SYNTH_TEST_OK\");return 0;}\n")
    toothless = "#include \"synth_backend.hh\"\nint main(){return 0;}\n"
    contract = resolve_contract(FAMILIES["gather"], REPO / "library")
    for text, accepted in ((killing, True), (toothless, False)):
        invoker = lambda files, prompt, t=text: {"tests": [{"path": "test_gather.cpp", "content": t}], "unresolved": []}
        result = run_testgen_gate("gather", contract, backend, target, tmp_path / str(accepted), invoker=invoker,
                                  extra_include=tmp_path, mutant_rng=random.Random(1))
        assert result.accepted is accepted, result.reason


# --- provenance and the port boundary -----------------------------------------------

EXTENSA = REPO / "swdb" / "extensa"


def test_every_ported_file_has_spdx_and_provenance_headers_and_is_listed():
    listing = (EXTENSA / "PROVENANCE.md").read_text()
    files = sorted(p for p in EXTENSA.rglob("*.py"))
    files += sorted(p for p in (REPO / "library/library_operations/drivers").glob("*.tmpl"))
    assert files
    for path in files:
        head = "\n".join(path.read_text().splitlines()[:4])
        assert "SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception" in head, path
        assert "af3d6d7f7a69a72facdc3b95b42e78c952f44a76" in head and "Source:" in head, path
        rel = path.relative_to(REPO).as_posix()
        stem = rel.rsplit("_", 1)[0] if rel.endswith(".cpp.tmpl") else rel
        assert rel in listing or stem.split("/")[-1] in listing, rel


def test_the_check_would_catch_a_file_without_headers(tmp_path):
    bad = tmp_path / "x.py"
    bad.write_text('"""no headers"""\n')
    assert "SPDX-License-Identifier" not in bad.read_text()


FORBIDDEN = ("agent_runtime", "claude_invoke", "measurement", "fitness", "profitability", "a5.loop",
             "a5.selection", "smt_", "refiner")


def test_nothing_from_the_not_ported_list_is_imported():
    for path in EXTENSA.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            for name in names:
                assert not any(bad in name for bad in FORBIDDEN), (path, name)
