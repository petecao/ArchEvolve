"""Exact future parent-owned ticket14 export invocation; preparation NOT RUN.

Infrastructure preregistration only. Original503f/928/science remain unchanged.
No generic dispatcher, source copy, socket wrapper, reader, retry or admission.
Missing actual completion/correction/parent pins refuse before child launch.
All diagnostics stay in fresh private original remote streams.
"""
import argparse
import datetime
import hashlib
import json
import os
import platform
import pwd
import re
import socket
import stat
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
UID = 114316761
R14 = "c4ab2fdbb0b0c57ee9f515522835897f24466d6b"
C = "f893fed400347ed23d92e917d8bde21b75e5375d"
F6 = "f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3"
E79 = "e79e4b2e295f07967a1f4f67e7501c35d9d402101330ac9347f98cfb282bf63a"
SOURCE = Path("/data1/yanruj/ArchEvolve-lanl-generality-final-20261007-a1")
RAW = Path("/data/yanruj/EvolveSWDB_runs/lanl-generality-final-20261007-a1")
LEASES = Path("/data1/yanruj/lact-host-lease")
HELPER = Path("/data1/yanruj/lanl14_final_reports_catalog_caps_a5.py")
TAG = "final-20261007-a1"
JOB = "swdb-lanl14-reports-" + TAG
MAX_OTHER = 100 * 1024 * 1024
MAX_REPORT = 1024 * 1024 * 1024
MAX_JSON = 8 * 1024 * 1024
MAX_PASS = MAX_REPORT + 20 * MAX_OTHER
MAX_READ = 2 * MAX_PASS + 128 * 1024 * 1024
MAX_JOURNAL = 1024 * 1024
MAX_ENTRIES = 16384
NATIVE = {
    "/usr/bin/python3.12": (8020928, "e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f"),
    "/usr/bin/git": (4019024, "06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb"),
}
ORDER = [("bfs", "dx100"), ("bfs", "cpu"), ("bc", "cpu"),
         ("pagerank", "cpu"), ("pagerank", "dx100"), ("pagerank", "maple"),
         ("bfs", "maple"), ("bc", "maple"), ("bc", "dx100")]
STABLE = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_uid", "st_gid",
          "st_size", "st_mtime_ns", "st_ctime_ns")
PRIMARY = Path("/data1/yanruj/ArchEvolve")
C_ROOT = Path("/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1")
C_PROJECT = C_ROOT / "swdb-project"
ARCHIVE = PRIMARY / "swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence"
SUP = ARCHIVE / "14-export-reader-lifecycle-supervisor-controls-20261007-a1/lanl14_export_reader_administrative_supervisor_20261007_a1_r1.py"
EXPORTER = ARCHIVE / "14-lossless-report-export-controls-20261007-a1/lanl14_final_export_lossless_gzip_20261007_a1.py"
CLEANUP = Path("/data1/yanruj/lanl17-control-20261006.py")
COUNT = Path("/data/yanruj/EvolveSWDB_runs/lanl-generality-counts-20261006-a1/controls/pr-cpu/dispatcher.py")
PROCESSES = C_PROJECT / "swdb/processes.py"
EXPORT_W = Path("/data1/yanruj/ArchEvolve-lanl-generality-final-export-20261007-a1")
BRANCH = "codex/lanl-generality-estimate-evidence-20261007-a1"
ADMIN = Path("/data/yanruj/EvolveSWDB_runs/lanl14-export-reader-administration-20261007-a1")
CONTROL = ADMIN / "lanl14-export-reader-control-export-a1"
PY = Path("/usr/bin/python3.12")
GNU = Path("/usr/bin/timeout")
MEMACC = Path("/data1/yanruj/Memacc-repro-20260925")
WRAPPER_REL = "AgenticRefiner/scripts/host/socket_lane.sh"
CODE = {
    str(SUP): (14547, "503fc5defcf96a5177599185a9895c00ae64b3e1b0058128b9e283ef3bd39f3f"),
    str(EXPORTER): (22967, "928af82facd9f36dfdbca6595d2c2e9d1091dd0064c9fe53fc41c163879e026e"),
    str(CLEANUP): (38190, "31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec"),
    str(COUNT): (19622, "b797a19f0d80a1a91b852a360c19e59beba4fa082ce88c38cbec029670e7deda"),
    str(HELPER): (23351, E79),
    str(PROCESSES): (912, "bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289"),
    str(SOURCE / "swdb-project/scripts/generality_report.py"): (None, "26f6d803d17381a70241e77bed5a28a3340f03549135100e475f550c4e252303"),
}
CORRECTION_SHA = "ee12a535ea2c3e6976c920f483c72e8367cd36ec311bf26585137023a2d29ec7"
# The exact correction SHA is inserted by the source-generation step, never a runtime default.
ENV_OVERRIDES = {
    "PATH": "/usr/bin:/bin", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONPATH": str(SOURCE / "swdb-project"), "OMP_NUM_THREADS": "1",
    "OMP_THREAD_LIMIT": "1", "OMP_DYNAMIC": "FALSE", "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1",
}
STARTUP = ("BASH_ENV", "ENV", "PYTHONHOME", "LD_PRELOAD", "LD_LIBRARY_PATH",
           "SOCKET_LANE_REEXEC", "SOCKET_LANE_NODE_DIR", "LACT_LEASE_ROOT",
           "LACT_LEASE_NAME", "LACT_NUMACTL", "LOCKDIR")
