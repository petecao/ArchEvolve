# Ticket14 isolated-catalog feasibility — 2026-10-07

Read-only at C `f893fed400347ed23d92e917d8bde21b75e5375d`, portable bundle F6 `f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3`; source inspected in clean owned ticket14 worktree at `9e555f5`. No Store/catalog construction, tests, source/control edits, forecast values, native/provider execution, real PR replay or SSH. Active model-a3 and selected ticket14 controls are untouched.

**Recommendation: retain the complete copied catalogue for current acceptance.** Public `--records` plus the existing forward-closure helper can support a future per-case package, but that is not a demonstrated equivalent execution boundary. Removing unrelated large estimates plausibly reduces metadata work; it can also change admission/refusal independently of scientific costs.

## What the current seams preserve, and what they miss

All source references below are relative to `swdb-project/` at C.

| Seam | Exact behavior and implication |
|---|---|
| `extensa_boundary.py:175–201` | `closure` recursively follows any string equal to an existing record ID. It silently drops absent initial IDs and ignores strings absent from its input Store. Compute against the full baseline, require all requested roots, and copy reached records byte-for-byte; computing against an already reduced Store can hide references. It does not compute reverse/global/filesystem dependencies. |
| `estimate_protocol.py:32–62,102–118` | Freeze pins the target snapshot, all target forward dependencies, explicit inputs/sources and optional band dependencies. Frozen validation requires exact dependency hashes and recomputed closure equality. The CPU target's four admitted BF/BC characterizations/calibrations remain required even for PR; do not trim allowlists or target content to shrink the package. CPU-band closure is separately pinned (`cpu_error_band.py:228–257`). |
| `archevolve.py:52–134` | The team guard resolves referenced strings through the supplied Store and recursively checks them, including mandatory calibration sources. It is not itself an unrelated-team-claim scan. Dropping a resolvable ID can alter traversal/refusal; exact closure and negative controls are necessary. Extensa owner/promotion/re-evaluation APIs additionally use reverse/global queries (`extensa_boundary.py:204–246`); their applicability must be audited per command, not assumed away generically. |
| `bfs_protocol.py:182–229` | Public validation and creation scan all records of the kind for logical `requested_id`/version conflicts; superseding also scans comparisons. An old conflicting protocol is not necessarily forward-reachable from a fresh request. A reduced catalogue can accept a name that the full one refuses. Other rules have global peer checks, e.g. strategy uniqueness (`rules.py:479–482`); relevance depends on included record kinds. |
| `validate.py:23–68`, `writer.py:96–135` | Public validation checks every local record, references, semantic rules, normative library and campaign configuration. Each writer independently checks the whole *local* catalogue under its lock and refuses ID/path collisions. Subset success is not complete-catalogue success; merging additions must preserve prior bytes and pass full public validation before acceptance. |
| `library.py:214–238`, `campaign.py:213–237`, `offload_observation.py:210–233` | External records default to sibling `library` and `campaigns/extensa`; missing directories can skip validation. Functional binding also directly reads `paths.HOME/library`. Preserve the actual full workflow's filesystem/defaults and all normative entry pins; merely passing a record subset is insufficient. Separate per-case parent/build directories are needed for index/lock isolation (`db.py:82–94`). |

`analytic.py:600–688` calculates from the selected characterization, target, frozen protocol, explicit optional baseline/band and trial reconciliation, then commits through the writer. Thus scientific composition might be identical with a proven sufficient package. The unsupported step is equating that package's admission/validation with the complete workflow. Explicit YAML-path fallback (`analytic.py:123–140`) is not a substitute for registered-ID resolution or missing-reference checks. Characterization's global profile reuse scan is a separate counting-time concern (`analytic_binding.py:79–94`), not evidence that present estimate execution performs that scan.

## Meaningful future differential gate

1. Start from one fully validated, immutable complete baseline; record its full inventory, selected roots, exact target/band closure and both source/sibling normative/default-directory pins. Verify output logical-name/version and path freshness against the full baseline. Never redact or stub native count facts or dependency records.
2. Use small independent public freeze/estimate fixtures first: compare full versus isolated admission and exact scientific outputs, including every trial/region/formula input, unknown reason, binding, reconciliation and parameter-report fact. Add refusal controls for missing/tampered dependencies, team-tagged references, logical-name/version collisions, library/campaign omissions and applicable global peer constraints. Protocol `frozen_at` participates in identity (`bfs_protocol.py:162–177`), so equal-ID testing needs a controlled fixture clock; actual independent freezes must retain their own correct identities, not waive seals.
3. Only after those gates, request a bounded metadata-only differential on representative accepted CPU legacy, PR unsupported-transfer, DX functional and MAPLE scopes at exact C/F6. Verify complete semantic equivalence, not just whole-call seconds. No such differential has run here.
4. Merge only fresh additive outputs into an external complete catalogue, preserving every prior file and all unique IDs, then run full public validation and the unchanged all-nine report. Full-catalogue acceptance remains the final gate. This is a future administrative execution-policy change requiring reviewed packaging/custody proof, not an optimization already established by `closure`.

## One finite conservative cap proposal for current full-catalogue execution

Parent's filesystem-only receipt at06:42:56Z reports base665 YAML324,332,488B, current669 YAML379,897,957B, first BFg16 estimate53,583,441B. Parent reports successful BC freeze1266.086438s and first BF estimate729.741s. Remaining estimate/catalogue sizes and stage costs are unknown. The256MiB parse cache counts canonical JSON, not YAML, and clears on overflow (`access.py:53–91`); separate CLI processes start cold. Neither these sizes nor successful times prove linear scaling or a future upper bound. Detailed pass counts are in `/private/tmp/lanl-ticket11-future-metadata-cost-audit-20261007.md`.

A single prospective administrative set aligned with the parent CPU choice is:

| Control | Proposed seconds |
|---|---:|
| Local PR freeze / estimate / checker | 3600 / 2400 / 2400 |
| Local PR enclosing envelope | 10000 (8400 stage sum +1600 reserve) |
| Nine-report each freeze / each estimate | 3600 / 2400 |
| Nine-report initial and final validation / reporter | 2400 each /2400 |
| Nine-report enclosing envelope | 66000 (61200 stage sum +4800 reserve) |
| Exporter's full validation | 2400 |

These are finite **unproved administrative ceilings**, not predicted runtimes or scientific budgets. Native900, source C/F6, exact inputs/ROI/threads/trials, observed counts, mechanisms, parameters, allowlists, unknowns and cleanup/lease/custody guards remain unchanged; local PR and nine-report stages execute no native/provider work. If selected, create distinct cap-only controls with explicit byte/AST reversal and compact existing mocks before dispatch. No controls were prepared or changed by this audit. Awaiting final model sizes could support a different later choice; the current proposed set makes no guarantee for arbitrary catalogue growth.
