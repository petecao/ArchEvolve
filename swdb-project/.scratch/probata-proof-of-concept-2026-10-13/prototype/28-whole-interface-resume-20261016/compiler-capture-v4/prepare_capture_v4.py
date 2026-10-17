"""2026-10-16 ET. Compiler-free controller/policy/recipe preparation only."""
import hashlib
import json
from pathlib import Path
import sys


def no_child(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "socket.")) or event in {"os.system", "ctypes.dlopen"}:
        raise RuntimeError("compiler-free capture preparation refuses " + event)


sys.addaudithook(no_child)
HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
TRACE = WHOLE.parent / "28-public-memory-trace-resume-20261016"
POC = WHOLE.parent.parent
PROJECT = WHOLE.parents[3]
COMMIT = "2baf722fdaa6cba24b859eae3172a6f597417d72"
RAW = "/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v4"
REMOTE_PROJECT = "/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project"


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    original = WHOLE / "linux_native86_policy_v4.json"
    assert pin(original)["sha256"] == "14be0baf2dece709210abb6039b0ab7ede41c5e8d5d1dfbe08ed47b6f3ba9f5b"
    policy = json.loads(original.read_bytes())
    path = WHOLE / "compiler_unit_adapter_v2.py"
    assert pin(path)["sha256"] == "1cf112859f976f77e8381c777c977f5cf5857d6e18f1bd0e24f9689148e80317"
    adapter = {"__file__": str(path), "__name__": "inert_capture_recipe"}
    exec(compile(path.read_bytes(), str(path), "exec"), adapter)
    sources = [HERE / "linux_compiler_capture_v4.py", WHOLE / "linux_native86_entry_v4.py",
        WHOLE / "compiler_unit_adapter_v2.py", WHOLE / "whole_interface_v3.py",
        WHOLE / "source_call_fixture_v2.cpp", WHOLE / "compiler_abi_probe_v1.cpp",
        WHOLE / "compiler_include_v1/gem5/m5ops.h", TRACE / "closed_python_surface.py",
        TRACE / "python_startup_roles_v2.py", TRACE / "python_role_observer_v2.py",
        POC / "evidence/resume-20261016-lane-coordination/t28-linux-runtime-observer-v2-actual-20261016.json"]
    assert len({p.name for p in sources}) == len(sources)
    policy.update(schema="t28-whole-source-compiler-capture-4", raw_name=Path(RAW).name,
        entry_sha256=pin(sources[0])["sha256"], source_project=REMOTE_PROJECT, source_commit=COMMIT,
        scope="Clang-only original-source full-TU and separate literal ABI observation; no native/proof/current0.2 admission",
        role_profile="linux-selected4GiB180s-entry-only-source-capture",
        controller_files={p.name: {k: pin(p)[k] for k in ("bytes", "sha256")} for p in sources})
    expected = {"apps/dx100/benchmarks/API/MAA.hpp": "4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd",
        "apps/dx100/benchmarks/API/MAA_gem5.hpp": "5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174",
        "tests/fixtures/proof/dx100/interface-declarations-e4fc4af.json": "d48a3971f2e9421e736d72ff160074f22e9cbbb7c9c756ef52457a5c4314b3b6"}
    policy["source_inputs"] = []
    for relative, sha in expected.items():
        row = pin(PROJECT / relative)
        assert row["sha256"] == sha
        policy["source_inputs"].append({"relative": relative, **{k: row[k] for k in ("bytes", "sha256")}})
    policy["capture_recipe"] = adapter["capture_recipe"](compiler=policy["compiler"]["command"][0], project=REMOTE_PROJECT, raw=RAW)
    policy_path = HERE / "linux_compiler_capture_policy_v4.json"
    policy_path.write_text(json.dumps(policy, sort_keys=True, indent=2) + "\n")
    sources.append(policy_path)
    controller_inputs = [pin(p) for p in sources]
    assert sum(p["bytes"] for p in controller_inputs) < 1048576
    command = {"date": "2026-10-16 ET", "status": "INERT; independent review and root admission pending",
        "argv": [policy["python"], "-I", "-B", RAW + "/control/linux_compiler_capture_v4.py", REMOTE_PROJECT,
                 RAW, RAW + "/control/" + policy_path.name, pin(policy_path)["sha256"]],
        "source": str(Path(REMOTE_PROJECT).parent), "project": REMOTE_PROJECT, "source_commit": COMMIT,
        "raw_root": RAW, "node": policy["node"], "controller_inputs": controller_inputs,
        "root_reviewed_wrapper_hashes": policy["guard_files"],
        "root_guard": {"whole_tree_seconds": 180, "rss_cap_bytes": 4294967296, "workers": 1,
            "per_file_limit_bytes": 134217728, "raw_budget_bytes": 268435456,
            "disk_floor_bytes": policy["disk_floor_bytes"], "external_timeout_seconds": 300},
        "run_environment_unset": ["LIBRARY_PATH"],
        "root_required_environment": {"PROBATA_OUTPUT": RAW, "SWDB_VERIFIER_LOCK": RAW + "/verifier.lock",
            "SWDB_VERIFIER_RSS_CAP_BYTES": "4294967296"},
        "recipe": policy["capture_recipe"], "actual_launched": False,
        "root_acceptance": "All four actual commands exit0, exact original-source/ABI consumer succeeds, all26 names/both RF overloads, complete before/after source/control/runtime and dependency pins, owned tree guard healthy and finite root settlement.",
        "native_or_solver_run": False, "source_call_admission": False, "public_proof": False,
        "current_0_2": False, "full_ticket28": False}
    command_path = HERE / "linux_compiler_capture_command_v4.json"
    command_path.write_text(json.dumps(command, sort_keys=True, indent=2) + "\n")
    packet = {"date": "2026-10-16 ET", "status": "SOURCE PREPARATION ONLY; actual capture not admitted",
        "controller_inputs": controller_inputs, "command": pin(command_path), "preparation": pin(Path(__file__)),
        "pure_controls": pin(HERE / "test_capture_v4.py"), "readme": pin(HERE / "README.md"),
        "validation": {"pure_tests": 10, "failures": 0, "errors": 0, "skips": 0, "actual_main_or_child_invoked": False},
        "source_basis": [pin(WHOLE / "compiler-unit-source-packet-v2.json"),
            pin(POC / "evidence/resume-20261016-lane-coordination/t28-compiler-unit-v2-independent-static-review-20261016.json")],
        "inherited_policy": pin(original), "controls_bytes": sum(row["bytes"] for row in controller_inputs),
        "original_recipe_unchanged": True, "derived_stub": "Flat pinned m5ops.h copied byte-exactly into closed control/include/gem5/m5ops.h before capture; no additional include input.",
        "scientific_execution": False, "public_admission": False, "inverse": pin(HERE / "compiler-capture-v4-inverse.json"),
        "preserved_V3_review": pin(POC / "evidence/resume-20261016-lane-coordination/t28-compiler-capture-v3-independent-static-review-20261016.json"),
        "finalization_reserve_bytes":1048576, "final_entry_deadline_seconds":165}
    output = HERE / "compiler-capture-source-packet-v4.json"
    output.write_text(json.dumps(packet, sort_keys=True, indent=2) + "\n")
    print(json.dumps(pin(output), sort_keys=True))


if __name__ == "__main__":
    main()
