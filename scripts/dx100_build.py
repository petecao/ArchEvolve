#!/usr/bin/env python3
"""Bounded, lane-confined DX100 BFS build helper. Updated: 2026-09-25.

Receipts are build evidence only. This helper never runs a BFS measurement.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import time


REVISION = "e4fc4afdf894f295442cef3604667a469fab8e62"


def save(path, data):
    temporary = path.with_suffix(".pending")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def output(command, cwd=None):
    return subprocess.check_output(command, cwd=cwd, text=True, timeout=30).strip()


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def disk_usage_kib(path):
    """Account for an active build tree, retaining harmless unlink races."""
    result = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True,
                            timeout=30, env=dict(os.environ, LC_ALL="C"))
    warnings = result.stderr.splitlines()
    vanished = (result.returncode == 1 and warnings and all(
        re.fullmatch(r"du: cannot access '.+': No such file or directory", line) for line in warnings))
    if result.returncode and not vanished:
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    fields = result.stdout.strip().split(maxsplit=1)
    if len(fields) != 2 or fields[1] != str(path):
        raise ValueError("disk monitor did not report the requested directory total")
    return int(fields[0]), warnings


def group_rss_kib(pgid):
    total = 0
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            stat = (entry / "stat").read_text()
            fields = stat[stat.rfind(")") + 2:].split()
            if int(fields[2]) == pgid:
                total += int(fields[21]) * os.sysconf("SC_PAGE_SIZE") // 1024
        except (OSError, ValueError, IndexError):
            continue  # Process exited during the snapshot.
    return total


def stop(process):
    if process is not None and process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        except ProcessLookupError:
            process.wait()


def interrupted(signum, frame):
    raise InterruptedError(f"build interrupted by signal {signum}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lane", type=int, choices=[0, 1], required=True)
    parser.add_argument("--jobs", type=int, choices=range(1, 9), default=8)
    parser.add_argument("--wall-seconds", type=int, default=7200)
    parser.add_argument("--memory-gib", type=int, default=48)
    parser.add_argument("--storage-gib", type=int, default=10)
    args = parser.parse_args()
    source, directory = args.source.resolve(), args.output.resolve()
    if platform.system() != "Linux" or platform.node().split(".")[0] != "mbit10":
        parser.error("this build must run on mbit10")
    if not source.is_relative_to("/data1/yanruj"):
        parser.error("source/build must remain under /data1/yanruj")
    if not any(directory.is_relative_to(root) for root in (
            "/data1/yanruj/EvolveSWDB_runs", "/data/yanruj/EvolveSWDB_runs")):
        parser.error("raw build evidence requires an EvolveSWDB_runs directory")
    if not 1 <= args.wall_seconds <= 7200 or not 1 <= args.memory_gib <= 48 or not 1 <= args.storage_gib <= 10:
        parser.error("build bounds cannot exceed 7200 seconds, 48 GiB memory, or 10 GiB storage")
    if directory.exists():
        parser.error("output directory already exists; preserve prior attempts and use a fresh directory")
    lease_name = f"mbit10-evaluation-node{args.lane}"
    lease = json.loads(Path(f"/data1/yanruj/lact-host-lease/{lease_name}.meta.json").read_text())
    allowed = next(line.split(":", 1)[1].strip() for line in Path("/proc/self/status").read_text().splitlines()
                   if line.startswith("Cpus_allowed_list:"))
    expected = Path(f"/sys/devices/system/node/node{args.lane}/cpulist").read_text().strip()
    policy = Path("/proc/self/numa_maps").read_text().splitlines()[0].split()[1]
    if (os.environ.get("LACT_LEASE_NAME") != lease_name or lease.get("state") != "held"
            or allowed != expected or policy != f"bind:{args.lane}"):
        parser.error("a held socket_lane.sh lease and matching CPU/memory confinement are required")
    if output(["git", "rev-parse", "HEAD"], source) != REVISION:
        parser.error("DX100 checkout does not match the pinned model revision")
    if output(["git", "diff", "--name-only", "HEAD"], source):
        parser.error("tracked model source differs from the pinned revision")
    directory.mkdir(parents=True)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    receipt_path = directory / "build-receipt.json"
    start = time.monotonic()
    receipt = {"version": "1.0", "classification": "build_only", "revision": REVISION,
               "source": str(source), "host": platform.node(), "lane": args.lane,
               "lease": lease, "started_unix": time.time(), "state": "running",
               "limits": {"wall_seconds": args.wall_seconds, "memory_gib": args.memory_gib,
                          "storage_gib": args.storage_gib, "raw_storage_gib": 2, "jobs": args.jobs}, "stages": [],
               "environment": {"uname": platform.uname()._asdict(),
                   "compiler": output(["g++-13", "--version"]),
                   "python": output(["python3", "--version"]),
                   "scons": output(["scons", "--version"]),
                   "disks": output(["df", "-h", "/data1", "/data"]),
                   "load": Path("/proc/loadavg").read_text().strip()}}
    save(receipt_path, receipt)
    env = dict(os.environ, TMPDIR=str(source / ".tmp"), XDG_CACHE_HOME=str(source / ".cache"))
    Path(env["TMPDIR"]).mkdir(exist_ok=True)
    Path(env["XDG_CACHE_HOME"]).mkdir(exist_ok=True)
    ramulator = source / "ext/ramulator2/ramulator2"
    stages = [
        ("ramulator-configure", ["cmake", "-S", str(ramulator), "-B", str(ramulator / "build"),
            "-G", "Unix Makefiles", "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_C_COMPILER=gcc-13", "-DCMAKE_CXX_COMPILER=g++-13"]),
        ("ramulator-build", ["cmake", "--build", str(ramulator / "build"), "--target", "ramulator", "--parallel", str(args.jobs)]),
        ("m5ops-build", ["scons", "-C", "util/m5", "build/x86/out/m5", f"-j{args.jobs}"]),
        ("gem5-configure", ["scons", "defconfig", "build/X86", "build_opts/X86"]),
        ("gem5-prune-unused-components", ["scons", "setconfig", "build/X86", "RUBY=n", "USE_SYSTEMC=n"]),
        ("gem5-build", ["scons", "build/X86/gem5.opt", f"-j{args.jobs}", "CXX=g++-13", "CC=gcc-13"]),
        ("bfs-build", ["make", "-C", "benchmarks/gapbs", f"-j{min(args.jobs, 4)}", "CXX=g++-13",
            "CXX_FLAGS=-std=c++11 -O3 -Wall -g3 -fopenmp -DGEM5", "bfs", "bfs_maa", "bfs_maa_1K", "converter"]),
    ]
    for name, command in stages:
        stage = {"name": name, "command": command, "state": "running", "peak_group_rss_kib": 0,
                 "log": str(directory / f"{name}.log"), "started_unix": time.time()}
        receipt["stages"].append(stage)
        save(receipt_path, receipt)
        reason = None
        next_disk_check = 0
        process = None
        try:
            with Path(stage["log"]).open("w") as log:
                process = subprocess.Popen(command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=True)
                while process.poll() is None:
                    elapsed = time.monotonic() - start
                    rss = group_rss_kib(process.pid)
                    stage["peak_group_rss_kib"] = max(stage["peak_group_rss_kib"], rss)
                    if elapsed >= args.wall_seconds:
                        reason = "wall_time_budget_exhausted"
                    elif rss > args.memory_gib * 1024 * 1024:
                        reason = "memory_budget_exhausted"
                    if time.monotonic() >= next_disk_check:
                        used, warnings = disk_usage_kib(source)
                        stage["source_storage_kib"] = used
                        if warnings:
                            stage.setdefault("storage_monitor_warnings", []).append(warnings)
                        if used > args.storage_gib * 1024 * 1024:
                            reason = "build_storage_budget_exhausted"
                        raw_used, warnings = disk_usage_kib(directory)
                        if warnings:
                            stage.setdefault("storage_monitor_warnings", []).append(warnings)
                        if raw_used > 2 * 1024 * 1024:
                            reason = "raw_storage_budget_exhausted"
                        next_disk_check = time.monotonic() + 30
                    if reason:
                        break
                    save(receipt_path, receipt)
                    time.sleep(2)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            reason = f"build_or_monitor_failure: {exc}"
        finally:
            stop(process)
        returncode = process.returncode if process is not None else None
        stage.update(returncode=returncode, ended_unix=time.time(),
                     state="completed" if returncode == 0 and not reason else "failed")
        if reason:
            stage["reason"] = reason
        save(receipt_path, receipt)
        if stage["state"] != "completed":
            receipt.update(state="failed", ended_unix=time.time(), host_wall_seconds=time.monotonic() - start)
            save(receipt_path, receipt)
            print(json.dumps({"receipt": str(receipt_path), "state": "failed", "stage": name}))
            return 1
    binaries = ["build/X86/gem5.opt", "benchmarks/gapbs/bfs", "benchmarks/gapbs/bfs_maa",
                "benchmarks/gapbs/bfs_maa_1K", "benchmarks/gapbs/converter", "ext/ramulator2/ramulator2/libramulator.so"]
    try:
        receipt["binaries"] = [{"path": str(source / path), "sha256": digest(source / path),
                                "bytes": (source / path).stat().st_size} for path in binaries]
        receipt["dependencies"] = {name: output(["git", "rev-parse", "HEAD"], ramulator / "ext" / name)
                                   for name in ("yaml-cpp", "spdlog", "argparse")}
        receipt["resolved_kconfig"] = (source / "build/X86/gem5.build/config").read_text()
    except (OSError, subprocess.SubprocessError) as exc:
        receipt.update(state="failed", reason=f"build_artifact_identity_failure: {exc}",
                       ended_unix=time.time(), host_wall_seconds=time.monotonic() - start)
        save(receipt_path, receipt)
        print(json.dumps({"receipt": str(receipt_path), "state": "failed", "stage": "artifact-identity"}))
        return 1
    receipt.update(state="completed", ended_unix=time.time(), host_wall_seconds=time.monotonic() - start)
    save(receipt_path, receipt)
    print(json.dumps({"receipt": str(receipt_path), "state": "completed", "classification": "build_only"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
