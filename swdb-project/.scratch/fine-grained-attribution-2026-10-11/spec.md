# Spec: Fine-grained estimate attribution and headroom

Created: 2026-10-11 14:51 ET
Updated: 2026-10-11 22:10 ET (review fix pass: decisions F26-F39 recorded); 2026-10-11 19:18 ET (ticket 08: decision F25 recorded); 2026-10-11 15:11 ET (rewritten to the full spec template after three grilling rounds;
decisions F1–F24 unchanged; test seams confirmed by Yan-Ru); 2026-10-11 15:08 ET (grilling round 3);
2026-10-11 15:04 ET (round 2); 2026-10-11 14:59 ET (round 1)
**Type:** spec
**Status:** ready-for-agent (implementation starts only on Yan-Ru's explicit go-ahead, in a fresh session)
**Blocked by:** None
Owner: Yan-Ru Jhou
Builds on: ADR 0013 (ArchEvolve mode estimates speed) and the closed analytic-eval spec
(`.scratch/lanl-db-analytic-eval-2026-10-06/`).
Map and tickets: [map.md](map.md)

## Summary (read this first)

1. **Problem:** an estimate gives one total time. It cannot say what the rewritten code gained
   or what the untouched code could still gain.
2. **Fix:** a new `swdb attribute` command splits two saved estimates by **code origin**
   (untouched, rewritten, unattributed) and reports per-group gain and the **Amdahl ceiling**.
3. **Headroom:** each region is compared with its **resource floor** and **catalog bound**; the
   **remaining gain bound** ranks regions for the next iteration.
4. **Trust before use:** one real CPU pair (the t75 native BFS candidate) is timed per group.
   The ranking steers the site finder only if the split check passes (within 10 points).
5. **No estimator change, no new counting, no gem5.**

## Problem Statement

Scott (advisor) says the evaluator is too coarse. Yan-Ru agrees.

- The estimator already estimates each exclusive region, but its record answers only "how long
  does the whole call take?"
- So Yan-Ru cannot answer the questions that matter after an agent rewrite:
  - The agent rewrote 60% of the time. How much faster is that 60% now?
  - Did the untouched 40% get slower as a side effect?
  - How much could the untouched 40% still gain in a later iteration?
  - Is the rewritten part already at its limit, so further work there is wasted?
- Without these answers, the paper has no breakdown figure, and the agent loop picks the next
  region without knowing where the remaining time is.

Worked example. Baseline 100 s. The rewritten part drops from 60 s to 30 s; the untouched 40 s
stays. Total 70 s, a 1.43× speedup. Even if the rewritten part dropped to 0 s, the best possible
is 100 / 40 = 2.5×. The untouched 40% is now the limit, so the next iteration should target it.

## Solution

A new **attribution report**, produced by one command from saved records only:

- **Inputs:** a baseline estimate and a candidate estimate (same target description, same input),
  their two source snapshots, and from iteration 2 on, the previous accepted candidate.
- **What it does:**
  1. Computes rewrite sites from the source diff.
  2. Labels every region with a code origin.
  3. Splits time into groups and reports realized gain, untouched drift and the Amdahl ceiling.
  4. Computes each region's headroom against two limits and ranks regions by remaining gain
     bound.
- **Where it goes:** a new record kind, indexed into SQLite, readable by Scott's figure and by
  the site finder.
- **Trust gate:** one real CPU pair is timed per group. If the measured split disagrees with the
  estimated split, the report is marked `split_unverified` and nothing uses its ranking.

## User Stories

**Seeing the split**

1. As Yan-Ru, I want each candidate region labeled untouched, agent-rewritten, library call,
   intrinsic, offload command or unattributed, so that I know where every second comes from.
2. As Yan-Ru, I want the rewritten part's baseline and candidate seconds side by side, so that I
   see what the rewrite itself gained.
3. As Yan-Ru, I want the untouched part re-estimated on the candidate, so that a rewrite that
   slows nearby code shows up as drift.
4. As Yan-Ru, I want each group's share of the baseline total, so that I see how much of the
   program the agent actually touched.
5. As Yan-Ru, I want the Amdahl ceiling (baseline total ÷ untouched candidate seconds), so that I
   know the most any further work on the rewritten part could give.
6. As Yan-Ru, I want total speedup in the same report, so that the split and the whole are read
   together.
7. As Yan-Ru, I want unattributed time shown as its own group, so that time I cannot place is never
   hidden inside another group.
8. As Yan-Ru, I want a flag when unattributed time exceeds 10% of the total, so that I know when
   the split is weak.
9. As Yan-Ru, I want an unknown region to make its group's numbers unknown with the reasons
   listed, so that a missing value never looks like zero.
10. As Yan-Ru, I want group medians computed per trial and never rescaled to the total, so that the
    report follows the same trial rule as the estimate.

**Rewrite sites**

11. As Yan-Ru, I want each contiguous changed span of the diff treated as one rewrite site, so that
    gains are grouped by what the agent changed, not by loop IDs that differ between versions.
12. As Yan-Ru, I want two sites that share a region merged into one, so that no region's time is
    counted twice.
13. As Yan-Ru, I want a region only partly inside a site counted as rewritten and flagged `mixed`,
    so that the loss of precision is visible.
14. As Yan-Ru, I want untouched regions matched across inserted or deleted lines, so that a shifted
    function is not mistaken for a rewritten one.
15. As Yan-Ru, I want inlined code labeled by its own file and line, so that a rewritten helper
    inlined into an untouched caller still counts as rewritten.
16. As Yan-Ru, I want loops without a catalog loop ID still labeled by file and line, so that CPU
    estimates (all such loops today) are not all unattributed.
17. As Yan-Ru, I want SWDB to compute the diff from the two source snapshots itself, so that the
    split never depends on a stored diff against the wrong base or on a remote path.

**Iterations**

18. As Yan-Ru, I want gain this iteration measured against the previous accepted candidate, so that
    I see what the latest rewrite added.
19. As Yan-Ru, I want cumulative gain measured against the original baseline, so that I see the
    total progress.
20. As Yan-Ru, I want each region to record the iteration that last changed it, so that a region
    rewritten in iteration 1 is not counted as new work in iteration 2.

**Headroom and ranking**

21. As Yan-Ru, I want each region's resource floor (counted useful work at the target description's
    own rates, without latency or overheads), so that I know the best any rewrite could do.
