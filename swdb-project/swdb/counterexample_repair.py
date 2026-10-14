"""Counterexample-guided repair: a refutation becomes a new candidate artifact, never a dead end.

Created: 2026-10-14 ET (Probata proof of concept ticket 13). Design: formal-verification map spec
("Refutation, repair and bugs"; "Proof-hint loop", the three loops kept apart); map decisions 13 items
6 and 10, 15 items 10 and 11, 22 items 5 and 6, 23 items 3 and 4, 25 items 2, 3 and 5; O1, O5.
Format: docs/reference/format-v0.4-repair.md.

This module is the one owner, in every mode, of the round cap (`budgets.counterexample_repair_rounds`
of the pinned method version) and of the reverted-repair flag (`contract_match`). Campaigns (14) and
ArchEvolve mode (18) call `loop`; `swdb repair <proof record>` runs one round.

- **Only a refutation starts a repair.** `repairable` is the explicit filter: a `not_proven` record,
  a spurious counterexample above all (failure class `spurious_counterexample`, a tool or encoding
  failure, Yan-Ru 2026-10-14 02:25 ET), never reaches the rewriting role.
- **One round = one rewriting-role repair call.** The provider workspace is the rewriting workspace
  over the refuted candidate artifact's tree; it holds the refuted patch and the counterexample, both
  hashed in its manifest (`repair_inputs`). The call is recorded as a rewriting-role repair call
  (`attempts[].call: counterexample_repair`), never as a proof-hint call.
- **A repaired candidate artifact is new:** its own proposal (with `repair_lineage` and
  `provider_pin`) and candidate record. Nothing about the refuted candidate artifact changes.
- **Settings:** `archevolve` (`swdb repair`), `campaign` (14), `evaluation` (`swdb repair
  --evaluation-run`). Only an evaluation repair run marks its workspace (`evaluation_repair`), which
  lets the guard show a guarded authors' function that is the refuted candidate artifact under repair
  (O5), and only it admits a refuted candidate artifact that failed certification (O1).
"""

import copy
import fcntl
import hashlib
import json
import re
import subprocess
from pathlib import Path

from swdb import artifacts
from swdb.cli import Failure

SETTINGS = ("archevolve", "campaign", "evaluation")
#: How every call this loop makes is recorded: a rewriting-role repair call (never a proof-hint call).
CALL = "counterexample_repair"
STAGE = "counterexample_repair"
COUNTEREXAMPLE_FORMAT = "swdb.counterexample.v1"
SPURIOUS = "spurious_counterexample"
SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".inc"}


# --- the filter: only a refutation reaches repair ---------------------------------------------

def repairable(proof):
    """Why this proof record may not start a repair, or None when it may.

    Explicit filter (Yan-Ru 2026-10-14): a spurious counterexample is a tool or encoding failure; it
    never goes to the rewriting role. Neither does any other record that is not a refutation of a
    candidate artifact's proof unit with its counterexample inline."""
    if not isinstance(proof, dict) or proof.get("kind") != "proof":
        return "repair needs a proof record"
    rid = proof.get("id")
    if proof.get("failure_class") == SPURIOUS or "unreplayed_counterexample" in proof:
        return (f"proof record {rid} holds a spurious counterexample (failure class {SPURIOUS}): it did not "
                "replay on the compiled code, so it never goes to repair; fix the encoding, add the case to "
                "the regression corpus and rerun")
    if proof.get("verdict") != "refuted" or not proof.get("counterexample"):
        return (f"proof record {rid} is not a refutation with an inline counterexample (verdict "
                f"{proof.get('verdict') or 'none'}); only a refuted proof record starts a repair")
    if (proof.get("subject") or {}).get("kind") != "candidate_proof_unit":
        return f"proof record {rid} is not about a candidate artifact's proof unit"
    return None


# --- the cap: the method version's per-candidate budget ---------------------------------------

def cap(records):
    """`budgets.counterexample_repair_rounds` of the current method version (25 item 2)."""
    from swdb import method_version
    from swdb.library import default_root
    found = method_version.current(default_root(records))
    if found is None:
        raise Failure("no method version beside the records: the repair cap is its "
                      "budgets.counterexample_repair_rounds")
    rounds = (found.data.get("budgets") or {}).get("counterexample_repair_rounds")
    if not isinstance(rounds, int) or isinstance(rounds, bool) or rounds < 1:
        raise Failure(f"method version {found.id} has no budgets.counterexample_repair_rounds")
    return rounds, found.id


