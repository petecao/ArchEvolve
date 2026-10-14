"""The contract-fixture target adapter of `swdb campaign --fixture` (tickets 52-57).

Created 2026-10-03 ET in `swdb/campaign.py`; moved here 2026-10-05 ET (code review F13) and made a
`TargetAdapter`, so the Extensa campaign loop calls every adapter the same way. Fixture records are
labeled `contract_fixture` and are never performance evidence.
Updated 2026-10-09 ET: record copies go through `swdb.access`.
Updated 2026-10-14 ET (Probata PoC 19): an optional `base_snapshot` in the fixture file names the team-store
source snapshot candidate artifacts are built from. With it, a candidate artifact is a real tree (the start's
tree with the patch applied, refused when the patch does not apply), so a certified enabling rewrite can
become a derived implementation, and an iteration may start from one (`start`). Without it, nothing changes.
Updated 2026-10-14 ET (Probata PoC 14, the bounded gate): with `base_snapshot`, a candidate artifact also
retains its own patch (`diff`), which a counterexample repair shows. The fixture file may hold
`contract_proofs` (contract-fixture contract proofs and minimum bounds, written into the campaign store when
the gate is set up) and `proof` (the proof unit's function); a class row's `proof` scripts the bounded
verdicts per rung and attempt and says whether the code is inside the C++ subset.
Updated 2026-10-14 ET (Probata PoC 16, the WP phase): a class row's `proof.wp` scripts the WP job (`proven_at`,
`unit_postcondition`); `open_timing_step: {seconds}` scripts a timing step still open when the phase starts.
"""
from __future__ import annotations

import copy
import json
import shutil
import time
from argparse import Namespace
from pathlib import Path

from swdb import access, artifacts, derived, paths, workflow, yamlio
from swdb.campaign import Refused, Stop, _now, apply_speed_rule
from swdb.campaign_targets import ADAPTERS, TargetAdapter
from swdb.cli import Failure, UsageError
from swdb.extensa_boundary import MODE


