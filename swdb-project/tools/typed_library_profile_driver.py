#!/usr/bin/env python3
"""Bounded tickets 27/34/36 driver, launched by the operator's socket lane.

Updated: 2026-10-03. No dispatch, Git mutation, fixture, graph generation or
source copying to another host happens here. Records and raw output stay on
mbit10; the operator synchronizes records through Git after checking them.
"""

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import socket
import signal
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from swdb import artifacts, dispatch_preflight, host_observation, profile_package, provider_adapters, provider_guard
from swdb.cli import Failure, _require_valid
from swdb.processes import stop_group

SOURCE = "bfs-dx100-scalar-only-20260929-a1.source"
SOURCE_SHA256 = "2bf9b1b85bf3be392e2986d1879aeabea5a23479fd7e8060a31d76e5b3a5c6af"
WORKLOAD = "bfs-20260928-kronecker18-s0.cf4283236c5cb50c"
WORKLOAD_SHA256 = "cf4283236c5cb50c245b7e5c883ce2f9a0f548287eb072707b49bbf3376deea2"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, value):
    temporary = path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(value, indent=2)+"\n")
    temporary.replace(path)


def checked_command(arguments, folder, stage, *, timeout, environment=None):
    """Retain argv and bounded command output before classifying success."""
    row = {"stage": stage, "command": [str(v) for v in arguments], "started": now(), "timeout_seconds": timeout}
    output, errors = folder/(stage+".json"), folder/(stage+".stderr.txt")
    child = None
    try:
        with output.open("x") as stdout, errors.open("x") as stderr:
            child = subprocess.Popen(row["command"], cwd=PROJECT, env=environment, stdout=stdout, stderr=stderr,
                                     text=True, start_new_session=True)
            returncode = child.wait(timeout=timeout)
        row.update(finished=now(), returncode=returncode, state="complete" if returncode == 0 else "failed",
                   output={"path": str(output), "sha256": artifacts.file_hash(output)},
                   stderr={"path": str(errors), "sha256": artifacts.file_hash(errors)})
        save(folder/(stage+".command.json"), row)
        if returncode:
            raise Failure(f"{stage} returned {returncode}; see {errors}")
        if output.stat().st_size > 64*1024*1024:
            raise Failure(f"{stage} returned more than 64 MiB of record JSON")
        return json.loads(output.read_text())
    except subprocess.TimeoutExpired:
        row.update(finished=now(), state="timed_out")
        save(folder/(stage+".command.json"), row)
        raise Failure(f"{stage} exceeded {timeout} seconds") from None
    finally:
        stop_group(child, grace_seconds=5)


def _cli(args, command):
    result = [sys.executable, "-m", "swdb", command, "--records", str(args.records), "--format", "json"]
    if command not in {"annotate", "annotate-score"}:
        result += ["--db", str(args.runs_dir/(args.id+".sqlite"))]
    return result


def _request(folder, name, value):
    path = folder/(name+".request.json")
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2)+"\n")
    return path


def validate_inputs(args, store):
    source = store.get(args.source_snapshot, "source_snapshot")
    workload = store.get(args.workload, "workload")
    if not source or source.get("implementation") != "dx100-bfs-scalar":
        raise Failure("driver requires the scalar DX100 BFS source snapshot")
    if args.source_snapshot == SOURCE and source["artifact"]["sha256"] != SOURCE_SHA256:
        raise Failure("default scalar source snapshot differs from its pinned identity")
    root = artifacts.verify(source["artifact"])
    code = root/"benchmarks/gapbs/src/bfs.cc"
    if not code.is_file() or re.search(r"\b(?:TDStepMAA|DOBFSMAA)\s*\(", code.read_text()):
        raise Failure("driver source exposes the authors' accelerated BFS")
    definition = (workload or {}).get("definition", {})
    if (not workload or workload.get("identity_sha256") != (WORKLOAD_SHA256 if args.workload == WORKLOAD else workload.get("identity_sha256"))
            or definition.get("family") != "kronecker" or definition.get("sources") != [0]
            or definition.get("generator", {}).get("parameters", {}).get("scale") != 18):
        raise Failure("driver requires the registered Kronecker18 source0 workload pin")
    from swdb.bfs_protocol import verify_immutable
    verify_immutable(workload)
    return source, workload


