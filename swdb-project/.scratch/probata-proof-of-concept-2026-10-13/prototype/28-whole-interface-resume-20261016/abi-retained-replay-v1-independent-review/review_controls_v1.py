"""Independent ABI replay source controls; never executes the remote reader."""
import ast
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "abi-retained-replay-v1"
def audit(event, arguments):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "socket.")) or event in {"os.system", "ctypes.dlopen"}:
        raise AssertionError("Independent source-only boundary: " + event)
sys.addaudithook(audit)
packet_raw = (SOURCE / "source-packet-v1.json").read_bytes()
packet = json.loads(packet_raw)
rows = packet["owned"] + packet["basis"]
for row in rows:
    raw = Path(row["path"]).read_bytes()
    assert len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"]
staging = json.loads((SOURCE / "staging-manifest-v1.json").read_bytes())
assert len(staging["files"]) == 8
for row in staging["files"]:
    raw = Path(row["source"]["path"]).read_bytes()
    assert len(raw) == row["source"]["bytes"] == row["destination"]["bytes"]
    assert hashlib.sha256(raw).hexdigest() == row["source"]["sha256"] == row["destination"]["sha256"]
assert sum(row["source"]["bytes"] for row in staging["files"]) <= 1024**2
command = json.loads((SOURCE / "command-v1.json").read_bytes())
entry = (SOURCE / "replay_entry_v1.py").read_bytes()
assert len(entry) == command["stdin"]["bytes"] and hashlib.sha256(entry).hexdigest() == command["stdin"]["sha256"]
assert command["argv"] == ["ssh", "mbit10", command["remote_shell_command"]]
inverse = json.loads((SOURCE / "scanner-inverse-v1.json").read_bytes())
base = Path(inverse["basis"]["path"]).read_text()
current = entry.decode()
def functions(text):
    return {n.name: ast.get_source_segment(text, n) for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)}
a, b = functions(base), functions(current)
assert a["scan"] == b["scan"] and a["pam_identity"] == b["pam_identity"]
assert b["transport_identity"].replace("'185s'", "'35s'") == a["transport_identity"]
main = b["main"]
assert main.count("subprocess.check_output(") == 2
assert main.index("dirty=subprocess.check_output(") < main.index("sys.addaudithook(readonly)")
assert "subprocess." not in main[main.index("sys.addaudithook(readonly)"):]
assert "deadline();sys.stdout.write(encoded.decode());sys.stdout.flush();deadline()" in main
namespace = runpy.run_path(str(SOURCE / "test_replay_v1.py"), run_name="independent_ABI_source_controls")
log = io.StringIO()
result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(namespace["Controls"]))
assert result.testsRun == 8 and not result.failures and not result.errors and not result.skipped
log.write("\nAll 31 source/basis pins and eight staged payloads match; scanner inverse is exact.\n")
log.write("No original ABI payload, remote reader, compiler, native program or project module was executed.\n")
(HERE / "independent-controls-v1.log").write_text(log.getvalue())
print(json.dumps(dict(packet_sha256=hashlib.sha256(packet_raw).hexdigest(), pin_count=len(rows),
                     staged_files=len(staging["files"]), staged_bytes=sum(row["source"]["bytes"] for row in staging["files"]),
                     tests=result.testsRun, failures=0, errors=0, skips=0, scientific_acceptance=False), sort_keys=True))
