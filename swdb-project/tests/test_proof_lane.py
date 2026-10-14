"""Proof workers in a socket lane (Probata proof of concept ticket 57).

Created: 2026-10-14 ET. Seams: `swdb prove-lane run` (a batch plan in, proof records and a batch
record out), `swdb prove-lane compare`, `swdb prove` under a worker's RSS watchdog, and `swdb validate`
/ `swdb build` on the records a lane batch writes. Fixture records only (scripted adapter, contract
fixtures); tool jobs run small Python commands. The Mac pins no core, so core choice is checked on a
fake sysfs topology; mbit10 runs the real batch (ticket 57's Answer).
"""

import json
import shutil
import sys

import pytest
import yaml

from conftest import run_swdb
from test_proof_records import ASSUMPTION, FUNCTION, proof_seed  # noqa: F401  (the certified fixture candidate)

JOB_FIELDS = {"adapter", "host", "worker_core", "wall_seconds", "cpu_seconds", "batch_load", "peak_rss_bytes",
              "batch", "position"}
MB = 1024 * 1024
LAB = "swdb-fixture-lab"          # a fixture machine that requires no lane (the Mac stands in for it)


def _alloc(megabytes, hold=1.5):
    """A command whose RSS climbs to `megabytes` and holds there (a tool that eats memory)."""
    return [sys.executable, "-c",
            f"import time\nb=[]\nfor _ in range({megabytes // 10}):\n b.append(b'\\x01'*(10*1024*1024))\n"
            f" time.sleep(0.01)\ntime.sleep({hold})\nprint('done')"]


def _say(text):
    return [sys.executable, "-c", f"print({text!r})"]


@pytest.fixture
def lane(proof_seed, tmp_path):
    source, candidate = proof_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    machine = yaml.safe_load((tmp_path / "records" / "machines" / "mbit10.yaml").read_text())
    machine.update(id=LAB, hostname=LAB, lane_required=False)
    (tmp_path / "records" / "machines" / f"{LAB}.yaml").write_text(yaml.safe_dump(machine, sort_keys=False))
    return Lane(tmp_path, candidate)


class Lane:
    def __init__(self, root, candidate):
        self.root, self.candidate = root, candidate
        self.records = root / "records"
        self.runs = root / "runs-outside-repo"

    def script(self, name, **data):
        data.setdefault("verdict", "proven")
        data.setdefault("bounds", {"threads": 1})
        data.setdefault("assumptions", [ASSUMPTION])
        path = self.root / f"script-{name}.yaml"
        path.write_text(yaml.safe_dump(data))
        return path

    def prove_job(self, configuration, subject, **script):
        path = self.script(f"{configuration}-{subject}", **script)
        return {"configuration": configuration, "subject": subject,
                "prove": ["--candidate", self.candidate, "--function", FUNCTION, "--adapter", "scripted",
                          "--script", str(path)]}

    def plan(self, jobs, **extra):
        data = {"plan": "proof_lane_batch.1", "machine": LAB, "workers": 2, "jobs": jobs, **extra}
        path = self.root / f"plan-{len(list(self.root.glob('plan-*')))}.yaml"
        path.write_text(yaml.safe_dump(data, sort_keys=False))
        return path

    def run(self, plan, *extra, ok=True):
        result = run_swdb("prove-lane", "run", plan, "--records", self.records, "--runs-dir", self.runs,
                          "--format", "json", *extra)
        assert (result.returncode == 0) is ok, result.stderr + result.stdout
        return json.loads(result.stdout) if ok else result

    def record(self, rid):
        return yaml.safe_load((self.records / "proofs" / f"{rid}.yaml").read_text())

    def swdb(self, command, *args):
        db = ["--db", self.root / "build" / "swdb.sqlite"] if command in {"build", "sql"} else []
        return run_swdb(command, "--records", self.records, *db, *args)


# --- a batch, its order and its records ------------------------------------------------------

def test_a_grouped_plan_runs_interleaved_and_the_records_show_the_order(lane):
    jobs = [lane.prove_job("A", "s1"), lane.prove_job("A", "s2"), lane.prove_job("B", "s1"),
            lane.prove_job("B", "s2")]
    batch = lane.run(lane.plan(jobs))
    assert batch["order"]["interleaved_as_given"] is False
    order = [(job["configuration"], job["subject"]) for job in batch["jobs"]]
    assert order == [("A", "s1"), ("B", "s1"), ("A", "s2"), ("B", "s2")]
    for position, job in enumerate(batch["jobs"], start=1):
        record = lane.record(job["record"])
        assert set(record["job"]) == JOB_FIELDS
        assert record["job"]["batch"] == batch["batch"] and record["job"]["position"] == position
        assert record["verdict"] == job["verdict"] == "proven"
    assert lane.swdb("validate").returncode == 0
    assert lane.swdb("build").returncode == 0


