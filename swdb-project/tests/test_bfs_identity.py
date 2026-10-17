"""Public source/comparator workflows; fixture ratios are not gains. Created 2026-09-25."""

import copy
import hashlib
import json

import pytest

from conftest import REPO


@pytest.fixture
def repo(records):
    return records.copy_repo()


def output(result):
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def query(repo):
    return output(repo.swdb("implementations", "gapbs-bfs", "--format", "json"))


def test_both_sources_retain_context_after_index_rebuild(repo):
    first = query(repo)
    found = {row["implementation"]: row["source_context"] for row in first}
    upstream, dx100 = found["gapbs-bfs-do"], found["dx100-bfs-scalar"]
    assert upstream["application"] == "gapbs"
    assert dx100["application"] == "dx100-gapbs"
    assert upstream["source"]["commit"] == "2972aeb2703165bafd921222f4ed7196f542d3a8"
    assert dx100["source"]["commit"] == "e4fc4afdf894f295442cef3604667a469fab8e62"
    assert dx100["source"]["uri"] == "https://github.com/arkhadem/DX100"
    assert dx100["code"][0]["path"] == "benchmarks/gapbs/src/bfs.cc"
    assert "benchmarks/API" in dx100["build"]["command"]
    assert "-DFUNC" in dx100["build"]["flags"]
    assert dx100["evaluator"]["verifier"]["code"]["path"] == dx100["code"][0]["path"]
    assert dx100["verification"]["status"] == "unchecked"
    assert dx100["verification"]["evidence"] == []
    assert upstream["verification"]["status"] == "passed"
    assert dx100["source_baseline"] == "dx100-bfs-scalar"
    assert dx100["comparison_baseline"] is None and dx100["source_ancestor"] is None
    assert repo.swdb("build").returncode == 0
    assert query(repo) == first
    view = output(repo.swdb("view", "dx100-bfs-scalar", "kron-g16-k16", "mbit10", "--format", "json"))
    assert view["code"]["application"] == "dx100-gapbs"
    assert view["code"]["commit"] == dx100["source"]["commit"]


def test_vendored_dx100_snapshot_matches_manifest():
    folder = REPO / "apps" / "dx100"
    for line in (folder / "SHA256SUMS").read_text().splitlines():
        digest, rel = line.split(maxsplit=1)
        assert hashlib.sha256((folder / rel).read_bytes()).hexdigest() == digest


def test_author_accelerated_reference_has_its_own_function_and_unchanged_source(repo, tmp_path):
    found = {row["implementation"]: row["source_context"] for row in query(repo)}
    scalar, reference = found["dx100-bfs-scalar"], found["dx100-bfs-maa-reference"]
    assert scalar["function"] == "DOBFS" and reference["function"] == "DOBFSMAA"
    assert reference["application"] == scalar["application"] == "dx100-gapbs"
    assert reference["source"] == scalar["source"] and reference["code"] == scalar["code"]
    assert reference["source_baseline"] == "dx100-bfs-maa-reference" and reference["source_ancestor"] is None
    assert reference["comparison_baseline"] == "dx100-bfs-scalar"
    assert reference["build"]["compiler"] == "g++-13"
    assert reference["build"]["flags"].split() == ["-std=c++11", "-O3", "-Wall", "-g3", "-fopenmp", "-DGEM5", "-DMAA", "-DNUM_CORES=4", "-DTILE_SIZE=16384"]
    assert reference["run"]["timer"] == "gem5_roi_ticks"
    assert reference["evaluator"]["backend"] == "dx100.author_artifact.v1"
    assert reference["verification"]["status"] == "unchecked" and not reference["verification"]["evidence"]
    runs = tmp_path / "reference-sources"
    source = output(repo.swdb("source-snapshot", "dx100-bfs-maa-reference", "--id", "author-reference-source", "--runs-dir", runs, "--format", "json"))
    candidate = output(repo.swdb("baseline-candidate", source["id"], "--id", "author-reference-baseline", "--runs-dir", runs, "--format", "json"))
    assert candidate["artifact_role"] == "source_baseline" and candidate["artifact"]["sha256"] == source["artifact"]["sha256"]
    assert candidate["context"]["function"] == "DOBFSMAA" and candidate["implementation"] == "dx100-bfs-maa-reference"
    assert "proposal" not in candidate
    result = repo.swdb("profile", "dx100-bfs-maa-reference", "kron-g16-k16", "mbit10", "--runs-dir", runs)
    assert result.returncode == 1 and "requires the evaluation workflow" in result.stderr
    assert repo.swdb("build").returncode == 0
    again = {row["implementation"]: row["source_context"] for row in query(repo)}
    assert again["dx100-bfs-maa-reference"] == reference


