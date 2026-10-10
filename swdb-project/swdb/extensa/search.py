# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/a5/search.py (SearchBudget, SearchLedger, feedback,
#         plan_rollback/apply_rollback) and the attempt-outcome and stop-reason types of
#         AgenticRefiner/refiner/a5/outcomes.py. Rewritten onto Extensa-mode campaigns.
"""Search accounting for Extensa-mode campaigns: budget, plateau, feedback, rollback.

Kept from Extensa (decision D1):

* **Budget.** Every opened provider call is charged. Nothing gets a free retry. The
  only exception is decision D7's uncounted failures (usage limit, login), which pause
  the campaign and are recorded with ``counted: false``.
* **Plateau.** Every *completed* non-improving iteration advances the plateau counter
  exactly once. An infrastructure stop consumes what it used but does not move the
  plateau: the search was interrupted, it did not run out of ideas.
* **Incumbent state.** A rejected candidate is rolled back in full before the next
  call; nothing it wrote survives, and nothing that was there is destroyed.
* **No defaults.** Budgets come from the campaign file and are never defaulted here.

SWDB changes: the unit of plateau is an iteration (one rewrite call, one artifact per
workload class); budgets add lane-hours, disk and setup calls; the stop reasons are
decision D6's closed set; feedback carries evaluator-supplied numbers only as
structured fields, and its free text passes the ported leakage check.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional

from swdb.extensa.leakage import find_outcome_claims

__all__ = ["StopReason", "IterationOutcome", "CallOutcome", "SearchBudget", "SearchLedger",
           "FEEDBACK_REASONS", "FEEDBACK_FIELDS", "Feedback", "FeedbackError", "RollbackPlan",
           "plan_rollback", "apply_rollback", "BUDGET_KEYS"]


class StopReason(str, Enum):
    """Decision D6's closed stop-reason set."""
    MAX_ITERATIONS = "max_iterations"
    PLATEAU = "plateau"
    LANE_HOURS = "lane_hours"
    PROVIDER_CALLS = "provider_calls"
    DISK = "disk"
    BASELINE_UNSTABLE = "baseline_unstable"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    STOPPED_BY_YANRU = "stopped_by_yanru"


#: Precedence when several stop conditions coincide (first wins; ported from
#: outcomes.resolve_stop_reason, which ranks exhaustion of the budget above plateau).
STOP_PRECEDENCE = (StopReason.INFRASTRUCTURE_FAILURE, StopReason.BASELINE_UNSTABLE,
                   StopReason.STOPPED_BY_YANRU, StopReason.DISK, StopReason.LANE_HOURS,
                   StopReason.PROVIDER_CALLS, StopReason.MAX_ITERATIONS, StopReason.PLATEAU)


class IterationOutcome(str, Enum):
    IMPROVED = "improved"                       # some class's best improved in selection order
    NOT_IMPROVED = "not_improved"               # completed, nothing improved: plateau advances
    INFRASTRUCTURE_FAILED = "infrastructure_failed"   # stops; plateau unchanged
    PAUSED = "paused"                           # usage limit / login: not an iteration


COMPLETED_ITERATION_OUTCOMES = frozenset({IterationOutcome.IMPROVED, IterationOutcome.NOT_IMPROVED})


class CallOutcome(str, Enum):
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    MALFORMED_OUTPUT = "malformed_output"
    GUARD_REFUSED = "guard_refused"
    FAILED = "failed"
    USAGE_LIMIT = "usage_limit"
    LOGIN = "login"
    #: SWDB addition, ticket 73 (2026-10-05 ET): transient provider-side unavailability (D7, uncounted).
    PROVIDER_CAPACITY = "provider_capacity"
    #: SWDB addition, ticket 74 (2026-10-05 ET): the provider guard stopped the call for the harness's own
    #: limit on the provider runtime, not for anything the model did (D7: not a real attempt, uncounted).
    GUARD_INFRASTRUCTURE = "guard_infrastructure"


UNCOUNTED_CALL_OUTCOMES = frozenset({CallOutcome.USAGE_LIMIT, CallOutcome.LOGIN, CallOutcome.PROVIDER_CAPACITY,
                                     CallOutcome.GUARD_INFRASTRUCTURE})

BUDGET_KEYS = ("max_iterations", "plateau_iterations", "lane_hours", "provider_calls_per_iteration",
               "provider_calls_setup", "disk_gb", "lanes")


