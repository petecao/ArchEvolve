"""The `certification_level` block of the `evaluation_result` handoff: the level in plain, fixed words.

Created: 2026-10-14 ET (Probata proof of concept ticket 18). Design: formal-verification map spec ("ArchEvolve
mode", "Records and levels", "What a proven verdict asserts"); map decision 26 items 2, 7 and 9; ADR 0016.
Format: docs/bfs-handoff-contract-v1.2.md.

The block is a dated snapshot of what `swdb candidate-level` reads when the message is rendered (the level
rule, `swdb.level_rule`); it is reported, never ranked, and never changes the envelope's performance claim or
result class. Every sentence comes from a fixed template here; nothing a proof record says in free text (an
assumption entry's own `sentence`) reaches it, and no LLM writes it:

- the level sentence (`LEVEL_SENTENCES`), with each bound dimension's value or "any";
- one sentence per assumption from the template of its kind (`TEMPLATES`, all seven kinds), filled only with
  the entry's reference ID; an assumed clause's sentence is that clause's own statement in the library;
- when not proven, the highest level reached and each failure class in its plain words (the `words` field
  of vocabulary `proof_failure_classes`);
- always the speed sentence, `SPEED`.

`check` stops rendering instead of emitting a block that breaks these rules: a missing speed sentence, a
proven level whose proof record IDs do not resolve, a rank or score field. A kind with no template, an
assumed clause the library does not hold, or a reference that is not an ID stops rendering too.
"""

import re

from swdb.cli import Failure

SPEED = "Says nothing about speed."
#: One fixed template per assumption kind (vocabulary `proof_assumption_kinds`); `{id}` is the reference ID.
TEMPLATES = {
    "assumed_clause": "{statement} (assumed{owner}).",
    "proof_semantics": "The hardware target follows its proof semantics {id}.",
    "summary": "{id} behaves as its summary states (not proven in this job).",
    "reduction": "The reduction {id} holds (it narrows what was checked).",
    "trusted_tool": "{id} works correctly (a trusted tool, not checked).",
    "written_proof": "{id} holds as written (not yet machine-checked).",
    "platform_choice": "The platform fixes {id} by choice.",
}
LEVEL_SENTENCES = {
    "proven_unbounded": "Proven for every size and every thread count ({bounds}).",
    "proven_within_bounds_threads_k": "Proven within bounds ({bounds}).",
    "proven_within_bounds_threads_1": "Proven within bounds, one thread ({bounds}).",
}
NOT_PROVEN = "Not proven. Highest level reached: {level}."
#: Words for the outcomes that are not failure classes (the failure classes' words live in the vocabulary).
OUTCOME_WORDS = {"refuted": "refuted: the verifier found a counterexample",
                 "stale": "an earlier proof stopped counting (an input it pinned changed)"}
NO_ATTEMPT = "No proof attempt yet."
REFERENCE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:#/+@-]*")
FORBIDDEN = {"rank", "score", "ranking"}
FAILURE_VOCAB = "proof_failure_classes"


def render(store, candidate_id, now=None):
    """The checked block for one candidate artifact (None: the evaluation names no candidate artifact)."""
    made = block(store, candidate_id, now=now)
    check(made, store)
    return made


def block(store, candidate_id, now=None):
    from swdb import level_rule
    rule = level_rule.Rule(store)
    if not candidate_id or store.get(candidate_id, "candidate") is None:
        level, result = "uncertified", None
    else:
        result = rule.candidate(candidate_id)
        level = result["level"]
    proven = (result or {}).get("proven")
    made = {"candidate": candidate_id, "level": level, "level_words": level_rule.WORDS.get(level, level),
            "proven": proven is not None}
    sentences = []
    if proven is not None:
        bounds = _bounds(proven["bounds"])
        made.update(bounds=bounds, proof_records=list(proven["records"]))
        sentences.append(LEVEL_SENTENCES[proven["level"]].format(bounds="; ".join(
            f"{row['dimension']}: {'any' if row['value'] == 'any' else 'up to ' + str(row['value'])}" for row in bounds)))
        made["assumptions"] = _assumptions(result["assumptions"], rule.library)
        if made["assumptions"]:
            sentences.append("Assumes: " + " ".join(a["sentence"] for a in made["assumptions"]))
    else:
        made.update(bounds=None, assumptions=[], highest_level_reached=level,
                    proof_records=list((result or {}).get("proof_records") or []))
        made["failures"] = _failures(store, result)
        sentences.append(NOT_PROVEN.format(level=level_rule.WORDS.get(level, level)))
        sentences.append("Proof attempts ended: " + "; ".join(f["words"] for f in made["failures"]) + "."
                         if made["failures"] else NO_ATTEMPT)
    sentences.append(SPEED)
    made["speed"] = SPEED
    made["snapshot"] = level_rule.snapshot(level, made["proof_records"] if proven is not None else [], now=now)
    made["text"] = " ".join(sentences)
    return made


