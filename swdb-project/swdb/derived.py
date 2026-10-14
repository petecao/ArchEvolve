"""Derived implementations: the result of a certified enabling rewrite (Probata PoC ticket 19).

Created: 2026-10-14 ET. Design: the formal-verification map, decision 17 items 5-8 (enabling rewrites),
24 item 3 and 26 item 2; ADR 0005 (the root baseline stays the comparator) and ADR 0016 (records never
change; what still holds is computed on read).

A certified candidate artifact whose every contract is an enabling contract (none of its strategy effects
offloads) is recorded as an implementation with `origin.kind: derived`, `origin.derived_from` its
predecessor, `applies` its predecessor's strategies then its contracts' strategies, `contract_lineage`
(every rewrite contract applied since the baseline implementation) and `rewrite_links` (per contract: the
contract hash, predecessor snapshot hash, result hash and certification record its verdict holds for).
Its code is the candidate artifact's tree, recorded as its own source snapshot; from then on proposals and
the site finder treat it like any implementation. It lives in the store that certified it (the research
database side) until promotion, which is not built here.

On read (`swdb build`), each link either still matches (its contract, predecessor snapshot and result
hashes are current and every earlier link of the chain matches) or names why not, and shows the proof
route of the rewrite's proof record ("none yet" without one). No record is ever rewritten for that.
"""
from __future__ import annotations

import copy
import hashlib
import shutil
from pathlib import Path

from swdb import access, artifacts
from swdb.cli import Failure
from swdb.problems import Problem

#: A target or parameter value of a derived implementation's `applies` entry that only the profiling
#: agent's annotation of the derived implementation can name (Probata PoC 52 checks pattern classes).
UNRESOLVED = "unresolved"
NO_ROUTE = "none yet"
SUFFIX = ".derived"


# --- enabling contracts -------------------------------------------------------------------------

def is_enabling(library, stores, contract_id):
    """True when the rewrite contract exists and none of its strategies' effects offloads.

    Strategy records are read from the first of `stores` that has them; a contract whose strategy
    records no store has is not known to be enabling (False)."""
    entry = library.get(contract_id) if library is not None else None
    if not entry or entry.get("kind") != "rewrite_contract":
        return False
    for sid in entry.get("strategies") or []:
        strategy = next((s.get(sid, "strategy") for s in stores if s.get(sid, "strategy") is not None), None)
        if strategy is None:
            return False
        if any(effect.get("kind") == "offload" for effect in strategy.get("effect") or []):
            return False
    return True


def is_derived(data):
    return isinstance(data, dict) and (data.get("origin") or {}).get("kind") == "derived"


def snapshot_of(impl):
    """The source snapshot ID of a derived implementation's code (its rewrite's result), or None."""
    links = (impl or {}).get("rewrite_links") or []
    return links[0]["result"]["snapshot"] if links else None


def certification_problem(store, impl, library=None):
    """Why a derived implementation does not count as certified (a phrase), or None.

    Every rewrite link needs its certification record, certified, still counting for the result
    candidate artifact (current contract content, newest command version)."""
    from swdb.extensa_boundary import candidate_certifications
    links = impl.get("rewrite_links") or []
    if not links:
        return "has no certification record"
    for link in links:
        cert = store.get(link["certification"], "certification")
        if cert is None:
            return f"has no certification record {link['certification']}"
        if cert.get("verdict") != "certified":
            return f"has certification {cert['id']} with verdict {cert.get('verdict')}"
        try:
            _bound, counted = candidate_certifications(store, link["result"]["candidate"], library)
        except Failure:
            return f"has no result candidate artifact {link['result']['candidate']}"
        if cert["id"] not in {r["id"] for r in counted}:
            return f"has certification {cert['id']}, which no longer counts"
    return None


def start_problem(store, start, *, kernel, listed, library=None):
    """Why an Extensa iteration may not start from `start`, or None (decision 17 item 8)."""
    if start not in listed:
        return f"start {start} is not one of the campaign file's derived_starts"
    impl = store.get(start, "implementation")
    if impl is None:
        return f"start {start} is not an implementation in the campaign's records"
    if not is_derived(impl):
        return f"start {start} is not a derived implementation"
    if impl.get("kernel") != kernel:
        return f"start {start} implements kernel {impl.get('kernel')}, not the campaign's kernel {kernel}"
    problem = certification_problem(store, impl, library)
    if problem:
        return f"start {start} is not a certified derived implementation: it {problem}"
    if store.get(snapshot_of(impl), "source_snapshot") is None:
        return f"start {start} has no source snapshot in the campaign's records"
    return None


