# Map: Typed library and DX100 BFS rewrites in ArchEvolve and Extensa modes

Created: 2026-10-03 02:28 ET
Updated: 2026-10-05 18:35 ET (row 79; code-review and spec-review pointer); 2026-10-05 18:20 ET (certification code-review fixes pointer: version tables, certify 1.6, BC record); 2026-10-05 17:20 ET (code review: one Updated line; row 66 deduplicated, row 70 in order, row 77 added; link pointers for tickets 01–36); 2026-10-05 16:10 ET (row 78; certify 1.5 and library-operation 1.2, evaluator process); 2026-10-05 15:00 ET (row 75; ticket 56 a8 addendum); 2026-10-05 13:25 ET (row 76; certify 1.4); 2026-10-05 10:45 ET (row 74; a8 erratum pointer); 2026-10-05 10:00 ET (ticket 56 a8 pointer); 2026-10-05 03:15 ET (row 73; a7 erratum and a8 pre-registration pointers); 2026-10-05 02:50 ET (ticket 56 a7 pointer); 2026-10-05 00:40 ET (row 70 added; certification isolation, certify 1.3); 2026-10-04 23:40 ET (row 72 resolved; ticket 72 pointer); 2026-10-04 23:10 ET (row 68 added; ticket 56 a6 pointer); 2026-10-04 21:50 ET (row 69 added; profiling role strict schema); 2026-10-04 21:50 ET (row 66 added; ticket 56 a5 result and 57 a7 audit pointers); 2026-10-04 21:40 ET (row 68 added; knob_range and schedule_range); 2026-10-04 21:35 ET (rows 66 resolved and 67 added; pointers for tickets 66 and 67); 2026-10-04 21:10 ET (row 67 added; forged_frontier v2 and the a7 re-judgement); 2026-10-04 ET (ticket rows 56–65 synced with the ticket files by the final code review); 2026-10-04 ET (ticket rows 56–65 synced with the ticket files by the final code review) 2026-10-04 23:10 ET (row 68 added; ticket 56 a6 pointer); 2026-10-04 ET (ticket rows 56–65 synced with the ticket files by the final code review) 2026-10-05 00:40 ET (row 70 added; certification isolation, certify 1.3)
**Type:** ticket map
**Status:** ready-for-agent
**Spec:** [spec.md](spec.md)

Statuses: ready-for-agent; ready-for-human (Yan-Ru acts); needs-triage (readied by the Extensa-mode design session, or triggered by an L3 refutation). Tickets marked go-ahead run on mbit10. The user's explicit standing approval on 2026-10-03 supersedes repeated approval requests for related dispatches (Q62); actual admission and receipts remain required. The pull request to `main` stays as the archevolve-handoff pull-request ticket, blocked by this feature's last tickets.

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
| 29 | [Timed gem5 runs, comparison and team summary](issues/29-timed-runs-comparison-summary.md) | resolved | 28 | yes |
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
| 38 | [Prefactor: kernel plug-in seam, native side](issues/38-kernel-seam-native.md) | resolved | — |  |
| 39 | [Prefactor: kernel plug-in seam, gem5 side](issues/39-kernel-seam-gem5.md) | resolved | 23 |  |
| 40 | [BC on the native evaluator (code)](issues/40-bc-native-code.md) | resolved | 38 |  |
| 41 | [BC native evaluation on mbit10](issues/41-bc-native-run.md) | resolved | 08, 40 | yes |
| 42 | [BC certification and the derived BC contract](issues/42-bc-certification-and-derived-contract.md) | resolved | 18, 17, 28, 40 |  |
| 43 | [Yan-Ru promotes the derived BC contract](issues/43-promote-bc-contract.md) | resolved | 42 |  |
| 44 | [BC gem5 completion witness and execution case](issues/44-bc-gem5-completion-witness.md) | resolved | 39, 40 |  |
| 45 | [BC gem5 evaluation](issues/45-bc-gem5-evaluation.md) | resolved | 26, 29, 41, 43, 44 | yes |
| 46 | [Library JSON schema and SQLite index](issues/46-library-schema-and-index.md) | resolved | 42 |  |

## Phase 5: Extensa mode

