"""Proof workers in a socket lane: `swdb prove-lane` (Probata proof of concept ticket 57).

Created: 2026-10-14 ET. Design: `.scratch/formal-verification-2026-10-09/spec.md` ("Providers and
machines", "Evaluation design", O9); map decisions 23 item 6, 26 items 5-6, 19 item 8.
Format: docs/reference/format-v0.4-proof.md ("Proof workers in a socket lane").

One lane job runs one batch plan: up to 6 workers, each pinned to its own physical core of the lane's
socket and watched by an 8 GB RSS watchdog (swdb.rss_watchdog). A job is either
- a `prove` job: one `swdb prove` call (an adapter exists); its proof record's job block is filled
  here (worker core = the pinned core, peak RSS = the worker watchdog's reading), or
- a `tool` job: a verifier with no adapter yet, run under the same worker wrapper; its result file
  holds the same job block (adapter `none`) and a verdict read from the tool's exit code and output.

- `swdb prove-lane leases`: the states of both socket leases and the legacy lease, before dispatch.
- `swdb prove-lane run <plan>`: the batch, inside the lane (`scripts/mbit10/prove_in_lane.sh`).
  On a machine that requires lanes it refuses unless socket_lane.sh started it and holds the lease
  (swdb.profile._verified_lane), and unless a lease check is given.
- `swdb prove-lane compare <batch.json> <batch.json>`: do the verdicts of two batches match
  (a batch against the same jobs run alone)?

Configurations under comparison are interleaved: a plan whose order is not interleaved (some prefix
holds one configuration twice more than another) is reordered round-robin, and the batch record
keeps the order given.
"""

import datetime
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from swdb import paths, rss_watchdog, yamlio
from swdb.cli import Failure, UsageError

PLAN_FORMAT = "proof_lane_batch.1"
MAX_WORKERS = 6                       # LR-07 and ticket 57: at most 6 workers in one lane
DEFAULT_TIMEOUT_SECONDS = 3600
WORKER_CAP_ENV = "SWDB_WORKER_RSS_CAP_BYTES"
CPU_SYSFS = Path("/sys/devices/system/cpu")
NODE_SYSFS = Path("/sys/devices/system/node")


# --- CLI ----------------------------------------------------------------------------------------

def register_cli(commands):
    lane = commands.add_parser("prove-lane", help="proof workers in a socket lane (mbit10): lease check, batch, compare")
    actions = lane.add_subparsers(dest="lane_command", required=True)

    sub = actions.add_parser("leases", help="record the states of both socket leases and the legacy lease")
    sub.add_argument("--host", default="mbit10")
    sub.add_argument("--node", type=int, required=True, help="the lane the batch will use")
    sub.add_argument("--out", type=Path, help="write the lease check here (JSON)")
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(analytic_handler=leases)

    sub = actions.add_parser("run", help="run a batch plan inside a socket lane, up to 6 pinned workers")
    sub.add_argument("plan", type=Path)
    sub.add_argument("--records", type=Path, default=paths.RECORDS)
    sub.add_argument("--runs-dir", type=Path, required=True, help="raw output folder outside the repo")
    sub.add_argument("--lease-check", type=Path, help="the output of `swdb prove-lane leases` (required in a lane)")
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(analytic_handler=run)

    sub = actions.add_parser("compare", help="do two batches give the same verdict for every job?")
    sub.add_argument("first", type=Path)
    sub.add_argument("second", type=Path)
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(analytic_handler=compare)


# --- leases ---------------------------------------------------------------------------------------