MAX_RETURN = 16384
INVOCATION_WAIT_S = 18300


class Refusal(RuntimeError):
    pass

def require(value, reason):
    if not value:
        raise Refusal(reason)

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha_syntax(value):
    require(type(value) is str and re.fullmatch(r"[a-f0-9]{64}", value), "exact SHA-256 required")
    return value

def stamp(s):
    return {name: getattr(s, name) for name in STABLE}

def checked(path, directory=False, owner=UID):
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts and len(str(path)) <= 4096,
            "canonical absolute path required")
    for part in (path, *path.parents):
        require(not part.is_symlink(), "symlink component refused")
    require(path.resolve(strict=True) == path, "path resolution differs")
    s = path.lstat()
    require(s.st_uid == owner and (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode)),
            "owned path type differs")
    if not directory:
        require(s.st_nlink == 1, "single-link original required")
    return path

def object_pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, "duplicate JSON key refused")
        result[key] = value
    return result

def constant_refused(value):
    raise Refusal("nonfinite JSON refused")

def true_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()

def original_true(value):
    require(type(value) is dict and type(value.get("identity_sha256")) is str,
            "original sealed metadata required")
    if "canonical_ensure_ascii" in value:
        require(value["canonical_ensure_ascii"] is True, "original policy differs")
    require(value["identity_sha256"] == true_digest({k: v for k, v in value.items() if k != "identity_sha256"}),
            "original defaultTrue seal differs")
    return value

class Budget:
    def __init__(self, seconds):
        require(type(seconds) is int and 60 <= seconds <= 3600, "explicit 60..3600 metadata seconds required")
        self.deadline = time.monotonic() + seconds
        self.bytes_read = 0

    def check(self):
        require(time.monotonic() < self.deadline, "cumulative metadata deadline exceeded")

    def consume(self, count):
        self.check()
        self.bytes_read += count
        require(self.bytes_read <= MAX_READ, "cumulative streamed byte bound exceeded")

def fd_hash(fd, path, maximum, budget, expected=None, retain=False):
    budget.check()
    before = os.fstat(fd)
    require(stamp(before) == stamp(checked(path).lstat()), "FD/path identity differs")
    require(0 < before.st_size <= maximum, "file size bound exceeded")
    os.lseek(fd, 0, os.SEEK_SET)
    total, hasher, blocks = 0, hashlib.sha256(), []
    while True:
        budget.check()
        block = os.read(fd, min(1024 * 1024, maximum - total + 1))
        if not block:
            break
        total += len(block)
        require(total <= maximum, "returned bytes exceed bound")
        budget.consume(len(block))
        hasher.update(block)
        if retain:
            blocks.append(block)
    require(total == before.st_size and stamp(os.fstat(fd)) == stamp(before) == stamp(checked(path).lstat()),
            "original changed during streaming")
    pin = {"path": str(path), "bytes": total, "sha256": hasher.hexdigest(), "stat": stamp(before)}
    if expected is not None:
        require(pin["sha256"] == expected, "original returned-byte SHA differs")
    return pin, b"".join(blocks) if retain else None

def read_file(path, maximum, budget, expected=None, retain=False, owner=UID):
    path = checked(path, owner=owner)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        # fd_hash's checked path is deliberately account-owned for metadata.
        if owner != UID:
            before = os.fstat(fd)
            require(stamp(before) == stamp(path.lstat()) and 0 < before.st_size <= maximum,
                    "native opened identity differs")
            raw = b""
            while len(raw) <= maximum:
                budget.check()
                block = os.read(fd, min(1024 * 1024, maximum - len(raw) + 1))
                if not block:
                    break
                budget.consume(len(block)); raw += block
            require(len(raw) == before.st_size and stamp(os.fstat(fd)) == stamp(before) == stamp(path.lstat()),
                    "native returned bytes changed")
            require(hashlib.sha256(raw).hexdigest() == expected, "native byte pin differs")
            return {"path": str(path), "bytes": len(raw), "sha256": expected, "stat": stamp(before)}, raw
        return fd_hash(fd, path, maximum, budget, expected, retain)
    finally:
        os.close(fd)

def read_json(path, budget, expected=None, sealed=False):
    pin, raw = read_file(path, MAX_JSON, budget, expected, True)
    value = json.loads(raw, object_pairs_hook=object_pairs, parse_constant=constant_refused)
    if sealed:
        original_true(value)
    return value, pin

def git(*argv, budget):
    budget.check()
    env = {**os.environ, "PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0",
           "GIT_TERMINAL_PROMPT": "0"}
    child = subprocess.run(["/usr/bin/git", "-c", "core.fsmonitor=false", "-C", str(SOURCE), *argv],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=min(25, budget.deadline - time.monotonic()),
                           env=env)
    require(child.returncode == 0 and len(child.stdout) <= MAX_JSON, "fixed read-only Git failed; prose omitted")
    return child.stdout

