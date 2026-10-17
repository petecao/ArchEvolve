# Completed21 mode custody — independent local reconciliation

Reviewed 2026-10-08T01:16:28.893402+00:00. PASS, no original metadata mismatch found. Read-only local reconciliation; no new remote observation, permission action, target runtime or scientific admission.

## Exact original pins

- receipt: `/private/tmp/lanl14-completed21-mode-actual-20261008-a1/remote-receipt.json` — 30,212 bytes; SHA `8a838ddbfd636796350cb89b1ccdc759476bf26c970dc9aa9a0d868106be55ad`.
- journal: `/private/tmp/lanl14-completed21-mode-actual-20261008-a1/remote-journal.jsonl` — 32,329 bytes; SHA `5ce5eb903cf1e5790adb36a8304481f7ddbfe83b73573113689aedc2c787be14`.
- preflight: `/private/tmp/lanl14-completed21-mode-actual-20261008-a1/remote-preflight.json` — 19,387 bytes; SHA `e8a39a97af49fab160c17413f0889aa3f51357930e782ae7c73a19138698af59`.
- supplier: `/private/tmp/lanl14-completed-metadata-supplier-r1-actual-20261008-a1/stdout.json` — 29,107 bytes; SHA `62d3f72960c96084840c03382b9057d06d9d43d90d249d0c6d1390ebc9a15ada`.

All three original JSON documents explicitly have sealed:false, with canonical/identity fields absent. The42-row JSONL remains unsealed. No original was reserialized, rewritten or resealed.

## Findings

All21 ordered supplier BEFORE rows equal preflight selected and receipt/journal BEFORE pins by path, bytes, original SHA and complete stat. The18 protocol/estimate IDs match their original filenames/kinds. Their content identity is inherited through exact request/SHA custody rather than newly recomputed from unseen YAML.

Every AFTER row changes exactly st_mode and st_ctime_ns:0664→0644, nondecreasing ctime. Device/inode/owner/group/link count/type/size/mtime and all other stat bits stay fixed. Every receipt row preserves the original SHA/bytes and records content_identity_preserved=true.

Exactly42 journal rows form21 pending_fchmod/completed_fchmod pairs in the same order. Pending originals equal preflight pins; completed journal payloads equal receipt rows, with the journal-only state marker excluded from that payload comparison. Requested mode, both stats/ctimes, ordered timestamps and enclosing receipt chronology all reconcile. Journal byte count and SHA match the exact original local JSONL.

All8 original completion-input pins including recorded pre-change stats match supplier/preflight/receipt. Both native-tool pins, all3 released lease observations and R14/185/F6 facts match supplier/preflight. The selected request's mode change is explicitly one of21; matching original_inputs are pre-change snapshots, not a claim its physical mode stayed0664 afterward.

Report68,324,111 bytes/SHA c340d66bce2d968aa5ef70b2bc0b4042484af2a7fc711a639e9d4af9b32f04e2; Markdown1475/SHA ed85628937628e7065bc36bcefa810ee23aa993e096dabf68a2197a1649a453b; request18698/SHA18c3875e6cd46bf8cf54ca32d54e41755d125b3100fda1a4c48c2a584766cf0b all reconcile. Report semantic identity e8f63e16562c7e6926b8ec689a4733010b42edec735076e2ce868ce5f30e4068 remains explicitly inherited acceptance metadata, not a new body parse.

Completion01:13:46.386456–01:13:47.729821Z,21 completed files/failure_type=null, ee12 sourceSHA and F6/R14 match. Original science_or_exporter_reader_main_invoked:false and scientific_admission:false remain administrative custody only. Preflight no_permission_changes_yet precedes first mutation.

## Limits and local checker chronology

Only supplied original local metadata was read. No target source import/main, Git, tests, Store, SSH/remote reads, chmod, source staging, cleanup, exporter or reader ran. Remote byte equality derives from retained runner hash/stat custody; this review reconciles it without rereading remote bodies. Original unselected-preservation scope remains inherited stat/name witness; complete-byte validation is still delegated to unchanged928. No new unselected-byte/readiness/export/numerical admission claim.

The first local metadata assertion compared a completed journal row directly with a receipt row and refused because the journal adds its own state marker. The corrected comparison excludes only that known journal-only marker and compares every remaining field exactly. This was a local comparison-shape correction before note publication, not a change to any original or repeated remote action.
