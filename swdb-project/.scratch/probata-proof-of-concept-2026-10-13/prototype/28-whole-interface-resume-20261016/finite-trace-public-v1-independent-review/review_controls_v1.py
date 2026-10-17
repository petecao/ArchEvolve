"""Independent source/pin controls. No project, compiler, native, or network execution."""
import ast
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "finite-trace-public-v1"

def audit(event, arguments):
    if event in {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "ctypes.dlopen"} or event.startswith("socket."):
        raise AssertionError("Independent source-only boundary: " + event)

sys.addaudithook(audit)
packet_raw = (SOURCE / "source-packet-v1.json").read_bytes()
packet = json.loads(packet_raw)
rows = packet["owned_files"] + packet["basis_files"]
for row in rows:
    raw = Path(row["path"]).read_bytes()
    assert len(raw) == row["bytes"]
    assert hashlib.sha256(raw).hexdigest() == row["sha256"]

namespace = runpy.run_path(str(SOURCE / "test_finite_public.py"), run_name="independent_source_controls")
log = io.StringIO()
result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(namespace["Controls"]))
assert result.testsRun == 13 and not result.failures and not result.errors and not result.skipped

adapter = SOURCE / "proposed/swdb/dx100_finite_trace_adapter.py"
core = SOURCE / "proposed/swdb/dx100_finite_trace.py"
adapter_text = adapter.read_text()
core_text = core.read_text()
ast.parse(adapter_text)
ast.parse(core_text)
# These retained exact seams support the findings. They are not scientific executions.
assert "if outcome['verdict']=='proven':return finish(adapter,'proven',context,why=outcome['why'])" in adapter_text
assert "replayed=row['failed']==[failure['property']]" in adapter_text
assert "source=contract['proof_unit']['source'];need(source['sha256']==trace_policy['source_plan']['sha256'] and Path(library.resolve(source)).resolve()==Path(trace_policy['source_plan']['path'])" in core_text
log.write("\nAll 80 packet pins match; 13 controls pass without child/native/network execution.\n")
log.write("Three source findings remain; this is not public or scientific acceptance.\n")
(HERE / "independent-pure-controls-v1.log").write_text(log.getvalue())
print(json.dumps(dict(packet_sha256=hashlib.sha256(packet_raw).hexdigest(), pin_count=len(rows), tests=result.testsRun,
                     failures=len(result.failures), errors=len(result.errors), skips=len(result.skipped),
                     source_only=True, scientific_acceptance=False), sort_keys=True))