@dataclass(frozen=True)
class SearchBudget:
    """The campaign file's budgets. No value here has a code default."""

    max_iterations: int
    plateau_iterations: int
    lane_hours: float
    provider_calls_per_iteration: int
    provider_calls_setup: int
    disk_gb: float
    lanes: int
    source: str
    """Which campaign file (path and sha256) these numbers were copied from."""

    def __post_init__(self) -> None:
        for name in ("max_iterations", "plateau_iterations", "provider_calls_per_iteration", "lanes"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"budget {name} must be a positive integer")
        if type(self.provider_calls_setup) is not int or self.provider_calls_setup < 0:
            raise ValueError("budget provider_calls_setup must be a nonnegative integer")
        for name in ("lane_hours", "disk_gb"):
            value = getattr(self, name)
            if type(value) not in (int, float) or value <= 0:
                raise ValueError(f"budget {name} must be positive")
        if not self.source:
            raise ValueError("a budget must name the campaign file it was copied from; none is invented")

    @classmethod
    def from_mapping(cls, budgets: dict, source: str) -> "SearchBudget":
        if not isinstance(budgets, dict):
            raise ValueError("budgets must be a mapping")
        missing = [key for key in BUDGET_KEYS if key not in budgets]
        if missing:
            raise ValueError("campaign budgets have no code defaults; missing: " + ", ".join(missing))
        unknown = set(budgets) - set(BUDGET_KEYS)
        if unknown:
            raise ValueError("unknown budget keys: " + ", ".join(sorted(unknown)))
        return cls(**{key: budgets[key] for key in BUDGET_KEYS}, source=source)

    def to_dict(self) -> dict:
        return {key: getattr(self, key) for key in BUDGET_KEYS}


@dataclass
class CallRecord:
    index: int
    iteration: int            # 0 for the setup call
    role: str
    invocation: str
    outcome: Optional[str] = None
    counted: bool = True

    def to_dict(self) -> dict:
        return {"index": self.index, "iteration": self.iteration, "role": self.role,
                "invocation": self.invocation, "outcome": self.outcome, "counted": self.counted}


@dataclass
class IterationRecord:
    index: int
    outcome: IterationOutcome
    advanced_plateau: bool
    plateau_after: int

    def to_dict(self) -> dict:
        return {"index": self.index, "outcome": self.outcome.value,
                "advanced_plateau": self.advanced_plateau, "plateau_counter": self.plateau_after}


class CallRefused(RuntimeError):
    """Opening this call would exceed the provider-call cap (D7)."""


