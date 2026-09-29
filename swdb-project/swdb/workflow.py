"""Public, durable proposal workflow. Source changes never imply correctness.

Updated: 2026-09-29 (pinned repair identity and unavailable-provider retries); 2026-09-28 (patch headers
parsed outside hunk bodies only). YAML records remain authoritative; raw artifacts are external.
"""

import copy
import fcntl
import fnmatch
import hashlib
import json
import re
import socket
import subprocess
import uuid
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from swdb import artifacts, db, writer, yamlio
from swdb.cli import Failure, _require_valid
from swdb.store import Store

VERSION = "1.0"
OPERATOR = {"name": "swdb", "role": "operator", "test_client": False}


def message_from_text(raw):
    """Retain invalid YAML messages without committing JSON-incompatible values."""
    try:
        request = yaml.load(raw, Loader=yamlio._Loader)
    except (yaml.YAMLError, TypeError, ValueError, RecursionError) as exc:
        return {"raw_text": raw, "parse_error": str(exc)}
    try:
        encoded = json.dumps(request, allow_nan=False)
        if json.loads(encoded) != request:
            raise ValueError("message changes during JSON serialization")
    except (TypeError, ValueError, RecursionError):
        return {"raw_text": raw, "parse_error": "request is not a JSON-compatible message"}
    return request


def _source_destination(runs_dir, rid):
    """Keep buildable source on mbit10's source/build volume (2026-09-25)."""
    base = (Path('/data1/yanruj/EvolveSWDB_sources')
            if socket.gethostname().split('.')[0] == 'mbit10' else Path(runs_dir))
    return artifacts.external_directory(base) / rid / 'source'


def record(kind, rid, **fields):
    return {"kind": kind, "schema_version": "0.4", "id": rid, "status": "draft",
            "created": writer.today(), "updated": writer.today(), "message_version": VERSION,
            "producer": copy.deepcopy(OPERATOR),
            "provenance": [{"id": "workflow", "kind": "agent_run",
                            "description": "Created through the public SWDB workflow.", "uri": None}], **fields}


def persist(records, data, db_path=None, *, create=False):
    """Commit metadata first; an index error reports that the durable record survives."""
    data["updated"] = writer.today()
    try:
        encoded = json.dumps(data, allow_nan=False)
        if json.loads(encoded) != data:
            raise ValueError("record changes during JSON serialization")
    except (TypeError, ValueError, RecursionError) as exc:
        raise Failure(f"record {data['id']} is not JSON-compatible; nothing was persisted: {exc}") from None
    writer.commit(records, new=[data] if create else [], upsert=[] if create else [data])
    try:
        db.build(records, db_path or db.default_path(records))
    except (OSError, ValueError, db.sqlite3.Error) as exc:
        raise Failure(f"record {data['id']} persisted, but query indexing failed: {exc}") from None
    return data


def snapshot(args):
    store = _require_valid(args.records)
    impl = store.get(args.implementation, "implementation")
    if not impl:
        raise Failure(f"unknown implementation {args.implementation!r}")
    rid = args.id or f"snapshot-{uuid.uuid4().hex}"
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", rid):
        raise Failure("snapshot id must use the record identifier syntax")
    if store.get(rid):
        raise Failure(f"record {rid!r} already exists")
    context = store.source_context(impl)
    source = artifacts.source_root(store, impl)
    destination = _source_destination(args.runs_dir, rid)
    if source == destination or source in destination.parents:
        raise Failure("a source snapshot cannot be materialized inside its input source")
    artifact = artifacts.copy_snapshot(source, destination)
    regions = []
    for code in context["code"]:
        text = (destination / code["path"]).read_text()
        lines = code.get("lines") or [1, len(text.splitlines())]
        fragment = "".join(text.splitlines(keepends=True)[lines[0]-1:lines[1]])
        h = hashlib.sha256(fragment.encode()).hexdigest()
        regions.append({"id": f"{code['path']}:{lines[0]}-{lines[1]}:{h[:16]}",
                        "path": code["path"], "lines": lines, "source_sha256": h,
                        "text": fragment, "association": "declared_source_region"})
    data = record("source_snapshot", rid, implementation=impl["id"], application=context["application"],
                  revision=context["source"]["commit"], artifact=artifact, context=context,
                  regions=regions, protections=artifacts.protections(destination, context))
    return persist(args.records, data, args.db, create=True)


