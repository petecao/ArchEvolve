"""`swdb profile <implementation> <input> <machine>`: build, run, measure, and write a
profile record. Counter-free: timing across thread counts, footprints, index-stream
features, and cachegrind's simulated cache misses.

Steps, each recorded as a `part` with its command and outcome:
  1. build the implementation (and a -g copy for cachegrind) into the run folder;
  2. run the kernel's correctness check once (a failure stops the profile);
  3. the timing sweep: one process per thread count, each running --trials trials, timed
     by the benchmark's own timer;
  4. one single-threaded logging run that counts sweeps per call;
  5. the index-stream feature extractor (tools/index_features), if the implementation
     names an index stream;
  6. cachegrind, single-threaded, with a timeout;
  7. footprints from element size times element count on the input.
Raw output stays in the run folder (outside git). On mbit10 the whole command runs inside
a socket lane (scripts/mbit10/profile_in_lane.sh); this module never starts a job on
another socket by itself.
"""

import datetime
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import socket
import statistics
import subprocess
import time
from pathlib import Path

from swdb import formula, paths, writer, yamlio
from swdb.cli import Failure
from swdb.machine import llc_bytes
from swdb.rules import implementation_symbols, resolve_code
from swdb.store import Store
from swdb.validate import validate_records

TRIAL_TIME = re.compile(r"^Trial Time:\s+([0-9.eE+-]+)\s*$", re.M)
GRAPH_LINE = re.compile(r"^Graph has (\d+) nodes and (\d+) (un)?directed edges", re.M)
STEP_LINE = re.compile(r"^\s*(\d+)\s+([0-9.eE+-]+)\s*$", re.M)

# Bottleneck inference thresholds (counter-free; see _bottleneck).
EFFICIENCY_SCALES = 0.5      # parallel efficiency at the largest thread count
LL_MISS_RATE_LOW = 0.01      # simulated LL misses per data reference


def _now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)


