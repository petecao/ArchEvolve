"""2026-10-16 ET. Inert prospective mixed-pair public profile; root admits execution.

Exact reviewed runtime gates run before any project import or native tool.
The public test owns all eight original obligations and negative controls.
Producer completion is separate from independent cold scientific acceptance.
"""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time
import types
import xml.etree.ElementTree as ET

SOURCE = "dcdecf317a0e9b34f3ce12d5b914eb823c439fbc"
RAW_NAME = "probata-resume-20261016-dcdecf31-mixed-pair-public-v5"
NODE = 0
WHOLE_SECONDS = 1200
TEST_SECONDS = 900
RSS_BYTES = 8589934592
TOTAL_BYTES = 268435456
STAGE_BYTES = 134217728
FINAL_RESERVE_BYTES = 65536
FINAL_RESULT_BYTES = 16384
FINAL_MARGIN_SECONDS = 1.0
SELECTION = "tests/test_pair_pointer_workflow.py::test_actual_mixed_pair_bodies_callers_and_bounded_cpp_replay"
CASE_PREFIX = "test_actual_mixed_pair_bodies_"
PYTEST_BASE = Path("mixed-pair-profile/pytest")
MEMBERS = tuple("std_pair_int_int_ptr_" + name for name in
                ("ctor_default", "ctor", "copy_ctor", "operator_assign"))


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def policy_gate(expected):
    need(expected["source_commit"] == SOURCE and expected["raw_name"] == RAW_NAME
         and expected["linux_launch_binding"]["node"] == NODE
         and expected["profile_seconds"] == TEST_SECONDS and expected["selection"] == SELECTION
         and expected["guard"] == {"whole_tree_seconds": WHOLE_SECONDS, "external_timeout_seconds": 1320,
             "rss_cap_bytes": RSS_BYTES, "workers": 1, "raw_budget_bytes": TOTAL_BYTES,
             "per_file_bytes": STAGE_BYTES}, "mixed-pair source/profile/budget binding differs")
    need(expected["finalization"]["reserve_bytes"] == FINAL_RESERVE_BYTES
         and expected["finalization"]["result_byte_cap"] == FINAL_RESULT_BYTES
         and expected["finalization"]["time_margin_seconds"] == FINAL_MARGIN_SECONDS,
         "closed finalization reserve/size/time policy differs")
    need(expected["source_admission"]["root_authorized"] is True,
         "published source requires exact admitted root30-control success before tools")


def root_control_gate(expected, control):
    need(control["schema"] == "mixed-pair-root30-admission-1"
         and control["status"] == "ROOT_CONTROLS_PASSED"
         and control.get("actual_success_admitted") is True
         and control["source_commit"] == SOURCE
         and control["raw_root"] == expected["root_control_admission"]["expected_raw_root"],
         "exact root30 actual source/status/raw admission required")
    need(control["tests"] == {"cases": 30, "failures": 0, "errors": 0, "skips": 0, "cache_absent": True}
         and all(type(control["tests"][key]) is int for key in ("cases", "failures", "errors", "skips"))
         and control["tests"]["cache_absent"] is True,
         "root30 controls must actually complete without skips/errors/failures/cache writes")
    need(control["guard"] == {"exit_code": 0, "rss_cap_bytes": RSS_BYTES, "workers": 1, "whole_seconds": WHOLE_SECONDS}
         and all(type(value) is int for value in control["guard"].values())
         and type(control["outer_exit_code"]) is int and control["outer_exit_code"] == 0
         and control["formal_WP_CBMC_disabled"] is True
         and control["actual_flags"] == {"SWDB_PAIR_ACTUAL": "0", "SWDB_MIXED_PAIR_ACTUAL": "0"},
         "root30 actual guard/outer/resource/disabled-formal context differs")
    need(set(control["evidence"]) == {"command", "junit", "result", "guard", "outer", "source_publication"},
         "complete exact root30 compact evidence pin set required")
    for name, row in control["evidence"].items():
        need(set(row) == {"path", "bytes", "sha256"} and isinstance(row["path"], str)
             and Path(row["path"]).is_absolute() and type(row["bytes"]) is int and row["bytes"] > 0
             and isinstance(row["sha256"], str) and len(row["sha256"]) == 64
             and all(char in "0123456789abcdef" for char in row["sha256"]),
             "root30 evidence physical pin is incomplete: " + name)
    return control