def fixture_package(args):
    store = _require_valid(args.records)
    source = store.get(args.snapshot, "source_snapshot")
    if not source:
        raise Failure("source snapshot does not exist")
    artifacts.verify(source["artifact"])
    if store.get(args.id):
        raise Failure(f"record {args.id!r} already exists")
    return persist(args.records, record("profile_package", args.id,
        producer={"name": "swdb-contract-fixture", "role": "operator", "test_client": True},
        implementation=source["implementation"], source_snapshot=source["id"],
        context={"fixture": True, "source_sha256": source["artifact"]["sha256"]},
        completeness="fixture", regions=source["regions"], dynamic_memory=[], constraints={"protections": source["protections"]},
        evidence={"classification": "contract_fixture"},
        reasons=["Explicit contract fixture: no execution, correctness, profiling, or gain evidence."]), args.db, create=True)


def baseline_candidate(args):
    """Materialize the exact starting source for a baseline or reference execution."""
    store = _require_valid(args.records)
    source = store.get(args.snapshot, "source_snapshot")
    if not source:
        raise Failure("source snapshot does not exist")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", args.id) or store.get(args.id):
        raise Failure("baseline candidate needs a new valid record identifier")
    root = artifacts.verify(source["artifact"])
    artifact = artifacts.copy_snapshot(root, _source_destination(args.runs_dir, args.id))
    artifacts.check_protections(Path(artifact["path"]), source["protections"])
    if artifact["sha256"] != source["artifact"]["sha256"]:
        raise Failure("baseline materialization changed the starting source")
    return persist(args.records, record("candidate", args.id, artifact_role="source_baseline",
        implementation=source["implementation"], source_snapshot=source["id"], artifact=artifact,
        state="unverified", protections=source["protections"], context=source["context"]), args.db, create=True)


def get_record(args):
    store = db.query_store(args.records, getattr(args, "db", None))
    data = store.get(args.id)
    if data is None:
        raise Failure(f"record {args.id!r} does not exist")
    if getattr(args, "chain", False):
        seen = {}
        downstream = {}
        for kind, keys in (("evaluation", ("candidate", "proposal")),
                           ("region_profile", ("evaluation",)),
                           ("profile_package", ("evaluation",))):
            for row in store.of_kind(kind):
                for key in keys:
                    parent = row.data.get(key)
                    if parent:
                        downstream.setdefault(parent, []).append(row.data)
        def visit(d):
            if d["id"] in seen:
                return
            seen[d["id"]] = d
            def mapping(value):
                return value if isinstance(value, dict) else {}
            linked = [d.get(key) for key in (
                "proposal", "candidate", "source_snapshot", "profile_package", "parent_candidate",
                "protocol", "candidate_evaluation", "baseline_evaluation", "comparison_baseline",
                "evaluation", "region_profile", "implementation", "application", "kernel",
                "machine", "hardware_target")]
            request, build, settings = (mapping(d.get(key)) for key in ("request", "build", "settings"))
            context = mapping(d.get("context"))
            linked.append(mapping(context.get("pairing")).get("pair_id"))
            linked.extend(owner.get("protocol") for owner in (request, context))
            linked.append(context.get("target"))
            for owner in (d, request, context):
                workload = owner.get("workload")
                linked.append(workload if isinstance(workload, str) else mapping(workload).get("id"))
            linked.extend(mapping(d.get("workload_identities")))
            if isinstance(settings.get("workloads"), list):
                linked.extend(settings["workloads"])
            linked.extend(request.get(key) for key in (
                "build_evaluation", "candidate_build", "diagnostic_evaluation", "checkpoint_evaluation"))
            linked.extend(mapping(request.get("region_packages")).values())
            linked.append(mapping(build.get("model_build")).get("evaluation"))
            simulation = mapping(settings.get("simulation_identity"))
            linked.append(mapping(simulation.get("model_build")).get("evaluation"))
            for reference in mapping(settings.get("reference_artifacts")).values():
                linked.extend(mapping(reference).get(key) for key in ("candidate", "source_snapshot"))
            for record_id in linked:
                target = store.get(record_id) if isinstance(record_id, str) else None
                if target:
                    visit(target)
            for component in d.get('component_evaluations', []):
                target = store.get(component.get('evaluation'))
                if target:
                    visit(target)
            for target in downstream.get(d["id"], []):
                visit(target)
            if d["kind"] == "proposal":
                for attempt in d["attempts"]:
                    for key in ("candidate", "parent_candidate", "trigger_evaluation"):
                        target = store.get(attempt.get(key))
                        if target:
                            visit(target)
        visit(data)
        return {"root": data["id"], "records": seen}
    return data