def lineage(store, candidate_id):
    """The repair lineage of the proposal that made this candidate artifact, or None."""
    candidate = store.get(candidate_id, "candidate") or {}
    proposal = store.get(candidate.get("proposal") or "", "proposal") or {}
    return proposal.get("repair_lineage")


def root_candidate(store, candidate_id):
    """The first refuted candidate artifact of the chain that holds this one."""
    seen = set()
    while candidate_id not in seen:
        seen.add(candidate_id)
        found = lineage(store, candidate_id)
        if not found:
            return candidate_id
        candidate_id = found["refuted_candidate"]
    raise Failure(f"repair lineage of {candidate_id} forms a cycle")


# --- the reverted-repair flag: a deterministic contract-match check ---------------------------

def _tokens():
    from swdb.cpp_lexical import LEXICAL
    return re.compile(LEXICAL.pattern + r"|[A-Za-z_]\w*|\S")


def _code(path):
    """Code tokens of one C/C++ file: comments and layout dropped, strings kept."""
    return [t for t in _tokens().findall(Path(path).read_text(errors="replace")) if not t.startswith(("//", "/*"))]


def normalized_sha256(artifact):
    """Content hash of a tree with C/C++ comments and layout removed (other files by their bytes)."""
    root = artifacts.verify(artifact)
    rows = []
    for entry in sorted(artifact["files"], key=lambda e: e["path"]):
        if Path(entry["path"]).suffix in SOURCE_SUFFIXES:
            rows.append([entry["path"], hashlib.sha256("\0".join(_code(root / entry["path"])).encode()).hexdigest()])
        else:
            rows.append([entry["path"], entry["sha256"]])
    return artifacts.digest(rows)


def offload_calls(library, contract_id):
    """The call names of the contract's offload: every intrinsic it uses, directly or through library
    operations, by the function name in its `signature`."""
    names, pending, seen = set(), [contract_id], set()
    while pending:
        entry = library.get(pending.pop()) or {}
        if entry.get("kind") == "intrinsic":
            match = re.search(r"(\w+)\s*\(", entry.get("signature") or "")
            if match:
                names.add(match.group(1))
            continue
        for ref in entry.get("uses_intrinsics", []) + entry.get("uses_library_operations", []):
            if ref not in seen:
                seen.add(ref)
                pending.append(ref)
    return names


def _calls_present(artifact, editable, names):
    import fnmatch
    root = artifacts.verify(artifact)
    found = set()
    for entry in artifact["files"]:
        name = entry["path"]
        if Path(name).suffix not in SOURCE_SUFFIXES or not any(fnmatch.fnmatchcase(name, p) for p in editable):
            continue
        tokens = _code(root / name)
        found |= {t for t, after in zip(tokens, tokens[1:] + [""]) if t in names and after == "("}
    return found


def contract_match(store, library, refuted, repaired, contract_id, editable):
    """The contract-match check (no LLM): does the repair still apply the refuted candidate artifact's
    rewrite contract? `reverted_repair` is set when the repaired tree's normalized content hash equals the
    baseline implementation's, or when it drops an offload call the refuted candidate artifact made
    (in its editable files)."""
    snapshot = store.get(repaired.get("source_snapshot") or "", "source_snapshot") or {}
    reasons = []
    repaired_hash = normalized_sha256(repaired["artifact"])
    baseline_hash = normalized_sha256(snapshot["artifact"]) if snapshot.get("artifact") else None
    if baseline_hash is not None and repaired_hash == baseline_hash:
        reasons.append("equals_baseline")
    names = offload_calls(library, contract_id)
    before = _calls_present(refuted["artifact"], editable, names)
    after = _calls_present(repaired["artifact"], editable, names)
    dropped = sorted(before - after)
    if dropped:
        reasons.append("drops_offload")
    return {"contract": contract_id, "reverted_repair": bool(reasons), "reasons": reasons,
            "offload_calls": {"refuted": sorted(before), "repaired": sorted(after), "dropped": dropped},
            "normalized_sha256": {"repaired": repaired_hash, "baseline": baseline_hash}}


# --- one round ------------------------------------------------------------------------------

def _certified(store, candidate_id, library):
    from swdb.extensa_boundary import certification_level
    return certification_level(store, candidate_id, library)["level"] == "certified"


def _new_proposal_id(store, root_proposal, round_number):
    base = f"{root_proposal}.cex-repair-{round_number}"
    rid, n = base, 1
    while store.get(rid) is not None or store.get(f"{rid}.candidate-1") is not None:
        n += 1
        rid = f"{base}.{n}"
    return rid


