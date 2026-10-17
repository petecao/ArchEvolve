"""2026-10-16 ET. Inert prospective closed-source public profile; root admits execution.

Exact reviewed runtime gates run before any project import or native tool.
The source/slot placeholders are inert until the pure metadata author freezes them.
The public cases own the original source-result obligations and four opt-in controls.
Producer completion is separate from independent cold scientific acceptance.
"""
import contextlib
import hashlib
import json
import os
import re
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time
import types
import xml.etree.ElementTree as ET

SOURCE = "__SOURCE_COMMIT__"
RAW_NAME = "__RAW_NAME__"
NODE = __NODE__
WHOLE_SECONDS = 1200
TEST_SECONDS = 1000
RSS_BYTES = 8589934592
TOTAL_BYTES = 536870912
STAGE_BYTES = 134217728
FINAL_RESERVE_BYTES = 65536
FINAL_RESULT_BYTES = 16384
FINAL_MARGIN_SECONDS = 1.0
CASE_IDS = ("safe", "missing_bundle", "stale_method", "wrong_result", "default_method")
CASE_PREFIX = "test_public_closed_source_proo"
PYTEST_BASE = Path("closed-source-profile/pytest")
SELECTION = "tests/test_vector_reallocation_closed_public_workflow.py::test_public_closed_source_proof_and_exact_opt_in_controls"


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
             "per_file_bytes": STAGE_BYTES}, "closed-source profile/source/budget binding differs")
    need(expected["finalization"] == {"reserve_bytes": FINAL_RESERVE_BYTES,
         "result_byte_cap": FINAL_RESULT_BYTES, "time_margin_seconds": FINAL_MARGIN_SECONDS},
         "closed finalization reserve/size/time policy differs")
    need(expected["source_preparation_complete"] is True, "complete reviewed source packet required")
    need(expected["source_files"]["swdb/verifier_lock.py"] == LOCK_SOURCE_SHA256
         and expected["transient_lock_policy"] == {
             "lock_relative": str(LOCK_RELATIVE), "source_sha256": LOCK_SOURCE_SHA256,
             "active_poll_only": True, "settled_missing_entries_refused": True,
             "queue_ticket_pattern": "[0-9]{20}-[1-9][0-9]*",
             "slots": 1, "nested": False}, "exact source-derived transient lock protocol differs")


def save(path, value):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())




def pytest_alias_policy(raw):
    alias = str(PYTEST_BASE / (CASE_PREFIX + "current"))
    targets = [{"literal_target": str(raw / PYTEST_BASE / (CASE_PREFIX + str(index))),
                "target_relative": str(PYTEST_BASE / (CASE_PREFIX + str(index)))}
               for index in range(len(CASE_IDS))]
    return {alias: {"allowed_targets": targets, "final_target": targets[-1]}}


def pytest_source_check(expected):
    wanted = expected["pytest_alias_policy"]
    derived = [re.sub(r"[\W]", "_", SELECTION.split("::")[-1] + "[" + name + "]")[:30]
               for name in CASE_IDS]
    need(all(name == CASE_PREFIX for name in derived)
         and wanted["case_prefix"] == CASE_PREFIX and wanted["case_ids"] == list(CASE_IDS)
         and wanted["basetemp_relative"] == str(PYTEST_BASE)
         and wanted["aliases"] == pytest_alias_policy(output), "closed five-case pytest alias policy differs")
    source = wanted["source"]
    path = Path(source["path"])
    need(path.resolve(strict=True) == path and path.is_file() and not path.is_symlink(),
         "pinned pytest tmpdir source must be physical regular input")
    raw = path.read_bytes()
    need(len(raw) == source["bytes"] and sha(raw) == source["sha256"], "pinned pytest tmpdir source changed")
    return wanted


LOCK_RELATIVE = Path("closed-source-profile/verifier.lock")
LOCK_SOURCE_SHA256 = "35329946b838d80edd842d235ad477b6727d08eeebd66f28a0adc47ecb8bbeb8"


