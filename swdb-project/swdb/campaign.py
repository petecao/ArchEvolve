"""`swdb campaign CAMPAIGN_FILE`: the Extensa-mode campaign loop (tickets 52-54).

Created 2026-10-03 ET. Original SWDB code (decisions D2-D10 of
`.scratch/typed-library-dx100-bfs-2026-10-03/extensa-design-2026-10-03.md`); the
loop accounting is the ported `swdb.extensa.search`.

One campaign names one hardware target. Each iteration: a fixed region list, or with
`regions: query` the query site finder (`swdb.site_finder`, ticket 55); one rewrite-role call that returns one patch with per-class knob
values; one candidate artifact per workload class; certification (contracts) or the
uncertified label (no contract); the evaluator through a target adapter; records
tagged `mode: extensa` and `campaign`; selection per class (certification level first,
then the evaluator's lower bound against the base-source baseline); outcome-free
feedback. The campaign stops on its budgets (D6 stop reasons) and writes one
`campaign_summary` record to its own store and to the team store.

`--fixture` selects the contract-fixture target adapter (`swdb.campaign_fixture`). Without it,
the Extensa campaign's target selects a real adapter from `swdb.campaign_targets`: native CPU
(ticket 56) or DX100 gem5 (ticket 57), updated 2026-10-04 ET. Ticket 63 (2026-10-04 ET): a native campaign file
may pin `protocol.evaluator` (native evaluator v2 for the scale-22 graphs). Ticket 66
(2026-10-04 ET, decided by Yan-Ru): a native campaign file may set `protocol.speed_rule:
swdb.speed_rule.ci_width.v1` (a relative bootstrap CI-width gate for the A/A pilot and every
candidate block, from the same CI as the 1.05 lower bound); files without it keep the range rule.
Ticket 72 (2026-10-04 ET): `swdb.speed_rule.ci_width.v2` is v1 with the A/A pilot gated on the
`base_source` role only, and a reported level mix of upstream DO-BFS trials.

Code review 2026-10-05 ET: `SpeedRule` is the one place the speed rule lives (frozen settings,
verdict, A/A gate); a real target's verdict is the evaluator's `decision.state` (F1). The adapters
answer every per-target question (pilot, shared baseline, evidence basis, campaign-file rules), so
the loop has no target-string switches; the contract-fixture adapter is a `TargetAdapter` in
`swdb.campaign_fixture` (F13). Knob ranges are checked by `swdb.library.knob_problem`.
"""
from __future__ import annotations

import contextlib
import copy
import json
import re
import os
import statistics
import subprocess
import time
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from swdb import artifacts, certification_feedback, paths, workflow, writer, yamlio
from swdb.bfs_protocol import CI_WIDTH_GATE
from swdb.cli import Failure, UsageError
from swdb.extensa_boundary import MODE
from swdb.extensa import search as S
from swdb.extensa.leakage import scan_patch_additions
from swdb.problems import Problem

FORMAT = "swdb.extensa-campaign.v1"
LABEL = "single graph per class"
GAIN_THRESHOLD = 1.05          # strict: a gain needs lower > 1.05
SPREAD_LIMIT = 0.1             # every spread must be <= 0.1
#: Native speed-rule versions (ticket 66, decided by Yan-Ru 2026-10-04). A campaign file without
#: `protocol.speed_rule` keeps the range rule; protocols frozen under it keep their meaning.
RANGE_RULE = "swdb.speed_rule.range.v1"
CI_WIDTH_RULE = "swdb.speed_rule.ci_width.v1"
#: Ticket 72 (2026-10-04 ET, agent-decided under Yan-Ru's delegation; revisable): as v1, but the A/A
#: pilot gates only on the campaign's selection baseline (`base_source`); other roles are reported.
CI_WIDTH_RULE_V2 = "swdb.speed_rule.ci_width.v2"
CI_RULES = (CI_WIDTH_RULE, CI_WIDTH_RULE_V2)
LEVEL_SPLIT_MIN_RATIO = 1.08   # ticket 72: two-level trials when the largest adjacent ratio is >= 1.08
#: Ticket 73 (2026-10-05 ET): a provider at capacity is an uncounted D7 outcome. The call is retried
#: after these waits (seconds); past the bounded total wait the campaign stops `infrastructure_failure`.
CAPACITY_BACKOFF_S = (60, 120, 300, 600, 600, 600, 600)
CAPACITY_WAIT_S = 3600


#: Ticket 74 (2026-10-05 ET): a guard stop for the harness's own runtime limit is uncounted and retried
#: after GUARD_RETRY_S, at most GUARD_RETRIES times per call; then the campaign stops `infrastructure_failure`.
GUARD_RETRIES = 2
GUARD_RETRY_S = 30


def guard_retry_s():
    """The wait before a retry; SWDB_GUARD_RETRY_S overrides it for tests."""
    return float(os.environ.get("SWDB_GUARD_RETRY_S", GUARD_RETRY_S))


def capacity_backoff():
    """The backoff schedule; SWDB_CAPACITY_BACKOFF_S (comma-separated seconds) overrides it for tests."""
    raw = os.environ.get("SWDB_CAPACITY_BACKOFF_S")
    if raw is None:
        return CAPACITY_BACKOFF_S
    return tuple(float(x) for x in raw.split(",") if x.strip())
CI_WIDTH_LIMIT = 0.05          # relative 95% CI width (upper - lower) / ratio must be <= 0.05
CI_BLOCK_LENGTH = 4            # circular block bootstrap: 4 consecutive repetitions per block
AA_EQUIVALENCE = 1.05          # an A/A CI must lie strictly inside (1/1.05, 1.05)
CI_BOOTSTRAP_SEED = 20260925   # 2000 resamples, 95% percentile interval (the evaluator's policy)
#: The native paired collection every Extensa native block uses (D3; order seed pre-registered).
NATIVE_ORDER_SEED = 20260926
#: The spec's budget defaults (D5). A campaign may exceed one only with an approval
#: entry naming it. These are limits for validation, never values the loop assumes.
SPEC_BUDGETS = {"max_iterations": 8, "plateau_iterations": 4, "lane_hours": 24,
                "provider_calls_per_iteration": 3, "provider_calls_setup": 1, "disk_gb": 20, "lanes": 1}
DEFAULT_MAX_REPAIRS = 2        # D7: the ArchEvolve-mode repair limit
EXTENSA_SOURCE = {"repository": "MaizeHPC/MemAcc", "commit": "af3d6d7f7a69a72facdc3b95b42e78c952f44a76"}
LOGIN = re.compile(r"login|not logged in|unauthori[sz]ed|authentication|credentials", re.I)


class _Capacity(Exception):
    """Ticket 73: one provider call met transient unavailability (handled inside `_call`)."""


class _GuardInfrastructure(Exception):
    """Ticket 74: the guard stopped one provider call for its own runtime limit (handled inside `_call`)."""


