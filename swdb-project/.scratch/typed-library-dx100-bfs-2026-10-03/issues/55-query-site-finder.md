# 55 — Query site finder

Created: 2026-10-03
Updated: 2026-10-04 ET (resolved); 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md))
**Type:** slice
**Status:** resolved
**Blocked by:** 46, 52
**Spec:** `../spec.md`

**What to build:** Regions are chosen by a repeatable query instead of a fixed list.

## Acceptance

- [x] With `regions: query` in the campaign file, `swdb campaign` selects regions by one SQL query over the SQLite access-pattern and step tables, the statements index and the indexed contract pattern keys (all from ticket 46). It never reads library YAML.
- [x] Results are deterministic: the same database gives the same ordered region list, and the query text's sha256 is recorded in the summary.
- [x] Each chosen region records why it was chosen: the matched pattern key, the statement IDs, and the contract and entry IDs.
- [x] A contract applies only when its pattern key matches and every legality clause holds on the region's recorded facts. A clause with no recorded fact counts as not holding, and the reason is recorded.
- [x] Fixture tests on BFS TDStep select the read-offload region for a gem5 campaign and the library-operation regions (ticket 51 pattern keys) for a native campaign.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).

## Answer

Resolved 2026-10-04 00:58 ET by the agent under Yan-Ru's standing implementation approval.

**Built.**

- `swdb/site_finder.py`: one SQL query (`QUERY`, sha256 `QUERY_SHA256`, format
  `swdb.site-finder.v1`) over `access_patterns`, `steps`, `statements`, `statement_steps`,
  `statement_facts`, `library_entries`, `library_dependencies`, `library_clauses` and the new
  pattern-key tables. It never reads library YAML (test: the library folder is deleted after
  indexing and the answer is unchanged). `assemble` is a pure function of the query rows, so the
  same database gives the same ordered list. The full decision procedure is in the module docstring:
  1. **Eligible entries.** Campaign-named rewrite contracts and every library operation that has a
     pattern key and sits in an allowed tier. Each must be bound to the target: `native_cpu` means
     no lowering in the dependency closure; `dx100_gem5` means only `dx100-mmio` lowerings.
  2. **Key-pattern match.** Exact chain equality (ADR 0003): same step count, the same role and
     address shape at every position (relational division over `steps`), and the same update kind.
  3. **Region.** The statements performing any matched pattern, with ID
     `<impl>/<function>:<first>-<last>` (pinned lines).
  4. **Pattern key matches** only when distinct access patterns serve all key patterns at once (a
     system of distinct representatives). The first assignment is recorded.
  5. **Legality.** Every `legality` clause needs a recorded fact: a statement `annotation_facts`
     entry (never an agent claim) on a region statement, field `legality:<entry>:<clause>`. A clause
     holds only when there is at least one `true` value and no other value. No fact, `false`, a
     non-boolean value, or contradicting facts mean "does not hold", with the reason recorded.
- `swdb/db.py`: the new tables `statement_facts`, `library_pattern_keys` and
  `library_pattern_key_steps`, documented in `docs/reference/database.md`. Builds and staleness
  accept an explicit library folder.
- `swdb campaign` with `regions: query`:
  - Before setup, the campaign refuses (with the rejected reasons) when no region is chosen.
  - Each iteration's `regions` rows carry `id`, `reason` and `why`: statements, source lines, and
    per entry the contract/entry IDs, content sha256, pattern-key assignment and each legality
    clause with its reason.
  - The iteration also carries `site_finder.rejected`. The summary carries `site_finder`
    (`query_sha256`, parameters; schema and `format-v0.4-extensa.md` updated).
  - `REGIONS.json` gives the provider the chosen regions.
  - A returned contract that the finder did not apply rejects the candidate.

**Tests.** `tests/test_site_finder.py`, 17 cases:
- gem5 picks `dx100-bfs-scalar/TDStep:240-243` for `contract.bfs_read_offload`.
- Native picks gather staging (240-241) and regroup (241-241). Binning and relabel are rejected by
  the key, and the DX100 contract is not eligible on native.
- Determinism, and no reading of library YAML.
- Key match with a failing clause is not applied: a false fact, a missing fact, a non-boolean
  value, a fact outside the region, contradicting facts, and no facts at all.
- The derived BC contract needs its own facts.
- Tier and contract scope, the distinct-pattern requirement, and chain-form validation.
- Three end-to-end `swdb campaign` runs: query regions, a contract outside the chosen regions, and
  the no-region refusal.

**Assumptions (agent-decided, revisable).**

- Ticket 51's library-operation keys were not chains (for example two roles with one shape). They
  are normalized to chain form, and `swdb validate` now requires that form for both contracts and
  operations: one role per shape, ending at `target`, with `offsets` before `ranged_indirect`.
- Library operations declare no legality clause, so they apply on a key match alone; certification
  remains their check. Knob-range clauses also need recorded facts, the same as every other clause.
- Facts are not inherited by derived contracts.
- **Consequence for tickets 56 and 57.** The repository records hold no legality facts yet. On real
  records, a gem5 `regions: query` campaign therefore refuses with every BFS clause listed as
  "no recorded fact" until someone records them on `dx100-bfs-scalar` statements. Native campaigns
  find the two library-operation regions today.