# --- the record ---------------------------------------------------------------------------------

def _kernel_file(pred):
    """The predecessor's kernel file (code[0]) as a path inside the application's source tree."""
    code = pred["code"][0]
    if code["root"] == "application":
        return code["path"]
    prefix = f"implementations/{pred['id']}/"
    if is_derived(pred) and code["path"].startswith(prefix):
        return code["path"][len(prefix):]
    raise Failure(f"predecessor {pred['id']} has no kernel file inside its application's source tree")


def _description(pred):
    """Loops and access patterns copied from the predecessor; claims about its code are dropped.

    The profiling agent annotates the derived implementation like any implementation (decision 17
    item 5); until then its description is the predecessor's, without code lines or agent claims."""
    loops = []
    for loop in pred["loops"]:
        loop = copy.deepcopy(loop)
        loop.pop("code", None)
        loops.append(loop)
    patterns = []
    for pattern in pred["access_patterns"]:
        pattern = copy.deepcopy(pattern)
        pattern.pop("agent_claims", None)
        pattern.pop("annotation_facts", None)
        patterns.append(pattern)
    return loops, patterns


def _applies(store, library, contracts, knobs):
    rows = []
    for cid in contracts:
        for sid in library.get(cid).get("strategies") or []:
            strategy = store.get(sid, "strategy")
            target = "input" if strategy["target"] == "input" else UNRESOLVED
            rows.append({"strategy": sid, "target": target,
                         "parameters": {p["name"]: knobs.get(p["name"], UNRESOLVED)
                                        for p in strategy.get("parameters") or []}})
    return rows


def _copy_strategies(store_dir, team_dir, strategy_ids):
    """Copy strategy records the store lacks from the team store (as campaign preparation does)."""
    from swdb.extensa_boundary import closure
    from swdb.store import Store
    store, team = Store(store_dir), Store(team_dir)
    missing = [sid for sid in strategy_ids if store.get(sid, "strategy") is None]
    for rid in sorted(closure(team, missing)):
        record = team.by_id[rid]
        target = Path(store_dir) / record.rel
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            access.copy_record(Path(team_dir) / record.rel, target)


