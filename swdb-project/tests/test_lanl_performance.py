"""LANL `hardware_profiles`, `run_configs`, `performance_runs`, `performance_metrics` and the
`swdb_estimates` extension (LANL-shaped-db ticket 04). Created 2026-10-11 ET.

Built once from a small record closure (LR-03), never the ~1 GB catalog: the repository's one
small estimate (78 KB), a candidate, and the profiles, machines and hardware targets they reach.
Expected values come from the YAML records themselves or from literals read off them."""

import json

import pytest

from conftest import make_records, read_yaml
from testkit.lanl import (assert_foreign_keys_clean, assert_guessed_listed, assert_lanl_shape, assert_origins,
                          assert_separable, sql)

ESTIMATE = "lanl.bound-v2.fixture.20261006.estimate"
CANDIDATE = "bfs-functional-read-offload-20261006-a1.proposal.candidate-1"
PROFILE = "gapbs-pr-jacobi.kron-g16-k16.mbit10.20260922t212416z"
REPEAT = "gapbs-pr-jacobi.kron-g16-k16.mbit10.20260922t212417z"
NO_COMMIT = "gapbs-pr-jacobi.kron-g16-k16.mbit10.20260922t212418z"
BY_CANDIDATE ="lanl.bound-v2.fixture.20261006.candidate-subject.estimate"
TABLES = ("hardware_profiles", "run_configs", "performance_runs", "performance_metrics")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    records = make_records(tmp_path_factory.mktemp("lanl-performance")).copy_closure(ESTIMATE, CANDIDATE, PROFILE)
    # a repeat of PROFILE a second later: same implementation, input, build and binding
    repeat = records.read(f"profiles/{PROFILE}.yaml")
    repeat["id"] = REPEAT
    repeat["environment"]["started"] = "2026-09-22T21:24:17Z"
    records.write(f"profiles/{REPEAT}.yaml", repeat)
    # and another whose application commit was not recorded
    repeat["id"], repeat["build"]["application_commit"] = NO_COMMIT, None
    repeat["environment"]["started"] = "2026-09-22T21:24:18Z"
    records.write(f"profiles/{NO_COMMIT}.yaml", repeat)
    # the same estimate with a candidate as its subject
    estimate = records.read(f"estimates/{ESTIMATE}.yaml")
    estimate["id"] = BY_CANDIDATE
    estimate["subject"] = {"kind": "candidate", "id": CANDIDATE}
    records.write(f"estimates/{BY_CANDIDATE}.yaml", estimate)
    result = records.swdb("build")
    assert result.returncode == 0, result.stderr
    return records


def records_of(records, folder):
    return [read_yaml(path) for path in sorted((records.path / folder).glob("*.yaml"))]


def test_hardware_profiles_has_exactly_the_slide_columns(built):
    assert_lanl_shape(built, "hardware_profiles")


def test_each_machine_record_is_one_hardware_profile(built):
    rows = sql(built, "select h.cpu_model, h.cores, h.memory_gb, o.record_id from hardware_profiles h "
                      "join swdb_row_origins o on o.table_name = 'hardware_profiles' and o.row_id = h.id")
    assert sorted(r["record_id"] for r in rows) == sorted(m["id"] for m in records_of(built, "machines"))
    mbit10 = next(r for r in rows if r["record_id"] == "mbit10")
    # mbit10: 2 sockets x 16 cores (64 logical CPUs are hyperthreads); 134580494336 bytes = 125.34 GiB
    assert mbit10["cpu_model"] == "Intel(R) Xeon(R) Gold 6326 CPU @ 2.90GHz"
    assert mbit10["cores"] == 32
    assert mbit10["memory_gb"] == pytest.approx(125.337, abs=1e-3)


def test_a_hardware_target_never_becomes_a_hardware_profile(built):
    targets = {t["id"] for t in records_of(built, "hardware_targets")}
    assert any(t.startswith("dx100") for t in targets)
    origins = sql(built, "select o.record_id, r.kind from swdb_row_origins o join swdb_records r on r.id = o.record_id "
                         "where o.table_name = 'hardware_profiles'")
    assert {r["kind"] for r in origins} == {"machine"}
    assert not targets & {r["record_id"] for r in origins}


def test_performance_runs_has_the_slide_columns_and_the_guessed_links(built):
    assert_lanl_shape(built, "performance_runs")


