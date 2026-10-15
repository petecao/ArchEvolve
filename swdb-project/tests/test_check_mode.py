"""Check mode through `swdb runtime-check` (Probata proof of concept ticket 23).

Created: 2026-10-14 ET. Design: formal-verification map spec ("Formal-half language and the C++ subset": the
runtime-check form); map 16 items 1 and 8. Format: docs/reference/format-v0.4-stubs-check-mode.md.

The public command runs the runtime form of a contract's formal halves on a candidate's own C++ over the bounded
domain. Fixture candidates are ticket 22's (tests/test_cbmc_adapter.py). Needs clang 22.1.8 only (no verifier).
"""

import json
import shutil

import pytest

from test_cbmc_adapter import COPY, FILL, HALF, POST_BOUND, Seed, build_cbmc_seed


def _clang_present():
    from swdb import c_lowering
    return not c_lowering.locate().missing


needs_clang = pytest.mark.skipif(not _clang_present(), reason="clang 22.1.8 is missing")


@pytest.fixture(scope="module")
def check_seed(tmp_path_factory):
    path = tmp_path_factory.mktemp("check-seed")
    return path, build_cbmc_seed(path)


@pytest.fixture
def seed(check_seed, tmp_path):
    source, candidates = check_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    return Seed(tmp_path, candidates)


def check(seed, function, contract, bounds, *extra, candidate="safe", ok=True):
    result = seed.swdb("runtime-check", "--candidate", seed.candidates[candidate], "--function", function,
                       "--contract", contract, "--bounds", json.dumps(bounds), "--runs-dir", seed.runs,
                       "--format", "json", *extra)
    assert (result.returncode == 0) is ok, result.stderr + result.stdout
    return json.loads(result.stdout) if ok else result


@needs_clang
def test_a_correct_implementation_passes_every_runtime_form_and_a_seeded_bug_fails_one(seed):
    passed = check(seed, "swdb_fixture_fill", FILL, {"threads": 1, "n": 3})
    assert passed["verdict"] == "pass" and passed["feasible_runs"] > 100 and passed["failures"] == 0
    failed = check(seed, "swdb_fixture_fill", FILL, {"threads": 1, "n": 3}, candidate="bug")
    assert failed["verdict"] == "fail" and failed["failed_properties"] == [f"{FILL}#fill_post.ensures1"]


@needs_clang
def test_a_frame_clause_over_old_values_under_a_quantifier_catches_a_frame_violation(seed):
    bounds = {"threads": 1, "n": 3}
    assert check(seed, "swdb_fixture_copy", COPY, bounds)["verdict"] == "pass"
    violated = check(seed, "swdb_fixture_copy", COPY, bounds, "--define", "SWDB_SEEDED_FRAME_BUG")
    assert violated["verdict"] == "fail" and violated["failed_properties"] == [f"{COPY}#copy_post.ensures1"]
    program = open(violated["program"]["path"]).read()
    assert "tabulated" in program                                  # \old(a[k]) snapshotted over 0 <= k < n on entry


@needs_clang
def test_a_quantifier_bound_that_depends_on_the_post_state_is_refused(seed):
    result = check(seed, "swdb_fixture_total", POST_BOUND, {"threads": 1, "n": 3}, ok=False)
    assert "check mode refuses" in result.stderr and "post-state" in result.stderr


@needs_clang
def test_a_real_result_within_the_certify_tolerance_passes_and_one_outside_it_fails(seed):
    bounds = {"threads": 1}
    exact = check(seed, "swdb_fixture_half", HALF, bounds)
    assert exact["verdict"] == "pass" and exact["tolerance"] == 0.0
    off = ("--define", "SWDB_SEEDED_REAL_ERROR")                   # the result is 1e-3 off
    within = check(seed, "swdb_fixture_half", HALF, bounds, *off, "--tolerance", "0.01")
    assert within["verdict"] == "pass" and within["tolerance_source"] == "--tolerance"
    outside = check(seed, "swdb_fixture_half", HALF, bounds, *off, "--tolerance", "0.0001")
    assert outside["verdict"] == "fail" and outside["failed_properties"] == [f"{HALF}#half_post.ensures1"]