def record(store_dir, *, candidate_id, contracts, links, predecessor_snapshot, library, knobs=None,
           team_dir=None):
    """Write the derived implementation of a certified enabling candidate artifact and its snapshot.

    `links` are the candidate's certification links (one `{contract, record}` per contract, ticket 02).
    Returns the derived implementation's ID. Recording the same candidate again returns the same ID."""
    from swdb import db, workflow, writer
    from swdb.store import Store
    store_dir = Path(store_dir)
    store = Store(store_dir)
    rid = candidate_id + SUFFIX
    if store.get(rid) is not None:
        return rid
    candidate = store.get(candidate_id, "candidate")
    snapshot = store.get(predecessor_snapshot, "source_snapshot")
    if candidate is None or snapshot is None:
        raise Failure(f"derived implementation {rid}: candidate or predecessor snapshot is missing")
    pred = store.get(snapshot["implementation"], "implementation")
    if pred is None or pred.get("schema_version") != "0.4":
        raise Failure(f"derived implementation {rid}: predecessor {snapshot['implementation']} "
                      "lacks an explicit (format 0.4) source context")
    by_contract = {link.get("contract"): link.get("record") for link in links}
    if [c for c in contracts if not by_contract.get(c)]:
        raise Failure(f"derived implementation {rid}: a contract has no certification record")
    if team_dir is not None:
        _copy_strategies(store_dir, team_dir, [s for c in contracts for s in library.get(c).get("strategies") or []])
        store = Store(store_dir)
    tree = artifacts.verify(candidate["artifact"])
    result_sha = candidate["artifact"]["sha256"]
    kernel_file = _kernel_file(pred)
    source = tree / kernel_file
    if not source.is_file():
        raise Failure(f"derived implementation {rid}: the result has no {kernel_file}")
    artifacts.check_protections(tree, snapshot["protections"])
    code_rel = f"implementations/{rid}/{kernel_file}"
    sid = f"{rid}.source"
    loops, patterns = _description(pred)
    today = writer.today()
    impl = {
        "kind": "implementation", "schema_version": "0.4", "id": rid, "status": "draft",
        "created": today, "updated": today,
        "provenance": copy.deepcopy(pred["provenance"]) + [{
            "id": f"derivation-{len(pred.get('contract_lineage') or []) + 1}", "kind": "agent_run", "uri": None,
            "description": (f"Recorded by swdb when candidate artifact {candidate_id} passed certification of "
                            f"enabling contract(s) {', '.join(contracts)} (Probata PoC 19).")}],
        **workflow.CREATION_TAGS,
        "name": f"{pred['name']} after {', '.join(c.removeprefix('contract.') for c in contracts)}",
        "kernel": pred["kernel"], "function": pred["function"],
        "origin": {"kind": "derived", "derived_from": pred["id"],
                   "description": f"Result of the certified enabling rewrite {candidate_id} of {pred['id']}."},
        "application": pred["application"], "source_baseline": pred["source_baseline"],
        **({"comparison_baseline": pred["comparison_baseline"]} if "comparison_baseline" in pred else {}),
        "code": [{"root": "records", "path": code_rel, "sha256": artifacts.file_hash(source)}],
        "build": copy.deepcopy(pred["build"]), "run": copy.deepcopy(pred["run"]),
        "evaluator": copy.deepcopy(pred["evaluator"]),
        "verification": {"status": "unchecked", "evidence": [],
                         "scope": "Certified enabling rewrite; no profile of this derived implementation yet."},
        "loops": loops, "access_patterns": patterns,
        **({"uses_intrinsics": list(pred["uses_intrinsics"])} if pred.get("uses_intrinsics") else {}),
        "applies": copy.deepcopy(pred.get("applies") or []) + _applies(store, library, contracts, knobs or {}),
        "contract_lineage": copy.deepcopy(pred.get("contract_lineage") or []) + [
            {"contract": c, "version": library.get(c).get("version"), "content_sha256": library.content_sha256(c)}
            for c in contracts],
        "rewrite_links": [{"contract": c, "contract_sha256": library.content_sha256(c),
                           "predecessor_snapshot": {"id": snapshot["id"], "sha256": snapshot["artifact"]["sha256"]},
                           "result": {"candidate": candidate_id, "snapshot": sid, "sha256": result_sha},
                           "certification": by_contract[c]} for c in contracts],
        "notes": ["Loops and access patterns are the predecessor's until the profiling agent annotates this "
                  "derived implementation; `unresolved` applies targets and parameters wait for it."],
    }
    text = source.read_text()
    region_hash = hashlib.sha256(text.encode()).hexdigest()
    lines = [1, len(text.splitlines())]
    snap = workflow.record(
        "source_snapshot", sid, implementation=rid, application=pred["application"],
        revision=snapshot["revision"], artifact=copy.deepcopy(candidate["artifact"]),
        context=store.source_context(impl),
        regions=[{"id": f"{kernel_file}:{lines[0]}-{lines[1]}:{region_hash[:16]}", "path": kernel_file,
                  "lines": lines, "source_sha256": region_hash, "text": text,
                  "association": "declared_source_region"}],
        protections=copy.deepcopy(snapshot["protections"]))
    code_path = store_dir / code_rel
    code_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, code_path)
    try:
        writer.commit(store_dir, new=[impl, snap])
    except Failure:
        shutil.rmtree(store_dir / "implementations" / rid, ignore_errors=True)
        raise
    db.build(store_dir, db.default_path(store_dir))
    return rid


# --- `swdb build`: links on read -----------------------------------------------------------------

def _routes(store):
    """{(candidate, contract): route} from proof records of candidate proof units that name a route.

    The route field is defined by ticket 04 and filled by 61 and 62; with several such records, the
    first by ID names the route (62 chooses routes)."""
    routes = {}
    for proof in sorted(store.of_kind("proof"), key=lambda r: r.id):
        data = proof.data
        subject = data.get("subject") or {}
        if subject.get("kind") != "candidate_proof_unit" or not data.get("route"):
            continue
        contract = ((data.get("pins") or {}).get("contract") or {}).get("id")
        routes.setdefault((subject.get("candidate"), contract), data["route"])
    return routes


def _candidate_links(store, candidate):
    """A final candidate artifact's links: one per certified certification record bound to it."""
    sha = candidate["artifact"]["sha256"]
    built_on = candidate["predecessor"]
    rows = []
    for cert in sorted(store.of_kind("certification"), key=lambda r: r.id):
        pin = cert.data.get("candidate") or {}
        if pin.get("id") != candidate["id"] or pin.get("tree_sha256") not in {None, sha}:
            continue
        if cert.data.get("verdict") != "certified":
            continue
        rows.append({"contract": pin.get("contract") or (cert.data.get("entry") or {}).get("id"),
                     "contract_sha256": (cert.data.get("entry") or {}).get("content_sha256"),
                     "predecessor_snapshot": dict(built_on["snapshot"]),
                     "result": {"candidate": candidate["id"], "snapshot": None, "sha256": sha},
                     "certification": cert.id})
    return rows