def test_an_interleaved_plan_keeps_its_order(lane):
    jobs = [lane.prove_job("A", "s1"), lane.prove_job("B", "s1"), lane.prove_job("A", "s2"),
            lane.prove_job("B", "s2")]
    batch = lane.run(lane.plan(jobs))
    assert batch["order"]["interleaved_as_given"] is True
    assert [job["subject"] for job in batch["jobs"]] == ["s1", "s1", "s2", "s2"]


def test_a_plan_asking_for_seven_workers_is_refused(lane):
    result = lane.run(lane.plan([lane.prove_job("A", "s1")], workers=7), ok=False)
    assert result.returncode == 2 and "at most 6" in result.stderr
    assert not (lane.records / "proofs").exists()


def test_started_without_the_lane_script_the_batch_refuses_to_run(lane):
    result = lane.run(lane.plan([lane.prove_job("A", "s1")], machine="mbit10"), ok=False)
    assert result.returncode == 1 and "socket_lane.sh" in result.stderr
    assert not (lane.records / "proofs").exists()


def _lease_files(root, **states):
    root.mkdir(exist_ok=True)
    for name in ("mbit10-evaluation-node0", "mbit10-evaluation-node1", "mbit10-evaluation"):
        meta = {"state": states.get(name.replace("-", "_"), "released"),
                "lease": {"generation": 7, "acquired_at": "2026-10-14T05:00:00Z", "daemon_pid": 1}}
        (root / f"{name}.meta.json").write_text(json.dumps(meta))
    return {"LACT_LEASE_ROOT": str(root)}


def test_the_lease_check_records_both_socket_leases_and_the_legacy_one(tmp_path):
    out = tmp_path / "leases.json"
    env = _lease_files(tmp_path / "leases", mbit10_evaluation_node0="held")
    result = run_swdb("prove-lane", "leases", "--node", "1", "--out", out, "--format", "json", env=env)
    assert result.returncode == 0, result.stderr                  # node 0 busy: lane 1 is free
    states = json.loads(out.read_text())["states"]
    assert states == {"mbit10-evaluation-node0": "held", "mbit10-evaluation-node1": "released",
                      "mbit10-evaluation": "released"}
    held_own = run_swdb("prove-lane", "leases", "--node", "0", "--out", out, env=env)
    assert held_own.returncode == 1 and "mbit10-evaluation-node0 is held" in held_own.stderr
    legacy = run_swdb("prove-lane", "leases", "--node", "1", "--out", out,
                      env=_lease_files(tmp_path / "legacy", mbit10_evaluation="held"))
    assert legacy.returncode == 1 and "legacy lease" in legacy.stderr
    assert json.loads(out.read_text())["states"]["mbit10-evaluation"] == "held"   # recorded even when refused


def test_the_batch_record_holds_the_host_record_and_the_lease_check(lane):
    leases = lane.root / "leases.json"
    assert run_swdb("prove-lane", "leases", "--node", "1", "--out", leases,
                    env=_lease_files(lane.root / "leases")).returncode == 0
    batch = lane.run(lane.plan([lane.prove_job("A", "s1")]), "--lease-check", leases)
    saved = json.loads((lane.runs / batch["batch"] / "batch.json").read_text())
    assert saved["lease_check"]["states"]["mbit10-evaluation"] == "released"
    host = saved["host"]
    assert set(host["load"]) == {"start", "end"} and len(host["archevolve_commit"]) == 40
    assert "lane_node_free_memory" in host["start"] and "lane_node_free_memory" in host["end"]
    assert saved["workers"] == 1                                   # never more workers than jobs
    assert saved["rss_cap_bytes"] == 8 * 1024 * MB                 # design O9 default


# --- the RSS watchdog ------------------------------------------------------------------------

