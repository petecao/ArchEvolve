"""Linux confinement through public submit. Updated: 2026-09-29 ET.

Run on mbit10 inside socket_lane.sh. Probes report actual kernel results in
retained fixture events; these are confinement checks, not provider evidence.
"""
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

from test_provider_workspace import proposal_setup

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Landlock ABI 4 checks require Linux")


@pytest.mark.parametrize("probe,blocked", [("inside_read", False), ("outside_read", True),
                                         ("outside_write", True), ("outside_tcp", True),
                                         ("allowed_tcp", False)])
def test_guard_confines_actual_fixture_syscalls(proposal_setup, tmp_path, probe, blocked):
    records, runs, snapshot, request = proposal_setup
    program = tmp_path / "guard-fixture.py"
    plan = tmp_path / "guard-plan.json"
    outside = records.path / "implementations/gapbs-bfs-do.yaml"
    plan.write_text(json.dumps({"probe": probe, "outside": str(outside)}))
    program.write_text('''import json,sys,socket,errno
from pathlib import Path
if "--version" in sys.argv:
 print("guard-fixture-1");raise SystemExit(0)
plan=json.loads(Path(sys.argv[1]).read_text())
probe=plan["probe"]
observed="allowed"
try:
 if probe=="inside_read": Path("src/bfs.cc").read_text()
 elif probe=="outside_read": Path(plan["outside"]).read_text()
 elif probe=="outside_write": Path("../forbidden.txt").write_text("forbidden")
 elif probe=="outside_tcp": socket.create_connection(("1.1.1.1",80),5).close()
 elif probe=="allowed_tcp": socket.create_connection(("1.1.1.1",443),5).close()
except OSError as e: observed="blocked:"+str(e.errno)
if probe=="outside_read": command="cat "+plan["outside"]
elif probe=="outside_write": command="printf forbidden > ../forbidden.txt"
elif probe=="outside_tcp": command="python -c 'socket.create_connection((\\\"1.1.1.1\\\",80))'"
else: command="guard-fixture transport or workspace probe"
print(json.dumps({"type":"item.completed","item":{"type":"command_execution","command":command,"exit_code":0,"aggregated_output":observed}}),flush=True)
path=Path("src/bfs.cc")
path.write_text(path.read_text().replace("int alpha = 15","int alpha = 14"))
result={"interpretation":"Confinement probe with parameter rewrite.","unresolved":[]}
Path(sys.argv[sys.argv.index("--output-last-message")+1]).write_text(json.dumps(result))
print(json.dumps({"type":"turn.completed","usage":{"output_tokens":1}}),flush=True)
''')
    config = tmp_path / "guard-config.yaml"
    config.write_text(yaml.safe_dump({"kind": "external_fixture", "emulates": "codex",
        "command": [sys.executable, str(program), str(plan)], "workspace": True,
        "timeout_s": 30, "total_seconds": 60}))
    result = records.swdb("submit", request(payload={"kind": "natural_language", "content": "Set alpha to 14."}),
                          "--provider-config", config, "--runs-dir", runs, "--format", "json")
    assert result.stdout, result.stderr
    proposal = json.loads(result.stdout)
    meta = proposal["attempts"][0]["provider"]
    policy = meta["guard_policy"]
    assert policy["enforced"] is True and policy["landlock_abi"] >= 4
    assert policy["tcp_connect_ports"] == [443] and policy["inner_tcp_connect_ports"] == []
    assert policy["limits"] == {"threads": 16, "memory_bytes": 32 * 1024**3,
                                "command_seconds": 120, "workspace_bytes": 5 * 1024**3}
    log = Path(meta["audit"]["raw_log"]["path"])
    event = next(json.loads(line) for line in log.read_text().splitlines() if '"command_execution"' in line)
    observed = event["item"]["aggregated_output"]
    assert observed == "blocked:13" if blocked else observed == "allowed"
    assert result.returncode == (1 if blocked else 0), proposal["outcome"]
    assert meta["audit"]["passed"] is not blocked
    assert meta["workspace_manifest"]["login_copy_deleted"] is True
    assert not (Path(meta["workspace_manifest"]["root"]).parent / "forbidden.txt").exists()