def save(path, value):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def pytest_alias_policy(raw):
    target = PYTEST_BASE / (CASE_PREFIX + "0")
    return {str(PYTEST_BASE / (CASE_PREFIX + "current")):
            {"literal_target": str(raw / target), "target_relative": str(target)}}


def pytest_source_check(expected):
    wanted = expected["pytest_alias_policy"]
    need(wanted["case_prefix"] == CASE_PREFIX and wanted["basetemp_relative"] == str(PYTEST_BASE)
         and wanted["aliases"] == pytest_alias_policy(output), "closed pytest alias policy differs")
    source = wanted["source"]
    path = Path(source["path"])
    need(path.resolve(strict=True) == path and path.is_file() and not path.is_symlink(),
         "pinned pytest tmpdir source must be physical regular input")
    raw = path.read_bytes()
    need(len(raw) == source["bytes"] and sha(raw) == source["sha256"], "pinned pytest tmpdir source changed")
    return wanted


def native_c_wrapper_check(expected):
    wanted = expected["mixed_native_c_wrapper"]
    name = expected["linux_clang_components"]["command"][0].replace("clang++", "clang")
    need(wanted["admitted"] is True and wanted["path"] == name,
         "CBMC C-side sibling wrapper needs a fresh exact physical pin")
    path = Path(name)
    need(path.is_absolute() and path.resolve(strict=True) == path and path.is_file()
         and not path.is_symlink(), "CBMC C-side wrapper must be an exact physical regular input")
    raw = path.read_bytes()
    need(len(raw) == wanted["bytes"] and sha(raw) == wanted["sha256"]
         and stat.S_IMODE(path.stat().st_mode) == wanted["mode"], "CBMC C-side wrapper bytes/mode differ")
    return wanted


def raw_extent(raw, *, require_aliases=False, reserve=None):
    """Walk physical entries without traversing even the one permitted alias."""
    need(raw.is_absolute() and raw.resolve(strict=True) == raw and raw.is_dir(),
         "physical raw directory required")
    reserve = FINAL_RESERVE_BYTES if reserve is None else reserve
    allowed, aliases, total, regular_files = pytest_alias_policy(raw), [], 0, 0
    pending = [raw]
    while pending:
        parent = pending.pop()
        with os.scandir(parent) as entries:
            for item in entries:
                path = Path(item.path)
                observed = item.stat(follow_symlinks=False)
                mode = observed.st_mode
                relative = str(path.relative_to(raw))
                if stat.S_ISLNK(mode):
                    need(relative in allowed, "unlisted raw output symlink refused")
                    wanted = allowed[relative]
                    literal = os.readlink(path)
                    need(literal == wanted["literal_target"], "pytest-current link literal differs")
                    target = raw / wanted["target_relative"]
                    # No resolution of arbitrary link text or recursive traversal
                    # through aliases. Every target component must be physical.
                    part = raw
                    for name in target.relative_to(raw).parts:
                        part = part / name
                        need(stat.S_ISDIR(part.lstat().st_mode), "pytest-current target is not physical directory")
                    need(target.resolve(strict=True) == target and target.parent == raw / PYTEST_BASE,
                         "pytest-current target escapes sole expected test directory")
                    aliases.append({"relative": relative, "literal_target": literal,
                                    "target_relative": wanted["target_relative"]})
                    total += observed.st_size
                elif stat.S_ISDIR(mode):
                    pending.append(path)
                else:
                    need(stat.S_ISREG(mode), "raw output special entry refused")
                    need(observed.st_size <= STAGE_BYTES, "raw per-file budget exceeded")
                    total += observed.st_size
                    regular_files += 1
    aliases.sort(key=lambda row: row["relative"])
    if require_aliases:
        need({row["relative"] for row in aliases} == set(allowed), "complete exact pytest-current alias set required")
        need({path.name for path in (raw / PYTEST_BASE).iterdir()}
             == {CASE_PREFIX + "0", CASE_PREFIX + "current"}, "sole expected pytest test directory required")
    need(total <= TOTAL_BYTES - reserve, "raw total budget/final metadata reserve exceeded")
    return {"bytes": total, "regular_files": regular_files, "aliases": aliases}