def test_each_measured_timing_of_a_profile_is_one_performance_run(built):
    rows = sql(built, "select p.elapsed_seconds, p.throughput_value, o.record_id, v.slug as variant, h.cpu_model "
                      "from performance_runs p "
                      "join swdb_row_origins o on o.table_name = 'performance_runs' and o.row_id = p.id "
                      "left join kernel_variants v on v.id = p.kernel_variant_id "
                      "left join hardware_profiles h on h.id = p.hardware_profile_id")
    profiles = records_of(built, "profiles")
    assert len(rows) == sum(len(profile["timing"]) for profile in profiles) > 0
    one = [r for r in rows if r["record_id"] == PROFILE]
    # the profile's five thread counts, median of five trials each (records/profiles/<PROFILE>.yaml)
    assert sorted(r["elapsed_seconds"] for r in one) == [0.00518, 0.0052, 0.00528, 0.01028, 0.02045]
    assert {r["variant"] for r in one} == {"gapbs-pr-jacobi"}
    assert {r["cpu_model"] for r in one} == {"Intel(R) Xeon(R) Gold 6326 CPU @ 2.90GHz"}
    assert all(r["throughput_value"] is None for r in rows)   # no record states a throughput


def test_run_configs_has_the_slide_columns_and_the_guessed_link(built):
    assert_lanl_shape(built, "run_configs")


def test_a_run_config_names_what_the_run_ran_with(built):
    rows = sql(built, "select c.label, c.parameters_json, c.git_commit, v.slug as variant from performance_runs p "
                      "join run_configs c on c.id = p.run_config_id join kernel_variants v on v.id = c.kernel_variant_id "
                      "join swdb_row_origins o on o.table_name = 'performance_runs' and o.row_id = p.id "
                      f"where o.record_id = '{PROFILE}' and p.elapsed_seconds = 0.00528")
    assert len(rows) == 1
    config = rows[0]
    assert config["variant"] == "gapbs-pr-jacobi"
    assert config["git_commit"] == "2972aeb2703165bafd921222f4ed7196f542d3a8"   # build.application_commit
    assert config["label"] == "gapbs-pr-jacobi on kron-g16-k16, 4 threads"
    parameters = json.loads(config["parameters_json"])
    assert parameters["input"] == "kron-g16-k16"
    assert parameters["input_arguments"] == built.read("inputs/kron-g16-k16.yaml")["generator"]["arguments"]
    assert (parameters["threads"], parameters["trials"]) == (4, 5)
    assert parameters["flags"] == "-std=c++11 -O3 -Wall -fopenmp"
    assert (parameters["omp_places"], parameters["omp_proc_bind"]) == ("cores", "close")


def test_runs_with_the_same_parameters_share_one_run_config(built):
    rows = sql(built, "select p.run_config_id, o.record_id from performance_runs p join swdb_row_origins o "
                      "on o.table_name = 'performance_runs' and o.row_id = p.id "
                      f"where o.record_id in ('{PROFILE}', '{REPEAT}')")
    assert len(rows) == 10
    configs = {r["run_config_id"] for r in rows}
    assert len(configs) == 5
    origins = sql(built, "select row_id, record_id from swdb_row_origins where table_name = 'run_configs' "
                         f"and row_id in ({', '.join(map(str, configs))})")
    assert sorted(r["record_id"] for r in origins) == sorted([PROFILE] * 5 + [REPEAT] * 5)


def test_an_unrecorded_commit_is_null_and_a_config_of_its_own(built):
    rows = sql(built, "select c.git_commit, p.run_config_id from performance_runs p join run_configs c "
                      "on c.id = p.run_config_id join swdb_row_origins o on o.table_name = 'performance_runs' "
                      f"and o.row_id = p.id where o.record_id in ('{PROFILE}', '{NO_COMMIT}')")
    unknown = {r["run_config_id"] for r in rows if r["git_commit"] is None}
    assert len(unknown) == 5 and not unknown & {r["run_config_id"] for r in rows if r["git_commit"] is not None}


def test_performance_metrics_has_the_slide_columns_and_the_guessed_link(built):
    assert_lanl_shape(built, "performance_metrics")


def metric_rows(built):
    return sql(built, "select m.metric_name, m.metric_value, o.record_id, o.record_field, p.elapsed_seconds "
                      "from performance_metrics m join swdb_row_origins o "
                      "on o.table_name = 'performance_metrics' and o.row_id = m.id "
                      "left join performance_runs p on p.id = m.performance_run_id")