def profile_stage(args, folder, lane, environment):
    native_id, candidate_id, profile_id = args.id+".native", args.id+".baseline", args.id+".profile"
    candidate = checked_command(_cli(args, "baseline-candidate") + [args.source_snapshot, "--id", candidate_id,
        "--runs-dir", str(args.runs_dir)], folder, "baseline-candidate", timeout=180, environment=environment)
    request = {"message_version": "1.0", "id": native_id, "machine": "mbit10", "candidate": candidate_id,
        "workload": {"id": args.workload}, "sources": [0], "threads": args.threads, "repetitions": 1,
        "roi": "bfs.complete_call.v1", "protocol": None, "fixture": False,
        "budget": {"build_seconds": 120, "run_seconds": 120, "total_seconds": 600}}
    evaluation = checked_command(_cli(args, "evaluate") + [str(_request(folder, "native", request)),
        "--runs-dir", str(args.runs_dir), "--lane", lane.split(" ", 1)[0]], folder, "native",
        timeout=660, environment=environment)
    if evaluation["outcome"]["state"] != "complete" or evaluation["correctness"]["state"] != "passed" or evaluation["evidence_kind"] != "execution":
        raise Failure("native stage did not produce real complete correctness evidence")
    request = {"message_version": "1.0", "id": profile_id, "evaluation": native_id,
        "repetitions": 1, "fixture": False, "memory": True, "per_line": True,
        "discovery": {"library": str(args.libclang)},
        "budget": {"discovery_seconds": 120, "build_seconds": 120, "run_seconds": 900, "total_seconds": 3000}}
    profile = checked_command(_cli(args, "bfs-profile") + [str(_request(folder, "profile", request)),
        "--runs-dir", str(args.runs_dir), "--lane", lane.split(" ", 1)[0]], folder, "profile",
        timeout=3060, environment=environment)
    if not profile.get("per_line_memory") or len(profile.get("statement_memory", [])) != 7:
        raise Failure("profiling did not produce independently attributed costs for seven TDStep statements")
    request = {"message_version": "1.0", "id": args.id+".package", "implementation": "dx100-bfs-scalar",
        "evaluation": native_id, "region_profile": profile_id, "context": profile_package._context(evaluation)}
    package = checked_command(_cli(args, "profile-package") + [str(_request(folder, "package", request))],
        folder, "package", timeout=300, environment=environment)
    if package.get("completeness") != "complete" or package.get("evidence", {}).get("classification") != "execution":
        raise Failure("profile package is incomplete: " + "; ".join(package.get("reasons", [])))
    return {"candidate": candidate_id, "evaluation": native_id, "region_profile": profile_id,
            "profile_package": package["id"], "source_snapshot": args.source_snapshot,
            "per_line_rows": len(profile["per_line_memory"]), "statements": len(profile["statement_memory"]),
            "package_completeness": package["completeness"], "gain_claim": False}