def source_identity(budget):
    checked(SOURCE, True)
    require(git("rev-parse", "HEAD", budget=budget).decode().strip() == R14, "original R14 HEAD differs")
    require(not git("status", "--porcelain", budget=budget), "original R14 is not clean")
    require(git("merge-base", C, R14, budget=budget).decode().strip() == C, "C ancestry differs")
    modules = sorted((SOURCE / "swdb-project/swdb").rglob("*.py"))
    require(len(modules) == 185, "source module count differs")
    pins = {p.relative_to(SOURCE / "swdb-project/swdb").as_posix():
            read_file(p, MAX_JSON, budget)[0]["sha256"] for p in modules}
    require(true_digest(pins) == F6, "original F6 differs")
    return {"commit": R14, "modules": 185, "estimator_sha256": F6}

def released(budget):
    result = {}
    for name in ("mbit10-evaluation-node0", "mbit10-evaluation-node1", "mbit10-evaluation"):
        value, pin = read_json(LEASES / (name + ".meta.json"), budget)
        require(value.get("state") == "released", "all three authoritative leases must be released")
        result[name] = pin
    return result

def completion(args, budget):
    manifest, mp = read_json(RAW / "manifest.json", budget, args.manifest_file_sha256, True)
    require(manifest["identity_sha256"] == args.manifest_identity_sha256 and
            manifest["format"] == "swdb.lanl14-final-reports-manifest.v1" and
            manifest["source"] == str(SOURCE) and manifest["source_commit"] == manifest["tested_source_sha"] == R14 and
            manifest["raw"] == str(RAW) and manifest["tag"] == TAG and manifest["estimator_sha256"] == F6,
            "original manifest source/tag differs")
    require(manifest["helper"] == {"path": str(HELPER), "sha256": E79}, "original e79 supplier path/pin differs")
    for path in (HELPER, RAW / "control/helper.py"):
        read_file(path, MAX_JSON, budget, E79)
    accept, ap = read_json(RAW / "control/acceptance.json", budget, args.acceptance_file_sha256, True)
    dispatch, dp = read_json(RAW / "control/dispatch.json", budget, sealed=True)
    request, rp = read_json(RAW / "report-request.json", budget, args.request_file_sha256, True)
    protected, pp = read_json(RAW / "protected.json", budget, args.protected_file_sha256, True)
    require(accept["identity_sha256"] == args.acceptance_identity_sha256 and
            accept["format"] == "swdb.lanl14-final-reports-acceptance.v1" and
            accept["manifest_sha256"] == dispatch["manifest_sha256"] == manifest["identity_sha256"] and
            accept["source_commit"] == R14 and accept["source_clean"] is True and
            accept["final_estimator_sha256"] == F6 and accept["all_nine_public_estimates"] is True and
            accept["prior_record_library_app_bytes_preserved"] is True and accept["raw_transferred"] is False and
            accept["provider_calls"] == accept["application_timings"] == 0,
            "original complete acceptance differs")
    require(type(accept["completed_utc"]) is str and bool(accept["completed_utc"]) and
            "(verified:" in accept["verified_lane"], "original completed/verified report window differs")
    require(request["format"] == "swdb.generality-report-request.v1" and
            request["identity_sha256"] == args.request_identity_sha256 == accept["request_sha256"] and
            request["reference"] == {"kernel": "bfs", "target": "dx100"} and
            accept["report_sha256"] == args.report_identity_sha256,
            "original request/report inherited semantic pins differ")
    require(type(manifest["module_hashes"]) is dict and len(manifest["module_hashes"]) == 185 and
            true_digest(manifest["module_hashes"]) == F6, "original manifest complete bundle differs")
    require(set(protected) == {"records", "library", "apps", "identity_sha256"} and
            true_digest({k: v for k, v in protected.items() if k != "identity_sha256"}) == manifest["protected_sha256"],
            "original protected inventory differs")
    for name in ("records", "library", "apps"):
        require(type(protected[name]) is dict and len(protected[name]) <= MAX_ENTRIES, "protected inventory bound differs")
    for name in ("runner-exit-code.txt", "wrapper-exit-code.txt"):
        _, body = read_file(RAW / "control" / name, 64, budget, retain=True)
        require(body.strip() == b"0", "original runner/wrapper nonzero")
    _, done = read_file(RAW / "control/completed.txt", 4096, budget, retain=True)
    require(bool(done.strip()), "original completed marker empty")
    cleanup, cp = read_json(RAW / "control/final-cleanup.json", budget)
    require(cleanup.get("subreaper") is True and cleanup.get("survivors") == {}, "original owned cleanup differs")
    validation_pin, validation = read_file(RAW / "final-validate.stdout", MAX_JSON, budget,
                                           args.final_validation_file_sha256, True)
    require(validation.decode().strip() == accept["validation"] and accept["validation"].startswith("OK: "),
            "original full validation differs")
    lane, lp = read_json(RAW / "control/lane.json", budget)
    lane = lane["socket_lane"]
    command = ["python3", str(RAW / "control/helper.py"), "run", "--manifest", str(RAW / "manifest.json")]
    require(dispatch["node"] == 0 and dispatch["job"] == JOB and dispatch["command"] == command and
            lane["node"] == 0 and lane["lease_generation"] == 510 and lane["job"] == JOB and
            lane["lease_name"] == "mbit10-evaluation-node0" and lane["numa_memory_policy"] == "bind:0" and
            lane["command"] == command and lane["exit_code"] == 0 and bool(lane["ended_utc"]) and
            not lane.get("record_errors"), "original successful generation510 lane differs")
    return manifest, accept, request, protected, {"manifest": mp, "acceptance": ap, "dispatch": dp,
        "request": rp, "protected": pp, "validation": validation_pin, "cleanup": cp, "lane": lp}

