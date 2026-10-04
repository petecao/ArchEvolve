# 48 — Mode tags, team-boundary refusals and candidate-artifact promotion

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md))
**Type:** slice
**Status:** resolved
**Blocked by:** 11, 15, 47 (all resolved)
**Spec:** `../spec.md`

**What to build:** Extensa records are tagged at creation and kept out of team results until promoted.

## Acceptance

- [x] Every record schema gains two optional fields, `mode` (enum `extensa`) and `campaign` (a campaign ID matching `extensa-(native|gem5)-bfs-[0-9]{8}-[a-z][0-9]+`), documented in the format reference. Absent means ArchEvolve mode. `campaign` is required when `mode` is present and forbidden otherwise.
- [x] The writer sets both fields only when a record is created. A test shows that rewriting an existing record to add or change either field is refused, and that all records in `records/` revalidate unchanged.
- [x] No candidate-artifact record has a certification-level field (schema refuses it). A query helper derives the level (`certified` or `uncertified`) from certification records. A failed certification derives `rejected`.
- [x] `swdb compare-evaluations`, `swdb handoff-message` and `swdb bfs-coverage` refuse an input record tagged `mode: extensa` unless a review record promotes its candidate artifact. Each refusal names the record. Tests use fixture records.
- [x] `swdb promote` accepts a candidate artifact tagged `mode: extensa`. It records Yan-Ru's review, then derives a team protocol from the named current team protocol with only the artifact's workload class. The re-evaluation request it writes cites the Extensa campaign as origin. Until that re-evaluation's comparison exists, team commands still refuse the artifact (fixture test, end to end through `swdb`).
- [x] The ArchEvolve-mode test showing that a valid regression returns without tuning still passes.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).

## Answer

Resolved 2026-10-03 20:42 ET (agent, under Yan-Ru's standing implementation approval).

What was built:

- `schemas/envelope.schema.json`: optional `mode` (enum `extensa`) and `campaign` (pattern
  `extensa-(native|gem5)-bfs-YYYYMMDD-<letter><n>`) on every record kind; each requires the other.
  Documented in `docs/reference/format-v0.4-extensa.md`.
- `swdb/writer.py`: a replace that adds, removes or changes either tag is refused, nothing written.
- Candidate schema already refuses unknown keys, so a stored `certification_level` fails validation
  (test). `swdb candidate-level CANDIDATE` (in `swdb/extensa_boundary.py`) derives
  `certified` / `uncertified` / `rejected` from certification records (any failed one: rejected).
- Team boundary (`swdb/extensa_boundary.py`, one call each in `bfs_protocol.compare_evaluations`,
  `handoff.message`, `bfs_coverage.report`): the record closure (every record reachable through ID
  references) of each input is checked; a tagged record is refused, naming it, unless it is a
  candidate (or its proposal / source snapshot) promoted by a candidate review AND a non-rejected
  comparison under the review's derived protocol exists. `compare-evaluations` under the derived
  protocol itself is the allowed re-evaluation. An Extensa-tagged protocol accepts only records of
  its own campaign (campaign-internal comparisons). Coverage refuses named inputs and scans a team
  view without refused records.
- `swdb promote CANDIDATE --protocol TEAM_PROTOCOL --workload-class CLASS --output DIR`: Yan-Ru
  only; rejected (failed-certification) candidates refused; derives and freezes a team protocol
  with only the workloads whose family is CLASS; writes one evaluation request per workload citing
  the campaign, candidate, review and team protocol under `origin`; writes a `review` record with
  `target_kind: candidate`, `origin`, `reevaluation` (`schemas/review.schema.json`; library reviews
  keep the certification `x-ref`). Evidence: the candidate's certification or its campaign summary.
- Tests: `tests/test_extensa_boundary.py` (16 cases, fixture records only), including the end-to-end
  promotion: refused before promotion, still refused after promotion, accepted only after the
  re-evaluation comparison through public `swdb evaluate` / `compare-evaluations`.
  Regression: `test_bfs_protocol`, `test_bfs_coverage`, `test_bfs_package_handoff`,
  `test_typed_library`, `test_writer_persistence`, `test_format_doc`, `test_format_versions`,
  `test_bfs_rewrite` (incl. "regressions do not trigger tuning"), `test_records`: 192 passed.

Assumptions (agent-decided, revisable):

- "Promoted" means a current candidate review by Yan-Ru bound to the candidate artifact sha256.
- Workload class = workload `definition.family`.
- The re-evaluation request is a file (no request record kind exists); the review pins its sha256.
- Tagged evaluations, comparisons and protocols never enter team results even after promotion;
  only the team re-evaluation's untagged records do.
