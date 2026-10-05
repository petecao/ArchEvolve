"""Linux confinement through public submit. Updated: 2026-10-05 ET (ticket 74: split thread caps, lane CPUs).

Run on mbit10 inside socket_lane.sh. Probes report actual kernel results in
retained fixture events; these are confinement checks, not provider evidence.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from swdb import provider_guard
from test_provider_workspace import proposal_setup

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Landlock ABI 4 checks require Linux")


def test_standalone_probe_uses_registered_fixture_and_owned_cleanup(tmp_path):
    project = Path(__file__).resolve().parents[1]
    folder = tmp_path / "guard-probe"
    result = subprocess.run([sys.executable, str(project / "scripts/provider_guard_spike.py"),
                             "probe", "--runs-dir", str(folder)], cwd=project,
                            env={**os.environ, "PYTHONPATH": str(project)},
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads((folder / "receipt.json").read_text())
    assert receipt["kind"] == "probe" and receipt["passed"]
    assert receipt["guard_policy"]["model_api"] == {"hosts": [], "addresses": []}
    assert receipt["guard_policy"]["process_ownership"]["subreaper"] is True
    assert receipt["guard_audit"]["passed"]
    assert receipt["guard_audit"]["original_provider"] is not None
    assert receipt["guard_audit"]["process_cleanup"]["passed"]
    assert receipt["guard_audit"]["process_cleanup"]["survivors"] == []


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
    assert policy["limits"] == {"threads": 16, "runtime_threads": 64, "memory_bytes": 32 * 1024**3,
                                "command_seconds": 120, "workspace_bytes": 5 * 1024**3}
    assert policy["lane_cpus"] == sorted(os.sched_getaffinity(0))
    log = Path(meta["audit"]["raw_log"]["path"])
    event = next(json.loads(line) for line in log.read_text().splitlines() if '"command_execution"' in line)
    observed = event["item"]["aggregated_output"]
    assert observed == "blocked:13" if blocked else observed == "allowed"
    assert result.returncode == (1 if blocked else 0), proposal["outcome"]
    assert meta["audit"]["passed"] is not blocked
    assert meta["workspace_manifest"]["login_copy_deleted"] is True
    assert not (Path(meta["workspace_manifest"]["root"]).parent / "forbidden.txt").exists()


RESOURCE_PROGRAM = '''import ctypes, json, os, platform, shutil, signal, sys, threading, time
from pathlib import Path
if "--version" in sys.argv:
 print("resource-guard-fixture-1"); raise SystemExit(0)
mode = json.loads(Path(sys.argv[1]).read_text())["mode"]
pidfile = Path("build/resource-pid.json")
pidfile.write_text(json.dumps({"provider": os.getpid()}))
print(json.dumps({"type":"item.completed", "item":{"type":"command_execution", "command":"local resource fixture probe", "exit_code":0, "aggregated_output":"started:"+mode}}), flush=True)
if mode == "threads":
 # Ticket 74: a tool process (not the provider runtime) over the 16-thread tool cap.
 if os.fork() == 0:
  gate = threading.Event()
  for number in range(17):
   threading.Thread(target=gate.wait, daemon=True).start()
  time.sleep(30); os._exit(0)
elif mode == "runtime_threads":
 # The provider runtime itself over its 64-thread cap: a harness limit, not tool work.
 gate = threading.Event()
 for number in range(64):
  threading.Thread(target=gate.wait, daemon=True).start()
elif mode == "cpu_escape":
 # A tool process widening its affinity beyond the lane (as taskset or numactl would).
 if os.fork() == 0:
  os.sched_setaffinity(0, range(os.cpu_count()))
  time.sleep(30); os._exit(0)
elif mode == "workspace":
 # Two sparse files cross the actual aggregate 5 GiB allowance without
 # allocating 6 GiB physically. Each file stays below RLIMIT_FSIZE.
 for name in ("resource-growth-a.bin", "resource-growth-b.bin"):
  with Path("build", name).open("wb") as handle:
   handle.truncate(3 * 1024**3)
elif mode in {"orphan_threads", "supervisor_signals", "command_timeout"}:
 # A model-selected helper named like Codex's persistent service must retain
 # the tool watchdog: its executable and parent are not the selected CLI.
 if mode == "command_timeout":
  helper = Path("build/codex-code-mode-host")
  shutil.copyfile("/usr/bin/sleep", helper)
  helper.chmod(0o700)
 provider, tracer, provider_session = os.getpid(), os.getppid(), os.getsid(0)
 if mode == "supervisor_signals":
  protection = json.loads((Path.cwd().parent / "guard/provider-process.json").read_text())["supervisor_protection"]
 first = os.fork()
 if first == 0:
  os.setsid()
  if os.fork() != 0: os._exit(0)
  observations = {}
  if mode == "supervisor_signals":
   # Attack immediately after the double fork, before waiting for adoption or
   # the observer's first sample. The inherited filter must protect continuity.
   worker, trace = protection["supervisors"]
   libc = ctypes.CDLL(None, use_errno=True)
   libc.syscall.restype = ctypes.c_long
   calls = ({"kill":62,"tkill":200,"tgkill":234,"queue":129,"thread_queue":297}
    if platform.machine() == "x86_64" else {"kill":129,"tkill":130,"tgkill":131,"queue":138,"thread_queue":240})
   def check(name, action):
    try: action(); observations[name] = "allowed"
    except OSError as error: observations[name] = "blocked:"+str(error.errno)
   def syscall(number, *arguments):
    result = libc.syscall(ctypes.c_long(number), *arguments)
    if result < 0: raise OSError(ctypes.get_errno(), "signal syscall rejected")
   def pidfd_probe(pid):
    descriptor = os.pidfd_open(pid)
    os.close(descriptor)
   check("kill_tracer", lambda:os.kill(tracer, signal.SIGKILL))
   check("kill_worker", lambda:os.kill(worker["pid"], signal.SIGKILL))
   check("pidfd_tracer", lambda:pidfd_probe(tracer))
   check("pidfd_worker", lambda:pidfd_probe(worker["pid"]))
   check("kill_all", lambda:os.kill(-1, 0))
   check("group_tracer", lambda:os.kill(-trace["process_group"], 0))
   check("group_worker", lambda:os.kill(-worker["process_group"], 0))
   check("tkill_tracer", lambda:syscall(calls["tkill"], ctypes.c_int(trace["tids"][0]), ctypes.c_int(0)))
   check("tgkill_tracer", lambda:syscall(calls["tgkill"], ctypes.c_int(tracer), ctypes.c_int(trace["tids"][0]), ctypes.c_int(0)))
   check("queue_tracer", lambda:syscall(calls["queue"], ctypes.c_int(tracer), ctypes.c_int(0), ctypes.c_void_p()))
   check("thread_queue_tracer", lambda:syscall(calls["thread_queue"], ctypes.c_int(tracer), ctypes.c_int(trace["tids"][0]), ctypes.c_int(0), ctypes.c_void_p()))
   check("high_word_tracer", lambda:syscall(calls["kill"], ctypes.c_ulonglong((1<<32)|tracer), ctypes.c_int(signal.SIGKILL)))
   check("own_group", lambda:os.kill(0, 0))
   check("own_tkill", lambda:syscall(calls["tkill"], ctypes.c_int(os.getpid()), ctypes.c_int(0)))
   check("own_tgkill", lambda:syscall(calls["tgkill"], ctypes.c_int(os.getpid()), ctypes.c_int(os.getpid()), ctypes.c_int(0)))
   for action in ("helper_sigterm", "helper_pidfd_signal"):
    helper_pid = os.fork()
    if helper_pid == 0:
     time.sleep(5); os._exit(0)
    if action == "helper_sigterm": os.kill(helper_pid, signal.SIGTERM)
    else:
     descriptor = os.pidfd_open(helper_pid)
     try: signal.pidfd_send_signal(descriptor, signal.SIGTERM)
     finally: os.close(descriptor)
    _, status = os.waitpid(helper_pid, 0)
    observations[action] = "terminated" if os.WIFSIGNALED(status) and os.WTERMSIG(status) == signal.SIGTERM else "unexpected"
  # Double-forking used to escape PPid closure and process-group cleanup.
  # Allocate only after adoption so the observer must find the orphan.
  deadline = time.monotonic() + 5
  while os.getppid() != tracer and time.monotonic() < deadline: time.sleep(.01)
  Path("build/detached-pid.json").write_text(json.dumps({"pid":os.getpid(),
   "parent":os.getppid(), "session":os.getsid(0), "provider_session":provider_session,
   "signal_results":observations}))
  if mode == "command_timeout": os.execv(str(helper.resolve()), [str(helper), "130"])
  gate = threading.Event()
  for number in range(17): threading.Thread(target=gate.wait, daemon=True).start()
  time.sleep(130)
  os._exit(0)
 os.waitpid(first, 0)
print(json.dumps({"type":"item.completed", "item":{"type":"command_execution", "command":"local resource fixture probe", "exit_code":0, "aggregated_output":"allocated:"+mode}}), flush=True)
if mode == "command_timeout": time.sleep(140)
else: time.sleep(10)
Path("build/unexpected-completion.json").write_text("{}")
result={"interpretation":"Resource fixture completed unexpectedly.", "unresolved":[]}
Path(sys.argv[sys.argv.index("--output-last-message")+1]).write_text(json.dumps(result))
print(json.dumps({"type":"turn.completed"}), flush=True)
'''


@pytest.mark.parametrize("mode,reason", [
    ("threads", "provider resource limit exceeded: tool threads="),
    ("runtime_threads", "provider resource limit exceeded by the provider runtime"),
    ("cpu_escape", "may run outside the lane CPUs"),
    ("orphan_threads", "provider resource limit exceeded"),
    ("supervisor_signals", "provider resource limit exceeded"),
    ("workspace", "provider workspace exceeds"),
    ("command_timeout", "provider tool command exceeds the 120 s wall-time limit"),
])
def test_public_submit_enforces_actual_resource_overruns(proposal_setup, tmp_path, mode, reason):
    if mode == "cpu_escape" and set(os.sched_getaffinity(0)) == set(range(os.cpu_count())):
        pytest.skip("run inside socket_lane.sh: the observer's affinity is every CPU")
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
        assert meta["guard_policy"]["persistent_services"] == []
        assert (Path(meta["workspace_manifest"]["root"]) / "build/codex-code-mode-host").is_file()
    else:
        assert meta["host_wall_s"] < 10, "fixture reached its own completion instead of being stopped by the guard"
    violations = meta["audit"]["violations"]
    code = "guard_violation" if mode == "cpu_escape" else "resource_limit"
    assert any(v["code"] == code and reason in v["reason"] for v in violations)
    assert not any(v["code"] == "outbound_connection" for v in violations)
    assert not meta["guard_result"]["passed"]
    assert any(reason in r for r in meta["guard_result"]["reasons"])
    workspace = Path(meta["workspace_manifest"]["root"])
    assert not (workspace / "build/unexpected-completion.json").exists()
    assert meta["workspace_manifest"]["login_copy_deleted"]
    assert not (Path(meta["workspace_manifest"]["home"]) / "auth.json").exists()
    policy = meta["guard_policy"]
    assert policy["limits"]["threads"] == 16 and policy["limits"]["memory_bytes"] == 32*1024**3
    assert policy["limits"]["runtime_threads"] == 64
    assert policy["limits"]["command_seconds"] == 120
    assert policy["limits"]["workspace_bytes"] == 5*1024**3 and "test_override" not in policy
    assert policy["process_ownership"]["subreaper"] is True
    cleanup = meta["guard_result"]["process_cleanup"]
    assert cleanup["passed"] and cleanup["survivors"] == []
    assert meta["guard_result"]["original_provider"]["pid"] == json.loads(
        (workspace / "build/resource-pid.json").read_text())["provider"]
    assert any(row["pid"] == cleanup["tracer_pid"] for row in cleanup["processes_observed"])
    protection = meta["guard_result"]["supervisor_protection"]
    assert protection["enforced"] and protection["provider_session"] == meta["guard_result"]["original_provider"]["pid"]
    assert all(row["session"] != protection["provider_session"] for row in protection["supervisors"])
    if mode in {"orphan_threads", "supervisor_signals", "command_timeout"}:
        detached = json.loads((workspace / "build/detached-pid.json").read_text())
        assert detached["parent"] == cleanup["tracer_pid"]
        assert detached["session"] != detached["provider_session"]
        identity = next(row for row in cleanup["processes_observed"] if row["pid"] == detached["pid"])
        # PID reuse is harmless; a remaining process with this same kernel
        # identity (including an unreaped zombie) means owned cleanup failed.
        try:
            fields = Path(f'/proc/{detached["pid"]}/stat').read_text().rsplit(")", 1)[1].split()
        except FileNotFoundError:
            pass
        else:
            assert int(fields[19]) != identity["start_time_ticks"], "detached owned helper survived cleanup"
        if mode == "supervisor_signals":
            observed = detached["signal_results"]
            blocked = {"kill_tracer", "kill_worker", "pidfd_tracer", "pidfd_worker", "kill_all",
                       "group_tracer", "group_worker", "tkill_tracer", "tgkill_tracer", "queue_tracer",
                       "thread_queue_tracer", "high_word_tracer"}
            assert {key: observed[key] for key in blocked} == dict.fromkeys(blocked, "blocked:1")
            assert all(observed[key] == "allowed" for key in ("own_group", "own_tkill", "own_tgkill"))
            assert observed["helper_sigterm"] == observed["helper_pidfd_signal"] == "terminated"
        if mode in {"orphan_threads", "supervisor_signals"}:
            details = json.loads((Path(meta["audit"]["raw_log"]["path"]).parent / "resource-overrun.json").read_text())
            assert details["format"] == "swdb.guard-overrun.v2" and details["scope"] == "tools"
            orphan = next(row for row in details["processes"] if row["pid"] == detached["pid"])
            assert orphan["parent"] == cleanup["tracer_pid"] and orphan["threads"] > 1
            assert orphan["scope"] == "tool"          # adopted by the tracer, still the model's work
            # The observer may catch the allocation before all 17 requested
            # threads start. Admission depends on the actual tool-thread count.
            assert details["tools"]["threads"] > policy["limits"]["threads"]
            assert any(row["pid"] == cleanup["tracer_pid"] and row["scope"] == "tracer" for row in details["processes"])
    if mode in {"threads", "orphan_threads", "supervisor_signals"}:
        measured = next(r for r in meta["guard_result"]["reasons"] if reason in r)
        assert int(re.search(r"tool threads=(\d+)", measured)[1]) > 16
        assert provider_guard.harness_limit(Path(meta["audit"]["raw_log"]["path"]).parent) is None
    elif mode == "runtime_threads":
        measured = next(r for r in meta["guard_result"]["reasons"] if reason in r)
        assert int(re.search(r"runtime threads=(\d+)", measured)[1]) > 64
        assert provider_guard.harness_limit(Path(meta["audit"]["raw_log"]["path"]).parent) == measured
    elif mode == "workspace":
        growth = [workspace / "build" / name for name in ("resource-growth-a.bin", "resource-growth-b.bin")]
        assert sum(p.stat().st_size for p in growth) == 6*1024**3
        assert all(p.stat().st_size < policy["limits"]["workspace_bytes"] for p in growth)
        assert sum(p.stat().st_blocks*512 for p in growth) < 1024**2
        assert sum(p.stat().st_size for p in workspace.rglob("*") if p.is_file()) > policy["limits"]["workspace_bytes"]
    later = records.swdb("get", proposal["id"], "--format", "json")
    assert later.returncode == 0
    assert json.loads(later.stdout)["attempts"][0]["provider"]["audit"] == meta["audit"]


UNTRACED_PROGRAM = '''import ctypes, errno, json, platform, socket, sys
from pathlib import Path
if "--version" in sys.argv:
 print("untraced-network-fixture-1"); raise SystemExit(0)
probe = json.loads(Path(sys.argv[1]).read_text())["probe"]
observed = "allowed"
try:
 if probe == "io_uring":
  libc = ctypes.CDLL(None, use_errno=True)
  params = ctypes.create_string_buffer(120)
  if libc.syscall(425, 4, params) < 0:
   raise OSError(ctypes.get_errno(), "io_uring_setup")
 else:
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.sendto(b"x", 0x20000000, ("1.1.1.1", 443))
except OSError as exc:
 observed = "blocked:" + str(exc.errno)
print(json.dumps({"type":"item.completed","item":{"type":"command_execution","command":"untraced network probe","exit_code":0,"aggregated_output":observed}}), flush=True)
path = Path("src/bfs.cc")
path.write_text(path.read_text().replace("int alpha = 15", "int alpha = 14"))
Path(sys.argv[sys.argv.index("--output-last-message")+1]).write_text(json.dumps({"interpretation":"Probe.","unresolved":[]}))
print(json.dumps({"type":"turn.completed"}), flush=True)
'''


@pytest.mark.parametrize("probe", ["io_uring", "tcp_fastopen"])
def test_codex_guard_refuses_untraced_network_syscalls(proposal_setup, tmp_path, probe):
    """Calls the connect() trace cannot see are refused for Codex-shaped sessions."""
    records, runs, _, request = proposal_setup
    program, plan = tmp_path / "untraced.py", tmp_path / "untraced-plan.json"
    program.write_text(UNTRACED_PROGRAM)
    plan.write_text(json.dumps({"probe": probe}))
    config = tmp_path / "untraced.yaml"
    config.write_text(yaml.safe_dump({"kind": "external_fixture", "emulates": "codex", "workspace": True,
        "command": [sys.executable, str(program), str(plan)], "timeout_s": 30, "total_seconds": 60}))
    result = records.swdb("submit", request(payload={"kind": "natural_language", "content": "Set alpha to 14."}),
                          "--provider-config", config, "--runs-dir", runs, "--format", "json")
    proposal = json.loads(result.stdout)
    meta = proposal["attempts"][0]["provider"]
    assert meta["guard_policy"]["untraced_network_filter"]
    log = Path(meta["audit"]["raw_log"]["path"])
    event = next(json.loads(line) for line in log.read_text().splitlines() if '"command_execution"' in line)
    assert event["item"]["aggregated_output"] == "blocked:1", event