def leases(args):
    """Both socket leases and the legacy one; refuse (exit 1) when this lane's or the legacy lease is held."""
    root = paths.lease_root()
    names = [f"{args.host}-evaluation-node0", f"{args.host}-evaluation-node1", f"{args.host}-evaluation"]
    states, details = {}, {}
    for name in names:
        try:
            meta = json.loads((root / f"{name}.meta.json").read_text())
        except (OSError, ValueError) as exc:
            raise Failure(f"cannot read lease metadata {root / (name + '.meta.json')}: {exc}") from None
        states[name] = meta.get("state")
        lease = meta.get("lease") or {}
        details[name] = {"generation": lease.get("generation"), "acquired_at": lease.get("acquired_at"),
                         "released_at": meta.get("released_at"), "holder_pid": lease.get("daemon_pid")}
    check = {"checked": _now(), "lease_root": str(root), "node": args.node, "states": states, "details": details}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(check, indent=1) + "\n")
    own, legacy = names[args.node], names[2]
    if states[own] == "held":
        raise Failure(f"lease {own} is held; pick the other lane or wait")
    if states[legacy] == "held":
        raise Failure(f"the legacy lease {legacy} is held: it occupies a socket, and a third job is never added")
    return check


# --- the plan ---------------------------------------------------------------------------------------

def load_plan(path):
    try:
        plan = yamlio.load(path)
    except (OSError, ValueError) as exc:
        raise UsageError(f"cannot read the batch plan {path}: {exc}") from None
    if not isinstance(plan, dict) or plan.get("plan") != PLAN_FORMAT:
        raise UsageError(f"{path} is not a batch plan (plan: {PLAN_FORMAT})")
    jobs = plan.get("jobs") or []
    if not jobs:
        raise UsageError(f"batch plan {path} has no jobs")
    for number, job in enumerate(jobs, start=1):
        if not job.get("configuration") or not job.get("subject"):
            raise UsageError(f"job {number} of {path} needs a configuration and a subject")
        if ("prove" in job) == ("tool" in job):
            raise UsageError(f"job {number} of {path} is either a prove job or a tool job")
        if "tool" in job and not job["tool"].get("command"):
            raise UsageError(f"tool job {number} of {path} has no command")
        if "prove" in job and {"--batch", "--position", "--runs-dir", "--records"} & set(map(str, job["prove"])):
            raise UsageError(f"prove job {number} of {path}: the batch sets --batch, --position, --runs-dir, --records")
    workers = plan.get("workers", MAX_WORKERS)
    if not isinstance(workers, int) or workers < 1 or workers > MAX_WORKERS:
        raise UsageError(f"batch plan {path} asks for {workers} workers: a lane runs at most {MAX_WORKERS}, "
                         "each on its own physical core")
    return plan


def interleaved(order):
    """True when every prefix holds each configuration at most once more than any other."""
    configs = sorted(set(order))
    counts = dict.fromkeys(configs, 0)
    for config in order:
        counts[config] += 1
        if max(counts.values()) - min(counts.values()) > 1:
            return False
    return True


def interleave(jobs):
    """The jobs in round-robin order of configuration (each configuration keeps its own order)."""
    by = {}
    for job in jobs:
        by.setdefault(job["configuration"], []).append(job)
    out, lanes = [], list(by.values())
    while any(lanes):
        for lane in lanes:
            if lane:
                out.append(lane.pop(0))
    return out


# --- cores and the lane ---------------------------------------------------------------------------

def _cpu_list(text):
    cpus = set()
    for part in text.strip().split(","):
        if "-" in part:
            lo, hi = part.split("-")
            cpus.update(range(int(lo), int(hi) + 1))
        elif part.strip():
            cpus.add(int(part))
    return cpus


def physical_cores(allowed, sysfs=CPU_SYSFS):
    """One logical CPU per physical core among `allowed` (the lowest of each sibling set)."""
    seen, cores = set(), []
    for cpu in sorted(allowed):
        siblings = frozenset(_cpu_list((Path(sysfs) / f"cpu{cpu}" / "topology" / "thread_siblings_list").read_text()))
        if siblings & seen:
            continue
        seen |= siblings
        cores.append(cpu)
    return cores


