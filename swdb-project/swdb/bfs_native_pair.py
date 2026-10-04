"""Prospective paired native collection and receipt admission. Updated: 2026-09-27.

2026-10-03 ET (ticket 38): raw rechecks use the evaluation's kernel plug-in.
2026-10-04 ET (ticket 63): evaluator v2 receipts recheck raw output with the compiled verifier.
"""

import copy
import json
import random
import re
import signal
import time
from pathlib import Path

from swdb import artifacts, bfs_native, kernels, workflow
from swdb.cli import Failure, _require_valid

METHOD = "native_paired.v1"
ANALYSIS = "paired_repetition_block_bootstrap.v1"
ROLES = ("baseline", "candidate")


def require(condition, message):
    if not condition:
        raise Failure(message)


def collection_policy(value):
    require(isinstance(value, dict) and set(value) == {"method", "order_seed"}
            and value.get("method") == METHOD, "unsupported native paired collection policy")
    bfs_native._integer(value.get("order_seed"), "collection.order_seed", minimum=0)
    return value


def schedule(sources, repetitions, collection):
    """Seeded, source-stratified balanced order; each role keeps the same source order."""
    collection_policy(collection)
    rng = random.Random(collection["order_seed"])
    orders = []
    for _ in sources:
        first = list(ROLES) * (repetitions // 2)
        if repetitions % 2:
            first.append(rng.choice(ROLES))
        rng.shuffle(first)
        orders.append(first)
    result = []
    for repetition in range(repetitions):
        for position, source in enumerate(sources):
            first = orders[position][repetition]
            for role in (first, ROLES[1 - ROLES.index(first)]):
                result.append({"sequence": len(result), "block": repetition,
                    "repetition": repetition, "source_position": position, "source": source, "role": role})
    return result


def validate_request(request):
    require(isinstance(request, dict) and request.get("message_version") == workflow.VERSION,
            "paired evaluation requires message_version 1.0")
    require(isinstance(request.get("id"), str) and re.fullmatch(r"[a-z0-9][a-z0-9._-]*", request["id"]),
            "paired evaluation requires a record ID")
    collection_policy(request.get("collection"))
    require(isinstance(request.get("budget"), dict), "paired evaluation requires a total budget")
    total = bfs_native._seconds(request["budget"].get("total_seconds"), "pair budget.total_seconds")
    members = [request.get(role) for role in ROLES]
    for role, member in zip(ROLES, members):
        _, repetitions, _, _ = bfs_native._request(member)
        require(repetitions >= 5, "paired collection requires at least five repetitions")
        require(member.get("protocol_role") == role if member.get("protocol") else
                member.get("protocol_role") in {None, role}, "paired evaluation has the wrong protocol role")
    a, b = members
    require(len({request["id"], a["id"], b["id"]}) == 3, "pair and evaluation IDs must be distinct")
    for key in ("machine", "workload", "sources", "repetitions", "threads", "roi", "protocol"):
        require(a.get(key) == b.get(key), f"paired requests disagree on {key}")
    for key, default in (("fixture", False), ("target_configuration", {})):
        require(a.get(key, default) == b.get(key, default), f"paired requests disagree on {key}")
    if a["candidate"] == b["candidate"]:
        require(a.get("build", {}) == b.get("build", {}), "A/A requires identical build settings")
    return total


def _advance(steps, slot=None):
    try:
        return False, steps.send(slot)
    except StopIteration as finished:
        return True, finished.value


def run(args):
    """One public path for unchanged A/A calibration and candidate A/B collection."""
    store = _require_valid(args.records)
    raw = Path(args.file).read_text()
    require(len(raw.encode()) <= bfs_native.MAX_REQUEST_BYTES, "paired request exceeds 10 MiB")
    request = workflow.message_from_text(raw)
    total = validate_request(request)
    require(all(store.get(rid) is None for rid in
                (request["id"], request["baseline"]["id"], request["candidate"]["id"])),
            "pair or evaluation ID already exists; earlier evidence cannot be overwritten")
    deadline = time.monotonic() + total
    planned = schedule(request["baseline"]["sources"], request["baseline"]["repetitions"], request["collection"])
    data = workflow.record("evaluation_pair", request["id"], request=copy.deepcopy(request),
        collection=copy.deepcopy(request["collection"]), schedule=planned,
        schedule_sha256=artifacts.digest(planned), request_sha256=artifacts.digest(request),
        outcome={"state": "running", "stage": "preparation", "reason": None},
        observations=[], evaluation_identities={}, started=bfs_native._now(), gain_claim=False,
        evidence_kind="contract_fixture" if request["baseline"].get("fixture") else "execution")
    workflow.persist(args.records, data, getattr(args, "db", None), create=True)
    active, evaluated, handlers = {}, {}, {}

    def save():
        workflow.persist(args.records, data, getattr(args, "db", None))

    def stopped(signum, frame):
        raise bfs_native.Stopped(f"paired collection interrupted by {signal.Signals(signum).name}")

    try:
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            handlers[sig] = signal.signal(sig, stopped)
        for role in ROLES:
            require(time.monotonic() < deadline, "pair total budget exhausted before preparation")
            pairing = {"pair_id": data["id"], "role": role, "collection": data["collection"],
                       "schedule_sha256": data["schedule_sha256"]}
            reuse = evaluated.get("baseline") if role == "candidate" and request[role]["candidate"] == request["baseline"]["candidate"] else None
            steps = bfs_native.evaluation_steps(args, request=request[role], pairing=pairing,
                                                reuse=reuse, deadline=deadline)
            active[role] = steps
            finished, evaluated[role] = _advance(steps)
            data[role + "_evaluation"] = evaluated[role]["id"]
            save()
            if finished:
                active.pop(role)
                raise Failure(f"{role} preparation failed: {evaluated[role]['outcome']['reason']}")
        data.update(prepared_at=bfs_native._now())
        data["outcome"]["stage"] = "collection"
        save()
        for slot in planned:
            role = slot["role"]
            finished, evaluated[role] = _advance(active[role], slot)
            if finished:
                active.pop(role)
                raise Failure(f"{role} trial failed: {evaluated[role]['outcome']['reason']}")
            evaluation = evaluated[role]
            observation, check = evaluation["timing"][-1], evaluation["correctness"]["checks"][-1]
            data["observations"].append({**copy.deepcopy(slot), "evaluation": evaluation["id"],
                "started": observation["pairing"]["started"], "finished": observation["pairing"]["finished"],
                "output": observation["output"], "output_sha256": observation["output_sha256"],
                "binary_sha256": observation["binary_sha256"],
                "observation_sha256": artifacts.digest(observation), "correctness_sha256": artifacts.digest(check)})
            save()
        for role in ROLES:
            finished, evaluated[role] = _advance(active[role])
            require(finished, "paired collector emitted unexpected additional trial")
            active.pop(role)
            require(evaluated[role]["outcome"]["state"] == "complete", f"{role} finalization failed")
        require(time.monotonic() < deadline, "pair total budget exhausted before completion")
        data["outcome"] = {"state": "complete", "stage": "collection", "reason": None}
    except (Failure, bfs_native.StageFailure, bfs_native.Stopped, OSError, ValueError) as exc:
        data["outcome"] = {"state": "interrupted" if isinstance(exc, bfs_native.Stopped) else "failed",
                           "stage": data["outcome"]["stage"], "reason": str(exc)}
    finally:
        for role, steps in active.items():
            try:
                steps.throw(bfs_native.StageFailure("interrupted", "paired collection did not complete"))
            except StopIteration as finished:
                evaluated[role] = finished.value
            finally:
                steps.close()
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
        data["evaluation_identities"] = {row["id"]: artifacts.digest(row) for row in evaluated.values() if row}
        data["finished"] = bfs_native._now()
        data["receipt_sha256"] = artifacts.digest(data)
        save()
    return data


def validate_receipt(store, baseline, candidate, settings, *, verify_raw=True):
    """Admit only exact complete paired evidence; no metadata-only relabeling.

    `verify_raw=False` (2026-09-27 ET) is only for a reader that cannot reach the
    collecting host's files, such as the acceptance report on the Mac. It still
    checks every retained record binding, digest, schedule, and correctness
    claim, but skips reopening the graph, binaries, logs, and raw parent vectors.
    The caller must report that the raw evidence is unverified; this mode never
    turns missing local evidence into verified evidence.
    """
    from swdb.bfs_protocol import _get, _timestamp, materialize_workload, verify_immutable
    collection = settings["sampling"]["collection"]
    evaluations = dict(zip(ROLES, (baseline, candidate)))
    pairing = baseline.get("context", {}).get("pairing")
    require(isinstance(pairing, dict), "baseline has no paired collection binding")
    pair_id = pairing.get("pair_id")
    pair = store.get(pair_id, "evaluation_pair")
    require(pair is not None and pair.get("outcome", {}).get("state") == "complete", "missing or incomplete paired receipt")
    require(pair.get("receipt_sha256") == artifacts.digest({key: value for key, value in pair.items() if key != "receipt_sha256"}),
            "paired receipt identity changed")
    request = pair["request"]
    validate_request(request)
    require(pair["request_sha256"] == artifacts.digest(request) and pair["collection"] == collection
            and request["collection"] == collection, "paired request or frozen collection policy changed")
    planned = schedule(baseline["context"]["sources"], settings["sampling"]["repetitions"], collection)
    require(pair["schedule"] == planned and pair["schedule_sha256"] == artifacts.digest(planned),
            "paired schedule differs from the prospective seeded order")
    require(len(pair["observations"]) == len(planned), "paired receipt has incomplete trial coverage")
    workload_id = baseline["context"]["workload"]["id"]
    from swdb import bfs_native_scalable as scalable
    v2 = scalable.evaluator_of_settings(settings) == scalable.EVALUATOR_V2
    if verify_raw and v2:
        # Ticket 63: v2 re-binds the registered SG file by hash; no Python adjacency.
        registered = _get(store, workload_id, "workload")
        verify_immutable(registered)
        canonical, actual_workload = None, {"canonical_sha256": registered["definition"]["canonical_sha256"]}
        for evaluation in evaluations.values():
            graph_input = evaluation["context"]["workload"].get("graph_input", {})
            require(any(rep.get("sha256") == graph_input.get("sha256") and rep.get("path") == graph_input.get("path")
                        for rep in registered["definition"]["representations"])
                    and artifacts.file_hash(graph_input["path"]) == graph_input["sha256"],
                    "paired SG input differs from the registered representation")
    elif verify_raw:
        canonical, actual_workload = bfs_native.canonical_graph(materialize_workload(store, workload_id))
    else:
        registered = _get(store, workload_id, "workload")
        verify_immutable(registered)
        canonical, actual_workload = None, {"canonical_sha256": registered["definition"]["canonical_sha256"]}
    require(all(evaluation["context"]["workload"].get("id") == workload_id
                and evaluation["context"]["workload"].get("canonical_sha256") == actual_workload["canonical_sha256"]
                for evaluation in evaluations.values()), "paired graph differs from revalidated canonical adjacency")
    previous = _timestamp(pair["prepared_at"])
    outputs = set()
    for role, evaluation in evaluations.items():
        expected = {"pair_id": pair_id, "role": role, "collection": collection, "schedule_sha256": pair["schedule_sha256"]}
        require(pair.get(role + "_evaluation") == evaluation["id"]
                and evaluation["context"].get("pairing") == expected
                and pair["evaluation_identities"].get(evaluation["id"]) == artifacts.digest(evaluation)
                and request[role] == evaluation["request"], "evaluation is mismatched, changed, or from another pair")
        require(evaluation.get("evidence_kind") == pair["evidence_kind"], "paired evidence classification differs")
        builds = [stage for stage in evaluation["stages"] if stage["stage"] in {"build", "build_reuse"}]
        require(len(builds) == 1 and builds[0]["state"] == "complete"
                and _timestamp(builds[0]["finished"]) <= previous, "both artifacts must be ready before paired trials")
        require(not verify_raw or artifacts.file_hash(evaluation["build"]["binary"]) == evaluation["build"]["binary_sha256"],
                "paired timed binary changed or is unavailable")
    if baseline["candidate"] == candidate["candidate"]:
        require(baseline["build"]["binary"] == candidate["build"]["binary"]
                and candidate["build"].get("reused_from_evaluation") == baseline["id"], "A/A must reuse its exact compiled executable")
    for slot, retained in zip(planned, pair["observations"]):
        require(all(retained.get(key) == value for key, value in slot.items()), "paired receipt reordered its observations")
        evaluation = evaluations[slot["role"]]
        index = slot["repetition"] * len(evaluation["context"]["sources"]) + slot["source_position"]
        observation, check = evaluation["timing"][index], evaluation["correctness"]["checks"][index]
        binding = observation.get("pairing", {})
        require(isinstance(binding, dict) and all(binding.get(key) == value for key, value in slot.items()) and binding.get("pair_id") == pair_id
                and check.get("pairing") == binding, "paired timing and correctness lack their exact schedule binding")
        require(retained["evaluation"] == evaluation["id"] and retained["observation_sha256"] == artifacts.digest(observation)
                and retained["correctness_sha256"] == artifacts.digest(check)
                and all(retained[key] == observation[key] for key in ("output", "output_sha256", "binary_sha256")),
                "paired receipt no longer binds the exact timed output and correctness")
        started, finished = _timestamp(binding["started"]), _timestamp(binding["finished"])
        require(previous <= started <= finished and retained["started"] == binding["started"]
                and retained["finished"] == binding["finished"], "paired execution timestamps contradict the schedule")
        previous = finished
        executions = [stage for stage in evaluation["stages"] if stage["stage"] == "execution"
                      and stage.get("repetition") == slot["repetition"] and stage.get("source_position") == slot["source_position"]]
        require(len(executions) == 1 and executions[0]["state"] == "complete"
                and all(executions[0].get(key) == binding[key] for key in ("started", "finished"))
                and executions[0].get("log") == binding["execution_log"]
                and executions[0].get("log_sha256") == binding["execution_log_sha256"],
                "paired receipt is not linked to its actual execution stage")
        require(observation["output"] not in outputs, "paired trials must have distinct process outputs")
        outputs.add(observation["output"])
        if not verify_raw:
            require(check.get("graph_sha256") == actual_workload["canonical_sha256"] and check.get("passed") is True
                    and check.get("source") == slot["source"],
                    "paired retained correctness does not bind a passed check to the registered graph and source")
            continue
        if v2:
            try:
                raw, raw_hash = bfs_native.json_observation(observation["output"], scalable.TRIAL_RECORD_LIMIT,
                                                           "paired raw trial record")
            except bfs_native.StageFailure as exc:
                raise Failure(str(exc)) from None
            require(raw_hash == observation["output_sha256"]
                    and artifacts.file_hash(binding["execution_log"]) == binding["execution_log_sha256"],
                    "paired raw execution evidence changed or is unavailable")
            require(scalable.check_trial_record(raw, slot["source"], evaluation["context"]["threads"], observation["roi"],
                                                evaluation["context"]["workload"]["num_vertices"]) is None
                    and type(raw.get("duration_s")) in (int, float) and raw["duration_s"] == observation["duration_s"],
                    "paired timing/context differs from its hash-bound raw output")
            checked = scalable.recheck_retained(evaluation, observation, check, slot["source"], graph_checked=True)
            checked["parents_sha256"] = observation.get("parents_sha256")
            require(checked["passed"], "paired raw parent vector failed independent structural verification: "
                    + str(checked["reason"]))
            require(check.get("graph_sha256") == actual_workload["canonical_sha256"]
                    and all(check.get(key) == value for key, value in checked.items()),
                    "paired retained correctness differs from the independent raw-result check")
            continue
        # Ticket 38 (2026-10-03 ET): the evaluation's retained native verifier
        # selects its kernel plug-in; records before the seam are BFS.
        plugin = kernels.by_native_verifier(evaluation["context"].get("verifier"))
        try:
            raw, raw_hash = bfs_native.json_observation(observation["output"], plugin.native_output_limit(bfs_native.MAX_VERTICES),
                                                       "paired raw execution output")
        except bfs_native.StageFailure as exc:
            raise Failure(str(exc)) from None
        require(raw_hash == observation["output_sha256"]
                and artifacts.file_hash(binding["execution_log"]) == binding["execution_log_sha256"],
                "paired raw execution evidence changed or is unavailable")
        require(raw.get("format") == plugin.native_trial_format
                and type(raw.get("source")) is int and raw["source"] == slot["source"]
                and type(raw.get("configured_threads")) is int and raw["configured_threads"] == evaluation["context"]["threads"]
                and raw.get("roi") == observation["roi"]
                and type(raw.get("duration_s")) in (int, float) and raw["duration_s"] == observation["duration_s"],
                "paired timing/context differs from its hash-bound raw output")
        checked = plugin.check_native_trial(canonical["adjacency"], slot["source"], raw,
                                            application=evaluation["context"].get("application"))
        require(checked["passed"], f"paired raw {'parent vector' if plugin is kernels.BFS else 'result'} failed independent "
                f"{'structural ' if plugin is kernels.BFS else ''}verification: " + str(checked["reason"]))
        require(check.get("graph_sha256") == actual_workload["canonical_sha256"]
                and all(check.get(key) == value for key, value in checked.items()),
                "paired retained correctness differs from the independent raw-result check")
    require(previous <= _timestamp(pair["finished"]), "paired receipt finished before its trials")
    return {"id": pair_id, "receipt_sha256": pair["receipt_sha256"], "schedule_sha256": pair["schedule_sha256"]}
