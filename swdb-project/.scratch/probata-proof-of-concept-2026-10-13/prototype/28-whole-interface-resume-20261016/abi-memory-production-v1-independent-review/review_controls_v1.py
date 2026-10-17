"""Independent scratch integration review; no installed project imports or tools."""
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "abi-memory-production-v1"
def audit(event, arguments):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "socket.")) or event in {"os.system", "ctypes.dlopen"}:
        raise AssertionError("Independent source-only boundary: " + event)
sys.addaudithook(audit)
packet_raw = (SOURCE / "source-packet-v1.json").read_bytes()
packet = json.loads(packet_raw)
for row in packet["files"] + packet["basis"]:
    raw = Path(row["path"]).read_bytes()
    assert len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"]
manifest = json.loads((SOURCE / "production-paths-and-bases-v1.json").read_bytes())
assert len(manifest["paths"]) == 10 and sum(row["base"] is not None for row in manifest["paths"]) == 3
for row in manifest["applied_V5_observed_rows"]:
    raw = Path(row["path"]).read_bytes()
    assert len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"]
inverse = json.loads((SOURCE / "exact-source-inverses-v1.json").read_bytes())
for relative, replacements in inverse["files"].items():
    text = (SOURCE / "proposed" / relative).read_text()
    for change in reversed(replacements):
        assert text.count(change["new"]) == change.get("count", 1)
        text = text.replace(change["new"], change["old"])
    assert text == (SOURCE / "base-source" / relative).read_text()
namespace = runpy.run_path(str(SOURCE / "test_integration_v1.py"), run_name="independent_ABI_memory_integration_controls")
log = io.StringIO()
result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(namespace["IntegrationControls"]))
assert result.testsRun == 8 and not result.failures and not result.errors and not result.skipped
log.write("\nAll 29 packet pins, 50 applied V5 bytes and three complete existing-file inverses match.\n")
log.write("No retained ABI or full TU, installed project module, compiler, native program or prover executed.\n")
(HERE / "independent-controls-v1.log").write_text(log.getvalue())
print(json.dumps(dict(packet_sha256=hashlib.sha256(packet_raw).hexdigest(), packet_pin_occurrences=len(packet["files"])+len(packet["basis"]),
                     applied_V5_files=len(manifest["applied_V5_observed_rows"]), proposed_paths=len(manifest["paths"]),
                     tests=result.testsRun, failures=0, errors=0, skips=0, scientific_acceptance=False), sort_keys=True))