def call_opened(attempt):
    """True when the attempt's provider call opened (the provider process started): a guard refusal before
    the call leaves a workspace receipt without a command."""
    provider = attempt.get("provider") or {}
    return "command" in provider and attempt.get("state") != "provider_unavailable"


def _opened_calls(store, refuted_id, round_number):
    """Proposals of this round on this refuted candidate artifact whose provider call opened."""
    found = []
    for row in store.of_kind("proposal"):
        data = row.data
        found_lineage = data.get("repair_lineage") or {}
        if found_lineage.get("refuted_candidate") == refuted_id and found_lineage.get("round") == round_number:
            if any(call_opened(a) for a in data.get("attempts", [])):
                found.append(data["id"])
    return found


def check(records, proof_id, setting):
    """Everything the round checks before any record is written or call opens.

    Returns (proof, refuted candidate, its proposal, round, cap) or raises Failure."""
    from swdb.cli import _require_valid
    from swdb.extensa_boundary import _library_for
    if setting not in SETTINGS:
        raise Failure(f"repair setting must be one of {', '.join(SETTINGS)}")
    store = _require_valid(records)
    proof = store.get(proof_id, "proof")
    reason = repairable(proof) if proof is not None else f"proof record {proof_id!r} does not exist"
    if reason:
        raise Failure(reason)
    refuted_id = proof["subject"]["candidate"]
    refuted = store.get(refuted_id, "candidate")
    if refuted is None:
        raise Failure(f"refuted candidate artifact {refuted_id!r} does not exist")
    if ((proof.get("pins") or {}).get("code") or {}).get("sha256") != (refuted.get("artifact") or {}).get("sha256"):
        raise Failure(f"proof record {proof_id} pins another tree than candidate artifact {refuted_id}")
    library = _library_for(store)
    if not _certified(store, refuted_id, library) and setting != "evaluation":
        raise Failure(f"candidate artifact {refuted_id} is not certified: outside an evaluation repair run a "
                      "refuted record starts a repair only after certification (O1 applies to the evaluation only)")
    proposal = store.get(refuted.get("proposal") or "", "proposal")
    if proposal is None or not isinstance(proposal.get("request"), dict):
        raise Failure(f"candidate artifact {refuted_id} has no proposal with a request: a repair keeps its "
                      "request, intent and profile package")
    previous = lineage(store, refuted_id)
    number = (previous["round"] if previous else 0) + 1
    rounds, method = cap(records)
    if number > rounds:
        raise BudgetSpent(rounds, method, refuted_id)
    opened = _opened_calls(store, refuted_id, number)
    if opened:
        raise Failure(f"round {number} on {refuted_id} already made its provider call ({', '.join(opened)}); "
                      "a round has one call")
    return store, library, proof, refuted, proposal, number, rounds


class BudgetSpent(Failure):
    """The loop's budget is spent: a loop outcome, not a proof failure class."""

    def __init__(self, rounds, method, refuted_id):
        self.rounds = rounds
        super().__init__(f"counterexample repair budget spent: {rounds} of {rounds} rounds (method version "
                         f"{method}); no further provider call opens for {refuted_id}")