class Paused(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


class Refused(Exception):
    """A target refuses one class's candidate artifact (tickets 56/57); never a campaign stop."""

    def __init__(self, reason, explanation, failed_checks=()):
        super().__init__(explanation)
        self.reason, self.explanation, self.failed_checks = reason, explanation, list(failed_checks)


class Stop(Exception):
    def __init__(self, reason, detail=""):
        super().__init__(detail or reason)
        self.reason = S.StopReason(reason)
        self.detail = detail


_now = writer.now      # code review F20 (2026-10-05 ET): the one timestamp helper


# --- campaign file (D5) ----------------------------------------------------------------

def _schema():
    """The campaign-file schema with the envelope's Extensa campaign-ID definition (one pattern)."""
    from swdb.schemas import campaign_id_def
    schema = json.loads((paths.SCHEMAS / "extensa_campaign.schema.json").read_text())
    schema.setdefault("$defs", {})["extensa_campaign_id"] = campaign_id_def(paths.SCHEMAS)
    return schema


def campaign_problems(data):
    """Every reason a campaign file is refused (schema plus D5's rules)."""
    if not isinstance(data, dict):
        return ["a campaign file must be a mapping"]
    problems = [f"{'.'.join(map(str, e.absolute_path)) or '-'}: {e.message}"
                for e in Draft202012Validator(_schema()).iter_errors(data)]
    if problems:
        return problems
    from swdb import campaign_targets
    from swdb.library import authorized_reviewer
    target, proto = data["target"], data["protocol"]
    problems += campaign_targets.ADAPTERS[target].file_problems(data)
    if proto["region_pairs"]:
        problems.append("protocol.region_pairs: Extensa protocols have no region pairs")
    if data["label"] != LABEL:
        problems.append(f"label: must be {LABEL!r}")
    roles = [b["role"] for b in data["baselines"]]
    if len(set(roles)) != len(roles):
        problems.append("baselines: each role appears once")
    if data["base_source"] not in roles:
        problems.append("base_source: must name one of the baselines (the selection baseline)")
    classes = [c["class"] for c in data["workload_classes"]]
    if len(set(classes)) != len(classes):
        problems.append("workload_classes: each class appears once")
    approval = data.get("approval") or {}
    raised = set(approval.get("raised_budgets") or [])
    for key, limit in SPEC_BUDGETS.items():
        if key == "lanes":
            continue
        if data["budgets"][key] > limit and key not in raised:
            problems.append(f"budgets.{key}: {data['budgets'][key]} exceeds the spec default {limit} "
                            "without an approval entry naming it")
    if data["budgets"]["lanes"] == 2 and not approval.get("two_lanes"):
        problems.append("budgets.lanes: two lanes require an approval entry (two_lanes: true)")
    if approval and not authorized_reviewer(approval.get("by")):
        problems.append("approval.by: Extensa campaign approvals are Yan-Ru Jhou's")
    return problems


def load_campaign(path):
    path = Path(path)
    try:
        data = yamlio.load(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise UsageError(f"cannot read campaign file {path}: {exc}") from None
    problems = campaign_problems(data)
    if problems:
        raise Failure("campaign file refused:\n" + "\n".join(f"  {p}" for p in problems))
    return data, artifacts.file_hash(path)


def campaigns_root(records_dir):
    records_dir = Path(records_dir)
    if records_dir.resolve() == paths.RECORDS.resolve():
        return paths.HOME / "campaigns" / "extensa"
    return records_dir.parent / "campaigns" / "extensa"


def validate_campaign_dir(records_dir):
    """`swdb validate` checks every campaign file under campaigns/extensa/."""
    root = campaigns_root(records_dir)
    found = []
    if not root.is_dir():
        return found
    for path in sorted(root.glob("*.y*ml")):
        try:
            data = yamlio.load(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            found.append(Problem(str(path), "-", f"not valid YAML: {exc}"))
            continue
        for problem in campaign_problems(data):
            field, _, reason = problem.partition(": ")
            found.append(Problem(str(path), field, reason))
        if isinstance(data, dict) and data.get("id") and data["id"] != path.stem:
            found.append(Problem(str(path), "id", "the campaign file is named after its ID"))
    return found


# --- protocol and speed rule (ticket 53) -------------------------------------------------

class SpeedRule:
    """The Extensa campaign's speed rule: its frozen settings, a comparison's verdict and the A/A gate.

    Code review F1 (2026-10-05 ET): one object instead of copies of the evaluator's decision. A real
    target's comparison carries the evaluator's `decision.state` (`swdb.bfs_protocol.decide` under the
    protocol this rule froze); that state is the verdict, with `regression` read as `no_gain`. A
    contract-fixture comparison (`fixture_comparison`, numbers from the fixture file) is judged from
    its numbers by the same rule. `profitability()` and `apply()` are byte-identical to the
    functions they replace: they feed frozen protocol identities."""

    VERDICTS = {"gain": "gain", "no_gain": "no_gain", "inconclusive": "inconclusive", "regression": "no_gain"}

    def __init__(self, name=RANGE_RULE, point_ratios=False):
        self.name, self.point_ratios = name, point_ratios

    @classmethod
    def of(cls, campaign):
        from swdb.campaign_targets import ADAPTERS
        return cls(campaign["protocol"].get("speed_rule", RANGE_RULE), ADAPTERS[campaign["target"]].POINT_RATIOS)

    @property
    def ci(self):
        """True for the CI-width rules (ticket 66, 72)."""
        return self.name in CI_RULES

    @property
    def reports_ci_width(self):
        """A comparison row carries its upper bound and relative CI width (native CI-width rule)."""
        return self.ci and not self.point_ratios

    def profitability(self):
        """The campaign-level profitability settings every adapter freezes."""
        if self.ci:
            return {"minimum_speedup": GAIN_THRESHOLD, "speed_rule": self.name,
                    "gate": {"statistic": CI_WIDTH_GATE, "maximum": CI_WIDTH_LIMIT},
                    "block_length": CI_BLOCK_LENGTH, "aa_equivalence": AA_EQUIVALENCE,
                    "rule": "relative 95% CI width at most the gate; then the lower bound of the same CI "
                            "strictly above the minimum"}
        return {"minimum_speedup": GAIN_THRESHOLD, "maximum_relative_spread": SPREAD_LIMIT,
                "rule": "lower bound strictly above the minimum; every spread at most the maximum"}

    @staticmethod
    def apply(frozen, settings):
        """Write the campaign's speed rule into a native protocol's frozen settings (ticket 66).

        The range rule sets `maximum_relative_spread`; the CI-width rule sets the circular block
        analysis, its block length and `profitability.gate`, and removes `maximum_relative_spread`."""
        profitability = settings["profitability"]
        frozen["profitability"]["minimum_speedup"] = profitability["minimum_speedup"]
        if profitability.get("speed_rule") not in CI_RULES:
            frozen["profitability"]["maximum_relative_spread"] = profitability["maximum_relative_spread"]
            return frozen
        from swdb.bfs_native_pair import METHOD
        from swdb.bfs_protocol import ANALYSIS_CIRCULAR_BLOCK
        frozen["profitability"].pop("maximum_relative_spread", None)
        frozen["profitability"]["gate"] = dict(profitability["gate"])
        frozen["profitability"]["bootstrap_seed"] = CI_BOOTSTRAP_SEED    # pre-registered (ticket 66)
        frozen["sampling"].setdefault("collection", {"method": METHOD, "order_seed": NATIVE_ORDER_SEED})
        frozen["sampling"]["analysis"] = ANALYSIS_CIRCULAR_BLOCK
        frozen["sampling"]["block_length"] = profitability["block_length"]
        return frozen

    @staticmethod
    def relative_width(comparison):
        """(upper - lower) / ratio of one comparison."""
        return (comparison["upper"] - comparison["lower"]) / comparison["ratio"]

    def verdict(self, comparison):
        """`gain`, `no_gain` or `inconclusive`: the evaluator's state, or the rule on fixture numbers."""
        state = comparison.get("state")
        if state in self.VERDICTS:
            return self.VERDICTS[state]
        if self.point_ratios:
            return "gain" if comparison["ratio"] > GAIN_THRESHOLD else "no_gain"
        if self.ci:
            if self.relative_width(comparison) > CI_WIDTH_LIMIT:
                return "inconclusive"
        elif any(s > SPREAD_LIMIT for s in comparison["spreads"]):
            return "inconclusive"
        return "gain" if comparison["lower"] > GAIN_THRESHOLD else "no_gain"

    def pilot_passes(self, block):
        """One A/A block: range rule, spread at most 0.1; CI-width rule (ticket 66), relative CI width at
        most 0.05 and the CI strictly inside (1/1.05, 1.05)."""
        if not self.ci:
            return block["spread"] <= SPREAD_LIMIT
        return (self.relative_width(block) <= CI_WIDTH_LIMIT
                and 1 / AA_EQUIVALENCE < block["lower"] and block["upper"] < AA_EQUIVALENCE)

    def gating_roles(self, roles, base_source):
        """Roles whose A/A block gates a class: every role, or (ci_width.v2, ticket 72) the selection baseline."""
        return [base_source] if self.name == CI_WIDTH_RULE_V2 else list(roles)


def speed_rule(campaign):
    """The Extensa campaign's native speed-rule version (absent: the range rule)."""
    return campaign["protocol"].get("speed_rule", RANGE_RULE)


def protocol_settings(campaign):
    """The campaign-level frozen settings every adapter freezes into one protocol."""
    from swdb.campaign_targets import ADAPTERS
    proto = campaign["protocol"]
    return {"target": campaign["target"], "roi": proto["roi"], "threads": proto["threads"],
            "repetitions": proto["repetitions"], "sources": list(proto["sources"]), "region_pairs": [],
            "differences": proto["differences"],
            "evidence_basis": ADAPTERS[campaign["target"]].EVIDENCE_BASIS,
            "profitability": SpeedRule.of(campaign).profitability(),
            "workloads": {c["class"]: c["workload"] for c in campaign["workload_classes"]}}


# Module-level forms of the SpeedRule methods (kept for callers and tests).
apply_speed_rule = SpeedRule.apply
relative_ci_width = SpeedRule.relative_width


def speed_verdict(comparison, target, rule=RANGE_RULE):
    from swdb.campaign_targets import ADAPTERS
    return SpeedRule(rule, ADAPTERS[target].POINT_RATIOS).verdict(comparison)


def pilot_gating_roles(rule, roles, base_source):
    return SpeedRule(rule).gating_roles(roles, base_source)


def pilot_passes(block, rule=RANGE_RULE):
    return SpeedRule(rule).pilot_passes(block)


def level_mix(times):
    """Ticket 72 (reporting only): split one side's sorted ROI times of one source at the largest
    adjacent ratio; at least LEVEL_SPLIT_MIN_RATIO means two levels, the upper group being slow."""
    xs = sorted(times)
    if len(xs) < 2:
        return {"levels": 1, "slow_trials": 0, "trials": len(xs), "slow_share": 0.0}
    split = max(range(1, len(xs)), key=lambda i: xs[i] / xs[i - 1])
    ratio = xs[split] / xs[split - 1]
    if ratio < LEVEL_SPLIT_MIN_RATIO:
        return {"levels": 1, "slow_trials": 0, "trials": len(xs), "slow_share": 0.0,
                "largest_adjacent_ratio": ratio}
    fast, slow = xs[:split], xs[split:]
    fast_median, slow_median = statistics.median(fast), statistics.median(slow)
    return {"levels": 2, "slow_trials": len(slow), "trials": len(xs), "slow_share": len(slow) / len(xs),
            "fast_median_s": fast_median, "slow_median_s": slow_median,
            "level_ratio": slow_median / fast_median, "largest_adjacent_ratio": ratio}


def level_mix_of(evaluation):
    """Per-source level mix of one evaluation's timing, plus the side's overall slow share."""
    by_source = {}
    for row in evaluation.get("timing", []):
        by_source.setdefault(row["source_position"], []).append(row["duration_s"])
    sources = {str(pos): level_mix(times) for pos, times in sorted(by_source.items())}
    total = sum(v["trials"] for v in sources.values())
    return {"by_source_position": sources,
            "slow_share": (sum(v["slow_trials"] for v in sources.values()) / total) if total else 0.0}


LEVEL_RANK = {"certified": 2, "uncertified": 1}


def selection_key(candidate):
    return (LEVEL_RANK[candidate["level"]], candidate["selection"]["lower"])


def select(candidates):
    """Per class: (best, faster_uncertified, verdict). Rejected artifacts never compete.

    Certified before uncertified, then by the lower bound (point ratio on gem5) against
    the base-source baseline; only gain artifacts can be best; an uncertified one is best
    only when no certified one passes."""
    eligible = [c for c in candidates if c["level"] in LEVEL_RANK and c.get("selection")]
    passing = [c for c in eligible if c["selection"]["verdict"] == "gain"]
    if not passing:
        if eligible and all(c["selection"]["verdict"] == "inconclusive" for c in eligible):
            return None, [], "inconclusive"
        return None, [], "no_gain"
    best = max(passing, key=selection_key)
    faster = [c["id"] for c in passing if c["level"] == "uncertified" and best["level"] == "certified"
              and c["selection"]["lower"] > best["selection"]["lower"]]
    return best, sorted(faster), "gain"


# --- provider roles ------------------------------------------------------------------------

def _roles():
    from swdb import provider_roles
    rewrite = provider_roles.Role("extensa_rewriting", {
        "type": "object", "additionalProperties": False,
        "required": ["patch", "contracts", "knobs", "unresolved"],
        "properties": {"patch": {"type": "string"},
                       "contracts": {"type": "array", "items": {"type": "string"}},
                       # 2026-10-04 ET (ticket 57, campaign a1): strict structured output needs a fixed
                       # object shape, so knob assignments are a list of {class, name, value} rows.
                       "knobs": {"type": "array", "items": {
                           "type": "object", "additionalProperties": False, "required": ["class", "name", "value"],
                           "properties": {"class": {"type": "string"}, "name": {"type": "string"},
                                          "value": {"type": ["number", "string"]}}}},
                       "unresolved": {"type": "array", "items": {"type": "string"}}}})
    profiling = provider_roles.Role("extensa_profiling", {
        "type": "object", "additionalProperties": False, "required": ["notes"],
        "properties": {"notes": {"type": "array", "items": {"type": "string"}}}})
    return {"rewriting": rewrite, "repair": rewrite, "profiling": profiling,
            "independent_test_generation": provider_roles.ROLES["independent_test_generation"]}


def knobs_by_class(response):
    """{class: {knob: value}} from the rewrite role's knob rows (a mapping is accepted as is)."""
    knobs = response.get("knobs") or {}
    if isinstance(knobs, dict):
        return knobs
    out = {}
    for row in knobs:
        value = row["value"]
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        out.setdefault(row["class"], {})[row["name"]] = value
    return out


REWRITE_PROMPT = """\
Extensa-mode rewrite, campaign {campaign}, iteration {iteration}.
Rewrite the base source under `source/` within the regions in REGIONS.json. You may use
the rewrite contracts under `contracts/` (name the ones you use in `contracts`) and give at
most one knob assignment per workload class in `knobs`, one row {{class, name, value}} per knob
(classes: {classes}); knob values
must stay inside the contract's declared ranges; the evaluator defines each assigned value
as the macro `SWDB_KNOB_<KNOB NAME IN UPPER CASE>` at the top of `bfs.cc` (give each knob a
default with `#ifndef`). When you name a contract, the evaluator adds its canonical lowering
header `swdb_dxc_lowering.hpp`; patch `bfs.cc` only.{history} Return ONE
unified diff against `source/` in `patch`. Do not state performance outcomes.
Work only by reading the files listed here and writing your answer: read no other path, do not
use shell heredocs, `git apply`, `patch` or any command that runs or applies generated text; put
the diff only in `patch`. To read, use only `cat FILE`, `nl -ba FILE`, `sed -n 'A,Bp' FILE` with
literal line numbers, `grep -n 'TEXT' FILE`, `ls DIR` and `wc -l FILE`, one command at a time,
with no pipes, awk, command substitution or redirection. Workspace files: {files}.
"""


def rewrite_prompt(campaign_id, iteration, classes, files):
    """The rewrite prompt names only the files the workspace holds (2026-10-04 ET, campaign a2:
    the provider audit refused a read of an absent `best/` and FEEDBACK.json)."""
    history = []
    if "library/swdb_dxc_lowering.hpp" in files:
        history.append(" `library/swdb_dxc_lowering.hpp` is that header (read it for the intrinsic calls; "
                       "`#include \"swdb_dxc_lowering.hpp\"` from `bfs.cc`) and `library/intrinsics/` describes "
                       "each intrinsic.")
        if any(f.startswith("library/intrinsics/notes/") for f in files):
            # Ticket 64 (campaign a6 set last_i to -1; ticket 58 passed values as registers).
            history.append(" `library/intrinsics/notes/` states each intrinsic's operand kinds: an operand "
                           "named `*_reg` is a register handle from the thread's `dxc_context` whose value is "
                           "set by `__dxc_const_i32`, never a plain value; a range-loop batch starts with "
                           "`last_i_reg` = 0 and `last_j_reg` = -1.")
    best = sorted(f for f in files if f.startswith("best/"))
    if best:
        history.append(" " + ", ".join(f"`{f}`" for f in best) + " hold this campaign's current per-class best patches.")
    if "FEEDBACK.json" in files:
        history.append(" `FEEDBACK.json` holds the previous iteration's feedback.")
    if "PROTECTED.json" in files:
        # Ticket 73 (2026-10-05 ET): campaign a7's iteration 1 edited the protected verifier.
        history.append(" `PROTECTED.json` lists protected evaluator regions (for example the `BFSVerifier` "
                       "function of `bfs.cc`) by their lines in the workspace copy; a patch that touches any "
                       "of them is rejected, so never edit them. In REGIONS.json, `source.lines` number the "
                       "registered full-source revision; edit the region's function at its `workspace` lines "
                       "in `source/`.")
    return REWRITE_PROMPT.format(campaign=campaign_id, iteration=iteration, classes=", ".join(classes),
                                 history="".join(history), files=", ".join(f"`{f}`" for f in sorted(files)))


# --- the loop --------------------------------------------------------------------------------

class Campaign:
    def __init__(self, args):
        self.args = args
        self.file = Path(args.file)
        self.data, self.sha256 = load_campaign(self.file)
        self.cid = self.data["id"]
        runs_root = Path(args.runs_root or self.data["runs_root"])
        self.folder = artifacts.external_directory(runs_root) / "extensa" / self.cid
        self.store_dir = self.folder / "records"
        self.state_file = self.folder / "state.json"
        self.team = Path(args.records)
        self.library_root = Path(args.library) if args.library else paths.HOME / "library"
        self.budget = S.SearchBudget.from_mapping({k: self.data["budgets"][k] for k in S.BUDGET_KEYS},
                                                  f"{self.file}@{self.sha256}")
        self.max_repairs = self.data["budgets"].get("max_repairs", DEFAULT_MAX_REPAIRS)
        self.classes = [c["class"] for c in self.data["workload_classes"]]
        self.all_classes = list(self.classes)
        self.roles = [b["role"] for b in self.data["baselines"]]
        from swdb import rewrite
        self.provider_config = rewrite.configuration(Path(args.provider_config))
        self.query = self.data["regions"] == "query"
        self.applied_contracts = None     # query mode: contracts the site finder applied this iteration
        self.rule = SpeedRule.of(self.data)
        if args.fixture:
            from swdb.campaign_fixture import FixtureAdapter
            self.adapter = FixtureAdapter(args.fixture, self.data, self.team, self.store_dir, self.folder)
        else:
            # Tickets 56/57 (2026-10-04 ET): the campaign's target selects its real adapter.
            from swdb import campaign_targets
            data = {**self.data, "runs_root": str(runs_root)}
            self.adapter = campaign_targets.adapter_for(data, self.team, self.store_dir, self.folder,
                                                        self.library_root, **getattr(args, "adapter_options", {}))

    # state ------------------------------------------------------------------------------
    def _load_state(self):
        if self.state_file.is_file():
            state = json.loads(self.state_file.read_text())
            if state["campaign_sha256"] != self.sha256:
                raise Failure("the campaign file changed since the campaign started; a changed campaign is a new campaign")
            return state
        return None

    def _save(self):
        self.state["ledger"] = self.ledger.to_state()
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=2))
        tmp.replace(self.state_file)

    @contextlib.contextmanager
    def _tags(self):
        previous = dict(workflow.CREATION_TAGS)
        workflow.CREATION_TAGS.clear()
        workflow.CREATION_TAGS.update(mode=MODE, campaign=self.cid)
        try:
            yield
        finally:
            workflow.CREATION_TAGS.clear()
            workflow.CREATION_TAGS.update(previous)

    # budgets ----------------------------------------------------------------------------
    def _step(self, step, *, job=False):
        """Refuse a step whose budgeted time would exceed the lane-hour cap (and, for a
        job, the disk cap and the dispatch preflight)."""
        if self.state["lane_hours"] + self.adapter.step_budget_hours(step) > self.budget.lane_hours:
            raise Stop("lane_hours", f"the next {step} step would exceed {self.budget.lane_hours} lane-hours")
        if job:
            planned = self.adapter.planned_bytes()
            used = _du(self.folder)
            self.state["disk_bytes_peak"] = max(self.state.get("disk_bytes_peak", 0), used)
            if used + planned > self.budget.disk_gb * 1e9:
                raise Stop("disk", f"campaign folder holds {used} bytes; the next job would exceed {self.budget.disk_gb} GB")
            try:
                receipt = self.adapter.preflight(planned, step=step)
            except Failure as exc:
                raise Stop("disk" if "run disk" in str(exc) else "infrastructure_failure",
                           f"dispatch preflight refused: {exc}") from None
            if receipt:
                self.state.setdefault("preflights", []).append({"step": step, "state": receipt.get("state")})

    def _spent(self, step, started):
        hours = self.adapter.step_hours(step)
        if not hours and started is not None:
            hours = (time.monotonic() - started) / 3600
        self.state["lane_hours"] += hours

    # provider calls (D7) -------------------------------------------------------------------
    def _call(self, kind, files, prompt, iteration_row):
        """One provider call. Ticket 73: a provider at capacity is recorded uncounted and retried after
        a backoff; past CAPACITY_WAIT_S of waiting the campaign stops `infrastructure_failure`.
        Ticket 74: a guard stop for the harness's own runtime limit is recorded uncounted and retried
        at most GUARD_RETRIES times; then the campaign stops `infrastructure_failure`."""
        waited, schedule, guard_stops = 0.0, list(capacity_backoff()), 0
        while True:
            try:
                return self._call_once(kind, files, prompt, iteration_row)
            except _GuardInfrastructure as stopped:
                guard_stops += 1
                if guard_stops > GUARD_RETRIES:
                    raise Stop("infrastructure_failure", f"the provider guard stopped {guard_stops} consecutive "
                               f"{kind} calls for its own runtime limit: {stopped}") from None
                delay = guard_retry_s()
                iteration_row["provider_calls"][-1]["retry_after_s"] = delay
                time.sleep(delay)
            except _Capacity as capacity:
                delay = schedule.pop(0) if schedule else None
                if delay is None or waited + delay > CAPACITY_WAIT_S:
                    raise Stop("infrastructure_failure",
                               f"the provider stayed unavailable after {waited:.0f} s of backoff: {capacity}") from None
                iteration_row["provider_calls"][-1]["backoff_s"] = delay
                time.sleep(delay)
                waited += delay

    def _call_once(self, kind, files, prompt, iteration_row):
        from swdb import provider_adapters, provider_roles
        self._step("provider")
        total = self.budget.provider_calls_setup + self.budget.provider_calls_per_iteration * self.budget.max_iterations
        if self.ledger.counted_calls >= total:
            if kind == "rewriting":
                raise Stop("provider_calls", f"the campaign's {total} counted provider calls are spent")
            iteration_row.setdefault("refused_calls", []).append({"role": kind, "reason": "campaign total spent"})
            return None
        try:
            call = self.ledger.open_call(kind, f"{self.cid}.call{len(self.ledger.calls) + 1}")
        except S.CallRefused as exc:
            iteration_row.setdefault("refused_calls", []).append({"role": kind, "reason": str(exc)})
            return None
        folder = self.folder / "provider" / call.invocation
        started = time.monotonic()
        outcome, response, error = S.CallOutcome.COMPLETED, None, None
        try:
            response, _meta = provider_roles.run(_roles()[kind], files, prompt, self.provider_config, folder)
        except provider_adapters.ProviderCapacity as exc:
            outcome, error = S.CallOutcome.PROVIDER_CAPACITY, exc
        except provider_adapters.ProviderUnavailable as exc:
            outcome, error = S.CallOutcome.USAGE_LIMIT, exc
        except provider_adapters.GuardInfrastructure as exc:     # ticket 74
            outcome, error = S.CallOutcome.GUARD_INFRASTRUCTURE, exc
        except Failure as exc:
            text = str(exc)
            stderr = folder / "stderr.txt"
            text += stderr.read_text(errors="replace") if stderr.is_file() else ""
            outcome = (S.CallOutcome.LOGIN if LOGIN.search(text) else
                       S.CallOutcome.TIMEOUT if "timed out" in text or "timeout" in text else
                       S.CallOutcome.MALFORMED_OUTPUT if "structured" in text or "JSON" in text else
                       S.CallOutcome.GUARD_REFUSED if "guard" in text or "audit" in text else S.CallOutcome.FAILED)
            error = exc
        self._spent("provider", started)
        self.ledger.close_call(call, outcome)
        meta = {}
        receipt = folder / "provider.json"
        if receipt.is_file():
            meta = json.loads(receipt.read_text())
        provider = self.data["provider"]
        iteration_row["provider_calls"].append({
            "role": kind, "invocation": call.invocation, "outcome": outcome.value, "counted": call.counted,
            "model": meta.get("model") or provider["model"], "effort": meta.get("effort") or provider["effort"],
            "classification": meta.get("classification")})
        if outcome == S.CallOutcome.PROVIDER_CAPACITY:
            raise _Capacity(str(error))
        if outcome == S.CallOutcome.GUARD_INFRASTRUCTURE:
            iteration_row["provider_calls"][-1]["guard_reason"] = str(error)[:1000]
            raise _GuardInfrastructure(str(error))
        if outcome in S.UNCOUNTED_CALL_OUTCOMES:
            raise Paused(outcome.value)
        if error is not None:
            return None
        return response

    # setup -----------------------------------------------------------------------------------
    def _setup(self):
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.adapter.prepare()
        frozen = self.adapter.freeze_protocol(protocol_settings(self.data))
        self.adapter.protocol_id = frozen["id"]
        self.state["protocol"] = {"id": frozen["id"], "identity_sha256": frozen["identity_sha256"],
                                  "settings": frozen["settings"]}
        if frozen.get("by_role"):          # ticket 56: one frozen native protocol per baseline role
            self.state["protocol"]["by_role"] = frozen["by_role"]
        self.state["setup_done"] = True

    def _pilot(self):
        """Native A/A pilot (D3): a class with a failing A/A block is not timed.

        Ticket 64 (2026-10-04 ET, agent-decided under Yan-Ru's delegation; revisable): the gate
        applies per class. An unstable class stops as `baseline_unstable` for that class only;
        the campaign stops with `baseline_unstable` only when every class is unstable. The
        threshold is unchanged and never loosened inside a campaign.

        Ticket 66 (2026-10-04 ET, decided by Yan-Ru): under the CI-width rule a block fails when
        its relative CI width exceeds 0.05 or its CI leaves (1/1.05, 1.05); spreads are recorded
        as description only."""
        rule = self.rule
        gating = rule.gating_roles(self.roles, self.data["base_source"])
        spreads, intervals, failed, mixes = {}, {}, {}, {}
        for cls in self.classes:
            for role in self.roles:
                self._step("evaluation", job=True)
                started = time.monotonic()
                block = self.adapter.pilot(cls, role)
                spreads.setdefault(cls, {})[role] = block["spread"]
                if rule.ci:
                    intervals.setdefault(cls, {})[role] = {
                        "ratio": block["ratio"], "lower": block["lower"], "upper": block["upper"],
                        "relative_width": rule.relative_width(block), "passed": rule.pilot_passes(block),
                        "gates": role in gating}
                if block.get("level_mix") is not None:
                    mixes.setdefault(cls, {})[role] = block["level_mix"]
                if role in gating and not rule.pilot_passes(block):
                    failed.setdefault(cls, []).append(role)
                if block.get("other_socket") is not None:
                    self.state.setdefault("pilot_other_socket", {}).setdefault(cls, {})[role] = block["other_socket"]
                if block.get("isolation") is not None:
                    self.state.setdefault("pilot_isolation", {}).setdefault(cls, {})[role] = block["isolation"]
                self._spent("evaluation", started)
        unstable = [cls for cls in self.classes if failed.get(cls)]
        self.state["pilot"] = {"spreads_by_class_and_role": spreads, "passed": not unstable,
                               "unstable_classes": unstable}
        if rule.ci:
            self.state["pilot"].update(speed_rule=rule.name, ci_by_class_and_role=intervals,
                                       gate={"maximum_relative_ci_width": CI_WIDTH_LIMIT,
                                             "aa_interval": [1 / AA_EQUIVALENCE, AA_EQUIVALENCE]},
                                       gating_roles=gating)
        if mixes:
            self.state["pilot"]["level_mix_by_class_and_role"] = mixes
        if self.state.get("pilot_other_socket"):
            self.state["pilot"]["other_socket_by_class_and_role"] = self.state["pilot_other_socket"]
        if self.state.get("pilot_isolation"):
            self.state["pilot"]["isolation_by_class_and_role"] = self.state["pilot_isolation"]
        self._apply_pilot()
        if not self.classes:
            self.ledger.terminate(S.StopReason.BASELINE_UNSTABLE)
            self.state["stop_detail"] = ("baseline A/A CI-width gate failed in every class" if rule.ci
                                         else "baseline A/A spread exceeds 0.1 in every class")

    def _apply_pilot(self):
        """Time only the classes whose A/A pilot passed (also after a resume)."""
        unstable = (self.state.get("pilot") or {}).get("unstable_classes")
        if unstable is None and (self.state.get("pilot") or {}).get("passed") is False:
            unstable = list(self.all_classes)      # a pilot recorded before the per-class gate
        self.classes = [cls for cls in self.all_classes if cls not in (unstable or [])]

    def _setup_call(self):
        if self.budget.provider_calls_setup < 1 or self.state.get("setup_call_done"):
            return
        row = {"provider_calls": []}
        files = {f"source/{k}": v for k, v in self.adapter.source_files().items()}
        self._call("profiling", files, "Profile the base source; return notes only.", row)
        self.state["setup_calls"] = row["provider_calls"]
        self.state["setup_call_done"] = True

    # regions (ticket 55) ----------------------------------------------------------------------
    def _find_sites(self):
        """Run the query site finder over the team store and the campaign's library."""
        from swdb import site_finder
        return site_finder.find(self.team, self.data, library=self.library_root,
                                db_path=site_finder.default_db_path(self.folder))

    def _regions(self, row):
        """The iteration's region rows: the fixed list, or the site finder's chosen regions,
        each with why it was chosen; rejected sites are kept with their reasons."""
        if not self.query:
            self.current_regions = list(self.data["regions"])
            return [{"id": r, "reason": "fixed region list (campaign file)"} for r in self.data["regions"]]
        from swdb import site_finder
        result = self._find_sites()
        row["site_finder"] = {"format": result["format"], "query_sha256": result["query_sha256"],
                              "parameters": result["parameters"], "database": result["database"],
                              "rejected": [{k: r[k] for k in ("entry", "region", "reason")} for r in result["rejected"]]}
        self.state["site_finder"] = {"format": result["format"], "query_sha256": result["query_sha256"],
                                     "parameters": result["parameters"]}
        if not result["regions"]:
            raise Stop("infrastructure_failure", "the site finder chose no region: " + "; ".join(
                f"{r['entry']}: {r['reason']}" for r in result["rejected"])[:2000])
        self.current_regions = [{"id": r["id"], "source": r["source"], "statements": r["statements"],
                                 "applications": [{"entry": a["entry"], "contract": a["contract"], "kind": a["kind"]}
                                                  for a in r["applications"]]} for r in result["regions"]]
        self.applied_contracts = {a["contract"] for r in result["regions"] for a in r["applications"] if a["contract"]}
        return site_finder.region_rows(result)

    def _check_sites(self):
        """Query mode: refuse to start a campaign for which the site finder chooses no region."""
        result = self._find_sites()
        if not result["regions"]:
            raise Failure("regions: query chose no region; rejected sites: " + ("; ".join(
                f"{r['entry']} {r['region'] or ''}: {r['reason']}" for r in result["rejected"]) or "none"))

    # iteration --------------------------------------------------------------------------------
    def _workspace(self, iteration):
        from swdb.library import Library
        library = Library(self.library_root)
        files = {f"source/{k}": v for k, v in self.adapter.source_files().items()}
        for cid in self.data["library"]["contracts"]:
            path = library.files.get(cid)
            if path is None:
                raise Failure(f"campaign contract {cid} is not in the library")
            files[f"contracts/{cid}.yaml"] = path.read_text()
            # 2026-10-04 ET (attempt a4): a contract edit needs the intrinsics' C++ interface. The
            # workspace holds each used intrinsic's entry and the target's canonical lowering
            # header as read-only references (as ticket 58's arms did); no evaluator input.
            for iid in (library.get(cid) or {}).get("uses_intrinsics", []):
                ipath = library.files.get(iid)
                if ipath is not None:
                    files[f"library/intrinsics/{ipath.name}"] = ipath.read_text()
                    # Ticket 64: the non-normative usage note (operand kinds, conventions) rides
                    # along; it is outside the entry, so the entry's hash and tier stay unchanged.
                    note = ipath.parent / "notes" / (ipath.stem + ".md")
                    if note.is_file():
                        files[f"library/intrinsics/notes/{note.name}"] = note.read_text()
        if self.data["library"]["contracts"]:
            files.update({f"library/{name}": text for name, text in self.adapter.reference_files().items()})
        regions = self.current_regions if self.query else self.data["regions"]
        # Ticket 73 (2026-10-05 ET): workspace line spans for each region and the protected regions.
        if regions:
            regions = self.adapter.workspace_region_lines(regions)
        files["REGIONS.json"] = json.dumps({"regions": regions}, indent=2)
        rows = self.adapter.protected_regions()
        if rows:
            files["PROTECTED.json"] = json.dumps({
                "note": ("Evaluator inputs. A patch that changes any of these is rejected before it is "
                         "built. Never edit them."), "protected": rows}, indent=2)
        for cls, best in self.state["bests"].items():
            if best:
                files[f"best/{cls}.patch"] = best["patch"]
        if iteration > 1:
            files["FEEDBACK.json"] = json.dumps({"feedback": self.state["feedback"]}, indent=2)
        return files

    def _knob_problem(self, contracts, knobs):
        from swdb.library import Library, knob_problem
        return knob_problem(Library(self.library_root), contracts, knobs)

    def _contract_tier_problem(self, contracts):
        from swdb.library import Library
        from swdb.store import Store
        library = Library(self.library_root, Store(self.team))
        for cid in contracts:
            if cid not in self.data["library"]["contracts"]:
                return f"contract {cid} is outside the campaign's contracts"
            if self.applied_contracts is not None and cid not in self.applied_contracts:
                return f"contract {cid} applies to no region the site finder chose"
            if library.get(cid) is None:
                return f"contract {cid} is not in the library"
            if library.state(cid)["tier"] not in self.data["library"]["allowed_tiers"]:
                return f"contract {cid} is in a tier the campaign does not allow"
        return None

    def _iteration(self, iteration, row):
        files = self._workspace(iteration)
        response = self._call("rewriting", files, rewrite_prompt(self.cid, iteration, self.classes, files), row)
        if response is None:
            row["feedback_reasons"].append("provider_output_invalid")
            self.state["feedback"] = [S.Feedback("provider_output_invalid",
                                                 "The rewrite call returned no usable output.").to_dict()]
            return S.IterationOutcome.NOT_IMPROVED
        self._synthesis(iteration, row)
        feedback = []
        for cls in self.classes:
            candidate = self._artifact(iteration, cls, response, row, feedback)
            row["candidates"].append(candidate)
        improved = []
        for cls in self.classes:
            pool = [c for r in self.state["iterations"] + [row] for c in r["candidates"] if c["class"] == cls]
            best, _faster, _verdict = select(pool)
            previous = self.state["bests"].get(cls)
            if best and (previous is None or selection_key(best) > tuple(previous["key"])):
                self.state["bests"][cls] = {"id": best["id"], "key": list(selection_key(best)),
                                            "patch": best.pop("_patch", "")}
                improved.append(cls)
            for c in pool:
                c.pop("_patch", None)
        row["improved_classes"] = improved
        row["feedback_reasons"] = sorted({f["reason_code"] for f in feedback})
        self.state["feedback"] = feedback
        return S.IterationOutcome.IMPROVED if improved else S.IterationOutcome.NOT_IMPROVED

    def _artifact(self, iteration, cls, response, row, feedback):
        patch, contracts = response["patch"], list(response.get("contracts") or [])
        knobs = knobs_by_class(response).get(cls, {})
        entry = {"id": None, "class": cls, "patch_sha256": artifacts.digest(patch), "knobs": knobs,
                 "contracts": contracts, "certification": None, "comparisons": [], "level": None,
                 "selection": None, "_patch": patch}

        def reject(reason, explanation, **fields):
            entry["level"] = "rejected"
            entry["rejection"] = explanation
            feedback.append(S.Feedback(reason, explanation, {"class": cls, **fields}).to_dict())
            return entry

        claims = scan_patch_additions(patch)
        if claims:
            return reject("provider_output_invalid", "The patch text states a performance outcome.")
        problem = self._contract_tier_problem(contracts)
        if problem:
            return reject("provider_output_invalid", problem)
        problem = self._knob_problem(contracts, knobs)
        if problem:     # D7: rejected before certification, never a repair call
            return reject("knob_out_of_range", problem)
        try:
            return self._certified_and_evaluated(iteration, cls, entry, patch, knobs, contracts, row, feedback, reject)
        except Refused as refused:       # tickets 56/57: a target refusal rejects this class's artifact
            return reject(refused.reason, refused.explanation, failed_checks=refused.failed_checks)

    def _certified_and_evaluated(self, iteration, cls, entry, patch, knobs, contracts, row, feedback, reject):
        attempt = 0
        candidate = self.adapter.materialize(iteration, cls, patch, knobs, attempt, contracts=contracts)
        entry.update(id=candidate["id"], artifact_sha256=candidate["sha256"])
        self.adapter.admit(candidate, contracts)
        if not contracts:
            entry["level"] = "uncertified"
            feedback.append(S.Feedback("uncertified_edit", "The edit used no rewrite contract.",
                                       {"class": cls}).to_dict())
        else:
            tests = self._test_generation(contracts, row)
            while True:
                self._step("certification", job=True)
                started = time.monotonic()
                outcome = self.adapter.certify(candidate, contracts, iteration, cls, attempt, tests=tests)
                self._spent("certification", started)
                entry["certification"] = {"record": outcome["record"], "outcome": outcome["outcome"],
                                          "level_at_summary": outcome["outcome"]}
                if outcome.get("failed_checks"):
                    entry["certification"]["failed_checks"] = list(outcome["failed_checks"])
                if outcome["outcome"] == "certified":
                    entry["level"] = "certified"
                    feedback.append(S.Feedback("certified", "Certification passed.", {"class": cls}).to_dict())
                    break
                # Ticket 64: name the failing check and its public precondition (never run output).
                # Ticket 76 (2026-10-05 ET): surviving controls reach the provider only as one
                # aggregate category; the campaign record keeps the detailed names.
                public = certification_feedback.public_checks(outcome["failed_checks"])
                named = certification_feedback.explanation(public)
                if attempt >= self.max_repairs:
                    return reject("certification_failed", named, failed_checks=public)
                # 2026-10-04 ET: the repair workspace holds the failing patch, and the prompt names
                # only the files present (the provider audit refuses reads outside them).
                files = {**self._workspace(iteration), "CANDIDATE.patch": patch,
                         "CERTIFICATION.json": json.dumps({"class": cls, "failed_checks": public,
                                                           "messages": certification_feedback.messages(public)})}
                repaired = self._call("repair", files, "Repair: `CANDIDATE.patch` failed the certification checks "
                                      "named in `CERTIFICATION.json`; return a repaired patch.\n"
                                      + rewrite_prompt(self.cid, iteration, self.classes, files), row)
                if repaired is None:
                    return reject("certification_failed", named, failed_checks=public)
                attempt += 1
                patch = repaired["patch"]
                knobs = knobs_by_class(repaired).get(cls, knobs)
                entry.update(_patch=patch, patch_sha256=artifacts.digest(patch), knobs=knobs)
                # 2026-10-04 ET (final code review): a repaired patch passes the same leakage
                # scan as a first rewrite before it can become a candidate or `best/` input.
                if scan_patch_additions(patch):
                    return reject("provider_output_invalid", "The patch text states a performance outcome.")
                problem = self._knob_problem(contracts, knobs)
                if problem:
                    return reject("knob_out_of_range", problem)
                candidate = self.adapter.materialize(iteration, cls, patch, knobs, attempt, contracts=contracts)
                entry.update(id=candidate["id"], artifact_sha256=candidate["sha256"])
                self.adapter.admit(candidate, contracts)
        self._evaluate(iteration, cls, candidate, attempt, entry)
        selection = next((c for c in entry["comparisons"] if c["baseline_role"] == self.data["base_source"]), None)
        if selection:
            entry["selection"] = {"lower": selection["lower"], "verdict": selection["verdict"], "ratio": selection["ratio"]}
            feedback.append(S.Feedback("verdict_" + selection["verdict"], "Evaluator verdict for this class.",
                                       {"class": cls, "verdict": selection["verdict"], "ratio": selection["ratio"],
                                        "lower": selection["lower"], "spread": selection["spread"],
                                        "evidence_basis": protocol_settings(self.data)["evidence_basis"]}).to_dict())
        return entry

    def _test_generation(self, contracts, row):
        """D7: one independent test-generation call per contract per campaign, at first use."""
        tests = []
        for cid in contracts:
            if cid in self.state["tested_contracts"]:
                tests.extend(self.state["tested_contracts"][cid])
                continue
            from swdb.library import Library
            text = Library(self.library_root).files[cid].read_text()
            response = self._call("independent_test_generation", {f"contracts/{cid}.yaml": text},
                                  "Write differential-test inputs for this contract only.", row)
            generated = [t.get("path") for t in (response or {}).get("tests", [])]
            self.state["tested_contracts"][cid] = generated
            tests.extend(generated)
        return tests

    def _synthesis(self, iteration, row):
        """D7: synthesis calls are charged; entries enter the library only certified."""
        families = [f for f in self.data["library"].get("synthesize") or [] if f not in self.state["synthesized"]]
        for family in families:
            self._step("synthesis", job=True)
            try:
                call = self.ledger.open_call("synthesis", f"{self.cid}.call{len(self.ledger.calls) + 1}")
            except S.CallRefused as exc:
                row.setdefault("refused_calls", []).append({"role": "synthesis", "reason": str(exc)})
                return
            from swdb import library_operations
            started = time.monotonic()
            try:
                result = library_operations.synthesize(
                    family, library_root=self.library_root, records=self.store_dir,
                    provider_config=self.args.provider_config, runs=self.folder / "synthesis",
                    campaign=self.cid, goal="A correct, simple C++11 backend for this hook.")
                outcome = S.CallOutcome.COMPLETED
            except Failure as exc:
                # 2026-10-04 ET (final code review): D7 — usage-limit and login failures are
                # uncounted and pause the campaign; the family stays unsynthesized for the resume.
                from swdb import provider_adapters
                # Ticket 73: transient unavailability is uncounted too (it pauses here; a resume retries).
                # Ticket 74: a guard stop for the harness's own runtime limit is uncounted (it pauses here).
                outcome = (S.CallOutcome.PROVIDER_CAPACITY if isinstance(exc, provider_adapters.ProviderCapacity)
                           else S.CallOutcome.GUARD_INFRASTRUCTURE
                           if isinstance(exc, provider_adapters.GuardInfrastructure)
                           else S.CallOutcome.USAGE_LIMIT if isinstance(exc, provider_adapters.ProviderUnavailable)
                           else S.CallOutcome.LOGIN if LOGIN.search(str(exc)) else S.CallOutcome.FAILED)
                result = {"state": "failed", "reason": str(exc)}
            self._spent("synthesis", started)
            self.ledger.close_call(call, outcome)
            row["provider_calls"].append({"role": "synthesis", "invocation": call.invocation,
                                          "outcome": outcome.value, "counted": call.counted,
                                          "model": self.data["provider"]["model"],
                                          "effort": self.data["provider"]["effort"]})
            if outcome in S.UNCOUNTED_CALL_OUTCOMES:
                raise Paused(outcome.value)
            self.state["synthesized"][family] = {"state": result.get("state"), "entry": result.get("entry"),
                                                 "tier": result.get("tier")}

    def _evaluate(self, iteration, cls, candidate, attempt, entry):
        rule = self.rule
        for role in self.roles:
            self._step("evaluation", job=True)
            if not self.adapter.SHARED_BASELINE:
                # 2026-10-04 ET (final code review): the adapter's check honors the campaign's
                # approval.gem5_other_socket (ticket 64), exactly as the pilot does.
                refusal = self.adapter.other_gem5()
                if refusal:
                    raise Stop("infrastructure_failure", refusal)
                baseline_eval = None
            else:
                key = f"{cls}/{role}"
                if key not in self.state["baselines"]:
                    self.state["baselines"][key] = self.adapter.baseline_evaluation(cls, role)
                baseline_eval = self.state["baselines"][key]
            started = time.monotonic()
            result = self.adapter.compare(candidate, cls, role, iteration, attempt, baseline_evaluation=baseline_eval)
            self._spent("evaluation", started)
            verdict = rule.verdict(result)
            row = {"baseline_role": role, "comparison": result["comparison"],
                   "ratio": result["ratio"], "lower": result["lower"],
                   "spread": max(result["spreads"]), "verdict": verdict,
                   "baseline_evaluation": result["baseline_evaluation"]}
            if rule.reports_ci_width:
                row.update(upper=result["upper"], relative_ci_width=rule.relative_width(result))
            if result.get("level_mix") is not None:
                row["level_mix"] = result["level_mix"]
            entry["comparisons"].append(row)
            self._prune(result["evaluations"])

    def _prune(self, evaluation_ids):
        """ADR 0011: prune debug traces and checkpoint payloads right after the comparison,
        with a retention record, unless a team claim cites the run."""
        from swdb import retention
        from swdb.store import Store
        team = Store(self.team)
        for eid in evaluation_ids:
            store = Store(self.store_dir)
            evaluation = store.get(eid, "evaluation")
            if evaluation is None:
                continue
            if retention.team_state(store, eid) == "claimed" or retention.team_state(team, eid) == "claimed":
                self.state["kept_for_claims"].append(eid)
                continue
            entries = []
            for row in evaluation.get("raw_artifacts", []):
                folder = Path(row.get("path", ""))
                if not folder.is_dir():
                    continue
                for path in sorted(folder.rglob("*")):
                    if path.is_file() and not path.is_symlink() and retention.classify(
                            path, retention.references(store, path)) == "bulky":
                        entries.append({"path": str(path), "sha256": artifacts.file_hash(path),
                                        "bytes": path.stat().st_size, "class": "bulky"})
            if entries:
                retention._delete(self.store_dir, eid, entries, "Extensa campaign pruning after its comparison")
        self.state["retentions"] = sorted(r.id for r in Store(self.store_dir).of_kind("retention")
                                          if r.data.get("event") == "prune")

    # main ---------------------------------------------------------------------------------------
    def run(self):
        resumed = self._load_state()
        self.folder.mkdir(parents=True, exist_ok=True)
        if resumed:
            if not self.args.resume:
                raise Failure(f"campaign {self.cid} already has state at {self.state_file}; use --resume")
            if resumed.get("stopped"):
                raise Failure(f"campaign {self.cid} already stopped ({resumed['stop_reason']})")
            self.state = resumed
            self.ledger = S.SearchLedger.from_state(self.budget, resumed["ledger"])
            for pause in self.state["pauses"]:
                pause["resumed_at"] = pause.get("resumed_at") or _now()
            # Tickets 56/57 (2026-10-04 ET): a resume after an interrupted process also gets
            # fresh record IDs for the retried iteration.
            if not self.state.pop("clean_exit", False):
                self.state["resumes"] = self.state.get("resumes", 0) + 1
        else:
            self.state = {"campaign": self.cid, "campaign_sha256": self.sha256, "started": _now(),
                          "lane_hours": 0.0, "iterations": [], "bests": {}, "feedback": [], "pauses": [],
                          "baselines": {}, "tested_contracts": {}, "synthesized": {}, "retentions": [],
                          "kept_for_claims": [], "setup_done": False, "pilot": None}
            self.ledger = S.SearchLedger(self.budget)
            if self.query:
                self._check_sites()
        with self._tags():
            try:
                if not self.state["setup_done"]:
                    self._setup()
                self.adapter.protocol_id = self.state["protocol"]["id"]
                self.adapter.restore(self.state)
                if self.adapter.HAS_PILOT and self.state["pilot"] is None:
                    self._pilot()
                elif self.adapter.HAS_PILOT:
                    self._apply_pilot()
                if getattr(self.args, "baselines_only", False) and self.ledger.stop()[0] is None:
                    return self._baselines_only()
                if self.ledger.stop()[0] is None:
                    self._setup_call()
                while self.ledger.may_open_iteration():
                    if (self.folder / "STOP").exists():
                        raise Stop("stopped_by_yanru", (self.folder / "STOP").read_text().strip()[:200])
                    self.adapter.round = len(self.state["pauses"]) + self.state.get("resumes", 0)
                    index = self.ledger.begin_iteration()
                    row = {"index": index, "started": _now(), "ended": None, "regions": [],
                           "provider_calls": [], "candidates": [], "feedback_reasons": [], "improved_classes": []}
                    row["regions"] = self._regions(row)
                    try:
                        outcome = self._iteration(index, row)
                    except Stop:
                        # Ticket 73 (2026-10-05 ET): keep the interrupted iteration's calls (for example
                        # uncounted provider-capacity retries) in the summary; it is not a completed iteration.
                        row["ended"] = _now()
                        for c in row["candidates"]:
                            c.pop("_patch", None)
                        self.state["interrupted_iteration"] = row
                        raise
                    except Paused as pause:
                        self.ledger.record_iteration(S.IterationOutcome.PAUSED)
                        self.state["pauses"].append({"at": _now(), "reason": pause.reason, "resumed_at": None,
                                                     "iteration": index, "provider_calls": row["provider_calls"]})
                        self.adapter.release_lane()
                        self._save()
                        return {"state": "paused", "reason": pause.reason, "campaign": self.cid,
                                "resume": f"swdb campaign {self.file} --resume"}
                    row["ended"] = _now()
                    for c in row["candidates"]:
                        c.pop("_patch", None)
                    self.state["iterations"].append(row)
                    self.ledger.record_iteration(outcome)
                    self._save()
            except Stop as stop:
                self.ledger.terminate(stop.reason)
                self.state["stop_detail"] = stop.detail
            except (Failure, OSError) as exc:      # a real target's command or host failure
                self.ledger.terminate(S.StopReason.INFRASTRUCTURE_FAILURE)
                self.state["stop_detail"] = f"{type(exc).__name__}: {exc}"[:2000]
            except Paused as pause:            # setup call
                self.state["pauses"].append({"at": _now(), "reason": pause.reason, "resumed_at": None,
                                             "iteration": 0})
                self.adapter.release_lane()
                self._save()
                return {"state": "paused", "reason": pause.reason, "campaign": self.cid}
            return self._finish()

    def _baselines_only(self):
        """Run the provider-free setup steps, then pause (2026-10-04 ET, ticket 57).

        On gem5 this evaluates the one baseline per class that serves every candidate, so a
        campaign can do its baseline work while the provider login is in use elsewhere. A
        later `--resume` continues with the setup provider call and iteration 1."""
        if self.adapter.SHARED_BASELINE:
            for cls in self.classes:
                for role in self.roles:
                    key = f"{cls}/{role}"
                    if key in self.state["baselines"]:
                        continue
                    self._step("evaluation", job=True)
                    started = time.monotonic()
                    self.state["baselines"][key] = self.adapter.baseline_evaluation(cls, role)
                    self._spent("evaluation", started)
                    self._save()
        self.state.setdefault("prepared", []).append(_now())
        self.state["clean_exit"] = True
        self.adapter.release_lane()
        self._save()
        return {"state": "prepared", "campaign": self.cid, "baselines": self.state["baselines"],
                "lane_hours": self.state["lane_hours"], "resume": f"swdb campaign {self.file} --resume"}

    def _class_row(self, c):
        """Ticket 64 (2026-10-04 ET): report the registered timed sources and any recorded replacement."""
        row = {"class": c["class"], "workload": c["workload"], "sources": list(self.data["protocol"]["sources"])}
        try:
            from swdb.store import Store
            definition = (Store(self.store_dir).get(c["workload"], "workload") or {}).get("definition", {})
        except Exception:      # a fixture store without the workload keeps the campaign's sources
            definition = {}
        if definition.get("source_policy"):
            row["sources"] = list(definition["sources"])
            row["source_policy"] = definition["source_policy"]
        return row

    def _finish(self):
        from swdb import writer
        self.adapter.release_lane()
        reason = self.ledger.stop()[0] or S.StopReason.MAX_ITERATIONS
        summary = self.summary(reason)
        workflow.persist(self.store_dir, copy.deepcopy(summary), create=True)
        # D6: the summary is the only campaign record always copied to the team store.
        writer.commit(self.team, new=[copy.deepcopy(summary)])
        self.state["stopped"] = True
        self.state["stop_reason"] = reason.value
        self._save()
        return summary

    def summary(self, reason):
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=paths.HOME, capture_output=True, text=True)
        try:
            rel = self.file.resolve().relative_to(paths.HOME).as_posix()
        except ValueError:
            rel = str(self.file.resolve())
        per_class = []
        unstable = (self.state.get("pilot") or {}).get("unstable_classes") or []
        for cls in self.all_classes:
            pool = [c for r in self.state["iterations"] for c in r["candidates"] if c["class"] == cls]
            best, faster, verdict = select(pool)
            if cls in unstable:
                verdict = "baseline_unstable"
            other = None
            if best:
                other = next(({"role": c["baseline_role"], "ratio": c["ratio"], "lower": c["lower"],
                               "verdict": c["verdict"]} for c in best["comparisons"]
                              if c["baseline_role"] != self.data["base_source"]), None)
            per_class.append({"class": cls, "verdict": verdict, "best": best["id"] if best else None,
                              "best_level": best["level"] if best else None,
                              "best_selection_baseline": self.data["base_source"] if best else None,
                              "best_other_baseline": other, "faster_uncertified": faster, "label": LABEL})
        used = {"iterations": self.ledger.iterations_completed, "lane_hours": round(self.state["lane_hours"], 6),
                "provider_calls_counted": self.ledger.counted_calls,
                "provider_calls_uncounted": self.ledger.uncounted_calls,
                "disk_gb_peak": round(max(self.state.get("disk_bytes_peak", 0), _du(self.folder)) / 1e9, 6)}
        artifacts_list = []
        for row in self.state["iterations"]:
            for c in row["candidates"]:
                if c.get("id"):
                    artifacts_list.append({"path": f"records/candidates/{c['id']}.yaml",
                                           "sha256": c.get("artifact_sha256"), "retained": True})
        library_entries = [{"family": f, **v} for f, v in sorted(self.state["synthesized"].items())]
        settings = self.state.get("protocol", {}).get("settings") or protocol_settings(self.data)
        record = workflow.record(
            "campaign_summary", f"{self.cid}.summary",
            campaign_file={"path": rel, "sha256": self.sha256},
            swdb_commit=commit.stdout.strip() or "unknown", extensa_source=dict(EXTENSA_SOURCE),
            target=self.data["target"], evidence_basis=settings["evidence_basis"],
            evidence_kind=self.adapter.evidence_kind,
            protocol=self.state.get("protocol"),
            baselines=[{"role": b["role"], "candidate": b["candidate"],
                        "evaluation_ids_by_class": {k.split("/")[0]: v for k, v in self.state["baselines"].items()
                                                    if k.split("/")[1] == b["role"]}} for b in self.data["baselines"]],
            workload_classes=[self._class_row(c) for c in self.data["workload_classes"]],
            label=LABEL, provider=dict(self.data["provider"]), pilot=self.state.get("pilot"),
            setup={"provider_calls": self.state.get("setup_calls", [])},
            iterations=copy.deepcopy(self.state["iterations"]), per_class=per_class,
            budgets={"limits": self.budget.to_dict(), "used": used},
            pauses=copy.deepcopy(self.state["pauses"]), stop_reason=reason.value,
            stop_detail=self.state.get("stop_detail"), artifacts=artifacts_list,
            retentions=list(self.state["retentions"]), library_entries=library_entries,
            site_finder=self.state.get("site_finder"))
        if self.state.get("interrupted_iteration"):
            record["interrupted_iteration"] = copy.deepcopy(self.state["interrupted_iteration"])
        record["mode"], record["campaign"] = MODE, self.cid
        return record


def _du(folder):
    total = 0
    for path in Path(folder).rglob("*"):
        if path.is_file() and not path.is_symlink():
            total += path.stat().st_size
    return total


def run_cli(args):
    return Campaign(args).run()


def register_cli(commands, paths_module):
    sub = commands.add_parser("campaign", help="run an Extensa campaign on its target (or the contract-fixture adapter)",
                              description="run one Extensa campaign file: budgets, certification-first "
                                          "selection and a campaign_summary record (decisions D2-D10)")
    sub.add_argument("file", type=Path)
    sub.add_argument("--records", type=Path, default=paths_module.RECORDS, help="the team record store")
    sub.add_argument("--library", type=Path, default=None)
    sub.add_argument("--provider-config", type=Path, required=True)
    sub.add_argument("--runs-root", type=Path, default=None,
                     help="override the campaign file's runs_root (tests use a temporary folder)")
    sub.add_argument("--fixture", type=Path, default=None, help="contract-fixture target adapter file")
    sub.add_argument("--resume", action="store_true", help="resume a paused campaign")
    sub.add_argument("--baselines-only", action="store_true",
                     help="run setup and the per-class gem5 baselines (no provider call), then pause")
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(extensa_handler=run_cli)
