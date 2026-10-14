"""The bounded gate: in a campaign, refuted code never spends evaluation time.

Created: 2026-10-14 ET (Probata proof of concept ticket 14). Design: formal-verification map spec
("Solution", steps 1-3; "Bounds"; "Verifier lineup and order"; "Extensa mode", bounded gate; S6, S8, O7);
map decisions 11 item 3, 15 item 9, 19 items 1, 3, 6, 7, 8, 25 items 1, 3; ADR 0010 ("Bounded gate").
Format: docs/reference/format-v0.4-extensa.md ("The bounded gate").

Right after certification and before speed evaluation, each certified candidate artifact runs the two
bounded rungs through `swdb prove`, once per rewrite contract it applies (one proof unit per contract):

- `threads_1`: one thread (SAW's rung), at the contract's single-thread minimum bounds;
- `threads_k`: threads <= k (CIVL's rung, GenMC the second refuter), at the multi-thread minimum bounds
  with the thread count raised to k, the method version's `civl_k`: the one decided exception to
  "minimum only" (19 item 6, 15 item 9). No other dimension runs above the minimum.

Every job has the method version's `bounded_job_minutes` as its wall budget; a candidate artifact's
rungs run in parallel (on the Mac a real verifier job still queues machine-wide, one at a time). A
timeout is not proven for that rung only: no bounded level from it, no retry at smaller bounds.

Skips (O7) skip only the steps that need the missing piece and keep the level: no contract proof (no
counting proven contract-proof part of the contract's current content) skips both rungs; no minimum
bounds for a rung skips that rung; code outside the C++ subset skips only `threads_k` (CIVL and GenMC
read the C lowering; SAW reads the C++ bitcode). Each skip is a skip record.

The gate stores no level: whether the candidate artifact is refuted is read by the level rule
(`swdb.level_rule`, the refuted flag) from the records just written. Nothing here repairs: a refuted
candidate artifact goes to `swdb.counterexample_repair.loop`, which owns the round cap and the
reverted-repair flag.
"""

import concurrent.futures
import os
import uuid
from argparse import Namespace
from pathlib import Path

from swdb.cli import Failure

RUNGS = ("threads_1", "threads_k")
MINIMUM_PART = "minimum_bounds_derivation"
NO_CONTRACT_PROOF, NO_MINIMUM_BOUNDS, OUTSIDE_SUBSET = "no_contract_proof", "no_minimum_bounds", "outside_cpp_subset"


def method_version_of(library_root, pinned=None):
    """The method version the campaign's gate runs under, or None (no gate).

    fix-21 (2026-10-14 ET): the one the campaign file pins (`method_version`, draft or frozen; a pin with
    no file is refused), else the current frozen one. A library holding only drafts keeps the gate off."""
    from swdb import method_version
    if pinned is None:
        return method_version.current(Path(library_root))
    try:
        return method_version.select(Path(library_root), pinned)
    except LookupError as exc:
        raise Failure(f"campaign file refused:\n  method_version: {exc}") from None


def budgets(found):
    """(bounded_job_minutes, civl_k) of a method version; the gate has no fallback default (25 item 2)."""
    values = (found.data.get("budgets") or {})
    minutes, k = values.get("bounded_job_minutes"), values.get("civl_k")
    for name, value in (("bounded_job_minutes", minutes), ("civl_k", k)):
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise Failure(f"method version {found.id} has no budgets.{name}: the bounded gate reads it there")
    return minutes, k