def _request_error(request):
    schema_path = Path(__file__).resolve().parents[1] / "schemas/messages/rewrite-proposal.schema.json"
    schema = json.loads(schema_path.read_text())
    problems = sorted(Draft202012Validator(schema).iter_errors(request), key=lambda e: str(e.path))
    if problems:
        return "proposal contract: " + "; ".join(e.message for e in problems[:5])
    for name in request["constraints"]["editable_files"]:
        artifacts.relative_path(name)
    return None


def check_capabilities(request, store):
    """Unknown accelerator capabilities stay unresolved until a backend contract checks them."""
    if request.get("required_operations") or request.get("require_executable_backend"):
        try:
            from swdb.capabilities import check_requirements
        except ImportError:
            return "required operation support is unresolved: no applicable operation contract"
        return check_requirements(request, store)
    return None


def _patch_paths(patch):
    """Names from per-file '--- '/'+++ ' headers; hunk bodies are skipped by their @@ line counts (2026-09-28)."""
    mentioned, old, new = [], 0, 0
    for line in patch.splitlines():
        if old > 0 or new > 0:
            tag = line[:1]
            if tag == "\\":
                continue
            if tag in (" ", ""):
                old, new = old - 1, new - 1
                continue
            if tag == "-":
                old -= 1
                continue
            if tag == "+":
                new -= 1
                continue
            old = new = 0  # malformed hunk; the apply check below rejects it
        hunk = re.match(r"@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@", line)
        if hunk:
            old, new = (1 if count is None else int(count) for count in hunk.groups())
        elif line.startswith(("--- ", "+++ ")):
            name = line[4:].split("\t", 1)[0]
            if name == "/dev/null":
                continue
            if not name.startswith(("a/", "b/")):
                raise Failure("patch paths must use a/ and b/ prefixes")
            mentioned.append(artifacts.relative_path(name[2:]))
    return mentioned


def apply_patch(source, destination, patch, allowed, protections):
    if not isinstance(patch, str) or not patch.strip():
        raise Failure("patch payload must contain an actual unified diff")
    if re.search(r"\bmode 120000\b", patch) or "GIT binary patch" in patch:
        raise Failure("symbolic-link and binary patches are not supported")
    mentioned = _patch_paths(patch)
    if not mentioned:
        raise Failure("patch has no textual file edits")
    for name in mentioned:
        if not any(fnmatch.fnmatchcase(name, pattern) for pattern in allowed):
            raise Failure(f"patch changes a file outside its declared edit scope: {name}")
    artifacts.copy_snapshot(source, destination)
    for check in (True, False):
        cmd = ["git", "apply", "--no-index", "--whitespace=nowarn"]
        if check:
            cmd += ["--check"]
        result = subprocess.run(cmd + ["-"], input=patch, text=True, cwd=destination,
                                capture_output=True, timeout=30)
        if result.returncode:
            raise Failure(f"patch application failed: {result.stderr.strip()}")
    artifacts.check_protections(destination, protections)
    before, after = artifacts.identify(source), artifacts.identify(destination)
    if before["sha256"] == after["sha256"]:
        raise Failure("proposal produced no source change")
    old = {f["path"]: f for f in before["files"]}
    new = {f["path"]: f for f in after["files"]}
    for name in old.keys() | new.keys():
        if old.get(name) != new.get(name) and not any(fnmatch.fnmatchcase(name, p) for p in allowed):
            raise Failure(f"candidate changed undeclared supporting input {name}")
    return after


