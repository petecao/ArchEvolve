"""`swdb campaign-export CAMPAIGN_FILE`: copy candidate artifacts and team claims from an Extensa campaign's
record store into the team store. Created 2026-10-05 ET (ticket 80, spec review C17). Original SWDB code.

The spec's "Records" rule: an Extensa campaign's records stay in its own store on mbit10; only the summary,
promoted candidate artifacts and team claims with their evidence are copied into the team store, tags kept.
The summary is copied when the campaign stops (D6). Ticket 75 imported native a8's best and its proposal by
hand; this command does that step for any candidate artifact the campaign summary lists:

- the closure of each named candidate artifact: the candidate, its proposal, every certification bound to it,
  every evaluation of it (timed, companion, aggregate), every comparison or evaluation pair that cites one of
  them, the retention records of those evaluations, and every record they reference (protocols, baselines,
  workloads; team inputs that are already in the team store byte for byte are left alone);
- every team claim recorded in the campaign store that cites a record of that closure, with its own closure
  (with `--claims`, every team claim of the campaign).

Each file is copied byte for byte (tags kept): the sha256 of the source bytes is taken before the copy and
checked on the written file. A record already in the team store must be byte-identical; any difference refuses
the whole export and nothing is written. The team store is validated with the new records before anything is
written. A rejected (certification failed) candidate artifact is never exported, since it is never promoted.

Exporting is the step before `swdb promote`: the team boundary (`swdb.extensa_boundary`) keeps refusing the
exported records in team results until Yan-Ru's review promotes the candidate artifact and its team
re-evaluation exists. Raw run output is not copied (records name it by path on the campaign's host).
"""
from __future__ import annotations

import json
from pathlib import Path

from swdb import artifacts
from swdb.cli import Failure, UsageError

FORMAT = "swdb.campaign-export.v1"
#: Record kinds found by looking backward from the candidate's evaluations (records that cite them).
CITING_KINDS = ("comparison_result", "evaluation_pair", "certification")


def _campaign_store(campaign_file, runs_root):
    from swdb.campaign import load_campaign
    data, _sha = load_campaign(campaign_file)
    root = Path(runs_root or data["runs_root"])
    store_dir = root / "extensa" / data["id"] / "records"
    if not store_dir.is_dir():
        raise UsageError(f"campaign record store not found: {store_dir}")
    return data, store_dir


def _cites(store, record, ids):
    """True when the record references any of `ids` (one hop)."""
    from swdb.extensa_boundary import _references
    return bool(_references(store, record.data) & ids)


def candidate_roots(store, candidate_id):
    """The candidate, its certifications and evaluations, and the records that cite those evaluations."""
    evaluations = {r.id for r in store.of_kind("evaluation") if r.data.get("candidate") == candidate_id}
    # An aggregate whose components are this candidate's runs belongs to it too.
    evaluations |= {r.id for r in store.of_kind("evaluation")
                    if any(c.get("evaluation") in evaluations for c in r.data.get("component_evaluations") or [])}
    roots = {candidate_id} | evaluations
    for kind in CITING_KINDS:
        roots |= {r.id for r in store.of_kind(kind) if _cites(store, r, {candidate_id} | evaluations)}
    return roots


def plan(store, campaign_id, candidates=(), all_claims=False):
    """The record IDs to export and why, from the campaign store alone (no writes)."""
    from swdb.extensa_boundary import certification_level, closure, tagged
    summary = store.get(f"{campaign_id}.summary", "campaign_summary")
    if summary is None:
        raise Failure(f"campaign {campaign_id} has no campaign_summary yet; export after the campaign stops")
    listed = {c.get("id") for it in summary.get("iterations", []) for c in it.get("candidates", []) if c.get("id")}
    roots, reasons = set(), {}
    for cid in candidates:
        record = store.get(cid, "candidate")
        if record is None or not tagged(record) or record.get("campaign") != campaign_id:
            raise Failure(f"{cid} is not a candidate artifact of Extensa campaign {campaign_id}")
        if cid not in listed:
            raise Failure(f"{cid} is not listed in the campaign summary {campaign_id}.summary")
        level = certification_level(store, cid)["level"]
        if level == "rejected":
            raise Failure(f"{cid} failed certification; a rejected candidate artifact is never promoted or exported")
        found = candidate_roots(store, cid)
        roots |= found
        reasons[cid] = level
    reached = closure(store, sorted(roots))
    claims = [r for r in store.of_kind("team_claim") if r.data.get("action") == "claim"
              and (all_claims or set(r.data.get("records") or []) & reached)]
    claim_ids = sorted(r.id for r in claims)
    reached = closure(store, sorted(reached | set(claim_ids)))
    evaluations = {rid for rid in reached if store.get(rid, "evaluation") is not None}
    retentions = {r.id for r in store.of_kind("retention") if r.data.get("evaluation") in evaluations}
    reached = closure(store, sorted(reached | retentions))
    return {"records": sorted(reached), "candidates": reasons, "claims": claim_ids}