class Gate:
    """The bounded gate of one campaign. `store_dir` is the campaign store; `library_root` its library."""

    def __init__(self, store_dir, runs_dir, library_root, adapter, found):
        from swdb import method_version
        self.store_dir, self.runs_dir = Path(store_dir), Path(runs_dir)
        self.library_root = Path(library_root)
        self.adapter = adapter
        self.method = method_version.pin(found)
        self.minutes, self.k = budgets(found)

    def describe(self):
        """The gate block of the campaign state and summary."""
        return {"method_version": dict(self.method), "budget_minutes": self.minutes, "k": self.k,
                "rungs": list(RUNGS)}

    # setup ------------------------------------------------------------------------------------
    def setup(self, team_dir):
        """Put the campaign's library beside its store (so `swdb prove`, `swdb candidate-level` and the
        repair loop read the same library and method version) and copy the records the library names
        from the team store (record closure), then let the target write its contract proofs."""
        beside = self.store_dir.parent / "library"
        target = self.library_root.resolve()
        if beside.is_symlink() or beside.exists():
            if beside.resolve() != target:
                raise Failure(f"{beside} is not the campaign's library {target}")
        else:
            beside.symlink_to(target, target_is_directory=True)
        self._copy_library_records(Path(team_dir))
        self.adapter.prepare_proofs(self.store_dir, method=dict(self.method))    # fix-21: the gate's method version

    def _copy_library_records(self, team_dir):
        from swdb import access
        from swdb.extensa_boundary import closure
        from swdb.library import Library
        from swdb.store import Store
        roots = set()
        for entry in Library(self.library_root).entries.values():
            if entry.get("intrinsic_record"):
                roots.add(entry["intrinsic_record"])
            roots.update(entry.get("hardware_operations", []))
            roots.update(entry.get("strategies", []))
        team, mine = Store(team_dir), Store(self.store_dir)
        missing = sorted(rid for rid in roots if rid not in team.by_id and rid not in mine.by_id)
        if missing:
            raise Failure("the bounded gate validates the campaign store with its library, but the team store "
                          "lacks records the library names: " + ", ".join(missing))
        for rid in sorted(closure(team, sorted(roots))):
            record = team.by_id[rid]
            path = self.store_dir / record.rel
            if rid not in mine.by_id and not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                access.copy_record(team_dir / record.rel, path)

    # what the store holds ---------------------------------------------------------------------
    def contract_proof(self, store, contract):
        """{parts: [record IDs], minimum: {rung: record ID or None}} for the contract's current content.

        Counting proven contract-proof parts only (the level rule's status); a minimum-bounds derivation
        with threads 1 is the single-thread minimum, one with more threads the multi-thread minimum."""
        from swdb.level_rule import Rule
        rule = Rule(store)
        current = rule.current_entry(contract)
        parts, minimum = [], {rung: None for rung in RUNGS}
        for rid, record in sorted(rule.proofs.items()):
            subject = record.get("subject") or {}
            pin = (record.get("pins") or {}).get("contract") or {}
            if subject.get("kind") != "contract_proof_part" or subject.get("id") != contract:
                continue
            if record.get("verdict") != "proven" or pin.get("sha256") != current or not rule.status(rid)["counts"]:
                continue
            if subject.get("part") == MINIMUM_PART:
                threads = (record.get("bounds") or {}).get("threads")
                minimum["threads_1" if threads == 1 else "threads_k"] = rid
            else:
                parts.append(rid)
        return {"parts": parts, "minimum": minimum}

    def plan(self, store, candidate_id, contracts, context):
        """One row per contract and rung: what runs at which bounds, or why it is skipped."""
        outside = self.adapter.outside_cpp_subset(candidate_id, **context)
        rows = []
        for contract in contracts:
            proof = self.contract_proof(store, contract)
            for rung in RUNGS:
                row = {"contract": contract, "rung": rung}
                minimum = proof["minimum"][rung]
                if not proof["parts"]:
                    row["skip_reason"] = NO_CONTRACT_PROOF
                elif rung == "threads_k" and outside:
                    row["skip_reason"] = OUTSIDE_SUBSET
                elif minimum is None:
                    row["skip_reason"] = NO_MINIMUM_BOUNDS
                else:
                    bounds = dict(store.get(minimum, "proof")["bounds"])
                    if rung == "threads_k":
                        bounds["threads"] = self.k          # the one exception to "minimum only"
                    row.update(minimum_bounds=minimum, bounds=bounds)
                rows.append(row)
        return rows

    # one candidate artifact ---------------------------------------------------------------------
    def run(self, candidate_id, contracts, context):
        """Run (or skip) every rung of every contract; return the gate result for the campaign entry.

        `context` ({iteration, cls, attempt}) lets the target name its scripted or real verifier jobs."""
        from swdb.level_rule import Rule
        from swdb.store import Store
        store = Store(self.store_dir)
        rows = self.plan(store, candidate_id, contracts, context)
        batch = f"batch.gate.{candidate_id}.{uuid.uuid4().hex[:8]}"
        for position, row in enumerate(rows, start=1):
            row["position"] = position
        for row in rows:
            if "skip_reason" in row:
                record = self._prove(candidate_id, row, batch, skip=row["skip_reason"])
                row["record"] = record["id"]
        runs = [row for row in rows if "skip_reason" not in row]
        if runs:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(RUNGS)) as pool:
                done = [(row, pool.submit(self._job, candidate_id, row, batch, context)) for row in runs]
                for row, future in done:
                    record = future.result()
                    row.update(record=record["id"], verdict=record["verdict"],
                               wall_seconds=record["job"]["wall_seconds"])
                    if record.get("failure_class"):
                        row["failure_class"] = record["failure_class"]
        read = Rule(Store(self.store_dir)).candidate(candidate_id)["refuted"]
        order = [row["record"] for row in rows]
        refutations = sorted((r["record"] for r in read["records"]), key=lambda rid: order.index(rid)
                             if rid in order else len(order))
        return {"batch": batch, "method_version": dict(self.method), "budget_minutes": self.minutes, "k": self.k,
                "jobs": rows, "refuted": read["flag"], "refutations": refutations,
                "job_hours": round(sum(r.get("wall_seconds", 0.0) for r in rows) / 3600, 9)}

    def _job(self, candidate_id, row, batch, context):
        job = self.adapter.bounded_job(candidate_id, row["contract"], row["rung"], row["bounds"], **context)
        return self._prove(candidate_id, row, batch, adapter=job["adapter"], script=job.get("script"))

    def _prove(self, candidate_id, row, batch, *, skip=None, adapter="scripted", script=None):
        from swdb import proof
        args = Namespace(records=self.store_dir, candidate=candidate_id,
                         function=self.adapter.proof_function(row["contract"]), contract=row["contract"],
                         adapter=adapter, script=[script] if script else None, skip=skip, runs_dir=self.runs_dir,
                         batch=batch, position=row["position"], id=None, method_version=self.method["id"],
                         run_index=None, provider_kind=None,
                         provider_model=None, provider_effort=None, format="json",
                         bounds=row.get("bounds"), minimum_bounds=row.get("minimum_bounds"),
                         budget_minutes=None if skip else self.minutes)
        os.makedirs(self.runs_dir, exist_ok=True)
        return proof.prove(args)["record"]
