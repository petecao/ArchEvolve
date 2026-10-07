# Prospective ticket 17 accepted-input seal contract

Prepared 2026-10-07 ET, source-only. The reviewed r1 auditor/collector and their packet remain byte-exact. No program imports/execution, tests, Store, actual campaign inputs, SSH, staging or tracked changes occurred. This distinct small revision addresses the remaining conditional-seal concern; it is still pending parent review and concrete actual inputs.

Selected auditor: `/private/tmp/lanl17_selected_record_trajectory_auditor_a2r1s1_20261007.py`, 115,130 bytes, SHA-256 `6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da`. Collector remains exact r1 `/private/tmp/lanl17_compact_attempt_custody_a2r1_20261007.py`, SHA `b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c`.

Source-only proof: `/private/tmp/lanl17-auditor-a2r1s1-seal-gate-preparation-20261007.json`, seal `01de27e9f11774ba0a724f79d754bb64aceb4e12b0a7d552562dc6c5559f73e0`, file SHA `8a5a54cac7f3e3191925e8c44afccf4b42075a147b248d514997f6e9c87ac39d`. It reverses only the new `sealed_json` call spellings and verifies every existing Reader method AST is unchanged; every other module/public/scientific AST symbol is unchanged. It pins the exact small diff and new generator. No methods or fixtures ran.

## Required compact receipt pins

Each claimed sealed receipt pin requires all the following explicitly:

- `path`: exact absolute local path, or allowed original Git-relative path together with an explicit allowed `commit`.
- `bytes`: exact original byte count, bounded by the reader.
- `sha256`: exact 64-character original file SHA-256.
- `identity_sha256`: exact 64-character original compact receipt identity.
- `canonical_ensure_ascii`: a JSON boolean matching the **original writer's** canonical hashing policy.

`canonical_ensure_ascii` must not be guessed, defaulted or copied blindly from another writer. For example the selected supervisor's source explicitly uses ensure_ascii=false; the collector's own compact digest uses Python's default true. Other original writers must be identified from their pinned source. File SHA provides exact custody; the required compact identity plus original canonical policy independently recomputes the claimed seal. A receipt claiming an identity without these required pin fields is pending/refused.

The new Reader.sealed_json gate enforces this at 19 call sites: actual metadata supervisor; M2; original freeze/final compact receipts; prepare/finalize preregistrations; publication; both final dependency selected admissions and their actual export receipts; before/after attempt custody; dispatch-state corroboration; concrete unclean resume custody; missing-component refusal custody; trajectory projection; original campaign dispatch/stopped/release; interrupted selected-body custody; original named candidate-selection custody. Several call sites cover multiple receipts/iterations. This count describes source sites, not receipt count or executed controls.

The accepted-pins root remains explicitly file-SHA-bound and self-sealed under its declared reader-owned input format. Public agreement_policy/report/paired identities and YAML evaluation/summary records retain their exact existing fixed-key public checks, not a newly substituted whole-object compact seal.

## Legitimate original unsealed data

The original public `campaign-export` JSON has no compact identity field in its writer. Its `exported=self.json(pin)` site is preserved exactly and uses mandatory byte count/file SHA, original format/content checks and inherited named-selection custody. Do not insert an invented identity into that output or require a seal it never had.

Original state bytes remain remote-only and file-SHA-bound. Full record indexes, original status/exit files and unsealed original metadata are file-SHA/semantic-digest-bound according to their existing source formats; they must not be relabeled sealed or rewritten to satisfy this contract. The compact parent projections containing them are separate new sealed receipts requiring the full pin fields above. Public summaries and selected record bodies remain exact original Git/YAML content with their public identities/selected closure checks and original full-catalogue validation boundary.

## Preservation and actual admission boundary

Only a new seal helper and the own Reader receipt-read call sites changed. Source_pairing_context, public D30/accounting/selection projections, real control helper 28d, supervisor fa703, guard 9c5d, C/F6, provider/scientific budgets and all earlier preparation/actual proof history remain unchanged. The previously reviewed r1 source remains immutable rather than overwritten.

All r1 requirements still apply: explicit actual final R/EF/ER/M1/M2/policy/publication and final11/14 receipts; exact manifest source/project, Linux mbit10/parent-supplied own account, safe projections, closed counted rewrite/model/effort, prior released nonterminal state only, concrete refusal and named-selection custody, original validation/index/closure, four normal substantive trajectories and recorded blind ordering. Seals alone establish none of those semantics. D30 remains unsupported/no-switch with zero eligible pairs; no actual campaign or completion evidence is supplied by this preparation.
