"""Real target adapters for `swdb campaign` (tickets 56 and 57).

Created 2026-10-04 ET; ticket 63 (2026-10-04 ET): a native campaign that pins evaluator v2
freezes protocols with that evaluator, its driver and its compiled verifier. Original SWDB code (design decisions D2-D4, D7, D9 and D10 of
`.scratch/typed-library-dx100-bfs-2026-10-03/extensa-design-2026-10-03.md`).

An adapter turns the campaign loop's steps into the public SWDB evaluator commands, run
as child processes against the campaign's own record store, with every record they create
tagged `mode: extensa` and `campaign` (``workflow.EXTENSA_CAMPAIGN_ENV``). The evaluator
supplies every number (ADR 0010); an adapter never computes a ratio itself.

- ``NativeAdapter`` (ticket 56, target ``native_cpu``): one frozen native protocol per
  baseline role (a frozen protocol names one baseline build). The A/A pilot times each
  baseline against itself on each class graph. Each candidate artifact gets its own
  paired block (`swdb evaluate-pair`) against each baseline, compared separately; the
  campaign loop selects on the `base_source` comparison (Q61).
- ``Gem5Adapter`` (ticket 57, target ``dx100_gem5``): one frozen controlled-simulator
  protocol copied from ticket 29's read-offload freeze; one baseline evaluation per class
  serves every candidate artifact; point ratios. Before certification, each candidate's
  DX100 session begin is checked to sit inside the timed BFS call (`bfs.complete_call.v1`
  times the whole `DOBFS` call). Each gem5 job is admitted by the dispatch preflight against
  the lane's memory node (36 GiB per run) before it starts.

Both adapters share the candidate-artifact path: the scalar-only DX100 BFS snapshot (the
fork's scalar TDStep without the authors' accelerated code) plus the provider's patch, the
class's knob values as `SWDB_KNOB_<NAME>` defines at the top of `bfs.cc`, and, for an edit
that uses a DX100 contract, the byte-identical canonical lowering header.
"""
from __future__ import annotations

import copy
import fcntl
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from swdb import artifacts, paths, workflow
from swdb.cli import Failure, UsageError

SNAPSHOT = "bfs-dx100-scalar-only-20260929-a1.source"
BFS = "benchmarks/gapbs/src/bfs.cc"
HEADER = "benchmarks/gapbs/src/swdb_dxc_lowering.hpp"
TIMED_FUNCTION = "DOBFS"          # bfs.complete_call.v1 times the whole DOBFS call
GIB = 1024 ** 3
#: Native D3 build flags; the evaluator appends -DFUNC for DX100-fork sources.
NATIVE_FLAGS = ["-std=c++11", "-O3", "-Wall", "-fopenmp", "-pthread"]
#: The frozen 2026-09-27 one-thread protocols the native campaign copies its treatment from.
NATIVE_TEMPLATES = {"fork_scalar_tdstep": "bfs-native-one-thread-dx100-scalar-20260927.0d2d6da657751ff3",
                    "upstream_do_bfs": "bfs-native-one-thread-upstream-do-20260927.9d4b53fd41e79297"}
ROLE_IMPLEMENTATION = {"fork_scalar_tdstep": "dx100-bfs-scalar", "upstream_do_bfs": "gapbs-bfs-do"}
#: Ticket 29's frozen read-offload protocol (T17 v2 treatment) and its inputs.
GEM5_TEMPLATE = "typed-library-bfs-gem5-20261003-a2.protocol.84229924369fc6b0"
GEM5_MEMORY_GIB = 36             # ticket 28/29 admission budget per gem5 run
GEM5_STORAGE_GIB = 8
VERIFICATION_MAX_TICKS = 10 ** 14
POSTPROCESS_SECONDS = 3600


from swdb.campaign import Refused, Stop  # noqa: E402  (the loop's refusal and stop types)


def _stop(reason, detail):
    return Stop(reason, detail)


# --- session begin inside the timed call (ticket 57) -----------------------------------

_LEXICAL = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/')


def _code_only(text):
    """Blank comments and literals, keeping offsets, so braces and calls are lexical."""
    text = re.sub(r"\\\r?\n", "  ", text)
    return _LEXICAL.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text)


def _bodies(code, function):
    spans = []
    for match in re.finditer(r"\b" + re.escape(function) + r"\s*\(", code):
        depth, i = 0, match.end() - 1
        while i < len(code):                 # the parameter list
            depth += {"(": 1, ")": -1}.get(code[i], 0)
            i += 1
            if depth == 0:
                break
        rest = code[i:]
        head = re.match(r"\s*(?:const\s*)?(?:noexcept\s*)?\{", rest)
        if not head:
            continue                          # a call or a declaration, not a definition
        start = i + head.end() - 1
        depth, j = 0, start
        while j < len(code):
            depth += {"{": 1, "}": -1}.get(code[j], 0)
            if depth == 0:
                break
            j += 1
        spans.append((start, j))
    return spans


def session_begin_problem(source, function=TIMED_FUNCTION):
    """None when every DX100 session begin is inside the timed function's body.

    `bfs.complete_call.v1` times the whole call of `function`. A session begin anywhere
    else (a static initializer, `main`, a helper defined outside) runs outside the timed
    BFS call and is refused. The check is lexical and conservative: a helper that wraps
    the session begin is refused even when only the timed function calls it."""
    code = _code_only(source)
    calls = [m.start() for m in re.finditer(r"\b__dxc_session_begin\s*\(", code)]
    if not calls:
        return "the candidate never begins a DX100 session"
    if re.search(r"#\s*define\b[^\n]*\b__dxc_session_begin\b", code):
        return "a macro redefines __dxc_session_begin"
    spans = _bodies(code, function)
    if not spans:
        return f"the timed function {function} is not defined in the candidate"
    outside = [code.count("\n", 0, at) + 1 for at in calls if not any(a < at < b for a, b in spans)]
    if outside:
        return (f"DX100 session begin at line(s) {', '.join(map(str, outside))} runs outside the timed "
                f"{function} call (bfs.complete_call.v1)")
    return None


