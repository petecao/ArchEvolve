"""2026-10-16 ET. INERT until root admission: four Clang observation phases.

No native executable, linker, version, WP/CBMC/solver or project import. Complete
original-source full-TU IDs, separate literal ABI observation, exact dependency
closure and explicit capture timing are retained. This is source preparation,
never public source-call/model/proof admission.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import stat
import subprocess
import sys
import time
import types


RAW_NAME = "probata-resume-20261016-t28-full-tu-2baf722f-v5"
SOURCE_COMMIT = "2baf722fdaa6cba24b859eae3172a6f597417d72"
WHOLE_SECONDS, ENTRY_SECONDS, RSS_BYTES = 180, 165, 4294967296
STAGE_BYTES, TOTAL_BYTES = 134217728, 268435456
FINAL_METADATA_RESERVE = 1048576
HELPER_SHA = "9f63dbe826ca70f2ceacd37b56753a5f212811a5a377c7baed59da4de60b7721"
ADAPTER_SHA = "1cf112859f976f77e8381c777c977f5cf5857d6e18f1bd0e24f9689148e80317"
BINDER_SHA = "217cdda6ca8eaea99526010f2c379dad963ca81c18c79322ce02ab8cc9296ed8"


def pin(path):
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or path.resolve(strict=True) != path:
        raise ValueError("canonical regular capture input required")
    with path.open("rb") as stream:
        value = hashlib.file_digest(stream, "sha256").hexdigest()
    if path.lstat() != before:
        raise ValueError("capture input changed while hashing")
    return {"path": str(path), "bytes": before.st_size, "sha256": value}


def save(path, value):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def recheck(rows):
    for row in rows:
        if pin(row["path"]) != row:
            raise ValueError("capture input changed: " + row["path"])


def original_helpers(path):
    if pin(path)["sha256"] != HELPER_SHA:
        raise ValueError("exact reviewed native runtime/role helper source required")
    wanted = {"make_dependencies", "verified_linux_lane", "physical_runtime"}
    nodes = [node for node in ast.parse(Path(path).read_bytes()).body
             if isinstance(node, ast.FunctionDef) and node.name in wanted]
    if len(nodes) != 3 or {node.name for node in nodes} != wanted:
        raise ValueError("exact three inherited helper nodes required")
    namespace = {"Path": Path, "hashlib": hashlib, "json": json, "os": os, "stat": stat,
                 "pin": pin, "recheck": recheck}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<reviewed-capture-role-runtime>", "exec"), namespace)
    return namespace


def check_derived_stub(control):
    include = control / "include"
    members = list(sorted(include.rglob("*")))
    if [str(p.relative_to(include)) for p in members] != ["gem5", "gem5/m5ops.h"]:
        raise ValueError("closed derived stub membership differs")
    if include.is_symlink() or not include.is_dir() or members[0].is_symlink() or not members[0].is_dir():
        raise ValueError("physical derived include directories required")
    actual, original = pin(members[1]), pin(control / "m5ops.h")
    if {k: actual[k] for k in ("bytes", "sha256")} != {k: original[k] for k in ("bytes", "sha256")}:
        raise ValueError("derived declaration-only stub differs")


def compare_dependencies(before, after, required):
    names = [row["path"] for row in before]
    if len(names) != len(set(names)) or after != names or not set(required) <= set(names):
        raise ValueError("AST/preprocessing physical dependency membership differs")


def check_prepared(prepared, declarations):
    if {row["name"] for row in prepared["calls"]} != {row["name"] for row in declarations}:
        raise ValueError("actual source fixture does not exercise all26 source names")
    if {row["formal_arity"] for row in prepared["calls"] if row["name"] == "get_new_reg"} != {0, 1}:
        raise ValueError("actual initialized/uninitialized register overload census differs")


def finalization_payloads(raw, out, result, *, used_bytes, elapsed):
    """Plan exact final metadata extent before publication; never raise caps."""
    result = dict(result)
    if not (0 <= elapsed <= ENTRY_SECONDS):
        result["accepted"] = False
        result["finalization_refusal"] = "entry deadline exceeded"
    result["wall_seconds"] = elapsed
    existing = [path for path in sorted(out.rglob("*"))
                if path.is_file() and path not in {out / "result.json", out / "artifact-manifest.json"}]
    rows = [{"relative": str(path.relative_to(out)), **pin(path)} for path in existing]
    def encode(value):
        return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    def plan(value):
        result_bytes = encode(value)
        result_row = {"relative": "result.json", "path": str(out / "result.json"),
                      "bytes": len(result_bytes), "sha256": hashlib.sha256(result_bytes).hexdigest()}
        manifest_bytes = encode(sorted([*rows, result_row], key=lambda row: Path(row["relative"]).parts))
        return result_bytes, manifest_bytes
    result_bytes, manifest_bytes = plan(result)
    if used_bytes + len(result_bytes) + len(manifest_bytes) > TOTAL_BYTES:
        result["accepted"] = False
        result["finalization_refusal"] = "projected final raw budget exceeded"
        result_bytes, manifest_bytes = plan(result)
    return result, result_bytes, manifest_bytes


def finalize_capture(raw, out, result, *, started):
    def used():
        return sum(path.stat().st_size for path in raw.rglob("*") if path.is_file())
    value, result_bytes, manifest_bytes = finalization_payloads(raw, out, result,
        used_bytes=used(), elapsed=time.monotonic() - started)
    if len(result_bytes) + len(manifest_bytes) > FINAL_METADATA_RESERVE or used() + len(result_bytes) + len(manifest_bytes) > TOTAL_BYTES:
        raise ValueError("reserved final metadata cannot fit unchanged raw budget")
    for name, data in (("result.json", result_bytes), ("artifact-manifest.json", manifest_bytes)):
        with (out / name).open("xb") as stream:
            stream.write(data)
    # Check the settled view after serialization and both publications. If an
    # overrun occurred, invalidate only these two owned final metadata files.
    elapsed, total = time.monotonic() - started, used()
    if value["accepted"] and (elapsed > ENTRY_SECONDS or total > TOTAL_BYTES):
        value["accepted"] = False
        value["finalization_refusal"] = "settled entry deadline or raw budget exceeded"
        value["wall_seconds"] = elapsed
        result_size = (out / "result.json").stat().st_size
        manifest_size = (out / "artifact-manifest.json").stat().st_size
        value, result_bytes, manifest_bytes = finalization_payloads(raw, out, value,
            used_bytes=total-result_size-manifest_size, elapsed=elapsed)
        for name, data in (("result.json", result_bytes), ("artifact-manifest.json", manifest_bytes)):
            with (out / name).open("wb") as stream:
                stream.write(data)
    return value["accepted"]


def main(argv):
    started = time.monotonic()
    deadline = started + ENTRY_SECONDS
    if len(argv) != 5 or not __debug__ or sys.flags.optimize or not sys.flags.isolated or not sys.dont_write_bytecode:
        raise ValueError("exact isolated -I -B PROJECT RAW POLICY SHA invocation required")
    project, raw, policy_path = (Path(value).resolve(strict=True) for value in argv[1:4])
    if raw.name != RAW_NAME or raw.is_symlink() or raw.is_relative_to(project.parent):
        raise ValueError("fresh external source-capture raw root required")
    control = raw / "control"
    if policy_path.parent != control or Path(__file__).resolve().parent != control:
        raise ValueError("exact raw/control controller paths required")
    policy_bytes = policy_path.read_bytes()
    if hashlib.sha256(policy_bytes).hexdigest() != argv[4]:
        raise ValueError("root-pinned capture policy differs")
    policy = json.loads(policy_bytes)
    if policy["raw_name"] != RAW_NAME or policy["source_commit"] != SOURCE_COMMIT or policy["source_project"] != str(project):
        raise ValueError("exact source/raw identity required")
    if policy["budgets"] != {"whole_seconds": WHOLE_SECONDS, "entry_seconds": ENTRY_SECONDS,
            "rss_bytes": RSS_BYTES, "stage_bytes": STAGE_BYTES, "total_bytes": TOTAL_BYTES}:
        raise ValueError("unchanged whole-tree/time/output capture budgets required")
    if sys.executable != policy["python"]:
        raise ValueError("selected Python invocation differs")
    controls = policy["controller_files"]
    derived = False

    def control_check():
        if policy_path.is_symlink() or not stat.S_ISREG(policy_path.lstat().st_mode):
            raise ValueError("physical regular policy required")
        expected = {policy_path.name, *controls} | ({"include"} if derived else set())
        if {p.name for p in control.iterdir()} != expected:
            raise ValueError("closed source-capture control membership differs")
        for name, value in controls.items():
            path = control / name
            if path.name != name or pin(path) != {"path": str(path), **value}:
                raise ValueError("staged capture controller differs: " + name)
        if derived:
            check_derived_stub(control)
        if pin(__file__)["sha256"] != policy["entry_sha256"] or hashlib.sha256(policy_path.read_bytes()).hexdigest() != argv[4]:
            raise ValueError("entry/policy changed")

    control_check()
    if shutil.disk_usage(raw).free < policy["disk_floor_bytes"] + TOTAL_BYTES:
        raise ValueError("capture disk floor plus unchanged output allowance required")
    for name, value in {"PROBATA_OUTPUT": str(raw), "SWDB_VERIFIER_LOCK": str(raw / "verifier.lock"),
                        "SWDB_VERIFIER_RSS_CAP_BYTES": str(RSS_BYTES)}.items():
        if os.environ.get(name) != value:
            raise ValueError("actual Linux capture role differs: " + name)
    launch = json.loads((raw / "launch.json").read_bytes())
    command = [policy["python"], "-I", "-B", str(Path(__file__).resolve()), str(project), str(raw), str(policy_path), argv[4]]
    if launch.get("command") != command or Path(launch["source"]).resolve() != project.parent or launch.get("source_commit") != SOURCE_COMMIT:
        raise ValueError("actual launch source/command differs")
    if any(launch.get(k) != v for k, v in {"rss_cap_bytes": RSS_BYTES, "workers": 1,
                                         "timeout_seconds": WHOLE_SECONDS, "node": policy["node"]}.items()):
        raise ValueError("actual capture lane/guard differs")
    for name, value in policy["guard_files"].items():
        if pin(raw / name)["sha256"] != value or launch.get("reviewed_wrapper_reuse", {}).get(name) != value:
            raise ValueError("exact adapted execute/watch bytes required")
    helpers = original_helpers(control / "linux_native86_entry_v4.py")
    live = helpers["verified_linux_lane"](policy["node"])
    marker = hashlib.sha256(json.dumps({"launch": pin(raw / "launch.json"), "live": live}, sort_keys=True).encode()).hexdigest()
    save(raw / "capture-linux-role.json", {"launch": pin(raw / "launch.json"), "live": live,
        "derived_marker": marker, "Mac_counted_claim": False})
    cache = raw / "entry-source-cache"
    if os.path.lexists(cache):
        raise ValueError("absent entry source cache required")
    sys.pycache_prefix = str(cache)
    os.environ.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPYCACHEPREFIX=str(cache))

    def module(name, expected=None):
        path = control / name
        if expected is not None and pin(path)["sha256"] != expected:
            raise ValueError("exact source consumer required")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != controls[name]["sha256"]:
            raise ValueError("capture module changed")
        result = types.ModuleType("capture_" + name[:-3])
        result.__file__ = str(path)
        exec(compile(data, str(path), "exec"), result.__dict__)
        return result

    closed, roles, observer = (module(name) for name in ("closed_python_surface.py", "python_startup_roles_v2.py", "python_role_observer_v2.py"))
    before = helpers["physical_runtime"](policy, closed)
    save(raw / "capture-runtime-before.json", before)
    roles.validate_role_plan_v2(policy["startup_roles"], metadata=policy["python_surface_binding"], source_project=project,
        root_observer_bytes=(control / policy["root_observer_file"]).read_bytes(), closed=closed)
    request = roles.role_request_v2(policy["startup_roles"], role="entry-isolated", environment=os.environ, cache=cache)
    observed = observer.observe_role_v2(request)
    roles.check_role_observation_v2(request, observed)
    save(raw / "capture-python-entry-role.json", observed)
    compiler = policy["compiler"]
    if compiler["command"] != [compiler["wrapper"]["path"]] or compiler["version"] != "22.1.8":
        raise ValueError("selected absolute LLVM22 wrapper required")
    recheck([compiler["wrapper"], compiler["driver"]])
    forbidden = ("CPATH", "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH", "OBJC_INCLUDE_PATH", "INCLUDE", "SDKROOT",
        "GCC_EXEC_PREFIX", "COMPILER_PATH", "LIBRARY_PATH", "LD_PRELOAD", "LD_AUDIT", "ASAN_SYMBOLIZER_PATH", "UBSAN_OPTIONS", "ASAN_OPTIONS")
    if any(os.environ.get(name) for name in forbidden):
        raise ValueError("ambient compiler/loader/sanitizer override refused")
    adapter = module("compiler_unit_adapter_v2.py", ADAPTER_SHA)
    binder = module("whole_interface_v4.py", BINDER_SHA)
    declarations = binder.inventory(project)
    out = raw / "component"
    out.mkdir()
    (out / "tmp").mkdir()
    (control / "include").mkdir()
    (control / "include/gem5").mkdir()
    with (control / "include/gem5/m5ops.h").open("xb") as stream:
        stream.write((control / "m5ops.h").read_bytes())
    derived = True
    control_check()
    original_inputs = [pin(control / name) for name in ("source_call_fixture_v2.cpp", "compiler_abi_probe_v1.cpp", "m5ops.h")]
    original_inputs += [pin(project / row["relative"]) for row in policy["source_inputs"]]
    for row, expected in zip(original_inputs[3:], policy["source_inputs"]):
        if {k: row[k] for k in ("bytes", "sha256")} != {k: expected[k] for k in ("bytes", "sha256")}:
            raise ValueError("immutable source/header input differs")
    recipe = adapter.capture_recipe(compiler=compiler["command"][0], project=str(project), raw=str(raw))
    if recipe != policy["capture_recipe"]:
        raise ValueError("reviewed four-phase recipe differs")
    environment = {"PATH": policy["path"], "HOME": policy["home"], "LANG": "C", "LC_ALL": "C", "TMPDIR": str(out / "tmp")}
    environment.update(policy["native_runtime"]["loader_environment"])
    save(out / "inputs-before.json", {"source": original_inputs, "environment": environment, "compiler": compiler,
        "recipe": recipe, "entry": pin(__file__), "policy": pin(policy_path), "scope": "Clang observations only"})
    commands, groups, prepared, error, after_errors = [], [], None, None, []

    def bytes_used():
        return sum(p.stat().st_size for p in raw.rglob("*") if p.is_file())

    def limit():
        resource.setrlimit(resource.RLIMIT_FSIZE, (STAGE_BYTES, STAGE_BYTES))

    def stage(item):
        remaining = min(45, deadline - time.monotonic() - 10)
        if remaining <= 0 or bytes_used() > TOTAL_BYTES-FINAL_METADATA_RESERVE:
            raise ValueError("capture time/output allowance exhausted")
        name = item["phase"]
        stdout_path = Path(item.get("stdout", str(out / (name + ".stdout"))))
        stderr_path = out / (name + ".stderr")
        row = {"phase": name, "argv": item["argv"], "cwd": str(out), "timeout_seconds": remaining}
        commands.append(row)
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            process = subprocess.Popen(item["argv"], cwd=out, env=environment, stdout=stdout, stderr=stderr,
                start_new_session=True, preexec_fn=limit)
            expires = time.monotonic() + remaining
            try:
                while process.poll() is None:
                    if time.monotonic() >= expires or bytes_used() > TOTAL_BYTES-FINAL_METADATA_RESERVE or stdout.tell() > STAGE_BYTES or stderr.tell() > STAGE_BYTES:
                        raise ValueError("capture stage time/output cap exceeded")
                    time.sleep(0.05)
            except BaseException:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                raise
            row["returncode"] = process.wait()
        row["stdout"], row["stderr"] = pin(stdout_path), pin(stderr_path)
        if row["returncode"] or bytes_used() > TOTAL_BYTES-FINAL_METADATA_RESERVE:
            raise ValueError("capture phase failed: " + name)

    try:
        for offset, label in ((0, "caller"), (2, "abi")):
            control_check()
            recheck(original_inputs)
            if helpers["physical_runtime"](policy, closed) != before:
                raise ValueError("runtime differs before preprocessing")
            stage(recipe["commands"][offset])
            dependencies = [pin(path) for path in helpers["make_dependencies"]((out / (label + ".d")).read_text(), label, out)]
            source_name = "source_call_fixture_v2.cpp" if label == "caller" else "compiler_abi_probe_v1.cpp"
            required = {str(control / source_name), str(control / "include/gem5/m5ops.h"),
                        str(project / "apps/dx100/benchmarks/API/MAA.hpp"), str(project / "apps/dx100/benchmarks/API/MAA_gem5.hpp")}
            compare_dependencies(dependencies, [row["path"] for row in dependencies], required)
            group = {"label": label, "dependencies": dependencies, "frozen": pin(out / (label + ".ii")),
                     "preprocess_dependency": pin(out / (label + ".d"))}
            groups.append(group)
            recheck(dependencies + original_inputs + [group["frozen"], group["preprocess_dependency"]])
            control_check()
            if helpers["physical_runtime"](policy, closed) != before:
                raise ValueError("runtime differs before original-source AST")
            stage(recipe["commands"][offset + 1])
            ast_used = helpers["make_dependencies"]((out / (label + ".ast.d")).read_text(), label + "-ast", out)
            compare_dependencies(dependencies, ast_used, required)
            recheck(dependencies + original_inputs + [group["frozen"], group["preprocess_dependency"]])
            control_check()
            if helpers["physical_runtime"](policy, closed) != before:
                raise ValueError("runtime differs after original-source AST")
            group["ast"] = pin(out / (label + ".ast.json"))
            group["ast_dependency"] = pin(out / (label + ".ast.d"))
        observation = {"commands": commands, "inputs": original_inputs, "groups": groups,
            "source_commit": SOURCE_COMMIT, "original_source_coordinates": True,
            "timing_tcb": recipe["dependency_timing_tcb"]}
        save(out / "compiler-observation.json", observation)
        prepared = adapter.prepare_unit(binder.__dict__, full_tu_raw=(out / "caller.ast.json").read_bytes(),
            abi_raw=(out / "abi.ast.json").read_bytes(), source_path=control / "source_call_fixture_v2.cpp",
            source_bytes=(control / "source_call_fixture_v2.cpp").read_bytes(), probe_path=control / "compiler_abi_probe_v1.cpp",
            probe_bytes=(control / "compiler_abi_probe_v1.cpp").read_bytes(), declarations=declarations,
            compiler_capture_pin=pin(out / "compiler-observation.json")["sha256"])
        check_prepared(prepared, declarations)
        save(out / "source-preparation.json", prepared)
    except Exception as failure:
        error = {"type": type(failure).__name__, "message": str(failure)}
    finally:
        save(out / "commands.json", commands)
        save(out / "used-inputs.json", groups)
        try:
            if helpers["physical_runtime"](policy, closed) != before:
                raise ValueError("runtime differs after capture")
            recheck(original_inputs)
            control_check()
            for group in groups:
                recheck(group["dependencies"] + [group["frozen"], group["preprocess_dependency"]] + [group[k] for k in ("ast", "ast_dependency") if k in group])
            for name, expected in policy["guard_files"].items():
                if pin(raw / name)["sha256"] != expected:
                    raise ValueError("Linux guard changed after capture")
        except Exception as failure:
            after_errors.append({"type": type(failure).__name__, "message": str(failure)})
        save(raw / "capture-runtime-after.json", {"runtime": before, "after_errors": after_errors})
        cache_present = os.path.lexists(cache)
        accepted = error is None and not after_errors and prepared is not None and len(commands) == 4 and not cache_present and bytes_used() <= TOTAL_BYTES
        accepted = finalize_capture(raw, out, {"accepted": accepted, "error": error, "after_input_errors": after_errors,
            "bytecode_cache_present": cache_present,
            "source_names": sorted({row["name"] for row in prepared["calls"]}) if prepared else [],
            "source_call_count": len(prepared["calls"]) if prepared else 0,
            "scope": "Actual Clang source/ABI preparation only; source/CPU/model/public admission remains required",
            "native_or_solver_executed": False, "public_proof": False, "current_0_2": False, "full_ticket28": False}, started=started)
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