22. As Yan-Ru, I want the resource floor never to use a theoretical peak, so that it follows the
    estimator's bandwidth convention.
23. As Yan-Ru, I want each region's catalog bound (the best estimate a site-finder-matched entry
    reaches on that region's counts), so that I know what a known rewrite could reach today.
24. As Yan-Ru, I want an entry that needs counts only a rewrite produces (such as offload address
    counts) reported as unknown with a named reason, so that it never looks free.
25. As Yan-Ru, I want a region with no matching entry reported as `no_catalog_match`, not as
    infinite headroom.
26. As Yan-Ru, I want headroom always to name which limit it uses, so that the two are never
    confused.
27. As Yan-Ru, I want the rewritten part's headroom too, so that I know when it is already at its
    limit.
28. As Yan-Ru, I want regions ranked by remaining gain bound, with floor-only regions listed after
    and never mixed with them, so that the ranking compares like with like.
29. As Yan-Ru, I want the remaining gain bound named and described as an upper limit, so that the
    paper never claims an expected value.

**Agent loop**

30. As the agent loop, I want the site finder to order its eligible regions by remaining gain bound,
    so that rewrites target the largest remaining time first.
31. As the agent loop, I want eligibility unchanged by the ranking, so that the ranking cannot
    admit a region a contract does not allow.
32. As the agent loop, I want the site finder to ignore a `split_unverified` report and keep today's
    order, so that an untrusted split never steers rewrites.
33. As a rewrite provider, I want my prompt unchanged by this feature, so that existing prompt
    hashes and blinding still hold.

**Trust check and paper**

34. As Yan-Ru, I want one real pair (the t75 native BFS candidate and its baseline) estimated on the
    exact input that is timed, so that the first real report is checkable.
35. As Yan-Ru, I want both estimates saved before any timing, with their order recorded, so that the
    check is prospective (LR-02).
36. As Yan-Ru, I want each group timed natively with the existing BFS region thread-CPU counters, so
    that the measured split comes from the same machine without new instrumentation.
37. As Yan-Ru, I want the pass rule (every group within 10 percentage points) fixed before timing, so
    that the result cannot be tuned afterward.