# --- child-process runner and host ------------------------------------------------------

class Runner:
    """Run one public `swdb` command as a child process with retained request and output."""

    def __init__(self, records, folder, campaign_id, db):
        self.records, self.folder, self.cid, self.db = Path(records), Path(folder), campaign_id, Path(db)
        self.folder.mkdir(parents=True, exist_ok=True)

    def __call__(self, command, request=None, *, stage, extra=(), timeout=600):
        """Returns (returncode, record-or-None). Timeouts raise Failure."""
        argv = [sys.executable, "-m", "swdb", command, "--records", str(self.records), "--format", "json",
                "--db", str(self.db)]
        if request is not None:
            path = self.folder / f"{stage}.request.json"
            path.write_text(json.dumps(request, indent=2) + "\n")
            argv.append(str(path))
        argv += [str(v) for v in extra]
        out, err = self.folder / f"{stage}.json", self.folder / f"{stage}.stderr.txt"
        row = {"stage": stage, "command": argv, "started": time.time(), "timeout_seconds": timeout}
        env = {**os.environ, workflow.EXTENSA_CAMPAIGN_ENV: self.cid}
        child = None
        try:
            with out.open("w") as stdout, err.open("w") as stderr:
                child = subprocess.Popen(argv, cwd=paths.HOME, env=env, stdout=stdout, stderr=stderr,
                                         text=True, start_new_session=True)
                code = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            row["state"] = "timed_out"
            (self.folder / f"{stage}.command.json").write_text(json.dumps(row, indent=2))
            raise Failure(f"{command} ({stage}) exceeded {timeout} seconds") from None
        finally:
            if child is not None:
                from swdb.processes import stop_group
                stop_group(child, grace_seconds=5)
        row.update(returncode=code, finished=time.time())
        (self.folder / f"{stage}.command.json").write_text(json.dumps(row, indent=2))
        try:
            result = json.loads(out.read_text()) if out.stat().st_size else None
        except ValueError:
            result = None
        return code, result


class Host:
    """The lane this campaign runs in, the other socket's lease and the dispatch preflight."""

    LEASES = Path(os.environ.get("LACT_LEASE_ROOT", "/data1/yanruj/lact-host-lease"))

    def lane(self):
        from swdb import provider_guard
        return provider_guard._lane().split(" ", 1)[0]

    def held(self, name):
        path = self.LEASES / f"{name}.lease"
        if not path.is_file():
            return False
        with path.open("r") as stream:
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
                return False
            except BlockingIOError:
                return True

    def marker_root(self, runs_root):
        return Path(runs_root) / "extensa" / "active-lanes"

    def other_socket_lease(self, lane, runs_roots):
        """The other socket's lease when held, with the Extensa campaign marker if one runs there."""
        node = lane[-1]
        other = lane[:-1] + ("1" if node == "0" else "0")
        if not self.held(other):
            return None
        row = {"lease": other, "mode": None, "target": None, "campaign": None}
        for root in runs_roots:
            marker = self.marker_root(root) / f"{other}.json"
            if marker.is_file():
                data = json.loads(marker.read_text())
                if Path(f"/proc/{data.get('pid')}").exists():
                    row.update(mode="extensa", target=data.get("target"), campaign=data.get("campaign"))
        return row

    def mark(self, runs_root, lane, campaign, target):
        root = self.marker_root(runs_root)
        root.mkdir(parents=True, exist_ok=True)
        (root / f"{lane}.json").write_text(json.dumps({"lane": lane, "campaign": campaign, "target": target,
                                                       "pid": os.getpid(), "host": socket.gethostname()}))

    def unmark(self, runs_root, lane):
        path = self.marker_root(runs_root) / f"{lane}.json"
        if path.is_file() and json.loads(path.read_text()).get("pid") == os.getpid():
            path.unlink()

    def preflight(self, runs_dir, lane, *, storage_bytes, memory_bytes):
        from swdb import dispatch_preflight
        return dispatch_preflight.check(runs_dir, lane, storage_bytes=storage_bytes, memory_bytes=memory_bytes)


# --- shared adapter ---------------------------------------------------------------------------

def _pin(data):
    return {"id": data["id"], "sha256": artifacts.digest(data)}


