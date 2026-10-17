"""2026-10-16 ET. INERT Linux private native86 controller; never public proof.

No project import. Root independently admits source, Python/runtime/link closure,
exact launch and a live socket lane before one180-second/4-GiB tree. The selected
wrapper/driver/linker paths are prospective pins, never discovered with probes.
"""
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


RAW_NAME = "probata-resume-20261016-t28-whole-native86-2baf722f-v3"
SANITIZERS = ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-fno-sanitize-recover=all"]
RESULT = {"controls": 86, "family_dtype_cases": 66, "history_cases": 6,
          "subtract_fold_cases": 6, "action_order_cases": 2, "refusals": 6}
INPUTS = ("whole_values_native_v1.c", "whole_value_backend_v1.h", "whole_adapters.h",
          "whole_value_builders_v1.h", "whole_closed_routes_v1.h")
CLANG_WRAPPER = ("/data/yanruj/EvolveSWDB_runs/probata-source-gate-native-20261015-1102-node0/compiler-bin/clang++",
                 "3c053dce26cf5ef22656f1ec9efe0cdf2911a37d5a910261895ac9c42e128fe4")
CLANG_DRIVER = ("/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin/clang-22",
                "31a40dc31f3c15a47aa119aa148f339bf363d8f61202ddbdacbd3f24b71ba113")
WHOLE_SECONDS, ENTRY_SECONDS, RSS_BYTES = 180, 165, 4294967296
STAGE_BYTES, TOTAL_BYTES = 134217728, 268435456


def pin(path):
    path = Path(path).resolve(strict=True)
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest}


def save(path, value):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def recheck(rows):
    for row in rows:
        if pin(row["path"]) != row:
            raise ValueError("physical input changed: " + row["path"])


def make_dependencies(text, target, cwd):
    """Closed Make syntax copied from reviewed memory53 preparation entry."""
    if not text.startswith(target + ":"):
        raise ValueError("dependency target differs")
    text = text[len(target) + 1:]
    result, token, index = [], "", 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 1
            if index >= len(text): raise ValueError("truncated dependency escape")
            char = text[index]
            if char == "\n":
                index += 1
                continue
            if char not in " \t#\\:": raise ValueError("unsupported dependency escape")
            token += char
        elif char in "$#": raise ValueError("dependency expansion/comments refused")
        elif char.isspace():
            if token:
                result.append(token)
                token = ""
        else: token += char
        index += 1
    if token: result.append(token)
    if not result: raise ValueError("empty dependency set")
    return sorted({str((Path(cwd) / value).resolve(strict=True)) for value in result})


def link_inputs(text, cwd):
    """GNU/LLD -t paths, optionally followed by an archive member name."""
    result = set()
    for line in text.splitlines():
        value = line.strip()
        if not value: continue
        if value.endswith(")") and "(" in value:
            value, member = value.rsplit("(", 1)
            if not member[:-1] or any(c in member for c in "\n\r"): raise ValueError("link archive member syntax")
        if not value or any(c.isspace() for c in value): raise ValueError("unreviewed linker trace syntax")
        path = (Path(cwd) / value).resolve(strict=True)
        if not path.is_file(): raise ValueError("link trace input is not a file")
        result.add(str(path))
    if not result: raise ValueError("linker trace is empty")
    return sorted(result)


