"""2026-10-16 ET. Root-authorized passive preflight, never record audit.

Exact staged source/runtime hashes plus a finite process/lease observation.
No project import, child, scientific process, socket or filesystem mutation.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types


CONTEXT = Path("/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-cold-04af74c1-v8")
RAW = "/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-pair-04af74c1-v5"
PROJECT = "/data1/yanruj/probata-resume-20261016-04af74c1/swdb-project"
POLICY_SHA = "c4f0bd5ea71b59fe8672c378ac04f2de58c07434b237c4158d3a7750a831762a"
READER_SHA = "c34a2541db95fc00a9d396019bedcaaf2facb403d7aafcd83a4f462ab62f1276"


def deny(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "socket.", "ctypes.dlopen")) or event in {
            "os.system", "os.remove", "os.rename", "os.rmdir", "os.mkdir", "os.link", "os.symlink", "os.truncate", "os.chmod", "os.chown", "os.utime"}:
        raise RuntimeError("passive settlement preflight refuses " + event)
    if event == "open":
        _path, mode, flags = args
        if mode is not None and any(c in mode for c in "wax+") or flags & (1 | 2 | 64 | 512 | 1024):
            raise RuntimeError("passive settlement preflight refuses writes")


sys.addaudithook(deny)
control = CONTEXT / "control"
reader_path = control / "initialized_cold_audit_v8.py"
policy_path = control / "initialized-cold-policy-04af74c1-v8.json"
assert hashlib.sha256(reader_path.read_bytes()).hexdigest() == READER_SHA
assert hashlib.sha256(policy_path.read_bytes()).hexdigest() == POLICY_SHA
reader = types.ModuleType("passive_initialized_preflight_only")
reader.__file__ = str(reader_path)
exec(compile(reader_path.read_bytes(), str(reader_path), "exec"), reader.__dict__)
physical = reader.Physical()
policy = reader.strict_json(policy_path.read_bytes())
modules = reader.load_reviewed_modules(policy, physical)
expected = reader.strict_json(physical.read(policy["source_policy"]))
helpers = reader.pure_runtime_helpers(physical.read(policy["original_entry"]).decode(), physical)
runtime = reader.runtime_closure(expected, modules["closed_python_surface.py"], helpers, physical)
closed = modules["closed_python_surface.py"]
python = closed.verify_python_metadata(expected["python_surface_binding"])
staged = []
for path in sorted(control.iterdir()):
    assert stat.S_ISREG(path.lstat().st_mode) and path.resolve() == path
    staged.append({"path": str(path), "bytes": path.stat().st_size, "sha256": physical.pin(path)})
assert len(staged) == 10 and sum(row["bytes"] for row in staged) == 233351
assert not os.path.lexists(CONTEXT / "reader-source-cache")
leases = {}
for name in ("mbit10-evaluation-node0", "mbit10-evaluation"):
    path = Path("/data1/yanruj/lact-host-lease") / (name + ".meta.json")
    raw = path.read_bytes()
    leases[name] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "metadata": reader.strict_json(raw)}
processes, failures = [], []
pids = [p for p in Path("/proc").iterdir() if p.name.isdigit()]
assert len(pids) < 50000
tokens = [RAW.encode(), str(CONTEXT).encode(), PROJECT.encode()]
for path in pids:
    try:
        command = (path / "cmdline").read_bytes()
    except OSError as error:
        failures.append({"pid": int(path.name), "type": type(error).__name__})
        continue
    if any(token in command for token in tokens):
        processes.append({"pid": int(path.name), "argv": [part.decode("utf-8", "replace") for part in command.split(b"\0") if part]})
physical.unchanged()
print(json.dumps({"date": "2026-10-16 ET", "observed_utc": datetime.now(timezone.utc).isoformat(),
    "classification": "PASSIVE_PREFLIGHT_AND_FINITE_SETTLEMENT_OBSERVATION", "original_raw": RAW,
    "source_commit": expected["source_commit"], "reader_sha256": READER_SHA, "policy_sha256": POLICY_SHA,
    "staged_files": staged, "runtime": runtime, "python": python, "physical_checks": physical.checks,
    "target_and_legacy_leases": leases, "scanned_processes": len(pids), "selected_live_processes": processes,
    "proc_read_failures": failures, "reader_audit_executed": False, "scientific_reexecution": False,
    "continuing_process_absence_claim": False, "separate_final_null_watchdog_inferred": False}, sort_keys=True, indent=2, allow_nan=False))
