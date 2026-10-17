"""Independent semantic-reader review over authorized small metadata inputs."""
import ast
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "abi-enum-repair-v1"
def audit(event, arguments):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "socket.")) or event in {"os.system", "ctypes.dlopen"}:
        raise AssertionError("Independent offline-only boundary: " + event)
sys.addaudithook(audit)
packet_raw = (SOURCE / "source-packet-v1.json").read_bytes()
packet = json.loads(packet_raw)
for selected in packet["files"]:
    row = selected["pin"]
    raw = Path(row["path"]).read_bytes()
    assert len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"]
original = (SOURCE / "base-source.py").read_bytes()
current = (SOURCE / "proposed/compiler_unit_adapter_v4.py").read_bytes()
def functions(raw):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(raw).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
old, new = functions(original), functions(current)
assert {name for name in old if old[name] != new[name]} == {"observed_abi"}
assert hashlib.sha256(original).hexdigest() == "775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c"
namespace = runpy.run_path(str(SOURCE / "test_enum_repair_v1.py"), run_name="independent_semantic_ABI_controls")
log = io.StringIO()
result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(namespace["Controls"]))
assert result.testsRun == 11 and not result.failures and not result.errors and not result.skipped
log.write("\nBoth complete actual29-root/23-enum offline metadata pipelines pass; 506 shape mutations refuse.\n")
log.write("No remote original changed, no full TU or compiler/native/prover executed, and original reader refusals remain.\n")
(HERE / "independent-controls-v1.log").write_text(log.getvalue())
print(json.dumps(dict(packet_sha256=hashlib.sha256(packet_raw).hexdigest(), pin_count=len(packet["files"]),
                     tests=result.testsRun, failures=0, errors=0, skips=0, actual_small_metadata_families=2,
                     scientific_or_source_admission=False), sort_keys=True))