def verified_linux_lane(node):
    """Same live-kernel lease/affinity checks as the reviewed initialized V4."""
    lane = os.environ.get("LACT_SOCKET_LANE_PID", "")
    generation = os.environ.get("LACT_SOCKET_LANE_GENERATION", "")
    if not lane.isdigit() or not generation.isdigit(): raise ValueError("live socket lane/generation required")
    pid, ancestors = os.getpid(), []
    for _ in range(64):
        if pid <= 1 or pid == int(lane): break
        ancestors.append(pid)
        pid = int(Path("/proc/" + str(pid) + "/stat").read_text().rsplit(") ", 1)[1].split()[1])
    if pid != int(lane) or b"socket_lane.sh" not in Path("/proc/" + lane + "/cmdline").read_bytes():
        raise ValueError("actual socket-lane ancestor required")
    def cpu_set(text):
        result = set()
        for part in text.strip().split(","):
            ends = part.split("-"); result.update(range(int(ends[0]), int(ends[-1]) + 1))
        return result
    cpus = cpu_set(Path("/sys/devices/system/node/node" + str(node) + "/cpulist").read_text())
    if not cpus or set(os.sched_getaffinity(0)) != cpus: raise ValueError("exact selected-node CPU affinity required")
    first = Path("/proc/self/numa_maps").read_text().splitlines()[0].split()
    if len(first) < 2 or first[1] != "bind:" + str(node): raise ValueError("exact selected-node memory bind required")
    lease_root = Path("/data1/yanruj/lact-host-lease")
    name = "mbit10-evaluation-node" + str(node)
    lease, descriptor = lease_root / (name + ".lease"), Path("/proc/" + lane + "/fd/9")
    if descriptor.resolve() != lease or (descriptor.stat().st_dev, descriptor.stat().st_ino) != (lease.stat().st_dev, lease.stat().st_ino):
        raise ValueError("socket-lane ancestor lease fd9 differs")
    metadata = json.loads((lease_root / (name + ".meta.json")).read_bytes()); owner = metadata.get("lease", {})
    if metadata.get("state") != "held" or str(owner.get("daemon_pid")) != lane or str(owner.get("generation")) != generation:
        raise ValueError("live socket lease generation differs")
    return {"lease": name, "generation": int(generation), "ancestor_pid": int(lane),
            "ancestor_chain": ancestors, "cpus": sorted(cpus), "memory_policy": "bind:" + str(node), "fd9_matches_lease": True}


def physical_runtime(policy, closed):
    python = closed.verify_python_metadata(policy["python_surface_binding"])
    for path, expected in policy["runtime_files"].items():
        if pin(path)["sha256"] != expected: raise ValueError("runtime file differs: " + path)
    headers = policy["linux_header_surfaces"]
    if set(headers) != {"libc++", "clang-resource"}: raise ValueError("two exact LLVM header surfaces required")
    for name, header in headers.items():
        root = Path(header["path"])
        if closed._resolution(root, []) != root or root.is_symlink() or not root.is_dir():
            raise ValueError("physical LLVM header root required")
        rows = []
        for path in sorted(root.rglob("*")):
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode): continue
            if not stat.S_ISREG(mode): raise ValueError("nonregular LLVM header input")
            row = pin(path); rows.append({"relative": str(path.relative_to(root)), "bytes": row["bytes"], "sha256": row["sha256"]})
        digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        if len(rows) != header["count"] or digest != header["inventory_sha256"]:
            raise ValueError("LLVM header membership/content differs: " + name)
    native = policy["native_runtime"]
    if native.get("admitted") is not True or not native.get("pins") or not native.get("trees"):
        raise ValueError("complete prospectively admitted native link/runtime closure required")
    recheck(native["pins"])
    for alias in native["aliases"]:
        path = Path(alias["path"])
        if not path.is_symlink() or os.readlink(path) != alias["target"] or str(path.resolve(strict=True)) != alias["resolved"]:
            raise ValueError("native runtime link chain differs")
    for absent in native["absence"]:
        if os.path.lexists(absent): raise ValueError("native runtime absence obligation changed")
    for tree in native["trees"]:
        root = Path(tree["path"])
        if root.is_symlink() or not root.is_dir(): raise ValueError("physical native runtime root required")
        found = []
        for path in sorted(root.rglob("*")):
            mode = path.lstat().st_mode
            if stat.S_ISDIR(mode): continue
            if stat.S_ISLNK(mode):
                found.append({"relative": str(path.relative_to(root)), "symlink": os.readlink(path), "resolved": str(path.resolve(strict=True))})
            elif stat.S_ISREG(mode):
                row = pin(path); found.append({"relative": str(path.relative_to(root)), "bytes": row["bytes"], "sha256": row["sha256"]})
            else: raise ValueError("special native runtime input")
        if found != tree["files"]: raise ValueError("native runtime membership/content differs")
    return {"python": python, "runtime_files": len(policy["runtime_files"]), "native_pins": len(native["pins"]),
            "native_roots": len(native["trees"]), "scope": "physical source/runtime identity; no proof or native result"}