def _lane(store, plan, lease_check):
    """(lane description, node, the CPUs workers may use) after the lane check; refuse outside the lane."""
    from swdb.profile import _verified_lane, lane_required
    machine = store.get(plan.get("machine") or "", "machine")
    if machine is None:
        raise Failure(f"the batch plan names machine {plan.get('machine')!r}, which is not a machine record")
    described = _verified_lane(machine, None) or "no lane: the machine record requires none"
    if lane_required(machine) and lease_check is None:
        raise Failure(f"machine {machine['id']!r} requires a socket lane: pass --lease-check (the output of "
                      "`swdb prove-lane leases`, taken before dispatch), as scripts/mbit10/prove_in_lane.sh does")
    if not hasattr(os, "sched_getaffinity"):
        return described, None, None
    allowed = set(os.sched_getaffinity(0))
    nodes = [n["node"] for n in machine.get("numa_nodes", []) if _cpu_list(str(n["cpus"])) == allowed]
    return described, (nodes[0] if len(nodes) == 1 else None), physical_cores(allowed)


# --- the host record ------------------------------------------------------------------------------

def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _node_free(node):
    if node is None:
        return {"not_available": "no NUMA node (this host pins no lane)"}
    try:
        for line in (NODE_SYSFS / f"node{node}" / "meminfo").read_text().splitlines():
            if "MemFree:" in line:
                return {"node": node, "free_bytes": int(line.split()[-2]) * 1024}
    except OSError as exc:
        return {"not_available": str(exc)}
    return {"not_available": "no MemFree line"}


def _sample(node):
    return {"time": _now(), "load1": round(os.getloadavg()[0], 3), "lane_node_free_memory": _node_free(node)}


def _commit():
    def git(*args):
        return subprocess.run(["git", "-C", str(paths.HOME), *args], capture_output=True, text=True).stdout.strip()
    return git("rev-parse", "HEAD"), bool(git("status", "--porcelain", "--untracked-files=no", "--", "."))


def _df(runs):
    targets = [p for p in ("/data1", "/data") if Path(p).is_dir()] + [str(runs)]
    return subprocess.run(["df", "-h", *targets], capture_output=True, text=True).stdout


# --- the batch ------------------------------------------------------------------------------------

