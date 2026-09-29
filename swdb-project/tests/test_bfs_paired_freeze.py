"""Publisher boundary regressions; synthetic fixtures only. Date: 2026-09-26 ET.

No fixture is an empirical pilot. Package and paired-driver admission use
explicit seams; historical receipt/raw validation, publisher gate
routing, historical selection, and negative-control statistics run normally.
"""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import bfs_freeze_pilot as publisher
from scripts import bfs_native_repeatability as serial
from scripts import bfs_paired_calibration as paired
from swdb import artifacts, bfs_protocol
from swdb.bfs_native import RUNTIME_INHERITED
from swdb.cli import Failure
from test_bfs_freeze_pilot import aa_control
from test_bfs_paired_admission import admission_case


POLICY = {"minimum_speedup": 1.05, "confidence": 0.95,
          "bootstrap_resamples": 2000, "bootstrap_seed": 20260925,
          "maximum_relative_spread": 0.10}
SAMPLING = {"repetitions": 10, "warmups": 0,
            "aggregation": "geomean_source_median_ratio",
            "collection": {"method": "native_paired.v1", "order_seed": 20260926},
            "analysis": "paired_repetition_block_bootstrap.v1"}


@pytest.fixture
def paired_review(aa_control, monkeypatch):
    """Four synthetic historical cells, retaining real temporary hashed outputs."""
    _, spec, packets, store, seconds, receipt, save, trials = aa_control
    plan = json.loads(serial.PLAN.read_text())
    original_get = store.get
    additional = {}
    store.get = lambda rid, kind=None: additional.get(rid) or original_get(rid, kind)
    implementation = copy.deepcopy(store.get("dx100-bfs-scalar"))
    implementation["id"] = "gapbs-bfs-do"
    candidate = copy.deepcopy(store.get("unchanged"))
    candidate.update(id="unchanged-upstream", implementation=implementation["id"],
                     source_snapshot="source-upstream")
    source = copy.deepcopy(store.get("source"))
    source.update(id="source-upstream", implementation=implementation["id"])
    additional.update({row["id"]: row for row in (implementation, candidate, source)})

    # Extend the existing two-cell serial fixture to its full fixed four-cell
    # order. Source/build bytes are artificial and never enter the catalog.
    for index, original in zip((1, 3), list(packets)):
        cell = plan["cells"][index]
        first = copy.deepcopy(original["evaluation"])
        first.update(id=cell["first_evaluation"], candidate=candidate["id"],
                     implementation=implementation["id"], source_snapshot=source["id"])
        first["request"].update(id=first["id"], candidate=candidate["id"],
                                comparison_baseline=implementation["id"])
        trials(first, 1)
        cell.update(first_evaluation_sha256=artifacts.digest(first),
                    implementation=implementation["id"], candidate=candidate["id"],
                    workload=first["context"]["workload"]["id"],
                    source_sha256=candidate["artifact"]["sha256"],
                    canonical_graph_sha256=first["context"]["workload"]["canonical_sha256"],
                    primary_binary_sha256=first["build"]["binary_sha256"],
                    compiler=first["build"]["compiler"], flags=first["build"]["flags"],
                    driver_template_sha256=first["build"]["template_sha256"])
        second = copy.deepcopy(first)
        second.update(id=cell["id"], request=serial.first_request(first, cell, store.get("mbit10")))
        second["context"]["verifier_sha256"] = "2" * 64
        trials(second, 1)
        additional.update({row["id"]: row for row in (first, second)})
        packets.append({"evaluation": first, "package": {"id": f"package{index}"},
                        "diagnostic": {"id": f"profile{index}"}})
        seconds.append(second)
        receipt["cells"][index].update(
            evaluation=second["id"], first_evaluation=first["id"],
            first_record_sha256=artifacts.digest(first),
            first_binary_sha256=first["build"]["binary_sha256"],
            second_binary_sha256=first["build"]["binary_sha256"],
            first_verifier_module_sha256="1" * 64, compiler_sha256="c" * 64)
    packets.sort(key=lambda item: next(i for i, cell in enumerate(plan["cells"])
                                      if cell["first_evaluation"] == item["evaluation"]["id"]))
    seconds.sort(key=lambda row: next(i for i, cell in enumerate(plan["cells"]) if cell["id"] == row["id"]))
    for index, (item, second, cell) in enumerate(zip(packets, seconds, plan["cells"])):
        first = item["evaluation"]
        for row in (first, second):
            row["context"].update(adapter="synthetic.native.v1", application="synthetic-source")
        cell["first_evaluation_sha256"] = artifacts.digest(first)
        receipt["cells"][index]["first_record_sha256"] = artifacts.digest(first)
        item.update(candidate=store.get(first["candidate"]),
                    implementation=store.get(first["implementation"]),
                    workload={"id": first["context"]["workload"]["id"], "definition": {
                        "family": "uniform_random" if index < 2 else "kronecker"}},
                    regions=[{"kind": "function"}, {"kind": "loop"}],
                    availability=[{"state": "synthetic-package-admission-seam"}])
        item["package"]["evidence"] = {"diagnostic_build": {"scope": "historical-instrumented-binary"}}
        item["diagnostic"]["executions"] = [
            {"kind": kind, "source": 0, "correctness": {"passed": True},
             "diagnostic_wall_seconds": 2, "output_sha256": "a" * 64, "binary_sha256": "b" * 64}
            for kind in ("regions", "memory")]
        item["record_identities"] = {row["id"]: artifacts.digest(row)
                                     for row in (first, item["package"], item["diagnostic"])}
    serial.PLAN.write_text(json.dumps(plan))
    receipt["plan"]["sha256"] = artifacts.file_hash(serial.PLAN)
    spec.update(mode="native", id="synthetic-paired-freeze", maximum_relative_spread=0.10,
                spread_justification="Synthetic gate-routing test; no empirical justification.",
                packages=[packets[index]["package"]["id"] for index in (1, 3)],
                size_selection={"scale": 18, "justification": "synthetic", "accelerator_packages": []},
                paired_calibration={"historical_packages": [item["package"]["id"] for item in packets]})
    spec["repeatability"]["evaluations"] = {
        item["evaluation"]["id"]: second["id"] for item, second in zip(packets, seconds)}
    save()

    by_package = {item["package"]["id"]: item for item in packets}
    monkeypatch.setattr(publisher, "packet", lambda _store, rid: by_package[rid])
    monkeypatch.setattr(publisher, "workload_plan", lambda *_: None)
    monkeypatch.setattr(publisher, "freeze_header", lambda value, _: {
        "message_version": "1.0", "id": value["id"], "version": 1})
    monkeypatch.setattr(bfs_protocol, "_validate_settings", lambda *_: None)
    accelerator_calls = []

    def accepted_accelerator(*args):
        accelerator_calls.append(args)
        return {"executions": ["synthetic-accelerator-admission-seam"], "repeatability": []}

    monkeypatch.setattr(publisher, "accelerator_gate", accepted_accelerator)
    new_samples = [{role: [publisher.summary(vertex, [1 + 0.001 * repeat for repeat in range(10)])
                          for vertex in serial.SOURCES] for role in ("baseline", "candidate")}
                   for _ in packets]
    new_primary = {}
    for item in packets:
        first = item["evaluation"]
        value = copy.deepcopy(first)
        value["id"] += ".paired-baseline"
        value["context"]["repetitions"] = 10
        new_primary[first["id"]] = value
    qualified_calls = []

    def admitted_paired(_spec, selected, _store, _identities, gates):
        # The paired driver's raw admission has its own tests. This seam returns
        # its four-cell contract while retaining real negative-control statistics.
        qualified_calls.append(True)
        controls = []
        for index, samples in enumerate(new_samples):
            control = paired.negative_control(samples, POLICY, SAMPLING)
            gates.extend(f"new-cell-{index}: {reason}" for reason in control["unmet_gates"])
            member = new_primary[packets[index]['evaluation']['id']]
            controls.append({"pair": f"new-cell-{index}", **control,
                             "evaluations": {role: copy.deepcopy(member) for role in ('baseline', 'candidate')}})
        primary = [new_primary[item["evaluation"]["id"]] for item in selected]
        return {"pairs": controls, "sampling": copy.deepcopy(SAMPLING), "gain_claim": False,
                "retained_driver": {"inherited_runtime_settings": dict.fromkeys(RUNTIME_INHERITED)},
                "driver_receipt": copy.deepcopy(spec['repeatability']['driver_receipt']),
                "selected_primary_evaluations": [row["id"] for row in primary]}, primary

    monkeypatch.setattr(paired, "qualify", admitted_paired)
    return SimpleNamespace(spec=spec, store=store, packets=packets, seconds=seconds,
                           receipt=receipt, save=save, trials=trials, samples=new_samples,
                           new_primary=new_primary, qualified_calls=qualified_calls,
                           accelerator_calls=accelerator_calls)


