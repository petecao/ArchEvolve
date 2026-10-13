"""Bounded offline search and reflector trials using explicitly supplied adapters.

No network client, shell execution, dynamic code loading, or catalog mutation.
Adapters are trusted Python code; generated content is always treated as data.
"""

from copy import deepcopy

from .evolution_policy import EDITABLE_SECTIONS, exclusion_reasons, finite_number, validate_cohort, validate_prompt_revision
from .evolution_store import digest

REFLECTOR_FIELDS = {"evidence_selection", "diagnosis", "generalization", "revision_method"}
MUTATIONS = {"placement", "composition", "scheduling", "organization", "admitted_parameter", "simplification"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_reflector(content):
    require(isinstance(content, dict) and set(content) == REFLECTOR_FIELDS,
            "Only reflector evidence selection, diagnosis, generalization and revision method are editable.")
    require(all(text(v) for v in content.values()), "Reflector sections must be nonempty text.")


def validate_strategy(content):
    require(isinstance(content, dict) and set(content) == EDITABLE_SECTIONS, "Unknown strategy section.")
    require(text(content["search_focus"]), "Search focus required.")
    for key in EDITABLE_SECTIONS - {"search_focus"}:
        require(isinstance(content[key], list) and all(text(x) for x in content[key]), "Strategy lists require text.")


class OfflineEvolution:
    """One coordinator per database. Methods persist attempts before invoking adapters.

    proposer(request) returns {content, tokens}; evaluator(request) returns a record
    accepted by evolution_policy. Token counts are adapter-reported; no live API
    enforcement is provided. Incomplete calls reserve their full token allowance.
    """

    def __init__(self, store, proposer, evaluator):
        self.store, self.proposer, self.evaluator = store, proposer, evaluator
        campaigns = store.events("campaign")
        require(len(campaigns) == 1, "Initialize exactly one campaign per store.")
        self.campaign_ref = campaigns[0]["ref"]
        self.campaign = campaigns[0]["record"]
        self.policy = self.campaign["policy"]

    @staticmethod
    def initialize(store, *, catalog, core, policy, strategy, reflector):
        require(not store.events(), "Store already initialized.")
        expected = {"mode", "max_calls", "max_tokens", "max_evaluations", "tokens_per_call",
                    "proposals_per_task", "area_limit_mm2", "min_relative_gain", "tasks"}
        require(set(policy) == expected, "Unexpected frozen policy fields.")
        require(policy["mode"] in {"synthetic_demo", "offline_evidence"}, "Offline modes only.")
        for key in ("max_calls", "max_tokens", "max_evaluations", "tokens_per_call", "proposals_per_task"):
            require(type(policy[key]) is int and policy[key] > 0, "Budgets must be positive integers.")
        require(finite_number(policy["area_limit_mm2"], positive=True), "Positive area limit required.")
        require(finite_number(policy["min_relative_gain"]) and policy["min_relative_gain"] < 1, "Invalid gain threshold.")
        require(text(core) and isinstance(catalog, dict), "Snapshot the core and catalog.")
        require(isinstance(policy["tasks"], list) and policy["tasks"], "Tasks required.")
        ids, splits = set(), set()
        for task in policy["tasks"]:
            require(set(task) == {"id", "split", "input", "cohort", "baseline_latency_ms"}, "Unexpected task fields.")
            require(text(task["id"]) and task["id"] not in ids, "Unique task IDs required.")
            ids.add(task["id"])
            require(task["split"] in {"development", "validation", "holdout"}, "Unknown task split.")
            splits.add(task["split"])
            validate_cohort(task["cohort"])
            require(task["cohort"]["catalog_sha256"] == digest(catalog), "Task must bind this catalog snapshot.")
            require(finite_number(task["baseline_latency_ms"], positive=True), "Baseline latency required.")
        require({"development", "validation"} <= splits, "Separate development and validation tasks required.")
        validate_strategy(strategy)
        validate_reflector(reflector)
        campaign = {"catalog_ref": store.put(catalog), "core_ref": store.put(core), "policy": policy}
        campaign_ref = store.append("campaign", campaign)
        pins = {"campaign_ref": campaign_ref, "core_sha256": digest(core), "policy_sha256": digest(policy)}
        for kind, content in (("strategy", strategy), ("reflector", reflector)):
            ref = store.put({"kind": kind, "pins": pins, "parent_ref": None, "content": content,
                             "feedback_refs": [], "author_reflector": None})
            store.append("activation", {"kind": kind, "version_ref": ref, "previous_ref": None,
                                        "reason": "seed", "review": None})
        return campaign_ref

    @property
    def pins(self):
        return {"campaign_ref": self.campaign_ref, "core_sha256": self.campaign["core_ref"],
                "policy_sha256": digest(self.policy)}

    def version(self, ref, kind):
        value = self.store.get(ref)
        require(value.get("kind") == kind and value.get("pins") == self.pins, "Wrong version kind or campaign pins.")
        (validate_strategy if kind == "strategy" else validate_reflector)(value["content"])
        return value

    def active(self, kind):
        versions = [x["record"]["version_ref"] for x in self.store.events("activation") if x["record"]["kind"] == kind]
        require(bool(versions), "No active version.")
        self.version(versions[-1], kind)
        return versions[-1]

    def history(self):
        # Final holdouts and trial-validation observations never enter reflection context.
        return [e["ref"] for e in self.store.events("observation") if e["record"]["split"] == "development"]

    def rules(self):
        return [e["record"]["rule_ref"] for e in self.store.events("rule_admission")]

    def usage(self):
        starts = self.store.events("call_start")
        ends = {e["record"]["call_id"]: e["record"] for e in self.store.events("call_end")}
        return {"calls": len(starts), "tokens": sum(ends.get(e["ref"], {}).get("tokens", self.policy["tokens_per_call"])
                for e in starts), "evaluations": len(self.store.events("evaluation_start"))}

    def _call(self, operation, context):
        u = self.usage()
        require(u["calls"] < self.policy["max_calls"] and
                u["tokens"] + self.policy["tokens_per_call"] <= self.policy["max_tokens"], "Generation budget exhausted.")
        # Include a sequence to retain repeated/failed identical requests distinctly.
        request = {"operation": operation, "context": context, "max_tokens": self.policy["tokens_per_call"],
                   "sequence": u["calls"], "mode": self.policy["mode"]}
        call_id = self.store.append("call_start", request)
        try:
            response = self.proposer(deepcopy(request))
            require(isinstance(response, dict) and set(response) == {"content", "tokens"}, "Bad adapter response.")
            require(type(response["tokens"]) is int and 0 <= response["tokens"] <= request["max_tokens"], "Invalid token receipt.")
            self.store.append("call_end", {"call_id": call_id, **response})
            return response["content"], call_id
        except Exception as exc:
            self.store.append("call_failure", {"call_id": call_id, "error": str(exc)})
            raise

    def _context(self, reflector_ref, strategy_ref, history=None, rules=None):
        history = self.history() if history is None else history
        require(set(history) <= set(self.history()), "Reflection may only read development observations.")
        rules = self.rules() if rules is None else rules
        require(set(rules) <= set(self.rules()), "Only reviewed learned rules may enter context.")
        observations = []
        decisions = {}
        for ref in history:
            observation = self.store.get(ref)
            strategy = self.version(observation["strategy_ref"], "strategy")
            decisions[observation["strategy_ref"]] = strategy
            observations.append({**observation, "candidate": self.store.get(observation["candidate_ref"]),
                "evaluation": self.store.get(observation["evaluation_ref"]) if observation["evaluation_ref"] else None})
        return {"reflector_ref": reflector_ref, "reflector": self.version(reflector_ref, "reflector")["content"],
                "strategy_ref": strategy_ref, "strategy": self.version(strategy_ref, "strategy")["content"],
                "history_refs": history, "history": observations, "strategy_decisions": decisions,
                "rule_refs": rules, "rules": [self.store.get(r) for r in rules],
                "core": self.store.get(self.campaign["core_ref"]), "catalog": self.store.get(self.campaign["catalog_ref"])}

    def _revision(self, kind, parent_ref, author_reflector, content, feedback_refs, call_id):
        parent = self.version(parent_ref, kind)
        require(content != parent["content"], "No-op revision.")
        require(feedback_refs, "Revision requires development evidence.")
        (validate_strategy if kind == "strategy" else validate_reflector)(content)
        if kind == "strategy":
            def envelope(body, sid, pid, refs):
                return {"strategy_id": sid, "parent_strategy_id": pid, "core_sha256": self.pins["core_sha256"],
                        "task_sha256": self.campaign_ref, "policy_sha256": self.pins["policy_sha256"],
                        "editable": body, "feedback_refs": refs}
            validate_prompt_revision(envelope(parent["content"], parent_ref, None, []),
                                     envelope(content, digest(content), parent_ref, feedback_refs))
        value = {"kind": kind, "pins": self.pins, "parent_ref": parent_ref, "content": content,
                 "feedback_refs": feedback_refs, "author_reflector": author_reflector, "call_id": call_id}
        return self.store.append("revision", value)

    def revise(self, kind):
        require(kind in {"strategy", "reflector"}, "Unknown revision kind.")
        r, s = self.active("reflector"), self.active("strategy")
        context = self._context(r, s)
        require(context["history_refs"], "Collect development observations first.")
        content, call = self._call("revise_" + kind, context)
        try:
            return self._revision(kind, s if kind == "strategy" else r, r, content, context["history_refs"], call)
        except Exception as exc:
            self.store.append("revision_rejection", {"call_id": call, "kind": kind, "error": str(exc)})
            raise

    def _search(self, strategy_ref, reflector_ref, tasks, history, rules, arm, trial_id):
        context = self._context(reflector_ref, strategy_ref, history, rules)
        # Candidate generation is conditioned on the strategy, not the reflector instructions.
        context.pop("reflector")
        observations = []
        for task in tasks:
            parent = {"baseline_task": task["id"], "input": task["input"]}
            parent_latency = task["baseline_latency_ms"]
            require(task["split"] != "holdout", "Holdout execution is outside adaptive runtime.")
            for slot in range(self.policy["proposals_per_task"]):
                parent_ref = self.store.put(parent)
                content, call = self._call("propose", {**context, "task": task, "slot": slot,
                                                      "parent_ref": parent_ref, "parent": parent})
                candidate_ref = self.store.put(content)
                record = {"task_id": task["id"], "split": task["split"], "candidate_ref": candidate_ref,
                          "strategy_ref": strategy_ref, "reflector_ref": reflector_ref, "call_id": call, "parent_ref": parent_ref,
                          "trial_id": trial_id, "arm": arm, "eligible": False, "reasons": [], "evaluation_ref": None}
                try:
                    require(isinstance(content, dict) and set(content) == {"parent_ref", "mutation", "design", "rationale", "obligations"}, "Bad candidate envelope.")
                    require(content["parent_ref"] == parent_ref, "Candidate parent mismatch.")
                    require(content["mutation"] in MUTATIONS and isinstance(content["design"], dict), "Unsupported mutation/design.")
                    require(text(content["rationale"]) and isinstance(content["obligations"], list) and
                            all(text(v) for v in content["obligations"]), "Candidate rationale/obligations required.")
                    require(self.usage()["evaluations"] < self.policy["max_evaluations"], "Evaluation budget exhausted.")
                    request = {"candidate": content, "candidate_ref": candidate_ref, "task": task, "mode": self.policy["mode"]}
                    attempt = self.store.append("evaluation_start", {**request, "call_id": call})
                    evaluation = self.evaluator(deepcopy(request))
                    evaluation_ref = self.store.put(evaluation)
                    self.store.append("evaluation_end", {"attempt_ref": attempt, "evaluation_ref": evaluation_ref})
                    record["evaluation_ref"] = evaluation_ref
                    require(isinstance(evaluation, dict), "Bad evaluation record.")
                    require(evaluation.get("candidate_sha256") == candidate_ref, "Evaluation candidate mismatch.")
                    require(evaluation.get("synthetic") is (self.policy["mode"] == "synthetic_demo"), "Evidence mode mismatch.")
                    record["reasons"] = exclusion_reasons(evaluation, task["cohort"])
                    if not record["reasons"]:
                        for ref in evaluation["evidence_refs"]:
                            self.store.get(ref)  # Evidence payloads must be preserved, not dangling paths.
                    if not record["reasons"] and evaluation["area_mm2"] > self.policy["area_limit_mm2"]:
                        record["reasons"].append("area_budget_exceeded")
                    record["eligible"] = not record["reasons"]
                    if record["eligible"] and evaluation["latency_ms"] < parent_latency:
                        parent, parent_latency = content, evaluation["latency_ms"]
                except Exception as exc:
                    record["reasons"] = [str(exc)]
                observations.append(self.store.append("observation", record))
        return observations

    def run_epoch(self):
        r, s = self.active("reflector"), self.active("strategy")
        return self._search(s, r, [t for t in self.policy["tasks"] if t["split"] == "development"],
                            self.history(), self.rules(), "development", None)

    def _score(self, refs, tasks):
        observations = [self.store.get(r) for r in refs]
        scores = {}
        for task in tasks:
            valid = [self.store.get(o["evaluation_ref"])["latency_ms"] for o in observations
                     if o["task_id"] == task["id"] and o["eligible"]]
            # Baseline is an explicit fixed fallback; unknown/refuted candidates cannot improve it.
            scores[task["id"]] = min([task["baseline_latency_ms"], *valid])
        return scores, sum(o["eligible"] for o in observations)

    def trial(self, revision_ref):
        revision = self.store.get(revision_ref)
        kind = revision.get("kind")
        require(kind in {"strategy", "reflector"}, "Not a revision.")
        self.version(revision_ref, kind)
        parent = self.active(kind)
        require(revision["parent_ref"] == parent, "Revision parent is no longer active.")
        history, rules = self.history(), self.rules()
        tasks = [t for t in self.policy["tasks"] if t["split"] == "validation"]
        count = len(tasks) * self.policy["proposals_per_task"]
        per_arm_calls = count + (kind == "reflector")
        u = self.usage()
        require(u["calls"] + 2 * per_arm_calls <= self.policy["max_calls"] and
                u["tokens"] + 2 * per_arm_calls * self.policy["tokens_per_call"] <= self.policy["max_tokens"] and
                u["evaluations"] + 2 * count <= self.policy["max_evaluations"], "Insufficient budget for both trial arms.")
        plan = {"attempt_index": len(self.store.events("trial_start")), "revision_ref": revision_ref, "parent_ref": parent, "kind": kind, "history_refs": history,
                "rule_refs": rules, "strategy_ref": self.active("strategy"), "reflector_ref": self.active("reflector"),
                "calls_per_arm": per_arm_calls, "token_allowance_per_arm": per_arm_calls * self.policy["tokens_per_call"],
                "evaluations_per_arm": count, "campaign_ref": self.campaign_ref}
        trial_id = self.store.append("trial_start", plan)
        results = {}
        try:
            for arm, version_ref in (("parent", parent), ("child", revision_ref)):
                before = self.usage()
                r = version_ref if kind == "reflector" else plan["reflector_ref"]
                s = version_ref if kind == "strategy" else plan["strategy_ref"]
                if kind == "reflector":
                    context = self._context(r, s, history, rules)
                    content, call = self._call("revise_strategy", context)
                    # A reflector may reasonably choose to retain the existing strategy.
                    if content != context["strategy"]:
                        s = self._revision("strategy", s, r, content, history, call)
                refs = self._search(s, r, tasks, history, rules, arm, trial_id)
                scores, valid = self._score(refs, tasks)
                after = self.usage()
                results[arm] = {"observations": refs, "scores": scores, "valid_count": valid,
                                "usage": {k: after[k] - before[k] for k in after}, "strategy_ref": s}
            a, b = results["parent"], results["child"]
            gains = [1 - b["scores"][t["id"]] / a["scores"][t["id"]] for t in tasks]
            eligible = (b["valid_count"] == count and b["valid_count"] >= a["valid_count"] and
                        all(g >= 0 for g in gains) and sum(gains) / len(gains) > self.policy["min_relative_gain"])
            result = {**plan, "trial_id": trial_id, "status": "completed", "results": results,
                      "mean_relative_gain": sum(gains) / len(gains), "eligible_for_review": eligible,
                      "synthetic": self.policy["mode"] == "synthetic_demo"}
            return self.store.append("trial_end", result)
        except Exception as exc:
            self.store.append("trial_incomplete", {"trial_id": trial_id, "partial_results": results, "error": str(exc)})
            raise

    def promote(self, trial_ref, review):
        result = self.store.get(trial_ref)
        require(trial_ref in {e["ref"] for e in self.store.events("trial_end")}, "Completed trial required.")
        require(result["eligible_for_review"], "Trial does not qualify for promotion.")
        self._review(review)
        require(result["rule_refs"] == self.rules(), "Learned-rule context changed since trial.")
        require(result["parent_ref"] == self.active(result["kind"]), "Stale trial parent.")
        require(result["strategy_ref"] == self.active("strategy") and result["reflector_ref"] == self.active("reflector"),
                "Active search context changed since trial.")
        return self.store.append("activation", {"kind": result["kind"], "version_ref": result["revision_ref"],
                    "previous_ref": result["parent_ref"], "reason": "reviewed_trial", "trial_ref": trial_ref, "review": review})

    def _review(self, review):
        require(isinstance(review, dict) and set(review) == {"reviewer", "rationale", "semantic_review_passed", "synthetic"}, "Explicit review required.")
        require(text(review["reviewer"]) and text(review["rationale"]) and review["semantic_review_passed"] is True,
                "Semantic review must pass.")
        require(review["synthetic"] is (self.policy["mode"] == "synthetic_demo"), "Review mode mismatch.")

    def rollback(self, kind, review):
        self._review(review)
        current = self.active(kind)
        last = [e["record"] for e in self.store.events("activation") if e["record"]["kind"] == kind][-1]
        require(last["previous_ref"] is not None, "No previous activation to restore.")
        self.version(last["previous_ref"], kind)
        return self.store.append("activation", {"kind": kind, "version_ref": last["previous_ref"],
                    "previous_ref": current, "reason": "rollback", "review": review})

    def propose_rule(self):
        context = self._context(self.active("reflector"), self.active("strategy"))
        require(context["history_refs"], "Rule needs observed evidence.")
        content, call = self._call("learn_rule", context)
        require(isinstance(content, dict) and set(content) == {"name", "transformation", "applicability",
                "obligations", "support_refs", "counterexample_refs", "limitations"}, "Bad learned-rule fields.")
        require(all(text(content[k]) for k in ("name", "transformation", "applicability", "limitations")), "Rule text required.")
        require(isinstance(content["obligations"], list) and content["obligations"] and all(text(x) for x in content["obligations"]), "Rule obligations required.")
        for key in ("support_refs", "counterexample_refs"):
            require(isinstance(content[key], list) and all(text(x) for x in content[key]) and
                    set(content[key]) <= set(context["history_refs"]), "Rules must cite development observations.")
        require(content["support_refs"] and not set(content["support_refs"]) & set(content["counterexample_refs"]), "Rule support is empty or contradictory.")
        baselines = {t["id"]: t["baseline_latency_ms"] for t in self.policy["tasks"]}
        for ref in content["support_refs"]:
            observation = self.store.get(ref)
            require(observation["eligible"], "Ineligible observations cannot support a successful rule.")
            evaluation = self.store.get(observation["evaluation_ref"])
            require(evaluation["latency_ms"] < baselines[observation["task_id"]],
                    "Support must improve the frozen baseline within the area limit.")
        return self.store.append("rule_proposal", {"content": content, "catalog_ref": self.campaign["catalog_ref"],
                "author_reflector": self.active("reflector"), "call_id": call, "status": "hypothesis_pending_review",
                "synthetic": self.policy["mode"] == "synthetic_demo"})

    def admit_rule(self, rule_ref, review):
        self._review(review)
        require(rule_ref in {e["ref"] for e in self.store.events("rule_proposal")}, "Unknown rule proposal.")
        require(rule_ref not in self.rules(), "Rule already admitted.")
        return self.store.append("rule_admission", {"rule_ref": rule_ref, "review": review,
            "status": "reviewed_for_search_context_only", "catalog_claim_admitted": False})
