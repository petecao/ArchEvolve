"""The WP phase: after an Extensa campaign stops, the unbounded rung on its `gain` candidate artifacts.

Created: 2026-10-14 ET (Probata proof of concept ticket 16). Design: formal-verification map spec ("Extensa
mode" (WP phase, budgets), "Records and levels" (campaign summary), "Proof-hint loop", "Verifier lineup and
order"; S1, S6; O7); map decisions 13 items 3, 10, 11, 25 items 1, 2, 4, 26 items 6, 10.
Format: docs/reference/format-v0.4-extensa.md ("The WP phase").

When a campaign whose library holds a method version stops and its first summary is written, the WP phase
runs step 4 of a candidate artifact's path. Per workload class it takes the certified, unrefuted `gain`
candidate artifacts, fastest first, and runs one `swdb prove` job per proof unit (one per rewrite contract):
WP alone, then the contract seeds, then proof-hint rounds. A class is done when one candidate artifact reads
proven unbounded (the level rule, over the records just written), or when its order is spent. The phase ends
when every class is done or the campaign's lane-hours run out; then the campaign rewrites its summary once.

- **Budgets.** Per candidate artifact, the method version's `hint_rounds`, `hint_loop_wall_minutes` (the job's
  wall budget) and `wp_seconds_per_solver`; per campaign, `budgets.provider_calls_proof` (proof-hint calls on
  the call ledger, never in the rewriting total) and the lane-hours every proof job shares. A spent hint cap
  leaves WP alone and the seeds; a job that is not proven ends "not proven, hint budget spent" and the
  candidate artifact keeps its level.
- **Skips (O7)** skip only what needs the missing piece: no contract proof means no seeds, and a proof unit
  with a unit postcondition still runs route-1 WP (without one, a skip record); code outside the C++ subset
  is a skip record (13 item 2). A skipped candidate artifact keeps its level and the next one is tried.
- **No overlap.** Each job starts only when the target reports no open timing step or gem5 simulation; the
  campaign state's `timeline` holds the start and end of every proof job, timing step and gem5 simulation.
- **The hint rounds are scripted here.** The target adapter's `wp_plan` says which stage proves the unit and
  `wp_job` gives the job's verdict script; ticket 37 replaces the stage loop with the real proof-hint loop
  (one provider call per round, charged through `Phase.charge_hint`).
"""

import copy
import datetime
import os
import time
import uuid
from argparse import Namespace

from swdb.cli import Failure

UNBOUNDED = "proven_unbounded"
HINT_BUDGET_SPENT = "hint_budget_spent"
NO_CONTRACT_PROOF, OUTSIDE_SUBSET = "no_contract_proof", "outside_cpp_subset"
BUDGET = "provider_calls_proof"
#: Method-version budgets the phase reads (25 item 2, 13 item 11); none has a fallback default.
METHOD_BUDGETS = ("hint_rounds", "hint_loop_wall_minutes", "wp_seconds_per_solver")
POLL_S = 1.0       # how often a waiting job asks whether a timing step is still open (SWDB_WP_POLL_S overrides)


class _End(Exception):
    def __init__(self, reason, detail):
        super().__init__(detail)
        self.reason, self.detail = reason, detail


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- what the campaign loop calls --------------------------------------------------------------------------

def require_budget(campaign):
    """A new campaign whose library holds a method version (it will have a WP phase) must set
    `budgets.provider_calls_proof`: budgets come from the campaign file, never from a default."""
    from swdb import bounded_gate
    if bounded_gate.method_version_of(campaign.library_root) is not None and BUDGET not in campaign.data["budgets"]:
        raise Failure(f"campaign file refused:\n  budgets.{BUDGET}: required when the campaign's library holds a "
                      "method version (the WP phase's proof-hint calls; the spec default is 30)")


def resumable(state):
    """True when a stopped campaign's WP phase has not ended (an interrupted phase continues on resume)."""
    return (state.get("wp_phase") or {}).get("state") in ("not_started", "running")


def timeline(campaign, kind, what, started, ended=None):
    """Record one interval (proof job, timing step or gem5 simulation) in the campaign state."""
    campaign.state.setdefault("timeline", []).append({"kind": kind, "what": what, "started": started,
                                                      "ended": ended or _now()})


def evaluation_spent(campaign, started, hours):
    """An evaluation step just ended: its interval goes to the timeline (`started` is time.monotonic())."""
    began = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=time.monotonic() - started)
    kind = "gem5_simulation" if campaign.adapter.SHARED_BASELINE else "timing_step"
    timeline(campaign, kind, "evaluation", began.isoformat())


def proof_spent(campaign, started, started_at, what):
    """A proof job just ended: charge it to the campaign's lane-hours and to its proof lane-hours line."""
    before = campaign.state["lane_hours"]
    campaign._spent("proof", started)
    hours = campaign.state["lane_hours"] - before
    campaign.state["proof_lane_hours"] = campaign.state.get("proof_lane_hours", 0.0) + hours
    timeline(campaign, "proof_job", what, started_at)
    return hours


