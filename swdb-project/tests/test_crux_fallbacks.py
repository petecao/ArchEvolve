"""The crux-llvm fallbacks and the bounded route through `swdb prove` (Probata proof of concept ticket 23).

Created: 2026-10-14 ET. Design: formal-verification map spec ("Verifier lineup and order": fallbacks in order,
floats as reals, failure classes; "Bounds": unwinding; Later change of 2026-10-14 13:19 ET: CBMC 6.11 on the C
lowering is the bounded verifier); map 11 items 2, 4, 6, 9; 19 item 5. Format:
docs/reference/format-v0.4-stubs-check-mode.md.

Seam 1 (`swdb prove`): `--adapter crux-llvm-cxx` (crux-llvm 0.12 on the C++), `--adapter crux-llvm-c` (on the C
lowering) and `--adapter bounded` (CBMC, then the two crux-llvm fallbacks; crux-llvm `-f real` for a real-valued
unit). The fixture candidates are ticket 22's (tests/test_cbmc_adapter.py). Real jobs skip cleanly without CBMC
6.11, crux-llvm 0.12 or clang 22.1.8; scripted faults use stand-ins (fake_cbmc.py, fake_crux.py).
"""

import json
import sys

import pytest
import yaml

from conftest import FIXTURES
from test_cbmc_adapter import (CBMC, FILL, FILL_BOUNDS, HALF, SMOKE, TWICE, VACUOUS, Seed, build_cbmc_seed,
                               needs_cbmc)


def _crux_present():
    from swdb import crux_adapter
    return not crux_adapter.locate()[3]


needs_crux = pytest.mark.skipif(not _crux_present(), reason="crux-llvm 0.12 is missing")
FAKE_CBMC = f"{sys.executable} {CBMC / 'fake_cbmc.py'}"
FAKE_CRUX = f"{sys.executable} {CBMC / 'fake_crux.py'}"
CRUX_FORMS = ("crux-llvm-cxx", "crux-llvm-c")


@pytest.fixture(scope="module")
def crux_seed(tmp_path_factory):
    path = tmp_path_factory.mktemp("crux-seed")
    return path, build_cbmc_seed(path)


@pytest.fixture
def seed(crux_seed, tmp_path):
    import shutil
    source, candidates = crux_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return Seed(tmp_path, candidates)


def prove(seed, adapter, function="swdb_fixture_fill", contract=FILL, bounds=None, *extra, candidate="safe", env=None,
          ok=True):
    args = ["--candidate", seed.candidates[candidate], "--function", function, "--contract", contract,
            "--adapter", adapter, "--runs-dir", seed.runs, "--format", "json",
            "--bounds", json.dumps(bounds or FILL_BOUNDS)]
    result = seed.swdb("prove", *args, *extra, env=env)
    assert (result.returncode == 0) is ok, result.stderr + result.stdout
    return seed.read(json.loads(result.stdout)) if ok else result


def fake(crux=None, cbmc=None, **more):
    from swdb import cbmc_adapter, crux_adapter
    env = {"SWDB_CRUX": FAKE_CRUX, "FAKE_CRUX_REAL": " ".join(crux_adapter.locate()[0]),
           "FAKE_CRUX_MODES": ",".join(f"{form}={mode}" for form, mode in (crux or {}).items()), **more}
    if cbmc:
        env.update(SWDB_CBMC=FAKE_CBMC, FAKE_CBMC_MODE=cbmc, FAKE_CBMC_REAL=" ".join(cbmc_adapter.locate()[0]))
    return env


def _handler(record, form):
    path = next(r["path"] for r in record["evidence"]["reports"] if r["name"] == "handler")
    assert f"/{form}/" in path
    return json.loads(open(path).read())


# --- each fallback, run for real ------------------------------------------------------------------------------

@needs_cbmc
@needs_crux
@pytest.mark.parametrize("adapter", CRUX_FORMS)
def test_each_crux_fallback_proves_the_safe_fixture_and_refutes_the_seeded_bug_with_a_counterexample(seed, adapter):
    proven = prove(seed, adapter)
    assert proven["verdict"] == "proven" and proven["job"]["adapter"] == adapter
    settings = proven["settings"]
    assert settings["form"] == adapter.split("-")[-1] and settings["float_mode"] == "ieee"
    assert "--floating-point=ieee" in settings["flags"] and settings["iteration_bound"]["unwind"] == 4   # K = n + 1
    assert any(t.startswith("crux-llvm-0.12") for t in proven["tools"])
    refuted = prove(seed, adapter, candidate="bug")
    assert refuted["verdict"] == "refuted"
    example = refuted["counterexample"]
    assert example["property"].startswith(f"{FILL}#fill_post") and example["replay"]["replayed"] is True
    assert 1 <= example["inputs"]["n"] <= 3


