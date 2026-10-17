"""Independent source/envelope controls. Does not execute an observer or compiler."""
import ast
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "normalized-unit-envelope-v4"
def audit(event, arguments):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "socket.")) or event in {"os.system", "ctypes.dlopen"}:
        raise AssertionError("Independent source-only boundary: " + event)
sys.addaudithook(audit)
packet_raw = (SOURCE / "source-packet-v4.json").read_bytes()
packet = json.loads(packet_raw)
for row in packet["files"] + packet["basis"]:
    raw = Path(row["path"]).read_bytes()
    assert len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"]
inverse = json.loads((SOURCE / "exact-inverses-v4.json").read_bytes())
for relative, row in inverse["files"].items():
    text = (SOURCE / relative).read_text()
    for change in reversed(row["replacements"]):
        assert text.count(change["new"]) == change["count"]
        text = text.replace(change["new"], change["old"])
    assert text.encode() == Path(row["basis"]["path"]).read_bytes()
command = json.loads((SOURCE / "command-v4.json").read_bytes())
policy = json.loads((SOURCE / "envelope-policy-v4.json").read_bytes())
for name, row in command["stage_sources"].items():
    raw = Path(row["path"]).read_bytes()
    assert len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"]
    assert name in policy["controls"]
    selected = policy["controls"][name]
    assert selected["bytes"] == row["bytes"] and selected["sha256"] == row["sha256"]
assert len(command["stage_sources"]) == 29
assert sum(row["bytes"] for row in command["stage_sources"].values()) + (SOURCE / "envelope-policy-v4.json").stat().st_size == 453830
manifest = json.loads((SOURCE / "observer/fixed-modules-v2.json").read_bytes())
for row in manifest["modules"]:
    raw = (SOURCE / "observer/modules" / row["file"]).read_bytes()
    assert len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"]
assert len(manifest["modules"]) == 13
suite = unittest.TestSuite()
for filename, classname in [("test_envelope_v4.py", "EnvelopeControls"), ("test_root_environment_v4.py", "Controls"), ("test_abi_observer_v4.py", "ABIObserverControls")]:
    namespace = runpy.run_path(str(SOURCE / filename), run_name="independent_" + filename[:-3])
    # Class names are discovered from the frozen module rather than importing any project package.
    classes = [value for value in namespace.values() if isinstance(value, type) and issubclass(value, unittest.TestCase) and value is not unittest.TestCase]
    assert len(classes) == 1
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(classes[0]))
log = io.StringIO()
result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
assert result.testsRun == 23 and not result.failures and not result.errors and not result.skipped
log.write("\nAll packet, fixed module, staged input pins and four complete source inverses match.\n")
log.write("The actual observer, original ABI eligibility and public source admission remain unexecuted.\n")
(HERE / "independent-controls-v4.log").write_text(log.getvalue())
print(json.dumps(dict(packet_sha256=hashlib.sha256(packet_raw).hexdigest(), packet_pin_occurrences=len(packet["files"])+len(packet["basis"]),
                     staged_controls=len(command["stage_sources"]), fixed_modules=len(manifest["modules"]),
                     tests=result.testsRun, failures=0, errors=0, skips=0, scientific_acceptance=False), sort_keys=True))
