# Consumed detached-source guard R1: independent source review

2026-10-07 ET. Source-only; no target import/main, tests, SSH, Git operation, actual plan/input construction, source edit or project mutation. Final R17, removal subset and actual capacity/visibility remain unknown. Original23f/R1 are unchanged NOTRUN preparations. This review does not clear a path.

Reviewed pins:

- R1 `/private/tmp/lanl_consumed_detached_source_guard_r1_20261007.py`, 64859 B, SHA256 `66944bb04d05a690dc1c81ced7c203c0494cc028c6c9c1531e1fcb9cecd110e1`.
- Original `/private/tmp/lanl_consumed_detached_source_guard_20261007.py`, 57079 B, SHA256 `23f0357c11706fd533cd32423820b1f32078d78e9441abffa8651b06a4d4250b`.
- Complete R1 derivation `/private/tmp/lanl-consumed-detached-source-guard-r1-complete-derivation-20261007.diff`, SHA256 `1c08b9a811816598d007aa4b01d8ed949b77547174ac024d4cf39792b63b7d7a`.
- R1 handoff `/private/tmp/lanl-consumed-detached-source-guard-r1-source-handoff-20261007.md`, SHA256 `709714a9deab4120544d2579d3de451e5dbf6ad96b427b6a299d4c3ee9331976`.

## 1. Blocking circular review/configuration binding

R1 lines820–836 load a sealed parent review, compute configuration SHA excluding only top-level `identity_sha256` and `parent_review_pin`, and require four configuration-contained review IDs to equal the sealed review identity. The review identity seals `reviewed_configuration_sha256`, which hashes those same review IDs. This creates `reviewID → configurationSHA → reviewID`; the normal parent cannot construct these documents without a cryptographic fixed point. This is a source/contract fault, independent of future host visibility or capacity. Original23f has the same structure.

Use one closed canonical configuration projection which excludes only these exact self-review-link leaves in addition to the two existing top-level exclusions:

- `control_siblings_complete_review.parent_review_identity_sha256`
- `pending_alias_coverage_review.parent_review_identity_sha256`
- `receipt_source_proofs_complete_review.parent_review_identity_sha256`
- `original_raw_files_complete_review.parent_review_identity_sha256`
- each `relevant_privileged_consumers[i].parent_review_identity_sha256` (R1 lines501–504)

Every other configured value, field, observation/file/source pin and consumer-identification fact must remain hashed. After validating the actual review seal/configuration SHA, compare every excluded value to that sealed review identity. Do not broadly remove all identity fields or weaken the later relationship checks. These are revision requirements, not changes made by this review.

## 2. Partial-removal receipt can omit a completed mutation

R1 lines858–862 set the current marker, remove via plain Git, confirm the directory absent, clear the marker at861, then append the completed row at862. TERM/INT/HUP handlers931–934 can raise between the last two statements. The exception path942–946 would then contain neither the newly completed row nor an `incomplete_removal_attempt`, despite the physical removal. This ordering also exists in original23f734–735.

Append the completed row before clearing `current_removal`. Keep the uncertain marker active until completion is journaled. An interruption earlier remains explicitly uncertain; an interruption after the append retains the completed row. No retry, rollback or broader removal permission is needed.

## Remaining disposition

No additional concrete fault found in the inspected fixed enum/plain-remove scope, strict returned-byte/stat reads, baseline/current-row/final witness schedule, tracked mode/blob/object retention, or preservation of original receipt file bytes without a invented uniform seal policy. R1 avoids classifying unrelated privileged daemons as relevant and avoids the earlier N-fold full raw/catalog hashing schedule.

The live process scan is observational and the parent no-concurrent-writer/pending-alias boundary remains inherited. Actual relevant `/proc` visibility, permission modes, raw inventories, byte/walk/deadline limits, final R/subset and capacity are future facts; this review supplies no root/sudo/security gate or host clearance. Current14 still prevents cleanup. No control or scientific action was performed.