class TargetAdapter:
    evidence_kind = "execution"
    #: Budgeted wall time per step (hours) for the lane-hour refusal before a step starts.
    STEP_BUDGET_HOURS = {"provider": 0.35, "certification": 0.5, "synthesis": 0.5, "evaluation": 1.0}
    PLANNED_BYTES = 2 * GIB

    def __init__(self, campaign, team_records, store_dir, folder, library_root, *, runner=None, host=None,
                 certify=None):
        self.campaign, self.team = campaign, Path(team_records)
        self.store_dir, self.folder, self.library_root = Path(store_dir), Path(folder), Path(library_root)
        self.cid = campaign["id"]
        self.runs = self.folder / "runs"
        self.runner = runner or Runner(self.store_dir, self.folder / "jobs", self.cid, self.folder / "campaign.sqlite")
        self.host = host or Host()
        self._certify = certify
        self.round = 0
        self.protocol_id = None
        self.released = 0
        self._lane = None
        self._artifacts = {}            # artifact sha256 -> candidate id (identical per-class artifacts)

    # host -------------------------------------------------------------------------------
    @property
    def lane(self):
        if self._lane is None:
            self._lane = self.host.lane()
            self.host.mark(self.campaign["runs_root"], self._lane, self.cid, self.campaign["target"])
        return self._lane

    def lane_digit(self):
        return self.lane[-1]

    def release_lane(self):
        self.released += 1
        if self._lane is not None:
            self.host.unmark(self.campaign["runs_root"], self._lane)

    def other_socket_lease(self):
        roots = {self.campaign["runs_root"], "/data1/yanruj/EvolveSWDB_runs", "/data/yanruj/EvolveSWDB_runs"}
        return self.host.other_socket_lease(self.lane, sorted(roots))

    def step_hours(self, step):
        return 0.0                      # real steps are charged their measured wall time

    def step_budget_hours(self, step):
        return self.STEP_BUDGET_HOURS.get(step, 0.5)

    def planned_bytes(self):
        return self.PLANNED_BYTES

    def memory_bytes(self, step):
        return 0

    def preflight(self, planned_bytes, step=None):
        self.runs.mkdir(parents=True, exist_ok=True)
        return self.host.preflight(self.runs, self.lane, storage_bytes=planned_bytes,
                                   memory_bytes=self.memory_bytes(step))

    def _it(self, iteration):
        return f"it{iteration}" + (f"r{self.round}" if self.round else "")

    def _store(self):
        from swdb.store import Store
        return Store(self.store_dir)

    def _get(self, rid, kind):
        value = self._store().get(rid, kind)
        if value is None:
            raise Failure(f"campaign store lacks {kind} {rid}")
        return value

    # setup ------------------------------------------------------------------------------
    def roots(self):
        roots = [b["candidate"] for b in self.campaign["baselines"]]
        roots += [c["workload"] for c in self.campaign["workload_classes"]]
        return roots + [self.campaign["machine"], SNAPSHOT]

    def prepare(self):
        """Copy the team inputs (untagged) the campaign reads into its own store."""
        from swdb.extensa_boundary import closure
        from swdb.store import Store
        team = Store(self.team)
        roots = self.roots()
        missing = [rid for rid in roots if rid not in team.by_id]
        if missing:
            raise _stop("infrastructure_failure", "team store lacks campaign inputs: " + ", ".join(missing))
        for rid in sorted(closure(team, roots)):
            record = team.by_id[rid]
            target = self.store_dir / record.rel
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(self.team / record.rel, target)

    def _base_tree(self):
        """The scalar-only snapshot (fork scalar TDStep without the authors' accelerated code)."""
        tree = self.folder / "base" / "source"
        if not tree.is_dir():
            from swdb import certification
            from swdb.store import Store
            certification.materialize_snapshot(Store(self.store_dir), SNAPSHOT, self.folder / "base")
        return tree

    def source_files(self):
        return {BFS: (self._base_tree() / BFS).read_text()}

    # candidate artifacts ------------------------------------------------------------------
    def needs_header(self, contracts):
        return False

    def materialize(self, iteration, cls, patch, knobs, attempt, contracts=()):
        snapshot = self._get(SNAPSHOT, "source_snapshot")
        rid = f"{self.cid}.{self._it(iteration)}.{cls}.a{attempt}"
        tree = self.folder / "sources" / rid / "source"
        if tree.exists():
            shutil.rmtree(tree)
        tree.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self._base_tree(), tree)
        patch_path = tree.parent / "provider.patch"
        patch_path.write_text(patch if patch.endswith("\n") else patch + "\n")
        applied = None
        # --recount (2026-10-04 ET, attempt a3): provider diffs often carry wrong hunk line
        # counts; git recomputes them from the hunk text, which must still match exactly.
        for strip in ("-p1", "-p2", "-p0"):
            check = subprocess.run(["git", "apply", "--check", "--recount", strip, str(patch_path)], cwd=tree,
                                   capture_output=True, text=True)
            if check.returncode == 0:
                applied = subprocess.run(["git", "apply", "--recount", strip, str(patch_path)], cwd=tree,
                                         capture_output=True, text=True)
                break
        if applied is None or applied.returncode:
            raise Refused("build_failed", "The patch does not apply to the base source.")
        if knobs:
            source = tree / BFS
            lines = [f"// swdb campaign knob values for workload class {cls}"]
            for name, value in sorted(knobs.items()):
                token = re.sub(r"[^A-Za-z0-9_]", "_", str(name)).upper()
                if isinstance(value, bool) or not isinstance(value, (int, float, str)) or (
                        isinstance(value, str) and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value)):
                    raise Refused("knob_out_of_range", f"knob {name} has a value that cannot be compiled in")
                lines.append(f"#define SWDB_KNOB_{token} {value}")
            source.write_text("\n".join(lines) + "\n" + source.read_text())
        if self.needs_header(contracts):
            header = tree / HEADER
            canonical = self.library_root / "dx100" / "dxc_lowering.hpp"
            if header.exists() and artifacts.file_hash(header) != artifacts.file_hash(canonical):
                raise Refused("build_failed", "The patch changes the canonical lowering header.")
            shutil.copy(canonical, header)
        try:
            artifacts.check_protections(tree, snapshot["protections"])
        except Failure as exc:
            raise Refused("correctness_failed", f"The patch changes a protected region: {str(exc)[:200]}") from None
        identity = artifacts.identify(tree)
        if identity["sha256"] in self._artifacts:
            existing = self._artifacts[identity["sha256"]]
            shutil.rmtree(tree.parent)
            return {"id": existing, "sha256": identity["sha256"], "reused": True}
        diff = patch_path.read_text()
        tags = {"mode": "extensa", "campaign": self.cid}
        # The rewrite call's patch for this class is the candidate's proposal (one per artifact).
        proposal = workflow.record(
            "proposal", f"{rid}.proposal",
            producer={"name": f"{self.campaign['provider']['name']}:{self.campaign['provider']['model']}",
                      "role": "worker", "test_client": False},
            request={"campaign": self.cid, "iteration": iteration, "attempt": attempt, "class": cls,
                     "contracts": list(contracts), "knobs": dict(knobs or {}), "source_snapshot": SNAPSHOT,
                     "payload": {"kind": "patch", "sha256": artifacts.digest(patch)}},
            payload_sha256=artifacts.digest(patch),
            outcome={"state": "candidate_created", "stage": "campaign_materialization", "reason": None},
            source_snapshot=SNAPSHOT, candidate=rid, attempts=[{"candidate": rid}],
            raw_artifacts=[{"kind": "provider_patch", "path": str(patch_path), "sha256": artifacts.file_hash(patch_path)}],
            **tags)
        data = workflow.record("candidate", rid, proposal=proposal["id"], source_snapshot=SNAPSHOT,
                               implementation=snapshot["implementation"],
                               artifact={"path": str(tree), **identity}, diff=diff,
                               diff_sha256=artifacts.digest(diff), state="unverified",
                               protections=copy.deepcopy(snapshot["protections"]),
                               context=copy.deepcopy(snapshot["context"]), **tags)
        from swdb import db, writer
        writer.commit(self.store_dir, new=[proposal, data])
        db.build(self.store_dir, db.default_path(self.store_dir))
        self._artifacts[identity["sha256"]] = rid
        return {"id": rid, "sha256": identity["sha256"]}

    def certify(self, candidate, contracts, iteration, cls, attempt, tests=None):
        """`swdb certify` of the candidate artifact against its rewrite contract."""
        from swdb import certification
        from swdb.store import Store
        certify = self._certify or certification.certify
        records, failed_checks = [], []
        for contract in contracts:
            try:
                record = certify(Store(self.store_dir), contract, runs_dir=self.folder / "certification",
                                 library=self.library_root, candidate=candidate["id"])
            except (Failure, UsageError) as exc:   # an aborted certification (e.g. scope, control site)
                text = str(exc)
                site = re.search(r"negative-control mutation site: (\w+)", text)
                failed_checks.append(f"negative_control_site:{site[1]}" if site else "certification_aborted")
                records.append(None)
                continue
            records.append(record["id"])
            if record["verdict"] != "certified":
                failed_checks += sorted({c.get("reason") or "matrix" for c in record.get("matrix", [])
                                         if c.get("status") != "passed"}
                                        | {f"control:{c['id']}" for c in record.get("negative_controls", [])
                                           if c.get("status") != "rejected"})
        passed = not failed_checks
        return {"record": next((r for r in records if r), None), "outcome": "certified" if passed else "failed",
                "failed_checks": failed_checks or []}