def test_legacy_source_defaults_keep_meaning(repo):
    data = repo.read("implementations/gapbs-bfs-do.yaml")
    data["schema_version"] = "0.2"
    for key in ("application", "source_baseline", "evaluator", "verification"):
        data.pop(key)
    repo.write("implementations/gapbs-bfs-do.yaml", data)
    row = next(row for row in query(repo) if row["implementation"] == data["id"])
    assert row["source_context"]["context_resolution"] == "legacy_kernel_defaults"
    assert row["source_context"]["application"] == "gapbs"
    assert row["source_context"]["verification"]["status"] == "legacy_unspecified"


def test_profile_executes_implementation_evaluator_not_shared_kernel_default(records, tmp_path):
    records.add_stub()
    path = "implementations/stub-impl.yaml"
    data = records.read(path)
    kernel = records.read("kernels/stub-kernel.yaml")
    data.update(schema_version="0.4", application="gapbs", source_baseline="stub-impl",
                origin={"kind": "application_source", "description": "Fixture source baseline."},
                verification={"status": "unchecked", "evidence": [], "scope": "Fixture only."},
                evaluator={"backend": "native", "command": "printf 'SOURCE_SPECIFIC_CHECK_FAIL'; exit 1",
                           "pass_regex": "UNREACHABLE_PASS", "verifier": kernel["correctness_check"]["verifier"]})
    records.write(path, data)
    runs = tmp_path / "runs"
    result = records.swdb("profile", "stub-impl", "tiny-sym", "testhost", "--runs-dir", runs,
                          "--threads", "1", "--trials", "1", "--features", "no", "--cachegrind", "no")
    assert result.returncode == 1 and "correctness check failed" in result.stderr
    logs = list(runs.glob("*/correctness.log"))
    assert len(logs) == 1 and "SOURCE_SPECIFIC_CHECK_FAIL" in logs[0].read_text()


def comparison_fixture(repo):
    data = repo.read("implementations/gapbs-bfs-do.yaml")
    data.update(id="bfs-fixture-candidate", comparison_baseline="dx100-bfs-scalar")
    data["origin"] = {"kind": "derived", "description": "Identity fixture, unchanged code, not performance evidence.",
                      "derived_from": "gapbs-bfs-do"}
    data["verification"] = {"status": "unchecked", "evidence": [], "scope": "Fixture only."}
    repo.write("implementations/bfs-fixture-candidate.yaml", data)
    original = repo.read("profiles/gapbs-bfs-do.kron-g16-k16.mbit10.20260922t221109z.yaml")
    for rid, owner, duration in (("candidate-fixture-profile", data["id"], 1.0),
                                 ("baseline-fixture-profile", "dx100-bfs-scalar", 2.0)):
        profile = copy.deepcopy(original)
        profile.update(id=rid, implementation=owner)
        if owner == "dx100-bfs-scalar":
            profile["build"]["application_commit"] = "e4fc4afdf894f295442cef3604667a469fab8e62"
        profile["timing"] = [{**profile["timing"][0], "threads": 1, "trials": 1,
                              "times_s": [duration], "median_s": duration, "min_s": duration,
                              "max_s": duration, "spread": 0.0}]
        profile["extensions"]["comparison_context"] = {
            "protocol": "fixture-protocol-v1", "roi": "bfs-call-v1", "target": "fixture-native-target",
            "workload": "fixture-kron-source-0", "threads": 1, "basis": "measured", "evidence_kind": "fixture"}
        repo.write(f"profiles/{rid}.yaml", profile)