def annotate_stage(args, folder, environment):
    store = _require_valid(args.records)
    profile = store.get(args.id+".profile", "region_profile")
    if not profile or not profile.get("per_line_memory"):
        raise Failure("annotate stage needs the existing profile stage's per-line record")
    pins = provider_adapters.PINS["codex"]
    if pins != {"model": "gpt-5.6-sol", "effort": "xhigh"}:
        raise Failure("driver's authorized Codex model/effort pin changed")
    config = _request(folder, "codex-provider", {"kind": "codex", "command": [args.codex_command],
        "workspace": True, "timeout_s": 900, "total_seconds": 900, "max_repairs": 0})
    annotated = checked_command(_cli(args, "annotate") + ["dx100-bfs-scalar", "--source-snapshot", args.source_snapshot,
        "--provider-config", str(config), "--runs-dir", str(args.runs_dir), "--id", args.id+f".annotation-a{args.annotation_attempt}",
        "--profile", args.id+".profile"], folder, "annotate", timeout=960, environment=environment)
    if annotated["classification"] != "rewrite_provider" or annotated["statements"] != 7:
        raise Failure("annotate did not produce seven real-provider statement predictions")
    table = folder/"josh-statement-table.md"
    report = checked_command(_cli(args, "annotate-score") + ["dx100-bfs-scalar", "--source-snapshot", args.source_snapshot,
        "--region-profile", args.id+".profile", "--table", str(table)], folder, "score", timeout=180, environment=environment)
    return {"receipt": annotated["receipt"], "model": pins["model"], "effort": pins["effort"],
            "spearman_rank_correlation": report["spearman_rank_correlation"], "top_3_overlap": report["top_3_overlap"],
            "statement_table": {"path": str(table), "sha256": artifacts.file_hash(table)}, "gain_claim": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["profile", "annotate"], required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--runs-dir", type=Path, required=True)
    parser.add_argument("--records", type=Path, default=PROJECT/"records")
    parser.add_argument("--source-snapshot", default=SOURCE)
    parser.add_argument("--workload", default=WORKLOAD)
    parser.add_argument("--threads", type=int, choices=range(1, 17), default=4)
    parser.add_argument("--libclang", type=Path, default=Path("/data1/yanruj/llvm18/lib/libclang.so"))
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--approval-reference", required=True)
    parser.add_argument("--annotation-attempt", type=int, choices=range(1, 11), default=1)
    args = parser.parse_args(argv)
    if socket.gethostname().split(".")[0] != "mbit10":
        raise Failure("real profiling driver requires mbit10")
    try:
        lane = provider_guard._lane()
    except provider_guard.GuardError as error:
        raise Failure(str(error)) from None
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", args.id):
        raise Failure("driver ID must use the record identifier syntax")
    args.runs_dir = args.runs_dir.resolve()
    if not any(args.runs_dir.is_relative_to(p) for p in (Path("/data1/yanruj/EvolveSWDB_runs"), Path("/data/yanruj/EvolveSWDB_runs"))):
        raise Failure("driver raw output requires one of the two approved run roots")
    store = _require_valid(args.records)
    source, workload = validate_inputs(args, store)
    receipt = {"format": "swdb.typed-library-profile-driver.v1", "stage": args.stage, "started": now(),
        "approval_reference": args.approval_reference, "host": socket.gethostname(), "lane": lane,
        "source_snapshot": source["id"], "source_sha256": source["artifact"]["sha256"],
        "workload": workload["id"], "workload_sha256": workload["identity_sha256"],
        "threads": args.threads, "build_parallel_jobs": 1, "state": "running", "gain_claim": False}
    receipt["preflight"] = dispatch_preflight.check(args.runs_dir, lane,
        storage_bytes=4*dispatch_preflight.GIB, memory_bytes=8*dispatch_preflight.GIB)
    suffix = "" if args.stage == "profile" else f"-a{args.annotation_attempt}"
    folder = artifacts.external_directory(args.runs_dir)/(args.id+".driver-"+args.stage+suffix)
    folder.mkdir(exist_ok=False)
    receipt["host_observation"] = host_observation.capture(folder, PROJECT)
    receipt["runtime_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT, text=True).strip()
    receipt["runtime_branch"] = subprocess.check_output(["git", "branch", "--show-current"], cwd=PROJECT, text=True).strip()
    receipt["tracked_changes"] = subprocess.check_output(["git", "status", "--short", "--untracked-files=no"], cwd=PROJECT, text=True).splitlines()
    receipt_path = folder/"driver.json"
    save(receipt_path, receipt)
    temporary = folder/"tmp";temporary.mkdir()
    environment = {**os.environ, "TMPDIR": str(temporary), "MAKEFLAGS": "-j4", "CMAKE_BUILD_PARALLEL_LEVEL": "4",
        "OMP_THREAD_LIMIT": "16", "OMP_WAIT_POLICY": "PASSIVE", "GOMP_SPINCOUNT": "0"}
    environment.pop("GOMP_CPU_AFFINITY", None)
    def interrupted(signum, frame):
        raise InterruptedError("driver interrupted by signal " + str(signum))
    previous = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGINT, signal.SIGTERM)}
    try:
        receipt["result"] = (profile_stage(args, folder, lane, environment) if args.stage == "profile" else
                              annotate_stage(args, folder, environment))
        receipt.update(state="complete", finished=now())
    except BaseException as error:
        receipt.update(state="failed", finished=now(), reason=str(error))
        raise
    finally:
        save(receipt_path, receipt)
        for signum, handler in previous.items():
            signal.signal(signum, handler)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Failure, OSError, ValueError, KeyError, InterruptedError) as error:
        print("typed-library-profile-driver: " + str(error), file=sys.stderr)
        raise SystemExit(1)