def summary_fields(campaign, record):
    """The summary's WP-phase block and its budget lines (26 item 6): proof lane-hours, proof-hint calls and
    the two kinds of repair call."""
    budgets = record["budgets"]
    counters = campaign._repair_counters()
    budgets["used"].update(proof_lane_hours=round(campaign.state.get("proof_lane_hours", 0.0), 6),
                           provider_calls_proof=campaign.ledger.proof_calls,
                           certification_repair_calls=counters["certification_repairs"],
                           counterexample_repair_calls=counters["counterexample_repair_rounds"])
    if BUDGET in campaign.data["budgets"]:
        budgets["limits"][BUDGET] = campaign.data["budgets"][BUDGET]
    record["wp_phase"] = copy.deepcopy(campaign.state.get("wp_phase") or {"state": "not_started"})


# --- the phase ---------------------------------------------------------------------------------------------

class Phase:
    """The WP phase of one stopped campaign (`campaign` is the `swdb.campaign.Campaign`, its gate open)."""

    def __init__(self, campaign):
        from swdb import bounded_gate
        self.c = campaign
        found = bounded_gate.method_version_of(campaign.library_root)
        values = found.data.get("budgets") or {}
        for name in METHOD_BUDGETS:
            value = values.get(name)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
                raise Failure(f"method version {found.id} has no budgets.{name}: the WP phase reads it there")
        self.budgets = {name: values[name] for name in METHOD_BUDGETS}
        self.cap = campaign.data["budgets"].get(BUDGET)
        self.block = campaign.state.setdefault("wp_phase", {"state": "not_started"})

    # the run ----------------------------------------------------------------------------------------------
    def run(self):
        block = self.block
        if block["state"] == "not_started":
            block.update(state="running", started=_now(), method_version=dict(self.c.gate.method),
                         budgets={**self.budgets, BUDGET: self.cap}, classes=self._orders(), waits=[],
                         provider_calls=[])
            self.c._save()
        try:
            if self.cap is None:
                raise _End("no_proof_call_budget", f"the campaign file sets no budgets.{BUDGET}")
            if self.c.state.get("stop_reason") == "lane_hours":
                raise _End("lane_hours", "the campaign stopped on its lane-hours: none are left for the WP phase")
            for row in block["classes"]:
                if row["state"] == "running":
                    self._class(row)
            self._end("classes_done", "every class is done: one candidate artifact proven unbounded, or its order spent")
        except _End as end:
            self._end(end.reason, end.detail)
        except Failure as exc:              # a target with no WP adapter yet, or a refused `swdb prove`
            self._end("failure", f"{type(exc).__name__}: {exc}"[:2000])
        self.c._save()

    def _end(self, reason, detail):
        if self.block["state"] == "ended":
            return
        for row in self.block.get("classes") or []:
            if row["state"] == "running":
                row["state"] = "unfinished"
        self.block.update(state="ended", ended=_now(), end_reason=reason, end_detail=detail)

    def _orders(self):
        """Per class: the certified, unrefuted `gain` candidate artifacts, fastest first (stable on ties)."""
        pool = [c for row in self.c.state["iterations"] for c in row["candidates"]]
        levels = self.c._levels(pool)
        rows = []
        for cls in self.c.all_classes:
            mine = [c for c in pool if c["class"] == cls and c.get("id") in levels and c["level"] == "certified"
                    and (c.get("selection") or {}).get("verdict") == "gain"
                    and levels[c["id"]]["certification_level"] == "certified"
                    and not levels[c["id"]]["refuted"]["flag"]]
            order = [c["id"] for c in sorted(mine, key=lambda c: -c["selection"]["lower"])]
            rows.append({"class": cls, "order": order, "state": "running", "proven": None, "tried": [], "jobs": []})
        return rows

    def _class(self, row):
        from swdb.level_rule import Rule
        from swdb.library import Library
        from swdb.store import Store
        for cid in row["order"]:
            if cid in row["tried"]:
                continue
            self._candidate(row, cid)
            row["tried"].append(cid)
            self.c._save()
            store = Store(self.c.store_dir)
            if Rule(store, Library(self.c.library_root, store)).candidate(cid)["level"] == UNBOUNDED:
                row.update(state=UNBOUNDED, proven=cid)
                return
        row["state"] = "order_spent"

    # one candidate artifact -----------------------------------------------------------------------------------
    def _candidate(self, row, cid):
        from swdb.store import Store
        iteration, entry = self._entry(cid)
        context = {"iteration": iteration, "cls": entry["class"]}
        rounds = self.budgets["hint_rounds"]
        batch = f"batch.wp.{cid}.{uuid.uuid4().hex[:8]}"
        for position, contract in enumerate(entry["contracts"], start=1):
            job = {"candidate": cid, "contract": contract, "position": position}
            if self.c.adapter.outside_cpp_subset(cid, attempt=0, **context):
                job.update(skip_reason=OUTSIDE_SUBSET, record=self._prove(cid, contract, batch, position,
                                                                          skip=OUTSIDE_SUBSET)["id"])
                row["jobs"].append(job)
                continue
            seeds = bool(self.c.gate.contract_proof(Store(self.c.store_dir), contract)["parts"])
            plan = self.c.adapter.wp_plan(cid, contract, **context)
            if not seeds and not plan.get("unit_postcondition", True):
                job.update(skip_reason=NO_CONTRACT_PROOF, record=self._prove(cid, contract, batch, position,
                                                                            skip=NO_CONTRACT_PROOF)["id"])
                row["jobs"].append(job)
                continue
            rounds -= self._job(job, cid, contract, batch, position, plan, seeds, rounds, context)
            row["jobs"].append(job)          # a job the phase's end kept from starting is not listed

    def _job(self, job, cid, contract, batch, position, plan, seeds, rounds, context):
        """One WP job: wait for open timing steps, run the stages, write the record. Returns the hint rounds used."""
        if self.c.state["lane_hours"] + self.budgets["hint_loop_wall_minutes"] / 60 > self.c.budget.lane_hours:
            raise _End("lane_hours", f"the next WP job's {self.budgets['hint_loop_wall_minutes']} minutes would exceed "
                       f"{self.c.budget.lane_hours} lane-hours")
        self._wait_for_timing_steps()
        started, started_at = time.monotonic(), _now()
        stages, proven, calls = [], False, 0
        for stage in ["wp"] + (["seeds"] if seeds else []) + list(range(1, int(rounds) + 1)):
            if isinstance(stage, int):
                if not self.charge_hint(cid):
                    break                   # the campaign's proof-hint calls are spent: WP and seeds only
                calls += 1
            stages.append(stage)
            if stage == plan.get("proven_at"):
                proven = True
                break
        script = self.c.adapter.wp_job(cid, contract, proven, **context)
        record = self._prove(cid, contract, batch, position, adapter=script["adapter"], script=script.get("script"))
        hours = proof_spent(self.c, started, started_at, f"WP {cid} {contract}")
        job.update(record=record["id"], verdict=record["verdict"], stages=stages, hint_calls=calls,
                   started=started_at, ended=self.c.state["timeline"][-1]["ended"], lane_hours=round(hours, 9))
        if record.get("failure_class"):
            job["failure_class"] = record["failure_class"]
        return calls

    def charge_hint(self, cid):
        """One proof-hint round's provider call on the ledger, under `provider_calls_proof`; False when refused."""
        from swdb.extensa import search as S
        ledger = self.c.ledger
        try:
            call = ledger.open_proof_call(f"{self.c.cid}.call{len(ledger.calls) + 1}", self.cap)
        except S.CallRefused:
            return False
        ledger.close_call(call, S.CallOutcome.COMPLETED)
        provider = self.c.data["provider"]
        self.block["provider_calls"].append({"role": call.role, "invocation": call.invocation, "candidate": cid,
                                             "outcome": call.outcome, "counted": call.counted,
                                             "model": provider["model"], "effort": provider["effort"]})
        return True

    def _wait_for_timing_steps(self):
        """No proof job overlaps a timing step or a gem5 simulation: wait until the target reports none open."""
        poll = float(os.environ.get("SWDB_WP_POLL_S", POLL_S))
        first, began = None, None
        while True:
            steps = self.c.adapter.open_timing_steps()
            if not steps:
                break
            if first is None:
                first, began = steps, time.monotonic()
            if self.c.state["lane_hours"] + (time.monotonic() - began) / 3600 > self.c.budget.lane_hours:
                raise _End("lane_hours", "a timing step stayed open past the campaign's lane-hours")
            time.sleep(poll)
        if first is not None:
            closed = _now()
            for step in first:
                timeline(self.c, step.get("kind", "timing_step"), step["what"], step["started"], closed)
            self.block["waits"].append({"for": [s["what"] for s in first], "seconds": round(time.monotonic() - began, 3),
                                        "until": closed})

    def _entry(self, cid):
        for row in self.c.state["iterations"]:
            for entry in row["candidates"]:
                if entry.get("id") == cid:
                    return row["index"], entry
        raise Failure(f"candidate artifact {cid} is not in the campaign's iterations")

    def _prove(self, cid, contract, batch, position, *, skip=None, adapter="scripted", script=None):
        from swdb import proof
        runs = self.c.folder / "proofs"
        runs.mkdir(parents=True, exist_ok=True)
        args = Namespace(records=self.c.store_dir, candidate=cid, function=self.c.adapter.proof_function(contract),
                         contract=contract, adapter=adapter, script=[script] if script else None, skip=skip,
                         runs_dir=runs, batch=batch, position=position, id=None, run_index=None, provider_kind=None,
                         provider_model=None, provider_effort=None, format="json", bounds=None, minimum_bounds=None,
                         budget_minutes=None if skip else self.budgets["hint_loop_wall_minutes"])
        return proof.prove(args)["record"]
