"""Native evaluation fixtures: the external compiler fixture program and an evaluation
request writer over a submitted candidate artifact. Created 2026-10-05 ET (code review T1),
from tests/test_bfs_native.py. Durations are fixture values, never evidence."""

import json
import socket

import pytest
import yaml

PROGRAM = r'''#!/usr/bin/env python3
import json, os, signal, subprocess, sys, time
from collections import deque
from pathlib import Path
mode = os.environ.get("SWDB_NATIVE_FIXTURE", "pass")
tokens = Path(sys.argv[1]).read_text().split()
n = int(tokens[1])
source = int(sys.argv[2])
out = Path(sys.argv[3])
adj = [[] for _ in range(n)]
for i in range(4, len(tokens), 2):
    adj[int(tokens[i])].append(int(tokens[i+1]))
parent = [-1] * n
parent[source] = source
q = deque([source])
while q:
    u = q.popleft()
    for v in (reversed(adj[u]) if mode == "alternate" else adj[u]):
        if parent[v] == -1:
            parent[v] = u
            q.append(v)
if mode in {"hang", "interrupt_second"} and (mode == "hang" or out.name == "trial-0-1.json"):
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    Path(os.environ["SWDB_NATIVE_PID_FILE"]).write_text(str(child.pid))
    time.sleep(120)
if mode == "exit_zero_fail":
    print("Verification: PASS")
    print("Verification: FAIL")
    parent[source] = -1
if mode == "wrong_depth": parent[3] = 0
if mode == "out_of_range": parent[-1] = n
if mode == "wrong_source": parent[source] = -1
if mode == "reachability": parent[-1] = source
if mode == "missing": sys.exit(0)
data = {"format": "swdb.bfs.native.trial.v1", "source": source,
        "configured_threads": int(os.environ["OMP_NUM_THREADS"]),
        "roi": "bfs.complete_call.v1", "duration_s": 0.025, "parents": parent}
if mode == "no_time": data.pop("duration_s")
if mode == "bool_source": data["source"] = bool(source)
out.write_text(json.dumps(data))
'''


def build_evaluation_setup(proposal_setup, tmp_path):
    records, runs, snapshot, proposal_request = proposal_setup
    keep = {"applications/gapbs.yaml", "kernels/gapbs-bfs.yaml", "implementations/gapbs-bfs-do.yaml",
            "machines/mbit10.yaml", "source_snapshots/test-source.yaml", "profile_packages/test-package.yaml"}
    for record in records.path.rglob("*.yaml"):
        if record.relative_to(records.path).as_posix() not in keep:
            record.unlink()
    impl = records.read("implementations/gapbs-bfs-do.yaml")
    impl["verification"] = {"status": "unchecked", "evidence": [], "scope": "Isolated contract fixture."}
    records.write("implementations/gapbs-bfs-do.yaml", impl)
    machine = records.read("machines/mbit10.yaml")
    machine.update(id="native-testhost", hostname=socket.gethostname().split(".")[0], lane_required=False)
    records.write("machines/native-testhost.yaml", machine)
    submitted = records.swdb("submit", proposal_request(), "--runs-dir", runs, "--format", "json")
    assert submitted.returncode == 0, submitted.stderr
    candidate = json.loads(submitted.stdout)["candidate"]
    compiler = tmp_path / "fixture-cxx"
    compiler.write_text("#!/usr/bin/env python3\nimport os,sys\nfrom pathlib import Path\n"
                        "if '--version' in sys.argv:\n print('SWDB external compiler contract fixture v1'); sys.exit(0)\n"
                        "if os.environ.get('SWDB_NATIVE_FIXTURE') == 'build_fail': sys.exit(7)\n"
                        f"p=Path(sys.argv[sys.argv.index('-o')+1]); p.write_text({PROGRAM!r}); p.chmod(0o755)\n")
    compiler.chmod(0o755)
    base = {"message_version": "1.0", "id": "eval-fixture", "candidate": candidate,
            "machine": "native-testhost", "threads": 1, "sources": [0], "repetitions": 1,
            "roi": "bfs.complete_call.v1", "fixture": True,
            "comparison_baseline": "gapbs-bfs-do",
            "build": {"compiler": str(compiler), "flags": ["-std=c++11", "-O2"]},
            "budget": {"build_seconds": 10, "run_seconds": 5, "total_seconds": 60},
            "workload": {"family": "contract_fixture", "graph": {"num_vertices": 5, "directed": True,
                           "edges": [[0,1], [0,2], [1,3], [2,3]]}}}

    def request(**changes):
        data = {**base, **changes}
        file = tmp_path / f"{data['id']}.yaml"
        file.write_text(yaml.safe_dump(data))
        return file
    return records, runs, request, base


@pytest.fixture
def evaluation_setup(proposal_setup, tmp_path):
    return build_evaluation_setup(proposal_setup, tmp_path)


def evaluate(setup, mode="pass", **changes):
    records, runs, request, _ = setup
    result = records.swdb("evaluate", request(**changes), "--runs-dir", runs, "--format", "json",
                         env={"SWDB_NATIVE_FIXTURE": mode, "SWDB_NATIVE_PID_FILE": str(runs / "child.pid")})
    assert result.stdout, result.stderr
    return result, json.loads(result.stdout)