38. As Scott, I want a breakdown figure (rewritten gain, untouched drift, Amdahl ceiling, headroom)
    with its split-check verdict, so that I can judge how much to trust it.
39. As Yan-Ru, I want an input mismatch between the two estimates or the timing refused, so that a
    share comparison is never made across inputs.
40. As Yan-Ru, I want a negative report naming the missing pieces if an estimate comes out unknown,
    so that the ticket can still close on a supported result (LR-01).

**Records and database**

41. As Yan-Ru, I want attribution reports saved as their own record kind and validated by
    `swdb validate`, so that they follow the same rules as every other record.
42. As Yan-Ru, I want attribution reports indexed into SQLite tables with the `swdb_` prefix, so that
    the figure and the site finder can query them under the LANL-shaped database rule.
43. As a reader, I want each report to pin the hashes of both estimates, both snapshots and the
    target description, so that it can be replayed and cannot drift.
44. As Yan-Ru, I want the same inputs always to give a byte-identical report, so that reports can be
    compared and cached.

## Implementation Decisions

**Modules**

- **Attribution command (new, deep module).** One public command takes the inputs above and writes
  one attribution record. Inside it: diff and rewrite sites, code-origin labeling, group
  composition, headroom and ranking. Only the command's input and output are a contract; the
  internal split may change.
- **Record kind and schema (new).** `swdb.attribution.v1`, with a validator and SQLite indexing,
  following ADR 0002 (YAML is the master copy, SQLite is generated).
- **Site finder (modified).** Reads the latest attribution report for the campaign's kernel and
  target and uses it only as an ordering key. Eligibility, legality and the recorded reasons are
  unchanged.
- **Estimator, mechanism models, count runtime, rewrite-provider prompts:** unchanged. The resource
  floor reuses the existing compute and streaming-bandwidth models as they are. No frozen protocol
  needs refreshing.

**Decisions F1–F39** (Yan-Ru, 2026-10-11; numbers kept for references in tickets; F25 recorded by ticket 08; F26–F39 recorded by the review fix pass on `fga/review-fixes`)