@pytest.mark.parametrize("fault", ["missing-selection", "changed-receipt", "changed-raw", "changed-public-result"])
def test_paired_publication_requires_reconstructed_historical_evidence(paired_review, fault):
    case = paired_review
    if fault == "missing-selection":
        case.spec.pop("repeatability")
    elif fault == "changed-receipt":
        Path(case.spec["repeatability"]["driver_receipt"]["path"]).write_text("{}")
    elif fault == "changed-raw":
        Path(case.seconds[0]["timing"][0]["output"]).write_text("changed historical observation")
    else:
        case.seconds[0]["timing"][0]["duration_s"] = 99
    with pytest.raises(ValueError, match="revalidated historical serial control"):
        publisher.prepare(case.spec, case.store)
    assert not case.qualified_calls


@pytest.mark.parametrize("fault", ["only-upstream", "reordered", "duplicate"])
def test_upstream_freeze_still_requires_all_four_historical_cells(paired_review, fault):
    case = paired_review
    selected = case.spec["paired_calibration"]["historical_packages"]
    if fault == "only-upstream":
        selected[:] = case.spec["packages"]
    elif fault == "reordered":
        selected[0], selected[1] = selected[1], selected[0]
    else:
        selected[0] = selected[1]
    with pytest.raises(ValueError, match="four distinct historical packages|four original cells"):
        publisher.prepare(case.spec, case.store)
    assert not case.qualified_calls


