"""Extensa mode tags, the team boundary and candidate-artifact promotion.

Created: 2026-10-03 ET (ticket 48). Original SWDB code, not ported from Extensa.

Records an Extensa campaign writes carry `mode: extensa` and `campaign`, set at
creation (the writer refuses any later change). Team commands (comparisons,
handoffs, coverage) refuse such records unless Yan-Ru's review promotes the
candidate artifact they belong to, and, except for the re-evaluation comparison
itself, until a comparison under the derived team protocol exists. A campaign's
own comparisons (an Extensa protocol) accept only records of that campaign.

The certification level of a candidate artifact is never stored on the candidate
record: `certification_level` derives it from certification records.
"""

import copy
import datetime
import hashlib
import json
import uuid
from argparse import Namespace
from pathlib import Path

from swdb import artifacts, writer, yamlio
from swdb.cli import Failure, UsageError
from swdb.problems import Problem

MODE = "extensa"
OWNED_KINDS = {"candidate", "proposal", "source_snapshot"}


def tagged(data):
    return isinstance(data, dict) and data.get("mode") == MODE


# --- certification level ---------------------------------------------------------

def certification_level(store, candidate_id):
    """`certified`, `uncertified` or `rejected`, derived from certification records.

    A failed certification of the candidate derives `rejected` (it is never merely
    uncertified). No certification record at all (an edit that used no contract)
    derives `uncertified`.
    """
    candidate = store.get(candidate_id, "candidate")
    if candidate is None:
        raise Failure(f"candidate {candidate_id!r} does not exist")
    sha = candidate.get("artifact", {}).get("sha256")
    verdicts = []
    for record in store.of_kind("certification"):
        bound = record.data.get("candidate") or {}
        if bound.get("id") != candidate_id:
            continue
        if bound.get("tree_sha256") not in {None, sha}:
            continue
        verdicts.append((record.id, record.data.get("verdict")))
    if any(verdict == "failed" for _, verdict in verdicts):
        level = "rejected"
    elif any(verdict == "certified" for _, verdict in verdicts):
        level = "certified"
    else:
        level = "uncertified"
    return {"candidate": candidate_id, "level": level,
            "certifications": [rid for rid, _ in verdicts],
            "mode": candidate.get("mode"), "campaign": candidate.get("campaign")}


# --- promotion state -------------------------------------------------------------

def _authorized(name):
    from swdb.library import authorized_reviewer
    return authorized_reviewer(name)


def promotion(store, candidate_id):
    """Yan-Ru's current candidate review, or None."""
    candidate = store.get(candidate_id, "candidate")
    if candidate is None:
        return None
    sha = candidate.get("artifact", {}).get("sha256")
    found = [r.data for r in store.of_kind("review")
             if r.data.get("target_kind") == "candidate"
             and r.data.get("target") == {"id": candidate_id, "content_sha256": sha}
             and _authorized(r.data.get("reviewer"))]
    return sorted(found, key=lambda r: r.get("reviewed_at", ""))[-1] if found else None


def reevaluation_comparisons(store, candidate_id, review=None):
    review = review or promotion(store, candidate_id)
    if review is None:
        return []
    protocol = review["reevaluation"]["protocol"]
    found = []
    for record in store.of_kind("comparison_result"):
        data = record.data
        if data.get("protocol") != protocol or tagged(data):
            continue
        if data.get("decision", {}).get("state") in {None, "rejected"}:
            continue
        evaluation = store.get(data.get("candidate_evaluation"), "evaluation") or {}
        if evaluation.get("candidate") == candidate_id:
            found.append(record.id)
    return sorted(found)


# --- closure and refusal ---------------------------------------------------------

def _references(store, data):
    found = set()

    def walk(value):
        if isinstance(value, str):
            if value in store.by_id:
                found.add(value)
        elif isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk({k: v for k, v in data.items() if k not in {"id", "kind"}})
    return found


def closure(store, ids):
    """Every record reachable from `ids` through ID references (the records themselves included)."""
    seen, pending = set(), [rid for rid in ids if rid in store.by_id]
    while pending:
        rid = pending.pop()
        if rid in seen:
            continue
        seen.add(rid)
        pending.extend(_references(store, store.by_id[rid].data) - seen)
    return seen


def _owners(store, record):
    data = record.data
    if record.kind == "candidate":
        return [record.id]
    if record.kind not in OWNED_KINDS:
        return []
    field = "proposal" if record.kind == "proposal" else "source_snapshot"
    return [c.id for c in store.of_kind("candidate") if c.data.get(field) == record.id]