def final_payload(result, extent, elapsed):
    result = dict(result)
    if elapsed >= WHOLE_SECONDS - FINAL_MARGIN_SECONDS:
        result.update(status="REFUSED_OR_FAILED", error="FinalizationDeadline",
                      reason="insufficient whole-entry time for bounded final metadata")
    result["finalization"] = {"before": extent, "elapsed_seconds_before": round(elapsed, 6),
        "whole_seconds": WHOLE_SECONDS, "margin_seconds": FINAL_MARGIN_SECONDS,
        "reserve_bytes": FINAL_RESERVE_BYTES, "result_byte_cap": FINAL_RESULT_BYTES,
        "result_bytes": 0, "projected_total_bytes": extent["bytes"],
        "controller_exit_zero_requires_post_fsync_extent_and_time_checks": True,
        "remaining_reserve_covers_bounded_stdout_and_root_guard_metadata": True}
    for _ in range(8):
        payload = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        if (result["finalization"]["result_bytes"] == len(payload)
                and result["finalization"]["projected_total_bytes"] == extent["bytes"] + len(payload)):
            break
        result["finalization"]["result_bytes"] = len(payload)
        result["finalization"]["projected_total_bytes"] = extent["bytes"] + len(payload)
    else:
        raise ValueError("final metadata size did not stabilize")
    need(len(payload) <= FINAL_RESULT_BYTES <= FINAL_RESERVE_BYTES
         and extent["bytes"] + len(payload) <= TOTAL_BYTES, "projected final metadata exceeds reserved raw budget")
    return result, payload


def finalize_result(raw, result, started, *, clock=time.monotonic):
    complete = result.get("status") == "PRODUCER_WORKFLOW_COMPLETE"
    before = raw_extent(raw, require_aliases=complete)
    result, payload = final_payload(result, before, clock() - started)
    with (raw / "mixed-result.json").open("xb") as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    after = raw_extent(raw, require_aliases=complete, reserve=0)
    need(after["bytes"] == before["bytes"] + len(payload)
         and after["regular_files"] == before["regular_files"] + 1
         and after["aliases"] == before["aliases"], "raw changed during bounded finalization")
    need(clock() - started < WHOLE_SECONDS, "whole-entry deadline exceeded after final fsync; controller exit is failure")
    return result, int(result.get("status") != "PRODUCER_WORKFLOW_COMPLETE")


def junit_census(path):
    root = ET.parse(path).getroot()
    suites, cases = list(root.iter("testsuite")), list(root.iter("testcase"))
    need(root.tag == "testsuites" and len(list(root.iter("testsuites"))) == 1
         and len(suites) == 1 and len(cases) == 1, "exact one-test JUnit required")
    need(suites[0].get("tests") == "1"
         and all(suites[0].get(key) == "0" for key in ("errors", "failures", "skipped"))
         and all(next(root.iter(key), None) is None for key in ("error", "failure", "skipped")),
         "mixed-pair JUnit did not execute exactly once without skips/errors/failures")
    need(cases[0].get("name") == SELECTION.split("::")[-1]
         and cases[0].get("classname") == "tests.test_pair_pointer_workflow"
         and cases[0] in list(suites[0]), "mixed-pair exact JUnit identity differs")
    return {"tests": 1, "errors": 0, "failures": 0, "skipped": 0}


