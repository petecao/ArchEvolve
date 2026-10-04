# 48 — Mode tags, team-boundary refusals and candidate-artifact promotion

Created: 2026-10-03
Updated: 2026-10-03 ET (revised by ticket 47; [design decisions](../extensa-design-2026-10-03.md))
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 11, 15, 47 (all resolved)
**Spec:** `../spec.md`

**What to build:** Extensa records are tagged at creation and kept out of team results until promoted.

## Acceptance

- [ ] Every record schema gains two optional fields, `mode` (enum `extensa`) and `campaign` (a campaign ID matching `extensa-(native|gem5)-bfs-[0-9]{8}-[a-z][0-9]+`), documented in the format reference. Absent means ArchEvolve mode. `campaign` is required when `mode` is present and forbidden otherwise.
- [ ] The writer sets both fields only when a record is created. A test shows that rewriting an existing record to add or change either field is refused, and that all records in `records/` revalidate unchanged.
- [ ] No candidate-artifact record has a certification-level field (schema refuses it). A query helper derives the level (`certified` or `uncertified`) from certification records. A failed certification derives `rejected`.
- [ ] `swdb compare-evaluations`, `swdb handoff-message` and `swdb bfs-coverage` refuse an input record tagged `mode: extensa` unless a review record promotes its candidate artifact. Each refusal names the record. Tests use fixture records.
- [ ] `swdb promote` accepts a candidate artifact tagged `mode: extensa`. It records Yan-Ru's review, then derives a team protocol from the named current team protocol with only the artifact's workload class. The re-evaluation request it writes cites the Extensa campaign as origin. Until that re-evaluation's comparison exists, team commands still refuse the artifact (fixture test, end to end through `swdb`).
- [ ] The ArchEvolve-mode test showing that a valid regression returns without tuning still passes.

## Comments

- 2026-10-03 ET: readied by ticket 47 under Yan-Ru's 2026-10-03 delegation (agent-decided; revisable).