def repair_round(records, proof_id, *, runs_dir, provider_config, setting="archevolve", db_path=None,
                 run_index=None):
    """One round: one rewriting-role repair call on the refuted candidate artifact the proof record names.

    Returns the new proposal record (outcome `candidate_created` with its `candidate`, or `failed`,
    `unresolved`, `provider_unavailable` without one). Raises Failure before writing anything when the
    record may not start a repair, and `BudgetSpent` when the cap is reached."""
    from swdb import provider_adapters, provider_roles, rewrite, workflow
    store, library, proof, refuted, parent, number, rounds = check(records, proof_id, setting)
    with (Path(records) / f".swdb-cex-repair.{refuted['id']}.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Failure(f"a repair of {refuted['id']} is already running") from None
        store, library, proof, refuted, parent, number, rounds = check(records, proof_id, setting)
        config = rewrite.configuration(provider_config)
        root = store.get(root_candidate(store, refuted["id"]), "candidate")
        root_proposal = root.get("proposal") or parent["id"]
        pid = _new_proposal_id(store, root_proposal, number)
        contract = proof["pins"]["contract"]["id"]
        identity = provider_adapters.identity(config)
        data = workflow.record(
            "proposal", pid, producer=copy.deepcopy(parent["producer"]), request=copy.deepcopy(parent["request"]),
            payload_sha256=parent.get("payload_sha256"),
            outcome={"state": "submitted", "stage": STAGE, "reason": None}, attempts=[], raw_artifacts=[],
            source_snapshot=parent["source_snapshot"], profile_package=parent["profile_package"],
            repair_lineage={"refuted_candidate": refuted["id"], "counterexample_record": proof["id"],
                            "round": number, "reverted_repair": False},
            repair_budget={"counterexample_repair_rounds": rounds, "round": number, "setting": setting})
        if identity.get("resolved_kind") in provider_adapters.PINS:
            data["provider_pin"] = {"kind": identity["resolved_kind"], "model": identity["model"],
                                    "effort": identity["effort"]}
        if run_index is not None:
            data["run_index"] = run_index
        folder = artifacts.external_directory(runs_dir) / pid
        folder.mkdir(exist_ok=False)
        attempt = {"number": 1, "stage": STAGE, "state": "running", "call": CALL, "role": "rewriting",
                   "trigger_proof": proof["id"], "parent_candidate": refuted["id"], "round": number,
                   "limits": {"provider_seconds": config["timeout_s"], "rounds": rounds}}
        data["attempts"].append(attempt)
        data["raw_artifacts"].append({"stage": STAGE, "path": str(folder)})
        data["provider"] = config
        workflow.persist(records, data, db_path, create=True)
        try:
            source_path = artifacts.verify(refuted["artifact"])
            artifacts.check_protections(source_path, refuted["protections"])
            diff = Path(refuted.get("diff") or "")
            if not diff.is_file() or artifacts.file_hash(diff) != refuted.get("diff_sha256"):
                raise Failure(f"refuted candidate artifact {refuted['id']} has no retained patch matching its diff_sha256")
            package = store.get(parent["profile_package"], "profile_package")
            current_source = {"artifact": refuted["artifact"], "context": refuted["context"],
                              "protections": refuted["protections"]}
            evidence = {"kind": CALL, "setting": setting, "round": number, "rounds": rounds, "contract": contract,
                        "proof_record": proof["id"], "refuted_candidate": refuted["id"],
                        "refuted_tree_sha256": refuted["artifact"]["sha256"],
                        "counterexample": copy.deepcopy(proof["counterexample"]),
                        "refuted_patch": diff.read_text(), "bounds": copy.deepcopy(proof.get("bounds"))}
            response, meta = provider_roles.rewriting(config, data["request"], current_source, package, store,
                                                      folder / "provider", repair=evidence)
            workflow._provider_receipt(data, meta, folder / "provider")
            attempt.update(interpretation=rewrite.response_record(config, response), provider=meta)
            if response["unresolved"]:
                reason = "unresolved repair requirements: " + "; ".join(response["unresolved"])
                attempt.update(state="unresolved", reason=reason)
                data["outcome"] = {"state": "unresolved", "stage": STAGE, "reason": reason}
                return workflow.persist(records, data, db_path)
            if not response["interpretation"].strip() or not rewrite.response_has_edits(config, response):
                raise Failure("repair must explain its interpretation and produce actual code edits")
            editable = data["request"]["constraints"]["editable_files"]
            patch = rewrite.response_patch(config, response, source_path, editable, refuted["protections"],
                                           folder / "full-files")
            candidate_source = workflow._source_destination(runs_dir, f"{pid}.candidate-1")
            artifact = workflow.apply_patch(source_path, candidate_source, patch, editable, refuted["protections"])
            rewrite.require_code_change(source_path, candidate_source)
            artifacts.verify(refuted["artifact"])
            patch_file = folder / "candidate.diff"
            patch_file.write_text(patch)
            candidate = workflow.record(
                "candidate", f"{pid}.candidate-1", producer=data["producer"], proposal=pid,
                implementation=refuted["implementation"], source_snapshot=refuted["source_snapshot"],
                artifact=artifact, diff=str(patch_file), diff_sha256=artifacts.file_hash(patch_file),
                state="unverified", protections=refuted["protections"], context=refuted["context"],
                parent_candidate=refuted["id"])
            match = contract_match(store, library, refuted, candidate, contract, editable)
            workflow.persist(records, candidate, db_path, create=True)
            data["candidate"] = candidate["id"]
            data["repair_lineage"]["reverted_repair"] = match["reverted_repair"]
            attempt.update(state="completed", candidate=candidate["id"], contract_match=match)
            data["outcome"] = {"state": "candidate_created", "stage": STAGE, "reason": None}
        except (Failure, OSError, ValueError, subprocess.SubprocessError) as exc:
            if isinstance(exc, Failure) and "persisted, but query indexing failed" in str(exc):
                raise
            metadata = folder / "provider" / "provider.json"
            if metadata.is_file() and "provider" not in attempt:
                meta = json.loads(metadata.read_text())
                attempt["provider"] = meta
                workflow._provider_receipt(data, meta, folder / "provider")
            unavailable = isinstance(exc, provider_adapters.ProviderUnavailable)
            state = "provider_unavailable" if unavailable else "failed"
            attempt.update(state=state, reason=str(exc))
            data["outcome"] = {"state": state, "stage": STAGE, "reason": str(exc)}
        return workflow.persist(records, data, db_path)


# --- the loop -------------------------------------------------------------------------------

LOOP_STATES = ("repaired", "reverted", "budget_spent", "certification_failed", "provider_failed")


def loop(records, proof_id, *, runs_dir, provider_config, certify, gate, setting="campaign", db_path=None,
         run_index=None):
    """Counterexample-guided repair from one refuted proof record until it ends; the one loop for every mode.

    Each round: one rewriting-role repair call (`repair_round`), then `certify(candidate_id)` (the
    certification command on the repaired candidate artifact) and `gate(candidate_id)` (`swdb prove`'s
    bounded rungs; returns the proof record IDs it wrote). Round r repairs what round r-1 produced, citing
    its refutation; the cap covers the whole chain. The loop ends when:

    - `repaired`: the bounded rungs did not refute the repair (it counts as a repair);
    - `reverted`: the contract-match check flagged the repair (it competes, never counts as a repair);
    - `budget_spent`: every round's repair was refuted and the cap is reached (no further call opens);
    - `certification_failed`: the repair failed certification (the build or correctness repair cap may
      apply; this loop does not repair it);
    - `provider_failed`: the round's call failed or stayed unresolved.

    A spurious counterexample from the gate never continues the loop (`repairable`)."""
    from swdb.extensa_boundary import _library_for
    from swdb.store import Store
    rows, trigger = [], proof_id
    rounds_cap, _method = cap(records)
    while True:
        try:
            proposal = repair_round(records, trigger, runs_dir=runs_dir, provider_config=provider_config,
                                    setting=setting, db_path=db_path, run_index=run_index)
        except BudgetSpent as spent:
            return _outcome("budget_spent", rows, rounds_cap, str(spent))
        row = {"round": proposal["repair_lineage"]["round"], "proposal": proposal["id"], "trigger": trigger,
               "candidate": proposal.get("candidate"),
               "reverted_repair": proposal["repair_lineage"]["reverted_repair"],
               "call_opened": any(call_opened(a) for a in proposal["attempts"]), "proof_records": [],
               "refuted": None}
        rows.append(row)
        if proposal["outcome"]["state"] != "candidate_created":
            return _outcome("provider_failed", rows, rounds_cap, proposal["outcome"]["reason"])
        certify(row["candidate"])
        store = Store(records)
        if not _certified(store, row["candidate"], _library_for(store)):
            return _outcome("certification_failed", rows, rounds_cap,
                            f"repaired candidate artifact {row['candidate']} failed certification")
        row["proof_records"] = list(gate(row["candidate"]))
        store = Store(records)
        refutations = [rid for rid in row["proof_records"] if repairable(store.get(rid, "proof")) is None]
        row["refuted"] = bool(refutations)
        if row["reverted_repair"]:
            return _outcome("reverted", rows, rounds_cap,
                            f"the round {row['round']} repair no longer applies the rewrite contract")
        if not refutations:
            return _outcome("repaired", rows, rounds_cap, None)
        trigger = refutations[0]


def _outcome(state, rows, rounds_cap, reason):
    """The loop's outcome: never a proof failure class. A flagged repair is a reverted repair, never a repair."""
    return {"state": state, "reason": reason, "cap": rounds_cap, "rounds": len(rows),
            "calls": sum(1 for r in rows if r["call_opened"]),
            "repairs": [r["candidate"] for r in rows if r["candidate"] and not r["reverted_repair"]
                        and r["refuted"] is False],
            "reverted_repairs": [r["candidate"] for r in rows if r["candidate"] and r["reverted_repair"]],
            "chain": rows}