def _stamp(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


class Interrupted(Exception):
    pass


class Run:
    """One profile run: its folder, its log of parts, and the helpers that run commands.

    Children run in their own process group (so a timeout can kill a whole benchmark,
    including shells and valgrind). A SIGTERM, SIGINT, or SIGHUP to swdb kills the running
    child's group before swdb exits, so no benchmark outlives the lane that admitted it."""

    def __init__(self, folder):
        self.folder = folder
        self.parts = []
        self.child = None
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, self._stop)

    def _stop(self, signum, frame):
        self._kill_child()
        raise Interrupted(f"stopped by signal {signal.Signals(signum).name}")

    def _kill_child(self):
        """Kill the child's whole process group (the child leads it), even if the child
        itself has exited but left helpers behind."""
        if self.child is None:
            return
        try:
            os.killpg(self.child.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        self.child.wait()

    def execute(self, part, command, env_extra=None, timeout=None, log_name=None, shell=True):
        """Run one command (a shell string) with its output in log_name. Returns
        (outcome, exit code, output text). Kills the whole process group on timeout."""
        log = self.folder / (log_name or f"{part}.log")
        env = dict(os.environ)
        env.update(env_extra or {})
        started = _now()
        with open(log, "w", encoding="utf-8") as out:
            out.write(f"# command: {command}\n# env: {json.dumps(env_extra or {})}\n# started: {_stamp(started)}\n")
            out.flush()
            proc = subprocess.Popen(command, shell=shell, stdout=out, stderr=subprocess.STDOUT, env=env,
                                    cwd=self.folder, start_new_session=True)
            self.child = proc
            try:
                code = proc.wait(timeout=timeout)
                outcome = "complete" if code == 0 else "failed"
            except subprocess.TimeoutExpired:
                self._kill_child()
                code, outcome = None, "timed_out"
            finally:
                self._kill_child()   # a child that forked helpers into its group leaves none behind
                self.child = None
        text = log.read_text(encoding="utf-8", errors="replace")
        entry = {"part": part, "outcome": outcome, "command": command, "started": _stamp(started),
                 "finished": _stamp(_now()), "timeout_s": timeout, "exit_code": code,
                 "raw_files": [log.name], "note": None}
        return entry, text

    def record(self, entry, note=None, outcome=None, raw=()):
        if note:
            entry["note"] = note if not entry.get("note") else entry["note"] + " " + note
        if outcome:
            entry["outcome"] = outcome
        entry["raw_files"] = list(dict.fromkeys(entry["raw_files"] + list(raw)))
        self.parts.append(entry)
        return entry


def run(args, records_dir):
    try:
        return _run(args, records_dir)
    except Interrupted as exc:
        raise Failure(f"{exc}; the running benchmark was killed and no profile was written") from None


def _run(args, records_dir):
    result = validate_records(records_dir)
    if result.problems:
        raise Failure("records do not validate; run swdb validate first:\n" + "\n".join(map(str, result.problems)))
    store = result.store
    impl = _get(store, args.implementation, "implementation")
    inp = _get(store, args.input, "input")
    machine = _get(store, args.machine, "machine")
    kernel = _get(store, impl["kernel"], "kernel")
    app = store.application_of(impl)
    threads = _threads(args.threads, machine)
    missing = sorted(implementation_symbols(impl, loops=True) - set(inp["properties"]))
    if missing:
        raise Failure(f"input {inp['id']!r} does not define {', '.join(missing)}, which the implementation's "
                      "formulas use; add them (unknown is fine) before profiling")
    if args.trials < 1:
        raise Failure("--trials must be at least 1")
    host = socket.gethostname().split(".")[0]
    if host != machine["hostname"]:
        raise Failure(f"this host is {host!r}, but machine record {machine['id']!r} is for {machine['hostname']!r}")

    started = _now()
    run_id = f"{impl['id']}.{inp['id']}.{machine['id']}.{started.strftime('%Y%m%dt%H%M%Sz')}"
    runs_dir = Path(args.runs_dir).resolve()
    if _inside(runs_dir, paths.HOME) or _inside(runs_dir, Path(records_dir).resolve()):
        raise Failure(f"runs folder {runs_dir} is inside the repo; raw output must stay outside git")
    folder = runs_dir / run_id
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "bin").mkdir()
    r = Run(folder)
    env_info = _environment(folder, args, host, started)

    input_args = _input_args(inp)
    cxx = args.cxx or impl["build"]["compiler"]
    compiler_version = _first_line([cxx, "--version"])
    source, reason = resolve_code(impl["code"][0], records_dir, paths.HOME, app)
    if source is None:
        raise Failure(f"cannot locate the implementation's code: {reason}")
    app_dir = paths.HOME / app["source"]["local_path"] if app["source"].get("local_path") else paths.HOME
    fill = {"cxx": cxx, "flags": impl["build"]["flags"], "source": shlex.quote(str(source)),
            "app": shlex.quote(str(app_dir)), "records": shlex.quote(str(Path(records_dir).resolve()))}

    # 1. build
    binary = folder / "bin" / impl["id"]
    build_cmd = impl["build"]["command"].format(**fill, binary=shlex.quote(str(binary)))
    entry, _ = r.execute("build", build_cmd, timeout=600)
    r.record(entry)
    if entry["outcome"] != "complete":
        raise Failure(f"build failed; see {folder / 'build.log'}")

    run_fill = {"binary": shlex.quote(str(binary)), "input_args": input_args}
    threads_env = impl["run"]["threads_env"]
    bind_env = {"OMP_PLACES": "cores", "OMP_PROC_BIND": "close"}

    # 2. correctness check
    check = kernel["correctness_check"]
    cmd = check["command"].format(**run_fill)
    entry, text = r.execute("correctness", cmd, env_extra={threads_env: str(max(threads)), **bind_env},
                            timeout=args.timeout)
    passed = entry["outcome"] == "complete" and re.search(check["pass_regex"], text) is not None
    r.record(entry, note=f"pass_regex {check['pass_regex']!r} {'matched' if passed else 'did not match'}.")
    if not passed:
        raise Failure(f"the correctness check failed; see {folder / 'correctness.log'}; no profile written")

    # 3. timing sweep
    timing, graph_counts = [], {}
    timing_ok = True
    for t in threads:
        cmd = impl["run"]["command"].format(**run_fill, trials=args.trials)
        entry, text = r.execute("timing", cmd, env_extra={threads_env: str(t), **bind_env}, timeout=args.timeout,
                                log_name=f"timing-t{t}.log")
        times = [float(x) for x in TRIAL_TIME.findall(text)]
        if entry["outcome"] == "complete" and len(times) != args.trials:
            entry["outcome"] = "failed"
            entry["note"] = f"expected {args.trials} Trial Time lines, found {len(times)}"
        r.record(entry, note=f"threads={t}")
        if entry["outcome"] != "complete":
            timing_ok = False
            break
        graph_counts = graph_counts or _graph_counts(text)
        med = statistics.median(times)
        timing.append({"threads": t, "trials": len(times), "times_s": times, "median_s": med,
                       "min_s": min(times), "max_s": max(times),
                       "spread": (max(times) - min(times)) / med if med > 0 else 0.0, "command": cmd})

    # 4. sweeps per call: one step line per sweep (sweep_log_flag), or a printed count (sweep_count_regex)
    sweeps = None
    flag, count_regex = impl["run"].get("sweep_log_flag"), impl["run"].get("sweep_count_regex")
    if (flag or count_regex) and timing_ok:
        cmd = impl["run"]["command"].format(**run_fill, trials=1) + (f" {flag}" if flag else "")
        entry, text = r.execute("sweeps", cmd, env_extra={threads_env: "1", **bind_env}, timeout=args.timeout)
        if count_regex:
            found = [m.group(1) for m in re.finditer(count_regex, text)]
            if found:
                sweeps = int(found[-1])
            how = f"{len(found)} match(es) of {count_regex!r}"
        else:
            steps = [int(m.group(1)) for m in STEP_LINE.finditer(text)]
            sweeps = max(steps) + 1 if steps else None
            how = f"{len(steps)} step lines"
        if entry["outcome"] != "complete":
            sweeps = None   # a partial log is not a measured count
        if sweeps is not None:
            r.record(entry, note=f"{how}; sweeps per call = {sweeps} at 1 thread.")
        else:
            r.record(entry, note=how if entry["outcome"] == "complete" else None,
                     outcome="failed" if entry["outcome"] == "complete" else None)

    # 5. index-stream features
    features = _features(r, args, impl, input_args, cxx, app_dir)

    # 6. cachegrind
    sim = _cachegrind(r, args, impl, fill, run_fill, threads_env)

    # measured input sizes, cross-checked between the benchmark and the extractor
    measured = dict(graph_counts)
    if features:
        g = features["graph"]
        for name, value in (("num_nodes", g["num_nodes"]), ("num_edges_directed", g["num_edges_directed"])):
            if name in measured and measured[name] != value:
                raise Failure(f"{name}: the benchmark printed {measured[name]} but index_features built {value}; "
                              "the two did not build the same graph")
            measured[name] = value
    new_input = _update_input(inp, measured, run_id) if args.update_input == "yes" else None
    values = {k: f.get("value") for k, f in (new_input or inp)["properties"].items()}

    metrics, counts = [], {}
    metrics.append(_metric("host_load_1min", env_info.pop("_load"), "load", "measured", note="os.getloadavg() at start"))
    _timing_metrics(metrics, timing)
    footprint, footprint_exact = _footprints(metrics, impl, values, machine)
    if features:
        _feature_metrics(metrics, features)
    if sim:
        metrics.extend(sim["metrics"])
    _counts(counts, impl, values, features, sweeps, timing, args.trials)

    complete = all(p["outcome"] in {"complete", "skipped"} for p in r.parts)
    bottleneck = _bottleneck(timing if timing_ok else [], footprint, footprint_exact, machine, sim)
    provenance = [{"id": "run", "kind": "agent_run" if args.agent else "measurement",
                   "description": f"swdb profile run {run_id} on {host}, started {_stamp(started)} (UTC).",
                   "uri": None}]
    env_info["finished"] = _stamp(_now())
    swdb_commit, dirty = _git_state()
    record = {
        "kind": "profile", "schema_version": "0.2", "id": run_id, "status": "draft", "deprecated_by": None,
        "created": writer.today(), "updated": writer.today(), "provenance": provenance,
        "implementation": impl["id"], "input": inp["id"], "machine": machine["id"], "complete": complete,
        "build": {"compiler": cxx, "compiler_version": compiler_version, "flags": impl["build"]["flags"],
                  "command": build_cmd, "application_commit": app["source"]["commit"],
                  "swdb_commit": swdb_commit, "swdb_dirty": dirty},
        "environment": env_info,
        "runs_folder": {"host": host, "path": str(folder), "note": args.runs_note},
        "parts": r.parts, "timing": timing, "counts": counts, "metrics": metrics, "bottleneck": bottleneck,
        "notes": [f"Raw output is in {folder} on {host}; it is not in git."],
        "extensions": {},
    }
    if args.agent:
        writer.mark_agent(record, "agent")
    (folder / "profile.yaml").write_text(yamlio.dumps(record), encoding="utf-8")
    written = writer.commit(records_dir, new=[record], replace=[new_input] if new_input else [])
    return ", ".join(written)


