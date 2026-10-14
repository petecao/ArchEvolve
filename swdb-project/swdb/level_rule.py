"""The level rule: a candidate artifact's full certification level, computed on read (ADR 0016).

Created: 2026-10-14 ET (Probata proof of concept ticket 10). Design: formal-verification map spec
("Solution" (levels), "What a proven verdict asserts", "Proven once vs per candidate", "Bounds",
"Refutation, repair and bugs", "Records and levels"; S6, S11, S14; O1, O6, O7); map decisions 09,
10, 12, 13, 15, 17, 19, 24, 26. Format: docs/reference/format-v0.4-level-rule.md.

Nothing here writes. `candidate_level` reads the certification records and the proof records and
returns one level, ranked (proven unbounded > proven within bounds, threads <= k > proven within
bounds, threads = 1 > certified > uncertified; rejected stays as certification gives it), with its
reason.

The rule, in order:
1. A proof record counts only while every pin in its content-hash set matches the current hash
   (`Rule.pin_problems`), no failed method part or contract-proof part voids a version or content it
   pins (`Rule._voids`), and every proof record it depends on still counts.
2. Each counting proven record's level is taken after its caps: per bound dimension, the smallest
   bound among its own bounds and those of the proven parts it depends on (summaries, contract-proof
   parts, the minimum-bounds derivation, a route-3 predecessor's level). An unproven dependency is
   an assumption entry and never caps; assumption entries never cap.
3. Within one proof unit, the highest counting record sets the unit's level, whatever its route
   (S11). Across proof units, the weakest wins.
4. Proven requires certified (O1). A counting refuted record for the candidate's content hash blocks
   every proven level and sets the refuted flag.

The rule has its own version, `VERSION`, outside the method version (26 item 9): a rule change
recomputes levels and voids no proof.
"""

import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from swdb import artifacts, yamlio

VERSION = "level-rule.1"
UNBOUNDED = "unbounded"
ORDER = ("uncertified", "certified", "proven_within_bounds_threads_1", "proven_within_bounds_threads_k",
         "proven_unbounded")
PROVEN = ORDER[2:]
SEMANTICS_PARTS = {"semantics_controls"}                                # void the proof-semantics version
CONCURRENCY_PARTS = {"concurrency_controls", "civl_genmc_agreement"}    # void the method version
NEGATIVE_CONTROLS_PART = "negative_controls"                            # void the contract content
MINIMUM_PART = "minimum_bounds_derivation"
PROOF_SEMANTICS_FOLDER = "proof_semantics"
BELOW_MINIMUM = "bounded check below minimum"
WORDS = {"proven_unbounded": "proven unbounded",
         "proven_within_bounds_threads_k": "proven within bounds, threads ≤ k",
         "proven_within_bounds_threads_1": "proven within bounds, threads = 1",
         "certified": "certified", "uncertified": "uncertified", "rejected": "rejected"}


def rank(level):
    """The level's place in ORDER (rejected ranks with uncertified: neither has a proven level)."""
    return ORDER.index(level) if level in ORDER else 0


def bounds_level(bounds):
    """The proven level that bounds alone give: every dimension unbounded, else the thread sub-rung."""
    if all(value == UNBOUNDED for value in bounds.values()):
        return "proven_unbounded"
    return "proven_within_bounds_threads_1" if bounds.get("threads") == 1 else "proven_within_bounds_threads_k"


def smallest(*bound_sets):
    """Per dimension, the smallest bound among the sets ("unbounded" is above every number)."""
    merged = {}
    for bounds in bound_sets:
        for dimension, value in bounds.items():
            old = merged.get(dimension, UNBOUNDED)
            merged[dimension] = value if old == UNBOUNDED or (value != UNBOUNDED and value < old) else old
    return merged