def link_rows(store, library=None):
    """Every rewrite link of the store, whether it still matches and its proof route (ADR 0016: on read).

    A link matches while its predecessor snapshot, contract (when a library is known) and result hashes
    are current and every earlier link of its chain matches. Subjects are derived implementations and
    candidate artifacts built on one (`predecessor`) that are not themselves a derived implementation's
    result. Proof route: the rewrite's proof record's route, or "none yet"."""
    routes = _routes(store)
    chains = {r.id: r.data for r in store.of_kind("implementation") if r.data.get("rewrite_links")}
    results = {link["result"]["candidate"] for data in chains.values() for link in data["rewrite_links"]}
    holds = {}

    def reasons(link, predecessor):
        found = []
        before = store.get(link["predecessor_snapshot"]["id"], "source_snapshot")
        if before is None or (before.get("artifact") or {}).get("sha256") != link["predecessor_snapshot"]["sha256"]:
            found.append("the predecessor snapshot changed")
        if library is not None:
            if library.get(link["contract"]) is None:
                found.append("the contract is not in the library")
            elif library.content_sha256(link["contract"]) != link["contract_sha256"]:
                found.append("the contract's content changed")
        result = link["result"]
        after = store.get(result["snapshot"], "source_snapshot") if result.get("snapshot") else None
        candidate = store.get(result["candidate"], "candidate")
        if (candidate or {}).get("artifact", {}).get("sha256") != result["sha256"] or (
                result.get("snapshot") and (after or {}).get("artifact", {}).get("sha256") != result["sha256"]):
            found.append("the result changed")
        if predecessor in chains and not still(predecessor):
            found.append("an earlier rewrite of the chain no longer matches")
        return found

    def still(impl_id):
        if impl_id not in holds:
            holds[impl_id] = False               # a cycle never matches (validation refuses one anyway)
            data = chains[impl_id]
            holds[impl_id] = not any(reasons(link, data["origin"].get("derived_from"))
                                     for link in data["rewrite_links"])
        return holds[impl_id]

    subjects = [("derived_implementation", rid, data["origin"].get("derived_from"), data["rewrite_links"])
                for rid, data in sorted(chains.items())]
    subjects += [("candidate", c.id, c.data["predecessor"]["implementation"], _candidate_links(store, c.data))
                 for c in sorted(store.of_kind("candidate"), key=lambda r: r.id)
                 if c.data.get("predecessor") and c.id not in results]
    rows = []
    for kind, subject, predecessor, links in subjects:
        for position, link in enumerate(links):
            why = reasons(link, predecessor)
            rows.append({"subject_kind": kind, "subject": subject, "position": position,
                         "contract": link["contract"], "contract_sha256": link["contract_sha256"],
                         "predecessor": predecessor, "predecessor_snapshot": link["predecessor_snapshot"]["id"],
                         "predecessor_snapshot_sha256": link["predecessor_snapshot"]["sha256"],
                         "result_candidate": link["result"]["candidate"], "result_snapshot": link["result"]["snapshot"],
                         "result_sha256": link["result"]["sha256"], "certification": link["certification"],
                         "proof_route": routes.get((link["result"]["candidate"], link["contract"]), NO_ROUTE),
                         "matches": int(not why), "reason": "; ".join(why) or None})
    return rows


def index(con, store, library_root=None):
    """`swdb build`: the contract lineage and rewrite-link tables (SWDB extension; db.SCHEMA defines them)."""
    from swdb.library import Library
    library = Library(library_root, store) if library_root is not None and Path(library_root).is_dir() else None
    con.executemany("INSERT INTO swdb_contract_lineage VALUES (?,?,?,?,?)",
                    [(r.id, i, e["contract"], e.get("version"), e["content_sha256"])
                     for r in store.of_kind("implementation") for i, e in enumerate(r.data.get("contract_lineage") or [])])
    columns = ("subject_kind", "subject", "position", "contract", "contract_sha256", "predecessor",
               "predecessor_snapshot", "predecessor_snapshot_sha256", "result_candidate", "result_snapshot",
               "result_sha256", "certification", "proof_route", "matches", "reason")
    con.executemany(f"INSERT INTO swdb_rewrite_links VALUES ({','.join('?' * len(columns))})",
                    [tuple(row[c] for c in columns) for row in link_rows(store, library)])