@needs_cbmc
@needs_crux
def test_crux_llvm_on_map_07s_smoke_pair_proves_the_safe_program_and_refutes_the_seeded_bug_at_41(seed):
    bounds = {"threads": 1}
    assert prove(seed, "crux-llvm-cxx", "smoke_main", SMOKE, bounds)["verdict"] == "proven"
    buggy = prove(seed, "crux-llvm-cxx", "smoke_main", SMOKE, bounds, "--define", "BUGGY")
    assert buggy["verdict"] == "refuted" and buggy["counterexample"]["inputs"] == {"x": 41}


@needs_cbmc
@needs_crux
def test_a_crux_loop_beyond_the_bound_from_the_sizes_is_unwinding_bound_too_small_never_proven(seed):
    record = prove(seed, "crux-llvm-cxx", "swdb_fixture_twice", TWICE, {"threads": 1, "n": 2})
    assert record["verdict"] == "not_proven" and record["failure_class"] == "unwinding_bound_too_small"
    assert "--iteration-bound=3" in record["settings"]["flags"]                       # K = n + 1, one too small


@needs_cbmc
@needs_crux
def test_contradictory_preconditions_under_crux_are_a_vacuous_pass_never_proven(seed):
    record = prove(seed, "crux-llvm-cxx", "smoke_main", VACUOUS, {"threads": 1})
    assert record["verdict"] == "not_proven" and record["failure_class"] == "vacuous_pass"


# --- the route: order, fallback handler, the tool that gave the verdict ------------------------------------------

@needs_cbmc
@needs_crux
def test_the_bounded_route_runs_cbmc_first_and_names_it_as_the_verdict_tool(seed):
    record = prove(seed, "bounded")
    assert record["verdict"] == "proven"
    route = record["settings"]["route"]
    assert route["order"] == ["cbmc", "crux-llvm-cxx", "crux-llvm-c"] and route["verdict_tool"] == "cbmc"
    assert [a["tool"] for a in route["attempts"]] == ["cbmc"]
    assert "cbmc-6.11.0" in record["tools"]


@needs_cbmc
@needs_crux
def test_when_each_earlier_tool_cannot_parse_the_route_falls_back_in_order_and_names_the_verdict_tool(seed):
    record = prove(seed, "bounded", env=fake(crux={"cxx": "parse_error"}, cbmc="parse_error"))
    assert record["verdict"] == "proven"
    route = record["settings"]["route"]
    assert [(a["tool"], a.get("failure_class")) for a in route["attempts"]] == [
        ("cbmc", "parse_error"), ("crux-llvm-cxx", "parse_error"), ("crux-llvm-c", None)]
    assert route["attempts"][0]["handler"].startswith("next fallback: crux-llvm-cxx")
    assert route["verdict_tool"] == "crux-llvm-c" and record["job"]["adapter"] == "bounded"
    assert any(t.startswith("crux-llvm-0.12") for t in record["tools"]) and "cbmc-6.11.0" not in record["tools"]


@needs_cbmc
@needs_crux
def test_a_timeout_is_the_tools_verdict_and_never_moves_to_the_next_fallback(seed):
    record = prove(seed, "bounded", "swdb_fixture_fill", FILL, None, "--budget-minutes", "0.02", env=fake(cbmc="sleep"))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "timeout"
    assert [a["tool"] for a in record["settings"]["route"]["attempts"]] == ["cbmc"]


# --- real-valued units ---------------------------------------------------------------------------------------------