def compare(repo, *extra):
    return repo.swdb("compare", "bfs-fixture-candidate", "--profile", "candidate-fixture-profile",
                     "--baseline-profile", "baseline-fixture-profile", "--protocol", "fixture-protocol-v1",
                     "--format", "json", *extra)


def test_comparison_uses_explicit_baseline_not_source_ancestor(repo):
    comparison_fixture(repo)
    result = output(compare(repo))
    assert result["source_ancestor"] == "gapbs-bfs-do"
    assert result["source_baseline"] == "gapbs-bfs-do"
    assert result["comparison_baseline"] == "dx100-bfs-scalar"
    assert result["fixture_ratio"] == 2.0 and result["gain_claim"] is False
    assert result["outcome"] == "fixture_comparison" and "speedup" not in result
    assert repo.swdb("build").returncode == 0
    assert output(compare(repo)) == result


@pytest.mark.parametrize("field,value", [("roi", "different-roi"), ("target", "different-target"),
                                         ("workload", "different-source-vertex"), ("threads", 2),
                                         ("protocol", "different-protocol"), ("basis", "simulated"),
                                         ("threads", True), ("basis", ["measured"])])
def test_incompatible_evidence_is_non_success(repo, field, value):
    comparison_fixture(repo)
    path = "profiles/baseline-fixture-profile.yaml"
    profile = repo.read(path)
    profile["extensions"]["comparison_context"][field] = value
    repo.write(path, profile)
    result = compare(repo)
    assert result.returncode == 1 and result.stdout == ""


def test_comparator_missing_conflicting_or_wrong_kernel_fails(repo):
    comparison_fixture(repo)
    result = compare(repo, "--baseline", "gapbs-bfs-do")
    assert result.returncode == 1 and "conflicts" in result.stderr
    path = "implementations/bfs-fixture-candidate.yaml"
    data = repo.read(path)
    data.pop("comparison_baseline")
    repo.write(path, data)
    for args, message in (((), "baseline is required"), (("--baseline", "missing"), "does not exist"),
                          (("--baseline", "gapbs-pr-gs"), "different kernel")):
        result = compare(repo, *args)
        assert result.returncode == 1 and message in result.stderr


@pytest.mark.parametrize("change", ["missing", "wrong-owner", "failed-check", "missing-context", "stale-source"])
def test_unusable_profiles_never_produce_ratio(repo, change):
    comparison_fixture(repo)
    path = "profiles/baseline-fixture-profile.yaml"
    profile = repo.read(path)
    if change == "missing":
        (repo.path / path).unlink()
    else:
        if change == "wrong-owner":
            profile["implementation"] = "gapbs-bfs-do"
        elif change == "failed-check":
            profile["parts"] = [part for part in profile["parts"] if part["part"] != "correctness"]
        elif change == "stale-source":
            profile["build"]["application_commit"] = "f" * 40
        else:
            profile["extensions"] = {}
        repo.write(path, profile)
    result = compare(repo)
    assert result.returncode == 1 and result.stdout == ""


@pytest.mark.parametrize("change", ["cross-app-baseline", "borrowed-evaluator", "missing-application",
                                     "false-passed", "foreign-evidence"])
def test_explicit_context_rejects_conflicting_source_and_invented_verification(repo, change):
    path = "implementations/dx100-bfs-scalar.yaml"
    data = repo.read(path)
    if change == "cross-app-baseline":
        data["source_baseline"] = "gapbs-bfs-do"
    elif change == "borrowed-evaluator":
        data["evaluator"]["verifier"]["code"]["path"] = "src/bfs.cc"
    elif change == "missing-application":
        data.pop("application")
    else:
        data["verification"]["status"] = "passed"
        if change == "foreign-evidence":
            data["verification"]["evidence"] = ["gapbs-bfs-do.kron-g16-k16.mbit10.20260922t221109z"]
    repo.write(path, data)
    result = repo.validate()
    assert result.returncode == 1 and "dx100-bfs-scalar.yaml" in result.stderr