def relative_yaml(value, kind):
    require(type(value) is str and len(value) <= 1024, "exact relative canonical path required")
    path = Path(value)
    prefix = "protocols" if kind == "protocol" else "estimates"
    require(not path.is_absolute() and ".." not in path.parts and len(path.parts) == 2 and
            path.parts[0] == prefix and path.suffix == ".yaml" and path.as_posix() == value,
            "selected canonical route differs")
    return path

def subjects(args, accept, request, protected):
    pairs = request["pairs"]
    require(type(pairs) is list and len(pairs) == 9 and
            [(p["kernel"], p["target"]) for p in pairs] == ORDER, "exact nine ordered pairs required")
    require(pairs[0]["estimate"] == accept["fresh_dx_bfs_reference"], "first actual reference differs")
    result, paths, ids = [], set(), set()
    for pair in pairs:
        for name, kind in (("protocol", "protocol"), ("estimate", "estimate")):
            pin = pair[name]
            require(set(pin) == {"path", "id", "kind", "sha256", "file_sha256"} and pin["kind"] == kind,
                    "original selected pin fields differ")
            path = relative_yaml(pin["path"], kind)
            require(type(pin["id"]) is str and path.stem == pin["id"] and
                    pin["id"] not in ids and pin["path"] not in paths and
                    pin["path"] not in protected["records"], "unique NEW selected canonical pin required")
            sha_syntax(pin["sha256"]); sha_syntax(pin["file_sha256"])
            ids.add(pin["id"]); paths.add(pin["path"])
            result.append({"path": RAW / "records" / path, "expected_sha256": pin["file_sha256"],
                           "maximum": MAX_OTHER, "kind": kind, "id": pin["id"]})
    require(type(accept["added_record_paths"]) is list and len(accept["added_record_paths"]) == 18 and
            len(set(accept["added_record_paths"])) == 18 and set(accept["added_record_paths"]) == paths,
            "actual acceptance 18-path set differs")
    baseline = {p for p in protected["records"] if p.endswith((".yaml", ".yml"))}
    require(len(baseline) == 686, "exact protected prior686 required")
    live = {p.relative_to(RAW / "records").as_posix() for p in (RAW / "records").rglob("*")
            if p.is_file() and p.suffix in (".yaml", ".yml")}
    require(live == baseline | paths and len(live) == 704, "complete raw canonical membership differs")
    source_yaml = {p.relative_to(SOURCE / "swdb-project/records").as_posix()
                   for p in (SOURCE / "swdb-project/records").rglob("*")
                   if p.is_file() and p.suffix in (".yaml", ".yml")}
    require(source_yaml == baseline, "source prior686 membership differs")
    result.extend([
        {"path": RAW / "report/report.json", "expected_sha256": args.report_file_sha256,
         "maximum": MAX_REPORT, "kind": "original_report_bytes", "expected_bytes": args.report_bytes},
        {"path": RAW / "report/report.md", "expected_sha256": args.markdown_file_sha256,
         "maximum": MAX_OTHER, "kind": "original_markdown_bytes", "expected_bytes": args.markdown_bytes},
        {"path": RAW / "report-request.json", "expected_sha256": args.request_file_sha256,
         "maximum": MAX_OTHER, "kind": "original_request_bytes"},
    ])
    require(len(result) == len({r["path"] for r in result}) == 21, "exact 21-file selection required")
    return result

