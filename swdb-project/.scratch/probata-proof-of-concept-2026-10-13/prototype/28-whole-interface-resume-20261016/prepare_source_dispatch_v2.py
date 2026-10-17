"""2026-10-16 ET. Pure source-dispatch artifact assembly, no compiler imports."""
import ast
import hashlib
import json
from pathlib import Path
import sys


def no_child(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork")) or event in {"os.system", "ctypes.dlopen"}:
        raise RuntimeError("source dispatch preparation forbids " + event)


sys.addaudithook(no_child)
HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent.parent / "evidence/resume-20261016-lane-coordination"


def pin(path):
    path = Path(path).resolve(strict=True)
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def own(name):
    path = HERE / name
    ns = {"__name__": "source_preparation_only", "__file__": str(path)}
    tree = ast.parse(path.read_bytes())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name not in {"hashlib", "json", "re"} for alias in node.names):
            raise ValueError("unreviewed source module import")
        if isinstance(node, ast.ImportFrom) and node.module != "pathlib": raise ValueError("unreviewed source import")
    exec(compile(tree, str(path), "exec"), ns)
    return ns


def prepare():
    values_path = HERE / "value-source-preparation-v1.json"
    values = json.loads(values_path.read_bytes())
    for row in values["source_inputs"] + values["outputs"]:
        if pin(row["path"]) != row: raise ValueError("frozen value packet changed")
    source, api = own("source_dispatch_v2.py"), own("whole_interface_v3.py")
    declarations = api["inventory"](HERE.parents[3])
    # Illustrative x86_64 type spellings only; no actual compiler ABI observed.
    abi = {"byte_order": "little", "int_bits": 32, "pointer_bits": 64,
        "canonical_types": dict(zip(api["TYPE_KEYS"], ("unsigned int", "int", "float", "unsigned long", "long", "double"))),
        "sizes": [4, 4, 4, 8, 8, 8], "alignments": [4, 4, 4, 8, 8, 8]}
    fixture_pin = pin(HERE / "source_call_fixture_v1.cpp")["sha256"]
    objects = [{"object_id": "whole_interface_source_fixture::data", "guest_base": 65536, "physical_base": 65536,
                "extent": 2, "dtype": 0, "source_pin": fixture_pin},
               {"object_id": "whole_interface_source_fixture::limits", "guest_base": 69632, "physical_base": 69632,
                "extent": 2, "dtype": 1, "source_pin": fixture_pin}]
    atlas = source["prepare_atlas"](objects)
    routes, contracts = source["render_routes"](api, declarations, abi)
    paths = {row["path"] for row in values["source_inputs"] + values["outputs"]}
    paths.update(str(HERE / name) for name in ("value-source-preparation-v1.json", "source_dispatch_v2.py",
        "whole_interface_v3.py", "whole-interface-v3-source-repair-receipt.json", "source_call_fixture_v1.cpp",
        "test_source_dispatch_v2.py", "prepare_source_dispatch_v2.py", "pure-source-dispatch-v2-initial.log",
        "pure-source-dispatch-v2-final.log", "README-source-dispatch-v2.md", "source-dispatch-v2-inverse-delta.json"))
    paths.update(str(EVIDENCE / name) for name in ("t28-whole-interface-values-v1-independent-static-review-20261016.json",
        "t28-whole-interface-binder-v3-independent-static-review-20261016.json"))
    before = [pin(path) for path in sorted(paths)]
    outputs = {"source_pointer_bridge_synthetic_v2.h": source["render_pointer_bridge"](atlas),
               "source_direct_families_v2.h": source["render_direct_families"](api, declarations),
               "source_routes_synthetic_v2.h": routes,
               "source-dispatch-synthetic-inputs-v2.json": json.dumps({"synthetic_only": True, "actual_compiler_abi": False,
                    "abi": abi, "objects": objects, "atlas": atlas, "page_bytes": 4096, "line_bytes": 64}, sort_keys=True, indent=2) + "\n",
               "source-dispatch-contracts-v2.json": json.dumps({"date": "2026-10-16 ET", "synthetic_abi_only": True,
                    "contracts": contracts, "other_selector": {"name": "get_data_type", "dtype": 6, "route": "dws_get_data_type_other"},
                    "owned_mmio_premise": True, "actual_full_tu_abi_cpu_access_producer_required": True,
                    "public_admission": False}, sort_keys=True, indent=2) + "\n"}
    for name, text in outputs.items(): (HERE / name).write_text(text)
    if before != [pin(path) for path in sorted(paths)]: raise ValueError("source input changed during assembly")
    result = {"date": "2026-10-16 ET", "status": "SOURCE_PREPARATION_ONLY / NO ACTUAL SOURCE-CALL ADMISSION",
        "source_inputs": before, "outputs": [pin(HERE / name) for name in sorted(outputs)],
        "counts": {"names": 26, "declarations": 27, "exact_six_type_instances": 132,
            "fixed_direct_packet_families": 11, "other_selector_helper": 1, "ordinary_fixture_objects": 2,
            "ordinary_fixture_cells": 4, "pure_tests": 14},
        "source_fixture": pin(HERE / "source_call_fixture_v1.cpp"),
        "proof_scope": "Owned MMIO semantics accepted TCB; optional body/hardware refinement is not required. Actual compiler/full-TU/ABI/source expression/CPU pointer instrumentation and new0.2 public verdict integration remain mandatory.",
        "synthetic_abi_and_address_layout": True, "alias_views_reuse_physical_cell_history": True,
        "registration_initializes_memory": False, "ordinary_mixed_width_or_type_aliases_refuse": True,
        "compiler_native_verifier_ssh_execution": False, "public_admission": False, "current_0_2": False,
        "full_ticket28": False, "prior_source_value_native_packets_unchanged": True}
    (HERE / "source-dispatch-preparation-v2.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    return pin(HERE / "source-dispatch-preparation-v2.json")


if __name__ == "__main__":
    print(json.dumps(prepare(), sort_keys=True))