def check_eight_records(records, model_hashes):
    need(isinstance(records, list) and len(records) == 8
         and len({row["id"] for row in records}) == 8, "exact eight distinct records required")
    for row in records:
        need(row["evidence_kind"] == "contract_fixture"
             and row["settings"]["rss_cap_bytes"] == RSS_BYTES
             and row["pins"]["method_version"]["id"] == "method.pair-workflow-fixture"
             and "skip_reason" not in row,
             "record fixture scope/RSS differs")
    need([row["job"]["adapter"] for row in records] == ["wp"] * 6 + ["cbmc"] * 2,
         "original four-model/two-WP/two-CBMC adapter order differs")
    models = dict(zip(MEMBERS, records[:4]))
    for name, row in models.items():
        need(row["subject"] == {"kind": "c_model", "id": name}
             and row["verdict"] == "proven" and row.get("unproven_properties", []) == [],
             "original mixed-pair model was not completely proven")
        need(row["pins"]["code"]["sha256"] == model_hashes[name], "original model code pin differs")
    safe, wrong, cbmc_safe, cbmc_wrong = records[4:]
    need([row["subject"] for row in records[4:]] == [
        {"kind": "library_summary", "id": name} for name in
        ("contract.fixture_pair_pointer_values", "contract.fixture_pair_pointer_wrong_identity") * 2],
        "original safe/wrong contract identity differs")
    for row in records[:6]:
        need(row["goals"] and any(not goal.get("smoke") for goal in row["goals"])
             and any(goal.get("smoke") for goal in row["goals"]),
             "complete ordinary and smoke WP observation required")
        if row is not wrong:
            need(all(goal["status"] == "valid" for goal in row["goals"]),
                 "positive ordinary/smoke WP goal was not valid")
    need(safe["verdict"] == "proven", "original WP caller not proven")
    pins = {row["id"]: row for row in safe["pins"]["models"]}
    need(len(safe["pins"]["models"]) == len(MEMBERS) and set(pins) == set(MEMBERS),
         "caller model dependency set differs")
    for name, row in models.items():
        need(pins[name]["proof_record"] == row["id"]
             and pins[name]["sha256"] == model_hashes[name], "caller uses another model proof/code")
    need(wrong["verdict"] == "not_proven" and wrong["failure_class"] in ("unknown", "timeout")
         and any(not goal.get("smoke") and goal["status"] != "valid" for goal in wrong["goals"])
         and all(goal["status"] == "valid" for goal in wrong["goals"] if goal.get("smoke")),
         "original wrong-identity WP duties or smoke health differ")
    need(cbmc_safe["verdict"] == "proven"
         and cbmc_safe["settings"]["agreement"]["verdict"] == "agree", "CBMC safe C/C++ agreement differs")
    need(cbmc_wrong["verdict"] == "refuted"
         and cbmc_wrong["counterexample"]["replay"]["replayed"] is True
         and cbmc_wrong["settings"]["forms"]["cxx"] == "refuted (counterexample replayed)",
         "original C++ wrong-identity counterexample was not replayed")
    return {"records": 8, "models": 4, "WP_callers": 2, "CBMC_callers": 2,
            "verdicts": [row["verdict"] for row in records], "independent_cold_acceptance": False}


def stop_tree(process):
    import psutil
    try:
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
    except psutil.NoSuchProcess:
        children = []
    for child in reversed(children):
        with contextlib.suppress(psutil.NoSuchProcess):
            child.terminate()
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    _gone, alive = psutil.wait_procs(children, timeout=10)
    for child in alive:
        with contextlib.suppress(psutil.NoSuchProcess):
            child.kill()
    with contextlib.suppress(subprocess.TimeoutExpired):
        process.wait(timeout=10)
    if process.poll() is None:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)


