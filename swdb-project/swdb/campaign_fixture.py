"""The contract-fixture target adapter of `swdb campaign --fixture` (tickets 52-57).

Created 2026-10-03 ET in `swdb/campaign.py`; moved here 2026-10-05 ET (code review F13) and made a
`TargetAdapter`, so the Extensa campaign loop calls every adapter the same way. Fixture records are
labeled `contract_fixture` and are never performance evidence.
Updated 2026-10-09 ET: record copies go through `swdb.access`.
"""
from __future__ import annotations

import copy
import json
from argparse import Namespace
from pathlib import Path

from swdb import access, artifacts, workflow, yamlio
from swdb.campaign import Stop, _now, apply_speed_rule
from swdb.campaign_targets import ADAPTERS, TargetAdapter
from swdb.cli import Failure, UsageError
from swdb.extensa_boundary import MODE


class FixtureAdapter(TargetAdapter):
    """Contract fixture standing in for a target evaluator (tickets 56/57 add real ones).

    Records are cloned from team-store templates and labeled `contract_fixture`; numbers
    come from the fixture file and are never performance evidence. It answers the per-target
    questions (pilot, shared baseline, evidence basis) as the campaign's real target would."""

    evidence_kind = "contract_fixture"

    def __init__(self, fixture_path, campaign, team_records, store_dir, folder):
        self.fx = yamlio.load(Path(fixture_path))
        if not isinstance(self.fx, dict) or self.fx.get("format") != "swdb.extensa-campaign-fixture.v1":
            raise UsageError("fixture file must have format swdb.extensa-campaign-fixture.v1")
        self.campaign, self.team, self.store_dir, self.folder = campaign, Path(team_records), Path(store_dir), Path(folder)
        self.cid = campaign["id"]
        self.released = 0
        self.round = 0          # retries of an iteration after a pause get fresh record IDs
        self.protocol_id = None
        real = ADAPTERS[campaign["target"]]
        self.HAS_PILOT, self.SHARED_BASELINE = real.HAS_PILOT, real.SHARED_BASELINE
        self.POINT_RATIOS, self.EVIDENCE_BASIS = real.POINT_RATIOS, real.EVIDENCE_BASIS

    def workspace_region_lines(self, regions):
        return regions

    def protected_regions(self):
        return []

    # setup ---------------------------------------------------------------------------
    def prepare(self):
        """Copy the team inputs (untagged) the campaign reads into its own store."""
        from swdb.extensa_boundary import closure
        from swdb.store import Store
        team = Store(self.team)
        roots = [b["candidate"] for b in self.campaign["baselines"]]
        roots += [c["workload"] for c in self.campaign["workload_classes"]]
        roots += [self.campaign["machine"], *self.fx["templates"].values()]
        missing = [rid for rid in roots if rid not in team.by_id]
        if missing:
            raise Failure("team store lacks campaign inputs: " + ", ".join(missing))
        for rid in sorted(closure(team, roots)):
            record = team.by_id[rid]
            target = self.store_dir / record.rel
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                access.copy_record(self.team / record.rel, target)

    def source_files(self):
        return dict(self.fx["source_files"])

    def freeze_protocol(self, settings):
        from swdb import bfs_protocol
        from swdb.store import Store
        template = Store(self.store_dir).get(self.fx["templates"]["protocol"], "protocol")
        frozen = copy.deepcopy(template["settings"])
        frozen["workloads"] = list(settings["workloads"].values())
        if not (self.POINT_RATIOS and frozen.get("mode") == "native"):
            # A native fixture template cannot freeze gem5's single run; the campaign-level
            # settings (one run, source 0) stay in the summary for the fixture case.
            frozen["sampling"]["repetitions"] = settings["repetitions"]
        frozen["threads"] = settings["threads"]
        frozen["roi"] = settings["roi"]
        frozen["region_pairs"] = []
        apply_speed_rule(frozen, settings)
        frozen["differences"]["software"] = list(frozen["differences"]["software"]) + [settings["differences"]]
        request = self.folder / "protocol-request.yaml"
        request.write_text(yamlio.dumps({"message_version": "1.0", "id": f"{self.cid}-protocol", "version": 1,
                                         "settings": frozen}))
        record = bfs_protocol.freeze_protocol(Namespace(file=request, records=self.store_dir, db=None))
        return {"id": record["id"], "identity_sha256": record["identity_sha256"], "settings": settings}

    def _iteration(self, iteration, cls):
        rows = self.fx.get("iterations") or []
        row = rows[min(iteration, len(rows)) - 1] if rows else {}
        return row.get(cls) or {}

    def _estimate_request(self, candidate, cls):
        return {'candidate': candidate, 'workload': {'id': self._workload(cls)},
                'fixture': True, 'backend': 'contract_fixture',
                'roi': self.campaign['protocol']['roi'], 'threads': self.campaign['protocol']['threads']}

    def pilot(self, cls, role):
        self.pairing.freeze([self._estimate_request(b['candidate'], c['class'])
            for b in self.campaign['baselines'] for c in self.campaign['workload_classes']])
        self.pairing.before(f'pilot.{cls}.{role}', [self._estimate_request(self.baseline(role), cls)])
        row = self.fx["pilot"][cls][role]
        if isinstance(row, dict):              # ticket 66: an A/A ratio and CI for the CI-width rule
            return {"spread": float(row.get("spread", 0.0)), "ratio": float(row["ratio"]),
                    "lower": float(row["lower"]), "upper": float(row["upper"])}
        return {"spread": float(row)}

    # artifacts -----------------------------------------------------------------------
    def materialize(self, iteration, cls, patch, knobs, attempt, contracts=()):
        from swdb.store import Store
        template = Store(self.store_dir).get(self.fx["templates"]["candidate"], "candidate")
        data = copy.deepcopy(template)
        rid = f"{self.cid}.{self._iteration_tag(iteration)}.{cls}.a{attempt}"
        data.update(id=rid, kind="candidate", mode=MODE, campaign=self.cid)
        data["artifact"] = {**data["artifact"], "sha256": artifacts.digest({"patch": patch, "knobs": knobs,
                                                                               "class": cls})}
        data.setdefault("notes", []).append(f"Contract fixture candidate artifact for class {cls}; knobs {knobs}.")
        workflow.persist(self.store_dir, _fresh(data), create=True)
        return {"id": rid, "sha256": data["artifact"]["sha256"]}

    def certify(self, candidate, contracts, iteration, cls, attempt, tests=None):
        from swdb.library import Library
        outcomes = self._iteration(iteration, cls).get("certification") or ["certified"]
        outcome = outcomes[min(attempt, len(outcomes) - 1)]
        library = Library()
        contract = contracts[0]
        pin = {"id": contract, "content_sha256": library.content_sha256(contract)}
        passed = outcome == "certified"
        failed_checks = [] if passed else list(self._iteration(iteration, cls).get("failed_checks") or ["verifier"])
        record = workflow.record(
            "certification", f"certification.{self.cid}.{self._iteration_tag(iteration)}.{cls}.a{attempt}", entry=pin,
            dependencies=[], candidate={"id": candidate["id"], "contract": contract,
                                        "contract_sha256": pin["content_sha256"], "tree_sha256": candidate["sha256"]},
            command={"version": "fixture", "contracts": contracts, "test_inputs": len(tests or [])},
            host={"hostname": "contract-fixture"},
            matrix=[{"cell": "fixture", "status": "passed" if passed else "failed",
                     "failed_checks": failed_checks}],
            negative_controls=[{"id": "fixture_control", "status": "rejected"}],
            verdict="certified" if passed else "failed", evidence_basis="simulated",
            evidence_kind="contract_fixture", created_at=_now())
        workflow.persist(self.store_dir, record, create=True)
        return {"record": record["id"], "outcome": "certified" if passed else "failed",
                "failed_checks": failed_checks}

    def _evaluation(self, rid, candidate_id, role):
        from swdb.store import Store
        template = Store(self.store_dir).get(self.fx["templates"]["evaluation"], "evaluation")
        data = copy.deepcopy(template)
        run = self.folder / "runs" / rid
        (run / "cpt.1").mkdir(parents=True, exist_ok=True)
        size = int(self.fx.get("run_bytes", 4096))
        (run / "debug.trace.gz").write_bytes(b"t" * size)
        (run / "cpt.1" / "payload.bin").write_bytes(b"c" * size)
        (run / "correctness.json").write_text(json.dumps({"fixture": True, "role": role}))
        data.update(id=rid, candidate=candidate_id, evidence_kind="contract_fixture", gain_claim=False,
                    raw_artifacts=[{"kind": "dx100_execute", "path": str(run)}], mode=MODE, campaign=self.cid)
        workflow.persist(self.store_dir, _fresh(data), create=True)
        if any(marker in rid for marker in self.fx.get("claim_runs") or []):
            claim = workflow.record("team_claim", f"claim.{rid}", action="claim", records=[rid],
                                    audience=["fixture"], recorded_at=_now())
            workflow.persist(self.store_dir, claim, create=True)
        return rid

    def baseline_evaluation(self, cls, role):
        """gem5: the fork's scalar TDStep is measured once per class."""
        baseline = self.baseline(role)
        self.pairing.freeze([self._estimate_request(b['candidate'], c['class'])
            for b in self.campaign['baselines'] for c in self.campaign['workload_classes']])
        self.pairing.before(f'baseline.{cls}.{role}', [self._estimate_request(baseline, cls)])
        return self._evaluation(f"{self.cid}.baseline.{cls}.{role}", baseline, role)

    def compare(self, candidate, cls, role, iteration, attempt, baseline_evaluation=None):
        """Native: a paired block (its own baseline evaluation); gem5: cite the class baseline."""
        self.pairing.freeze([self._estimate_request(candidate['id'], c['class'])
            for c in self.campaign['workload_classes']])
        self.pairing.before(f'comparison.{iteration}.{cls}.{role}',
            [self._estimate_request(self.baseline(role), cls), self._estimate_request(candidate['id'], cls)])
        numbers = (self._iteration(iteration, cls).get("comparisons") or {}).get(role)
        if numbers is None:
            raise Stop("infrastructure_failure", f"fixture has no comparison for {cls}/{role}")
        tag = f"{self.cid}.{self._iteration_tag(iteration)}.{cls}.a{attempt}.{role}"
        evaluations = [self._evaluation(f"{tag}.candidate-eval", candidate["id"], "candidate")]
        if baseline_evaluation is None:
            baseline = self.baseline(role)
            baseline_evaluation = self._evaluation(f"{tag}.baseline-eval", baseline, role)
            evaluations.append(baseline_evaluation)
        from swdb.store import Store
        template = Store(self.store_dir).get(self.fx["templates"]["comparison"], "comparison_result")
        data = copy.deepcopy(template)
        ratio = float(numbers["ratio"])
        if self.POINT_RATIOS:
            lower = upper = ratio
            spreads = [0.0]
        else:
            lower, upper = float(numbers["lower"]), float(numbers.get("upper", numbers["lower"]))
            spreads = [float(s) for s in (numbers["spreads"] if "spreads" in numbers else [numbers["spread"]])]
        rid = f"{tag}.comparison"
        data.update(id=rid, protocol=self.protocol_id, baseline_evaluation=baseline_evaluation,
                    candidate_evaluation=evaluations[0], evidence_kind="contract_fixture", gain_claim=False,
                    mode=MODE, campaign=self.cid,
                    decision={"state": "fixture_comparison",
                              "reasons": ["Contract fixture numbers are not performance evidence."]},
                    metrics={"fixture_ratio": ratio, "confidence_interval": {"lower": lower, "upper": upper},
                             "relative_spread": {"fixture": {"max": max(spreads)}}})
        data["request"] = {**data.get("request", {}), "id": rid, "protocol": self.protocol_id,
                           "baseline_evaluation": baseline_evaluation, "candidate_evaluation": evaluations[0]}
        data.pop("protocol_sha256", None)
        workflow.persist(self.store_dir, _fresh(data), create=True)
        return {"comparison": rid, "ratio": ratio, "lower": lower, "upper": upper, "spreads": spreads,
                "evaluations": evaluations, "baseline_evaluation": baseline_evaluation}

    # budgets and host ----------------------------------------------------------------------
    def step_hours(self, step):
        return float((self.fx.get("step_hours") or {}).get(step, 0.0))

    def step_budget_hours(self, step):
        return float((self.fx.get("step_budget_hours") or {}).get(step, self.step_hours(step)))

    def planned_bytes(self):
        return 2 * int(self.fx.get("run_bytes", 4096))

    def other_socket_lease(self):
        return self.fx.get("other_socket_lease")

    def preflight(self, planned_bytes, step=None):
        from swdb import dispatch_preflight
        observation = self.fx.get("preflight")
        if observation is None:
            return None
        return dispatch_preflight.check(self.folder, "mbit10-evaluation-node1", storage_bytes=planned_bytes,
                                        memory_bytes=0, observation={**observation, "memory_node": 1})

    def release_lane(self):
        self.released += 1


def _fresh(data):
    """A cloned template is a new record: fresh envelope dates and a fixture provenance."""
    data["created"] = data["updated"] = workflow.writer.today()
    data["status"] = "draft"
    data["provenance"] = [{"id": "campaign-fixture", "kind": "agent_run",
                           "description": "Contract-fixture record written by swdb campaign.", "uri": None}]
    return data
