"""The query site finder (ticket 55): regions chosen by one SQL query, with recorded reasons.

Created 2026-10-04 ET. Updated 2026-10-06 ET: query I/O goes through swdb.access.
Original SWDB code (spec "Site finder"; design decision D7: the site
finder is a query and costs no provider call). Updated 2026-10-05 ET: `swdb.db.meta` is public;
the statement-fact prefix `legality:` lives only in `QUERY` (its sha256 is recorded). It reads only the SQLite index (ADR 0002,
ticket 46): `access_patterns`, `steps`, `statements`, `statement_steps`, `statement_facts`,
`library_entries`, `library_dependencies`, `library_clauses`, `library_pattern_keys` and
`library_pattern_key_steps`. It never reads library YAML.

Decision procedure (the summary records `QUERY`'s sha256 and `FORMAT`; `assemble` is a pure
function of the query's rows, so the same database gives the same ordered region list):

1. Eligible entries: rewrite contracts named by the Extensa campaign and every library operation,
   in an allowed tier, with a pattern key, and bound to the Extensa campaign's target. An entry is
   bound to `native_cpu` when its dependency closure has no lowering (no hardware interface);
   to `dx100_gem5` when it has a lowering and every lowering uses a DX100 interface.
2. Key-pattern match (ADR 0003): key pattern k of entry E matches access pattern P of the
   campaign's kernel exactly when P's chain has as many steps as k, every step i has k's
   role and address shape at position i (relational division over `steps`), and P's update
   kind equals k's. Arrays are matched by role, never by name.
3. Region: for entry E in function F of implementation I, the statements (statements index)
   that perform a step of any access pattern matching any key pattern of E. Its ID is
   `<implementation>/<function>:<first line>-<last line>` over those statements' pinned lines.
4. The pattern key matches the region only when distinct access patterns can be assigned to
   all key patterns at once (a system of distinct representatives; the first assignment in
   key order over sorted pattern IDs is recorded).
5. Legality: every clause of E with role `legality` must hold on the region's recorded facts.
   A recorded fact is a statement annotation fact (`annotation_facts`, never an agent claim)
   on a statement of the region with field `legality:<entry id>:<clause id>`. The clause
   holds when at least one such fact has value true and none has another value. No fact, a
   false fact, or a non-boolean value means it does not hold, with the reason recorded.
6. The entry applies to the region only when 4 and 5 hold. Chosen regions are those with at
   least one applying entry, ordered by implementation, function, first line, last line;
   every other considered site is reported under `rejected` with its reason.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from swdb import access

FORMAT = "swdb.site-finder.v1"

#: Hardware interfaces a target's lowerings may use; an empty list means plain CPU code only.
TARGET_INTERFACES = {"native_cpu": [], "dx100_gem5": ["dx100-mmio"]}

QUERY = """\
-- swdb site finder v1 (ticket 55). Parameters: :kernel, :interfaces (JSON list, [] = plain CPU),
-- :tiers (JSON list), :contracts (JSON list of campaign rewrite contracts).
WITH
eligible AS (
  SELECT e.id AS entry, e.kind, e.tier, e.status, e.content_sha256, e.derived_from,
         json_extract(e.json, '$.pattern_key') AS pattern_key,
         (SELECT count(*) FROM library_pattern_keys k WHERE k.entry = e.id) AS key_count
  FROM library_entries e
  WHERE e.kind IN ('rewrite_contract', 'library_operation')
    AND e.tier IN (SELECT value FROM json_each(:tiers))
    AND (e.kind = 'library_operation' OR e.id IN (SELECT value FROM json_each(:contracts)))
    AND EXISTS (SELECT 1 FROM library_pattern_keys k WHERE k.entry = e.id)
    AND CASE WHEN json_array_length(:interfaces) = 0 THEN
          NOT EXISTS (SELECT 1 FROM library_dependencies d JOIN library_entries l ON l.id = d.dependency
                      WHERE d.entry = e.id AND l.kind = 'lowering')
        ELSE
          EXISTS (SELECT 1 FROM library_dependencies d JOIN library_entries l ON l.id = d.dependency
                  WHERE d.entry = e.id AND l.kind = 'lowering')
          AND NOT EXISTS (SELECT 1 FROM library_dependencies d JOIN library_entries l ON l.id = d.dependency
                          WHERE d.entry = e.id AND l.kind = 'lowering'
                            AND coalesce(json_extract(l.json, '$.interface.id'), '')
                                NOT IN (SELECT value FROM json_each(:interfaces)))
        END
),
chain_lengths AS (
  SELECT implementation, pattern, count(*) AS step_count FROM steps GROUP BY implementation, pattern
),
key_matches AS (
  SELECT k.entry, k.key_position, p.implementation, p.pattern, p.pattern_class
  FROM eligible el
  JOIN library_pattern_keys k ON k.entry = el.entry
  JOIN access_patterns p ON p.kernel = :kernel AND p.update_kind = k.update_kind
  JOIN chain_lengths n ON n.implementation = p.implementation AND n.pattern = p.pattern
                      AND n.step_count = k.step_count
  WHERE NOT EXISTS (
    SELECT 1 FROM library_pattern_key_steps ks
    WHERE ks.entry = k.entry AND ks.key_position = k.key_position
      AND NOT EXISTS (SELECT 1 FROM steps s
                      WHERE s.implementation = p.implementation AND s.pattern = p.pattern
                        AND s.position = ks.step AND s.role = ks.role AND s.address_shape = ks.address_shape))
),
sites AS (
  SELECT DISTINCT m.entry, m.key_position, m.implementation, st.function, m.pattern, m.pattern_class,
         st.statement, st.path, st.revision, st.first_line, st.last_line
  FROM key_matches m
  JOIN statement_steps ss ON ss.implementation = m.implementation AND ss.pattern = m.pattern
  JOIN statements st ON st.implementation = ss.implementation AND st.statement = ss.statement
),
regions AS (
  SELECT DISTINCT entry, implementation, function FROM sites
),
clauses AS (
  SELECT r.entry, r.implementation, r.function, c.clause, c.discharge_mode,
         (SELECT json_group_array(json_array(f.statement, f.value, f.basis, f.evidence))
          FROM statement_facts f
          WHERE f.implementation = r.implementation
            AND f.field = 'legality:' || r.entry || ':' || c.clause
            AND f.statement IN (SELECT s.statement FROM sites s
                                WHERE s.entry = r.entry AND s.implementation = r.implementation
                                  AND s.function IS r.function)) AS detail
  FROM regions r
  JOIN library_clauses c ON c.entry = r.entry AND c.role = 'legality'
)
SELECT 'entry' AS row_kind, entry, kind, tier, status, content_sha256, derived_from, key_count,
       NULL AS implementation, NULL AS function, NULL AS key_position, NULL AS pattern, NULL AS pattern_class,
       NULL AS statement, NULL AS path, NULL AS revision, NULL AS first_line, NULL AS last_line,
       NULL AS clause, NULL AS discharge_mode, pattern_key AS detail