def test_a_tool_job_above_the_rss_cap_ends_out_of_memory_and_the_others_carry_on(lane):
    jobs = [{"configuration": "A", "subject": "hungry", "tool": {"command": _alloc(400), "bounds": {"threads": 1}}},
            {"configuration": "A", "subject": "calm", "tool": {
                "command": _say("VERIFICATION SUCCESSFUL"), "bounds": {"threads": 1},
                "verdicts": [{"verdict": "proven", "exit": 0, "output": "VERIFICATION SUCCESSFUL"}]}},
            {"configuration": "A", "subject": "buggy", "tool": {
                "command": _say("x=41 VERIFICATION FAILED"), "bounds": {"threads": 1},
                "verdicts": [{"verdict": "refuted", "exit": 0, "output": "VERIFICATION FAILED"}]}}]
    batch = lane.run(lane.plan(jobs, rss_cap_bytes=150 * MB, workers=3))
    by = {job["subject"]: job for job in batch["jobs"]}
    assert by["hungry"]["verdict"] == "not_proven" and by["hungry"]["failure_class"] == "out_of_memory"
    assert by["hungry"]["job"]["peak_rss_bytes"] > 150 * MB
    assert by["calm"]["verdict"] == "proven" and by["buggy"]["verdict"] == "refuted"
    assert "x=41" in by["buggy"]["counterexample"]["output_lines"][0]
    for job in batch["jobs"]:
        assert set(job["job"]) == JOB_FIELDS and job["job"]["adapter"] == "none"
        saved = json.loads((lane.runs / batch["batch"] / "jobs" / f"{job['job']['position']}.json").read_text())
        assert saved["verdict"] == job["verdict"]
        log = lane.runs / batch["batch"] / "jobs" / f"{job['job']['position']}.log"
        assert saved["log"]["path"] == str(log) and log.exists()
    assert not list((lane.runs / batch["batch"] / "jobs").glob("*.scratch"))     # scratch gone when each job ends


def test_a_tool_job_with_no_matching_verdict_is_not_proven_unknown(lane):
    job = {"configuration": "A", "subject": "odd", "tool": {
        "command": _say("something else"), "bounds": {"threads": 1},
        "verdicts": [{"verdict": "proven", "exit": 0, "output": "VERIFICATION SUCCESSFUL"}]}}
    done = lane.run(lane.plan([job]))["jobs"][0]
    assert done["verdict"] == "not_proven" and done["failure_class"] == "unknown"


def test_a_prove_job_whose_tool_passes_the_cap_gets_an_out_of_memory_record(lane):
    batch = lane.run(lane.plan([lane.prove_job("A", "hungry", run=_alloc(400)),
                                lane.prove_job("A", "calm")], rss_cap_bytes=200 * MB))
    by = {job["subject"]: lane.record(job["record"]) for job in batch["jobs"]}
    assert by["hungry"]["verdict"] == "not_proven" and by["hungry"]["failure_class"] == "out_of_memory"
    assert by["hungry"]["job"]["peak_rss_bytes"] > 200 * MB
    assert by["calm"]["verdict"] == "proven"
    assert lane.swdb("validate").returncode == 0


def test_the_job_block_peak_rss_is_what_the_worker_watchdog_read(lane):
    batch = lane.run(lane.plan([lane.prove_job("A", "medium", run=_alloc(120, hold=1.0))], rss_cap_bytes=1024 * MB))
    record = lane.record(batch["jobs"][0]["record"])
    assert record["verdict"] == "proven" and record["job"]["peak_rss_bytes"] >= 120 * MB


# --- comparing a batch with the same jobs run alone -----------------------------------------------

def test_compare_finds_matching_and_differing_verdicts(lane):
    jobs = [lane.prove_job("A", "s1"), lane.prove_job("B", "s1")]
    first = lane.run(lane.plan(jobs))
    alone = lane.run(lane.plan(jobs, workers=1))
    paths = [lane.runs / b["batch"] / "batch.json" for b in (first, alone)]
    same = run_swdb("prove-lane", "compare", *paths, "--format", "json")
    assert same.returncode == 0, same.stderr
    assert json.loads(same.stdout)["matching"] == 2
    other = lane.run(lane.plan([lane.prove_job("A", "s1", verdict="not_proven", failure_class="timeout"),
                                lane.prove_job("B", "s1")]))
    differ = run_swdb("prove-lane", "compare", paths[0], lane.runs / other["batch"] / "batch.json", "--format", "json")
    assert differ.returncode == 1 and "A s1" in differ.stderr


# --- cores --------------------------------------------------------------------------------------

def test_workers_get_one_logical_cpu_per_physical_core(tmp_path):
    """mbit10's node 1 shape: even/odd CPUs per node, sibling i+32 of each core."""
    from swdb.proof_lane import physical_cores
    for cpu in range(64):
        topology = tmp_path / f"cpu{cpu}" / "topology"
        topology.mkdir(parents=True)
        topology.joinpath("thread_siblings_list").write_text(f"{cpu % 32},{cpu % 32 + 32}\n")
    allowed = set(range(1, 64, 2))
    cores = physical_cores(allowed, tmp_path)
    assert len(cores) == 16 and all(cpu in allowed for cpu in cores)
    assert len({cpu % 32 for cpu in cores}) == 16                  # never two hyperthread siblings