# --- `swdb validate` ----------------------------------------------------------------------------

def validate_implementation(record, ctx):
    """Store rules for an implementation's lineage and rewrite links (run after its schema passed).

    The lineage is the predecessor's lineage, then this rewrite's contracts, in order; a lineage that
    skips, adds or reorders a rewrite is refused. Each link's certification record covers the link's
    contract, certifies the link's result candidate artifact, and that candidate artifact was built on the
    link's predecessor snapshot (a snapshot of the predecessor)."""
    data, rel = record.data, record.rel
    lineage, links = data.get("contract_lineage"), data.get("rewrite_links")
    if lineage is None and links is None:
        return
    if not is_derived(data):
        yield Problem(rel, "origin.kind", "only a derived implementation carries contract_lineage and rewrite_links")
        return
    if lineage is None or links is None:
        yield Problem(rel, "rewrite_links" if links is None else "contract_lineage",
                      "a derived implementation's contract lineage and rewrite links come together")
        return
    pred_id = data["origin"].get("derived_from")
    if pred_id is None:
        yield Problem(rel, "origin.derived_from", "a derived implementation with rewrite links names its predecessor")
    pred = ctx.passed(pred_id, "implementation") if pred_id else None
    if pred is not None:
        expected = [(e["contract"], e["content_sha256"]) for e in pred.get("contract_lineage") or []]
        expected += [(link["contract"], link["contract_sha256"]) for link in links]
        if [(e["contract"], e["content_sha256"]) for e in lineage] != expected:
            yield Problem(rel, "contract_lineage", "skips, adds or reorders a rewrite of the chain: expected "
                          + ", ".join(c for c, _ in expected) + f" (the lineage of {pred_id}, then this rewrite's "
                          "contracts, with the hashes its links certify)")
    for i, link in enumerate(links):
        where = f"rewrite_links[{i}]"
        before = ctx.passed(link["predecessor_snapshot"]["id"], "source_snapshot")
        if before is not None and pred_id and before.get("implementation") != pred_id:
            yield Problem(rel, f"{where}.predecessor_snapshot.id", f"is a snapshot of {before.get('implementation')}, "
                                                                   f"not of the predecessor {pred_id}")
        after = ctx.passed(link["result"]["snapshot"], "source_snapshot")
        if after is not None and after.get("implementation") != data["id"]:
            yield Problem(rel, f"{where}.result.snapshot", f"is a snapshot of {after.get('implementation')}, "
                                                           "not of this derived implementation")
        cert = ctx.passed(link["certification"], "certification")
        if cert is None:
            continue
        pin = cert.get("candidate") or {}
        covered = pin.get("contract") or (cert.get("entry") or {}).get("id")
        named = f"{where}.certification"
        if covered != link["contract"]:
            yield Problem(rel, named, f"certification {cert['id']} covers contract {covered}, not {link['contract']}")
        if pin.get("id") != link["result"]["candidate"]:
            yield Problem(rel, named, f"certification {cert['id']} certifies candidate artifact {pin.get('id')}, "
                                      f"not the result {link['result']['candidate']}")
        built = ctx.passed(pin.get("id"), "candidate")
        if built is not None and built.get("source_snapshot") != link["predecessor_snapshot"]["id"]:
            yield Problem(rel, named, f"certification {cert['id']}'s candidate artifact {pin.get('id')} was built on "
                                      f"snapshot {built.get('source_snapshot')}, not the link's predecessor snapshot "
                                      f"{link['predecessor_snapshot']['id']}")
        if cert.get("verdict") != "certified":
            yield Problem(rel, named, f"certification {cert['id']} has verdict {cert.get('verdict')}, not certified")


def lineage_problems(store, library):
    """Library rule: every contract a lineage names is in the library (`swdb validate` with a library)."""
    for record in store.of_kind("implementation"):
        lineage = record.data.get("contract_lineage")
        if not isinstance(lineage, list):
            continue
        for i, entry in enumerate(lineage):
            contract = entry.get("contract") if isinstance(entry, dict) else None
            if isinstance(contract, str) and library.get(contract) is None:
                yield Problem(record.rel, f"contract_lineage[{i}].contract",
                              f"names contract {contract}, which the library does not hold")