| # | Decision |
|---|---|
| F1 | A rewrite site is one contiguous changed span of the diff, mapped to regions by file and line. Regions overlapping two sites merge them. |
| F2 | Code origin labels: untouched; agent_rewritten; library_call (a typed-library operation inside a site); intrinsic; offload_command (bound by the functional observation contract); unattributed (unmodeled calls, and regions with no source file and line). Precedence: offload_command > intrinsic > library_call > agent_rewritten. A loop lacking a catalog loop ID still gets its origin from file and line. Baseline libc/C++ library calls are untouched. |
| F3 | Untouched regions are re-estimated on the candidate; drift = candidate ÷ baseline. |
| F4 | Group seconds are summed per trial, then the median is taken per group. Group medians are never forced to add up to the total. |
| F5 | Per group: baseline seconds, candidate seconds, share, realized speedup, drift (untouched). Whole program: total speedup and Amdahl ceiling. Shares are in seconds; bytes and operations are diagnostics. |
| F6 | Two limits per region. Resource floor = max(compute bound, useful-bytes bandwidth bound) at the target description's own rates, without latency, row, queue or overhead terms, never a theoretical peak. Catalog bound = lowest estimate among matched entries whose mechanism models can run on the region's baseline counts; otherwise unknown (`needs_rewritten_counts`) or `no_catalog_match`. Headroom = estimate ÷ named limit. |
| F7 | Ranking by remaining gain bound = share × (1 − catalog bound ÷ estimate). Floor-only regions follow, ranked by floor headroom. Unknowns are never ranked against knowns. |
| F8 | Any unknown region makes its group's fields and dependent whole-program fields unknown, with reasons. |
| F9, F16 | First real pair: the t75 native BFS candidate (`extensa-native-bfs-20261005-a8.it1.kronecker.a0`, contract `bfs_tdstep_frontier_staging`) and its baseline, estimated with the BFS g16/g17 CPU target description. |
| F10 | Both limits are analytic. No gem5 run or number enters the report (ADR 0013). |
| F11 | Two readers with equal weight: Scott's figure and the agent loop. |
| F12 | Version 1 reports a limit only; no agent success probability. |
| F13 | From iteration 2: gain this iteration (against the previous accepted candidate) and cumulative gain (against the original baseline). Each region records the iteration that last changed it. |
| F14 | A partly rewritten region counts as rewritten, flagged `mixed`. |
| F15 | The split itself is checked, not only the total, by timing each group natively for one CPU pair with the existing BFS region thread-CPU counters. |
| F17 | SWDB computes both diffs from the source snapshots; the stored candidate diff is never read for attribution. |
| F18 | Both estimates and the timing use the exact same input, or the report is refused. |
| F19 | Split check passes when every group's measured and estimated shares differ by at most 10 percentage points. Fixed before timing. |
| F20 | The ranking reaches agents only through site-finder order. Headroom in the prompt is a later with/without experiment, after F19 passes. |
| F21 | Site-finder regions join estimator regions by file and line overlap; partial overlap is flagged `mixed`. |
| F22 | New record kind under the records tree plus generated `swdb_` SQLite tables. |
| F23 | A failed split check saves the report as `split_unverified`; the site finder ignores its ranking. |
| F24 | Unattributed time above 10% of the total is flagged, not refused. |
| F25 | An entry's mechanism models come from mapping its `uses_intrinsics` to the target description's offload mechanisms (through `hardware_operations`). Models that lack counts (`address_stream_counts`, `accelerator_calls`) give unknown `needs_rewritten_counts`; models runnable on the baseline counts give a numeric bound; no match gives `no_catalog_match`. |
| F26 | Real-pair baseline (tickets 03, 09): pair the t75 candidate with a source-baseline candidate of the scalar-only snapshot `bfs-dx100-scalar-only-20260929-a1.source` (reuse `typed-library-bfs-scalar-profile-20261003-a1.baseline` if it matches, else make one with `swdb baseline-candidate`), for both the estimate and the ticket 09 timing; not the full-fork a8 baseline `bfs-native-pilot-20260925-dx10018-a1.baseline`. |
| F27 | Real-pair protocol (ticket 03): freeze a fresh estimate protocol for the real pair on the pinned code commit, then estimate both sides with no code change in between. Existing frozen protocols and their records stay untouched; `estimate_protocol` is not changed. |
| F28 | `dx100.mmio.v1.*` and `dx100.functional.v1.*` operations are never mapped onto each other. An MMIO-intrinsic entry against a functional description gives `no_catalog_match`; offload entries get no catalog bound until a rewrite exists (Out of Scope: offload catalog bounds need a projection model). |
| F29 | The remaining gain bound clamps at 0: an entry slower than the region's estimate offers no gain, the same as a region already at its bound (F7 reads share × max(0, 1 − catalog bound ÷ estimate)). The clamp is stated in the record's `ranking_rule`. Ties (for example at 0) go by floor headroom, largest first, null last, then by region ID. |
| F30 | F21 as written: each site-finder region's lines move from its revision (a saved source record of that revision, `--site-finder-source`) into each tree by their offset inside the named function (definitions found at any column, counted in order). They are kept when the function's text matches in both trees or the moved lines stay inside the tree's definition. Overlap joins; `mixed` = some line of the region lies outside every joined span. Only when the lines cannot be moved does the whole function join, recorded as `join: function` with its reason, never silently. |
| F31 | A site-finder region that cannot be placed in a tree (no function in its ID, file or function missing, ambiguous definitions) is listed with its reason, and every region it could have joined has an unknown bound `site_finder_unplaced` unless another entry gives a known one; never `no_catalog_match`. |
| F32 | An application with no `content_sha256` is `entry_unhashed` (unknown), never evaluated against whatever entry version is current. |
| F33 | (F2) Time inside unmodeled calls belongs to `unattributed`, per trial: a region's call rows (`unmodeled_calls`, or rows that cover calls) move to the unattributed group, and the region's group keeps the region recomposed without them. |
| F34 | (F2) `offload_command` needs a command the pinned description's functional observation contract names. A region inside a site that executes any other command is `unattributed`, reason `unbound_offload_command`. |
| F35 | (F6) The catalog bound runs on baseline counts: a baseline row on its own, a candidate row on its `matched_region`'s; a candidate row with no matched region is unknown, `no_baseline_counts`. |
| F36 | (F7) A region whose catalog bound is unknown (`needs_rewritten_counts`, `unknown_catalog_entry` incl. `entry_changed`/`entry_unhashed`, `no_baseline_counts`, `site_finder_unplaced`) ranks in the `unknown` tier with its reason, never in `floor_headroom`. Only `no_catalog_match` (and `no_site_finder`) regions enter the floor tier. |
| F37 | (F20, F23) The site finder's "latest" report is the one with the newest inputs (a report's `created` is the latest `updated` date of its inputs, not its generation time), then the greatest record ID. The ordering block records `ORDERING_QUERY_SHA256` beside the rule. |
| F38 | Catalog-bound entries run each trial with that trial's own `unmodeled_calls`, as the estimator does; a single-run characterization uses its aggregate calls. |
| F39 | (F13) Only labels of comparisons the report shows pin catalog entries: last-changed iterations read no catalog, so a call seen only in an earlier diff pins nothing. Each diff is labeled once. |