FROM eligible
UNION ALL
SELECT 'match', entry, NULL, NULL, NULL, NULL, NULL, NULL, implementation, function, key_position, pattern,
       pattern_class, statement, path, revision, first_line, last_line, NULL, NULL, NULL
FROM sites
UNION ALL
SELECT 'clause', entry, NULL, NULL, NULL, NULL, NULL, NULL, implementation, function, NULL, NULL, NULL,
       NULL, NULL, NULL, NULL, NULL, clause, discharge_mode, detail
FROM clauses
ORDER BY row_kind, entry, implementation, function, key_position, pattern, statement, clause
"""

QUERY_SHA256 = hashlib.sha256(QUERY.encode()).hexdigest()


def parameters(campaign):
    """The query parameters an Extensa campaign file fixes (D5 fields only)."""
    target = campaign["target"]
    if target not in TARGET_INTERFACES:
        raise ValueError(f"no site-finder target binding for {target!r}")
    return {"kernel": campaign["kernel"], "target": target, "interfaces": list(TARGET_INTERFACES[target]),
            "tiers": sorted(campaign["library"]["allowed_tiers"]),
            "contracts": sorted(campaign["library"]["contracts"])}


def run_query(db_path, params):
    bound = {"kernel": params["kernel"], "interfaces": json.dumps(params["interfaces"]),
             "tiers": json.dumps(params["tiers"]), "contracts": json.dumps(params["contracts"])}
    return access.query(db_path, QUERY, bound)


def find(records_dir, campaign, *, library=None, db_path):
    """Build or refresh the index for (records, library) at `db_path`, run the query, assemble."""
    from swdb import db
    if db.is_stale(records_dir, db_path, library):
        db.build(records_dir, db_path, library)
    params = parameters(campaign)
    result = assemble(run_query(db_path, params))
    meta = dict(db.meta(db_path))
    return {"format": FORMAT, "query_sha256": QUERY_SHA256, "parameters": params,
            "database": {"fingerprint": meta.get("fingerprint"), "builder": meta.get("builder")}, **result}


# --- assembly (pure) ----------------------------------------------------------------------

def _key_text(key):
    if not isinstance(key, dict):
        return repr(key)
    steps = [f"{r}:{s}" for r, s in zip(key.get("roles") or [], key.get("address_shapes") or [])]
    return " > ".join(steps) + f" : {key.get('update_kind')}"


def _assign(candidates):
    """First system of distinct representatives in key order over sorted candidates, or None."""
    chosen = []

    def search(position):
        if position == len(candidates):
            return True
        for pattern in candidates[position]:
            if pattern not in chosen:
                chosen.append(pattern)
                if search(position + 1):
                    return True
                chosen.pop()
        return False
    return list(chosen) if search(0) else None


def _clause(row):
    facts = sorted((tuple(f) for f in json.loads(row["detail"] or "[]")), key=lambda f: (f[0], str(f[1])))
    shown = [{"statement": s, "value": json.loads(v) if v is not None else None, "basis": b, "evidence": e}
             for s, v, b, e in facts]
    values = [f["value"] for f in shown]
    if not shown:
        holds, reason = False, "no recorded fact on the region's statements (a missing fact counts as not holding)"
    elif any(v is not True and v is not False for v in values):
        holds, reason = False, "a recorded fact is not true or false"
    elif False in values:
        where = ", ".join(f"{f['statement']} ({f['basis']})" for f in shown if f["value"] is False)
        holds, reason = False, f"recorded fact says it does not hold: {where}"
    else:
        where = ", ".join(f"{f['statement']} ({f['basis']})" for f in shown)
        holds, reason = True, f"holds by recorded fact: {where}"
    return {"clause": row["clause"], "discharge_mode": row["discharge_mode"], "holds": holds,
            "reason": reason, "facts": shown}


def assemble(rows):
    entries, matches, clauses = {}, defaultdict(list), defaultdict(list)
    for row in rows:
        if row["row_kind"] == "entry":
            entries[row["entry"]] = row
        elif row["row_kind"] == "match":
            matches[(row["implementation"], row["function"], row["entry"])].append(row)
        else:
            clauses[(row["implementation"], row["function"], row["entry"])].append(row)
    regions, rejected = {}, []
    matched_entries = {key[2] for key in matches}
    for entry_id in sorted(set(entries) - matched_entries):
        rejected.append({"entry": entry_id, "region": None,
                         "reason": "no access pattern of the kernel matches any of its key patterns"})
    for (impl, function, entry_id), rows_here in sorted(matches.items(), key=lambda kv: tuple(map(str, kv[0]))):
        meta = entries[entry_id]
        keys = json.loads(meta["detail"] or "[]")
        statements = {}
        candidates = [[] for _ in range(meta["key_count"])]
        for r in rows_here:
            statements[r["statement"]] = r
            if r["pattern"] not in candidates[r["key_position"]]:
                candidates[r["key_position"]].append(r["pattern"])
        candidates = [sorted(c) for c in candidates]
        ordered = sorted(statements.values(), key=lambda r: (r["first_line"] or 0, r["last_line"] or 0, r["statement"]))
        first, last = ordered[0]["first_line"], max(r["last_line"] or 0 for r in ordered)
        region_id = f"{impl}/{function}:{first}-{last}"
        pattern_key = [{"key_position": k, "key": _key_text(keys[k] if k < len(keys) else None),
                        "patterns": candidates[k]} for k in range(meta["key_count"])]
        missing = [p["key_position"] for p in pattern_key if not p["patterns"]]
        assignment = None if missing else _assign(candidates)
        for p in pattern_key:
            p["assigned"] = assignment[p["key_position"]] if assignment else None
        legality = [_clause(r) for r in sorted(clauses.get((impl, function, entry_id), []), key=lambda r: r["clause"])]
        application = {
            "entry": entry_id, "kind": meta["kind"],
            "contract": entry_id if meta["kind"] == "rewrite_contract" else None,
            "derived_from": meta["derived_from"], "tier": meta["tier"], "status": meta["status"],
            "content_sha256": meta["content_sha256"], "pattern_key": pattern_key,
            "statements": [r["statement"] for r in ordered], "legality": legality,
        }
        if missing:
            reason = "key pattern(s) " + ", ".join(
                f"{k} ({pattern_key[k]['key']})" for k in missing) + " match no access pattern of the region"
        elif assignment is None:
            reason = "no distinct access patterns serve every key pattern at once"
        else:
            failing = [c for c in legality if not c["holds"]]
            reason = ("legality clause(s) do not hold: " + "; ".join(f"{c['clause']}: {c['reason']}" for c in failing)
                      if failing else None)
        if reason:
            rejected.append({"entry": entry_id, "region": region_id, "reason": reason, "application": application})
            continue
        application["applies"] = True
        region = regions.setdefault(region_id, {
            "id": region_id, "implementation": impl, "function": function,
            "source": {"path": ordered[0]["path"], "revision": ordered[0]["revision"], "lines": [first, last]},
            "statements": [], "applications": [], "_order": (impl, str(function), first, last), "_lines": {}})
        region["_lines"].update({r["statement"]: r["first_line"] or 0 for r in ordered})
        region["statements"] = sorted(region["_lines"], key=lambda s: (region["_lines"][s], s))
        region["applications"].append(application)
    chosen = sorted(regions.values(), key=lambda r: (r.pop("_order"), r["id"]))
    for region in chosen:
        region.pop("_lines")
        region["applications"].sort(key=lambda a: a["entry"])
        region["reason"] = "; ".join(_why(a) for a in region["applications"])
    return {"regions": chosen, "rejected": rejected}


def _why(application):
    legality = application["legality"]
    holds = (f"all {len(legality)} legality clause(s) hold on recorded facts" if legality
             else "the entry declares no legality clause")
    assigned = ", ".join(p["assigned"] for p in application["pattern_key"])
    return (f"{application['entry']} ({application['kind']}): pattern key {len(application['pattern_key'])}/"
            f"{len(application['pattern_key'])} matched by {assigned} on statements "
            f"{', '.join(application['statements'])}; {holds}")


def region_rows(result):
    """The Extensa campaign summary's `regions` rows: ID, one-line reason, and the structured why."""
    return [{"id": r["id"], "reason": r["reason"],
             "why": {"query_sha256": result["query_sha256"], "statements": r["statements"],
                     "source": r["source"],
                     "applications": [{"entry": a["entry"], "contract": a["contract"], "kind": a["kind"],
                                       "content_sha256": a["content_sha256"],
                                       "pattern_key": a["pattern_key"], "statements": a["statements"],
                                       "legality": [{k: c[k] for k in ("clause", "holds", "reason")}
                                                    for c in a["legality"]]}
                                      for a in r["applications"]]}}
            for r in result["regions"]]


def default_db_path(folder):
    return Path(folder) / "site-finder.sqlite"
