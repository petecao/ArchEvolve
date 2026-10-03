# Map: Typed library and DX100 BFS rewrites in ArchEvolve and Extensa modes

Created: 2026-10-03 02:28 ET
**Type:** ticket map
**Status:** ready-for-agent
**Spec:** [spec.md](spec.md)

Statuses: ready-for-agent; ready-for-human (Yan-Ru acts); needs-triage (readied by the Extensa-mode design session, or triggered by an L3 refutation). Tickets marked go-ahead run on mbit10. The user's explicit standing approval on2026-10-03 supersedes repeated approval requests for related dispatches (Q62); actual admission and receipts remain required. The pull request to `main` stays as the archevolve-handoff pull-request ticket, blocked by this feature's last tickets.

## Phase 0–1: tell the team, record the design

| # | Ticket | Status | Blocked by | Go-ahead |
|---|---|---|---|---|
| 01 | [Send the Phase 0 decision note and Josh's statement-name mapping](issues/01-send-decision-note-and-mapping.md) | resolved | — |  |
| 02 | [Peter confirms the license for files ported from Extensa](issues/02-license-confirmation.md) | ready-for-human | — |  |
| 03 | [Decision records ADR 0007–0011 and the archevolve-handoff tracker updates](issues/03-design-session-commit.md) | resolved | 01 |  |
| 04 | [Per-person team update after the decision-record commit](issues/04-team-update.md) | resolved | 03 |  |

## Phase 2a: prefactors

| # | Ticket | Status | Blocked by | Go-ahead |
|---|---|---|---|---|
| 05 | [Prefactor: intrinsic records accept a hardware interface](issues/05-intrinsic-records-accelerator-interface.md) | resolved | 03 |  |
| 06 | [Prefactor: offload strategy effect and the DX100 read-offload strategy](issues/06-offload-strategy-effect.md) | resolved | 03 |  |
| 07 | [Prefactor: provider launcher runs every agent role](issues/07-role-based-provider-launcher.md) | resolved | 03 |  |
| 08 | [Dispatch preflight: disk and memory](issues/08-dispatch-preflight.md) | resolved | — |  |

## Phase 2b: library and certification on the Mac

| # | Ticket | Status | Blocked by | Go-ahead |
|---|---|---|---|---|
| 09 | [Library entry shapes and IDs, checked by swdb validate](issues/09-library-entry-shapes.md) | resolved | 03 |  |
| 10 | [Port Extensa's predicate grammar into the library validator](issues/10-port-extensa-grammar.md) | resolved | 02, 09 |  |
| 11 | [Tracer: certify the gather lowering and its setup intrinsics end to end](issues/11-tracer-certify-gather.md) | resolved | 05, 09 |  |
| 12 | [Strict layer: byte-offset, truncation and memory-region assertions](issues/12-strict-layer-assertions.md) | resolved | 11 |  |
| 13 | [Range loop with continuation and register operands](issues/13-range-loop-and-register-operands.md) | resolved | 12 |  |
| 14 | [Stream load, tile size and pointer, ALU-scalar, and the strict store](issues/14-stream-load-tile-access-alu.md) | resolved | 12 |  |
| 15 | [Derived tier and status, and swdb promote for library entries](issues/15-library-tiers-and-entry-promotion.md) | resolved | 11 |  |
| 16 | [Calibration on the T17-fixed authors' BFS, with the BFS matrix](issues/16-calibration-and-bfs-matrix.md) | resolved | 13, 14 |  |
| 17 | [BFS read-offload rewrite contract and the YAML draft for Peter](issues/17-bfs-read-offload-contract.md) | resolved | 06, 10 |  |
| 18 | [BFS candidate-artifact certification](issues/18-bfs-candidate-certification.md) | resolved | 16, 17 |  |
| 19 | [Submit a patch that ships the lowering header](issues/19-submit-patch-with-library-header.md) | resolved | 11, 15 |  |
| 20 | [Peter's §5 patch with fixes E1–E5, certified](issues/20-peter-section5-patch.md) | resolved | 13, 14, 18, 19, 17 |  |
| 21 | [Send Peter the contract YAML](issues/21-send-peter-contract-yaml.md) | resolved | 17 |  |
| 22 | [Yan-Ru promotes the DX100 entries and the BFS contract](issues/22-promote-dx100-entries.md) | resolved | 15, 20 |  |

## Phase 3: first gem5 result (ArchEvolve mode)

| # | Ticket | Status | Blocked by | Go-ahead |
|---|---|---|---|---|
| 23 | [Read-only gem5 checks: execution case, frontier sizes, parent-gather race](issues/23-read-only-gem5-checks.md) | resolved | 03 |  |
| 24 | [Retention and team-claim records; readers accept pruned files](issues/24-retention-and-team-claim-records.md) | resolved | 03 |  |
| 25 | [swdb prune: dry run, approval and apply](issues/25-prune-listing-and-apply.md) | resolved | 24 |  |
| 26 | [Automatic pruning of bulky raw output (ArchEvolve mode)](issues/26-automatic-pruning.md) | resolved | 24 |  |
| 27 | [Real profile package for the scalar-only snapshot on mbit10](issues/27-profile-package-scalar-only.md) | resolved | 05, 08 | yes |
| 28 | [Freeze the new protocol, submit the patch, run the companion case](issues/28-freeze-protocol-and-companion-runs.md) | resolved | 08, 20, 22, 23, 26, 27 | yes |
| 29 | [Timed gem5 runs, comparison and team summary](issues/29-timed-runs-comparison-summary.md) | claimed | 28 | yes |
| 30 | [Send the first gem5 result and record the team claim](issues/30-send-first-result.md) | ready-for-human | 29 |  |
| 31 | [Fallback contract: the CPU loads the parent value itself](issues/31-fallback-contract.md) | wontfix | 28 | yes |
| 32 | [Clean up existing run output on mbit10](issues/32-retroactive-cleanup.md) | resolved | 25 | yes |

## Phase 4a: profiling agent

| # | Ticket | Status | Blocked by | Go-ahead |
|---|---|---|---|---|
| 33 | [Per-line callgrind collection inside TDStep](issues/33-per-line-callgrind-collection.md) | resolved | — |  |
| 34 | [Per-line callgrind run on mbit10](issues/34-per-line-callgrind-run.md) | resolved | 08, 33 | yes |
| 35 | [Agent-claim storage on statement annotations and access patterns](issues/35-statement-claims-storage.md) | resolved | 03 |  |
| 36 | [swdb annotate, scoring and the statement table for Josh](issues/36-annotate-and-score.md) | resolved | 07, 34, 35 | yes |
| 37 | [Send Josh the statement table](issues/37-send-josh-statement-table.md) | ready-for-human | 36 |  |

## Phase 4b: BC

| # | Ticket | Status | Blocked by | Go-ahead |
|---|---|---|---|---|
| 38 | [Prefactor: kernel plug-in seam, native side](issues/38-kernel-seam-native.md) | ready-for-agent | — |  |
| 39 | [Prefactor: kernel plug-in seam, gem5 side](issues/39-kernel-seam-gem5.md) | ready-for-agent | 23 |  |
| 40 | [BC on the native evaluator (code)](issues/40-bc-native-code.md) | ready-for-agent | 38 |  |
| 41 | [BC native evaluation on mbit10](issues/41-bc-native-run.md) | ready-for-agent | 08, 40 | yes |
| 42 | [BC certification and the derived BC contract](issues/42-bc-certification-and-derived-contract.md) | ready-for-agent | 18, 17, 28, 40 |  |
| 43 | [Yan-Ru promotes the derived BC contract](issues/43-promote-bc-contract.md) | ready-for-human | 42 |  |
| 44 | [BC gem5 completion witness and execution case](issues/44-bc-gem5-completion-witness.md) | ready-for-agent | 39, 40 |  |
| 45 | [BC gem5 evaluation](issues/45-bc-gem5-evaluation.md) | ready-for-agent | 26, 29, 41, 43, 44 | yes |
| 46 | [Library JSON schema and SQLite index](issues/46-library-schema-and-index.md) | ready-for-agent | 42 |  |

## Phase 5: Extensa mode

| # | Ticket | Status | Blocked by | Go-ahead |
|---|---|---|---|---|
| 47 | [Extensa-mode design session](issues/47-extensa-design-session.md) | ready-for-human | 03 |  |
| 48 | [Mode tags, team-boundary refusals and candidate-artifact promotion](issues/48-mode-tags-and-team-boundary.md) | needs-triage | 11, 15, 47 |  |
| 49 | [Port Extensa's machinery](issues/49-port-extensa-machinery.md) | needs-triage | 07, 10, 11, 47 |  |
| 50 | [Tracer: certify one library operation (packing)](issues/50-library-operation-tracer.md) | needs-triage | 02, 11, 47 |  |
| 51 | [Seed the experimental tier from Extensa](issues/51-seed-extensa-families.md) | needs-triage | 50 |  |
| 52 | [Extensa campaign skeleton](issues/52-campaign-skeleton.md) | needs-triage | 07, 48, 49, 24 |  |
| 53 | [Speed rule, per-class verdicts, selection and knob tuning](issues/53-speed-rule-and-selection.md) | needs-triage | 52 |  |
| 54 | [Extensa campaign budgets and pruning](issues/54-campaign-budgets.md) | needs-triage | 08, 26, 52 |  |
| 55 | [Query site finder](issues/55-query-site-finder.md) | needs-triage | 46, 52 |  |
| 56 | [Native-CPU Extensa campaign target for BFS](issues/56-native-campaign-target.md) | needs-triage | 51, 53, 54, 55 | yes |
| 57 | [gem5 Extensa campaign target](issues/57-gem5-campaign-target.md) | needs-triage | 29, 53, 54, 55 | yes |
| 58 | ["Is the specification enough?" experiment](issues/58-spec-enough-experiment.md) | needs-triage | 08, 07, 20, 48 | yes |

## Context pointers

- Q60 intrinsic records widen to accelerator commands: spec, Implementation Decisions > Typed library — [spec.md](spec.md)
- Q61 native selection uses the rewritten baseline: spec, Extensa mode > Speed rule — [spec.md](spec.md)
- Q62 approvals per dispatch or Extensa campaign launch: spec, Further Notes > Approvals — [spec.md](spec.md)
- Q63–Q66 (gem5 point ratios, no region pairs, parent-gather race case, license): spec, Further Notes > "Confirmed 2026-10-03" — [spec.md](spec.md)

- Ticket 11, completed 2026-10-03: Strict C++11 lowerings, independent reference semantics and executable certification receipts are implemented. [11-tracer-certify-gather](issues/11-tracer-certify-gather.md).

- Ticket 12, completed 2026-10-03: Per-thread strict checks reject byte-offset overflow, tile truncation and unregistered memory access. [12-strict-layer-assertions](issues/12-strict-layer-assertions.md).

- Ticket 13, completed 2026-10-03: The register-operand range loop passes cross-tile continuation tests and rejects dropped continuation/wrap. [13-range-loop-and-register-operands](issues/13-range-loop-and-register-operands.md).

- Ticket 14, completed 2026-10-03: Stream, tile access and ALU lowerings certify; the strict store requires a result-tile covering wait. [14-stream-load-tile-access-alu](issues/14-stream-load-tile-access-alu.md).

- Ticket 16, completed 2026-10-03: T17 calibration passes all ten functional matrix cells and rejects all seven applicable control cells. [16-calibration-and-bfs-matrix](issues/16-calibration-and-bfs-matrix.md).

- Ticket 18, completed 2026-10-03: The final exact BFS candidate passes ten matrix cells and sixteen controls, including forged frontier prints. [18-bfs-candidate-certification](issues/18-bfs-candidate-certification.md).

- Ticket 20, completed 2026-10-03: The delivered Peter section 5 patch implements E1-E5 and ships the exact lowering header; tree 991de65287fe1fae3a20412704cccb6140a93f84cc11200032b20214f5174ff1. [20-peter-section5-patch](issues/20-peter-section5-patch.md).

- 2026-10-03: Tickets05,06,09,10,15,17 implementation complete with hash-bound evidence and explicit target assumptions; see each Answer. General autonomous implementation/sync instruction authorizes this batch commit; ADRs remain proposed. Human sends/reviews retain their own receipts.

- 2026-10-03: Tickets08,23–26,33,35 implementation gates pass; their Answers preserve fixture-versus-execution boundaries. Tickets27–29,34,36 have bounded real drivers and await actual admitted runs; see [progress](progress.md).

- 2026-10-03: Ticket19 resolved after50 public library/submit regressions and exact tree reproduction; all four two-axis review findings were corrected and independently rechecked. [Code review](code-review.md) and [promotion packet](drafts/promotion-review.md) bind the fresh receipts.

- Historical local checkpoint, 2026-10-03 ET:22 tickets resolved, six needs-info (03/27/28/29/34/36), eight ready-for-human, one conditional 31. Ticket07 role launcher resolved after complete regression coverage. All 3,679 current cases reconcile to3,643 pass / 36 skip with zero unresolved failure; [verification](verification.json). Six Standards/Spec findings are corrected with final independent passes. The source push approval, actual sends/promotion and real target runs remain open; [progress](progress.md).

- 2026-10-03 08:14 ET: ticket22 resolved after21 actual user-approved promotions, publication8959b4d and remote readback425 valid records/21 certified-shared entries. [Promotion receipts](promotion-receipts.json). Source export block cleared; node0 native/profile sequence assigned under standing related-action approval.

- 2026-10-03 08:21 ET:01 and21 resolved with three real Gmail Sent receipts;03 reconciles the handoff tracker and closes from the actual mapping delivery.04 personal sends released. [Send receipts](drafts/outgoing-2026-10-03/send-receipts-01-21.json).

- 2026-10-03 08:35 ET: ticket04 resolved with three actual personal Gmail Sent receipts. Ticket32 claimed after root reviewed the exact failed-smoke two-file cleanup listing under standing approval.

- 2026-10-03 08:37 ET: both supplemental runtime review axes pass;3,687 current cases reconcile to3,651 pass/36 skip. Six actual sends are recorded. Exact failed-smoke cleanup deleted2files18,039,198bytes and preserved9compact artifacts; metadata export is pending. Current operational state supersedes historical checkpoint wording above; [progress](progress.md).

- 2026-10-03 08:40 ET: ticket32 resolved after the exact two-file apply, preserved compact artifacts,431 valid records, published metadata010bec7, and local Git readback. [Cleanup receipt](evaluation/ticket32-cleanup-receipt.json).

- 2026-10-03 08:51 ET:27/34 actual execution passed from the a2 complete package; final closure waits required Git publication of these records and31 validated TDStep/worker line rows. Source attribution remains explicitly bounded; modeled costs are not gain evidence. [Execution summary](evaluation/profile-a2-success-summary.json).

- 2026-10-03 08:57 ET:27/34 resolved after8506be7 publication and Git readback. Actual28 preparation passed; companion memory remains blocked.36 retains two real failed attempts and is receiving the narrow transport correction.

- 2026-10-03 09:01 ET:30/37 resolved;27/34 actual package and28 builds are published8506be7. Both supplemental provider transport review axes pass; affected tests continue before actual36 attempt3. Companion/timed memory remains gated on actual36GiB node-local MemFree. [Current progress](progress.md).

- 2026-10-03 09:03 ET: provider transport fix passes both review axes and all45 affected cases; current complete local regression coverage is3,654 pass/36 skip across3,690 identities. Publication and fresh actual36 attempt3 follow.

- 2026-10-03 09:19 ET:36 resolved after actual guarded attempt3, independent score/isolation audit and exact19-path metadata publication/readback6c65bdf. Spearman0.492569/top-three2of3 are simulated-line attribution scores, not native bottleneck/gain evidence. [Actual table](evaluation/annotation-a3/josh-statement-table.md).37 reviewed delivery is being prepared.

- 2026-10-03 09:23 ET: both final library-state review axes pass; all50 affected cases pass and current identity coverage is3,705 (3,669 pass/36 skip). Corrected local state is21 shared/certified with unchanged normative/review pins.37 is claimed for the exact reviewed institutional send after source publication.

- 2026-10-03 09:29 ET:37 is needs-info after automatic approval review rejected the exact send to Josh, requiring specific human payload/destination approval. Zero Sent matches, no confirmed delivery and no retry. The reviewed draft and blocked-action receipt are preserved; 31 of 37 tickets are resolved. [Ticket37](issues/37-send-josh-statement-table.md).

- 2026-10-03 10:40 ET: Yan-Ru took ownership of ticket37 delivery and instructed the agent to ignore sending for now. Ticket37 is ready-for-human; the agent will not retry or ask for send approval. The user's memory-admission question triggered a fresh read-only selected-node audit: plentiful inactive file cache shows that MemFree-only refusal is not proof of insufficient allocatable RAM. Budget and target treatment are unchanged while the admission method is reviewed.

- 2026-10-03 11:10 ET: ticket28 resolved after both actual companions passed and exact metadata publication/readback `5d74de87bfe45023ab7193f36659c0f3f9999bfb`. Diagnostic L3 observed: 14,546 negative-hint CAS failures, zero violations. Ticket31 is wontfix because its refutation condition did not trigger;29 is claimed for fresh timed runs. Valid bounded v2 guest completion now qualifies through the authoritative witness validator, independently reviewed on both axes; 200 affected tests pass and 3,752 current identities reconcile to 3,716 pass/36 skip. Current local actual-record replay derives 19 shared/evaluated-on-target and two shared/certified entries. [Companion summary](evaluation/companion-a1-summary.json); [review](code-review.md).
