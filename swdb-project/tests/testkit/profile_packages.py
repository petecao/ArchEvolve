"""Profile-package fixtures: one evaluated candidate artifact per module and package
assembly helpers. Created 2026-10-05 ET (code review T1), from
tests/test_profile_packages.py."""

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from conftest import make_records
from testkit.bfs_native import build_evaluation_setup
from testkit.bfs_protocol import _payload
from testkit.proposals import build_proposal_setup


def _read(records, rid):
    result = records.swdb("get", rid, "--format", "json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def package_seed(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("package-seed")
    records = make_records(tmp)
    proposal = build_proposal_setup(records, tmp)
    records, runs, evaluate, base = build_evaluation_setup(proposal, tmp)
    records.copy_repo("strategies", "intrinsics", "operations")
    evaluated = records.swdb("evaluate", evaluate(id="package-evaluation"), "--runs-dir", runs, "--format", "json")
    assert evaluated.returncode == 0, evaluated.stderr
    evaluation = json.loads(evaluated.stdout)
    candidate = _read(records, evaluation["candidate"])
    file = Path(candidate["artifact"]["path"]) / "src/bfs.cc"
    raw = file.read_bytes()
    regions, lines = [], raw.splitlines(keepends=True)
    for kind, first, last in (("function", 67, 89), ("loop", 74, 85)):
        start, end = sum(map(len, lines[:first-1])), sum(map(len, lines[:last]))
        fragment = raw[start:end]
        regions.append({"id": f"fixture-{kind}", "kind": kind, "path": "src/bfs.cc", "lines": [first,last],
                        "byte_range": [start,end], "source_sha256": hashlib.sha256(fragment).hexdigest(),
                        "text": fragment.decode(), "function": "TDStep", "callers": ["DOBFS"], "helpers": [],
                        "metrics": {"inclusive_thread_cpu_seconds": 0.02, "exclusive_thread_cpu_seconds": 0.01, "invocations": 3},
                        "basis": "measured", "scope": "accumulated diagnostic ROI; contract fixture",
                        "artifact_sha256": "d"*64, "source_artifact_sha256": candidate["artifact"]["sha256"]})
    executions, memory = [], []
    for position, source_id in enumerate(evaluation["context"]["sources"]):
        for kind in ("regions", "memory"):
            output = tmp / f"fixture-{kind}-{position}.json"
            output.write_text(json.dumps({"source": source_id, "contract_fixture": True, "value": 123}))
            sha = hashlib.sha256(output.read_bytes()).hexdigest()
            execution = {"kind": kind, "source": source_id, "source_position": position, "repetition": 0,
                         "binary_sha256": "d"*64, "output": str(output), "output_sha256": sha,
                         "evidence_kind": "contract_fixture"}
            if kind == "regions":
                execution.update(region_output=str(output), region_output_sha256=sha)
            else:
                execution.update(raw_artifact=str(output), raw_sha256=sha)
                memory.append({"metric": "data_reads", "available": True, "value": 123, "unit": "accesses",
                               "definition": "fixture cache-model read accesses", "basis": "simulated", "scope": "ROI",
                               "collector": "fixture-model", "artifact_sha256": "d"*64,
                               "source_artifact_sha256": candidate["artifact"]["sha256"],
                               "execution": {"source": source_id, "source_position": position, "repetition": 0},
                               "raw_artifact": str(output), "raw_sha256": sha})
            executions.append(execution)
    profile = {key: copy.deepcopy(evaluation[key]) for key in ("schema_version", "status", "created", "updated", "provenance", "message_version", "producer")}
    profile.update(kind="region_profile", id="package-diagnostics", request={"fixture": True},
                   build={"native_runtime": copy.deepcopy(evaluation['build']['native_runtime'])},
                   evaluation=evaluation["id"], candidate=candidate["id"], source_snapshot=candidate["source_snapshot"],
                   implementation=candidate["implementation"], machine=evaluation["machine"],
                   context={**copy.deepcopy(evaluation["context"]), "primary_binary_sha256": evaluation["build"]["binary_sha256"]},
                   discovery={"backend": "contract-fixture", "scope": "two fixture regions", "limitations": ["fixture attribution only"]},
                   outcome={"state": "complete", "stage": "completed", "reason": None}, stages=[], regions=regions,
                   dynamic_memory=memory, executions=executions, raw_artifacts=[], reasons=[], gain_claim=False)
    added = records.swdb("add", _payload(tmp, "profile", profile))
    assert added.returncode == 0, added.stderr
    context = evaluation["context"]
    request = {"message_version": "1.0", "id": "assembled", "implementation": evaluation["implementation"],
               "evaluation": evaluation["id"], "region_profile": profile["id"],
               "context": {"source_sha256": context["candidate_sha256"], "canonical_graph_sha256": context["workload"]["canonical_sha256"],
                           "sources": context["sources"], "target": context["target"], "target_configuration": context["backend_configuration"],
                           "threads": context["threads"], "roi": context["roi"]}}
    return records, request, evaluation, profile, candidate


@pytest.fixture
def package_setup(package_seed, records):
    source, request, evaluation, profile, candidate = package_seed
    shutil.copytree(source.path, records.path, dirs_exist_ok=True)
    return records, copy.deepcopy(request), copy.deepcopy(evaluation), copy.deepcopy(profile), copy.deepcopy(candidate)


def _assemble(records, tmp, request):
    result = records.swdb("profile-package", _payload(tmp, request["id"], request), "--format", "json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _callgrind_profile(profile, tmp_path, fault=None):
    """Actual a3 counter patterns in synthetic, explicitly fixture executions."""
    rows = []
    for original in profile['dynamic_memory']:
        events = {'Dr': 200, 'Dw': 100, 'D1mr': 20, 'D1mw': 10, 'DLmr': 5, 'DLmw': 3}
        if fault == 'a3-underflow':
            events.update(Dr=0, Dw=2**64-7, D1mw=2**64-3, DLmw=2**64-3)
        elif fault == 'misses-exceed-references': events['D1mr'] = 201
        elif fault == 'll-exceeds-l1': events['DLmr'] = 21
        elif fault == 'noninteger': events['Dw'] = 0.5
        elif fault == 'write-only': events.update(Dr=0, D1mr=0, DLmr=0)
        elif fault == 'one-bad-execution' and original['execution']['source_position'] == 0:
            events['Dw'] = 2**64-7
        raw = tmp_path / f"callgrind-{original['execution']['source_position']}.out"
        totals = ' '.join(map(str, [1000, *events.values()]))
        raw.write_text('events: Ir ' + ' '.join(events) + '\nsummary: ' + totals + '\ntotals: ' + totals + '\n')
        digest = hashlib.sha256(raw.read_bytes()).hexdigest()
        for execution in profile['executions']:
            if execution['kind'] == 'memory' and execution['source_position'] == original['execution']['source_position']:
                execution.update(raw_artifact=str(raw), raw_sha256=digest)
        for metric, value in events.items():
            rows.append({**copy.deepcopy(original), 'metric': metric, 'value': value,
                         'raw_artifact': str(raw), 'raw_sha256': digest,
                         'unit': 'references' if metric in ('Dr', 'Dw') else 'misses',
                         'collector': {'name': 'Callgrind', 'version': 'explicit contract fixture'}})
        if fault == 'duplicate': rows.append(copy.deepcopy(rows[-1]))
        if fault == 'split-raw-identity': rows[-1]['raw_sha256'] = 'a' * 64
    profile['dynamic_memory'] = rows
    return profile