def transient_lock_missing(raw, path, physical_directories):
    """Only the checked one-slot lock protocol may remove these exact entries."""
    lock = raw / LOCK_RELATIVE
    queue = lock.with_name("verifier.queue")
    profile = lock.parent
    if not (path == lock or path == lock / "owner" or
            (path.parent == queue and re.fullmatch(r"[0-9]{20}-[1-9][0-9]*", path.name))):
        return False
    if path.parent not in physical_directories:
        return False
    # The immutable profile ancestor must still be physical. A removed owner
    # may have a now-absent lock parent that this same walk already saw as a
    # physical directory; no arbitrary parent resolution or links are admitted.
    return (stat.S_ISDIR(profile.lstat().st_mode)
            and profile.resolve(strict=True) == profile)


def raw_extent(raw, *, require_aliases=False, reserve=None, active_poll=False):
    """Walk physical entries without traversing even the five-target permitted alias."""
    need(raw.is_absolute() and raw.resolve(strict=True) == raw and raw.is_dir(),
         "physical raw directory required")
    reserve = FINAL_RESERVE_BYTES if reserve is None else reserve
    allowed, aliases, total, regular_files = pytest_alias_policy(raw), [], 0, 0
    need(not (active_poll and require_aliases), "settled census cannot tolerate active lock races")
    pending, physical_directories, vanished = [raw], {raw}, []
    while pending:
        parent = pending.pop()
        try:
            entries = os.scandir(parent)
        except FileNotFoundError:
            if not active_poll or not transient_lock_missing(raw, parent, physical_directories):
                raise
            vanished.append(str(parent.relative_to(raw)))
            continue
        with entries:
            for item in entries:
                path = Path(item.path)
                try:
                    observed = item.stat(follow_symlinks=False)
                except FileNotFoundError:
                    if not active_poll or not transient_lock_missing(raw, path, physical_directories):
                        raise
                    vanished.append(str(path.relative_to(raw)))
                    continue
                mode = observed.st_mode
                relative = str(path.relative_to(raw))
                if stat.S_ISLNK(mode):
                    need(relative in allowed, "unlisted raw output symlink refused")
                    policy = allowed[relative]
                    literal = os.readlink(path)
                    matches = [item for item in policy["allowed_targets"] if literal == item["literal_target"]]
                    need(len(matches) == 1, "pytest-current link literal differs")
                    wanted = matches[0]
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
                    physical_directories.add(path)
                    pending.append(path)
                else:
                    need(stat.S_ISREG(mode), "raw output special entry refused")
                    need(observed.st_size <= STAGE_BYTES, "raw per-file budget exceeded")
                    total += observed.st_size
                    regular_files += 1
    aliases.sort(key=lambda row: row["relative"])
    if require_aliases:
        lock = raw / LOCK_RELATIVE
        queue = lock.with_name("verifier.queue")
        need(not os.path.lexists(lock), "completed public workflow retains an active verifier lock")
        need(not os.path.lexists(queue) or not list(queue.iterdir()), "completed public workflow retains queued verifier work")
        need({row["relative"] for row in aliases} == set(allowed), "complete exact pytest-current alias set required")
        need({path.name for path in (raw / PYTEST_BASE).iterdir()}
             == {*(CASE_PREFIX + str(index) for index in range(len(CASE_IDS))), CASE_PREFIX + "current"},
             "exact five physical pytest test directories required")
        need(all({key: item[key] for key in ("literal_target", "target_relative")}
                 == allowed[item["relative"]]["final_target"] for item in aliases),
             "completed pytest-current must target the fifth case")
    need(total <= TOTAL_BYTES - reserve, "raw total budget/final metadata reserve exceeded")
    return {"bytes": total, "regular_files": regular_files, "aliases": aliases,
            "transient_lock_disappearances": sorted(vanished)}