def test_old_dx100_false_gain_is_retained_without_becoming_a_new_paired_input(paired_review):
    case = paired_review
    case.trials(case.seconds[0], 0.5)
    case.save()
    result = publisher.prepare(case.spec, case.store)
    calibration = result["freeze_request"]["settings"]["calibration"]
    old = calibration["historical_serial_control"]
    assert result["publishable"] and not result["unmet_gates"] and not result["gain_claim"]
    assert old["control"]["state"] == "numerical_gain_detected"
    assert old["admitted_for_new_sampling"] is False and old["unmet_gates"]
    assert [row["first_evaluation"] for row in old["control"]["pairs"]] == [
        item["evaluation"]["id"] for item in case.packets]
    assert old["control"]["pairs"][0]["directions"][0]["numerical_gain_leg"] is True
    assert len(calibration["repeatability_control"]["pairs"]) == 4
    assert not any(row["unmet_gates"] for row in calibration["repeatability_control"]["pairs"])
    for item in case.packets:
        for rid, digest in item["record_identities"].items():
            assert calibration["record_identities"][rid] == digest


def test_paired_publication_binds_observed_unsets_without_rewriting_old_blocks(paired_review):
    case = paired_review
    before = copy.deepcopy(case.packets)
    result = publisher.prepare(case.spec, case.store)
    settings = result['freeze_request']['settings']
    runtime = settings['native_runtime']
    assert result['publishable'] and runtime['version'] == 1
    assert runtime['environment'] == {
        'OMP_NUM_THREADS': '4', 'OMP_DYNAMIC': 'FALSE', 'OMP_PROC_BIND': 'close', 'OMP_PLACES': 'cores',
        **dict.fromkeys(RUNTIME_INHERITED)}
    evidence = settings['calibration']['native_runtime_evidence']
    assert len(evidence['evaluations']) == 8 and evidence['driver_receipt']
    assert case.packets == before
    assert all('native_runtime' not in block['build'] for pair in
               settings['calibration']['historical_serial_control']['control']['pairs'] for block in pair['blocks'])


@pytest.mark.parametrize('fault', ['missing-snapshot', 'missing-key', 'thread-limit', 'waiting',
                                  'unselected-member', 'unselected-controlled', 'missing-member',
                                  'unselected-boolean-version', 'unselected-float-version'])
