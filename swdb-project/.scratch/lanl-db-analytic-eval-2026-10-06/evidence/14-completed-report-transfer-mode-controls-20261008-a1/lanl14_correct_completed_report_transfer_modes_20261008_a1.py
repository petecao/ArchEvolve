"""Parent-reviewed future Linux permission administration; preparation NOT RUN.

Only 18 actual request-pinned new YAMLs and three fixed report originals can
change from 0664 to 0644. Completion is mandatory. All custody is unsealed
factual metadata; it is neither scientific admission nor a rewritten original.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import signal
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
CONTENT_ID = ("st_dev", "st_ino", "st_nlink", "st_uid", "st_gid", "st_size", "st_mtime_ns")


class Refusal(RuntimeError):
    pass


class Interrupted(BaseException):
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


def content_id(s):
    return tuple(getattr(s, name) for name in CONTENT_ID)


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


def unaffected_snapshot(selected, budget):
    """Stat/name witness only; original complete byte preservation is inherited."""
    result = {}
    for root in (RAW, SOURCE / "swdb-project/records", SOURCE / "swdb-project/library", SOURCE / "swdb-project/apps"):
        checked(root, True)
        rows = {}
        for path in sorted(root.rglob("*")):
            budget.check()
            status = path.lstat()
            if stat.S_ISDIR(status.st_mode):
                continue
            if path in selected:
                continue
            require(len(rows) < MAX_ENTRIES, "unselected witness count exceeds bound")
            require(status.st_uid == UID, "unselected original owner differs")
            row = stamp(status)
            if stat.S_ISLNK(status.st_mode):
                # Witness this original without following or opening its target.
                target = os.readlink(path)
                require(len(target.encode()) <= 4096, "unselected link witness bound exceeded")
                row["link_target_sha256"] = hashlib.sha256(target.encode()).hexdigest()
                require(stamp(path.lstat()) == stamp(status), "unselected link changed during witness")
            rows[path.relative_to(root).as_posix()] = row
        result[str(root)] = rows
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


def append_journal(stream, value):
    body = (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n").encode()
    require(stream.tell() + len(body) <= MAX_JOURNAL, "journal bound exceeded")
    require(stream.write(body) == len(body), "journal short write")
    stream.flush(); os.fsync(stream.fileno())


def output_root(value):
    path = Path(value)
    require(path.parent == RAW.parent and re.fullmatch(r"lanl14-report-transfer-mode-administration-[a-z0-9-]{1,80}", path.name),
            "fixed external fresh administrative route required")
    checked(path.parent, True)
    require(not os.path.lexists(path), "existing custody/partial preserved; refusing")
    require(not any(path.is_relative_to(p) or p.is_relative_to(path) for p in
                    (RAW, SOURCE, Path("/data1/yanruj/ArchEvolve"))), "custody overlaps originals/source")
    path.mkdir(mode=0o700)
    require(stat.S_IMODE(checked(path, True).lstat().st_mode) == 0o700, "custody directory privacy differs")
    return path


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-sha256", "manifest-file-sha256", "manifest-identity-sha256", "acceptance-file-sha256",
                 "acceptance-identity-sha256", "request-file-sha256", "request-identity-sha256", "protected-file-sha256",
                 "final-validation-file-sha256", "report-file-sha256", "report-identity-sha256", "markdown-file-sha256"):
        parser.add_argument("--" + name, required=True, type=sha_syntax)
    parser.add_argument("--report-bytes", required=True, type=int)
    parser.add_argument("--markdown-bytes", required=True, type=int)
    parser.add_argument("--deadline-s", required=True, type=int)
    parser.add_argument("--output-directory", required=True, type=Path)
    args = parser.parse_args()
    require(0 < args.report_bytes <= MAX_REPORT and 0 < args.markdown_bytes <= MAX_OTHER,
            "explicit original byte sizes outside unchanged limits")
    budget = Budget(args.deadline_s)
    os.umask(0o077)
    native_pins = native(budget)
    own = Path(__file__).absolute()
    own_pin, _ = read_file(own, MAX_JSON, budget, args.source_sha256)
    require(not own_pin["stat"]["st_mode"] & 0o022, "own reviewed source writable by another account")
    require(not own.is_relative_to(RAW) and not own.is_relative_to(SOURCE), "own source overlaps protected originals")
    root = output_root(args.output_directory)
    started, failure, completed, journal_pin = now(), None, [], None
    subject_rows, handles, inputs, witnesses, source_before, leases_before = [], [], None, None, None, None
    changed = False
    previous = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGALRM)}

    def interrupted(number, frame):
        raise Interrupted("administrative interruption")

    for number in previous:
        signal.signal(number, interrupted)
    signal.alarm(max(1, int(budget.deadline - time.monotonic())))
    journal = None
    try:
        source_before = source_identity(budget)
        manifest, accept, request, protected, inputs = completion(args, budget)
        leases_before = released(budget)
        subject_rows = subjects(args, accept, request, protected)
        total = 0
        for row in subject_rows:
            path = checked(row["path"])
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            handle = {"fd": fd, "row": row}
            handles.append(handle)
            before = os.fstat(fd)
            require(stat.S_IMODE(before.st_mode) == 0o664, "only original0664 selection admitted; preserve prior corrections")
            pin, _ = fd_hash(fd, path, row["maximum"], budget, row["expected_sha256"])
            if "expected_bytes" in row:
                require(pin["bytes"] == row["expected_bytes"], "original explicit byte size differs")
            total += pin["bytes"]
            require(total <= MAX_PASS, "21-file cumulative pass bound exceeded")
            handle["before"] = before
            handle["pin"] = pin
        selected = {row["path"] for row in subject_rows}
        witnesses = unaffected_snapshot(selected, budget)
        require(released(budget) == leases_before and source_identity(budget) == source_before,
                "pre-change source/released leases changed")
        private_json(root / "preflight.json", {"format": "swdb.lanl14-report-transfer-mode-preflight-facts.v1",
            "created_utc": now(), "source": source_before, "native": native_pins, "original_inputs": inputs,
            "selected": [h["pin"] for h in handles], "leases": leases_before,
            "unselected_stat_witness_sha256": true_digest(witnesses), "sealed": False,
            "scientific_admission": False, "no_permission_changes_yet": True})
        jfd = os.open(root / "journal.jsonl", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        journal = os.fdopen(jfd, "wb")
        for handle in handles:
            budget.check()
            require(released(budget) == leases_before, "authoritative released lease changed; preserve partials")
            fd, row, before = handle["fd"], handle["row"], handle["before"]
            require(stamp(os.fstat(fd)) == stamp(before) == stamp(checked(row["path"]).lstat()),
                    "selected original changed before mode action")
            append_journal(journal, {"state": "pending_fchmod", "created_utc": now(), "original": handle["pin"],
                                     "requested_mode": "0o644"})
            changed = True
            os.fchmod(fd, 0o644)
            after = os.fstat(fd)
            require(content_id(after) == content_id(before) and stat.S_IMODE(after.st_mode) == 0o644 and
                    stamp(after) == stamp(checked(row["path"]).lstat()) and after.st_ctime_ns >= before.st_ctime_ns,
                    "mode-only FD action identity differs")
            pin, _ = fd_hash(fd, row["path"], row["maximum"], budget, handle["pin"]["sha256"])
            record = {"path": str(row["path"]), "kind": row["kind"], "bytes": pin["bytes"], "sha256": pin["sha256"],
                      "before_stat": stamp(before), "after_stat": pin["stat"], "before_mode": "0o664", "after_mode": "0o644",
                      "ctime_before_ns": before.st_ctime_ns, "ctime_after_ns": after.st_ctime_ns,
                      "content_identity_preserved": True, "completed_utc": now()}
            completed.append(record)
            handle["after"] = os.fstat(fd)
            append_journal(journal, {"state": "completed_fchmod", **record})
        require(len(completed) == 21, "exact21 completed actions required")
        require(unaffected_snapshot(selected, budget) == witnesses, "unselected stat/name witness changed")
        # Original request's intended mode/ctime differs; its bytes/seal remain exact.
        _, _, _, _, final_inputs = completion(args, budget)
        for key in inputs:
            require(final_inputs[key]["sha256"] == inputs[key]["sha256"] and
                    final_inputs[key]["bytes"] == inputs[key]["bytes"], "original input bytes changed")
        require(released(budget) == leases_before and source_identity(budget) == source_before,
                "final source/released leases changed")
        require(read_file(own, MAX_JSON, budget, args.source_sha256)[0] == own_pin, "own source changed")
        for handle in handles:
            require(stamp(os.fstat(handle["fd"])) == stamp(handle["after"]) == stamp(checked(handle["row"]["path"]).lstat()),
                    "completed selected file changed before success")
    except BaseException as exc:
        failure = type(exc).__name__
    finally:
        signal.alarm(0)
        for number in previous:
            signal.signal(number, signal.SIG_IGN)
        if journal is not None:
            journal.close()
            body = (root / "journal.jsonl").read_bytes()
            journal_pin = {"path": str(root / "journal.jsonl"), "bytes": len(body),
                           "sha256": hashlib.sha256(body).hexdigest()}
        for handle in handles:
            os.close(handle["fd"])
        result = {"format": "swdb.lanl14-report-transfer-mode-facts.v1", "started_utc": started, "ended_utc": now(),
            "state": "completed" if failure is None else "partial_failure" if changed else "preflight_failed",
            "failure_type": failure, "changes_started": changed, "completed_file_count": len(completed),
            "completed_files": completed, "journal": journal_pin, "original_inputs": inputs,
            "source_sha256": args.source_sha256, "source_revision": R14, "estimator_sha256": F6,
            "requested_deadline_s": args.deadline_s, "streamed_bytes": budget.bytes_read, "sealed": False,
            "scientific_admission": False, "science_or_exporter_reader_main_invoked": False,
            "report_semantic_binding": "Inherited from original all-nine acceptance and explicit parent pin; report bytes only, never JSON reserialization.",
            "unselected_preservation_scope": "No writes outside21 selected files and fresh private custody; unchanged stat/name witness. Original complete-byte validation/preservation inherited; unchanged928 repeats full inventory hashes.",
            "partial_policy": "No rollback, retry or cleanup. Keep journal/pending rows and every original."}
        pin = private_json(root / "receipt.json", result)
        for number, handler in previous.items():
            signal.signal(number, handler)
    print(json.dumps({"receipt": pin, "state": result["state"], "completed_file_count": len(completed),
                      "scientific_admission": False}, allow_nan=False))
    return 0 if failure is None else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Refusal, ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as exc:
        print("permission administration refused: " + type(exc).__name__, file=sys.stderr)
        raise SystemExit(2)