def progress_records(base):
    """One physical five-directory census per poll, independent of file order."""
    result = []
    for index in range(len(CASE_IDS)):
        path = base / (CASE_PREFIX + str(index)) / "retained-public-record.json"
        try:
            record = json.loads(path.read_bytes())
        except (OSError, ValueError):
            continue
        result.append((record["id"], record["verdict"]))
    return sorted(result)


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
    with (raw / "closed-result.json").open("xb") as stream:
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
         and len(suites) == 1 and len(cases) == 5, "exact five-test JUnit required")
    need(suites[0].get("tests") == "5"
         and all(suites[0].get(key) == "0" for key in ("errors", "failures", "skipped"))
         and all(next(root.iter(key), None) is None for key in ("error", "failure", "skipped")),
         "closed-source JUnit did not execute every case without skips/errors/failures")
    names = {SELECTION.split("::")[-1]+"["+name+"]" for name in
             ("safe", "missing_bundle", "stale_method", "wrong_result", "default_method")}
    need({case.get("name") for case in cases} == names
         and all(case.get("classname") == "tests.test_vector_reallocation_closed_public_workflow"
                 and case in list(suites[0]) for case in cases), "exact closed-source JUnit identities differ")
    return {"tests": 5, "errors": 0, "failures": 0, "skipped": 0}