Decisions: [extensa-design-2026-10-03.md](extensa-design-2026-10-03.md) (agent-decided under Yan-Ru's 2026-10-03 delegation; revisable). Go-ahead for 56–58 granted 2026-10-03.

| # | Ticket | Status | Blocked by | Go-ahead |
|---|---|---|---|---|
| 47 | [Extensa-mode design session](issues/47-extensa-design-session.md) | resolved | 03 |  |
| 48 | [Mode tags, team-boundary refusals and candidate-artifact promotion](issues/48-mode-tags-and-team-boundary.md) | resolved | 11, 15, 47 |  |
| 49 | [Port Extensa's machinery](issues/49-port-extensa-machinery.md) | resolved | 07, 10, 11, 47 |  |
| 50 | [Tracer: certify one library operation (packing)](issues/50-library-operation-tracer.md) | resolved | 11, 47 |  |
| 51 | [Seed the experimental tier from Extensa](issues/51-seed-extensa-families.md) | resolved | 50 |  |
| 52 | [Extensa campaign skeleton](issues/52-campaign-skeleton.md) | resolved | 07, 24, 48, 49 |  |
| 53 | [Speed rule, per-class verdicts, selection and knob tuning](issues/53-speed-rule-and-selection.md) | resolved | 52 |  |
| 54 | [Extensa campaign budgets and pruning](issues/54-campaign-budgets.md) | resolved | 08, 26, 52 |  |
| 55 | [Query site finder](issues/55-query-site-finder.md) | resolved | 46, 52 |  |
| 56 | [Native-CPU Extensa campaign target for BFS](issues/56-native-campaign-target.md) | resolved | 51, 53, 54, 55 | yes (granted) |
| 57 | [gem5 Extensa campaign target](issues/57-gem5-campaign-target.md) | resolved | 53, 54, 55 (29 resolved) | yes (granted) |
| 58 | ["Is the specification enough?" experiment](issues/58-spec-enough-experiment.md) | resolved | — (48, 07, 08, 20, 62 resolved) | yes (granted) |
| 59 | [Send Peter the Extensa-mode design note](issues/59-send-peter-extensa-design.md) | ready-for-human | 47 (resolved) |  |
| 60 | [Send Peter the "is the specification enough?" finding](issues/60-send-peter-spec-enough-finding.md) | ready-for-human | 58 |  |
| 61 | [Native protocol for the scale-22 Extensa classes](issues/61-native-scale22-protocol.md) | resolved | — |  |
| 62 | [Spelling-independent BFS certification controls for campaign rewrites](issues/62-spelling-independent-certification-controls.md) | resolved | — |  |
| 63 | [Scalable native BFS evaluator (v2) with a compiled structural verifier](issues/63-scalable-native-verifier.md) | resolved | — |  |
| 64 | [Native scale-22 A/A pilot is unstable: protocol options](issues/64-native-scale22-pilot-unstable.md) | resolved | — |  |
| 65 | [Range-loop convention, register operands and named-check campaign feedback](issues/65-range-loop-convention-and-named-check-feedback.md) | resolved | — |  |
| 66 | [Native protocol after the isolation test: options for Yan-Ru](issues/66-native-protocol-after-isolation-test.md) | resolved | — |  |
| 67 | [forged_frontier v2: a control every correct rewrite can kill](issues/67-forged-frontier-control-v2.md) | resolved | — |  |
| 68 | [knob_range and schedule_range: make the contracts' named checks enforceable](issues/68-knob-range-and-schedule-range-checks.md) | resolved | — |  |
| 69 | [Profiling role schema against the providers' strict mode](issues/69-profiling-role-strict-schema.md) | resolved | — |  |
| 70 | [Certification isolation: verdicts the candidate cannot print, faults it cannot see](issues/70-certification-isolation.md) | resolved | — |  |
| 71 | [Native evaluator v3: parent values checked at full width before narrowing](issues/71-native-evaluator-v3-parent-width.md) | resolved | — |  |
| 72 | [Native upstream DO-BFS trials are two-level: options for Yan-Ru](issues/72-native-upstream-two-level-trials.md) | resolved | — |  |
| 73 | [Provider capacity is an uncounted pause; the rewrite workspace names the protected verifier](issues/73-provider-capacity-and-protected-regions.md) | resolved | — |  |
| 74 | [The guard's thread cap bounds the model's work; a stop for the harness's own limit is uncounted](issues/74-provider-guard-runtime-threads.md) | resolved | — |  |
| 75 | [Certify native a8's best: a TDStep frontier-staging contract, promotion and team re-evaluation](issues/75-certify-a8-frontier-staging.md) | resolved | 56, 76 | go-ahead |
| 76 | [Certify 1.4: blinded controls, attributed rejections, a trusted frontier ledger, aggregate feedback](issues/76-attributed-blinded-certification.md) | resolved | 70 |  |
| 77 | [Library-operation certification 1.1: record verdicts, blinded driver faults, attributed controls](issues/77-library-operation-certification-records.md) | resolved | 76 |  |
| 78 | [Certify 1.5 and library-operation command 1.2: record-keeping in a separate evaluator process](issues/78-certification-evaluator-process.md) | resolved | 76, 77 |  |
| 79 | [Certify 1.5 behavior changes made inside ticket 78 (commit 93a2a94): awaiting ratification](issues/79-certify-1-5-behavior-changes.md) | ready-for-human | — |  |

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

- 2026-10-03 12:13 ET: ticket29 a1 first **uniform18** baseline stopped at the10**10 post-seal verifier cap, with no qualified verdict or ratio; failure metadata published8b68b2f, raw failed checkpoint retained. Restore prior common10**14 ceiling without changing ROI/checker/resource/wall/model constraints. Both final review axes pass,168 affected tests pass, full3,756case ledger reconciles3,720pass/36skip. Fresh a2 actual prepare/protocol/binary/companion/timed execution remains required. [Budget decision](evaluation/post-roi-budget-decision.md).

- 2026-10-03 18:20 ET: ticket30 is claimed under standing related-action approval for reviewed first-result delivery to Peter and actual team-claim recording. Its prepared body passes content review and remains unsent until the independent raw audit, exact compact publication, verified repository links and final review finish. Ticket37 remains personally human-owned and excluded from all mail actions. Both new official simulated point comparisons pass; final Kronecker raw audit remains active at frozen6cf. [Current progress](progress.md).

- 2026-10-03 18:47 ET:29resolved from allfouractualtimed passes, two publicsimulated point comparisons, independentfullraw/retention-aware custody, exactGitpublication/readback and bothfinalreviews.30remainsclaimed forreviewed delegated delivery/teamclaim;02/37human-owned and31wontfix. [Result and limits](evaluation/timed-a2-r1-result-summary.json).

- 2026-10-03 19:00 ET:30needs-info after automatic approval review rejected the exact reviewed first-result payload/destination; no delivery/claim asserted.33resolved,02/37ready-for-human,31wontfix. All implementation/evaluation/review findings are closed; final authorized metadata/source synchronization continues. [Blocked receipt](drafts/outgoing-2026-10-03/send-receipt-30-blocked.json).

- 2026-10-03 19:36 ET: all Josh/Peter/Eric communications are draft-only for the agent; Yan-Ru sends manually.30ready-for-human,02/37ready-for-human,31wontfix,33resolved. All assigned agent implementation/evaluation/review/draft tasks are complete. Send/team-claim acceptance stays unchecked; no delivery inferred. Final ownership metadata sync precedes pausing the progress heartbeat.

- 2026-10-03 ET: ticket 47 resolved. Extensa-mode decisions D1–D12 are agent-decided under Yan-Ru's 2026-10-03 delegation and revisable. 48–58 are ready-for-agent; 02 no longer blocks any ticket under the Q66 assumption; 59 and 60 are new ready-for-human send tickets with drafts. [Decisions](extensa-design-2026-10-03.md); [ticket 47](issues/47-extensa-design-session.md).

- Ticket 38, completed 2026-10-03 21:00 ET: native kernel plug-in seam (`swdb/kernels/`), BFS the only plug-in with its exact former identities; 350 BFS regression cases pass. [38-kernel-seam-native](issues/38-kernel-seam-native.md).

- Ticket 39, completed 2026-10-03 22:40 ET: gem5 kernel plug-in seam (driver/oracle, verifier binding, v2 witness, accelerator cases); BFS unchanged; 34 listed failures are pre-existing on 8ad6e8a. [39-kernel-seam-gem5](issues/39-kernel-seam-gem5.md).

- Ticket 40, completed 2026-10-03 23:05 ET: BC plug-in on the native evaluator (BCVerifier reproduction, NaN-closed; vacuous sources refused), DX100 BC record and scalar snapshot derivation, BC workloads on BFS graph files, BC protocol freeze. [40-bc-native-code](issues/40-bc-native-code.md).

- Ticket 42, completed 2026-10-03 23:20 ET: certification matrix and pass rule are a kernel plug-in; derived contract.bc_read_offload (cites the BFS contract, adds BC-L1) certifies on the Mac, 10/10 cells, 18/18 controls rejected; experimental until ticket 43. [42-bc-certification-and-derived-contract](issues/42-bc-certification-and-derived-contract.md).

- Ticket 44, completed 2026-10-03 23:35 ET: BC gem5 v2 completion witness (bc_witness: BC checks plus the frozen BFS v2 rules on a translated copy), BC verify driver copy, trusted BC oracle driver, forward-pass read-only case without a race companion; fixtures only. [44-bc-gem5-completion-witness](issues/44-bc-gem5-completion-witness.md).

- Ticket 46, completed 2026-10-03 23:50 ET: library entry JSON schema; SQLite library_entries/dependencies/clauses and statements/statement_steps; staleness covers the library folder. [46-library-schema-and-index](issues/46-library-schema-and-index.md).

- Ticket 41, completed 2026-10-03 23:15 ET: BC workloads bc-20261003-kronecker18/uniform18 registered on the BFS scale-18 graphs; scalar BC snapshot registered; native evaluation bc-native-20261003-a1.kronecker18 passes BCVerifier (9/9 trials) on mbit10 node 1, commit ec50f78. [41-bc-native-run](issues/41-bc-native-run.md).

- Ticket 43, completed 2026-10-03 23:31 ET: contract.bc_read_offload was agent-reviewed and promoted under Yan-Ru's 2026-10-03 delegation and is revisable by Yan-Ru. It is now shared/certified (review.contract.bc_read_offload.30a3747420b3). The Mac re-certification matches certification.1e389a95, and the review found no blocker. [43-promote-bc-contract](issues/43-promote-bc-contract.md), [review](bc-contract-review-2026-10-03.md).
- 2026-10-03 20:42 ET: ticket 48 resolved. Extensa mode/campaign tags, writer immutability, derived candidate level, team-boundary refusals and candidate promotion with a derived team re-evaluation protocol. [48-mode-tags-and-team-boundary](issues/48-mode-tags-and-team-boundary.md).

- 2026-10-03 21:03 ET: ticket 49 resolved. Extensa loop accounting, runtime probes, certification profiles and BFS-relevant synthesis ported under swdb/extensa/ with provenance; swdb certify --profile and swdb synthesize. [49-port-extensa-machinery](issues/49-port-extensa-machinery.md).

- 2026-10-03 21:08 ET: ticket 50 resolved. operation.pack_executor (base PackExecutor, experimental) certifies end to end against swdb_ref::pack_gather; three controls rejected by named checks; DX100 bodies refused by swdb validate. [50-library-operation-tracer](issues/50-library-operation-tracer.md).

- 2026-10-03 21:12 ET: ticket 51 resolved. Binning, relabeling, regrouping and gather-staging entries seeded in the experimental tier; each certifies with three named-check controls and declares a pattern key. [51-seed-extensa-families](issues/51-seed-extensa-families.md).

- 2026-10-03 21:49 ET: ticket 52 resolved. swdb campaign runs fixture iterations end to end (campaign file schema and D5 refusals, tagged campaign store, campaign_summary in both stores); native and gem5 adapters remain tickets 56/57. [52-campaign-skeleton](issues/52-campaign-skeleton.md).

- 2026-10-03 21:50 ET: ticket 53 resolved. One frozen protocol per campaign, strict >1.05 with spread <=0.1 (gem5 point ratios), native A/A pilot, per-class certification-first selection with faster_uncertified, knob range refusal. [53-speed-rule-and-selection](issues/53-speed-rule-and-selection.md).

- 2026-10-03 21:51 ET: ticket 54 resolved. Every D6 stop reason, uncounted usage-limit/login pauses with resume, campaign-wide call budget, disk cap and preflight, lane conflict, and post-comparison pruning with claimed runs kept are fixture-tested. [54-campaign-budgets](issues/54-campaign-budgets.md).

- 2026-10-04 00:58 ET: ticket 55 resolved. `regions: query` runs one SQL site-finder query (sha256 recorded) over access patterns, steps, the statements index, statement legality facts and indexed pattern keys; a contract applies only on exact key match plus a true recorded fact for every legality clause. [55-query-site-finder](issues/55-query-site-finder.md).
- Ticket 45, completed 2026-10-04 00:52 ET: one small BC gem5 run (Kronecker 14, source 0, node 0, 65a7c7b) passes the BC v2 completion witness for baseline and candidate; the candidate passes the read-only case, full/tail tiles and the frontier check. Simulated point ratio 0.424 (regression; one graph, one source). contract.bc_read_offload is now shared/evaluated_on_target. Witness build-ID bug fixed in b7f7798. [45-bc-gem5-evaluation](issues/45-bc-gem5-evaluation.md).

- Ticket 56, completed 2026-10-04 06:05 ET: native campaign adapter (per-role protocols, A/A pilot, separate paired blocks against both baselines, fork-baseline selection); Kronecker22 and three-source uniform22 workloads registered; campaign extensa-native-bfs-20261004-a1 stopped at setup (scale 22 exceeds the native evaluator limits); follow-up 61. [56-native-campaign-target](issues/56-native-campaign-target.md).
- Ticket 57, completed 2026-10-04 06:05 ET: gem5 campaign adapter (one baseline per class, point ratios, session begin inside DOBFS, 36 GiB admission), evidence-cited legality facts; acceptance run extensa-gem5-bfs-20261004-a5 plateaued with every contract edit refused by certify's spelling-bound control sites (a1-a4: harness fixes); follow-up 62. [57-gem5-campaign-target](issues/57-gem5-campaign-target.md).
- Ticket 62, completed 2026-10-04 ET: rewrite negative controls are library-side faults (private fault-injected copy of the canonical lowering header, one -DSWDB_DXC_FAULT_<ID> per control); BC-L1 uses a token matcher; reformatted and restructured ticket 20 rewrites certify 16/16. Codex sessions hold swdb-session.lock in CODEX_HOME. [62-spelling-independent-certification-controls](issues/62-spelling-independent-certification-controls.md).
- Ticket 58, completed 2026-10-04 08:03 ET: a2 scored nothing (audit refusals, one driver crash); a3 ran 9 sequential audited sessions, 0/9 certified: every sample passes values where DX100 takes register handles, as Peter v1.1 types them. Draft for ticket 60. [58-spec-enough-experiment](issues/58-spec-enough-experiment.md).
- Ticket 57 rerun a6, 2026-10-04 ET: with the ticket 62 certifier every applied contract edit is certified and fails on range_bounds (last_i initialized to -1); plateau after 4 iterations, 11 calls, 1.93 lane-h, no_gain both classes. [57-gem5-campaign-target](issues/57-gem5-campaign-target.md).
- 2026-10-04 06:30 ET: ticket 61 resolved as a decision (agent-decided under Yan-Ru's 2026-10-04 delegation; revisable): option 1, a scalable native verifier; D3/D4 unchanged; implementation slice 63. [61-native-scale22-protocol](issues/61-native-scale22-protocol.md), [63-scalable-native-verifier](issues/63-scalable-native-verifier.md).
- 2026-10-04 08:15 ET: ticket 63 resolved. Native evaluator v2 (mmap SG driver, compiled verifier `swdb.bfs.structural.compiled.v2` with exactly the verify_parents criterion), differential tests, mbit10 x86_64 check. [63-scalable-native-verifier](issues/63-scalable-native-verifier.md).
- 2026-10-04 10:55 ET: ticket 56 Answer updated. Campaign extensa-native-bfs-20261004-a3 (evaluator v2) stopped in the A/A pilot with baseline_unstable (Kronecker fork 0.161: source 7777 is isolated; uniform upstream 0.134); follow-up needs-info ticket 64. [56-native-campaign-target](issues/56-native-campaign-target.md), [64-native-scale22-pilot-unstable](issues/64-native-scale22-pilot-unstable.md).
- 2026-10-04 11:20 ET: ticket 64 resolved (agent-decided under Yan-Ru's delegation; revisable): recorded next-positive-out-degree source policy (Kronecker 22 v2 sources 0/1234/7778, uniform 22 v2 unchanged), per-class A/A gate, uniform upstream bimodal regimes diagnosed (cause unidentified; no control applied). [64-native-scale22-pilot-unstable](issues/64-native-scale22-pilot-unstable.md).
- 2026-10-04 12:15 ET: ticket 56 Answer updated. Campaign extensa-native-bfs-20261004-a4 (v2 workloads, per-class gate, beside gem5 a7) stopped baseline_unstable in both classes (Kronecker fork 0.225 / upstream 0.153; uniform fork 0.147 / upstream 0.014); 0 provider calls. [56-native-campaign-target](issues/56-native-campaign-target.md).
- Ticket 65, completed 2026-10-04 ET: range-loop convention verified (last_i_reg 0, last_j_reg -1; Peter v1.1 §3.3, authors' MAA_functional.hpp, strict layer); non-normative usage notes in library/intrinsics/notes/ ship with the rewrite workspace (entries unchanged, so shared tiers stay); campaign feedback names the failing strict-layer check and its precondition. [65-range-loop-convention-and-named-check-feedback](issues/65-range-loop-convention-and-named-check-feedback.md).
- Ticket 57 rerun a7, 2026-10-04 ET: with ticket 64 notes and named-check feedback, both classes reach certified gem5 candidates: kronecker 1.411 and uniform_random 1.553 simulated point ratios (gain, single graph per class); 8 iterations, 20 calls, 6.70 lane-h. [57-gem5-campaign-target](issues/57-gem5-campaign-target.md).
- 2026-10-04 20:30 ET: ticket 57 a7 audit against the final code review fixes: no erratum. The leakage scan is clean, re-judged verdicts are unchanged, and both best candidates re-certify on the Mac. Gains stand. Open: forged_frontier false rejections. [57-gem5-campaign-target](issues/57-gem5-campaign-target.md), [audit](evaluation/a7-review-fix-audit-2026-10-04.json).
- 2026-10-04 21:50 ET: ticket 56 closed `baseline_unstable` (Kronecker) by the pre-registered isolation test a5. The a5 pilot ran with node 0 free. Kronecker fork spread is 0.131 (fails); Kronecker upstream 0.008, uniform fork 0.084 and uniform upstream 0.012 pass. Uniform ran 4 iterations and stopped at plateau. Its two scalar candidates measured 1.284 and 1.318 against the fork, but both are `inconclusive` (spread 0.117 and 0.159). The review findings do not affect a5. Protocol options are in needs-info [66](issues/66-native-protocol-after-isolation-test.md). [56-native-campaign-target](issues/56-native-campaign-target.md), [evidence](evaluation/native-a5-isolation-2026-10-04.json).
- 2026-10-04 21:10 ET: ticket 67 resolved (agent-decided under Yan-Ru's 2026-10-04 delegation; revisable). forged_frontier v2 duplicates the first CPU queue push of the run, so it no longer depends on chunk or tile timing; it is versioned (`fault.version`, certify command 1.1). The six a7 candidates that failed only on v1 now certify on the Mac (10/10, 16/16). None has a gem5 timing, so they are "certified, not timed" and both class selections stand. Open: named-check lines and fault macros are visible to candidate code. [67-forged-frontier-control-v2](issues/67-forged-frontier-control-v2.md), [57 addendum](issues/57-gem5-campaign-target.md), [evidence](evaluation/a7-forged-frontier-v2-rejudge-2026-10-04.json).
- 2026-10-04 21:40 ET: ticket 68 resolved (agent-decided under Yan-Ru's 2026-10-04 delegation; revisable). `swdb certify` (command 1.2) now enforces knob_range (the SWDB_KNOB_<NAME> assignments, resolved by the preprocessor, inside the contract ranges) and schedule_range (every OpenMP worksharing schedule clause is static or dynamic with an in-range constant chunk). It runs two certifier controls, knob_out_of_range and schedule_out_of_range. No contract text changed; the contract's own controls for these clauses are recorded as unable to exercise them. Ticket 20 (20/20), BC (28/28) and both a7 bests re-certify on the Mac. [68-knob-range-and-schedule-range-checks](issues/68-knob-range-and-schedule-range-checks.md), [evidence](evaluation/legality-checks-recertification-2026-10-04.json).
- 2026-10-04 21:50 ET: ticket 69 resolved (agent-decided under Yan-Ru's 2026-10-04 delegation; revisable). The profiling role's minLength, minItems and minimum need no change. Codex strict mode accepted the byte-identical wire schema in annotation a3 (sha256 3928d885…) and refused only uniqueItems, which the transport already drops. `strict_problems` now also checks keywords against the accepted and refused sets, on each role's wire schema. Open: the Claude path is unverified. [69-profiling-role-strict-schema](issues/69-profiling-role-strict-schema.md).
- 2026-10-04 20:55 ET: ticket 66 resolved as decided by Yan-Ru ("go with the recommendation"): native CI-width speed rule `swdb.speed_rule.ci_width.v1`, pre-registered before any run (commit 84e44e1). Relative 95% CI width at most 0.05 from a circular block bootstrap over 20 repetitions (blocks of 4, same indices for all sources and both sides, 2000 resamples, seed 20260925); A/A interval also inside (1/1.05, 1.05); a gain needs the same interval's lower bound strictly above 1.05. Old protocols and a5 keep the range rule. Implemented in ce42a45. [66-native-protocol-after-isolation-test](issues/66-native-protocol-after-isolation-test.md).
- 2026-10-04 21:15 ET: ticket 71 resolved. Native evaluator `swdb.native.evaluator.scalable.v3`: compile-time integral parent type, saturating int32 narrowing (full-width verdicts), one retained parent copy per distinct vector; v2 unchanged. Closes the final code review's open P3. [71-native-evaluator-v3-parent-width](issues/71-native-evaluator-v3-parent-width.md).
- 2026-10-04 23:10 ET: ticket 56 a6 addendum. Campaign extensa-native-bfs-20261004-a6 ran the pre-registered CI-width gate (mbit10 node 1, generation 524, 21:06-23:04 ET, commit ce42a45, node 0 free). Fork A/A widths pass (Kronecker 0.040, uniform 0.019); upstream A/A widths fail (0.125, 0.093) on two-level trials, so both classes are baseline_unstable: 0 iterations, 0 calls, 1.97 lane-h. No rerun. Options in needs-info [72](issues/72-native-upstream-two-level-trials.md). [56-native-campaign-target](issues/56-native-campaign-target.md), [evidence](evaluation/native-a6-ci-gate-2026-10-04.json).
- 2026-10-04 23:30 ET: ticket 72 resolved (decision 23:15 ET, agent-decided under Yan-Ru's delegation; revisable; pre-registered 23:19 ET, commit 3147b31): speed rule `swdb.speed_rule.ci_width.v2` = v1 with the A/A pilot gated on the selection baseline (fork scalar TDStep) only; upstream DO-BFS reported beside each candidate with its own verdict and a per-side level mix (split at the largest adjacent ratio, two levels at 1.08 or more). a6 is not re-judged. Implemented in 8aea84f. [72-native-upstream-two-level-trials](issues/72-native-upstream-two-level-trials.md).
- 2026-10-04 21:15 ET: ticket 71 resolved. Native evaluator `swdb.native.evaluator.scalable.v3`: compile-time integral parent type, saturating int32 narrowing (full-width verdicts), one retained parent copy per distinct vector; v2 unchanged. Closes the final code review's open P3. [67-native-evaluator-v3-parent-width](issues/71-native-evaluator-v3-parent-width.md).
- 2026-10-04 23:10 ET: ticket 56 a6 addendum. Campaign extensa-native-bfs-20261004-a6 ran the pre-registered CI-width gate (mbit10 node 1, generation 524, 21:06-23:04 ET, commit ce42a45, node 0 free). Fork A/A widths pass (Kronecker 0.040, uniform 0.019); upstream A/A widths fail (0.125, 0.093) on two-level trials, so both classes are baseline_unstable: 0 iterations, 0 calls, 1.97 lane-h. No rerun. Options in needs-info [68](issues/72-native-upstream-two-level-trials.md). [56-native-campaign-target](issues/56-native-campaign-target.md), [evidence](evaluation/native-a6-ci-gate-2026-10-04.json).
- 2026-10-05 00:40 ET: ticket 70 resolved (agent-decided under Yan-Ru's 2026-10-04 delegation; revisable). `swdb certify` 1.3 isolates candidate certification:
  - Every named check is computed out of process from evaluator records on a harness-opened descriptor. An evaluator-owned `main` records the kernel's result.
  - Faults live in a separately compiled seam object, linked to one unchanged candidate object.
  - A harness scan refuses candidate text that names harness symbols.
  - Two adversarial patches that certify under 1.2 are refused under 1.3.
  - Ticket 20 (20/20), BC (28/28) and both a7 bests (20/20) re-certify. a7 `it5.kronecker.a2` and `it6.kronecker.a0` are now refused by the scan; neither is a best.
  - Open: run-time seam probing, the frontier hook inside the candidate's function, and feedback that names controls.
  - [70-certification-isolation](issues/70-certification-isolation.md), [evidence](evaluation/certification-isolation-2026-10-04.json).
- 2026-10-05 02:50 ET: ticket 56 a7 addendum. Campaign extensa-native-bfs-20261004-a7 under speed rule ci_width.v2 (ticket 72; mbit10 node 1, generation 525, 2026-10-04 23:33 to 02:43 ET, commit 8aea84f, node 0 free). Kronecker fork A/A width 0.055 fails (baseline_unstable); uniform fork 0.014 passes. Uniform: 4 iterations to plateau, one measured uncertified candidate at 1.004 [0.995, 1.017], no_gain; 5 calls, 3.15 lane-h. Calls 4-5 failed on Codex 'model at capacity' and were counted (harness defect, D7). No gain, no rerun. [56-native-campaign-target](issues/56-native-campaign-target.md), [evidence](evaluation/native-a7-ci-gate-v2-2026-10-05.json).
- 2026-10-05 03:15 ET: ticket 73 resolved (agent-decided under Yan-Ru's delegation; revisable). Provider capacity (a7 calls 4-5: "Selected model is at capacity") is now an uncounted D7 outcome with backoff (at most 1 h, then infrastructure_failure), never provider_output_invalid. The rewrite workspace has PROTECTED.json (BFSVerifier in workspace lines) and REGIONS.json workspace spans (the region numbers named the full fork source, which fall inside BFSVerifier in the scalar-only copy). Ticket 56 carries an a7 erratum (no_gain budget-contaminated) and the a8 pre-registration. [73-provider-capacity-and-protected-regions](issues/73-provider-capacity-and-protected-regions.md).
- 2026-10-05 10:00 ET: ticket 56 a8 result (pre-registered, last native run under ci_width.v2; mbit10 node 1, generation 526, 03:19-09:56 ET, commit b45c56a, node 0 free). Pilot passed in both classes. Uniform: **gain**, uncertified best it1.kronecker.a0 (TDStep frontier staging) at 1.457 [1.450, 1.472] vs fork scalar TDStep, replicated at 1.450 [1.441, 1.464] in iteration 4; 0.141 vs upstream DO-BFS. Kronecker inconclusive (CI widths 0.074, 0.057). Plateau after 5 iterations, 6 calls, 6.53 lane-h; certify 1.3 not applicable (no contract). [56-native-campaign-target](issues/56-native-campaign-target.md), [evidence](evaluation/native-a8-ci-gate-v2-2026-10-05.json).
- 2026-10-05 10:45 ET: ticket 74 resolved (agent-decided under Yan-Ru's delegation; revisable). a8 calls 1 and 6 were stopped about 0.5 s after launch for threads=17: strace plus Codex's own runtime (12 tokio threads, 2 inotify watchers), before any tool command, and counted. The guard now caps tool-command threads at 16 (story 33) and the provider runtime (tracer, CLI, code-mode host) at 64 (observed maximum 20). It also checks that every owned thread stays on the lane's CPUs. A stop for the runtime cap is `guard_infrastructure`: uncounted, retried twice after 30 s, then `infrastructure_failure`. Ticket 56 carries an a8 erratum (plateau partly infrastructure-driven; records unedited). The Linux guard tests are updated but not yet run on mbit10. [74-provider-guard-runtime-threads](issues/74-provider-guard-runtime-threads.md).
- 2026-10-05 13:25 ET: ticket 76 resolved (agent-decided under Yan-Ru's delegation; revisable). `swdb certify` 1.4 is the default for candidate artifacts; 1.3 stays selectable (`--command-version 1.3`). Per tile size the positive matrix and every library-fault control run one binary with a blinded run plan, in random order; a control counts as rejected only when its check is attributable to the fault's own action; windows are read from the queue at each slide; positive runs need the seam witness (clause L4); Extensa feedback names surviving controls only as `negative_controls_not_rejected`. Two attacks that certify under 1.3 fail under 1.4. Ticket 20 (20/20), BC (28/28) and both a7 bests (20/20) certify, all 16 library-fault controls attributed. Residuals: in-process memory introspection; same-thread probe-then-amplify for thread-attributed faults. [76-attributed-blinded-certification](issues/76-attributed-blinded-certification.md), [evidence](evaluation/certification-blinding-2026-10-05.json).
- 2026-10-05 14:21 ET: ticket 77 resolved (agent-decided under Yan-Ru's delegation; revisable). Library-operation certification (`swdb certify --profile`) command 1.1 is the default; 1.0 stays selectable (`--command-version 1.0`). A trusted driver records the frame check and output on a harness-read pipe; the reference runs before any candidate build; two driver-fault controls run blinded in the candidate's binary; every rejection is attributed; a scan covers body, template and controls. A fake-print control and a plan-detecting bypass certify under 1.0 and fail under 1.1. All five seeded entries re-certify (5/5 controls attributed each). Residuals: in-process introspection; transient input writes. [77-library-operation-certification-records](issues/77-library-operation-certification-records.md), [evidence](evaluation/library-operation-certification-2026-10-05.json).
- 2026-10-05 15:00 ET: ticket 75 resolved (agent-decided, agent-reviewed and promoted under Yan-Ru's delegation; revisable). `contract.bfs_tdstep_frontier_staging` (TDStep frontier staging plus post-claim store elimination, C2 preconditions (i)-(iv)) certifies a8's exact best tree under certify 1.3 (`certification.f5b8f6a7…`) and 1.4 (`certification.7f157865…`): 22/22 cells, 8/8 seam-fault controls rejected by their named checks, every 1.4 rejection attributed. Shared after two independent reviews. Team re-evaluation on mbit10 node 1 (generation 527, node 0 free) under the new team protocol `bfs-native-scale22-ci-team-20261005`: A/A 0.996 [0.989, 1.001]; certified candidate 1.454 [1.442, 1.464] vs fork scalar TDStep, **gain** (uniform22, single graph per class). [75-certify-a8-frontier-staging](issues/75-certify-a8-frontier-staging.md), [review](frontier-staging-contract-review-2026-10-05.md), [evidence](evaluation/ticket75-certification-and-reevaluation-2026-10-05.json), [56 addendum](issues/56-native-campaign-target.md).
- 2026-10-05 16:10 ET: ticket 78 resolved (scope decided by Yan-Ru 2026-10-05: engineering refactor plus overhead measurement; OS confinement and adversarial tests out of scope). Certify 1.5 (DX100 and native-CPU candidates) and library-operation command 1.2 are the defaults; 1.3/1.4 and 1.0/1.1 stay selectable. A trusted evaluator process (1.4's unchanged record writer and seams plus the strict layer) writes every record; the candidate runs as its child with its heap in a shared arena and reaches every seam by request. Overhead against 1.4: 1.2-3.0x per run (about 20 ms fixed), 1.00-1.27x per certification. Ticket 20, BC, both a7 bests, the native contract and the five library operations certify with the same rejections and attribution as 1.4/1.1. Ticket 75 review items folded in: nonce-named record files; a DX100 directive rule for 1.5. Residuals: shared writable arena, candidate-claimed thread identity, no confinement, probe-then-amplify, transient input writes. [78-certification-evaluator-process](issues/78-certification-evaluator-process.md), [evidence](evaluation/certification-evaluator-process-2026-10-05.json).

- 2026-10-05 17:20 ET (code review, tracker hygiene): link pointers for the tickets resolved before the one-pointer-per-ticket convention; each has its `## Answer`, and the dated bullets above give their gist: [01](issues/01-send-decision-note-and-mapping.md), [03](issues/03-design-session-commit.md), [04](issues/04-team-update.md), [05](issues/05-intrinsic-records-accelerator-interface.md), [06](issues/06-offload-strategy-effect.md), [07](issues/07-role-based-provider-launcher.md), [08](issues/08-dispatch-preflight.md), [09](issues/09-library-entry-shapes.md), [10](issues/10-port-extensa-grammar.md), [11](issues/11-tracer-certify-gather.md), [12](issues/12-strict-layer-assertions.md), [13](issues/13-range-loop-and-register-operands.md), [14](issues/14-stream-load-tile-access-alu.md), [15](issues/15-library-tiers-and-entry-promotion.md), [16](issues/16-calibration-and-bfs-matrix.md), [17](issues/17-bfs-read-offload-contract.md), [18](issues/18-bfs-candidate-certification.md), [19](issues/19-submit-patch-with-library-header.md), [20](issues/20-peter-section5-patch.md), [21](issues/21-send-peter-contract-yaml.md), [22](issues/22-promote-dx100-entries.md), [23](issues/23-read-only-gem5-checks.md), [24](issues/24-retention-and-team-claim-records.md), [25](issues/25-prune-listing-and-apply.md), [26](issues/26-automatic-pruning.md), [27](issues/27-profile-package-scalar-only.md), [28](issues/28-freeze-protocol-and-companion-runs.md), [29](issues/29-timed-runs-comparison-summary.md), [32](issues/32-retroactive-cleanup.md), [33](issues/33-per-line-callgrind-collection.md), [34](issues/34-per-line-callgrind-run.md), [35](issues/35-statement-claims-storage.md), [36](issues/36-annotate-and-score.md).
- 2026-10-05 18:35 ET: code review and spec review of tickets 38–78 (agent-decided under Yan-Ru's delegation; revisable).
  The campaign isolation check now covers the legacy lease; the lease audit of a5–a8 and ticket 75 found no block run
  while a `hostlock.sh` holder had it (isolation caveat for a5–a8: metadata, not kernel locks) [56](issues/56-native-campaign-target.md).
  ADR 0012 records the CI-width speed rule; ADR 0010 has a supersession note. Reviews state who performed them;
  attribution corrections for the four agent reviews; the a8 candidate re-promoted with the 1.4 certification of the
  current contract content [75](issues/75-certify-a8-frontier-staging.md), [43](issues/43-promote-bc-contract.md).
  Promotion refuses stale certifications and superseded team protocols; levels follow the newest command version.
  The spec's "Awaiting ratification" section lists the rules and reviews decided under delegation; 93a2a94's
  behavior changes are ticket [79](issues/79-certify-1-5-behavior-changes.md).

- 2026-10-05 18:20 ET: certification code-review fixes (agent-decided under Yan-Ru's delegation; revisable; commits 000e85f, 4fc80c5, bb7673f, 4164ce2 on the worktree branch, not pushed). One frozen version table per certify command family (swdb/certification_procedures.py; unknown versions raise), per-version source manifests with frozen digests, the git commit, command family and library_operation_version in new records, legacy label aliases (b7954f4d = native 1.3; DX100 1.4 before 93a2a94), evidence basis measured for native-CPU and library-operation runs, shared build/run/record/evidence code. Certify 1.6 is the default (knob_range reads every declared knob spelling, unverified never the default; _Pragma schedule controls); DX100 1.4-1.6 records persist (JSON evidence). 30/30 before/after re-certifications identical. Current BC record certification.1e424fce (1.6, 28/28) committed. Tests: full suite in 8 parallel partitions (separate TMPDIR and basetemp, at 4164ce2): 4,331 passed, 38 skipped, 4 failed. The 4: two format-document checks (the new schema fields were undocumented; now in docs/reference/bfs-typed-library.md), one frozen-pin check that counted the new BC record's source manifest as a pin (test corrected), one 15 s CLI timeout under the 8-way load (test_bfs_t17_diagnostic_build, passes alone). After the fixes those files pass (test_format_doc and test_bfs_t17_diagnostic_build 33, test_certification_procedures and test_format_doc 55). [78 addendum](issues/78-certification-evaluator-process.md), [68 erratum](issues/68-knob-range-and-schedule-range-checks.md), [76 drift](issues/76-attributed-blinded-certification.md), [42 BC record](issues/42-bc-certification-and-derived-contract.md), [evidence](evaluation/certification-review-fixes-2026-10-05.json).
