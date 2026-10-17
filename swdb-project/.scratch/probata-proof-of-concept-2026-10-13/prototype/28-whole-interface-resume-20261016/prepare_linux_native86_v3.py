"""2026-10-16 ET. Pure source/metadata packet assembly; never runs tools."""
import ast
import hashlib
import json
from pathlib import Path
import sys


def no_child(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork")) or event in {"os.system", "ctypes.dlopen"}:
        raise RuntimeError("inert native86 preparation forbids " + event)


sys.addaudithook(no_child)
HERE = Path(__file__).resolve().parent
POC = HERE.parent.parent
OLD = HERE.parent / "28-initialized-u32-resume-20261016"
HELPERS = HERE.parent / "28-public-memory-trace-resume-20261016"
EVIDENCE = POC / "evidence/resume-20261016-lane-coordination"
PROJECT = "/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project"
COMMIT = "2baf722fdaa6cba24b859eae3172a6f597417d72"
RAW = "/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-whole-native86-2baf722f-v3"


def pin(path):
    path = Path(path).resolve(strict=True)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def write(name, value):
    (HERE / name).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def prepare():
    prior_path = OLD / "linux_pair_policy_2baf722f_v4.json"
    prior = json.loads(prior_path.read_text())
    inventory_path = HERE / "native86-linux-runtime-passive-v5.json"
    inventory = json.loads(inventory_path.read_text())
    if not inventory["passive_only"] or inventory["admitted"] or inventory["unresolved"] or inventory["prior_pin_differences"]:
        raise ValueError("fresh passive unchanged physical runtime inventory required")
    entry = HERE / "linux_native86_entry_v3.py"
    ast.parse(entry.read_bytes())
    names = ["whole_values_native_v1.c", "whole_value_backend_v1.h", "whole_adapters.h",
             "whole_value_builders_v1.h", "whole_closed_routes_v1.h"]
    controls = [entry, *(HERE / name for name in names), *(HELPERS / name for name in
                ("closed_python_surface.py", "python_startup_roles_v2.py", "python_role_observer_v2.py")),
                EVIDENCE / prior["root_observer_file"]]
    for path in controls[6:]:
        if {key: value for key, value in pin(path).items() if key != "path"} != prior["controller_files"][path.name]:
            raise ValueError("reviewed helper/root observer identity changed")
    runtime = {key: inventory[key] for key in ("pins", "aliases", "trees", "absence", "loader_environment")}
    runtime.update(admitted=True, admission_boundary="Prospective policy requiring independent source review and root physical/launch admission before any child; not an actual run receipt.",
                   passive_inventory=pin(inventory_path), loader_scope="Exact closed child LD_LIBRARY_PATH and physical static candidates; OS loader/dlopen selection remains TCB, never observed by this inventory.")
    roles = dict(prior["startup_roles"])
    roles["source_project"] = PROJECT
    policy = {"date": "2026-10-16 ET", "schema": "private-native86-linux-policy-1", "raw_name": Path(RAW).name,
        "entry_sha256": pin(entry)["sha256"], "budgets": {"whole_seconds": 180, "entry_seconds": 165,
            "rss_bytes": 4294967296, "stage_bytes": 134217728, "total_bytes": 268435456},
        "disk_floor_bytes": 50 * 1024**3,
        "python": prior["linux_launch_binding"]["python"], "source_project": PROJECT, "source_commit": COMMIT,
        "node": 0, "path": "/usr/bin:/bin", "home": "/data1/yanruj/probata-verifiers/home",
        "controller_files": {path.name: {key: value for key, value in pin(path).items() if key != "path"} for path in controls},
        "guard_files": prior["linux_launch_binding"]["wrappers"],
        "python_surface_binding": prior["python_surface_binding"], "startup_roles": roles,
        "root_observer_file": prior["root_observer_file"], "runtime_files": prior["runtime_files"],
        "linux_header_surfaces": prior["linux_header_surfaces"], "compiler": inventory["compiler"], "native_runtime": runtime,
        "role_profile": {"entry": "entry-isolated", "rss_bytes": 4294967296, "whole_seconds": 180,
            "shared_child_environment_v2_called": False, "pytest_child": False,
            "scope": "Shared role parser/observer semantics only; actual 4-GiB startup environment is independently observed. No 8-GiB child builder, Mac run token or watchdog tag."},
        "source_origin": {"clean_git_source": {"project": PROJECT, "commit": COMMIT},
            "separately_pinned_payload": [pin(path) for path in controls], "prior_runtime_policy": pin(prior_path),
            "value_preparation": pin(HERE / "value-source-preparation-v1.json"),
            "independent_value_review": pin(EVIDENCE / "t28-whole-interface-values-v1-independent-static-review-20261016.json")},
        "scope": "Private C11/C++17 model harness only; no production/project import, body bypass, public formal proof, source-call admission or ticket completion."}
    policy_name = "linux_native86_policy_v3.json"
    write(policy_name, policy)
    argv = [policy["python"], "-I", "-B", RAW + "/control/" + entry.name, PROJECT, RAW,
            RAW + "/control/" + policy_name, pin(HERE / policy_name)["sha256"]]
    command = {"date": "2026-10-16 ET", "status": "INERT / UNLAUNCHED; independent review and root admission required",
        "argv": argv, "source": str(Path(PROJECT).parent), "project": PROJECT, "source_commit": COMMIT,
        "raw_root": RAW, "node": 0, "root_socket_lane_only": True, "root_creates_fresh_raw_root": True,
        "controller_inputs": [pin(path) for path in [*controls, HERE / policy_name]],
        "root_places_exact_controller_metadata": {"closed_control_membership": sorted([path.name for path in controls] + [policy_name])},
        "root_guard": {"whole_tree_seconds": 180, "rss_cap_bytes": 4294967296, "workers": 1,
            "external_timeout_seconds": 300, "queue_seconds": 300, "raw_budget_bytes": 268435456,
            "per_file_limit_bytes": 134217728, "disk_floor_bytes": 50 * 1024**3},
        "root_reviewed_wrapper_hashes": policy["guard_files"], "root_required_environment": {
            "PROBATA_OUTPUT": RAW, "SWDB_VERIFIER_LOCK": RAW + "/verifier.lock", "SWDB_VERIFIER_RSS_CAP_BYTES": "4294967296",
            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPYCACHEPREFIX": RAW + "/entry-source-cache"},
        "root_environment_requirement": "No extra PYTHON selectors, compiler include/library selectors, LD_PRELOAD/LD_AUDIT, sanitizer options or symbolizer overrides; child environment is closed by the entry.",
        "exact_native_result_each_language": {"controls": 86, "family_dtype_cases": 66, "history_cases": 6,
            "subtract_fold_cases": 6, "action_order_cases": 2, "refusals": 6},
        "compile_recipe": "Original -x c/-std=c11 and -x c++/-std=c++17 preprocessing -MD -MF -MT; first dependency hashes after preprocessing, then frozen .i/.ii compile, explicit canonical BFD -Wl,-t link and exact native JSON with empty sanitizer stderr. --no-default-config for every driver phase; ASan+UBSan, -O1 -g -fno-omit-frame-pointer -fno-sanitize-recover=all.",
        "root_acceptance": "Recheck every staged/source/runtime pin before launch; exact launch/execute/watch/live lane, outer guard exit0/time<=180/RSS<=4GiB/finalnull/nochildren, entry accepted true, eight zero-exit phases, two exact censuses, absent caches, complete manifests and cold independent reconciliation.",
        "physical_runtime_inventory": pin(inventory_path), "source_packet_preparation": pin(HERE / "value-source-preparation-v1.json"),
        "private_native_only": True, "actual_launched": False, "public_formal": False, "source_call_admission": False,
        "Mac_counted_token_required": False, "current_0_2": False, "full_ticket28": False}
    write("linux_native86_command_v3.json", command)
    write("linux-native86-source-packet-v3.json", {"date": "2026-10-16 ET", "source_only": True,
        "controls": [pin(path) for path in [*controls, HERE / policy_name, HERE / "linux_native86_command_v3.json",
             inventory_path, HERE / "collect_linux_native86_runtime_v5_frozen.py", HERE / "prepare_linux_native86_v3.py",
             HERE / "test_linux_native86_entry_v3.py", HERE / "pure-linux-native86-entry-v3-final.log", HERE / "linux-native86-plan-v3.md", HERE / "linux-native86-v3-inverse-delta.json"]],
        "parent_immutable_source": {"project": PROJECT, "commit": COMMIT},
        "runtime_counts": {"new_physical_pins": len(runtime["pins"]), "link_records": len(runtime["aliases"]),
            "complete_trees": len(runtime["trees"]), "prior_runtime_files": len(prior["runtime_files"])},
        "actual_compiler_linker_native_verifier_execution": False, "actual_runtime_inventory_only": True,
        "independent_source_review_pending": True})
    return {name: pin(HERE / name) for name in (entry.name, policy_name, "linux_native86_command_v3.json", "linux-native86-source-packet-v3.json")}


if __name__ == "__main__":
    print(json.dumps(prepare(), sort_keys=True, indent=2))