def refusal(store, ids, *, command, protocol=None):
    """A reason naming the first refused Extensa record, or None."""
    if not any(tagged(r.data) for r in store.records):
        return None
    protocol_data = store.get(protocol, "protocol") if protocol else None
    reached = closure(store, list(ids) + ([protocol] if protocol else []))
    if tagged(protocol_data):
        campaign = protocol_data.get("campaign")
        for rid in sorted(reached):
            data = store.by_id[rid].data
            if tagged(data) and data.get("campaign") != campaign:
                return (f"{command} refuses Extensa record {rid} (campaign {data.get('campaign')}): "
                        f"protocol {protocol} belongs to campaign {campaign}")
        return None
    for rid in sorted(reached):
        record = store.by_id[rid]
        if not tagged(record.data):
            continue
        where = f"Extensa record {rid} (campaign {record.data.get('campaign')})"
        owners = _owners(store, record)
        if not owners:
            return (f"{command} refuses {where}: campaign {record.kind} records never enter team results; "
                    "promote the candidate artifact and use its team re-evaluation")
        reviews = {owner: promotion(store, owner) for owner in owners}
        promoted = {owner: review for owner, review in reviews.items() if review}
        if not promoted:
            return f"{command} refuses {where}: its candidate artifact is not promoted by a review record"
        accepted = any(reevaluation_comparisons(store, owner, review)
                       or (protocol and protocol == review["reevaluation"]["protocol"])
                       for owner, review in promoted.items())
        if not accepted:
            return (f"{command} refuses {where}: promoted, but its team re-evaluation comparison under "
                    f"{sorted(r['reevaluation']['protocol'] for r in promoted.values())[0]} does not exist yet")
    return None


def require_team_inputs(store, ids, *, command, protocol=None):
    reason = refusal(store, ids, command=command, protocol=protocol)
    if reason:
        raise Failure(reason)


class TeamFilter:
    """Memoized skip test for scans over a team store (coverage reports)."""

    def __init__(self, store, command):
        self.store, self.command, self._cache = store, command, {}
        self._any = any(tagged(r.data) for r in store.records)

    def refused(self, rid):
        if not self._any:
            return None
        if rid not in self._cache:
            self._cache[rid] = refusal(self.store, [rid], command=self.command)
        return self._cache[rid]

    def team_store(self):
        """The same store without refused records (a snapshot; never written back)."""
        if not self._any:
            return self.store
        from swdb.store import Store
        return Store(self.store.dir, indexed_records=[r for r in self.store.records if not self.refused(r.id)])


# --- validation of candidate reviews ---------------------------------------------

def validate_review(record, ctx):
    data, rel = record.data, record.rel
    store = ctx.store
    target = data["target"]
    candidate = store.get(target["id"], "candidate")
    if candidate is None:
        yield Problem(rel, "target.id", "candidate review targets an unknown candidate artifact")
        return
    if not tagged(candidate):
        yield Problem(rel, "target.id", "only Extensa candidate artifacts are promoted by review")
    if candidate.get("campaign") != data["origin"]["campaign"]:
        yield Problem(rel, "origin.campaign", "review origin differs from the candidate's campaign")
    if candidate.get("artifact", {}).get("sha256") != target["content_sha256"]:
        yield Problem(rel, "target.content_sha256", "review is not bound to the candidate artifact sha256")
    if not _authorized(data.get("reviewer")):
        yield Problem(rel, "reviewer", "candidate promotion requires Yan-Ru Jhou's review")
    for index, rid in enumerate(data["evidence"]):
        evidence = store.get(rid)
        if evidence is None:
            yield Problem(rel, f"evidence[{index}]", f"evidence {rid!r} does not exist")
        elif evidence.get("kind") == "certification":
            if (evidence.get("candidate") or {}).get("id") != target["id"]:
                yield Problem(rel, f"evidence[{index}]", "certification evidence belongs to another candidate")
        elif evidence.get("kind") == "campaign_summary":
            if evidence.get("campaign") != data["origin"]["campaign"]:
                yield Problem(rel, f"evidence[{index}]", "campaign summary belongs to another campaign")
        else:
            yield Problem(rel, f"evidence[{index}]", "evidence must be a certification or campaign summary record")
    reevaluation = data["reevaluation"]
    derived = store.get(reevaluation["protocol"], "protocol")
    team = store.get(reevaluation["team_protocol"], "protocol")
    if derived and tagged(derived) or team and tagged(team):
        yield Problem(rel, "reevaluation", "re-evaluation protocols are team protocols, never Extensa protocols")
    if derived and sorted(derived.get("settings", {}).get("workloads", [])) != sorted(reevaluation["workloads"]):
        yield Problem(rel, "reevaluation.workloads", "derived protocol workloads differ from the recorded class")