class SearchLedger:
    """Budget and plateau accounting for one Extensa campaign."""

    def __init__(self, budget: SearchBudget):
        self.budget = budget
        self.iteration = 0              # index of the open iteration (0 = setup)
        self.iterations_completed = 0
        self.plateau = 0
        self.calls: list[CallRecord] = []
        self.iterations: list[IterationRecord] = []
        self._terminal: Optional[StopReason] = None
        self._iteration_calls = 0
        self._setup_calls = 0

    # -- state ------------------------------------------------------------
    @property
    def counted_calls(self) -> int:
        return sum(1 for c in self.calls if c.counted)

    @property
    def uncounted_calls(self) -> int:
        return sum(1 for c in self.calls if not c.counted)

    @property
    def plateau_reached(self) -> bool:
        return self.plateau >= self.budget.plateau_iterations

    @property
    def iterations_exhausted(self) -> bool:
        return self.iterations_completed >= self.budget.max_iterations

    def calls_remaining_this_iteration(self) -> int:
        if self.iteration == 0:
            return max(0, self.budget.provider_calls_setup - self._setup_calls)
        return max(0, self.budget.provider_calls_per_iteration - self._iteration_calls)

    def may_open_iteration(self) -> bool:
        return self._terminal is None and not self.iterations_exhausted and not self.plateau_reached

    # -- iterations --------------------------------------------------------
    def begin_iteration(self) -> int:
        if not self.may_open_iteration():
            raise RuntimeError("the campaign has stopped; no further iteration may open")
        self.iteration = self.iterations_completed + 1
        self._iteration_calls = 0      # unused calls never carry over
        return self.iteration

    def record_iteration(self, outcome: IterationOutcome) -> IterationRecord:
        if self._terminal is not None:
            raise RuntimeError("a terminal outcome cannot be followed by another iteration")
        if self.iteration == 0:
            raise RuntimeError("no iteration is open")
        advanced = False
        if outcome is IterationOutcome.PAUSED:
            # Not an iteration: it is retried from its start after resume.
            record = IterationRecord(self.iteration, outcome, False, self.plateau)
            self.iterations.append(record)
            self.iteration = 0
            return record
        if outcome is IterationOutcome.IMPROVED:
            self.plateau = 0
        elif outcome is IterationOutcome.NOT_IMPROVED:
            self.plateau += 1
            advanced = True
        else:
            self._terminal = StopReason.INFRASTRUCTURE_FAILURE
        if outcome in COMPLETED_ITERATION_OUTCOMES:
            self.iterations_completed += 1
        record = IterationRecord(self.iteration, outcome, advanced, self.plateau)
        self.iterations.append(record)
        self.iteration = 0
        return record

    # -- provider calls -----------------------------------------------------
    def open_call(self, role: str, invocation: str) -> CallRecord:
        """Charge one opened call, or refuse to open it (D7: the cap is never exceeded)."""
        if self._terminal is not None:
            raise CallRefused("the campaign has stopped")
        if self.calls_remaining_this_iteration() < 1:
            raise CallRefused("provider-call cap reached for "
                              + ("setup" if self.iteration == 0 else f"iteration {self.iteration}"))
        if self.iteration == 0:
            self._setup_calls += 1
        else:
            self._iteration_calls += 1
        call = CallRecord(len(self.calls) + 1, self.iteration, role, invocation)
        self.calls.append(call)
        return call

    def close_call(self, call: CallRecord, outcome: CallOutcome) -> CallRecord:
        call.outcome = CallOutcome(outcome).value
        if CallOutcome(outcome) in UNCOUNTED_CALL_OUTCOMES:
            # D7: recorded, never counted; the slot is returned for the retried iteration.
            call.counted = False
            if call.iteration == 0:
                self._setup_calls -= 1
            else:
                self._iteration_calls -= 1
        return call

    # -- stopping -----------------------------------------------------------
    def terminate(self, reason: StopReason) -> None:
        """End on a condition no iteration reported. The first terminal reason wins."""
        if self._terminal is None:
            self._terminal = StopReason(reason)

    def stop(self) -> tuple[Optional[StopReason], tuple[StopReason, ...]]:
        conditions = []
        if self._terminal is not None:
            conditions.append(self._terminal)
        if self.iterations_exhausted:
            conditions.append(StopReason.MAX_ITERATIONS)
        if self.plateau_reached:
            conditions.append(StopReason.PLATEAU)
        ordered = tuple(r for r in STOP_PRECEDENCE if r in conditions)
        return (ordered[0] if ordered else None), ordered

    # -- persistence (SWDB addition: a paused campaign resumes from its state file) ----
    def to_state(self) -> dict:
        return {"iteration": self.iteration, "iterations_completed": self.iterations_completed,
                "plateau": self.plateau, "calls": [c.to_dict() for c in self.calls],
                "iterations": [r.to_dict() for r in self.iterations],
                "terminal": self._terminal.value if self._terminal else None,
                "iteration_calls": self._iteration_calls, "setup_calls": self._setup_calls}

    @classmethod
    def from_state(cls, budget: SearchBudget, state: dict) -> "SearchLedger":
        ledger = cls(budget)
        ledger.iteration = state["iteration"]
        ledger.iterations_completed = state["iterations_completed"]
        ledger.plateau = state["plateau"]
        ledger.calls = [CallRecord(**c) for c in state["calls"]]
        ledger.iterations = [IterationRecord(r["index"], IterationOutcome(r["outcome"]), r["advanced_plateau"],
                                             r["plateau_counter"]) for r in state["iterations"]]
        ledger._terminal = StopReason(state["terminal"]) if state["terminal"] else None
        ledger._iteration_calls = state["iteration_calls"]
        ledger._setup_calls = state["setup_calls"]
        return ledger

    def to_dict(self) -> dict:
        winner, coincident = self.stop()
        return {"budget": self.budget.to_dict(), "iterations_completed": self.iterations_completed,
                "plateau_counter": self.plateau, "provider_calls_counted": self.counted_calls,
                "provider_calls_uncounted": self.uncounted_calls,
                "calls": [c.to_dict() for c in self.calls],
                "iterations": [r.to_dict() for r in self.iterations],
                "stop_reason": winner.value if winner else None,
                "coincident_stop_conditions": [c.value for c in coincident]}


# --------------------------------------------------------------------------
# Provider-visible feedback (decision D8)
# --------------------------------------------------------------------------

#: The closed set of reason codes the rewrite provider may be told about.
FEEDBACK_REASONS: tuple[str, ...] = (
    "certified",                 # certification passed for this class's artifact
    "uncertified_edit",          # the edit used no rewrite contract
    "certification_failed",      # a named check failed; the artifact is rejected
    "knob_out_of_range",         # a knob value outside its contract's declared range
    "build_failed",
    "correctness_failed",
    "evaluation_failed",
    "verdict_gain",
    "verdict_no_gain",
    "verdict_inconclusive",
    "provider_output_invalid",
)

