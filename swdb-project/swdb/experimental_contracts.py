"""Experimental enabling contracts and the shared-contracts rule (Probata PoC ticket 63).

Created: 2026-10-14 ET. Design: the formal-verification map spec ("Proof routes": a new experimental enabling
contract for any input, its results proven by route 1; "ArchEvolve mode": shared contracts only, one rewrite
proposal per rewrite, a derived implementation enters the main database only through promotion; O7, O10);
decisions 17 items 5, 6, 8; 24 item 3; ADR 0007 (ArchEvolve mode accepts only shared certified entries).
Format: docs/reference/format-v0.4-derived.md ("Experimental enabling contracts").

Extensa mode: in a campaign whose file sets `library.new_enabling_contracts: true`, the rewriting role's answer
carries `new_contract` (the YAML text of one rewrite-contract entry, or null) beside its patch. `admit` adds it
to the campaign's library, in the experimental tier (no review) with entry status draft, only when

1. the campaign's allowed library tiers include experimental entries;
2. it is a rewrite-contract mapping with a new ID, and the patch applies it alone (certified alone);
3. it only reshapes: none of its strategies' effects offloads (`swdb.derived.enabling_problem`);
4. it passes library validation (the library's own checks of that entry, against the team store).

Everything else is refused before certification, and the library is left unchanged. A certified result is a
derived implementation (`swdb.derived`), proven by route 1 like any other; the contract gets no contract proof.

ArchEvolve mode: `shared_problem` and `lineage_problem` say why a contract, or a derived implementation's
lineage, is not shared and certified. `swdb submit` (through `swdb.library.proposal_gate`) and the proof path
(`swdb.archevolve_proof.certified_contracts`) refuse on them.
"""

from pathlib import Path

import yaml

from swdb.cli import Failure

FIELD = "new_contract"
ORIGIN = "extensa_rewriting"
FOLDER = "rewrite_contracts"
PREFIX = "contract."
USABLE = {"certified", "evaluated_on_target"}
NOTE_FILE = "NEW_CONTRACT.json"
NOTE = ("When no contract under `contracts/` fits the reshape your patch needs, you may write a new enabling "
        "contract: put the YAML text of one rewrite-contract entry (kind rewrite_contract, a new `contract.` ID, the "
        "fields the contracts under `contracts/` have) in `new_contract`, and name it alone in `contracts`. It may "
        "only reshape: none of its strategies may offload. It enters the library as an experimental entry, usable "
        "only in Extensa mode until Yan-Ru's review. Otherwise answer null.")


def file_of(contract_id):
    """The new contract's file, relative to the library root."""
    return f"{FOLDER}/{contract_id.removeprefix(PREFIX).replace('.', '_')}.yaml"


def _parse(text):
    from swdb import yamlio
    try:
        data = yaml.load(text, Loader=yamlio._Loader) if isinstance(text, str) else None
    except yaml.YAMLError as exc:
        raise Failure(f"the new contract is not YAML: {str(exc)[:200]}") from None
    if not isinstance(data, dict) or data.get("kind") != "rewrite_contract" or not isinstance(data.get("id"), str):
        raise Failure("the new contract is not a rewrite-contract mapping with a text ID")
    return data


def admit(text, *, library_root, team_dir, allowed_tiers, contracts, campaign, iteration, known=None):
    """Add the rewriting role's new enabling contract to the campaign's library; returns {contract,
    content_sha256, path}. Raises Failure (the library unchanged) when the contract is refused.

    `contracts` are the contracts the answer's patch applies; `known` maps contract IDs this campaign
    already added to their content hash (an identical contract named again is reused, not rewritten)."""
    from swdb import artifacts, derived
    from swdb.library import Library
    from swdb.store import Store
    if "experimental" not in allowed_tiers:
        raise Failure("the campaign's allowed library tiers exclude experimental entries, and a new enabling "
                      "contract is an experimental entry until promotion")
    entry = _parse(text)
    cid = entry["id"]
    if list(contracts) != [cid]:
        raise Failure(f"a rewrite that carries the new contract {cid} applies that contract alone (each rewrite is "
                      f"certified alone), not {', '.join(contracts) or 'none'}")
    provenance = entry.get("provenance") if isinstance(entry.get("provenance"), dict) else {}
    entry["provenance"] = {**provenance, "origin": {"kind": ORIGIN, "campaign": campaign, "iteration": iteration}}
    root = Path(library_root)
    library = Library(root)
    sha = artifacts.digest(entry)
    rel = file_of(cid)
    if library.get(cid) is not None:
        if (known or {}).get(cid) == library.content_sha256(cid) == sha:
            return {"contract": cid, "content_sha256": sha, "path": rel}
        raise Failure(f"the new contract's ID {cid} is already in the library")
    team = Store(Path(team_dir))
    problem = derived.enabling_problem(entry, [team])
    if problem:
        raise Failure(f"the new contract {cid} is not an enabling contract: {problem}")
    path = root / rel
    if path.exists():
        raise Failure(f"the library already has a file {rel}")
    path.parent.mkdir(parents=True, exist_ok=True)
    from swdb import yamlio
    path.write_text(yamlio.dumps(entry))
    found = [p for p in Library(root, team).validate() if Path(p.file).resolve() == path.resolve()]
    if found:
        path.unlink()
        raise Failure(f"the new contract {cid} fails library validation: "
                      + "; ".join(f"{p.field}: {p.reason}" for p in found[:5]))
    return {"contract": cid, "content_sha256": sha, "path": rel}


# --- ArchEvolve mode: shared contracts only ------------------------------------------------------

def shared_problem(library, contract_id, content_sha256=None):
    """Why ArchEvolve mode may not use the contract (a phrase), or None: it must be in the library, shared
    (Yan-Ru's review of its current content) and certified; with `content_sha256`, of exactly that content."""
    if library.get(contract_id) is None:
        return f"contract {contract_id} is not in the library"
    if content_sha256 is not None and library.content_sha256(contract_id) != content_sha256:
        return f"contract {contract_id}'s content changed since it was applied"
    state = library.state(contract_id)
    if state["tier"] != "shared" or state["status"] not in USABLE:
        return (f"contract {contract_id} is {state['tier']} with entry status {state['status']}: ArchEvolve mode "
                "uses only shared certified contracts (an experimental entry is usable only in Extensa mode until "
                "promotion)")
    return None


def target_gate(request, store):
    """`swdb submit` in ArchEvolve mode: refuse a rewrite proposal whose target is a derived implementation
    with a contract in its lineage that is not shared and certified (Extensa mode builds on any)."""
    from swdb import derived, workflow
    from swdb.library import Library, default_root
    if workflow.CREATION_TAGS.get("mode") == "extensa" or not isinstance(request, dict):
        return
    impl = store.get(request.get("implementation") or "", "implementation")
    if not derived.is_derived(impl) or not impl.get("contract_lineage"):
        return
    problem = lineage_problem(Library(default_root(store.dir), store), impl)
    if problem:
        raise Failure(f"ArchEvolve submit refuses a rewrite of {problem}")


def lineage_problem(library, implementation):
    """Why ArchEvolve mode may not build on a derived implementation (a phrase), or None: every contract of
    its lineage must be shared and certified, or the shared-contracts rule is bypassed through the predecessor."""
    for row in (implementation or {}).get("contract_lineage") or []:
        problem = shared_problem(library, row.get("contract"), row.get("content_sha256"))
        if problem:
            return f"derived implementation {implementation['id']}'s lineage: {problem}"
    return None