def submit(args):
    store = _require_valid(args.records)
    raw = args.file.read_text()
    if len(raw.encode()) > 10 * 1024 * 1024:
        raise Failure("proposal exceeds the 10 MiB request limit")
    request = message_from_text(raw)
    rid = request.get("id") if isinstance(request, dict) else None
    if not isinstance(rid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", rid):
        rid = f"proposal-invalid-{uuid.uuid4().hex}"
    if store.get(rid):
        raise Failure(f"proposal ID {rid!r} is already used; retained evidence is immutable")
    data = record("proposal", rid, request=request, payload_sha256=None,
                  outcome={"state": "submitted", "stage": "submission", "reason": None}, attempts=[], raw_artifacts=[])
    persist(args.records, data, args.db, create=True)
    stage = "validation"
    try:
        reason = _request_error(request)
        if reason:
            raise Failure(reason)
        data["producer"] = request["producer"]
        data["payload_sha256"] = artifacts.digest(request["payload"])
        source = store.get(request["source_snapshot"], "source_snapshot")
        package = store.get(request["profile_package"], "profile_package")
        if not source or not package:
            raise Failure("source snapshot or profile package is missing")
        from swdb.profile_package import verify as verify_package
        verify_package(package)
        if source["implementation"] != request["implementation"] or package["implementation"] != request["implementation"]:
            raise Failure("conflicting implementation/source/profile-package identities")
        if package["source_snapshot"] != source["id"] or source["artifact"]["sha256"] != request["source_sha256"]:
            raise Failure("stale or conflicting source identity")
        known_regions = {r["id"] for r in package["regions"] if isinstance(r, dict) and "id" in r}
        if not set(request["regions"]) <= known_regions:
            raise Failure("requested region is absent from the identified profile package")
        data.update(source_snapshot=source["id"], profile_package=package["id"])
        source_path = artifacts.verify(source["artifact"])
        reason = check_capabilities(request, store)
        if reason:
            data["outcome"] = {"state": "unresolved", "stage": "capabilities", "reason": reason}
            return persist(args.records, data, args.db)
        config = None
        if request["payload"]["kind"] != "patch":
            from swdb import rewrite

            try:
                config = rewrite.configuration(getattr(args, "provider_config", None))
            except (Failure, OSError, yaml.YAMLError) as exc:
                data["outcome"] = {"state": "unresolved", "stage": "provider_configuration", "reason": str(exc)}
                return persist(args.records, data, args.db)
        stage = "rewriting"
        run_dir = artifacts.external_directory(args.runs_dir) / rid
        run_dir.mkdir(exist_ok=False)
        data["raw_artifacts"].append({"path": str(run_dir), "stage": stage})
        data["attempts"].append({"number": 1, "stage": stage, "state": "running"})
        persist(args.records, data, args.db)
        patch = request["payload"]["content"]
        if config is not None:
            data["provider"] = config
            data["repair_budget"] = {"max_repairs": config["max_repairs"], "total_seconds": config["total_seconds"],
                                     "used_seconds": 0, "repairs": 0}
            data["attempts"][-1]["stage"] = "interpretation"
            persist(args.records, data, args.db)
            response, meta = rewrite.call(config, request, source, package, store, run_dir / "provider-1")
            data["interpretation"] = rewrite.response_record(config, response)
            data["repair_budget"]["used_seconds"] = meta["host_wall_s"]
            data["attempts"][-1]["provider"] = meta
            _provider_receipt(data, meta, run_dir / "provider-1")
            if response["unresolved"]:
                data["outcome"] = {"state": "unresolved", "stage": "interpretation", "reason": "; ".join(response["unresolved"])}
                data["attempts"][-1]["state"] = "unresolved"
                return persist(args.records, data, args.db)
            if not rewrite.response_has_edits(config, response) or not response["interpretation"].strip():
                raise Failure("rewrite interpretation must produce actual edits and explain them")
            data["attempts"][-1]["stage"] = stage
            persist(args.records, data, args.db)
            # full_files: SWDB computes the diff; the patch route returns the provider's diff.
            patch = rewrite.response_patch(config, response, source_path, request["constraints"]["editable_files"],
                                           source["protections"], run_dir / "full-files")
        candidate_source = _source_destination(args.runs_dir, rid)
        candidate_artifact = apply_patch(source_path, candidate_source, patch,
                                         request["constraints"]["editable_files"], source["protections"])
        if config is not None:
            rewrite.require_code_change(source_path, candidate_source)
        artifacts.verify(source["artifact"])
        (run_dir / "candidate.diff").write_text(patch)
        candidate = record("candidate", f"{rid}.candidate-1", producer=request["producer"], proposal=rid,
                           implementation=source["implementation"], source_snapshot=source["id"],
                           artifact=candidate_artifact, diff=str(run_dir / "candidate.diff"),
                           diff_sha256=artifacts.file_hash(run_dir / "candidate.diff"), state="unverified",
                           protections=source["protections"], context=source["context"])
        persist(args.records, candidate, args.db, create=True)
        data["candidate"] = candidate["id"]
        data["attempts"][-1]["state"] = "completed"
        data["attempts"][-1]["candidate"] = candidate["id"]
        data["outcome"] = {"state": "candidate_created", "stage": stage, "reason": None}
    except (Failure, OSError, ValueError, subprocess.SubprocessError) as exc:
        if isinstance(exc, Failure) and "persisted, but query indexing failed" in str(exc):
            raise
        unavailable = isinstance(exc, rewrite.provider_adapters.ProviderUnavailable) if "provider" in data else False
        data["outcome"] = {"state": "provider_unavailable" if unavailable else
                           ("rejected" if stage == "validation" else "failed"), "stage": stage, "reason": str(exc)}
        if data["attempts"]:
            data["attempts"][-1].update(state="provider_unavailable" if unavailable else "failed", reason=str(exc))
            if "provider" in data and "provider" not in data["attempts"][-1]:
                metadata = run_dir / "provider-1" / "provider.json"
                if metadata.is_file():
                    meta = json.loads(metadata.read_text())
                    data["attempts"][-1]["provider"] = meta
                    _provider_receipt(data, meta, run_dir / "provider-1")
                    data["repair_budget"]["used_seconds"] += meta.get("host_wall_s", 0)
    return persist(args.records, data, args.db)


def _repairable_build_failure(evaluation, candidate):
    outcome = evaluation.get("outcome", {})
    if outcome.get("state") != "failed":
        return False
    if outcome.get("stage") == "build":
        return True
    if outcome.get("stage") != "candidate_compile":
        return False
    context = evaluation.get("context", {})
    return (context.get("backend") == "dx100-gem5-se"
            and context.get("candidate_sha256") == candidate["artifact"]["sha256"]
            and evaluation.get("request", {}).get("candidate") == candidate["id"]
            and evaluation.get("source_snapshot") == candidate["source_snapshot"]
            and evaluation.get("build", {}).get("adapter") in {"dx100.complete_call.v1", "dx100.complete_call.v2"}
            and any(stage.get("stage") == "candidate_compile" and stage.get("state") == "failed"
                    and type(stage.get("returncode")) is int and stage["returncode"] != 0
                    and stage.get("log_sha256") for stage in evaluation.get("stages", [])))


def repair(args):
    """Retain a new repair candidate without changing strategy or discarding failures."""
    from swdb import rewrite

    store = _require_valid(args.records)
    unavailable = store.get(args.evaluation, "proposal")
    if unavailable and unavailable.get("outcome", {}).get("state") == "provider_unavailable" and not unavailable.get("candidate"):
        return _retry_initial_provider(args, store, unavailable)
    evaluation = store.get(args.evaluation, "evaluation")
    if not evaluation or not evaluation.get("proposal"):
        raise Failure("repair requires a retained candidate evaluation")
    proposal_id = evaluation["proposal"]
    with (Path(args.records) / f".swdb-rewrite.{proposal_id}.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Failure("a repair of this proposal is already running") from None
        store = Store(args.records)
        data = copy.deepcopy(store.get(proposal_id, "proposal"))
        config = rewrite.configuration(args.provider_config)
        rewrite.require_same_provider(data.get("provider"), config)
        budget = data.setdefault("repair_budget", {"max_repairs": config["max_repairs"],
            "total_seconds": config["total_seconds"], "used_seconds": 0, "repairs": 0})
        maximum = min(budget["max_repairs"], config["max_repairs"])
        seconds = min(budget["total_seconds"], config["total_seconds"]) - budget["used_seconds"]
        prior = store.get(evaluation.get("candidate"), "candidate")
        reason = None
        if not prior or prior["id"] != data.get("candidate") or prior.get("proposal") != proposal_id:
            reason = "repair evaluation does not name the latest candidate of this proposal"
        elif not (_repairable_build_failure(evaluation, prior)
                  or evaluation["correctness"]["state"] == "failed"):
            reason = "only build or correctness failures admit repairs; regressions do not trigger tuning"
        elif budget["repairs"] >= maximum or seconds <= 0:
            reason = "repair attempt or provider-time budget exhausted"
        if reason:
            data["outcome"] = {"state": "unresolved", "stage": "repair", "reason": reason}
            return persist(args.records, data, args.db)
        data.setdefault("provider", config)
        number = budget["repairs"] + 1
        folder = artifacts.external_directory(args.runs_dir) / f"{proposal_id}.repair-{number}.attempt-{len(data['attempts'])+1}"
        folder.mkdir(exist_ok=False)
        budget["repairs"] = number
        attempt = {"number": len(data["attempts"]) + 1, "stage": "repair", "state": "running",
                   "trigger_evaluation": evaluation["id"], "parent_candidate": prior["id"],
                   "limits": {"provider_seconds": min(seconds, config["timeout_s"]), "max_repairs": maximum}}
        data["attempts"].append(attempt)
        data["raw_artifacts"].append({"stage": "repair", "path": str(folder)})
        data["outcome"] = {"state": "submitted", "stage": "repair", "reason": None}
        persist(args.records, data, args.db)
        try:
            source_path = artifacts.verify(prior["artifact"])
            artifacts.check_protections(source_path, prior["protections"])
            package = store.get(data["profile_package"], "profile_package")
            # Previous candidate is the input source; the original request/intent is unchanged.
            current_source = {"artifact": prior["artifact"], "context": prior["context"],
                              "protections": prior["protections"]}
            evidence = {"evaluation": evaluation["id"], "outcome": evaluation["outcome"],
                        "correctness": evaluation["correctness"], "logs": []}
            for stage in evaluation["stages"]:
                if stage.get("log") and Path(stage["log"]).is_file():
                    log = Path(stage["log"])
                    if stage.get("log_sha256") and artifacts.file_hash(log) != stage["log_sha256"]:
                        raise Failure("repair diagnostic log differs from its retained identity")
                    evidence["logs"].append({"stage": stage["stage"], "text": log.read_text(errors="replace")[-32000:]})
            response, meta = rewrite.call(config, data["request"], current_source, package, store,
                                          folder / "provider", repair=evidence, remaining_s=seconds)
            budget["used_seconds"] += meta["host_wall_s"]
            _provider_receipt(data, meta, folder / "provider")
            attempt.update(interpretation=rewrite.response_record(config, response), provider=meta)
            if response["unresolved"]:
                reason = "unresolved repair requirements: " + "; ".join(response["unresolved"])
                attempt.update(state="unresolved", reason=reason)
                data["outcome"] = {"state": "unresolved", "stage": "repair", "reason": reason}
                return persist(args.records, data, args.db)
            if not response["interpretation"].strip() or not rewrite.response_has_edits(config, response):
                raise Failure("repair must explain its interpretation and produce actual code edits")
            patch = rewrite.response_patch(config, response, source_path,
                                           data["request"]["constraints"]["editable_files"],
                                           prior["protections"], folder / "full-files")
            candidate_source = _source_destination(args.runs_dir, f"{proposal_id}.repair-{number}")
            artifact = apply_patch(source_path, candidate_source, patch,
                                   data["request"]["constraints"]["editable_files"], prior["protections"])
            rewrite.require_code_change(source_path, candidate_source)
            artifacts.verify(prior["artifact"])
            diff = folder / "candidate.diff"
            diff.write_text(patch)
            candidate = record("candidate", f"{proposal_id}.candidate-{number+1}", producer=data["producer"],
                proposal=proposal_id, implementation=prior["implementation"], source_snapshot=prior["source_snapshot"],
                artifact=artifact, diff=str(diff), diff_sha256=artifacts.file_hash(diff), state="unverified",
                protections=prior["protections"], context=prior["context"], parent_candidate=prior["id"])
            persist(args.records, candidate, args.db, create=True)
            data["candidate"] = candidate["id"]
            attempt.update(state="completed", candidate=candidate["id"])
            data["outcome"] = {"state": "candidate_created", "stage": "repair", "reason": None}
        except (Failure, OSError, ValueError, subprocess.SubprocessError) as exc:
            if isinstance(exc, Failure) and "persisted, but query indexing failed" in str(exc):
                raise
            metadata = folder / "provider" / "provider.json"
            if metadata.is_file() and "provider" not in attempt:
                meta = json.loads(metadata.read_text())
                budget["used_seconds"] += meta.get("host_wall_s", 0)
                attempt["provider"] = meta
                _provider_receipt(data, meta, folder / "provider")
            unavailable = isinstance(exc, rewrite.provider_adapters.ProviderUnavailable)
            if unavailable:
                budget["repairs"] -= 1
            state = "provider_unavailable" if unavailable else "failed"
            attempt.update(state=state, reason=str(exc))
            data["outcome"] = {"state": state, "stage": "repair", "reason": str(exc)}
        return persist(args.records, data, args.db)


def _retry_initial_provider(args, store, proposal):
    """Retry an unavailable first session using the retained immutable request.

    An initial usage-limit outcome has no evaluation to name. `repair <proposal>`
    therefore retries this case without consuming the build/correctness budget.
    """
    from swdb import rewrite
    proposal_id = proposal["id"]
    with (Path(args.records) / f".swdb-rewrite.{proposal_id}.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Failure("a repair of this proposal is already running") from None
        store = Store(args.records)
        data = copy.deepcopy(store.get(proposal_id, "proposal"))
        if data.get("candidate") or data["outcome"]["state"] != "provider_unavailable":
            raise Failure("proposal no longer admits an unavailable-provider retry")
        config = rewrite.configuration(args.provider_config)
        rewrite.require_same_provider(data.get("provider"), config)
        budget = data["repair_budget"]
        seconds = min(budget["total_seconds"], config["total_seconds"]) - budget["used_seconds"]
        if seconds <= 0:
            data["outcome"] = {"state": "unresolved", "stage": "retry", "reason": "provider-time budget exhausted"}
            return persist(args.records, data, args.db)
        folder = artifacts.external_directory(args.runs_dir) / f"{proposal_id}.retry-{len(data['attempts'])+1}"
        folder.mkdir(exist_ok=False)
        attempt = {"number": len(data["attempts"])+1, "stage": "interpretation", "state": "running"}
        data["attempts"].append(attempt)
        data["raw_artifacts"].append({"stage": "retry", "path": str(folder)})
        persist(args.records, data, args.db)
        try:
            source = store.get(data["source_snapshot"], "source_snapshot")
            package = store.get(data["profile_package"], "profile_package")
            source_path = artifacts.verify(source["artifact"])
            response, meta = rewrite.call(config, data["request"], source, package, store,
                                          folder / "provider", remaining_s=seconds)
            budget["used_seconds"] += meta["host_wall_s"]
            attempt["provider"] = meta
            _provider_receipt(data, meta, folder / "provider")
            if response["unresolved"]:
                attempt.update(state="unresolved", reason="; ".join(response["unresolved"]))
                data["outcome"] = {"state": "unresolved", "stage": "interpretation", "reason": attempt["reason"]}
                return persist(args.records, data, args.db)
            if not response["interpretation"].strip() or not rewrite.response_has_edits(config, response):
                raise Failure("rewrite interpretation must produce actual edits and explain them")
            data["interpretation"] = rewrite.response_record(config, response)
            patch = rewrite.response_patch(config, response, source_path,
                data["request"]["constraints"]["editable_files"], source["protections"], folder / "full-files")
            candidate_source = _source_destination(args.runs_dir, proposal_id)
            artifact = apply_patch(source_path, candidate_source, patch,
                data["request"]["constraints"]["editable_files"], source["protections"])
            rewrite.require_code_change(source_path, candidate_source)
            artifacts.verify(source["artifact"])
            diff = folder / "candidate.diff"; diff.write_text(patch)
            candidate = record("candidate", f"{proposal_id}.candidate-1", producer=data["producer"], proposal=proposal_id,
                implementation=source["implementation"], source_snapshot=source["id"], artifact=artifact,
                diff=str(diff), diff_sha256=artifacts.file_hash(diff), state="unverified",
                protections=source["protections"], context=source["context"])
            persist(args.records, candidate, args.db, create=True)
            data["candidate"] = candidate["id"]
            attempt.update(stage="rewriting", state="completed", candidate=candidate["id"])
            data["outcome"] = {"state": "candidate_created", "stage": "rewriting", "reason": None}
        except (Failure, OSError, ValueError, subprocess.SubprocessError) as exc:
            if isinstance(exc, Failure) and "persisted, but query indexing failed" in str(exc):
                raise
            metadata = folder / "provider" / "provider.json"
            if metadata.is_file() and "provider" not in attempt:
                meta = json.loads(metadata.read_text()); attempt["provider"] = meta
                _provider_receipt(data, meta, folder / "provider")
                budget["used_seconds"] += meta.get("host_wall_s", 0)
            state = "provider_unavailable" if isinstance(exc, rewrite.provider_adapters.ProviderUnavailable) else "failed"
            attempt.update(state=state, reason=str(exc))
            data["outcome"] = {"state": state, "stage": "retry", "reason": str(exc)}
        return persist(args.records, data, args.db)


def _provider_receipt(data, meta, folder):
    """Bind the resolved record block to its retained per-attempt receipt."""
    runtime = {key: meta[key] for key in
        ("resolved_kind", "model", "effort", "cli_version", "workspace", "guard_policy", "audit") if key in meta}
    actual_config = copy.deepcopy(meta.get("provider", data["provider"]))
    data["provider"].update(runtime)
    actual_config.update(runtime)
    meta["provider"] = actual_config
    (Path(folder) / "provider.json").write_text(json.dumps(meta, indent=2))