# --- helpers ------------------------------------------------------------------------

def _get(store, record_id, kind):
    found = store.get(record_id, kind)
    if found is None:
        raise Failure(f"{kind} {record_id!r} does not exist")
    return found


def _evaluate(text, values):
    try:
        return formula.evaluate(text, values)
    except formula.FormulaError as exc:
        raise Failure(str(exc)) from None


def _inside(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _threads(text, machine):
    try:
        threads = [int(x) for x in text.split(",") if x.strip()]
    except ValueError:
        raise Failure(f"--threads must be comma-separated integers, got {text!r}") from None
    limit = machine["cpu"]["cores_per_socket"]
    if not threads or min(threads) < 1 or max(threads) > limit:
        raise Failure(f"thread counts must be between 1 and {limit} (the cores of one socket of {machine['id']})")
    if 1 not in threads:
        raise Failure("the timing sweep must include 1 thread (speedup and efficiency are relative to it)")
    return sorted(set(threads))


def _input_args(inp):
    if inp.get("generator"):
        return inp["generator"]["arguments"]
    path = Path(inp["file"]["path"])
    if not path.is_absolute():
        path = paths.HOME / path
    if not path.is_file():
        raise Failure(f"input file {path} does not exist on this host")
    with open(path, "rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    if digest != inp["file"]["sha256"]:
        raise Failure(f"input file {path} has sha256 {digest}, not the recorded {inp['file']['sha256']}")
    return f"-f {shlex.quote(str(path))} {inp['file'].get('arguments', '')}".strip()


def _first_line(argv):
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        return (done.stdout or done.stderr).strip().splitlines()[0]
    except (OSError, subprocess.TimeoutExpired, IndexError):
        raise Failure(f"cannot run {' '.join(argv)}") from None


def _read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def _environment(folder, args, host, started):
    """Record the host state (the no-sudo measurement protocol) and return the environment fields."""
    load = os.getloadavg()[0]
    who = subprocess.run(["who"], capture_output=True, text=True).stdout
    users = sorted({line.split()[0] for line in who.splitlines() if line.strip()})
    numactl = None
    if shutil.which("numactl"):
        numactl = subprocess.run(["numactl", "--show"], capture_output=True, text=True).stdout.strip() or None
    lines = [f"uptime: {subprocess.run(['uptime'], capture_output=True, text=True).stdout.strip()}",
             f"users: {' '.join(users)}"]
    for cmd in (["df", "-h", str(folder)], ["lscpu"], ["numactl", "--hardware"], ["uname", "-a"]):
        if shutil.which(cmd[0]):
            lines.append(f"$ {' '.join(cmd)}\n" + subprocess.run(cmd, capture_output=True, text=True).stdout.strip())
    (folder / "host-state.txt").write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    binding = args.binding
    if binding is None:
        cpus = re.search(r"physcpubind:\s*(.*)", numactl or "")
        mems = re.search(r"membind:\s*(.*)", numactl or "")
        binding = "OMP_PLACES=cores OMP_PROC_BIND=close" + (
            f"; cpus {cpus.group(1).strip()}; memory nodes {mems.group(1).strip()}" if cpus and mems else
            "; process not bound by numactl")
    return {"host": host, "binding": binding, "omp_places": "cores", "omp_proc_bind": "close",
            "numactl_show": numactl, "lane": args.lane, "load_1min": round(load, 2), "users": users,
            "governor": _read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"),
            "no_turbo": _read("/sys/devices/system/cpu/intel_pstate/no_turbo"),
            "started": _stamp(started), "finished": None, "_load": round(load, 2)}


def _git_state():
    try:
        head = subprocess.run(["git", "-C", str(paths.HOME), "rev-parse", "HEAD"], capture_output=True, text=True)
        status = subprocess.run(["git", "-C", str(paths.HOME), "status", "--porcelain", "--untracked-files=no"],
                                capture_output=True, text=True)
        if head.returncode != 0:
            return None, None
        return head.stdout.strip(), bool(status.stdout.strip())
    except OSError:
        return None, None


def _graph_counts(text):
    match = GRAPH_LINE.search(text)
    if not match:
        return {}
    nodes, edges, undirected = int(match.group(1)), int(match.group(2)), match.group(3) is not None
    counts = {"num_nodes": nodes, "num_edges_directed": 2 * edges if undirected else edges}
    if undirected:
        counts["num_edges_undirected"] = edges
    return counts


def _update_input(inp, measured, run_id):
    """A copy of the input with measured sizes filled in, or None if nothing changes.
    A measured value that disagrees with an earlier measured value is an error."""
    if not measured:
        return None
    new = json.loads(json.dumps(inp))
    pid = "measured-sizes"
    changed = False
    for name, value in measured.items():
        fact = new["properties"].get(name)
        if fact and fact["basis"] == "measured":
            if fact["value"] != value:
                raise Failure(f"input {inp['id']}: {name} was measured as {fact['value']} before, now {value}")
            continue
        if fact and fact["basis"] == "code_reading" and fact["value"] == value:
            continue
        if fact and fact["basis"] == "code_reading" and fact["value"] != value:
            raise Failure(f"input {inp['id']}: {name} is {fact['value']} by code reading but measured {value}")
        new["properties"][name] = {"value": value, "basis": "measured", "evidence_refs": [pid],
                                   "note": f"Measured by swdb profile run {run_id} (the benchmark's 'Graph has' "
                                           "line and, when run, index_features)."}
        changed = True
    if not changed:
        return None
    if not any(p["id"] == pid for p in new["provenance"]):
        new["provenance"].append({"id": pid, "kind": "measurement",
                                  "description": f"Sizes of the built graph, first measured by swdb profile run {run_id}.",
                                  "uri": None})
    new["updated"] = writer.today()
    return new


def _metric(name, value, unit, basis, threads=None, array=None, scope=None, tool=None, note=None):
    m = {"name": name, "value": value, "unit": unit, "basis": basis}
    for key, val in (("threads", threads), ("array", array), ("scope", scope), ("tool", tool), ("note", note)):
        if val is not None:
            m[key] = val
    m["evidence_refs"] = ["run"]
    return m


def _timing_metrics(metrics, timing):
    base = next((t["median_s"] for t in timing if t["threads"] == 1), None)
    for t in timing:
        n = t["threads"]
        for name, key in (("time_per_trial_median", "median_s"), ("time_per_trial_min", "min_s"),
                          ("time_per_trial_max", "max_s")):
            metrics.append(_metric(name, t[key], "s", "measured", threads=n, scope="per_trial",
                                   tool="benchmark timer", note=f"over {t['trials']} trials"))
        metrics.append(_metric("time_per_trial_spread", round(t["spread"], 6), "ratio", "measured", threads=n,
                               scope="per_trial"))
        if base and t["median_s"] > 0:
            speedup = base / t["median_s"]
            metrics.append(_metric("speedup", round(speedup, 6), "ratio", "measured", threads=n))
            metrics.append(_metric("parallel_efficiency", round(speedup / n, 6), "ratio", "measured", threads=n))


def _footprints(metrics, impl, values, machine):
    """Per-array bytes = element_bytes * element_count on the input. On an undirected input an
    array and its undirected_alias are one memory, counted once. Returns (total, exact):
    exact is False when some array's size is unknown, and then the total is a lower bound."""
    arrays, conditional, pairs = {}, set(), set()
    for p in impl["access_patterns"]:
        for s in p["steps"]:
            name = s["array"]["name"]
            arrays.setdefault(name, s["array"])
            if s["array"].get("undirected_alias"):
                pairs.add(frozenset((name, s["array"]["undirected_alias"])))
            if p.get("condition"):
                conditional.add(name)
    undirected = values.get("directed") is False
    same_as = {}   # on an undirected input, each array of a pair names its partner
    for pair in pairs:
        if len(pair) == 2 and pair <= set(arrays):
            a, b = sorted(pair)
            same_as[a], same_as[b] = b, a
    total, unknown, counted = 0, [], set()
    for name, a in arrays.items():
        text = a.get("element_count")
        count = _evaluate(text, values) if text is not None else None
        if count is None:
            unknown.append(name)
            why = f"element count {text} is unknown for this input" if text else "its size depends on the data at run time"
            metrics.append(_metric("footprint_bytes", None, "B", "unknown", array=name, note=why))
            continue
        size = count * a["element_bytes"]
        alias = same_as.get(name)
        shared = undirected and alias in counted
        note = f"{a['element_bytes']} B x ({text} = {count})"
        if shared:
            note += f"; the same memory as {alias} on this undirected input, counted once"
        if name in conditional:
            note += "; used only by a conditional access pattern"
        metrics.append(_metric("footprint_bytes", size, "B", "inferred", array=name, note=note))
        if not shared:
            total += size
            counted.add(name)
    llc = llc_bytes(machine)
    exact = not unknown
    what = "sum over distinct arrays of the implementation's access patterns"
    if not exact:
        what = f"lower bound: excludes arrays of unknown size ({', '.join(unknown)})"
    if conditional:
        what += f"; includes arrays used only conditionally ({', '.join(sorted(conditional))})"
    metrics.append(_metric("total_footprint_bytes", total, "B", "inferred", note=what))
    metrics.append(_metric("footprint_llc_ratio", round(total / llc, 6), "ratio", "inferred",
                           note=f"last-level cache of one socket: {llc} B" + ("" if exact else "; a lower bound")))
    return total, exact


def _features(r, args, impl, input_args, cxx, app_dir):
    stream = impl["run"].get("index_stream")
    if args.features == "no" or (args.features == "auto" and not stream):
        return None
    if not stream:
        raise Failure("--features yes, but the implementation names no index stream (run.index_stream)")
    pattern = next(p for p in impl["access_patterns"] if p["id"] == stream["pattern"])
    element_bytes = pattern["steps"][-1]["array"]["element_bytes"]
    tool_src = paths.HOME / "tools" / "index_features" / "index_features.cc"
    tool = r.folder / "bin" / "index_features"
    openmp = " -fopenmp" if "-fopenmp" in impl["build"]["flags"] else ""
    build = (f"{cxx} -std=c++11 -O3 -Wall{openmp} -I {shlex.quote(str(app_dir / 'src'))} "
             f"{shlex.quote(str(tool_src))} -o {shlex.quote(str(tool))}")
    entry, _ = r.execute("index_features", build, timeout=600, log_name="index_features-build.log")
    if entry["outcome"] != "complete":
        r.record(entry, note="building the extractor failed")
        return None
    out = r.folder / "index_features.json"
    cmd = (f"{shlex.quote(str(tool))} --order {stream['order']} --element-bytes {element_bytes} --line-bytes 64 "
           f"--out {shlex.quote(str(out))} -- {input_args}")
    entry2, _ = r.execute("index_features", cmd, timeout=args.features_timeout, env_extra={"OMP_NUM_THREADS": "1"})
    entry2["raw_files"] = [entry["raw_files"][0]] + entry2["raw_files"]
    if entry2["outcome"] != "complete" or not out.exists():
        r.record(entry2, note="the extractor did not finish or wrote no output; its features are missing",
                 outcome="failed" if entry2["outcome"] == "complete" else None)
        return None
    r.record(entry2, note=f"built with {cxx} (the kernel's compiler, so Kronecker IDs match); pattern {pattern['id']}",
             raw=[out.name])
    data = json.loads(out.read_text())
    data["_pattern"] = pattern
    return data


def _feature_metrics(metrics, f):
    tool = f"index_features v{f['tool_version']} ({f['order']})"
    target = f["_pattern"]["steps"][-1]["array"]["name"]
    common = dict(tool=tool, scope="per_sweep", array=target)
    metrics.append(_metric("index_stream_length", f["stream_length"], "count", "measured", **common))
    for name in ("duplicate_ratio", "sequential_fraction", "same_line_fraction"):
        metrics.append(_metric(name, f[name], "ratio", "measured", **common))
    metrics.append(_metric("reuse_distance_histogram", f["reuse_distance_histogram"], "count", "measured", **common))
    metrics.append(_metric("line_reuse_distance_histogram", f["line_reuse_distance_histogram"], "count", "measured",
                           note=f["line_mapping"], **common))
    d = f["degree"]
    for name, key, unit in (("degree_skew", "gini", "ratio"), ("degree_cv", "cv", "ratio"),
                            ("max_degree", "max", "count"), ("mean_degree", "mean", "edges_per_vertex")):
        metrics.append(_metric(name, d[key], unit, "measured", tool=tool, note=f"{d['which']}-degree over all vertices"))


def _cachegrind(r, args, impl, fill, run_fill, threads_env):
    if args.cachegrind == "no" or (args.cachegrind == "auto" and not shutil.which("valgrind")):
        r.parts.append({"part": "cachegrind", "outcome": "skipped", "command": None, "started": None, "finished": None,
                        "timeout_s": None, "exit_code": None, "raw_files": [],
                        "note": "valgrind is not installed here" if args.cachegrind == "auto" else "--cachegrind no"})
        return None
    binary = r.folder / "bin" / f"{impl['id']}-g"
    build = impl["build"]["command"].format(**{**fill, "flags": impl["build"]["flags"] + " -g"},
                                            binary=shlex.quote(str(binary)))
    entry, _ = r.execute("cachegrind", build, timeout=600, log_name="cachegrind-build.log")
    if entry["outcome"] != "complete":
        r.record(entry, note="building the -g binary failed")
        return None
    out = r.folder / "cachegrind.out"
    cmd = (f"valgrind --tool=cachegrind --cache-sim=yes --cachegrind-out-file={shlex.quote(str(out))} "
           + impl["run"]["command"].format(**{**run_fill, "binary": shlex.quote(str(binary))}, trials=1))
    entry2, text = r.execute("cachegrind", cmd, env_extra={threads_env: "1"}, timeout=args.cachegrind_timeout)
    entry2["raw_files"] = [entry["raw_files"][0]] + entry2["raw_files"]
    if entry2["outcome"] != "complete" or not out.exists():
        r.record(entry2, note="cachegrind did not finish within its timeout; simulated misses are missing"
                 if entry2["outcome"] == "timed_out" else "cachegrind failed or wrote no output file",
                 outcome="failed" if entry2["outcome"] == "complete" else None)
        return None
    parsed = parse_cachegrind(out.read_text(errors="replace"), impl["run"].get("kernel_symbols", []))
    config = "; ".join(parsed["desc"])
    if not parsed["kernel"]:
        r.record(entry2, outcome="failed", raw=[out.name],
                 note=f"no function matched kernel_symbols {impl['run'].get('kernel_symbols')}; config: {config}")
        return None
    r.record(entry2, raw=[out.name], note=f"simulated caches: {config}; kernel functions: {', '.join(parsed['functions'])}")
    metrics = []
    for scope, totals, what in (("per_call", parsed["kernel"], "kernel functions only (one call)"),
                                ("per_run", parsed["total"], "whole run, including graph generation and building")):
        refs = totals["Dr"] + totals["Dw"]
        d1 = totals["D1mr"] + totals["D1mw"]
        ll = totals["DLmr"] + totals["DLmw"]
        common = dict(threads=1, scope=scope, tool="cachegrind --cache-sim=yes", note=f"{what}; {config}")
        metrics += [_metric("sim_instructions", totals["Ir"], "count", "simulated", **common),
                    _metric("sim_data_refs", refs, "count", "simulated", **common),
                    _metric("sim_d1_misses", d1, "count", "simulated", **common),
                    _metric("sim_ll_misses", ll, "count", "simulated", **common),
                    _metric("sim_d1_miss_rate", round(d1 / refs, 6) if refs else None, "ratio",
                            "simulated" if refs else "unknown", **common),
                    _metric("sim_ll_miss_rate", round(ll / refs, 6) if refs else None, "ratio",
                            "simulated" if refs else "unknown", **common)]
    return {"metrics": metrics, "kernel": parsed["kernel"]}


def parse_cachegrind(text, symbols):
    """Sum cachegrind events for the whole run and for functions whose (mangled or plain)
    name is one of the kernel symbols, including OpenMP outlined bodies (name._omp_fn.N)."""
    events, desc, fn = [], [], None
    total, kernel, functions = {}, {}, []
    # Mangled names carry the length first (_Z14PageRankPullGS...), which makes the match
    # exact; demangled names are matched as "name(".
    patterns = [re.compile(rf"(?<![0-9]){len(s)}{re.escape(s)}|(?<![A-Za-z0-9_:]){re.escape(s)}\(") for s in symbols]
    for line in text.splitlines():
        if line.startswith("desc:"):
            desc.append(line[5:].strip())
        elif line.startswith("events:"):
            events = line.split()[1:]
            total = dict.fromkeys(events, 0)
        elif line.startswith("fn="):
            fn = line[3:]
            match = any(p.search(fn) for p in patterns)
            if match and fn not in functions:
                functions.append(fn)
        elif line and line[0].isdigit() and events:
            nums = [int(x) for x in line.split()[1:]]
            nums += [0] * (len(events) - len(nums))
            for name, value in zip(events, nums):
                total[name] += value
            if fn in functions:
                for name, value in zip(events, nums):
                    kernel[name] = kernel.get(name, 0) + value
    for needed in ("Ir", "Dr", "Dw", "D1mr", "D1mw", "DLmr", "DLmw"):
        total.setdefault(needed, 0)
        if kernel:
            kernel.setdefault(needed, 0)
    return {"desc": desc, "total": total, "kernel": kernel, "functions": functions}


def _counts(counts, impl, values, features, sweeps, timing, trials):
    stream = impl["run"].get("index_stream")
    if features and stream:
        pattern = features["_pattern"]
        counts["iterations"] = {"value": features["stream_length"], "formula": None, "scope": "per_sweep",
                                "basis": "measured", "evidence_refs": ["run"],
                                "note": f"iterations of loop {pattern['loop']} in one sweep: index reads of pattern "
                                        f"{pattern['id']}, counted by index_features"}
    if sweeps is not None:
        counts["sweeps"] = {"value": sweeps, "formula": None, "scope": "per_call", "basis": "measured",
                            "evidence_refs": ["run"], "note": "iterations of the outer loop per call, from the "
                                                              "benchmark's own output at 1 thread"}
    if timing:
        counts["repetitions"] = {"value": trials, "formula": None, "scope": "per_run", "basis": "measured",
                                 "evidence_refs": ["run"],
                                 "note": "timed trials per process (-n), one kernel call each; Trial Time lines parsed"}
    for loop in impl["loops"]:
        tc = loop["trip_count"]
        if tc.get("formula"):
            value = _evaluate(tc["formula"], values)
            counts[f"trips_{loop['id']}"] = {
                "value": value, "formula": tc["formula"] if value is None else None, "scope": tc["scope"],
                "basis": "inferred" if value is not None else "code_reading", "evidence_refs": ["run"],
                "note": f"trip count of loop {loop['id']} ({tc['formula']}) evaluated on the input"}


def _bottleneck(timing, footprint, exact, machine, sim):
    """Counter-free inference. Rule, in order:
    - no timing, or a footprint that is only a lower bound and fits in the LLC: unknown;
    - footprint above one socket's LLC, and (no cachegrind or simulated kernel LL miss rate at
      least LL_MISS_RATE_LOW): memory_bound; bandwidth if parallel efficiency at the largest
      thread count is below EFFICIENCY_SCALES, else latency;
    - otherwise: compute_bound if that efficiency is at least EFFICIENCY_SCALES, else
      parallelism_bound."""
    rests = ["total_footprint_bytes", "footprint_llc_ratio", "parallel_efficiency"]
    llc = llc_bytes(machine)
    if not timing or len(timing) < 2 or (not exact and footprint <= llc):
        return {"value": None, "basis": "unknown", "memory_limit": None, "rests_on": rests, "evidence_refs": [],
                "note": "timing sweep incomplete, or the footprint is only a lower bound below the LLC size"}
    top = timing[-1]
    base = timing[0]["median_s"]
    eff = base / top["median_s"] / top["threads"] if top["median_s"] > 0 else 0.0
    ll_rate = None
    if sim:
        k = sim["kernel"]
        refs = k["Dr"] + k["Dw"]
        ll_rate = (k["DLmr"] + k["DLmw"]) / refs if refs else None
        rests.append("sim_ll_miss_rate")
    big = footprint > llc
    missy = ll_rate is None or ll_rate >= LL_MISS_RATE_LOW
    facts = (f"footprint {'at least ' if not exact else ''}{footprint} B vs LLC {llc} B ({footprint / llc:.2f}x); parallel efficiency at "
             f"{top['threads']} threads {eff:.2f}" + (f"; simulated kernel LL miss rate {ll_rate:.4f}" if ll_rate is not None else ""))
    if big and missy:
        limit = "bandwidth" if eff < EFFICIENCY_SCALES else "latency"
        value = "memory_bound"
    else:
        limit = None
        value = "compute_bound" if eff >= EFFICIENCY_SCALES else "parallelism_bound"
    return {"value": value, "basis": "inferred", "memory_limit": limit, "rests_on": rests, "evidence_refs": ["run"],
            "note": f"Counter-free rule (swdb/profile.py _bottleneck, thresholds efficiency {EFFICIENCY_SCALES}, "
                    f"LL miss rate {LL_MISS_RATE_LOW}): {facts}. Not a counter-based verdict."}