def run(args):
    from swdb.cli import _require_valid
    from swdb.proof import _outside_repo
    plan_path = args.plan.resolve()
    plan = load_plan(plan_path)
    store = _require_valid(args.records)
    lease_check = None
    if args.lease_check is not None:
        lease_check = {"path": str(args.lease_check.resolve()), "sha256": rss_watchdog.sha256(args.lease_check),
                       **json.loads(args.lease_check.read_text())}
    described, node, cores = _lane(store, plan, lease_check)
    runs = _outside_repo(args.runs_dir)
    given = [(job["configuration"], job["subject"]) for job in plan["jobs"]]
    as_given = interleaved([config for config, _subject in given])
    jobs = plan["jobs"] if as_given else interleave(plan["jobs"])
    workers = min(plan.get("workers", MAX_WORKERS), len(jobs))
    if cores is not None and len(cores) < workers:
        raise UsageError(f"the lane has {len(cores)} physical cores; the plan asks for {workers} workers")
    worker_cores = cores[:workers] if cores is not None else [None] * workers
    cap = int(plan.get("rss_cap_bytes", rss_watchdog.DEFAULT_CAP_BYTES))
    batch = plan.get("batch") or f"batch.lane.{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dt%H%M%Sz')}"
    folder = runs / batch
    if folder.exists():
        raise Failure(f"{folder} exists: a batch ID is used once")
    (folder / "jobs").mkdir(parents=True)
    commit, dirty = _commit()
    record = {"batch": batch, "plan": {"path": str(plan_path), "sha256": rss_watchdog.sha256(plan_path)},
              "lane": described, "lane_node": node, "lease_check": lease_check, "workers": workers,
              "worker_cores": [core if core is not None else "unpinned" for core in worker_cores],
              "rss_cap_bytes": cap, "records": str(Path(args.records).resolve()),
              "order": {"interleaved_as_given": as_given, "given": [list(pair) for pair in given]},
              "host": {"host": _host(), "archevolve_commit": commit, "archevolve_dirty": dirty,
                       "df_before": _df(runs), "start": _sample(node)}}
    context = {"plan_dir": plan_path.parent, "records": Path(args.records).resolve(), "folder": folder,
               "batch": batch, "cap": cap, "timeout": int(plan.get("job_timeout_seconds", DEFAULT_TIMEOUT_SECONDS))}
    results = [None] * len(jobs)
    todo = queue.Queue()
    for position, job in enumerate(jobs, start=1):
        todo.put((position, job))

    def worker(core):
        while True:
            try:
                position, job = todo.get_nowait()
            except queue.Empty:
                return
            runner = _prove_job if "prove" in job else _tool_job
            try:
                results[position - 1] = runner(job, position, core, context)
            except Exception as exc:          # one job's failure never stops the other workers
                results[position - 1] = {"configuration": job["configuration"], "subject": job["subject"],
                                         "position": position, "error": f"{type(exc).__name__}: {exc}"}

    threads = [threading.Thread(target=worker, args=(core,)) for core in worker_cores]
    for thread in threads:
        thread.start()
        time.sleep(0.05)                      # start order follows position order
    for thread in threads:
        thread.join()
    record["host"]["end"] = _sample(node)
    record["host"]["load"] = {"start": record["host"]["start"]["load1"], "end": record["host"]["end"]["load1"]}
    record["finished"] = _now()
    record["jobs"] = results
    out = folder / "batch.json"
    out.write_text(json.dumps(record, indent=1) + "\n")
    summary = {"batch": batch, "batch_record": {"path": str(out), "sha256": rss_watchdog.sha256(out)},
               "order": record["order"], "workers": workers, "jobs": results}
    errors = [job for job in results if job.get("error")]
    if errors:
        raise Failure(f"{len(errors)} job(s) of batch {batch} wrote no result: " +
                      "; ".join(f"position {job['position']}: {job['error']}" for job in errors) +
                      f". Batch record: {out}")
    return summary


def _host():
    from swdb.proof import _host
    return _host()


def _pin(core):
    def setup():
        if core is not None:
            os.sched_setaffinity(0, {core})
    return setup


def _prove_job(job, position, core, ctx):
    """One `swdb prove` call, pinned to `core`, under the worker watchdog (inside `swdb prove`)."""
    command = [sys.executable, "-m", "swdb", "prove", *map(str, job["prove"]), "--records", str(ctx["records"]),
               "--runs-dir", str(ctx["folder"] / "prove"), "--batch", ctx["batch"], "--position", str(position),
               "--format", "json"]
    env = dict(os.environ, PYTHONPATH=str(paths.HOME), **{WORKER_CAP_ENV: str(ctx["cap"])})
    done = subprocess.run(command, cwd=ctx["plan_dir"], env=env, capture_output=True, text=True,
                          preexec_fn=_pin(core), timeout=ctx["timeout"])
    out = {"configuration": job["configuration"], "subject": job["subject"], "position": position, "kind": "prove"}
    if done.returncode != 0:
        out["error"] = f"swdb prove exited {done.returncode}: {done.stderr.strip()[-2000:]}"
        return out
    written = json.loads(done.stdout)
    record = written["record"]
    out.update(record=record["id"], path=written["path"], verdict=record.get("verdict"),
               failure_class=record.get("failure_class"), job=record["job"])
    return out