def check(made, store):
    """Refuse a block that breaks the rendering rules (the envelope is never emitted then)."""
    if made.get("speed") != SPEED or not str(made.get("text", "")).endswith(SPEED):
        raise Failure(f"the certification_level block lacks the sentence {SPEED!r}; the handoff is not rendered")
    if FORBIDDEN & _keys(made):
        raise Failure("the certification_level block is reported, never ranked: it may hold no rank or score")
    if made.get("proven"):
        missing = [rid for rid in made.get("proof_records") or [] if store.get(rid, "proof") is None]
        if not made.get("proof_records") or missing:
            raise Failure("the proven level's proof records cannot be resolved: " + (", ".join(missing) or "none named")
                          + "; the handoff is not rendered")


def _keys(value):
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in _keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in _keys(v)}
    return set()


def _bounds(bounds):
    """[{dimension, value}] with the thread count first; an unbounded dimension reads "any"."""
    names = ["threads"] + sorted(d for d in bounds if d != "threads")
    return [{"dimension": d, "value": "any" if bounds.get(d) == "unbounded" else bounds.get(d)} for d in names]


def _assumptions(entries, library):
    """One templated sentence per assumption (kind, reference), in the level rule's order, once each."""
    rows, seen = [], set()
    for entry in entries:
        kind, reference = entry.get("kind"), dict(entry.get("reference") or {})
        key = (kind, reference.get("id"), reference.get("sha256"))
        if key in seen:
            continue
        seen.add(key)
        rows.append({"kind": kind, "reference": {"id": reference.get("id"), "sha256": reference.get("sha256")},
                     "sentence": _sentence(kind, reference.get("id"), library), "records": list(entry.get("records") or [])})
    return rows


def _sentence(kind, ident, library):
    template = TEMPLATES.get(kind)
    if template is None:
        raise Failure(f"no template for assumption kind {kind}: the handoff is not rendered (no free text is shown)")
    if not isinstance(ident, str) or not REFERENCE_ID.fullmatch(ident):
        raise Failure(f"assumption reference {ident!r} is not a reference ID: the handoff is not rendered")
    if kind != "assumed_clause":
        return template.format(id=ident)
    entry_id, _, clause_id = ident.partition("#")
    entry = library.get(entry_id) if library is not None else None
    clause = next((c for c in (entry or {}).get("clauses") or [] if c.get("id") == clause_id), None)
    if clause is None or not clause.get("statement"):
        raise Failure(f"assumed clause {ident}: the library holds no clause {clause_id} of {entry_id} to state it; "
                      "the handoff is not rendered")
    statement = " ".join(str(clause["statement"]).split()).rstrip(".")
    owner = f"; owner {clause['owner']}" if clause.get("owner") else ""
    return template.format(statement=statement, owner=owner)


def _failures(store, result):
    """Each distinct way the candidate artifact's proof attempts ended, in plain words."""
    from swdb import paths, vocab
    if not result:
        return []
    vocabs, _ = vocab.load_all(paths.VOCAB)
    words = {value: entry.get("words") for value, entry in vocabs.entries.get(FAILURE_VOCAB, {}).items()}
    found = {}
    if result["refuted"]["flag"]:
        found["refuted"] = [r["record"] for r in result["refuted"]["records"]]
    for row in result.get("stale_proofs") or []:
        found.setdefault("stale", []).append(row["record"])
    for rid in result.get("proof_records") or []:
        record = store.get(rid, "proof") or {}
        name = record.get("failure_class") or record.get("skip_reason")
        if name:
            found.setdefault(name, []).append(rid)
    rows = []
    for name, records in found.items():
        text = OUTCOME_WORDS.get(name) or words.get(name)
        if not text:
            raise Failure(f"failure class {name} has no plain words in vocabulary {FAILURE_VOCAB}: the handoff is "
                          "not rendered")
        rows.append({"class": name, "words": text, "records": sorted(records)})
    return sorted(rows, key=lambda row: row["words"])
