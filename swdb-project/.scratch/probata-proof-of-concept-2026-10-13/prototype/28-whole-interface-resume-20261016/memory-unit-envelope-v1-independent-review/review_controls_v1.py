"""Independent inert memory envelope review. No remote or scientific execution."""
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "memory-unit-envelope-v1"
def audit(event, arguments):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "socket.")) or event in {"os.system", "ctypes.dlopen"}:
        raise AssertionError("Independent source-only boundary: " + event)
sys.addaudithook(audit)
packet_raw = (SOURCE / "source-packet-v1.json").read_bytes()
packet = json.loads(packet_raw)
for row in packet["files"] + packet["basis"]:
    raw = Path(row["path"]).read_bytes()
    assert len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"]
inverse = json.loads((SOURCE / "exact-envelope-inverse-v1.json").read_bytes())
text = (SOURCE / "linux_memory_observation_envelope_v1.py").read_text()
for change in reversed(inverse["replacements"]):
    assert text.count(change["new"]) == change["count"]
    text = text.replace(change["new"], change["old"])
assert text.encode() == Path(inverse["basis"]["path"]).read_bytes()
policy = json.loads((SOURCE / "envelope-policy-v1.json").read_bytes())
command = json.loads((SOURCE / "command-v1.json").read_bytes())
assert policy["node"] is None and policy["guard_files"] is None and not command["root_metadata_complete"]
assert len(command["stage_sources"]) == 35
for name, row in command["stage_sources"].items():
    raw = Path(row["path"]).read_bytes()
    assert len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"]
    assert policy["controls"][name]["sha256"] == row["sha256"] and policy["controls"][name]["bytes"] == row["bytes"]
assert sum(row["bytes"] for row in command["stage_sources"].values()) + (SOURCE / "envelope-policy-v1.json").stat().st_size == 718864
suite = unittest.TestSuite()
for filename in ("test_envelope_v1.py", "test_root_environment_v1.py", "test_memory_bindings_v1.py"):
    namespace = runpy.run_path(str(SOURCE / filename), run_name="independent_" + filename[:-3])
    classes = [value for value in namespace.values() if isinstance(value, type) and issubclass(value, unittest.TestCase) and value is not unittest.TestCase]
    assert len(classes) == 1
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(classes[0]))
log = io.StringIO()
result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
assert result.testsRun == 22 and not result.failures and not result.errors and not result.skipped
log.write("\nComplete outer inverse, all fixed staged bytes and explicit inert node/guard fields match.\n")
log.write("No ABI/full-TU interpretation, original source execution, remote host or scientific tool ran.\n")
(HERE / "independent-controls-v1.log").write_text(log.getvalue())
print(json.dumps(dict(packet_sha256=hashlib.sha256(packet_raw).hexdigest(), packet_pin_occurrences=len(packet["files"])+len(packet["basis"]),
                     staged_controls=35, staged_bytes_including_policy=718864, tests=result.testsRun,
                     failures=0, errors=0, skips=0, scientific_acceptance=False), sort_keys=True))