class FixtureAdapter(TargetAdapter):
    """Contract fixture standing in for a target evaluator (tickets 56/57 add real ones).

    Records are cloned from team-store templates and labeled `contract_fixture`; numbers
    come from the fixture file and are never performance evidence. It answers the per-target
    questions (pilot, shared baseline, evidence basis) as the campaign's real target would."""

    evidence_kind = "contract_fixture"

    def __init__(self, fixture_path, campaign, team_records, store_dir, folder, library_root=None):
        self.fx = yamlio.load(Path(fixture_path))
        if not isinstance(self.fx, dict) or self.fx.get("format") != "swdb.extensa-campaign-fixture.v1":
            raise UsageError("fixture file must have format swdb.extensa-campaign-fixture.v1")
        self.campaign, self.team, self.store_dir, self.folder = campaign, Path(team_records), Path(store_dir), Path(folder)
        self.cid = campaign["id"]
        self.library_root = Path(library_root) if library_root else paths.HOME / "library"
        self.base_snapshot = self.fx.get("base_snapshot")
        self.starts = {}        # candidate artifact ID -> the derived implementation it was built on
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
        roots += [self.base_snapshot] if self.base_snapshot else []
        missing = [rid for rid in roots if rid not in team.by_id]
        if missing:
            raise Failure("team store lacks campaign inputs: " + ", ".join(missing))
        # Probata PoC 19: listed derived starts already in the team store come along (with their snapshots,
        # certifications and candidate artifacts); the others are made by this campaign.
        roots += [rid for rid in self.campaign.get("derived_starts") or [] if rid in team.by_id]
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
    def predecessor_snapshot(self, start=None):
        """The source snapshot a candidate artifact is built on: the start's, else the base snapshot."""
        if start:
            from swdb.store import Store
            return derived.snapshot_of(Store(self.store_dir).get(start, "implementation"))
        return self.base_snapshot

    def materialize(self, iteration, cls, patch, knobs, attempt, contracts=(), start=None):
        from swdb.store import Store
        store = Store(self.store_dir)
        template = store.get(self.fx["templates"]["candidate"], "candidate")
        data = copy.deepcopy(template)
        rid = f"{self.cid}.{self._iteration_tag(iteration)}.{cls}.a{attempt}"
        data.update(id=rid, kind="candidate", mode=MODE, campaign=self.cid)
        on = self.predecessor_snapshot(start)
        if start and not on:
            raise Refused("provider_output_invalid", f"The start {start} has no source snapshot.")
        if on:
            # Probata PoC 19: a real tree, the start's tree with the patch applied (knobs are not compiled in).
            snapshot = store.get(on, "source_snapshot")
            tree = self.folder / "sources" / rid / "source"
            if tree.parent.exists():
                shutil.rmtree(tree.parent)
            tree.parent.mkdir(parents=True)
            try:
                artifact = workflow.apply_patch(artifacts.verify(snapshot["artifact"]), tree, patch, ["*"],
                                                snapshot["protections"])
            except Failure as exc:
                raise Refused("build_failed", f"The patch does not apply to the start's source ({on}): "
                                              f"{str(exc)[:300]}") from None
            data.update(artifact=artifact, source_snapshot=on, implementation=snapshot["implementation"],
                        protections=copy.deepcopy(snapshot["protections"]), context=copy.deepcopy(snapshot["context"]))
            diff = tree.parent / "candidate.diff"            # Probata PoC 14: the candidate's own patch
            diff.write_text(patch if patch.endswith("\n") else patch + "\n")
            data.update(diff=str(diff), diff_sha256=artifacts.file_hash(diff))
        else:
            data["artifact"] = {**data["artifact"], "sha256": artifacts.digest({"patch": patch, "knobs": knobs,
                                                                                   "class": cls})}
        if start:
            self.starts[rid] = start
            data["predecessor"] = {"implementation": start,
                                   "snapshot": {"id": on, "sha256": snapshot["artifact"]["sha256"]}}
        data.setdefault("notes", []).append(f"Contract fixture candidate artifact for class {cls}; knobs {knobs}.")
        workflow.persist(self.store_dir, _fresh(data), create=True)
        return {"id": rid, "sha256": data["artifact"]["sha256"]}

    def certify(self, candidate, contracts, iteration, cls, attempt, tests=None):
        from swdb.library import Library
        outcomes = self._iteration(iteration, cls).get("certification") or ["certified"]
        outcome = outcomes[min(attempt, len(outcomes) - 1)]
        library = Library(self.library_root)
        passed = outcome == "certified"
        failed_checks = [] if passed else list(self._iteration(iteration, cls).get("failed_checks") or ["verifier"])
        # Probata PoC ticket 02 (2026-10-14 ET): one fixture certification per contract, in contract order, as
        # the real adapters write. A single contract keeps the record ID it had before; with several, each ID
        # ends in the contract's name. The fixture outcome of the attempt applies to every contract.
        base = f"certification.{self.cid}.{self._iteration_tag(iteration)}.{cls}.a{attempt}"
        links = []
        start = self.starts.get(candidate["id"])
        root_cells = []
        if start:
            # Probata PoC 19 (decision 17 item 7): a candidate artifact built on a derived implementation is
            # certified against that implementation's snapshot, and also runs the kernel's correctness check
            # against the root baseline implementation (a fixture cell with the attempt's outcome).
            from swdb.store import Store
            root = Store(self.store_dir).get(start, "implementation")["source_baseline"]
            root_cells = [{"cell": "root_baseline_correctness", "status": "passed" if passed else "failed",
                           "baseline": root, "check": "kernel correctness check",
                           **({} if passed else {"failed_checks": failed_checks})}]
        for contract in contracts:
            pin = {"id": contract, "content_sha256": library.content_sha256(contract)}
            rid = base if len(contracts) == 1 else f"{base}.{contract.removeprefix('contract.')}"
            record = workflow.record(
                "certification", rid, entry=pin,
                dependencies=[], candidate={"id": candidate["id"], "contract": contract,
                                            "contract_sha256": pin["content_sha256"], "tree_sha256": candidate["sha256"]},
                command={"version": "fixture", "contracts": [contract], "test_inputs": len(tests or []),
                         **({"start": start} if start else {})},
                host={"hostname": "contract-fixture"},
                matrix=[{"cell": "fixture", "status": "passed" if passed else "failed",
                         "failed_checks": failed_checks}, *root_cells],
                negative_controls=[{"id": "fixture_control", "status": "rejected"}],
                verdict="certified" if passed else "failed", evidence_basis="simulated",
                evidence_kind="contract_fixture", created_at=_now())
            workflow.persist(self.store_dir, record, create=True)
            links.append({"contract": contract, "record": rid})
        return {"record": links[0]["record"], "records": links, "outcome": "certified" if passed else "failed",
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

    # the bounded gate (Probata PoC 14) --------------------------------------------------------
    def proof_function(self, contract):
        return (self.fx.get("proof") or {}).get("function") or self.PROOF_FUNCTION

    def prepare_proofs(self, store_dir):
        """Write the fixture file's contract-fixture contract proofs into the campaign store, once.

        `contract_proofs: {contract: {parts: [part names] (default [unit_postcondition]), minimum_bounds:
        {threads_1: bounds, threads_k: bounds}}}`: each part is a proven record over unbounded data and threads;
        each minimum is a minimum-bounds derivation record whose bounds are the rung's minimum bounds."""
        from swdb import method_version, proof
        from swdb.library import Library, default_root
        from swdb.store import Store
        store = Store(store_dir)
        library = Library(default_root(store_dir))
        method = method_version.pin(method_version.current(default_root(store_dir)))
        for contract, spec in sorted((self.fx.get("contract_proofs") or {}).items()):
            if library.get(contract) is None:
                raise UsageError(f"fixture contract_proofs names {contract}, which the campaign's library does not hold")
            pin = {"id": contract, "sha256": library.content_sha256(contract)}
            rows = [(part, {"threads": "unbounded", "vertices": "unbounded", "edges": "unbounded"})
                    for part in (spec.get("parts") or ["unit_postcondition"])]
            rows += [("minimum_bounds_derivation", dict(bounds)) for _rung, bounds in
                     sorted((spec.get("minimum_bounds") or {}).items())]
            for position, (part, bounds) in enumerate(rows, start=1):
                tag = f"threads-{bounds['threads']}" if part == "minimum_bounds_derivation" else part
                rid = f"proof.{self.cid}.contract-fixture.{contract.removeprefix('contract.')}.{tag}"
                if store.get(rid) is not None:
                    continue
                log = self.folder / "contract-proofs" / f"{rid}.log"
                log.parent.mkdir(parents=True, exist_ok=True)
                log.write_text(f"contract-fixture contract proof {contract} {part}: proven at {bounds}\n")
                record = {"kind": "proof", "schema_version": "0.4", "id": rid, "status": "draft",
                          "created": workflow.writer.today(), "updated": workflow.writer.today(),
                          "provenance": [{"id": "campaign-fixture", "kind": "agent_run", "uri": None,
                                          "description": "Contract-fixture contract proof written by swdb campaign."}],
                          "subject": {"kind": "contract_proof_part", "id": contract, "part": part},
                          "verdict": "proven", "bounds": bounds, "assumptions": [dict(FIXTURE_ASSUMPTION)],
                          "pins": {"code": dict(pin), "contract": dict(pin),
                                   "baseline_function": {"not_applicable": NOT_APPLICABLE},
                                   "reference_semantics": {"not_applicable": NOT_APPLICABLE},
                                   "proof_semantics": {"not_applicable": NOT_APPLICABLE},
                                   "method_version": method, "summaries": [],
                                   "minimum_bounds": {"not_applicable": NOT_APPLICABLE},
                                   "predecessor_snapshot": {"not_applicable": NOT_APPLICABLE}, "build_constants": []},
                          "job": proof._job("scripted", 0.0, 0.0, {"start": 0.0, "end": 0.0}, 0,
                                            {"batch": f"batch.{self.cid}.contract-fixture", "position": position}),
                          "evidence": {"adapter_log": {"path": str(log), "sha256": artifacts.file_hash(log)}},
                          "evidence_kind": "contract_fixture"}
                proof._write(store_dir, record)

    def _proof_spec(self, iteration, cls, contract=None):
        spec = dict(self._iteration(iteration, cls).get("proof") or {})
        return {**spec, **((spec.get("contracts") or {}).get(contract) or {})} if contract else spec

    def outside_cpp_subset(self, candidate_id, iteration, cls, attempt):
        return self._proof_spec(iteration, cls).get("cpp_subset", True) is False

    def bounded_job(self, candidate_id, contract, rung, bounds, iteration, cls, attempt):
        """The scripted adapter's job: the class row's verdict for this rung and attempt (the last repeats).

        A verdict is `proven`, `refuted`, `timeout`, `spurious`, or a mapping with `verdict` set to one of
        them plus scripted-adapter keys; `{candidate}`, `{contract}`, `{rung}` and `{store}` in a `run`
        command are filled in."""
        verdicts = self._proof_spec(iteration, cls, contract).get(rung) or ["proven"]
        spec = verdicts[min(attempt, len(verdicts) - 1)]
        spec = dict(spec) if isinstance(spec, dict) else {"verdict": spec}
        script = dict(SCRIPTED[spec.pop("verdict")])
        values = {"candidate": candidate_id, "contract": contract, "rung": rung, "store": str(self.store_dir)}
        if "run" in spec:
            spec["run"] = [str(part).format(**values) for part in spec["run"]]
        script.update(spec)
        path = self.folder / "proof-scripts" / f"{candidate_id}.{contract}.{rung}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yamlio.dumps(script))
        return {"adapter": "scripted", "script": path}

    # the WP phase (Probata PoC 16) ----------------------------------------------------------------
    def wp_plan(self, candidate_id, contract, iteration, cls):
        """The class row's `proof.wp`: `proven_at` (`wp`, `seeds`, a hint round, or absent: never) and
        `unit_postcondition` (default true)."""
        spec = self._proof_spec(iteration, cls, contract).get("wp")
        if spec is None:
            raise Failure(f"the fixture scripts no WP job (proof.wp) for class {cls} in iteration {iteration}")
        return {"proven_at": spec.get("proven_at"), "unit_postcondition": spec.get("unit_postcondition", True)}

    def wp_job(self, candidate_id, contract, proven, iteration, cls):
        script = dict(SCRIPTED["unbounded" if proven else "hint_budget_spent"])
        path = self.folder / "proof-scripts" / f"{candidate_id}.{contract}.wp.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yamlio.dumps(script))
        return {"adapter": "scripted", "script": path}

    def open_timing_steps(self):
        """`open_timing_step: {seconds: S}` scripts a timing step that is open when the WP phase first asks and
        closes S seconds later."""
        spec = self.fx.get("open_timing_step")
        if not spec:
            return []
        if getattr(self, "_timing_open", None) is None:
            self._timing_open = (time.monotonic(), _now())
        if time.monotonic() - self._timing_open[0] >= float(spec["seconds"]):
            return []
        return [{"what": "scripted timing step", "kind": "timing_step", "started": self._timing_open[1]}]

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


NOT_APPLICABLE = "A contract-fixture contract proof pins no such version."
FIXTURE_ASSUMPTION = {"kind": "trusted_tool", "reference": {"id": "scripted-verifier", "sha256": "0" * 64},
                      "sentence": "The scripted verifier adapter stands in for the bounded verifiers (contract fixture)."}
FIXTURE_COUNTEREXAMPLE = {"source": 0, "graph": "3 vertices, 2 edges", "differs_at": "parent[2]"}
#: The scripted-adapter scripts behind the fixture's verdict words (contract fixture, never evidence).
SCRIPTED = {
    "proven": {"verdict": "proven", "assumptions": [FIXTURE_ASSUMPTION]},
    "refuted": {"verdict": "refuted", "counterexample": FIXTURE_COUNTEREXAMPLE, "assumptions": [FIXTURE_ASSUMPTION]},
    "timeout": {"verdict": "not_proven", "failure_class": "timeout", "assumptions": [FIXTURE_ASSUMPTION]},
    "spurious": {"verdict": "not_proven", "failure_class": "spurious_counterexample",
                 "unreplayed_counterexample": FIXTURE_COUNTEREXAMPLE, "assumptions": [FIXTURE_ASSUMPTION]},
    # Probata PoC 16: the WP job (route 1, WP on the C lowering per thread for symbolic N).
    "unbounded": {"verdict": "proven", "assumptions": [FIXTURE_ASSUMPTION],
                  "bounds": {"threads": "unbounded", "vertices": "unbounded", "edges": "unbounded"}},
    "hint_budget_spent": {"verdict": "not_proven", "failure_class": "hint_budget_spent", "assumptions": [FIXTURE_ASSUMPTION],
                          "bounds": {"threads": "unbounded", "vertices": "unbounded", "edges": "unbounded"}},
}


def _fresh(data):
    """A cloned template is a new record: fresh envelope dates and a fixture provenance."""
    data["created"] = data["updated"] = workflow.writer.today()
    data["status"] = "draft"
    data["provenance"] = [{"id": "campaign-fixture", "kind": "agent_run",
                           "description": "Contract-fixture record written by swdb campaign.", "uri": None}]
    return data
