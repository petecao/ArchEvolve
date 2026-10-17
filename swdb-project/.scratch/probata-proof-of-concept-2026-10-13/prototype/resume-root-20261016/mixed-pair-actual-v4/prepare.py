"""2026-10-16 ET. Inert metadata builder; read-only Git and physical files only.

No project import, tool discovery, remote operation, or evaluation is performed.
Published source and root30 actual success are bound; root still owns dispatch.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
PROJECT = POC.parents[1]
REPO = PROJECT.parent
SOURCE = "dcdecf317a0e9b34f3ce12d5b914eb823c439fbc"
REMOTE = "/data1/yanruj/probata-resume-20261016-dcdecf31"
RAW_NAME = "probata-resume-20261016-dcdecf31-mixed-pair-public-v4"
RAW = "/data/yanruj/EvolveSWDB_runs/" + RAW_NAME
SELECTION = "tests/test_pair_pointer_workflow.py::test_actual_mixed_pair_bodies_callers_and_bounded_cpp_replay"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def row(path, name=None):
    raw = path.read_bytes()
    return {"path": str(path), "name": name or path.name, "bytes": len(raw), "sha256": digest(raw)}


def document(path, expected):
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError("reviewed metadata input changed: " + str(path))
    return json.loads(raw)


def git(*args, data=None):
    return subprocess.check_output(["/usr/bin/git", "--no-replace-objects", "-C", str(REPO), *args],
                                   input=data, timeout=180)


def blob_hashes(names):
    requests = [(SOURCE + ":swdb-project/" + name).encode() for name in sorted(set(names))]
    packed = git("cat-file", "--batch", data=b"\n".join(requests) + b"\n")
    result, offset = {}, 0
    for name in sorted(set(names)):
        newline = packed.index(b"\n", offset)
        _oid, kind, size = packed[offset:newline].split()
        if kind != b"blob":
            raise ValueError("selected source must be an immutable Git blob")
        offset = newline + 1
        result[name] = digest(packed[offset:offset + int(size)])
        offset += int(size)
        if packed[offset:offset + 1] != b"\n":
            raise ValueError("invalid Git batch framing")
        offset += 1
    if offset != len(packed):
        raise ValueError("unconsumed Git batch output")
    return result


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")


def source_bytes(name):
    return git("cat-file", "blob", SOURCE + ":swdb-project/" + name)


def source_literals(raw, names):
    found = {}
    for item in ast.parse(raw).body:
        if isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
            name = item.targets[0].id
            if name in names:
                found[name] = ast.literal_eval(item.value)
        elif isinstance(item, ast.AugAssign) and isinstance(item.target, ast.Name) and item.target.id in names:
            if not isinstance(item.op, ast.Add) or item.target.id not in found:
                raise ValueError("unreviewed composite checker literal construction")
            found[item.target.id] += ast.literal_eval(item.value)
    if set(found) != set(names):
        raise ValueError("incomplete composite checker source constants")
    return found


def main():
    initialized_path = POC / "prototype/28-initialized-u32-resume-20261016/linux_pair_policy_04af74c1_v5.json"
    initialized = document(initialized_path, "bae7dc4c11e44bfd763ece9178dcc99f1aaffac3e492efdd3477137fae846637")
    trace_path = POC / "prototype/28-public-memory-trace-resume-20261016/linux_trace_policy_04af74c1_v4.json"
    trace = document(trace_path, "d61807f5595e77aabdbd054b6f00caff636775f07ab697f368af8f87864241de")
    native_path = POC / "prototype/28-whole-interface-resume-20261016/linux_native86_policy_v4.json"
    native = document(native_path, "14be0baf2dece709210abb6039b0ab7ede41c5e8d5d1dfbe08ed47b6f3ba9f5b")
    sibling_path = HERE / "clang-sibling-passive.json"
    sibling = document(sibling_path, "8dfe61c967652da23db53548286078356c100d896ba55bffb892596c77914f40")
    aliases_path = HERE / "prior19-pytest-aliases.json"
    aliases_observation = document(aliases_path, "69b6494d01946e34aeee72ff351ce3ec25d46296f52a416e175e0ee29e7dd0d3")
    pytest_path = HERE / "pytest-tmpdir-source-observation.json"
    pytest_observation = document(pytest_path, "24709dcf0212c84770bf60826a5472072e94862ad3d8a630b335e66c11c0777d")
    if (pytest_observation["sha256"] != "5099f71d89413191c9e7515c9d4fe9fc7083bb73306f2cf1f73a9f89c862ed90"
            or pytest_observation["bytes"] != 13271 or len(aliases_observation["symlinks"]) != 11):
        raise ValueError("root's pinned pytest source/alias observations differ")
    case_prefix = re.sub(r"[\W]", "_", SELECTION.split("::")[-1])[:30]
    if case_prefix != "test_actual_mixed_pair_bodies_":
        raise ValueError("exact selected pytest case prefix changed")
    pytest_base = "mixed-pair-profile/pytest/" + case_prefix
    c_wrapper = sibling["wrappers"][0]
    if (c_wrapper["sha256"] != "cb1253820eb3815c92a98f20e384f1dc8350eb90839588cd567f4b3963ba0d78"
            or digest(c_wrapper["inert_wrapper_text"].encode()) != c_wrapper["sha256"]
            or c_wrapper["mode"] != 0o755 or c_wrapper["bytes"] != 128
            or c_wrapper["symlink"] is not False or c_wrapper["path"] != c_wrapper["physical_path"]):
        raise ValueError("root passive C-side wrapper observation differs")
    native["native_runtime"]["pins"].append({key: c_wrapper[key] for key in ("path", "bytes", "sha256")})
    driver = initialized["linux_clang_components"]["driver"]
    bin_root = str(Path(driver["path"]).parent)
    aliases = {entry["path"]: entry for entry in native["native_runtime"]["aliases"]}
    for path, target, resolved in [(bin_root + "/clang", "clang-22", driver["path"]),
                                  (bin_root + "/clang++", "clang", driver["path"]),
                                  ("/bin", "usr/bin", "/usr/bin"), ("/usr/bin/sh", "dash", "/usr/bin/dash")]:
        if aliases.get(path) != {"path": path, "target": target, "resolved": resolved}:
            raise ValueError("C wrapper interpreter/driver alias closure differs")
    if not any(entry["path"] == driver["path"] and entry["sha256"] == driver["sha256"]
               for entry in native["native_runtime"]["pins"]):
        raise ValueError("C wrapper driver physical pin is not in native closure")
    policy = copy.deepcopy(initialized)
    if any(native[key] != initialized[key] for key in ("runtime_files", "linux_header_surfaces", "python_surface_binding")):
        raise ValueError("reviewed native/WP physical closure does not agree")
    if trace["runtime_files"] != initialized["runtime_files"]:
        raise ValueError("reviewed CBMC/WP runtime files do not agree")
    setup = source_literals(source_bytes("swdb/proof_setup.py"), {"CHECK_SOURCES", "SETUP_VERSION", "READING_VERSION"})
    checker_files = ["swdb/" + name for name in setup["CHECK_SOURCES"]]
    checker_files += ["vocab/proof_failure_classes.yaml", "vocab/proof_subject_kinds.yaml"]
    extras = ["tests/test_pair_pointer_workflow.py", "tests/test_pair_workflow.py", "tests/testkit/pair_workflow.py",
              "tests/testkit/dx100_selector.py", "tests/fixtures/proof/lowering/pair_pointer.cc",
              "tests/test_pair_pointer_initialization.py", *checker_files]
    policy["source_files"] = blob_hashes([*initialized["source_files"], *extras])
    roots = [*initialized["source_consumer_trees"], "tests/test_pair_pointer_workflow.py", "tests/test_pair_workflow.py",
             "tests/test_pair_pointer_initialization.py"]
    policy["source_consumer_trees"] = {name: {"oid": git("rev-parse", "--verify", SOURCE + ":swdb-project/" + name).decode().strip()}
                                       for name in sorted(set(roots))}
    cbmc_constants = source_literals(source_bytes("swdb/cbmc_translator.py"), {"TOOL_ID", "TOOL_VERSION"})
    model_constants = source_literals(source_bytes("swdb/std_models.py"), {"MODELS_ID", "MODELS_VERSION"})
    setup_rows = [{"path": name, "sha256": policy["source_files"][name]} for name in checker_files]
    setup_digest = digest(json.dumps(setup_rows, sort_keys=True, separators=(",", ":")).encode())
    checkers = {
        "bounded_initialization": {"id": "swdb-bounded-initialization-1", "sha256": digest(b"".join(source_bytes(name) for name in
            ("swdb/bounded_initialization.py", "swdb/proof_semantics.py", "swdb/bounded_std_initialization.py")))},
        "cbmc_translator": {"id": cbmc_constants["TOOL_ID"] + "-" + cbmc_constants["TOOL_VERSION"],
                            "sha256": digest(source_bytes("swdb/cbmc_translator.py") + source_bytes("swdb/bounded_entry_windows.py"))},
        "wp_pointer_bounds": {"id": "swdb-wp-pointer-bounds-1", "sha256": policy["source_files"]["swdb/wp_pointer_bounds.py"]},
        "std_models": {"id": model_constants["MODELS_ID"] + "-" + model_constants["MODELS_VERSION"],
                       "sha256": policy["source_files"]["swdb/std_models.py"]},
        "proof_setup": {"proof_setup_check": {"version": setup["SETUP_VERSION"], "sha256": setup_digest},
                        "verdict_reading": {"version": setup["READING_VERSION"], "sha256": setup_digest}}}
    root_admission_path = POC / "evidence/t25-pair-pointer-controls-v2-root-admission-20261016.json"
    root_admission = document(root_admission_path, "3ba333bebdd77c6117f4bfeb6981cafda249248a3323d6ab48b02f55ef12a9ae")
    if (root_admission["source_commit"] != SOURCE or root_admission["status"] != "ROOT_CONTROLS_PASSED"
            or root_admission["actual_success_admitted"] is not True):
        raise ValueError("exact root30 actual admission is not complete for this source")
    (HERE / "root30-control-admission.json").write_bytes(root_admission_path.read_bytes())
    policy.update(source_commit=SOURCE, raw_name=RAW_NAME, date="2026-10-16 ET", schema="mixed-pair-prospective-4",
                  selection=SELECTION, profile_seconds=900, native_runtime=native["native_runtime"],
                  accepted_cbmc_release_family=trace["accepted_cbmc_release_family"],
                  cbmc_version_output=trace["cbmc_version_output"],
                  source_checker_identities=checkers,
                  source_checker_material={"proof_setup_ordered_inputs": setup_rows,
                      "c_lowering_physical_source": policy["source_files"]["swdb/c_lowering.py"],
                      "c_lowering_composite": "Fresh project identity under admitted source/runtime guards; includes the fresh cc1/frontend context and new bounded initializedness digest. No retired host/source composite is copied."},
                  root_control_admission={"file": "root30-control-admission.json",
                      "expected_raw_root": "/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-dcdecf31-t25-pair-pointer-controls-v2",
                      "final_root_receipt": str(POC / "evidence/t25-pair-pointer-controls-v2-root-admission-20261016.json"),
                      "required_schema": "mixed-pair-root30-admission-1", "status": "ROOT_CONTROLS_PASSED",
                      "receipt_origin": row(root_admission_path)},
                  pytest_alias_policy={"case_prefix": case_prefix, "basetemp_relative": "mixed-pair-profile/pytest",
                      "source": {key: pytest_observation[key] for key in ("path", "bytes", "sha256")},
                      "source_observation": row(pytest_path), "prior_generated_alias_observation": row(aliases_path),
                      "aliases": {pytest_base + "current": {"literal_target": RAW + "/" + pytest_base + "0",
                                                            "target_relative": pytest_base + "0"}},
                      "fresh_basetemp_required": True, "require_exact_complete_final_set": True,
                      "scope": "Exactly one fresh test invocation; pinned _mk_tmp derives sanitized name[:30], numbered suffix0. Prior19 confirms the absolute current-link convention; no actual mixed-pair alias is claimed observed."},
                  finalization={"reserve_bytes": 65536, "result_byte_cap": 16384, "time_margin_seconds": 1.0,
                      "scope": "All pre-final extent checks leave64KiB. Result JSON projection must fit16KiB and remaining hard256MiB cap; exit0 additionally requires exact post-fsync extent/alias and whole-entry time checks. Remaining reserve covers bounded stdout and root guard metadata."},
                  mixed_native_c_wrapper={"admitted": True, **{key: c_wrapper[key] for key in ("path", "bytes", "sha256", "mode")},
                      "origin": {"file": sibling_path.name, "sha256": row(sibling_path)["sha256"]},
                      "scope": "Prospective physical pin from fresh root passive metadata. Existing native aliases close LLVM clang -> clang-22 and /bin/sh -> dash; all are rechecked before/after actual use. No driver executed to obtain this pin."},
                  guard={"whole_tree_seconds": 1200, "external_timeout_seconds": 1320,
                         "rss_cap_bytes": 8589934592, "workers": 1,
                         "raw_budget_bytes": 268435456, "per_file_bytes": 134217728},
                  source_admission={"root_authorized": True, "known_source_refusal": False,
                      "reason": "Exact published dcdecf source and root30 actual success are bound by the frozen root receipt. Authorization is only this prospective eight-record profile; root final packet/runtime/lane review still precedes actual dispatch.",
                      "supersession": "V1/V2 source refusals and V3 pending admission remain preserved. Root owns all final admission and actual execution."},
                  scope="Prospective eight-record mixed-pair public fixture workflow only. Published source/root30 actual success prerequisites are bound; root final packet/runtime/lane review remains required. Producer completion is not independent cold scientific acceptance.")
    policy["tools"]["cbmc"] = trace["tools"]["cbmc"]
    policy["startup_roles"]["source_project"] = REMOTE + "/swdb-project"
    policy["linux_launch_binding"].update(node=1, entry_sha256=row(HERE / "entry.py")["sha256"])
    inputs = [row(POC / "prototype/28-public-memory-trace-resume-20261016" / name) for name in
              ("closed_python_surface.py", "python_startup_roles_v2.py", "python_role_observer_v2.py", "cbmc_release_gate.py")]
    inputs += [row(POC / "evidence/resume-20261016-lane-coordination" / initialized["root_observer_file"])]
    inputs += [row(HERE / name) for name in ("reviewed_wp_gates.py", "reviewed_native_gates.py", "reviewed-function-lineage.json", "clang-sibling-passive.json", "prior19-pytest-aliases.json", "pytest-tmpdir-source-observation.json", "root30-control-admission.json")]
    for entry in inputs:
        if entry["name"] in initialized["controller_files"]:
            wanted = initialized["controller_files"][entry["name"]]
            if {key: entry[key] for key in ("bytes", "sha256")} != wanted:
                raise ValueError("reviewed helper/runtime observation changed")
    policy["controller_files"] = {entry["name"]: {key: entry[key] for key in ("bytes", "sha256")} for entry in inputs}
    write(HERE / "policy.json", policy)
    inputs += [row(HERE / name) for name in ("entry.py", "policy.json")]
    if len({entry["name"] for entry in inputs}) != len(inputs) or sum(entry["bytes"] for entry in inputs) > 1048576:
        raise ValueError("unique closed controls must fit root's 1MiB staging cap")
    command = {"date": "2026-10-16 ET", "status": "INERT_ROOT30_BOUND_PENDING_FINAL_ROOT_REVIEW", "actual_launched": False,
        "root_final_review_and_lane_admission_required": True, "source_commit": SOURCE,
        "source": REMOTE + "/swdb-project", "raw_root": RAW, "node": 1,
        "argv": [policy["tools"]["opam"]["path"], "exec", "--switch=framac-33", "--",
                 policy["linux_launch_binding"]["python"], "-I", "-B", RAW + "/control/entry.py",
                 REMOTE + "/swdb-project", RAW, RAW + "/control/policy.json", row(HERE / "policy.json")["sha256"]],
        "controller_inputs": inputs, "controller_total_bytes": sum(entry["bytes"] for entry in inputs),
        "root_guard": {"whole_tree_seconds": 1200, "external_timeout_seconds": 1320, "rss_cap_bytes": 8589934592,
                       "workers": 1, "raw_budget_bytes": 268435456, "per_file_bytes": 134217728},
        "run_environment_unset": ["LIBRARY_PATH"], "test_seconds": 900, "selection": SELECTION,
        "expected": {"junit_cases": 1, "skips": 0, "proof_records": 8, "WP_models": 4, "WP_callers": 2, "CBMC_callers": 2},
        "actual_environment": {"SWDB_MIXED_PAIR_ACTUAL": "1", "SWDB_PAIR_ACTUAL": "0",
                               "SWDB_DX100_SELECTOR_ACTUAL_LINEUP": policy["actual_initialized_lineup"],
                               "SWDB_PAIR_DEADLINE_MONOTONIC": "computed once from monotonic clock +900 seconds before the exact child startup/pytest"},
        "runtime_boundary": "Physical candidate closure rehashed before/after; OS loader/dlopen and between-check changes remain TCB. Every actual command runs inside reviewed whole-tree guards and the verified socket lane.",
        "additional_runtime_input": policy["mixed_native_c_wrapper"],
        "pytest_alias_policy": policy["pytest_alias_policy"], "finalization": policy["finalization"],
        "independent_cold_acceptance": False, "source_or_caller_admission": False}
    write(HERE / "command.json", command)
    preparation = {"date": "2026-10-16 ET", "status": "INERT_ROOT30_BOUND_PENDING_FINAL_ROOT_REVIEW", "actual_launched": False,
        "source_commit": SOURCE, "source_control_blocker": policy["source_admission"],
        "inputs": [row(path) for path in (initialized_path, trace_path, native_path, sibling_path, aliases_path, pytest_path, root_admission_path, HERE / "prepare.py")],
        "outputs": [row(HERE / name) for name in ("entry.py", "reviewed_wp_gates.py", "reviewed_native_gates.py",
                                                     "reviewed-function-lineage.json", "policy.json", "command.json")],
        "selected_source_count": len(policy["source_files"]), "consumer_root_count": len(policy["source_consumer_trees"]),
        "runtime_file_count": len(policy["runtime_files"]), "native_pin_count": len(policy["native_runtime"]["pins"]),
        "controller_total_bytes": command["controller_total_bytes"],
        "method": "Original public test/helper/method source pins and four-model/code/dependency/negative/replay criteria are unchanged. No record/catalog payload interpreted; selected source blobs only SHA-256 and consumer Git OIDs.",
        "boundaries": {"compiler_native_solver_executed": False, "SSH_used": False, "actual_admission": False,
                       "scientific_acceptance": False, "root_owned_actual_execution": True}}
    write(HERE / "preparation.json", preparation)
    print(json.dumps({"status": preparation["status"], "controller_total_bytes": command["controller_total_bytes"],
                      "selected_source_count": len(policy["source_files"]), "command": row(HERE / "command.json")}))


if __name__ == "__main__":
    main()