# --- native CPU (ticket 56) ---------------------------------------------------------------------

class NativeAdapter(TargetAdapter):
    STEP_BUDGET_HOURS = {"provider": 0.35, "certification": 0.5, "synthesis": 0.5, "evaluation": 0.75}
    PLANNED_BYTES = 6 * GIB

    def roots(self):
        return super().roots() + list(NATIVE_TEMPLATES.values()) + list(ROLE_IMPLEMENTATION.values())

    def evaluator(self):
        """Ticket 63: the campaign file may pin evaluator v2 (absent means v1)."""
        from swdb.bfs_native_scalable import EVALUATOR_V1
        return self.campaign["protocol"].get("evaluator", EVALUATOR_V1)

    def planned_bytes(self):
        # A v2 paired block keeps 60 small trial records plus gzip parent vectors
        # (at most 16 MiB raw each at scale 22) and logs: well under 2 GiB.
        from swdb.bfs_native_scalable import EVALUATOR_V2
        return 2 * GIB if self.evaluator() == EVALUATOR_V2 else self.PLANNED_BYTES

    def prepare(self):
        super().prepare()
        from swdb.bfs_native import MAX_DIRECTED_EDGES, MAX_VERTICES
        from swdb import bfs_native_scalable as scalable
        if self.evaluator() == scalable.EVALUATOR_V2:
            MAX_VERTICES, MAX_DIRECTED_EDGES = scalable.MAX_VERTICES, scalable.MAX_DIRECTED_EDGES
        store = self._store()
        for row in self.campaign["workload_classes"]:
            realized = store.get(row["workload"], "workload")["definition"]["realized"]
            if realized["num_vertices"] > MAX_VERTICES or realized["num_directed_edges"] > MAX_DIRECTED_EDGES:
                raise _stop("infrastructure_failure",
                            f"class {row['class']} workload {row['workload']} ({realized['num_vertices']} vertices, "
                            f"{realized['num_directed_edges']} directed edges) exceeds the native evaluator's "
                            f"materialization limits ({MAX_VERTICES} vertices, {MAX_DIRECTED_EDGES} directed edges); "
                            "the native protocol cannot time it")
            sources = store.get(row["workload"], "workload")["definition"]["sources"]
            if sources != list(self.campaign["protocol"]["sources"]):
                raise _stop("infrastructure_failure",
                            f"class {row['class']} workload {row['workload']} registers sources {sources}, "
                            f"not the campaign's {self.campaign['protocol']['sources']}")

    def baseline(self, role):
        return next(b["candidate"] for b in self.campaign["baselines"] if b["role"] == role)

    def freeze_protocol(self, settings):
        """One frozen native protocol per baseline role; the base-source one is the campaign's."""
        frozen = {}
        for role in [b["role"] for b in self.campaign["baselines"]]:
            template = self._get(NATIVE_TEMPLATES[role], "protocol")["settings"]
            out = {key: copy.deepcopy(template[key]) for key in
                   ("mode", "kernel", "targets", "builds", "instrumentation", "correctness", "sampling",
                    "profitability", "region_pairs")}
            out["workloads"] = list(settings["workloads"].values())
            out["threads"], out["roi"] = settings["threads"], settings["roi"]
            out["sampling"]["repetitions"] = settings["repetitions"]
            out["correctness"].pop("supporting_pilot_evidence", None)
            for side in ("baseline", "candidate"):
                out["targets"][side]["configuration"] = {"lane": self.lane}
                out["builds"][side]["flags"] = NATIVE_FLAGS + ["-DFUNC"]
            if role == "upstream_do_bfs":
                out["builds"]["baseline"]["flags"] = list(NATIVE_FLAGS)
                out["builds"]["baseline"]["adapter"] = "gapbs_native"
                out["builds"]["candidate"]["adapter"] = "dx100_scalar_func"
            out["native_runtime"] = {"version": 1, "environment": {
                "OMP_NUM_THREADS": str(settings["threads"]), "OMP_DYNAMIC": "FALSE", "OMP_PROC_BIND": "close",
                "OMP_PLACES": "cores", "OMP_THREAD_LIMIT": None, "OMP_WAIT_POLICY": None,
                "GOMP_SPINCOUNT": None, "GOMP_CPU_AFFINITY": None}}
            out["profitability"].update(minimum_speedup=settings["profitability"]["minimum_speedup"],
                                        maximum_relative_spread=settings["profitability"]["maximum_relative_spread"])
            out["differences"] = {"software": [settings["differences"],
                                               f"Baseline role {role}: {ROLE_IMPLEMENTATION[role]} unchanged source."],
                                  "accelerator": [], "configuration": []}
            out["region_pairs"] = []
            from swdb import bfs_native_scalable as scalable
            if self.evaluator() == scalable.EVALUATOR_V2:
                # Ticket 63: new protocols pin evaluator v2, its driver and its compiled verifier.
                out["evaluator"] = scalable.EVALUATOR_V2
                out["correctness"]["verifier"] = scalable.VERIFIER_V2
                for side in ("baseline", "candidate"):
                    out["instrumentation"][side] = {"template_sha256": artifacts.file_hash(scalable.DRIVER_V2),
                                                    "treatment": "included"}
            request = {"message_version": "1.0", "id": f"{self.cid}.protocol.{role}", "version": 1, "settings": out}
            code, record = self.runner("freeze-protocol", request, stage=f"freeze-{role}", timeout=600)
            if code or not record or record.get("kind") != "protocol":
                raise _stop("infrastructure_failure", f"native protocol freeze for {role} failed (see jobs/freeze-{role})")
            frozen[role] = {"id": record["id"], "identity_sha256": record["identity_sha256"]}
            if out["builds"]["baseline"] != out["builds"]["candidate"]:
                # Ticket 63 (2026-10-04 ET): the A/A pilot times this role's baseline against
                # itself, so it needs a protocol whose candidate side is the baseline build
                # (the upstream role's candidate build is the DX100 fork's).
                aa = copy.deepcopy(out)
                aa["builds"]["candidate"] = copy.deepcopy(aa["builds"]["baseline"])
                aa["instrumentation"]["candidate"] = copy.deepcopy(aa["instrumentation"]["baseline"])
                aa["differences"]["software"] = aa["differences"]["software"] + [
                    "A/A pilot protocol: both sides are the baseline build."]
                request = {"message_version": "1.0", "id": f"{self.cid}.protocol.{role}.aa", "version": 1,
                           "settings": aa}
                code, record = self.runner("freeze-protocol", request, stage=f"freeze-{role}-aa", timeout=600)
                if code or not record or record.get("kind") != "protocol":
                    raise _stop("infrastructure_failure",
                                f"native A/A protocol freeze for {role} failed (see jobs/freeze-{role}-aa)")
                frozen[role]["aa"] = record["id"]
        self.protocols = {role: row["id"] for role, row in frozen.items()}
        self.aa_protocols = {role: row.get("aa", row["id"]) for role, row in frozen.items()}
        base = frozen[self.campaign["base_source"]]
        return {"id": base["id"], "identity_sha256": base["identity_sha256"], "settings": settings, "by_role": frozen}

    def restore(self, state):
        if state.get("protocol") and getattr(self, "protocols", None) is None:      # a resumed campaign
            self.protocols = {role: row["id"] for role, row in state["protocol"]["by_role"].items()}
            self.aa_protocols = {role: row.get("aa", row["id"]) for role, row in state["protocol"]["by_role"].items()}

    def _member(self, rid, candidate, role, cls, side, protocol=None):
        return {"message_version": "1.0", "id": rid, "candidate": candidate, "machine": self.campaign["machine"],
                "protocol": protocol or self.protocols[role], "protocol_role": side,
                "threads": self.campaign["protocol"]["threads"],
                "repetitions": self.campaign["protocol"]["repetitions"],
                "sources": list(self.campaign["protocol"]["sources"]), "roi": self.campaign["protocol"]["roi"],
                "target_configuration": {"lane": self.lane},
                "workload": {"id": self._workload(cls)}, "comparison_baseline": ROLE_IMPLEMENTATION[role],
                "build": {"compiler": "/usr/bin/g++", "flags": list(NATIVE_FLAGS)},
                "budget": {"build_seconds": 300, "run_seconds": 120, "total_seconds": 7200},
                "build_directory": str(Path("/data1/yanruj/EvolveSWDB_builds") / self.cid / rid)
                if socket.gethostname().split(".")[0] == "mbit10" else str(self.folder / "builds" / rid)}

    def _workload(self, cls):
        return next(c["workload"] for c in self.campaign["workload_classes"] if c["class"] == cls)

    def _block(self, tag, candidate, role, cls, protocol=None):
        """One paired block (its own baseline evaluation) and its comparison."""
        protocol = protocol or self.protocols[role]
        pair = {"message_version": "1.0", "id": f"{tag}.pair", "collection": {"method": "native_paired.v1",
                "order_seed": 20260926}, "budget": {"total_seconds": 7200},
                "baseline": self._member(f"{tag}.baseline-eval", self.baseline(role), role, cls, "baseline", protocol),
                "candidate": self._member(f"{tag}.candidate-eval", candidate, role, cls, "candidate", protocol)}
        code, record = self.runner("evaluate-pair", pair, stage=f"{tag}.pair", timeout=7500,
                                   extra=["--runs-dir", self.runs, "--lane", self.lane])
        if not record or record.get("outcome", {}).get("state") != "complete":
            reason = (record or {}).get("outcome", {}).get("reason") or "paired collection failed"
            return None, reason, [pair["baseline"]["id"], pair["candidate"]["id"]]
        compare = {"message_version": "1.0", "id": f"{tag}.comparison", "protocol": protocol,
                   "comparison_baseline": ROLE_IMPLEMENTATION[role],
                   "baseline_evaluation": pair["baseline"]["id"], "candidate_evaluation": pair["candidate"]["id"]}
        code, result = self.runner("compare-evaluations", compare, stage=f"{tag}.comparison", timeout=POSTPROCESS_SECONDS)
        if not result or result.get("decision", {}).get("state") in {None, "rejected"}:
            return None, "; ".join((result or {}).get("decision", {}).get("reasons", [])) or "comparison rejected", \
                [pair["baseline"]["id"], pair["candidate"]["id"]]
        return result, None, [pair["baseline"]["id"], pair["candidate"]["id"]]

    @staticmethod
    def _numbers(result):
        metrics = result["metrics"]
        spreads = [v for rows in metrics["relative_spread"].values() for v in rows.values()]
        return {"ratio": metrics["roi_speedup"], "lower": metrics["confidence_interval"]["lower"],
                "upper": metrics["confidence_interval"]["upper"], "spreads": spreads}

    def pilot(self, cls, role):
        """D3 A/A pilot: the baseline timed against itself with the full protocol."""
        if self.other_gem5():
            raise _stop("infrastructure_failure", self.other_gem5())
        tag = f"{self.cid}.pilot.{cls}.{role}"
        result, reason, evaluations = self._block(tag, self.baseline(role), role, cls,
                                                  getattr(self, "aa_protocols", {}).get(role))
        if result is None:
            raise _stop("infrastructure_failure", f"A/A pilot {cls}/{role} failed: {reason}"[:1500])
        numbers = self._numbers(result)
        return {"spread": max(numbers["spreads"]), "comparison": result["id"], "evaluations": evaluations}

    def other_gem5(self):
        lease = self.other_socket_lease()
        if lease and lease.get("mode") == "extensa" and lease.get("target") == "dx100_gem5":
            return ("native timed blocks refuse to start while the other socket's lease is held by a gem5 job "
                    f"of Extensa campaign {lease.get('campaign')}")
        return None

    def compare(self, candidate, cls, role, iteration, attempt, baseline_evaluation=None):
        tag = f"{self.cid}.{self._it(iteration)}.{cls}.a{attempt}.{role}"
        result, reason, evaluations = self._block(tag, candidate["id"], role, cls)
        if result is None:
            kind = "correctness_failed" if re.search(r"incorrect|verifier|parent", reason or "") else \
                "build_failed" if "build" in (reason or "") else "evaluation_failed"
            raise Refused(kind, f"Native evaluation against {role} did not complete.", [kind])
        numbers = self._numbers(result)
        return {"comparison": result["id"], **numbers, "evaluations": evaluations,
                "baseline_evaluation": f"{tag}.baseline-eval"}


