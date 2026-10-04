# Independent hardware internal annotation review — 2026-10-03

Reviewed integration: **`c570772253a10298c3891bdf6f3594db6d4e8a65` — scoped acceptance, no blocking findings.** Starting commit: `ecaf4abaab1702b986a9ff7d8652f62229182c76`. Comparison baseline: `ef155cd621c466000b5beb910eb66a217a72b50d`. Scope is catalog source/evidence boundaries, annotation rendering and invariant operation support; no production files were modified by this reviewer.

Primary inspection finds no blocking contradiction in the integrated annotations. The exact integrated catalog equals the reviewed proposal overlay with its PHI ablation excluded and revision set to 0.1.5: seven records, 39 operations, 84 claims and 30 sources. This acceptance concerns descriptive evidence and representation, not hardware correctness, mapping legality, liveness or performance.

## Evidence and source scope

`source-checks.json` records fresh hash checks of the 14 DX100 bundle files (author PDF and 13 pinned code files), plus the three other primary PDFs. All match. Prior acquisition and bibliographic audits were reused. Primary passages and actual changed claim/annotation fields were independently inspected; no full corpus scan, download, simulation or benchmark was performed.

| Record | Checked locators | Review result |
|---|---|---|
| DX100 paper | Author edition §3.2 pp.4–5/Figs.3–4, §3.5 p.6, §3.6 pp.6–7 | Physical slice/row/column grouping, backward word associations, fixed request arbitration, original-index result placement and Fill-time H match. Exact reuse/completion details stay unknown. The author edition is identified separately from unverified publisher fulltext. |
| DX100 public model | IndirectAccess.cc 113–210, 243–528, 621–809, 868–927, 1158–1173; Tables.cc 142–217, 241–500; IF.cc 185–336; Port.cc 31–581; MAA.cc 261–334, 605–621; MAA.py 13–39; associated header and port locators | Failed insertion retains the iteration; same-row overflow can allocate another record; duplicate consumers share an unsent physical line. Build cycles slices and groups records by grow; producer wait alone does not start Build. Tick eligibility and port rejection constrain sends. Responses consume all associations; a row becomes reusable after all its lines return. Public forward links/packet-time snooping are not paper backward links/Fill-time H. |
| Terminus CAS and deferred variants | PDF pp.5–10 §§IV–VI/Figs.5,7–8,12–15/Table II; pp.12–13 §§VII-E–F/Figs.22–23 | Partition SWMR and ready-head arbitration, taskID/ROB result order, memory output-space admission and completion buffering are distinct. Deferred tasks keep their partition; CPU response/release is separate from engine CAS and global shared-memory synchronization. Reference capacities and cohort sensitivity do not create legal tuning ranges. |
| Prodigy | Downloaded PDF pp.7–10 §§III-B3,IV,VI-A/Figs.9–12; pp.13–14 §§VI-F–G | PFHR line-address CAM/bitmap identity, non-leaf allocation, bounded lookahead and trigger-demand cancellation match. Busy tracking drops optional work. No required gather result or CPU update completion is supplied. Exact stale-fill/reuse/duplicate-match protocols remain unspecified. Cover-page offset is preserved. |
| SpZip Push | PDF pp.3–4 §II-C/Figs.5–7; pp.6–9 §III-B,D,E/IV/Figs.10–11/Table I; p.12 §V-C/Figs.20–21 | Operator readiness needs input/output/FU resources, with round-robin selection. Required stream markers/adjacency decompression differ from destination prefetch with no output queue. CPU owns destination atomics. Eight AU lines and 2 KB scratchpad are reference choices. PHI ablations remain outside Push. |

The actual source passages support descriptive mechanisms. They do not prove universal reorder legality, fair scheduling, starvation freedom, transport tag generation protection, CPU fence semantics, private DX100 virtualization or new performance predictions. Existing unknowns are material implementation gaps, not review blockers for a descriptive catalog.

## Narrow advisory

The external proposal's `unknowns.SpZip Push` includes “Context count.” SpZip §III-B, PDF p.6 explicitly specifies 16 operator contexts and 16 queues in its implementation. Record that as a reference choice if this research unknown list is revised; retain uncertainty about queue credit reservation/return and exact context reuse. That research unknown list was not imported into `c570772`, so this is an external research advisory, not a remaining finding against the integrated catalog.

## Validation

`check_boundaries.py` checks the six affected designs against the pre-annotation baseline, preserving operations, support/roles, result/order/completion contracts, parameters and requirements. It verifies source/evidence-edition closure, keeps PHI evidence unattached to Push, and exercises 180 typed queries with role and old-value constraints. Deliberately corrupted catalogs test edition promotion, prefetch-to-gather promotion, CPU-assist-to-executor promotion, and invented legal capacity ranges. These are review-specific checks, not a change to the production validator's documented structural scope.

Observed validation at the exact integration: **PASS**, 180 equivalent queries; seven rejected mutations (including CPU-deferred CAS and Push destination-assistance promotion, same-kind evidence from a different paper, and the actual excluded PHI claim); six comparison YAML/Markdown records preserve authored annotations and exact claims while retaining generated unknowns and unevaluated performance. The focused `test_*mechanism*.py` suite passes **7/7**, including end-to-end handoff/Mermaid rendering without invented wiring or signatures. See `validation.json` and `focused-tests.txt`.

No whole-suite/corpus rerun was performed. Registered worktrees were checked after validation: all were clean except this review's intended untracked directory before its local commit; no generated caches/reports appeared elsewhere. Worktree and external corpus are preserved. This review authorizes no push, group publication or simulator activity.