def test_unsupported_calibration_runtime_keeps_review_unpublishable(paired_review, monkeypatch, fault):
    original = paired.qualify
    def changed(*args):
        control, primary = original(*args)
        environment = control['retained_driver']['inherited_runtime_settings']
        if fault == 'missing-snapshot': control.pop('retained_driver')
        elif fault == 'missing-key': environment.pop('GOMP_SPINCOUNT')
        elif fault == 'thread-limit': environment['OMP_THREAD_LIMIT'] = '1'
        elif fault == 'waiting': environment['OMP_WAIT_POLICY'] = 'invalid'
        elif fault == 'missing-member': control['pairs'][0]['evaluations'].pop('candidate')
        else:
            member = control['pairs'][0]['evaluations']['candidate']
            if fault == 'unselected-controlled': member['build']['execution_environment']['OMP_DYNAMIC'] = 'TRUE'
            else:
                member['build']['native_runtime'] = {'version': 1, 'environment': {
                    **member['build']['execution_environment'], **dict.fromkeys(RUNTIME_INHERITED)}}
                if fault == 'unselected-boolean-version':
                    member['build']['native_runtime']['version'] = True
                elif fault == 'unselected-float-version':
                    member['build']['native_runtime']['version'] = 1.0
                else:
                    member['build']['native_runtime']['environment']['GOMP_SPINCOUNT'] = '0'
        return control, primary
    monkeypatch.setattr(paired, 'qualify', changed)
    result = publisher.prepare(paired_review.spec, paired_review.store)
    assert result['publishable'] is False
    assert any('native runtime calibration is unsupported' in reason for reason in result['unmet_gates'])
    assert 'native_runtime' not in result['freeze_request']['settings']


@pytest.mark.parametrize('fault', ['missing-map', 'contradictory-controlled'])
def test_serial_runtime_requires_each_block_observation_not_current_shell(monkeypatch, fault):
    from swdb.bfs_native import controlled_environment
    runtime = {'version': 1, 'environment': {**controlled_environment(4), **dict.fromkeys(RUNTIME_INHERITED)}}
    blocks = [{'evaluation': name, 'context': {'threads': 4}, 'build': {
        'execution_environment': controlled_environment(4), 'native_runtime': copy.deepcopy(runtime)}}
              for name in ('first', 'second')]
    control = {'pairs': [{'blocks': blocks}]}
    actual, evidence = publisher.calibrated_runtime(control, False)
    assert actual == runtime and evidence['evaluations'] == ['first', 'second']
    if fault == 'missing-map': blocks[0]['build'].pop('native_runtime')
    else: blocks[0]['build']['execution_environment']['OMP_NUM_THREADS'] = '1'
    for key in RUNTIME_INHERITED:
        monkeypatch.setenv(key, 'recorded second block cannot supply the first block')
    with pytest.raises((Failure, ValueError), match='runtime'):
        publisher.calibrated_runtime(control, False)


@pytest.mark.parametrize("cell", range(4))
@pytest.mark.parametrize("factor", [0.5, 2])
def test_each_new_cell_and_label_direction_can_block_publication(paired_review, cell, factor):
    case = paired_review
    case.samples[cell]["candidate"] = [publisher.summary(vertex, [factor] * 10) for vertex in serial.SOURCES]
    result = publisher.prepare(case.spec, case.store)
    assert not result["publishable"] and not result["gain_claim"]
    assert any(f"new-cell-{cell}: unchanged-code" in reason for reason in result["unmet_gates"])
    assert not result["freeze_request"]["settings"]["calibration"]["historical_serial_control"]["unmet_gates"]


def test_paired_freeze_preserves_both_old_diagnostic_primary_scopes(paired_review):
    case = paired_review
    result = publisher.prepare(case.spec, case.store)
    settings = result["freeze_request"]["settings"]
    assert settings["sampling"] == SAMPLING
    assert settings["correctness"]["supporting_pilot_evidence"] == [
        case.new_primary[case.packets[index]["evaluation"]["id"]]["id"] for index in (1, 3)]
    old_rows = settings["calibration"]["native_pilots"]
    assert len(old_rows) == 2
    for row, index in zip(old_rows, (1, 3)):
        old = case.packets[index]
        assert row["evaluation"] == old["evaluation"]["id"]
        assert row["profile_package"] == old["package"]["id"]
        assert all(len(source["samples_seconds"]) == 5 for source in row["samples"])
        assert row["diagnostic_build"] == old["package"]["evidence"]["diagnostic_build"]
        for overhead in row["collector_overhead"]:
            assert overhead["primary_median_seconds"] == pytest.approx(1.02)
            assert overhead["observed_duration_ratio"] == pytest.approx(2 / 1.02)
    assert "historical five-trial primary" in settings["calibration"]["diagnostic_scope"]