# --- DX100 gem5 (ticket 57) -------------------------------------------------------------------------

class Gem5Adapter(TargetAdapter):
    STEP_BUDGET_HOURS = {"provider": 0.35, "certification": 0.5, "synthesis": 0.5, "evaluation": 1.6}
    PLANNED_BYTES = GEM5_STORAGE_GIB * GIB

    def roots(self):
        template = self._team_get(GEM5_TEMPLATE, "protocol")
        companion = template["settings"]["correctness"]["companion_cases"]["parent_gather_race"]["workload"]
        model = template["settings"]["simulation_identity"]["model_build"]["evaluation"]
        return super().roots() + [GEM5_TEMPLATE, companion, model]

    def _team_get(self, rid, kind):
        from swdb.store import Store
        value = Store(self.team).get(rid, kind)
        if value is None:
            raise _stop("infrastructure_failure", f"team store lacks {kind} {rid}")
        return value

    def memory_bytes(self, step):
        return GEM5_MEMORY_GIB * GIB if step == "evaluation" else 4 * GIB

    def needs_header(self, contracts):
        return bool(contracts)

    def reference_files(self):
        """The canonical lowering header a contract edit calls (shown read-only to the provider)."""
        return {"swdb_dxc_lowering.hpp": (self.library_root / "dx100" / "dxc_lowering.hpp").read_text()}

    def admit(self, candidate, contracts):
        """Ticket 57: the DX100 session begin must run inside the timed BFS call."""
        if not contracts:
            raise Refused("evaluation_failed", "The gem5 read-offload protocol requires a DX100 contract edit; "
                          "an edit without a contract cannot execute the required read-only case.",
                          ["required_accelerator_cases"])
        tree = Path(self._get(candidate["id"], "candidate")["artifact"]["path"])
        problem = session_begin_problem((tree / BFS).read_text())
        if problem:
            raise Refused("correctness_failed", problem[:400], ["session_begin_inside_timed_call"])

    def freeze_protocol(self, settings):
        template = copy.deepcopy(self._get(GEM5_TEMPLATE, "protocol")["settings"])
        if settings["threads"] != template["threads"]:
            raise _stop("infrastructure_failure", f"the gem5 protocol runs {template['threads']} guest threads; "
                        f"the campaign file says {settings['threads']}")
        template["workloads"] = list(settings["workloads"].values())
        runtime = {"driver_sha256": artifacts.file_hash(paths.HOME / "scripts/dx100_verify.py"),
                   "parser_sha256": artifacts.file_hash(paths.HOME / "swdb/dx100_witness.py"),
                   "observer_sha256": artifacts.file_hash(paths.HOME / "scripts/dx100_host_memory.py")}
        for role in ("baseline", "candidate"):
            template["instrumentation"][role]["verifier_runtime"] = runtime
        template["differences"]["software"] = [settings["differences"]]
        template["region_pairs"] = []
        template["profitability"].update(minimum_speedup=settings["profitability"]["minimum_speedup"],
                                         maximum_relative_spread=settings["profitability"]["maximum_relative_spread"])
        template["route"] = {"campaign": self.cid, "baseline_candidate": self.campaign["baselines"][0]["candidate"],
                             "copied_from": GEM5_TEMPLATE}
        request = {"message_version": "1.0", "id": f"{self.cid}.protocol", "version": 1, "supersedes": None,
                   "settings": template}
        code, record = self.runner("freeze-protocol", request, stage="freeze", timeout=600)
        if code or not record or record.get("kind") != "protocol":
            raise _stop("infrastructure_failure", "gem5 protocol freeze failed (see jobs/freeze)")
        self.protocol = record
        return {"id": record["id"], "identity_sha256": record["identity_sha256"], "settings": settings}

    def restore(self, state):
        if getattr(self, "protocol", None) is None:        # a resumed campaign
            self.protocol = self._get(state["protocol"]["id"], "protocol")

    def pilot(self, cls, role):
        raise Failure("the gem5 target has no A/A pilot (deterministic one-replay point ratios)")

    # jobs --------------------------------------------------------------------------------
    def _model(self):
        return self._get(self.protocol["settings"]["simulation_identity"]["model_build"]["evaluation"], "evaluation")

    def _compile(self, candidate_id, name, accelerated, diagnostic=False):
        cache = getattr(self, "_builds", None)
        if cache is None:
            cache = self._builds = {}
        key = (candidate_id, name)
        if key in cache:
            return cache[key]
        rid = f"{self.cid}.{name}.build" if not accelerated else f"{candidate_id}.{name}.build"
        existing = self._store().get(rid, "evaluation")
        if existing is not None and existing.get("outcome", {}).get("state") == "complete":
            cache[key] = existing                  # a resumed campaign reuses its completed build
            return existing
        settings = self.protocol["settings"]
        role = "candidate" if accelerated else "baseline"
        model = self._model()
        request = {"message_version": "1.0", "id": rid, "machine": "mbit10",
                   "hardware_target": settings["targets"][role]["id"], "model_root": model["context"]["model_root"],
                   "build_evaluation": model["id"], "candidate": candidate_id, "function": TIMED_FUNCTION,
                   "accelerated": accelerated, "roi": settings["roi"], "parent_gather_diagnostic": diagnostic,
                   "budget": {"total_seconds": 600, "build_seconds": 300, "memory_gib": 4, "storage_gib": 1}}
        code, record = self.runner("dx100-compile", request, stage=f"{request['id']}", timeout=660,
                                   extra=["--runs-dir", self.runs, "--lane", self.lane_digit()])
        if not record or record.get("outcome", {}).get("state") != "complete":
            reason = (record or {}).get("outcome", {}).get("reason") or "compile failed"
            raise Refused("build_failed", f"Guest build failed: {reason}"[:400], ["guest_build"])
        expected = settings["builds"][role]
        actual = copy.deepcopy(record["build"])
        if diagnostic:
            actual["flags"] = [f for f in actual["flags"] if f != "-DSWDB_DXC_DIAGNOSTIC"]
        if not all(actual.get(k) == expected[k] for k in ("compiler", "compiler_version", "flags", "adapter")):
            raise _stop("infrastructure_failure", "guest compiler/build identity differs from the frozen protocol")
        cache[key] = record
        return record

    def _representation(self, workload):
        """The adjacency-verified DX100 serialized graph (file and hash checked on the host)."""
        from swdb.bfs_protocol import workload_representation
        from swdb.store import Store
        return workload_representation(Store(self.store_dir), workload, "dx100-gapbs")["representation"]

    def _execute(self, label, candidate_id, build, role, workload, *, companion=False):
        settings = self.protocol["settings"]
        model = self._model()
        representation = self._representation(workload)
        configuration = settings["targets"][role]["configuration"]
        request = {"message_version": "1.0", "id": f"{label}.evaluation", "machine": "mbit10",
                   "hardware_target": settings["targets"][role]["id"], "model_root": model["context"]["model_root"],
                   "build_evaluation": model["id"], "simulator": copy.deepcopy(settings["simulation_identity"]["simulator"]),
                   "candidate": candidate_id, "candidate_build": build["id"],
                   "binary": {"path": build["build"]["binary"], "sha256": build["build"]["binary_sha256"]},
                   "workload": {"id": workload, "source": 0,
                                "representation": {k: representation[k] for k in ("path", "sha256")}},
                   "protocol": self.protocol["id"], "protocol_role": role,
                   "protocol_trial": {"source_position": 0, "repetition": 0},
                   "configuration": {k: configuration[k] for k in ("mode", "l3_size_mb", "l3_assoc", "tile_elements")},
                   "verification": {"checker": "dx100.bfs.verifier.v2", "max_ticks": VERIFICATION_MAX_TICKS,
                                    "coverage": role == "candidate", "post_roi_trace": "SyscallBase",
                                    "trace_transport": "gem5-gzip.v1", "read_only": role == "candidate"},
                   "budget": {"total_seconds": 3600 if companion else 9000,
                              "checkpoint_seconds": 600 if companion else 1800,
                              "run_seconds": 2940 if companion else 7140,
                              "memory_gib": GEM5_MEMORY_GIB, "storage_gib": GEM5_STORAGE_GIB}}
        if companion:
            request["protocol_companion"] = "parent_gather_race"
        self.runs.mkdir(parents=True, exist_ok=True)
        self.host.preflight(self.runs, self.lane, storage_bytes=GEM5_STORAGE_GIB * GIB,
                            memory_bytes=GEM5_MEMORY_GIB * GIB)
        code, record = self.runner("dx100-execute", request, stage=label, timeout=request["budget"]["total_seconds"] + 60,
                                   extra=["--runs-dir", self.runs, "--lane", self.lane_digit()])
        return record

    def _aggregate(self, label, evaluation, role):
        request = {"message_version": "1.0", "id": f"{label}.aggregate", "protocol": self.protocol["id"],
                   "protocol_role": role, "evaluations": [evaluation["id"]]}
        code, record = self.runner("aggregate-evaluations", request, stage=f"{label}-aggregate",
                                   timeout=POSTPROCESS_SECONDS)
        return record if record and record.get("outcome", {}).get("state") == "complete" else None

    def baseline_evaluation(self, cls, role):
        """One gem5 baseline evaluation per class serves every candidate artifact."""
        baseline = next(b["candidate"] for b in self.campaign["baselines"] if b["role"] == role)
        try:
            build = self._compile(baseline, "baseline.primary", False)
        except Refused as exc:
            raise _stop("infrastructure_failure", f"baseline guest build failed: {exc.explanation}") from None
        label = f"{self.cid}.baseline.{cls}"
        workload = next(c["workload"] for c in self.campaign["workload_classes"] if c["class"] == cls)
        observed = self._execute(label, baseline, build, "baseline", workload)
        if not observed or observed.get("outcome", {}).get("state") != "complete" \
                or observed.get("correctness", {}).get("state") != "passed":
            raise _stop("infrastructure_failure", f"gem5 baseline {cls} did not pass its verifier "
                        f"({(observed or {}).get('outcome', {}).get('reason')})"[:1500])
        aggregate = self._aggregate(label, observed, "baseline")
        if aggregate is None:
            raise _stop("infrastructure_failure", f"gem5 baseline {cls} aggregation failed")
        return aggregate["id"]

    def _companions(self, candidate_id):
        cache = getattr(self, "_companion_cache", None)
        if cache is None:
            cache = self._companion_cache = {}
        if candidate_id in cache:
            return cache[candidate_id]
        primary = self._compile(candidate_id, "primary", True)
        diagnostic = self._compile(candidate_id, "diagnostic", True, diagnostic=True)
        workload = self.protocol["settings"]["correctness"]["companion_cases"]["parent_gather_race"]["workload"]
        runs = {}
        for name, build in (("timed", primary), ("diagnostic", diagnostic)):
            runs[name] = self._execute(f"{candidate_id}.companion.{name}", candidate_id, build, "candidate",
                                       workload, companion=True)
        diag = runs["diagnostic"] or {}
        checks = diag.get("correctness", {}).get("checks", [])
        l3 = checks[0].get("parent_gather_race", {}).get("outcome", "inconclusive") if len(checks) == 1 else "inconclusive"
        timed = runs["timed"] or {}
        if l3 != "observed" or timed.get("correctness", {}).get("state") != "passed":
            raise Refused("correctness_failed", f"The parent-gather companion outcome is {l3}; timed runs need "
                          "an observed L3 companion with a passing verifier.", ["l3_companion"])
        cache[candidate_id] = {"primary": primary, "companions": {k: v["id"] for k, v in runs.items()}}
        return cache[candidate_id]

    def compare(self, candidate, cls, role, iteration, attempt, baseline_evaluation=None):
        jobs = self._companions(candidate["id"])
        label = f"{self.cid}.{self._it(iteration)}.{cls}.a{attempt}"
        workload = next(c["workload"] for c in self.campaign["workload_classes"] if c["class"] == cls)
        observed = self._execute(label, candidate["id"], jobs["primary"], "candidate", workload)
        if not observed or observed.get("outcome", {}).get("state") != "complete" \
                or observed.get("correctness", {}).get("state") != "passed":
            raise Refused("correctness_failed", "The gem5 candidate run did not pass its verifier.", ["verifier"])
        coverage = observed["correctness"]["checks"][0].get("coverage", {})
        if not all(coverage.get(case, {}).get("state") == "observed"
                   for case in ("read_only_executed", "full_tiles", "tail_tiles")):
            raise Refused("correctness_failed", "The gem5 candidate run did not exercise the frozen read-only, "
                          "full-tile and tail-tile cases.", ["required_accelerator_cases"])
        aggregate = self._aggregate(label, observed, "candidate")
        if aggregate is None:
            raise Refused("evaluation_failed", "The candidate aggregate did not complete.", ["aggregation"])
        request = {"message_version": "1.0", "id": f"{label}.{role}.comparison", "protocol": self.protocol["id"],
                   "comparison_baseline": "dx100-bfs-scalar", "baseline_evaluation": baseline_evaluation,
                   "candidate_evaluation": aggregate["id"], "companion_evaluations": jobs["companions"]}
        code, result = self.runner("compare-evaluations", request, stage=f"{label}.comparison",
                                   timeout=POSTPROCESS_SECONDS)
        if not result or result.get("decision", {}).get("state") in {None, "rejected"}:
            raise Refused("evaluation_failed", "The comparison rejected the retained evidence.", ["comparison"])
        ratio = result["metrics"]["roi_speedup"]
        return {"comparison": result["id"], "ratio": ratio, "lower": ratio, "upper": ratio, "spreads": [0.0],
                "evaluations": [observed["id"]], "baseline_evaluation": baseline_evaluation}


ADAPTERS = {"native_cpu": NativeAdapter, "dx100_gem5": Gem5Adapter}


def adapter_for(campaign, team, store_dir, folder, library_root, **options):
    return ADAPTERS[campaign["target"]](campaign, team, store_dir, folder, library_root, **options)