class Rule:
    """One read of the records: every proof record's status and every candidate's level, memoized."""

    def __init__(self, store, library=None):
        from swdb.extensa_boundary import _library_for
        from swdb.library import default_root
        self.store = store
        self.library = library if library is not None else _library_for(store)
        self.library_root = default_root(store.dir)
        self.proofs = {r.id: r.data for r in store.of_kind("proof")}
        self._status = {}
        self._candidates = {}
        self._current = {}
        self.voids = self._voids()

    # -- one record ------------------------------------------------------------------------

    def status(self, rid):
        """{counts, stale: [{pin, reason}], bounds (after caps; proven only), caps} of one record."""
        if rid in self._status:
            return self._status[rid]
        record = self.proofs.get(rid)
        if record is None:
            return _not_counting("-", f"no proof record {rid}")
        self._status[rid] = _not_counting("-", "the record depends on itself")
        stale = list(self.pin_problems(record)) + list(self._void_problems(record))
        dependencies, more = self._dependencies(record)
        stale += more
        result = {"counts": not stale, "stale": stale, "bounds": None, "caps": [], "uses": dependencies,
                  "below_minimum": None}
        if not stale and record.get("verdict") == "proven":
            own = dict(record.get("bounds") or {})
            below = self._below_minimum(record, own)
            if below is not None:
                result["below_minimum"] = below          # a bounded check below the minimum: no level
            else:
                result["bounds"] = smallest(own, *(d["bounds"] for d in dependencies))
                result["caps"] = [d for d in dependencies
                                  if rank(bounds_level(d["bounds"])) < rank(bounds_level(own))]
        self._status[rid] = result
        return result

    def _below_minimum(self, record, bounds):
        """The dimensions where bounds fall below the pinned minimum bounds, or None when none do.

        The minimum bounds are the bounds of the minimum-bounds derivation record the pin names; a
        dimension of the minimum that the record does not bound at all counts as below it."""
        pin = (record.get("pins") or {}).get("minimum_bounds") or {}
        derivation = self.proofs.get(pin.get("id") or "") if not _not_applicable(pin) else None
        if derivation is None:
            return None
        below = []
        for dimension, least in (derivation.get("bounds") or {}).items():
            value = bounds.get(dimension)
            if value is None or (value != UNBOUNDED and (least == UNBOUNDED or value < least)):
                below.append(dimension)
        return below or None

    def pin_problems(self, record):
        """Each pin whose hash differs from the current one: [{pin, reason}] (dependencies aside)."""
        pins = record.get("pins") or {}
        checks = {
            "code": self.current_code,
            "contract": self.current_entry,
            "baseline_function": self.current_snapshot,
            "reference_semantics": self.current_entry,
            "proof_semantics": lambda ident: self.current_version(PROOF_SEMANTICS_FOLDER, ident),
            "method_version": self.current_method,
            "minimum_bounds": self.current_record,
            "predecessor_snapshot": self.current_code,
        }
        for kind, current in checks.items():
            pin = pins.get(kind) or {}
            if _not_applicable(pin):
                continue
            now = current(pin.get("id"))
            if now != pin.get("sha256"):
                yield {"pin": kind, "reason": _changed(kind, pin, now)}
        for position, pin in enumerate(pins.get("summaries") or []):
            now = self.current_entry(pin.get("id"))
            if now != pin.get("sha256"):
                yield {"pin": "summaries", "reason": f"summary {position}: " + _changed("summary entry", pin, now)}

    def _dependencies(self, record):
        """([{kind, record | candidate, bounds}] of the proven parts this record depends on, [stale])."""
        pins = record.get("pins") or {}
        used, stale = [], []

        def depend(kind, rid, label, pin_kind):
            state = self.status(rid)
            if not state["counts"]:
                stale.append({"pin": pin_kind, "reason": f"{label} {rid} stopped counting", "dependency": rid})
                return
            used.append({"kind": kind, "record": rid, "bounds": state["bounds"],
                         "constants": (self.proofs[rid].get("pins") or {}).get("build_constants") or []})

        for pin in pins.get("summaries") or []:
            depend("summary", pin.get("proof_record"), f"the proof record of summary {pin.get('id')}", "summaries")
        minimum = pins.get("minimum_bounds") or {}
        if not _not_applicable(minimum) and minimum.get("id") in self.proofs:
            depend("minimum_bounds", minimum["id"], "the minimum-bounds derivation", "minimum_bounds")
        for part, rids in sorted(self._contract_parts(record).items()):
            counting = [(rid, self.status(rid)) for rid in sorted(rids)]
            counting = [(rid, state) for rid, state in counting if state["counts"]]
            if not counting:
                stale.append({"pin": "contract", "reason": f"contract-proof part {part} stopped counting",
                              "dependency": sorted(rids)[0]})
                continue
            proven = [(rid, state) for rid, state in counting if state["bounds"] is not None]
            if proven:          # within one part, the highest counting record: any valid proof counts
                rid, _state = max(proven, key=lambda item: rank(bounds_level(item[1]["bounds"])))
                depend("contract_proof_part", rid, f"contract-proof part {part}", "contract")
        predecessor = pins.get("predecessor_snapshot") or {}
        if not _not_applicable(predecessor) and self.store.get(predecessor.get("id") or "", "candidate"):
            proven = self.candidate(predecessor["id"])["proven"]
            if proven is None:
                stale.append({"pin": "predecessor_snapshot",
                              "reason": f"the predecessor {predecessor['id']} has no proven level"})
            else:
                used.append({"kind": "predecessor", "candidate": predecessor["id"], "bounds": proven["bounds"],
                             "records": proven["records"], "constants": []})
        constants = {c.get("name"): c.get("value") for c in pins.get("build_constants") or []}
        for dependency in used:
            for constant in dependency.pop("constants"):
                name = constant.get("name")
                if name in constants and constants[name] != constant.get("value"):
                    stale.append({"pin": "build_constants", "reason": f"build constant {name} is "
                                  f"{constants[name]!r} here but {constant.get('value')!r} in {dependency['record']}"})
        return [d for d in used if d["bounds"] is not None], stale

    def _contract_parts(self, record):
        """{part: [record IDs]}: the contract-proof parts of the contract content a candidate record pins."""
        if (record.get("subject") or {}).get("kind") != "candidate_proof_unit":
            return {}
        contract = (record.get("pins") or {}).get("contract") or {}
        if _not_applicable(contract):
            return {}
        parts = {}
        for rid, other in self.proofs.items():
            subject = other.get("subject") or {}
            if (subject.get("kind") == "contract_proof_part" and subject.get("id") == contract.get("id")
                    and subject.get("part") != MINIMUM_PART and other.get("verdict") is not None
                    and ((other.get("pins") or {}).get("contract") or {}) == contract):
                parts.setdefault(subject.get("part") or "-", []).append(rid)
        return parts

    # -- voids -------------------------------------------------------------------------------

    def _voids(self):
        """{(pin kind, id, sha256): failed record}: what a counting failed part voids.

        A failed part is a refuted record: a semantics control with the wrong verdict voids the
        proof-semantics version it pins (12 item 9); a concurrency control with the wrong verdict or
        a CIVL-GenMC contradiction voids the method version it pins (15 items 9, 12); a negative
        control that proves voids the contract content it pins (10 item 2)."""
        voids = {}
        for rid, record in sorted(self.proofs.items()):
            subject = record.get("subject") or {}
            if record.get("verdict") != "refuted" or list(self.pin_problems(record)):
                continue
            part, kind = subject.get("part"), None
            if subject.get("kind") == "method_part" and part in SEMANTICS_PARTS:
                kind = "proof_semantics"
            elif subject.get("kind") == "method_part" and part in CONCURRENCY_PARTS:
                kind = "method_version"
            elif subject.get("kind") == "contract_proof_part" and part == NEGATIVE_CONTROLS_PART:
                kind = "contract"
            pin = ((record.get("pins") or {}).get(kind) or {}) if kind else {}
            if kind and pin and not _not_applicable(pin):
                voids.setdefault((kind, pin.get("id"), pin.get("sha256")), rid)
        return voids

    def _void_problems(self, record):
        pins = record.get("pins") or {}
        for kind in ("proof_semantics", "method_version", "contract"):
            pin = pins.get(kind) or {}
            failed = self.voids.get((kind, pin.get("id"), pin.get("sha256")))
            if failed and failed != record.get("id"):
                yield {"pin": kind, "reason": f"{kind} {pin.get('id')} is void: failed record {failed}",
                       "failed": failed}

    # -- current hashes ------------------------------------------------------------------------

    def current_code(self, ident):
        candidate = self.store.get(ident or "", "candidate")
        if candidate is not None:
            return (candidate.get("artifact") or {}).get("sha256")
        return self.current_entry(ident)

    def current_entry(self, ident):
        if self.library is None or self.library.get(ident) is None:
            return None
        return self.library.content_sha256(ident)

    def current_snapshot(self, ident):
        snapshot = self.store.get(ident or "", "source_snapshot")
        return (snapshot.get("artifact") or {}).get("sha256") if snapshot else None

    def current_method(self, ident):
        from swdb import method_version
        if "method_version" not in self._current:
            found = method_version.current(self.library_root)
            self._current["method_version"] = method_version.pin(found) if found else {}
        current = self._current["method_version"]
        return current.get("sha256") if current.get("id") == ident else None

    def current_version(self, folder, ident):
        """The file sha256 of version `ident` in library/<folder>/ while it is current in its line, else None."""
        if folder not in self._current:
            self._current[folder] = current_versions(self.library_root, folder)
        return self._current[folder].get(ident)

    def current_record(self, ident):
        record = self.proofs.get(ident or "")
        return artifacts.digest(record) if record is not None else None

    # -- a candidate artifact ------------------------------------------------------------------

    def candidate(self, candidate_id):
        """The full answer for one candidate artifact (memoized; a predecessor is read the same way)."""
        if candidate_id in self._candidates:
            return self._candidates[candidate_id]
        from swdb.extensa_boundary import candidate_certifications, certification_level
        self._candidates[candidate_id] = {"proven": None}             # a predecessor cycle proves nothing
        result = certification_level(self.store, candidate_id, self.library)
        result["certification_level"] = result["level"]
        _bound, counted = candidate_certifications(self.store, candidate_id, self.library)
        contracts = {(r.get("candidate") or {}).get("contract") or (r.get("entry") or {}).get("id")
                     for r in counted if r.get("verdict") == "certified"} - {None}
        result.update(self.level(candidate_id, result["level"], contracts))
        self._candidates[candidate_id] = result
        return result

    def level(self, candidate_id, certification_level, contracts):
        """The proven part of the level and its reason, for a candidate with these counted contracts."""
        records = sorted((r for r in self.proofs.values()
                          if (r.get("subject") or {}).get("kind") == "candidate_proof_unit"
                          and r["subject"].get("candidate") == candidate_id), key=lambda r: r["id"])
        units = []
        for contract in sorted(contracts):
            mine = [r for r in records if ((r.get("pins") or {}).get("contract") or {}).get("id") == contract]
            proven = [(r, self.status(r["id"])) for r in mine]
            proven = [(r, s) for r, s in proven if s["counts"] and s["bounds"] is not None]
            best = max((bounds_level(s["bounds"]) for _r, s in proven), key=rank, default="certified")
            top = [{"record": r["id"], "bounds": s["bounds"], "route": r.get("route"), "caps": s["caps"]}
                   for r, s in proven if bounds_level(s["bounds"]) == best]
            units.append({"contract": contract, "level": best, "records": top,
                          "bounds": top[0]["bounds"] if top else None})
        level = min((u["level"] for u in units), key=rank) if units else "certified"
        refutation = self._refuted(records)
        proven = None
        if certification_level == "certified" and level in PROVEN and not refutation["flag"]:
            proven = {"level": level, "bounds": smallest(*(u["bounds"] for u in units)),
                      "records": sorted(r["record"] for u in units for r in u["records"])}
        final = proven["level"] if proven else certification_level
        stale = [{"record": r["id"], "pins": self.status(r["id"])["stale"]} for r in records
                 if r.get("verdict") is not None and not self.status(r["id"])["counts"]]
        below = [{"record": r["id"], "text": BELOW_MINIMUM, "dimensions": self.status(r["id"])["below_minimum"] or []}
                 for r in records if r.get("failure_class") == "below_minimum_bounds"
                 or (self.status(r["id"])["counts"] and self.status(r["id"])["below_minimum"])]
        direct = [{"record": r["id"], "text": f"direct proof, no matching contract: {self._words(r)}"}
                  for r in records if r.get("verdict") is not None and self.status(r["id"])["counts"]
                  and ((r.get("pins") or {}).get("contract") or {}).get("id") not in contracts]
        return {"level": final, "rank": rank(final), "level_rule": VERSION, "proven": proven, "refuted": refutation,
                "snapshot": snapshot(final, proven["records"] if proven else []),
                "proof_units": units, "assumptions": self._assumptions(proven["records"] if proven else []),
                "stale_proofs": stale, "below_minimum": below, "direct_proofs": direct,
                "skipped": [{"record": r["id"], "skip_reason": r["skip_reason"]} for r in records
                            if r.get("skip_reason")],
                "proof_records": [r["id"] for r in records]}

    def _refuted(self, records):
        """The refuted flag: counting refuted records of the candidate's content hash, their replay
        labels, and "bug" only while a counting kernel reproduction cites one of them (26 item 8)."""
        refutations = [r for r in records if r.get("verdict") == "refuted" and self.status(r["id"])["counts"]]
        cited = {r["id"] for r in refutations}
        reproductions = sorted(rid for rid, r in self.proofs.items()
                               if (r.get("subject") or {}).get("kind") == "kernel_reproduction"
                               and r["subject"].get("id") in cited and r.get("verdict") == "refuted"
                               and self.status(rid)["counts"])
        return {"flag": bool(refutations),
                "records": [{"record": r["id"], "replay_label": r.get("replay_label")} for r in refutations],
                "evidence": ("bug" if reproductions else "unit-level refutation") if refutations else None,
                "reproductions": reproductions}

    def _words(self, record):
        state = self.status(record["id"])
        if state["bounds"] is not None:
            return WORDS[bounds_level(state["bounds"])]
        if state["below_minimum"]:
            return BELOW_MINIMUM
        return record.get("verdict", "").replace("_", " ")

    def _assumptions(self, rids):
        """The assumption set of the level: every entry of the records that set it and of the proven
        parts they depend on, once each, with the records that hold it (assumption entries never cap)."""
        entries, seen, pending = {}, set(), list(rids)
        while pending:
            rid = pending.pop(0)
            if rid in seen or rid not in self.proofs:
                continue
            seen.add(rid)
            for entry in self.proofs[rid].get("assumptions") or []:
                key = (entry.get("kind"), (entry.get("reference") or {}).get("id"),
                       (entry.get("reference") or {}).get("sha256"), entry.get("sentence"))
                entries.setdefault(key, {**entry, "records": []})["records"].append(rid)
            for dependency in self.status(rid)["uses"]:
                pending += [dependency["record"]] if "record" in dependency else list(dependency.get("records", []))
        return list(entries.values())