def private_bytes(path, body):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        require(stream.write(body) == len(body), "custody short write")
        stream.flush(); os.fsync(stream.fileno())
    require(stat.S_IMODE(checked(path).lstat().st_mode) == 0o600, "custody privacy differs")
    return {"path": str(path), "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}

def private_json(path, value):
    body = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()
    require(len(body) <= MAX_JOURNAL, "unsealed custody bound exceeded")
    return private_bytes(path, body)

def native(budget):
    require(sys.platform == "linux" and socket.gethostname().split(".")[0] == "mbit10" and
            os.getuid() == os.geteuid() == UID, "exact native mbit10 account required")
    require(Path(sys.executable).resolve(strict=True) == Path("/usr/bin/python3.12"), "native Python route differs")
    result = {}
    for path, (size, digest) in NATIVE.items():
        pin, raw = read_file(path, 128 * 1024 * 1024, budget, digest, True, 0)
        require(pin["bytes"] == size and raw[:6] == b"\x7fELF\x02\x01" and
                int.from_bytes(raw[18:20], "little") == 62 and
                not pin["stat"]["st_mode"] & 0o022 and pin["stat"]["st_mode"] & 0o111,
                "root-owned native ELF differs")
        result[path] = pin
    return result

class PrivateParser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("argument_contract")


def exact_commit(value):
    require(type(value) is str and re.fullmatch(r"[a-f0-9]{40}", value), "exact_full40")
    return value


def fixed_git(root, argv, budget, allow_absent=False):
    budget.check(); checked(root, True)
    child = subprocess.run(["/usr/bin/git", "-c", "core.fsmonitor=false", "-C", str(root), *argv],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=min(120, budget.deadline - time.monotonic()),
        env={**os.environ, **ENV_OVERRIDES, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"})
    require(len(child.stdout) <= MAX_JSON and len(child.stderr) <= MAX_JSON, "git_output_bound")
    require(child.returncode == 0 or (allow_absent and child.returncode == 1), "fixed_git_status")
    return child.returncode, child.stdout


def fresh_absent(path):
    require(path.is_absolute() and ".." not in path.parts and len(str(path)) <= 4096,
            "fresh_absolute")
    require(not os.path.lexists(path), "partial_original_preserved")
    for parent in path.parents:
        require(not parent.is_symlink(), "fresh_parent_symlink")


def source_checks(args, budget):
    pins = {str(Path(__file__).absolute()): read_file(Path(__file__).absolute(), MAX_JSON, budget,
                                                     args.source_sha256)[0]}
    own = Path(__file__).absolute()
    require(all(not own.is_relative_to(p) for p in (PRIMARY, SOURCE, C_ROOT, RAW, EXPORT_W, ADMIN)),
            "own_source_external")
    for path, (size, digest) in CODE.items():
        pin, _ = read_file(path, MAX_JSON, budget, digest)
        require(not pin["stat"]["st_mode"] & 0o022 and (size is None or pin["bytes"] == size),
                "reviewed_code_mode_size")
        pins[path] = pin
    require(not pins[str(own)]["stat"]["st_mode"] & 0o022, "own_source_mode")
    for root, revision in ((PRIMARY, args.expected_primary), (C_ROOT, C)):
        require(fixed_git(root, ["rev-parse", "HEAD"], budget)[1].decode().strip() == revision,
                "primary_or_C_HEAD")
        require(not fixed_git(root, ["status", "--porcelain"], budget)[1], "primary_or_C_clean")
    require(fixed_git(PRIMARY, ["rev-parse", "origin/yanrujhou_main"], budget)[1].decode().strip()
            == args.expected_primary, "delivered_primary_upstream")
    require(fixed_git(PRIMARY, ["symbolic-ref", "--short", "HEAD"], budget)[1].decode().strip()
            == "yanrujhou_main", "primary_branch")
    identity = source_identity(budget)
    c_modules = sorted((C_PROJECT / "swdb").rglob("*.py"))
    require(len(c_modules) == 185, "C_modules")
    c_map = {p.relative_to(C_PROJECT / "swdb").as_posix():read_file(p, MAX_JSON, budget)[0]["sha256"]
             for p in c_modules}
    require(true_digest(c_map) == F6, "C_F6")
    return {"code": pins, "R14": identity, "C": C, "C_modules": 185,
            "C_estimator_sha256": F6, "primary": args.expected_primary}


def native_checks(budget):
    require(platform.machine() == "x86_64" and pwd.getpwuid(UID).pw_name == "yanruj", "native_arch_account")
    pins = native(budget)
    size, digest = 39880, "12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52"
    pin, body = read_file(GNU, 128 * 1024 * 1024, budget, digest, True, 0)
    require(pin["bytes"] == size and body[:6] == b"\x7fELF\x02\x01" and
            int.from_bytes(body[18:20], "little") == 62 and
            not pin["stat"]["st_mode"] & 0o022 and pin["stat"]["st_mode"] & 0o111,
            "native_GNU")
    pins[str(GNU)] = pin
    return pins


def correction(args, budget, selection, original_inputs):
    path = checked(args.mode_receipt)
    require(path.name == "receipt.json" and path.parent.parent == RAW.parent and
            re.fullmatch(r"lanl14-report-transfer-mode-administration-[a-z0-9-]{1,80}", path.parent.name),
            "original_correction_route")
    value, pin = read_json(path, budget, args.mode_receipt_sha256)
    require(value.get("format") == "swdb.lanl14-report-transfer-mode-facts.v1" and
            value.get("state") == "completed" and value.get("failure_type") is None and
            value.get("changes_started") is True and value.get("completed_file_count") == 21 and
            value.get("source_sha256") == CORRECTION_SHA and value.get("source_revision") == R14 and
            value.get("estimator_sha256") == F6 and value.get("sealed") is False and
            value.get("scientific_admission") is False and value.get("science_or_exporter_reader_main_invoked") is False,
            "actual_completed_correction")
    rows = value.get("completed_files")
    require(type(rows) is list and len(rows) == 21 and
            len({r["path"] for r in rows}) == 21 and
            {r["path"] for r in rows} == {str(r["path"]) for r in selection}, "exact_correction21")
    facts = value.get("original_inputs")
    require(type(facts) is dict and set(facts) == set(original_inputs), "correction_original_inputs")
    for name in facts:
        require(facts[name]["sha256"] == original_inputs[name]["sha256"] and
                facts[name]["bytes"] == original_inputs[name]["bytes"], "correction_input_bytes")
    live = []
    by_path = {r["path"]: r for r in rows}
    for item in selection:
        row = by_path[str(item["path"])]
        require(row["before_mode"] == "0o664" and row["after_mode"] == "0o644" and
                row["content_identity_preserved"] is True and row["sha256"] == item["expected_sha256"],
                "mode_only_original")
        status = checked(item["path"]).lstat()
        require(stamp(status) == row["after_stat"] and stat.S_IMODE(status.st_mode) == 0o644 and
                status.st_size == row["bytes"] and 0 < status.st_size <= item["maximum"], "live_corrected_original")
        if "expected_bytes" in item:
            require(status.st_size == item["expected_bytes"], "original_size")
        live.append({"path": str(item["path"]), "bytes": status.st_size, "sha256": row["sha256"],
                     "stat": stamp(status), "byte_SHA_basis": "exact_original_correction_streamed_hash"})
    journal = value["journal"]
    require(journal["path"] == str(path.parent / "journal.jsonl"), "correction_journal_route")
    jp, _ = read_file(journal["path"], MAX_JOURNAL, budget, journal["sha256"])
    require(jp["bytes"] == journal["bytes"], "correction_journal_pin")
    return {"receipt": pin, "journal": jp, "selected": live,
            "report_JSON_parsed": False, "original_byte_SHA_basis": "completed original correction; same exact stat"}


def gates(args, budget):
    manifest, accept, request, protected, inputs = completion(args, budget)
    require(manifest["count_helper"] == {"path": str(COUNT), "sha256": CODE[str(COUNT)][1]} and
            manifest["cleanup_helper"] == {"path": str(CLEANUP), "sha256": CODE[str(CLEANUP)][1]} and
            manifest["reporter_sha256"] == CODE[str(SOURCE / "swdb-project/scripts/generality_report.py")][1] and
            manifest["limits"] == {"threads_max":4,"thread_limit":16,"provider_calls":0,"application_timings":0,
                                   "freeze_s":6000,"estimate_s":4000,"validate_s":3600,"report_s":3600,"outer_s":108000},
            "original_supplier_science_limits")
    selection = subjects(args, accept, request, protected)
    cp = correction(args, budget, selection, inputs)
    require(fixed_git(MEMACC, ["rev-parse", "origin/yanrujhou_main"], budget)[1].decode().strip()
            == args.wrapper_upstream_commit, "parent_bound_wrapper_upstream")
    wrapper = checked(manifest["wrapper"]["path"])
    require(wrapper == MEMACC / WRAPPER_REL, "original_wrapper_route")
    wp, body = read_file(wrapper, MAX_JSON, budget, manifest["wrapper"]["sha256"], True)
    require(body == fixed_git(MEMACC, ["show", args.wrapper_upstream_commit + ":" + WRAPPER_REL], budget)[1],
            "wrapper_exact_upstream_bytes")
    proof = manifest["cleanup_proof"]
    proof_path = SOURCE / "swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-linux-cleanup-smoke-mbit10-20261006-a1.json"
    require(proof["path"] == str(proof_path), "original_cleanup_proof_route")
    pv, pp = read_json(proof_path, budget, proof["file_sha256"])
    receipt = pv.get("receipt", pv)
    original_true(receipt)
    require(receipt["identity_sha256"] == proof["receipt_identity_sha256"] and
            receipt["passed"] is True and receipt["cleanup"]["survivors"] == {} and
            receipt["unrelated_sibling_survived"] is True and
            receipt["helper_sha256"] == CODE[str(CLEANUP)][1] and
            receipt["processes_py_sha256"] == proof["processes_py_sha256"] == CODE[str(PROCESSES)][1],
            "original_cleanup_proof")
    leases = released(budget)
    memory_raw = Path("/proc/meminfo").read_bytes()
    require(len(memory_raw) <= 65536, "meminfo_bound")
    memory = dict(line.split(":", 1) for line in memory_raw.decode().splitlines())
    available = int(memory["MemAvailable"].split()[0]) * 1024
    disks = {mount:os.statvfs(mount).f_bavail * os.statvfs(mount).f_frsize for mount in ("/data1", "/data")}
    require(available >= 48 * 1024**3 and disks["/data1"] >= 21 * 1024**3 and disks["/data"] >= 24 * 1024**3,
            "unchanged_reserve")
    require(not os.path.lexists(RAW / "control/error.json"), "original_runner_error_preserved")
    return {"original_inputs": inputs, "manifest_identity_sha256": manifest["identity_sha256"],
            "acceptance_identity_sha256": accept["identity_sha256"], "original_correction": cp,
            "wrapper": wp, "wrapper_upstream_commit": args.wrapper_upstream_commit,
            "cleanup_original": pp, "released_leases": leases,
            "capacity": {"memory_available_bytes":available,"free_disk_bytes":disks},
            "scientific_admission_inherited_pending_original928_rechecks": True}


def absent_outputs(budget):
    for path in (ADMIN, CONTROL, EXPORT_W, RAW / "report/report-transfer.json.gz",
                 RAW / "export-validate.stdout", RAW / "export-validate.stderr"):
        fresh_absent(path)
    code, body = fixed_git(SOURCE, ["show-ref", "--verify", "--quiet", "refs/heads/" + BRANCH], budget, True)
    require(code == 1 and not body, "fresh_local_export_branch")
    require(not fixed_git(SOURCE, ["ls-remote", "--heads", "origin", BRANCH], budget)[1], "fresh_remote_export_branch")
    parent = checked(ADMIN.parent, True)
    require(all(not ADMIN.is_relative_to(p) and not p.is_relative_to(ADMIN) for p in
                (PRIMARY, SOURCE, C_ROOT, RAW, EXPORT_W)), "fresh_admin_disjoint")
    require(not any(Path(path).is_relative_to(ADMIN) for path in CODE), "admin_excludes_controls")
    return {"admin_parent":str(parent), "fresh_admin":str(ADMIN), "fresh_supervisor_leaf":str(CONTROL),
            "export_checkout":str(EXPORT_W), "export_branch":BRANCH,
            "export_validation_originals_absent":True,"compressed_partial_absent":True}


def argv():
    return [str(GNU), "--signal=TERM", "--kill-after=60s", "18120s", str(PY), "-B", str(SUP),
            "--cleanup-helper", str(CLEANUP), "--project", str(C_PROJECT), "--selected-source", str(EXPORTER),
            "--action", "exporter", "--timeout-s", "18000", "--python", str(PY),
            "--python-sha256", NATIVE[str(PY)][1], "--supervisor-sha256", CODE[str(SUP)][1],
            "--cwd", str(SOURCE / "swdb-project"), "--control-directory", str(CONTROL), "--",
            "--manifest", str(RAW / "manifest.json"), "--helper", str(HELPER), "--checkout", str(EXPORT_W),
            "--branch", BRANCH, "--push"]


def supervisor_result(budget):
    result, pin = read_json(CONTROL / "receipt.json", budget)
    require(pin["bytes"] <= MAX_RETURN and result.get("canonical_ensure_ascii") is False,
            "supervisor_original_bound_policy")
    payload = {k:v for k,v in result.items() if k != "identity_sha256"}
    actual = hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    require(result["identity_sha256"] == actual and result["format"] == "swdb.lanl14-export-reader-administrative-supervisor.v1",
            "supervisor_original_seal")
    require(result["action"] == "exporter" and result["selected_source_sha256"] == CODE[str(EXPORTER)][1] and
            result["supervisor_sha256"] == CODE[str(SUP)][1] and result["native_python_sha256"] == NATIVE[str(PY)][1] and
            result["timeout_s"] == 18000 and result["fixture"] is False and result["scientific_admission"] is False and
            result["child_scientific_result_assessed"] is False, "supervisor_exact_scope")
    compact = {"receipt":pin,"identity_sha256":result["identity_sha256"],"action":result["action"],
               "state":result["state"],"supervisor_exit":result["supervisor_exit"],
               "cleanup_survivor_count":result["cleanup"]["survivor_count"],"scientific_admission":False}
    success = (result["state"] == "child_returned" and result["returned_child_exit"] == result["child_exit"] ==
               result["supervisor_exit"] == 0 and result["timed_out"] is False and result["signal_received"] is None and
               result["error_type"] is None and result["cleanup_errors"] == [] and result["cleanup"]["subreaper"] is True and
               result["cleanup"]["survivor_count"] == 0 and result["supervision_success"] is True)
    return compact, success


def main():
    os.umask(0o077)  # Before any child, private original, or original928 exported file.
    parser = PrivateParser(description=__doc__)
    for name in ("source-sha256", "manifest-file-sha256", "manifest-identity-sha256", "acceptance-file-sha256",
                 "acceptance-identity-sha256", "request-file-sha256", "request-identity-sha256", "protected-file-sha256",
                 "final-validation-file-sha256", "report-file-sha256", "report-identity-sha256", "markdown-file-sha256",
                 "mode-receipt-sha256"):
        parser.add_argument("--" + name, required=True, type=sha_syntax)
    parser.add_argument("--expected-primary", required=True, type=exact_commit)
    parser.add_argument("--wrapper-upstream-commit", required=True, type=exact_commit)
    parser.add_argument("--mode-receipt", required=True, type=Path)
    parser.add_argument("--report-bytes", required=True, type=int)
    parser.add_argument("--markdown-bytes", required=True, type=int)
    parser.add_argument("--metadata-deadline-s", required=True, type=int)
    args = parser.parse_args()
    require(not any(name in os.environ for name in STARTUP), "startup_override_refused")
    require(not sys.flags.optimize and sys.flags.dont_write_bytecode, "native_flags_B_assertions")
    require(0 < args.report_bytes <= MAX_REPORT and 0 < args.markdown_bytes <= MAX_OTHER, "explicit_report_sizes")
    budget = Budget(args.metadata_deadline_s)
    before_native = native_checks(budget)
    before_source = source_checks(args, budget)
    before_gates = gates(args, budget)
    absence = absent_outputs(budget)
    require(released(budget) == before_gates["released_leases"], "prelaunch_leases_changed")
    require(source_checks(args, budget) == before_source and native_checks(budget) == before_native,
            "prelaunch_source_native_changed")
    # Originals are created only after every concrete completion/correction/absence gate.
    ADMIN.mkdir(mode=0o700)
    require(stat.S_IMODE(checked(ADMIN, True).lstat().st_mode) == 0o700, "admin_mode0700")
    registered = {"format":"swdb.lanl14-exact-export-invocation-preregistration.v1","sealed":False,
        "created_utc":now(),"scientific_admission":False,"execution_not_yet_started":True,
        "public_argv":argv(),"explicit_environment_overrides":ENV_OVERRIDES,
        "inherited_environment_or_auth_dumped":False,"cwd":str(SOURCE / "swdb-project"),"uid":UID,
        "native":before_native,"sources":before_source,"actual_completion_and_correction":before_gates,
        "fresh_outputs":absence,"umask":"0o077","GNU_outer_s":18120,"GNU_KILL_allowance_s":60,
        "unchanged_supervisor_child_s":18000,"invocation_wait_s":INVOCATION_WAIT_S,
        "administrative_duration_sufficiency":"unproved","report_body_parsed_or_transferred":False,
        "no_retry":True,"reader_not_invoked":True}
    prereg = private_json(ADMIN / "preregistration.json", registered)
    start = now(); launched = False; invocation_exit = None; failure = None; compact = None; cleanup_success = False
    out_pin = err_pin = status_pin = None
    try:
        require(not any(name in os.environ for name in STARTUP), "prechild_startup_override")
        require(released(budget) == before_gates["released_leases"], "immediate_leases_changed")
        require(source_checks(args, budget) == before_source, "immediate_code_changed")
        out_fd = os.open(ADMIN / "supervisor.stdout", os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
        with os.fdopen(out_fd, "wb") as out:
            err_fd = os.open(ADMIN / "supervisor.stderr", os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
            with os.fdopen(err_fd, "wb") as err:
                launched = True
                child = subprocess.run(argv(), cwd=SOURCE / "swdb-project", env={**os.environ, **ENV_OVERRIDES},
                    stdout=out, stderr=err, timeout=INVOCATION_WAIT_S)
                invocation_exit = child.returncode
                out.flush();err.flush();os.fsync(out.fileno());os.fsync(err.fileno())
        after = Budget(args.metadata_deadline_s)
        out_pin, out_body = read_file(ADMIN / "supervisor.stdout", MAX_RETURN, after, retain=True)
        err_pin, _ = read_file(ADMIN / "supervisor.stderr", MAX_JSON, after)
        compact, cleanup_success = supervisor_result(after)
        original_stdout = json.loads(out_body, object_pairs_hook=object_pairs, parse_constant=constant_refused)
        require(original_stdout == {"receipt_sha256":compact["receipt"]["sha256"],
            "identity_sha256":compact["identity_sha256"],"action":compact["action"],"state":compact["state"],
            "supervisor_exit":compact["supervisor_exit"],"cleanup_survivor_count":compact["cleanup_survivor_count"],
            "scientific_admission":False}, "bounded_original_supervisor_stdout")
        require(source_checks(args, after) == before_source and native_checks(after) == before_native,
                "post_source_native_changed")
        require(released(after) == before_gates["released_leases"], "post_released_leases_changed")
        require(invocation_exit == compact["supervisor_exit"], "GNU_and_original_supervisor_status")
    except BaseException as exc:
        failure = type(exc).__name__
    finally:
        # No new descendant cleanup: exact503f owns its child lifecycle; GNU is the finite outer.
        # Timeout/interruption is refused, never cleanup/admission success; parent retains all partials.
        status = {"format":"swdb.lanl14-exact-export-invocation-status.v1","sealed":False,
            "started_utc":start,"ended_utc":now(),"launched":launched,"invocation_exit":invocation_exit,
            "failure_type":failure,"original_preregistration":prereg,"supervisor_result":compact,
            "original_private_stdout":out_pin,"original_private_stderr":err_pin,
            "supervision_success":failure is None and invocation_exit == 0 and cleanup_success,
            "scientific_admission":False,"raw_streams_transferred":False,"reader_invoked":False,
            "partial_policy":"Keep every original/partial; no retry, deletion or normalization. Parent owns follow-up."}
        status_pin = private_json(ADMIN / "invocation-status.json", status)
    success = status["supervision_success"]
    returned = {"state":"supervised_export_returned" if success else "invocation_refused_or_failed",
        "code":0 if success else 1,"error_type":failure,"invocation_status":status_pin,
        "supervisor_result":compact,"scientific_admission":False,"raw_streams_transferred":False}
    raw = json.dumps(returned,ensure_ascii=True,allow_nan=False).encode()
    require(len(raw) <= MAX_RETURN, "compact_return_bound")
    sys.stdout.buffer.write(raw+b"\n");sys.stdout.buffer.flush()
    return 0 if success else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BaseException as exc:
        if isinstance(exc, SystemExit):
            raise
        raw = json.dumps({"state":"preflight_or_publication_refused","code":2,"error_type":type(exc).__name__,
                          "scientific_admission":False,"raw_streams_transferred":False},allow_nan=False).encode()
        sys.stdout.buffer.write(raw+b"\n");sys.stdout.buffer.flush()
        raise SystemExit(2)