@needs_cbmc
@needs_crux
def test_a_real_valued_unit_goes_to_crux_llvm_with_f_real_never_to_cbmc_and_the_record_names_why(seed):
    record = prove(seed, "bounded", "swdb_fixture_half", HALF, {"threads": 1})
    assert record["verdict"] == "proven"
    route = record["settings"]["route"]
    assert route["real_valued"] is True and route["order"] == ["crux-llvm-cxx", "crux-llvm-c"]
    assert route["verdict_tool"] == "crux-llvm-cxx" and "SAW's float mode is not confirmed" in route["reason"]
    assert record["settings"]["float_mode"] == "real" and "--floating-point=real" in record["settings"]["flags"]
    bug = prove(seed, "bounded", "swdb_fixture_half", HALF, {"threads": 1}, "--define", "SWDB_SEEDED_REAL_ERROR")
    assert bug["verdict"] == "refuted" and bug["counterexample"]["replay"]["replayed"] is True


@needs_cbmc
@needs_crux
def test_when_neither_crux_run_can_read_a_real_valued_unit_no_cbmc_job_starts(seed):
    record = prove(seed, "bounded", "swdb_fixture_half", HALF, {"threads": 1},
                   env=fake(crux={"cxx": "parse_error", "c": "parse_error"}))
    assert record["verdict"] == "not_proven" and record["failure_class"] in ("parse_error", "unsupported_construct")
    route = record["settings"]["route"]
    assert [a["tool"] for a in route["attempts"]] == ["crux-llvm-cxx", "crux-llvm-c"]
    assert "never serves a real-valued unit" in route["cbmc"]
    assert not (seed.runs / record["id"] / "cbmc").exists()                        # no CBMC job started


# --- failure classes and handlers ------------------------------------------------------------------------------------

@needs_cbmc
@needs_crux
@pytest.mark.parametrize("mode, failure_class", [("parse_error", "parse_error"), ("unsupported", "unsupported_construct"),
                                                 ("solver_error", "solver_error"), ("crash", "tool_crash")])
def test_scripted_crux_faults_map_to_their_class_and_run_its_handler(seed, mode, failure_class):
    record = prove(seed, "crux-llvm-cxx", env=fake(crux={"cxx": mode}))
    assert record["verdict"] == "not_proven" and record["failure_class"] == failure_class
    handler = _handler(record, "crux-llvm-cxx")
    assert handler["failure_class"] == failure_class and handler["handler"]


@needs_cbmc
@needs_crux
def test_a_crux_job_over_its_budget_is_timeout(seed):
    record = prove(seed, "crux-llvm-cxx", "swdb_fixture_fill", FILL, None, "--budget-minutes", "0.02",
                   env=fake(crux={"cxx": "sleep"}))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "timeout"


@needs_cbmc
@needs_crux
def test_a_crux_job_the_watchdog_kills_is_out_of_memory(seed):
    record = prove(seed, "crux-llvm-cxx", env={"SWDB_VERIFIER_RSS_CAP_BYTES": str(4 * 2**20)})
    assert record["verdict"] == "not_proven" and record["failure_class"] == "out_of_memory"


@needs_cbmc
@needs_crux
def test_a_crux_counterexample_that_does_not_replay_is_spurious(seed):
    record = prove(seed, "crux-llvm-cxx", env=fake(crux={"cxx": "spurious"}, FAKE_CRUX_PROPERTY=f"{FILL}#fill_post.ensures1"))
    assert record["verdict"] == "not_proven" and record["failure_class"] == "spurious_counterexample"
    assert record["unreplayed_counterexample"]["replay"]["replayed"] is False


@needs_cbmc
@needs_crux
def test_a_crux_outcome_with_no_class_stops_the_batch(seed):
    result = prove(seed, "crux-llvm-cxx", env=fake(crux={"cxx": "silent"}), ok=False)
    assert "unclassified_crux_outcome" in result.stderr
    assert not list((seed.records / "proofs").glob("*.yaml"))


# --- the regression corpus ------------------------------------------------------------------------------------------

CORPUS = sorted((FIXTURES / "proof" / "regression_corpus").glob("*.yaml"))


@needs_cbmc
@needs_crux
@pytest.mark.parametrize("case", [c for c in CORPUS if yaml.safe_load(c.read_text())["adapter"] in CRUX_FORMS],
                         ids=lambda c: c.stem)
def test_each_crux_regression_corpus_case_gives_its_recorded_class_again(seed, case):
    data = yaml.safe_load(case.read_text())
    assert data["cause"].strip()
    given = data["input"]
    extra = [part for d in given.get("defines") or [] for part in ("--define", d)]
    record = prove(seed, data["adapter"], given["function"], given["contract"], given["bounds"], *extra)
    assert record.get("failure_class") == data["failure_class"]