def _tool_job(job, position, core, ctx):
    """A verifier with no adapter yet, under the same worker wrapper: pinned, watched, timed."""
    tool = job["tool"]
    base = ctx["folder"] / "jobs"
    scratch, log = base / f"{position}.scratch", base / f"{position}.log"
    scratch.mkdir()
    for item in tool.get("inputs") or []:
        source = (ctx["plan_dir"] / item).resolve()
        (shutil.copytree if source.is_dir() else shutil.copy2)(source, scratch / source.name)
    env = dict(os.environ, **{key: str(value) for key, value in (tool.get("env") or {}).items()})
    load = os.getloadavg()[0]
    try:
        result = rss_watchdog.run([str(part) for part in tool["command"]], log=log, cap_bytes=ctx["cap"],
                                  timeout=tool.get("timeout_seconds", ctx["timeout"]), cwd=scratch, env=env,
                                  core=core, address_space_cap=ctx["cap"] if tool.get("address_space_cap") else None)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)                 # verifier scratch: gone when the job ends
    verdict = _read_verdict(tool, result, log.read_text(errors="replace"))
    out = {"configuration": job["configuration"], "subject": job["subject"], "position": position, "kind": "tool",
           **verdict, "bounds": tool.get("bounds") or {"threads": 1},
           "address_space_cap": bool(tool.get("address_space_cap")), "exit_code": result.exit_code,
           "log": {"path": str(log), "sha256": rss_watchdog.sha256(log)},
           "job": {"adapter": "none", "host": _host(), "worker_core": core if core is not None else "unpinned",
                   "wall_seconds": round(result.wall_seconds, 6), "cpu_seconds": round(result.cpu_seconds, 6),
                   "batch_load": {"start": round(load, 3), "end": round(os.getloadavg()[0], 3)},
                   "peak_rss_bytes": int(result.peak_rss_bytes), "batch": ctx["batch"], "position": position}}
    (base / f"{position}.json").write_text(json.dumps(out, indent=1) + "\n")
    return out


def _read_verdict(tool, result, output):
    """The tool's verdict: the watchdog first, then the first `verdicts` entry whose exit code and
    output pattern match; else not proven (`tool_crash` on a signal, `unknown` otherwise)."""
    if result.out_of_memory:
        return {"verdict": "not_proven", "failure_class": "out_of_memory"}
    if result.timed_out:
        return {"verdict": "not_proven", "failure_class": "timeout"}
    for rule in tool.get("verdicts") or []:
        if "exit" in rule and rule["exit"] != result.exit_code:
            continue
        if rule.get("output") and not re.search(rule["output"], output, re.MULTILINE):
            continue
        found = {"verdict": rule["verdict"]}
        if rule["verdict"] == "refuted":
            pattern = rule.get("counterexample") or rule.get("output") or "."
            found["counterexample"] = {"output_lines": [line for line in output.splitlines()
                                                        if re.search(pattern, line)][:20]}
        elif rule["verdict"] == "not_proven":
            found["failure_class"] = rule.get("failure_class", "unknown")
        return found
    return {"verdict": "not_proven", "failure_class": "tool_crash" if result.exit_code < 0 else "unknown"}


# --- compare --------------------------------------------------------------------------------------

def compare(args):
    """Every (configuration, subject) of the first batch has the same verdict in the second."""
    def verdicts(path):
        data = json.loads(Path(path).read_text())
        return {(job["configuration"], job["subject"]): (job.get("verdict"), job.get("failure_class"))
                for job in data["jobs"]}
    first, second = verdicts(args.first), verdicts(args.second)
    keys = sorted(set(first) | set(second))
    differ = [f"{c} {s}: {first.get((c, s))} vs {second.get((c, s))}" for c, s in keys
              if (first.get((c, s)) or (None,))[0] != (second.get((c, s)) or (None,))[0]]
    if differ:
        raise Failure("verdicts differ: " + "; ".join(differ))
    return {"matching": len(keys), "first": str(args.first), "second": str(args.second),
            "verdicts": [{"configuration": c, "subject": s, "verdict": first[(c, s)][0],
                          "failure_class": first[(c, s)][1]} for c, s in keys]}