def check_records(records):
    need(len(records) == 5 and len({row["id"] for row in records}) == 5, "five retained records required")
    need(all(row["evidence_kind"] == "contract_fixture" and row["job"]["adapter"] == "wp"
             and row["subject"] == {"kind": "library_summary", "id": "contract.fixture_vector_closed_no_growth"}
             and row["settings"]["verifier_launched"] is False
             and not any(report["name"] == "wp_log" for report in row["evidence"]["reports"])
             for row in records), "public fixture identity or native launch boundary differs")
    positive = [row for row in records if row["verdict"] == "proven"]
    negative = [row for row in records if row["verdict"] == "not_proven"]
    need(len(positive) == 1 and len(negative) == 4
         and all(row["failure_class"] == "unsupported_construct" for row in negative), "public opt-in result census differs")
    row = positive[0]
    need(row["settings"]["tool"] == "checked-vector-source-rule"
         and row["settings"]["proof_basis"] == "checked closed source observation rule and exact conditional mathematical evidence"
         and row["settings"]["source_typed_bridge_established"] is False
         and row["settings"]["original_diagnostic"]["normal_verdict"] == "not_proven"
         and row["settings"]["native_projected_diagnostic"]["normal_verdict"] == "not_proven"
         and row["settings"]["current_model_records_created"] == [], "source/native proof basis was relabeled")
    need(len(row["goals"]) == 24 and all(goal["source"] == "source_rule" and goal["status"] == "valid"
             for goal in row["goals"]), "complete source-rule ordinary census differs")
    need(sum(item["targets"] for item in row["settings"]["historical_scientific_components"]) == 82,
         "complete historical scientific target census differs")
    need(any(item.get("invocation") == "checked-source-rule-evaluation"
             and item.get("native_verifier_launched") is False for item in row["proof_setup_check"]["runs"]),
         "current source-rule setup check missing")
    standard = [item for item in row["assumptions"] if item["reference"] == row["pins"]["std_models"]]
    need(any(item["sentence"] == "Allocation succeeds: every malloc (std::vector growth, new[]) returns usable memory, never null."
             for item in standard) and any(item["sentence"].startswith("The pinned standard library ") for item in standard),
         "required original standard-library/allocation assumptions missing")
    return {"records": 5, "source_rule_proven": 1, "unsupported_controls": 4,
            "original_native_results_preserved": True, "independent_cold_acceptance": False}


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
    exec(compile((control / "reviewed_wp_gates.py").read_bytes(), str(control / "reviewed_wp_gates.py"), "exec"), globals())
    native = types.ModuleType("reviewed_mixed_native_gates")
    exec(compile((control / "reviewed_native_gates.py").read_bytes(), str(control / "reviewed_native_gates.py"), "exec"), native.__dict__)
    ambient_check(os.environ, EXPECTED["config"]["path"], project)
    admission = validate_linux_launch(EXPECTED, repo, output, policy_path, argv[4], __file__, os.environ)
    admission["live_lane"] = verified_linux_lane(NODE)
    role_digest = sha(json.dumps(admission, sort_keys=True, separators=(",", ":")).encode())
    os.environ["SWDB_LINUX_REVIEWED_ADMISSION"] = role_digest
    os.environ["SWDB_VERIFIER_RUN_TOKEN"] = "linux-reviewed:" + role_digest
    save(output / "closed-linux-admission.json", admission)
    save(output / "closed-pytest-alias-policy-before.json", pytest_source_check(EXPECTED))
    raw_extent(output)
    os.chdir(project)
    source_check()
    save(output / "closed-source-before.json", consumer_closure(project, repo, EXPECTED))
    closed_v4, _closed = load_controller_module_v4("closed_python_surface.py")
    roles_v4, _roles = load_controller_module_v4("python_startup_roles_v2.py")
    _observer, observer_source_v4 = load_controller_module_v4("python_role_observer_v2.py")
    runtime_surface_check_v4("before")
    save(output / "closed-native-runtime-before.json", native.physical_runtime(EXPECTED, closed_v4))
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
    save(output / "closed-why3-stdlib.json", stdlib_check())
    for name, wanted in EXPECTED["ocaml_packages"].items():
        done = subprocess.run([EXPECTED["tools"]["ocamlfind"]["path"], "query", name],
                              capture_output=True, text=True, timeout=10)
        need(done.returncode == 0 and not done.stderr and Path(done.stdout.strip()).resolve() == Path(wanted),
             "exact OCaml package binding differs")
    os.environ.update(SWDB_CLANG=shlex.join(EXPECTED["linux_clang_components"]["command"]),
        SWDB_FRAMA_C=EXPECTED["tools"]["frama-c"]["path"], SWDB_CBMC="none",
        SWDB_OCAMLFIND=EXPECTED["tools"]["ocamlfind"]["path"], WHY3CONFIG=EXPECTED["config"]["path"],
        SWDB_WHY3_CONFIG=EXPECTED["config"]["path"], SWDB_VERIFIER_RSS_CAP_BYTES=str(RSS_BYTES),
        SWDB_MIXED_PAIR_ACTUAL="0", SWDB_PAIR_ACTUAL="0", SWDB_VECTOR_CLOSED_SOURCE_ACTUAL="1",
        SWDB_DX100_SELECTOR_ACTUAL_LINEUP=json.dumps(EXPECTED["actual_initialized_lineup"], sort_keys=True))
    runtime_surface_check_v4("after-startup")
    sys.path.insert(0, str(project))
    from swdb import c_lowering, stdlib_provenance
    tool = c_lowering.locate()
    need(not tool.missing, "selected compiler unavailable")
    identity = c_lowering.identity()
    runtime = stdlib_provenance.runtime_identity(tool)
    compiler_components(runtime, EXPECTED["linux_clang_components"])
    save(output / "closed-project-runtime.json", {"lowering_identity": identity, "runtime": runtime,
         "scope": "Fresh source/compiler context; historical mathematical method identities remain separate"})
    profile = output / "closed-source-profile"
    profile.mkdir(exist_ok=False)
    environment = roles_v4.child_environment_v2(os.environ, project=project, raw=profile, cache=profile / "source-cache")
    environment.update(PROBATA_PYTHON=sys.executable, TMPDIR=str(profile / "tmp"), XDG_CACHE_HOME=str(profile / "cache"))
    Path(environment["TMPDIR"]).mkdir()
    Path(environment["XDG_CACHE_HOME"]).mkdir()
    need(not os.path.lexists(profile / "pytest"), "fresh absent five-case pytest basetemp required")
    deadline = time.monotonic() + TEST_SECONDS
    observe_startup_role_v4(plan, "pytest-child", environment, profile / "source-cache")
    command = [sys.executable, "-B", "-X", "pycache_prefix=" + str(profile / "source-cache"), "-m", "pytest",
               "-q", "-p", "no:cacheprovider", "--basetemp=" + str(profile / "pytest"),
               "--junitxml=" + str(profile / "junit.xml"), SELECTION]
    save(output / "closed-command.json", {"argv": command, "deadline_monotonic": deadline,
         "actual_flag": environment["SWDB_VECTOR_CLOSED_SOURCE_ACTUAL"], "lineup": EXPECTED["actual_initialized_lineup"]})
    code = None
    transient_lock_races = {}
    try:
        need(not os.path.lexists(profile / "pytest"), "pytest basetemp changed before dispatch")
        with (profile / "pytest.log").open("xb") as log, (profile / "progress-observer.jsonl").open("x") as progress:
            process = subprocess.Popen(command, cwd=project, env=environment, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            seen = None
            try:
                while process.poll() is None:
                    need(time.monotonic() < deadline, "closed-source shared deadline exhausted")
                    extent = raw_extent(output, active_poll=True)
                    for relative in extent["transient_lock_disappearances"]:
                        transient_lock_races[relative] = transient_lock_races.get(relative, 0) + 1
                    need(len(transient_lock_races) <= 64, "too many distinct transient verifier lock entries")
                    state = progress_records(profile / "pytest")
                    if state != seen:
                        progress.write(json.dumps({"records": len(state), "observed": state}, sort_keys=True) + "\n")
                        progress.flush(); os.fsync(progress.fileno()); seen = state
                    time.sleep(0.25)
                code = process.returncode
            finally:
                if process.poll() is None:
                    stop_tree(process)
        need(code == 0, "closed-source public pytest failed")
        census = junit_census(profile / "junit.xml")
        record_paths = sorted((profile / "pytest").rglob("retained-public-record.json"))
        need(len(record_paths) == 5, "five physical retained public record artifacts required")
        records = [json.loads(path.read_bytes()) for path in record_paths]
        import yaml
        for path, record in zip(record_paths, records, strict=True):
            physical = list((path.parent / "records/proofs").glob("*.yaml"))
            need(len(physical) == 1 and yaml.safe_load(physical[0].read_bytes()) == record,
                 "retained public record differs from final original physical proof")
        need(not list(profile.rglob("frama-c.log")), "this source-rule control may not run a new WP solver job")
        result = check_records(records)
        save(output / "closed-record-census.json", {**result, "junit": census,
             "physical_records": [{"path": str(path.relative_to(output)), "sha256": sha(path.read_bytes())} for path in record_paths]})
    finally:
        save(output / "closed-transient-lock-races.json", {"active_poll_only": True,
             "source_sha256": LOCK_SOURCE_SHA256, "disappearances": transient_lock_races,
             "settled_census_is_strict": True})
        source_check()
        save(output / "closed-source-after.json", consumer_closure(project, repo, EXPECTED))
        runtime_surface_check_v4("after")
        save(output / "closed-native-runtime-after.json", native.physical_runtime(EXPECTED, closed_v4))
        need(not os.path.lexists(bootstrap_cache) and not os.path.lexists(profile / "source-cache"),
             "unexpected source bytecode cache created")
        save(output / "closed-pytest-alias-policy-after.json", pytest_source_check(EXPECTED))
        save(output / "closed-final-aliases.json", raw_extent(output, require_aliases=code == 0))
        raw_extent(output, require_aliases=code == 0)
    return {"status": "PRODUCER_WORKFLOW_COMPLETE", "source_commit": SOURCE, "tests": 5, "records": 5,
            "exit_code": code, "independent_cold_acceptance": False,
            "scope": "Original closed-source public fixture workflow only; no source/caller/universal or ticket acceptance"}


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