def main(argv):
    global EXPECTED, project, output, repo, policy_path, bootstrap_cache
    global closed_v4, roles_v4, observer_source_v4
    need(len(argv) == 5 and __debug__ and not sys.flags.optimize
         and sys.flags.isolated and sys.dont_write_bytecode, "isolated nonoptimized -I -B entry required")
    project, output, policy_path = [Path(value) for value in argv[1:4]]
    need(all(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink()
             for path in (project, output, policy_path)), "canonical physical source/raw/policy required")
    repo = project.parent
    need(output.name == RAW_NAME and not output.is_relative_to(repo)
         and policy_path.parent == output / "control" and Path(__file__).parent == output / "control",
         "fresh exact external raw/control namespace required")
    data = policy_path.read_bytes()
    need(sha(data) == argv[4], "exact root-pinned policy bytes changed")
    EXPECTED = json.loads(data)
    policy_gate(EXPECTED)
    need(sys.executable == EXPECTED["linux_launch_binding"]["python"], "exact selected Python invocation required")
    bootstrap_cache = output / "bootstrap-source-cache"
    need(not os.path.lexists(bootstrap_cache), "absent fresh entry cache required")
    sys.pycache_prefix = str(bootstrap_cache)
    os.environ.update(PYTHONPYCACHEPREFIX=str(bootstrap_cache), PYTHONDONTWRITEBYTECODE="1",
                      PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    control = output / "control"
    names = {Path(__file__).name, policy_path.name, *EXPECTED["controller_files"]}
    need({path.name for path in control.iterdir()} == names, "exact staged control membership differs")
    for name, wanted in EXPECTED["controller_files"].items():
        path = control / name
        need(path.resolve(strict=True) == path and path.is_file() and not path.is_symlink(),
             "regular closed control input required")
        raw = path.read_bytes()
        need(len(raw) == wanted["bytes"] and sha(raw) == wanted["sha256"], "closed control pin differs")
    name = EXPECTED["root_control_admission"]["file"]
    need(name == "root30-control-admission.json" and name in EXPECTED["controller_files"],
         "exact closed root30 receipt basename required")
    save(output / "mixed-root30-admission.json", root_control_gate(EXPECTED, json.loads((control / name).read_bytes())))
    exec(compile((control / "reviewed_wp_gates.py").read_bytes(), str(control / "reviewed_wp_gates.py"), "exec"), globals())
    native = types.ModuleType("reviewed_mixed_native_gates")
    exec(compile((control / "reviewed_native_gates.py").read_bytes(), str(control / "reviewed_native_gates.py"), "exec"), native.__dict__)
    ambient_check(os.environ, EXPECTED["config"]["path"], project)
    admission = validate_linux_launch(EXPECTED, repo, output, policy_path, argv[4], __file__, os.environ)
    admission["live_lane"] = verified_linux_lane(NODE)
    role_digest = sha(json.dumps(admission, sort_keys=True, separators=(",", ":")).encode())
    os.environ["SWDB_LINUX_REVIEWED_ADMISSION"] = role_digest
    os.environ["SWDB_VERIFIER_RUN_TOKEN"] = "linux-reviewed:" + role_digest
    save(output / "mixed-linux-admission.json", admission)
    os.chdir(project)
    source_check()
    save(output / "mixed-source-before.json", consumer_closure(project, repo, EXPECTED))
    closed_v4, _closed = load_controller_module_v4("closed_python_surface.py")
    roles_v4, _roles = load_controller_module_v4("python_startup_roles_v2.py")
    _observer, observer_source_v4 = load_controller_module_v4("python_role_observer_v2.py")
    runtime_surface_check_v4("before")
    save(output / "mixed-native-runtime-before.json", native.physical_runtime(EXPECTED, closed_v4))
    save(output / "mixed-native-C-wrapper-before.json", native_c_wrapper_check(EXPECTED))
    save(output / "mixed-pytest-alias-policy-before.json", pytest_source_check(EXPECTED))
    plan = EXPECTED["startup_roles"]
    roles_v4.validate_role_plan_v2(plan, metadata=EXPECTED["python_surface_binding"], source_project=project,
        root_observer_bytes=controller_root_observer_v4(), closed=closed_v4)
    observe_startup_role_v4(plan, "entry-isolated", dict(os.environ), bootstrap_cache)
    need(not os.environ.get("LD_PRELOAD"), "loader injection refused")
    os.environ.pop("LIBRARY_PATH", None)
    os.environ["LD_LIBRARY_PATH"] = EXPECTED["native_runtime"]["loader_environment"]["LD_LIBRARY_PATH"]
    normalize_compiler_selector(os.environ, EXPECTED["linux_clang_components"])
    compiler_preflight(os.environ, EXPECTED["linux_clang_components"])
    for name, wanted in EXPECTED["tools"].items():
        actual = shutil.which(name)
        need(actual is not None and Path(actual).resolve() == Path(wanted["path"]).resolve()
             and pin(actual)["sha256"] == wanted["sha256"], "selected tool path/bytes differ: " + name)
    for path, digest in EXPECTED["wp_artifacts"].items():
        need(pin(path)["sha256"] == digest, "WP physical artifact differs")
    need(pin(EXPECTED["config"]["path"])["sha256"] == EXPECTED["config"]["sha256"], "Why3 config differs")
    save(output / "mixed-why3-stdlib.json", stdlib_check())
    for name, wanted in EXPECTED["ocaml_packages"].items():
        done = subprocess.run([EXPECTED["tools"]["ocamlfind"]["path"], "query", name],
                              capture_output=True, text=True, timeout=10)
        need(done.returncode == 0 and not done.stderr and Path(done.stdout.strip()).resolve() == Path(wanted),
             "exact OCaml package binding differs")
    os.environ.update(SWDB_CLANG=shlex.join(EXPECTED["linux_clang_components"]["command"]),
        SWDB_FRAMA_C=EXPECTED["tools"]["frama-c"]["path"], SWDB_CBMC=EXPECTED["tools"]["cbmc"]["path"],
        SWDB_OCAMLFIND=EXPECTED["tools"]["ocamlfind"]["path"], WHY3CONFIG=EXPECTED["config"]["path"],
        SWDB_WHY3_CONFIG=EXPECTED["config"]["path"], SWDB_VERIFIER_RSS_CAP_BYTES=str(RSS_BYTES),
        SWDB_MIXED_PAIR_ACTUAL="1", SWDB_PAIR_ACTUAL="0",
        SWDB_DX100_SELECTOR_ACTUAL_LINEUP=json.dumps(EXPECTED["actual_initialized_lineup"], sort_keys=True))
    release, _raw = load_controller_module_v4("cbmc_release_gate.py")
    got = subprocess.run([EXPECTED["tools"]["cbmc"]["path"], "--version"], capture_output=True, text=True, timeout=10)
    need(got.returncode == 0 and {"stdout": got.stdout, "stderr": got.stderr} == EXPECTED["cbmc_version_output"],
         "exact observed CBMC version output differs")
    save(output / "mixed-cbmc-release.json",
         release.check_cbmc_version(EXPECTED, got.returncode, got.stdout, got.stderr))
    runtime_surface_check_v4("after-startup")
    sys.path.insert(0, str(project))
    from swdb import bounded_initialization, cbmc_translator, c_lowering, proof_setup, std_models, stdlib_provenance, wp_pointer_bounds
    tool = c_lowering.locate()
    need(not tool.missing, "selected compiler unavailable")
    identity = c_lowering.identity()
    runtime = stdlib_provenance.runtime_identity(tool)
    compiler_components(runtime, EXPECTED["linux_clang_components"])
    checker_identities = {"bounded_initialization": bounded_initialization.identity(),
        "cbmc_translator": cbmc_translator.identity(), "wp_pointer_bounds": wp_pointer_bounds.identity(),
        "std_models": std_models.identity(), "proof_setup": proof_setup.identity()}
    need(checker_identities == EXPECTED["source_checker_identities"]
         and identity["naming_rules"] == EXPECTED["naming"], "fresh source/compiler/checker identity differs")
    model_hashes = {name: sha(c_lowering.model_text(name).encode()) for name in MEMBERS}
    save(output / "mixed-project-runtime.json", {"lowering_identity": identity, "runtime": runtime,
         "model_hashes": model_hashes, "source_checker_identities": checker_identities,
         "scope": "Fresh source and admitted runtime composite; old composite not promoted. Independent record/cold reconciliation required"})
    profile = output / "mixed-pair-profile"
    profile.mkdir(exist_ok=False)
    environment = roles_v4.child_environment_v2(os.environ, project=project, raw=profile, cache=profile / "source-cache")
    environment.update(PROBATA_PYTHON=sys.executable, TMPDIR=str(profile / "tmp"), XDG_CACHE_HOME=str(profile / "cache"))
    Path(environment["TMPDIR"]).mkdir()
    Path(environment["XDG_CACHE_HOME"]).mkdir()
    need(not os.path.lexists(profile / "pytest"), "fresh absent sole pytest basetemp required")
    deadline = time.monotonic() + TEST_SECONDS
    environment["SWDB_PAIR_DEADLINE_MONOTONIC"] = repr(deadline)
    observe_startup_role_v4(plan, "pytest-child", environment, profile / "source-cache")
    command = [sys.executable, "-B", "-X", "pycache_prefix=" + str(profile / "source-cache"), "-m", "pytest",
               "-q", "-p", "no:cacheprovider", "--maxfail=1", "--basetemp=" + str(profile / "pytest"),
               "--junitxml=" + str(profile / "junit.xml"), SELECTION]
    save(output / "mixed-command.json", {"argv": command, "deadline_monotonic": deadline,
         "actual_flag": environment["SWDB_MIXED_PAIR_ACTUAL"], "lineup": EXPECTED["actual_initialized_lineup"]})
    code = None
    try:
        need(not os.path.lexists(profile / "pytest"), "pytest basetemp changed before dispatch")
        with (profile / "pytest.log").open("xb") as log, (profile / "progress-observer.jsonl").open("x") as progress:
            process = subprocess.Popen(command, cwd=project, env=environment, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            seen = None
            try:
                while process.poll() is None:
                    need(time.monotonic() < deadline, "mixed-pair shared deadline exhausted")
                    raw_extent(output)
                    for path in (profile / "pytest").rglob("actual-mixed-pair-progress.json"):
                        try:
                            rows = json.loads(path.read_bytes())
                        except (OSError, ValueError):
                            continue
                        state = [(row["id"], row["verdict"]) for row in rows]
                        if state != seen:
                            progress.write(json.dumps({"records": len(rows), "observed": state}, sort_keys=True) + "\n")
                            progress.flush(); os.fsync(progress.fileno()); seen = state
                    time.sleep(0.25)
                code = process.returncode
            finally:
                if process.poll() is None:
                    stop_tree(process)
        need(code == 0, "mixed-pair actual pytest failed")
        census = junit_census(profile / "junit.xml")
        progress_paths = list((profile / "pytest").rglob("actual-mixed-pair-progress.json"))
        need(len(progress_paths) == 1, "one actual eight-record progress artifact required")
        progress_records = json.loads(progress_paths[0].read_bytes())
        import yaml
        paths = sorted((progress_paths[0].parent / "records/proofs").glob("*.yaml"))
        records = [yaml.safe_load(path.read_bytes()) for path in paths]
        need(len(records) == 8 and {row["id"] for row in records} == {row["id"] for row in progress_records},
             "physical proof record membership differs")
        by_id = {row["id"]: row for row in records}
        need(all(by_id[row["id"]] == row for row in progress_records), "retained progress/physical record bytes differ")
        result = check_eight_records(progress_records, model_hashes)
        save(output / "mixed-record-census.json", {**result, "junit": census,
             "physical_records": [{"path": str(path.relative_to(output)), "sha256": sha(path.read_bytes())} for path in paths]})
    finally:
        source_check()
        save(output / "mixed-source-after.json", consumer_closure(project, repo, EXPECTED))
        runtime_surface_check_v4("after")
        save(output / "mixed-native-runtime-after.json", native.physical_runtime(EXPECTED, closed_v4))
        save(output / "mixed-native-C-wrapper-after.json", native_c_wrapper_check(EXPECTED))
        save(output / "mixed-pytest-alias-policy-after.json", pytest_source_check(EXPECTED))
        need(not os.path.lexists(bootstrap_cache) and not os.path.lexists(profile / "source-cache"),
             "unexpected source bytecode cache created")
        save(output / "mixed-final-aliases.json", raw_extent(output, require_aliases=code == 0))
        raw_extent(output, require_aliases=code == 0)
    return {"status": "PRODUCER_WORKFLOW_COMPLETE", "source_commit": SOURCE, "tests": 1, "records": 8,
            "exit_code": code, "independent_cold_acceptance": False,
            "scope": "Original mixed-pair public fixture workflow only; no source/caller/universal or ticket acceptance"}


if __name__ == "__main__":
    started = time.monotonic()
    try:
        result = main(sys.argv)
    except (Exception, SystemExit) as error:
        result = {"status": "REFUSED_OR_FAILED", "error": type(error).__name__, "reason": str(error)[:4096],
                  "source_commit": SOURCE, "independent_cold_acceptance": False}
    try:
        need(len(sys.argv) >= 3 and Path(sys.argv[2]).is_dir(), "existing raw namespace required for finalization")
        result, status = finalize_result(Path(sys.argv[2]), result, started)
    except (Exception, SystemExit) as error:
        print(json.dumps({"status": "FINALIZATION_REFUSED", "error": type(error).__name__,
                          "reason": str(error)[:4096], "independent_cold_acceptance": False}, sort_keys=True))
        raise SystemExit(1)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(status)
