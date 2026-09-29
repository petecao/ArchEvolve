"""Linux confinement through public submit. Updated: 2026-09-29 ET.

Run on mbit10 inside socket_lane.sh. Probes report actual kernel results in
retained fixture events; these are confinement checks, not provider evidence.
"""
import json
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