def main(argv):
    started = time.monotonic(); deadline = started + ENTRY_SECONDS
    if len(argv) != 5 or not __debug__ or sys.flags.optimize or not sys.flags.isolated or not sys.dont_write_bytecode:
        raise ValueError("exact isolated nonoptimized -I -B PROJECT RAW POLICY SHA required")
    project, raw, policy_path = (Path(value).resolve(strict=True) for value in argv[1:4])
    if raw.name != RAW_NAME or raw.is_symlink() or raw.is_relative_to(project.parent): raise ValueError("fresh external native86 raw root required")
    control = raw / "control"
    if policy_path.parent != control or Path(__file__).resolve().parent != control: raise ValueError("exact raw/control inputs required")
    policy_bytes = policy_path.read_bytes()
    if hashlib.sha256(policy_bytes).hexdigest() != argv[4]: raise ValueError("root-pinned policy changed")
    policy = json.loads(policy_bytes)
    if policy["raw_name"] != RAW_NAME or policy["budgets"] != {"whole_seconds": WHOLE_SECONDS, "entry_seconds": ENTRY_SECONDS,
            "rss_bytes": RSS_BYTES, "stage_bytes": STAGE_BYTES, "total_bytes": TOTAL_BYTES}:
        raise ValueError("exact native86 whole-tree/output budgets required")
    if sys.executable != policy["python"]: raise ValueError("selected physical Python invocation differs")
    controls = policy["controller_files"]
    def control_check():
        if policy_path.is_symlink() or not stat.S_ISREG(policy_path.lstat().st_mode):
            raise ValueError("physical regular policy input required")
        if {p.name for p in control.iterdir()} != {policy_path.name, *controls}: raise ValueError("closed controller membership differs")
        for name, expected in controls.items():
            path = control / name
            if path.name != name or path.is_symlink() or not path.is_file() or pin(path) != {"path": str(path), **expected}:
                raise ValueError("controller physical input differs: " + name)
        if pin(__file__)["sha256"] != policy["entry_sha256"] or hashlib.sha256(policy_path.read_bytes()).hexdigest() != argv[4]:
            raise ValueError("native86 entry/policy bytes differ")
    control_check()
    if shutil.disk_usage(raw).free < policy["disk_floor_bytes"] + TOTAL_BYTES: raise ValueError("native disk floor plus output allowance required")
    if os.environ.get("PROBATA_OUTPUT") != str(raw) or os.environ.get("SWDB_VERIFIER_LOCK") != str(raw / "verifier.lock") or os.environ.get("SWDB_VERIFIER_RSS_CAP_BYTES") != str(RSS_BYTES):
        raise ValueError("actual Linux output/lock/RSS role differs")
    launch = json.loads((raw / "launch.json").read_bytes())
    expected_command = [policy["python"], "-I", "-B", str(Path(__file__).resolve()), str(project), str(raw), str(policy_path), argv[4]]
    if launch.get("command") != expected_command or Path(launch["source"]).resolve() != project.parent or launch.get("source_commit") != policy["source_commit"]:
        raise ValueError("exact native86 Linux launch/source differs")
    if any(launch.get(k) != v for k, v in {"rss_cap_bytes": RSS_BYTES, "workers": 1, "timeout_seconds": WHOLE_SECONDS, "node": policy["node"]}.items()):
        raise ValueError("native86 launch worker/guard/lane differs")
    for name, expected in policy["guard_files"].items():
        if pin(raw / name)["sha256"] != expected or launch.get("reviewed_wrapper_reuse", {}).get(name) != expected:
            raise ValueError("exact Linux execute/watch source differs")
    live = verified_linux_lane(policy["node"])
    marker = hashlib.sha256(json.dumps({"launch": pin(raw / "launch.json"), "live": live}, sort_keys=True).encode()).hexdigest()
    save(raw / "native86-linux-role.json", {"launch": pin(raw / "launch.json"), "live": live, "derived_marker": marker,
                                          "Mac_counted_claim": False, "scope": "actual Linux execute/watch/socket role"})
    cache = raw / "entry-source-cache"
    if cache.exists() or cache.is_symlink(): raise ValueError("absent entry bytecode prefix required")
    sys.pycache_prefix = str(cache)
    os.environ.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPYCACHEPREFIX=str(cache))
    def module(name):
        path = control / name; data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != controls[name]["sha256"]: raise ValueError("helper source changed")
        answer = types.ModuleType("native86_" + name[:-3]);answer.__file__ = str(path)
        exec(compile(data, str(path), "exec"), answer.__dict__);return answer
    closed, roles, observer = (module(name) for name in ("closed_python_surface.py", "python_startup_roles_v2.py", "python_role_observer_v2.py"))
    before = physical_runtime(policy, closed);save(raw / "native86-runtime-before.json", before)
    roles.validate_role_plan_v2(policy["startup_roles"], metadata=policy["python_surface_binding"], source_project=project,
        root_observer_bytes=(control / policy["root_observer_file"]).read_bytes(), closed=closed)
    request = roles.role_request_v2(policy["startup_roles"], role="entry-isolated", environment=os.environ, cache=cache)
    observed = observer.observe_role_v2(request);roles.check_role_observation_v2(request, observed)
    save(raw / "native86-python-entry-role.json", observed)
    compiler = policy["compiler"]
    if len(compiler["command"]) != 1 or not Path(compiler["command"][0]).is_absolute(): raise ValueError("selected absolute compiler wrapper required")
    recheck([compiler["wrapper"], compiler["driver"], compiler["linker"]])
    if any((compiler[name]["path"], compiler[name]["sha256"]) != wanted for name, wanted in
           (("wrapper", CLANG_WRAPPER), ("driver", CLANG_DRIVER))) or compiler.get("version") != "22.1.8":
        raise ValueError("exact selected LLVM22 wrapper/driver bytes required")
    native_paths = {row["path"] for row in policy["native_runtime"]["pins"]} | set(policy["runtime_files"])
    if not {compiler[k]["path"] for k in ("wrapper", "driver", "linker")} <= native_paths:
        raise ValueError("compiler/linker lack admitted physical closure")
    if compiler["command"][0] != compiler["wrapper"]["path"] or not Path(compiler["linker"]["path"]).is_absolute():
        raise ValueError("compiler/linker exact selection differs")
    forbidden = ("CPATH", "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH", "OBJC_INCLUDE_PATH", "INCLUDE", "SDKROOT", "GCC_EXEC_PREFIX",
                 "COMPILER_PATH", "LIBRARY_PATH", "LD_PRELOAD", "LD_AUDIT", "ASAN_SYMBOLIZER_PATH", "UBSAN_OPTIONS", "ASAN_OPTIONS")
    if any(os.environ.get(name) for name in forbidden): raise ValueError("ambient compiler/loader/sanitizer override refused")
    out = raw / "component";out.mkdir();(out / "tmp").mkdir()
    child_cache = out / "source-cache"
    environment = {"PATH": policy["path"], "HOME": policy["home"], "LANG": "C", "LC_ALL": "C", "TMPDIR": str(out / "tmp"),
                   "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPYCACHEPREFIX": str(child_cache),
                   "ASAN_OPTIONS": "detect_leaks=0:halt_on_error=1:abort_on_error=0:symbolize=0:exitcode=86",
                   "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=0", "PROBATA_OUTPUT": str(raw),
                   "SWDB_VERIFIER_LOCK": str(raw / "verifier.lock"), "SWDB_VERIFIER_RSS_CAP_BYTES": str(RSS_BYTES),
                   "SWDB_LINUX_REVIEWED_ADMISSION": marker}
    loader = policy["native_runtime"]["loader_environment"]
    if not isinstance(loader, dict) or set(loader) - {"LD_LIBRARY_PATH"}: raise ValueError("closed loader environment required")
    environment.update(loader)
    source_pins = [pin(control / name) for name in INPUTS]
    save(out / "inputs-before.json", {"source": source_pins, "environment": environment, "compiler": compiler,
        "policy": pin(policy_path), "entry": pin(__file__), "scope": "private86 controls only"})
    commands, groups, observations, error = [], [], [], None
    def bytes_used():
        return sum(p.stat().st_size for p in raw.rglob("*") if p.is_file())
    def file_limit(): resource.setrlimit(resource.RLIMIT_FSIZE, (STAGE_BYTES, STAGE_BYTES))
    def stage(name, command, maximum):
        remaining = min(maximum, deadline - time.monotonic() - 10)
        if remaining <= 0 or bytes_used() > TOTAL_BYTES: raise ValueError("native86 time/output allowance exhausted")
        row = {"name": name, "argv": command, "cwd": str(out), "timeout_seconds": remaining};commands.append(row)
        with (out / (name + ".stdout")).open("xb") as stdout, (out / (name + ".stderr")).open("xb") as stderr:
            process = subprocess.Popen(command, cwd=out, env=environment, stdout=stdout, stderr=stderr,
                                       start_new_session=True, preexec_fn=file_limit)
            expires = time.monotonic() + remaining
            try:
                while process.poll() is None:
                    if time.monotonic() >= expires or bytes_used() > TOTAL_BYTES or stdout.tell() > STAGE_BYTES or stderr.tell() > STAGE_BYTES:
                        raise ValueError("native86 stage time/output cap exceeded")
                    time.sleep(0.05)
            except BaseException:
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                process.wait();raise
            row["returncode"] = process.wait()
        row["stdout"], row["stderr"] = pin(out / (name + ".stdout")), pin(out / (name + ".stderr"))
        if row["returncode"] or bytes_used() > TOTAL_BYTES: raise ValueError("native86 stage failed: " + name)
    try:
        for label, language, frozen_language, standard, suffix in (("c11", "c", "cpp-output", "-std=c11", ".i"),
                ("cpp17", "c++", "c++-cpp-output", "-std=c++17", ".ii")):
            frozen, dependency, obj, binary = (out / (label + s) for s in (suffix, ".d", ".o", ".native"))
            flags = [standard, *SANITIZERS]
            stage(label + "-preprocess", [*compiler["command"], "--no-default-config", "-x", language, *flags, "-E", "-MD", "-MF", str(dependency),
                  "-MT", label, str(control / INPUTS[0]), "-o", str(frozen)], 45)
            deps = [pin(path) for path in make_dependencies(dependency.read_text(), label, out)]
            if not {row["path"] for row in source_pins} <= {row["path"] for row in deps}: raise ValueError("native86 source/header dependency census differs")
            frozen_pin = pin(frozen)
            group = {"language": label, "dependencies": deps, "frozen": frozen_pin,
                     "timing": "first dependency hashes after original preprocessing; rechecked before and after frozen compilation"};groups.append(group)
            recheck(deps + [frozen_pin] + source_pins)
            stage(label + "-compile", [*compiler["command"], "--no-default-config", "-x", frozen_language, *flags, "-c", str(frozen), "-o", str(obj)], 60)
            object_pin = pin(obj);recheck(deps + [frozen_pin])
            stage(label + "-link", [*compiler["command"], "--no-default-config", *SANITIZERS, "-fuse-ld=" + compiler["linker"]["path"],
                  "-Wl,-t", str(obj), "-o", str(binary)], 45)
            used = link_inputs((out / (label + "-link.stdout")).read_text(), out)
            if str(obj) not in used or not set(used) <= native_paths | {str(obj)}: raise ValueError("used linker input lacks prior physical admission")
            group["link_inputs"] = [pin(path) for path in used];group["object"] = object_pin
            binary_pin = pin(binary);recheck(group["link_inputs"] + deps + [frozen_pin, object_pin])
            stage(label + "-run", [str(binary)], 20)
            stdout, stderr = out / (label + "-run.stdout"), out / (label + "-run.stderr")
            if stdout.stat().st_size > 65536 or stderr.stat().st_size or json.loads(stdout.read_text()) != RESULT:
                raise ValueError("native86 exact census or empty sanitizer stderr differs")
            recheck([binary_pin, frozen_pin, object_pin] + deps + group["link_inputs"])
            observations.append({"language": label, "binary": binary_pin, "result": RESULT, "private_native_only": True})
    except Exception as failure:
        error = {"type": type(failure).__name__, "message": str(failure)}
    finally:
        save(out / "commands.json", commands);save(out / "used-inputs.json", groups);save(out / "observations.json", observations)
        after_errors = []
        try:
            physical = physical_runtime(policy, closed);recheck(source_pins);control_check()
            for name, expected in policy["guard_files"].items():
                if pin(raw / name)["sha256"] != expected: raise ValueError("Linux guard source changed")
            for group in groups:
                recheck(group["dependencies"] + [group["frozen"]] + group.get("link_inputs", []))
        except Exception as failure:
            after_errors.append({"type": type(failure).__name__, "message": str(failure)})
            physical = {"error": after_errors}
        save(raw / "native86-runtime-after.json", physical)
        cache_present = any(p.exists() or p.is_symlink() for p in (cache, child_cache))
        accepted = error is None and not after_errors and len(observations) == 2 and len(commands) == 8 and not cache_present and bytes_used() <= TOTAL_BYTES
        save(out / "result.json", {"accepted": accepted, "error": error, "wall_seconds": time.monotonic() - started,
             "after_input_errors": after_errors,
             "controls_by_language": {row["language"]: row["result"] for row in observations}, "bytecode_cache_present": cache_present,
             "header_timing_tcb": "dependencies first hashed after preprocessing; source/runtime known inputs checked before launch and after capture",
             "private_native_controls_only": True, "public_proof": False, "current_0_2": False, "full_ticket28": False})
        save(out / "artifact-manifest.json", [{"relative": str(p.relative_to(out)), **pin(p)} for p in sorted(out.rglob("*"))
             if p.is_file() and p.name not in {"artifact-manifest.json"}])
    return 0 if accepted and bytes_used() <= TOTAL_BYTES else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