**Record shape (decision-level, not final field names)**

- Identity: hashes of the baseline estimate, candidate estimate, previous candidate (if any), both
  source snapshots and the target description; the input ID.
- Rewrite sites: each with its baseline and candidate line spans, replaced and replacing regions,
  and the iteration that made it.
- Regions: ID, code origin, `mixed` flag, last-changed iteration, baseline and candidate seconds,
  resource floor, catalog bound with its entry or unknown reason, and both headrooms.
- Groups: the F5 fields for both F13 baselines.
- Whole program: total speedup, Amdahl ceiling, unattributed flag.
- Ranking: ordered region IDs with their remaining gain bound or floor headroom.
- Split check: absent, `passed` or `split_unverified`, with the measured shares and the rule.

## Testing Decisions

**What a good test is here:** it calls the public command on fixture records and checks the
written record against hand-computed values. It never imports internal helpers, so the internals
can change freely.

**Seams** (confirmed by Yan-Ru, 2026-10-11)

1. **The attribution command (the only new seam).** Fixture estimates and snapshots in, record out,
   then `swdb validate` and the SQLite index. Cases:
   - one rewrite site; two sites merged by a shared region; a partly rewritten region (`mixed`);
   - an untouched function shifted by inserted lines;
   - an inlined rewritten helper in an untouched caller;
   - a loop without a catalog loop ID that still gets a real origin;
   - an offload command inside a site (precedence);
   - the 100 s / 60% / 40% worked example, with hand-computed shares, speedups and ceiling;
   - one unknown region nulling its group, with reasons;
   - unattributed above 10% flagged;
   - an iteration-2 case reporting both baselines;
   - resource floor below the estimate; a missing rate giving an unknown floor;
   - catalog bound with an evaluable entry, a `needs_rewritten_counts` entry and no match;
   - input mismatch refused; identical inputs giving a byte-identical record.
2. **The existing site finder seam.** The order follows the ranking; eligibility is unchanged; a
   `split_unverified` report leaves today's order.

**Not a unit test:** the first real pair runs on mbit10 and is checked by its saved records and the
F19 verdict.

**Prior art:** the analytic command tests (fixture records, the public command, hand-computed
expected values, then validation) and the site finder tests. Fixture counts carry
`contract_fixture` evidence and are never application evidence.

## Out of Scope

- Changing the estimator, mechanism models, count runtime or frozen protocols.
- Headroom in the rewrite-provider prompt (F20: a later with/without experiment).
- An expected-value gain with agent success rates (F12).
- Catalog bounds for offload entries before a rewrite exists (needs a projection model).
- Splitting a partly rewritten region by operation share (F14).
- Extensa-mode agreement studies and any gem5 use.
- Per-region native timing beyond the one BFS pair.

## Further Notes

- **Why this is cheap:** the estimator already keeps per-region rows with their bounds; the report
  only labels and regroups them.
- **Main risk:** the t75 candidate's estimate may come out unknown. Then ticket 03 closes on a
  negative report, as ticket 17 did, and the split stays unverified.
- **Paper framing:** report the remaining gain bound as an upper limit; the split-check verdict goes
  next to every breakdown figure.
- **Glossary terms added 2026-10-11:** rewrite site, code origin, resource floor, catalog bound,
  headroom, remaining gain bound.