def current_versions(library_root, folder):
    """{version ID: file sha256} of the current version files in <library>/<folder>/.

    Versions form one line per `target` (a proof semantics belongs to its hardware target; a file
    with no target is in the one unnamed line). The current version of a line has the highest
    `sequence`; every older one is superseded, so records that pin it stop counting."""
    lines = {}
    path = Path(library_root) / folder
    for file in sorted(path.glob("*.yaml")) if path.is_dir() else []:
        try:
            data = yamlio.load(file)
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and isinstance(data.get("id"), str) and isinstance(data.get("sequence"), int):
            entry = (data["sequence"], data["id"], artifacts.file_hash(file))
            lines[data.get("target")] = max(lines.get(data.get("target"), entry), entry)
    return {ident: sha for _sequence, ident, sha in lines.values()}


def _not_counting(pin, reason):
    return {"counts": False, "stale": [{"pin": pin, "reason": reason}], "bounds": None, "caps": [], "uses": [],
            "below_minimum": None}


def _not_applicable(pin):
    return isinstance(pin, dict) and "not_applicable" in pin


def _changed(kind, pin, current):
    if current is None:
        return f"{kind} pin names {pin.get('id')!r}, which is not current"
    return f"{kind} pin {pin.get('id')!r} holds sha256 {pin.get('sha256')}; the current one is {current}"


def snapshot(level, records, now=None):
    """The dated level snapshot campaign summaries, handoffs and promotion reviews store (26 items 2, 9).

    It names the level, the time in Eastern Time, the level-rule version and the counting proof records
    that set the level. A snapshot is never recomputed: a later read may give another level."""
    now = now or datetime.datetime.now(ZoneInfo("America/New_York"))
    return {"level": level, "at": now.strftime("%Y-%m-%d %H:%M ET"), "level_rule": VERSION, "records": list(records)}


def candidate_level(store, candidate_id):
    """`swdb candidate-level`'s whole answer: certification, the proven level and the reason."""
    return Rule(store).candidate(candidate_id)