def export(campaign_file, team, *, runs_root=None, candidates=(), all_claims=False, dry_run=False):
    """Copy the planned records byte for byte into the team store (see the module docstring)."""
    from swdb import writer
    from swdb.cli import _require_valid
    from swdb.store import Record, Store
    from swdb.validate import _validate_store
    from swdb import yamlio
    if not candidates and not all_claims:
        raise UsageError("name at least one --candidate, or --claims")
    campaign, store_dir = _campaign_store(campaign_file, runs_root)
    cid = campaign["id"]
    source = _require_valid(store_dir)
    planned = plan(source, cid, candidates, all_claims)
    team = Path(team)
    rows, extra, writes = [], [], []
    with writer._locked(team):
        target = Store(team)
        for rid in planned["records"]:
            record = source.by_id[rid]
            path = store_dir / record.rel
            raw = path.read_bytes()
            digest = artifacts.file_hash(path)
            row = {"id": rid, "kind": record.kind, "path": record.rel, "sha256": digest,
                   "mode": record.data.get("mode"), "campaign": record.data.get("campaign")}
            present = target.by_id.get(rid)
            if present is not None:
                existing = team / present.rel
                if present.rel != record.rel or artifacts.file_hash(existing) != digest:
                    raise Failure(f"{rid} is already in the team store with other bytes ({present.rel}); "
                                  "nothing written")
                rows.append({**row, "action": "present"})
                continue
            if (team / record.rel).exists():
                raise Failure(f"{record.rel} already exists in the team store; nothing written")
            data = yamlio.load(path)
            if data != record.data:
                raise Failure(f"{record.rel} changed while the export read it; nothing written")
            extra.append(Record(record.rel, data))
            writes.append((record.rel, raw, digest))
            rows.append({**row, "action": "would_copy" if dry_run else "copied"})
        if extra:
            result = _validate_store(target, extra=extra)
            if result.problems:
                details = "\n".join(str(p) for p in result.problems)
                raise Failure(f"the team store would not validate; nothing written:\n{details}")
        if not dry_run:
            for rel, raw, digest in writes:
                destination = team / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                tmp = destination.with_suffix(destination.suffix + ".tmp")
                tmp.write_bytes(raw)
                if artifacts.file_hash(tmp) != digest:
                    tmp.unlink()
                    raise Failure(f"{rel}: the written bytes differ from the campaign store's (sha256); stopped")
                tmp.replace(destination)
                if artifacts.file_hash(destination) != digest:
                    raise Failure(f"{rel}: sha256 changed after the copy; stopped")
    from swdb.extensa_boundary import promotion
    promoted = {}
    if not dry_run:
        after = Store(team)
        for rid in planned["candidates"]:
            review = promotion(after, rid)
            promoted[rid] = review["id"] if review else None
    out = {"format": FORMAT, "campaign": cid, "campaign_store": str(store_dir), "team_store": str(team),
           "dry_run": bool(dry_run), "candidates": [{"id": rid, "level": level, "promotion": promoted.get(rid)}
                                                     for rid, level in sorted(planned["candidates"].items())],
           "claims": planned["claims"], "records": rows,
           "copied": sum(r["action"] == "copied" for r in rows), "present": sum(r["action"] == "present" for r in rows)}
    if not dry_run and writes:
        # A receipt beside the campaign store (outside the record folder): what was copied, with sha256s.
        import time
        import uuid
        receipts = store_dir.parent / "exports"
        receipts.mkdir(parents=True, exist_ok=True)
        name = f"export-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8]}.json"
        (receipts / name).write_text(json.dumps(out, indent=2) + "\n")
        out["receipt"] = str(receipts / name)
    return out


def run_cli(args):
    return export(args.file, args.records, runs_root=args.runs_root, candidates=args.candidate or (),
                  all_claims=args.claims, dry_run=args.dry_run)


def register_cli(commands, paths_module):
    sub = commands.add_parser(
        "campaign-export", help="copy an Extensa campaign's candidate artifacts and team claims to the team store",
        description="copy each named candidate artifact's record closure (candidate, proposal, certifications, "
                    "evaluations, comparisons, retention records) and the team claims citing it from the Extensa "
                    "campaign's record store into the team store, byte for byte with sha256 checks, tags kept "
                    "(ticket 80)")
    sub.add_argument("file", type=Path, help="the Extensa campaign file")
    sub.add_argument("--records", type=Path, default=paths_module.RECORDS, help="the team record store")
    sub.add_argument("--runs-root", type=Path, default=None, help="override the campaign file's runs_root")
    sub.add_argument("--candidate", action="append", help="a candidate artifact listed in the campaign summary")
    sub.add_argument("--claims", action="store_true", help="also export every team claim of the campaign")
    sub.add_argument("--dry-run", action="store_true", help="list what would be copied; write nothing")
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(extensa_handler=run_cli)