RESOURCE_PROGRAM = '''import json, os, subprocess, sys, threading, time
from pathlib import Path
if "--version" in sys.argv:
 print("resource-guard-fixture-1"); raise SystemExit(0)
mode = json.loads(Path(sys.argv[1]).read_text())["mode"]
pidfile = Path("build/resource-pid.json")
pidfile.write_text(json.dumps({"provider": os.getpid()}))
print(json.dumps({"type":"item.completed", "item":{"type":"command_execution", "command":"local resource fixture probe", "exit_code":0, "aggregated_output":"started:"+mode}}), flush=True)
if mode == "threads":
 gate = threading.Event()
 for number in range(17):
  threading.Thread(target=gate.wait, daemon=True).start()
elif mode == "workspace":
 # Two sparse files cross the actual aggregate 5 GiB allowance without
 # allocating 6 GiB physically. Each file stays below RLIMIT_FSIZE.
 for name in ("resource-growth-a.bin", "resource-growth-b.bin"):
  with Path("build", name).open("wb") as handle:
   handle.truncate(3 * 1024**3)
elif mode == "command_timeout":
 command = subprocess.Popen(["/usr/bin/sleep", "130"])
 pidfile.write_text(json.dumps({"provider":os.getpid(), "command":command.pid}))
print(json.dumps({"type":"item.completed", "item":{"type":"command_execution", "command":"local resource fixture probe", "exit_code":0, "aggregated_output":"allocated:"+mode}}), flush=True)
if mode == "command_timeout": command.wait()
else: time.sleep(10)
Path("build/unexpected-completion.json").write_text("{}")
result={"interpretation":"Resource fixture completed unexpectedly.", "unresolved":[]}
Path(sys.argv[sys.argv.index("--output-last-message")+1]).write_text(json.dumps(result))
print(json.dumps({"type":"turn.completed"}), flush=True)
'''


@pytest.mark.parametrize("mode,reason", [
    ("threads", "provider resource limit exceeded"),
    ("workspace", "provider workspace exceeds"),
    ("command_timeout", "provider tool command exceeds the 120 s wall-time limit"),
])
def test_public_submit_enforces_actual_resource_overruns(proposal_setup, tmp_path, mode, reason):
    records, runs, _, request = proposal_setup
    program, plan = tmp_path / "resource-fixture.py", tmp_path / "resource-plan.json"
    program.write_text(RESOURCE_PROGRAM)
    plan.write_text(json.dumps({"mode": mode}))
    config = tmp_path / "resource-config.yaml"
    config.write_text(yaml.safe_dump({"kind":"external_fixture", "emulates":"codex", "workspace":True,
        "command":[sys.executable, str(program), str(plan)], "timeout_s":150, "total_seconds":180}))
    result = records.swdb("submit", request(payload={"kind":"natural_language", "content":"Set alpha to 14."}),
                          "--provider-config", config, "--runs-dir", runs, "--format", "json")
    assert result.stdout, result.stderr
    proposal = json.loads(result.stdout)
    assert result.returncode == 1 and proposal["outcome"]["state"] == "failed", proposal["outcome"]
    assert reason in proposal["outcome"]["reason"] and "candidate" not in proposal
    meta = proposal["attempts"][0]["provider"]
    assert meta["classification"] == "contract_fixture" and meta["guard_policy"]["enforced"]
    if mode == "command_timeout":
        assert 120 <= meta["host_wall_s"] < 130, "fixture reached its own completion instead of being stopped by the guard"
    else:
        assert meta["host_wall_s"] < 10, "fixture reached its own completion instead of being stopped by the guard"
    violations = meta["audit"]["violations"]
    assert any(v["code"] == "resource_limit" and reason in v["reason"] for v in violations)
    assert not any(v["code"] == "outbound_connection" for v in violations)
    assert not meta["guard_result"]["passed"]
    assert any(reason in r for r in meta["guard_result"]["reasons"])
    workspace = Path(meta["workspace_manifest"]["root"])
    assert not (workspace / "build/unexpected-completion.json").exists()
    assert meta["workspace_manifest"]["login_copy_deleted"]
    assert not (Path(meta["workspace_manifest"]["home"]) / "auth.json").exists()
    policy = meta["guard_policy"]
    assert policy["limits"]["threads"] == 16 and policy["limits"]["memory_bytes"] == 32*1024**3
    assert policy["limits"]["command_seconds"] == 120
    assert policy["limits"]["workspace_bytes"] == 5*1024**3 and "test_override" not in policy
    if mode == "threads":
        measured = next(r for r in meta["guard_result"]["reasons"] if reason in r)
        assert int(re.search(r"threads=(\d+)", measured)[1]) > 16
    elif mode == "workspace":
        growth = [workspace / "build" / name for name in ("resource-growth-a.bin", "resource-growth-b.bin")]
        assert sum(p.stat().st_size for p in growth) == 6*1024**3
        assert all(p.stat().st_size < policy["limits"]["workspace_bytes"] for p in growth)
        assert sum(p.stat().st_blocks*512 for p in growth) < 1024**2
        assert sum(p.stat().st_size for p in workspace.rglob("*") if p.is_file()) > policy["limits"]["workspace_bytes"]
    later = records.swdb("get", proposal["id"], "--format", "json")
    assert later.returncode == 0
    assert json.loads(later.stdout)["attempts"][0]["provider"]["audit"] == meta["audit"]
