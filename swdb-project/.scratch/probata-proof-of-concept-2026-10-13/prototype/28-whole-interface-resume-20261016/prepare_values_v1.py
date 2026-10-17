"""2026-10-16 ET. Freeze generated value source; no compiler/runtime execution."""
import ast
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def prepare():
    packet = json.loads((HERE / "source-packet-author-receipt-v1.json").read_bytes())
    original = json.loads((HERE / "source-preparation.json").read_bytes())
    for expected in packet["pins"] + original["source_inputs"]:
        if pin(expected["path"]) != expected: raise ValueError("original source packet changed")
    range_dir = HERE / "source/gem5-e4fc4af"
    range_pins = {"RangeFuser.cc": "27a3713469a44031829d638b3e865f714cd63a0423c493d78cbcc07dd9b7d42e",
                  "RangeFuser.hh": "1794c7469f5b88e0ed36adb129f632d4370cf8adf983892b100b65a79cb88218"}
    for name, expected in range_pins.items():
        if pin(range_dir / name)["sha256"] != expected: raise ValueError("primary range source changed")
    provenance = json.loads((range_dir / "source-provenance.json").read_bytes())
    if provenance["commit"] != "e4fc4afdf894f295442cef3604667a469fab8e62": raise ValueError("range source commit differs")
    paths = {record["path"] for record in packet["pins"] + original["source_inputs"]}
    paths.add(str(HERE / "source-packet-author-receipt-v1.json"))
    paths.update(str(HERE / name) for name in ("value_builders.py", "prepare_values_v1.py", "test_value_builders_v1.py",
        "whole_values_native_v1.c", "README-values-v1.md", "pure-value-controls-v1-initial.log", "pure-value-controls-v1-final.log"))
    paths.update(str(range_dir / name) for name in (*range_pins, "source-provenance.json"))
    before = [pin(path) for path in sorted(paths)]
    source = (HERE / "value_builders.py").read_bytes()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name != "hashlib" for alias in node.names):
            raise ValueError("unreviewed builder import")
        if isinstance(node, ast.ImportFrom): raise ValueError("unreviewed builder import")
    namespace = {"__name__": "source_value_preparation", "__file__": str(HERE / "value_builders.py")}
    exec(compile(tree, str(HERE / "value_builders.py"), "exec"), namespace)
    base = (HERE / "whole_backend.h").read_text()
    declarations = json.loads((HERE / "declarations.json").read_bytes())
    outputs = {"whole_value_backend_v1.h": namespace["extend_backend"](base).encode(),
               "whole_value_builders_v1.h": namespace["render_builders"]().encode(),
               "whole_closed_routes_v1.h": namespace["render_closed_routes"](declarations).encode()}
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "extend_backend")
    changes = ast.literal_eval(next(node.value for node in fn.body if isinstance(node, ast.Assign)
                               and any(isinstance(t, ast.Name) and t.id == "changes" for t in node.targets)))
    inverse = outputs["whole_value_backend_v1.h"].decode()
    for old, new in reversed(changes):
        if inverse.count(new) != 1: raise ValueError("extension inverse anchor differs")
        inverse = inverse.replace(new, old, 1)
    if inverse != base: raise ValueError("extension has unaccounted edits")
    delta = {"date": "2026-10-16", "original_sha256": namespace["BASE_SHA256"],
             "extended_sha256": hashlib.sha256(outputs["whole_value_backend_v1.h"]).hexdigest(),
             "inverse_exact": True, "edits": [{"old": old, "new": new} for old, new in changes]}
    outputs["backend-extension-v1.json"] = (json.dumps(delta, indent=2, sort_keys=True) + "\n").encode()
    contracts = []
    for row in declarations:
        if "packet" not in row: continue
        opcode = row["packet"]["opcode"]
        builder = "dxw_alu" if opcode >= 8 else "dxw_range" if opcode == 7 else "dxw_stream" if opcode <= 1 else "dxw_indirect"
        contracts.append({"name": row["name"], "source_header": row["file"], "source_line": row["line"],
                          "source_body_sha256": row["body_sha256"], "source_packet": row["packet"],
                          "closed_route": "dxw_call_" + row["name"], "builder": builder,
                          "requested_types": list(range(6)), "effective_dtype": 1 if opcode == 7 else "actual source type",
                          "state": "SOURCE_IMPLEMENTED_UNCOMPILED_UNEXECUTED",
                          "owned_mmio_normal_return_premise": True, "public_support": False})
    outputs["value-contracts-v1.json"] = (json.dumps({"date": "2026-10-16", "contracts": contracts,
        "domain_document": str(HERE / "README-values-v1.md"), "native_harness": "INERT_86_CONTROLS_NOT_EXECUTED"},
        indent=2, sort_keys=True) + "\n").encode()
    if before != [pin(path) for path in sorted(paths)]: raise ValueError("input changed during value preparation")
    for name, data in outputs.items(): (HERE / name).write_bytes(data)
    result = {"date": "2026-10-16", "status": "AUTHOR_VALUE_SOURCE_READY_FOR_INDEPENDENT_REVIEW",
              "source_inputs": before, "outputs": [pin(HERE / name) for name in sorted(outputs)],
              "counts": {"closed_packet_families": 11, "requested_dtype_cases": 66, "pure_source_algebra_tests": 5,
                         "range_source_vs_formula_cases": 54, "native_controls_authored_not_executed": 86},
              "original_source_packet_unchanged": True, "compiler_native_verifier_ssh_execution": False,
              "public_admission": False,
              "remaining": "Independent source review, root-admitted native C11/C++17 sanitizer controls, actual full-TU/ABI/scalar/pointer routing and public synthetic verdicts under owned MMIO TCB; no hardware/body theorem requirement."}
    (HERE / "value-source-preparation-v1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    def no_child(event, args):
        if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork")) or event in {"os.system", "ctypes.dlopen"}:
            raise RuntimeError("source-only preparation: " + event)
    sys.addaudithook(no_child)
    prepare()