#: Structured fields a feedback item may carry. Numbers come only from the evaluator.
#: Raw timings, workload files and evaluator inputs are never feedback.
FEEDBACK_FIELDS = frozenset({"class", "failed_checks", "verdict", "ratio", "lower", "spread",
                             "evidence_basis"})
_FORBIDDEN_FIELD = re.compile(r"(?:time|timing|seconds|duration|ns|path|workload|input|graph)", re.I)

_ADVICE_MARKERS = re.compile(
    r"\b(?:instead|try|should|recommend\w*|suggest\w*|consider|use the|"
    r"apply the|rewrite the|prefer)\b", re.IGNORECASE)


class FeedbackError(ValueError):
    """Feedback that would disclose raw measurements or hand over an answer key."""


@dataclass(frozen=True)
class Feedback:
    """One closed reason code, a short outcome-free explanation, and structured fields."""

    reason_code: str
    explanation: str
    fields: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.reason_code not in FEEDBACK_REASONS:
            raise FeedbackError(f"feedback reason {self.reason_code!r} is outside the closed set")
        if not self.explanation.strip():
            raise FeedbackError("feedback must carry a short explanation")
        if len(self.explanation) > 400:
            raise FeedbackError("feedback explanation is long enough to smuggle a rationale")
        claims = find_outcome_claims(self.explanation, where="feedback")
        if claims:
            raise FeedbackError("feedback prose states a performance outcome: "
                                + ", ".join(c.evidence for c in claims))
        advice = _ADVICE_MARKERS.search(self.explanation)
        if advice:
            raise FeedbackError(f"feedback offers transformation advice ({advice.group(0)!r})")
        unknown = set(self.fields) - FEEDBACK_FIELDS
        if unknown or any(_FORBIDDEN_FIELD.search(k) for k in self.fields if k not in FEEDBACK_FIELDS):
            raise FeedbackError("feedback field outside the closed field set: " + ", ".join(sorted(unknown)))

    def to_dict(self) -> dict:
        return {"schema": "swdb.extensa-feedback.v1", "reason_code": self.reason_code,
                "explanation": self.explanation, **{k: self.fields[k] for k in sorted(self.fields)}}


# --------------------------------------------------------------------------
# Rollback (unchanged logic)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class RollbackPlan:
    remove: tuple[str, ...]
    preserve: tuple[str, ...]
    incumbent_ref: str

    def to_dict(self) -> dict:
        return {"remove": list(self.remove), "preserve": list(self.preserve), "incumbent_ref": self.incumbent_ref}


def _git(worktree: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=worktree, check=True, capture_output=True, text=True).stdout


def untracked_paths(worktree: Path) -> tuple[str, ...]:
    out = _git(worktree, "status", "--porcelain", "--untracked-files=all", "--ignored=matching")
    paths: list[str] = []
    for line in out.splitlines():
        if line[:2] in ("??", "!!"):
            paths.append(line[3:].strip().strip('"'))
    return tuple(sorted(paths))


def plan_rollback(worktree: Path, *, incumbent_ref: str, preserved_untracked: Iterable[str] = (),
                  launcher_owned: Iterable[str] = ()) -> RollbackPlan:
    """Decide what a rollback removes, without touching anything yet."""
    preserved = set(preserved_untracked)
    owned = tuple(launcher_owned)
    remove: list[str] = []
    keep: list[str] = []
    for path in untracked_paths(worktree):
        if path in preserved or any(path == o or path.startswith(o.rstrip("/") + "/") or path.startswith(o)
                                    for o in owned):
            keep.append(path)
        else:
            remove.append(path)
    return RollbackPlan(remove=tuple(sorted(remove)), preserve=tuple(sorted(keep)), incumbent_ref=incumbent_ref)


def apply_rollback(worktree: Path, plan: RollbackPlan) -> RollbackPlan:
    """Restore the worktree to the incumbent: tracked files reset, planned paths removed."""
    root = Path(worktree).resolve()
    _git(worktree, "reset", "--hard", plan.incumbent_ref)
    for path in plan.remove:
        target = root / path
        if target.is_dir():
            for child in sorted(target.rglob("*"), reverse=True):
                child.unlink() if child.is_file() else child.rmdir()
            target.rmdir()
        elif target.exists():
            target.unlink()
    for path in plan.remove:
        parent = (root / path).parent
        while parent != root and parent.is_dir():
            try:
                next(parent.iterdir())
            except StopIteration:
                parent.rmdir()
                parent = parent.parent
            else:
                break
    return plan