# --- swdb promote CANDIDATE ------------------------------------------------------

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _short(text):
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def promote_candidate(args):
    """Record Yan-Ru's review of an Extensa candidate artifact and derive its team re-evaluation.

    The derived protocol copies the named current team protocol and keeps only the
    workloads of the artifact's workload class. One evaluation request per workload is
    written to --output; each cites the Extensa campaign as its origin.
    """
    from swdb import bfs_protocol
    from swdb.cli import _require_valid

    if not _authorized(args.reviewer):
        raise Failure("candidate promotion requires the designated reviewer Yan-Ru Jhou")
    if not args.protocol or not args.workload_class or not args.output:
        raise UsageError("candidate promotion requires --protocol, --workload-class and --output")
    store = _require_valid(args.records)
    candidate = store.get(args.id, "candidate")
    if not tagged(candidate):
        raise Failure(f"{args.id} is not an Extensa candidate artifact; ArchEvolve candidates need no promotion")
    level = certification_level(store, args.id)["level"]
    if level == "rejected":
        raise Failure(f"{args.id} failed certification; a rejected candidate artifact is never promoted")
    team = store.get(args.protocol, "protocol")
    if team is None:
        raise Failure(f"protocol {args.protocol!r} does not exist")
    if tagged(team):
        raise Failure(f"{args.protocol} is an Extensa protocol; name the current team protocol")
    workloads = [wid for wid in team["settings"]["workloads"]
                 if (store.get(wid, "workload") or {}).get("definition", {}).get("family") == args.workload_class]
    if not workloads:
        raise Failure(f"team protocol {args.protocol} has no workload of class {args.workload_class!r}")
    evidence = [r.id for r in store.of_kind("certification")
                if (r.data.get("candidate") or {}).get("id") == args.id and r.data.get("verdict") == "certified"]
    evidence += [r.id for r in store.of_kind("campaign_summary") if r.data.get("campaign") == candidate["campaign"]]
    if not evidence:
        raise Failure("candidate promotion requires its certification record or its campaign summary in the team store")

    settings = copy.deepcopy(team["settings"])
    settings["workloads"] = workloads
    differences = settings.setdefault("differences", {}).setdefault("software", [])
    differences.append(f"Team re-evaluation of Extensa candidate artifact {args.id} "
                       f"(campaign {candidate['campaign']}), workload class {args.workload_class} only.")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    request_id = f"{team['requested_id']}-reeval-{args.workload_class.replace('_', '-')}-{_short(args.id)}"
    freeze_file = output / f"{request_id}.freeze.yaml"
    freeze_file.write_text(yamlio.dumps({"message_version": "1.0", "id": request_id, "version": 1,
                                         "settings": settings}))
    derived = bfs_protocol.freeze_protocol(Namespace(file=freeze_file, records=args.records,
                                                     db=getattr(args, "db", None)))
    review_id = f"review.{args.id}.{uuid.uuid4().hex[:12]}"
    origin = {"mode": MODE, "campaign": candidate["campaign"]}
    requests = []
    for wid in workloads:
        workload = store.get(wid, "workload")
        request = {"message_version": "1.0", "id": f"reeval-{_short(args.id + wid)}-{uuid.uuid4().hex[:8]}",
                   "candidate": args.id, "protocol": derived["id"], "protocol_role": "candidate",
                   "workload": {"id": wid}, "sources": workload["definition"]["sources"],
                   "threads": settings["threads"], "repetitions": settings["sampling"]["repetitions"],
                   "roi": settings["roi"],
                   "origin": {**origin, "candidate": args.id, "review": review_id,
                              "team_protocol": team["id"]}}
        file = output / f"{request['id']}.yaml"
        file.write_text(yamlio.dumps(request))
        requests.append({"id": request["id"], "sha256": artifacts.file_hash(file), "path": str(file)})
    record = {"kind": "review", "schema_version": "0.4", "id": review_id, "status": "reviewed",
              "created": writer.today(), "updated": writer.today(),
              "provenance": [{"id": "review", "kind": "human_report",
                              "description": f"Candidate review recorded by {args.reviewer} through swdb promote.",
                              "uri": None}],
              "target_kind": "candidate",
              "target": {"id": args.id, "content_sha256": candidate["artifact"]["sha256"]},
              "reviewer": "Yan-Ru Jhou", "reviewed_at": _now(), "evidence": sorted(evidence),
              "origin": origin,
              "reevaluation": {"team_protocol": team["id"], "protocol": derived["id"],
                               "workload_class": args.workload_class, "workloads": workloads,
                               "requests": [{"id": r["id"], "sha256": r["sha256"]} for r in requests]}}
    writer.commit(args.records, new=[record])
    return {"review": record, "derived_protocol": derived["id"], "requests": requests,
            "level": level}


def level_cli(args):
    from swdb.cli import _require_valid
    return certification_level(_require_valid(args.records), args.candidate)


def register_cli(commands, paths):
    sub = commands.add_parser("candidate-level", help="derive a candidate artifact's certification level",
                              description="derive a candidate artifact's certification level "
                                          "(certified, uncertified or rejected) from certification records")
    sub.add_argument("candidate")
    sub.add_argument("--records", type=Path, default=paths.RECORDS)
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(extensa_handler=level_cli)
    from swdb import library_operations
    library_operations.register_cli(commands, paths)