def test_only_measured_per_run_metrics_reach_performance_metrics(built):
    expected = []
    for profile in records_of(built, "profiles"):
        threads = {timing["threads"] for timing in profile["timing"]}
        for i, metric in enumerate(profile["metrics"]):
            number = isinstance(metric["value"], (int, float)) and not isinstance(metric["value"], bool)
            if metric["basis"] == "measured" and number and metric.get("threads") in threads:
                expected.append((profile["id"], f"metrics.{i}", metric["name"], metric["value"]))
    got = [(r["record_id"], r["record_field"], r["metric_name"], r["metric_value"]) for r in metric_rows(built)]
    assert sorted(got) == sorted(expected) and expected


def test_simulated_and_estimated_metrics_never_appear(built):
    profile = built.read(f"profiles/{PROFILE}.yaml")
    other = {f"metrics.{i}" for i, m in enumerate(profile["metrics"]) if m["basis"] != "measured"}
    assert any(m["basis"] == "simulated" and "cachegrind" in (m.get("tool") or "") for m in profile["metrics"])
    rows = metric_rows(built)
    assert not other & {r["record_field"] for r in rows if r["record_id"] == PROFILE}
    assert not [r for r in rows if r["metric_name"].startswith("sim_")]


def test_a_metric_links_to_the_run_with_its_thread_count(built):
    rows = [r for r in metric_rows(built) if r["record_id"] == PROFILE and r["metric_name"] == "time_per_trial_median"]
    # each run's median metric equals that run's elapsed seconds (same timing entry)
    assert len(rows) == 5 and all(r["metric_value"] == r["elapsed_seconds"] for r in rows)


def test_guessed_columns_list_the_performance_links(built):
    assert_guessed_listed(built, *TABLES)


def test_an_estimate_never_reaches_the_performance_tables(built):
    assert ESTIMATE in {e["id"] for e in records_of(built, "estimates")}
    kinds = sql(built, "select distinct o.table_name, r.kind from swdb_row_origins o join swdb_records r "
                       "on r.id = o.record_id where o.table_name in "
                       "('run_configs', 'performance_runs', 'performance_metrics')")
    assert {(r["table_name"], r["kind"]) for r in kinds} == {(t, "profile") for t in TABLES[1:]}


def estimate_rows(built):
    return {r["id"]: r for r in sql(built, "select e.*, v.slug as variant from swdb_estimates e "
                                           "left join kernel_variants v on v.id = e.kernel_variant_id")}


def test_each_estimate_is_one_swdb_estimates_row(built):
    rows = estimate_rows(built)
    assert set(rows) == {e["id"] for e in records_of(built, "estimates")} == {ESTIMATE, BY_CANDIDATE}
    row = rows[ESTIMATE]   # records/estimates/<ESTIMATE>.yaml
    assert (row["subject_kind"], row["subject_id"]) == ("implementation", "gapbs-bfs-do")
    assert (row["target"], row["input"], row["threads"]) == ("mbit10", "kron-g16-k16", 1)
    assert row["seconds"] == pytest.approx(2.2471697927392882e-08)
    assert row["ratio"] is None
    assert (row["verdict"], row["estimator_version"]) == ("within_error", "swdb.analytic.v1")


def test_an_estimate_of_an_implementation_links_to_its_variant(built):
    assert estimate_rows(built)[ESTIMATE]["variant"] == "gapbs-bfs-do"


def test_an_estimate_of_a_candidate_links_to_the_implementation_the_candidate_names(built):
    named = built.read(f"candidates/{CANDIDATE}.yaml")["implementation"]
    row = estimate_rows(built)[BY_CANDIDATE]
    assert (row["subject_kind"], row["subject_id"], row["variant"]) == ("candidate", CANDIDATE, named)


def test_an_estimate_whose_subject_names_no_implementation_has_no_variant(records):
    # A validated folder always resolves the subject; the builder itself (no validation) still
    # stores an unresolved subject as NULL, never a guess.
    from swdb import db

    records.add_stub()
    records.write("estimates/orphan.yaml", {"kind": "estimate", "id": "orphan", "basis": "estimated",
                                            "subject": {"kind": "candidate", "id": "no-such-candidate"}})
    path = records.path.parent / "build" / "unvalidated.sqlite"
    db.build(records.path, path)
    assert db.sql(path, "select id, subject_id, kernel_variant_id from swdb_estimates") == [
        {"id": "orphan", "subject_id": "no-such-candidate", "kernel_variant_id": None}]


def test_every_performance_row_names_its_record(built):
    assert_origins(built, *TABLES)


def test_a_build_passes_the_foreign_key_check(built):
    assert_foreign_keys_clean(built)


def test_deleting_every_swdb_table_leaves_a_consistent_lanl_database(built, tmp_path):
    assert_separable(built, tmp_path)