@pytest.mark.parametrize("field", ["binary_sha256", "execution_environment", "threads", "roi"])
def test_new_primary_must_preserve_old_diagnostic_treatment(paired_review, field):
    case = paired_review
    primary = case.new_primary[case.packets[1]["evaluation"]["id"]]
    (primary["build"] if field in ("binary_sha256", "execution_environment") else primary["context"])[field] = "changed"
    with pytest.raises(ValueError, match="source/build/target treatment"):
        publisher.prepare(case.spec, case.store)


def test_shared_accelerator_gate_still_blocks_a_passing_paired_study(paired_review, monkeypatch):
    case = paired_review
    # Restore the real gate: no accelerator packages were supplied by this
    # synthetic study, so native A/A alone must not make it publishable.
    import runpy
    actual = runpy.run_path(str(Path(publisher.__file__)))
    monkeypatch.setattr(publisher, "accelerator_gate", actual["accelerator_gate"])
    result = publisher.prepare(case.spec, case.store)
    assert not result["publishable"] and not result["gain_claim"]
    assert any("accelerator" in reason for reason in result["unmet_gates"])
    assert not result["freeze_request"]["settings"]["calibration"]["historical_serial_control"]["unmet_gates"]
    assert result["freeze_request"]["settings"]["calibration"]["accelerator_size_evidence"] == {
        "executions": [], "repeatability": []}


@pytest.mark.parametrize("fault", ["missing", "mapping", "bare", "wrong-node"])
def test_qualifier_requires_verified_lane_observations_even_when_consistently_resealed(admission_case, fault):
    """The real driver reader must reject loss of whole-study lane evidence."""
    case = admission_case
    sample_path = Path(case.receipt["rss"]["samples"]["path"])
    samples = [json.loads(line) for line in sample_path.read_text().splitlines()]
    value = {"mapping": {"id": "mbit10-evaluation-node1", "fixture": True},
             "bare": "mbit10-evaluation-node1",
             "wrong-node": "mbit10-evaluation-node0 (verified: affinity, bind:0, lease held, generation 375)"}
    for record in [case.receipt, *samples]:
        if fault == "missing":
            record.pop("lane", None)
        else:
            record["lane"] = value[fault]
    sample_path.write_text("".join(json.dumps(row) + "\n" for row in samples))
    case.receipt["rss"]["samples"]["sha256"] = artifacts.file_hash(sample_path)
    ref = case.spec["paired_calibration"]["driver_receipt"]
    Path(ref["path"]).write_text(json.dumps(case.receipt))
    ref["sha256"] = artifacts.file_hash(ref["path"])
    with pytest.raises((ValueError, Failure), match="lane"):
        paired.qualify(case.spec, case.packets, case.store, {}, [])


@pytest.mark.parametrize("fault", ["missing", "missing-key", "bad-value"])
def test_qualifier_retains_explicit_fresh_inherited_runtime_observations(admission_case, fault):
    case = admission_case
    observed = dict.fromkeys(("OMP_THREAD_LIMIT", "OMP_WAIT_POLICY", "GOMP_SPINCOUNT", "GOMP_CPU_AFFINITY"))
    case.receipt["inherited_runtime_settings"] = observed
    if fault == "missing":
        case.receipt.pop("inherited_runtime_settings")
    elif fault == "missing-key":
        observed.pop("OMP_WAIT_POLICY")
    else:
        observed["OMP_WAIT_POLICY"] = False
    ref = case.spec["paired_calibration"]["driver_receipt"]
    Path(ref["path"]).write_text(json.dumps(case.receipt))
    ref["sha256"] = artifacts.file_hash(ref["path"])
    with pytest.raises((ValueError, Failure), match="runtime"):
        paired.qualify(case.spec, case.packets, case.store, {}, [])
