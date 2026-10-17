"""2026-10-16 ET. Inert demonstration/source packet generation, stdlib only."""
import hashlib
import json
from pathlib import Path
import sys


def no_child(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "socket.")) or event in {"os.system", "ctypes.dlopen"}:
        raise RuntimeError("source-only model assembly refuses " + event)


sys.addaudithook(no_child)
HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
PROJECT = WHOLE.parents[3]


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    path = HERE / "whole_model_v1.py"
    module = {"__file__": str(path), "__name__": "inert_model_assembly"}
    exec(compile(path.read_bytes(), str(path), "exec"), module)
    synthetic = WHOLE / "source-dispatch-synthetic-inputs-v2.json"
    inputs = json.loads(synthetic.read_bytes())
    result = module["assemble"](WHOLE, PROJECT, abi=inputs["abi"], objects=inputs["objects"])
    body = HERE / "model-demonstration-synthetic-v1.h"
    body.write_text(result["c_text"])
    entry = HERE / "entry-demonstration-synthetic-v1.json"
    entry.write_text(json.dumps(result["entry"], sort_keys=True, indent=2) + "\n")
    owned = [HERE / name for name in ("whole_model_v1.py", "test_whole_model_v1.py", "prepare_model_entry_v1.py", "README.md")]
    owned += [synthetic, WHOLE / "new-0.2-contract-design-v1.json"]
    packet = {"date": "2026-10-16 ET", "status": "INERT CHECKED-BODY MODEL PREPARATION",
        "inputs": [pin(item) for item in owned] + result["entry"]["model"]["source_inputs"],
        "outputs": [pin(body), pin(entry)],
        "counts": {"call_contracts": 26, "source_declarations": 27, "typed_arity_instances": 132,
                   "direct_packet_families": 11, "pure_controls": 6},
        "synthetic_abi_address_demonstration_only": True,
        "actual_compiler_native_verifier_execution": False,
        "source_admission": False, "public_admission": False, "current_0_2": False, "full_ticket28": False,
        "pending_public_consumers": ["Actual compiler/source/ABI/CPU certificate", "Receiver-state and independent harness draws",
            "New isolated checked-C contract validator and model registration", "Source lowerer and method/public record routing",
            "Actual compiler/native/public positive and negative checks with complete property and replay reconciliation"],
        "old_0_1_bytes_changed": False}
    output = HERE / "model-entry-source-packet-v1.json"
    output.write_text(json.dumps(packet, sort_keys=True, indent=2) + "\n")
    print(json.dumps(pin(output), sort_keys=True))


if __name__ == "__main__":
    main()
