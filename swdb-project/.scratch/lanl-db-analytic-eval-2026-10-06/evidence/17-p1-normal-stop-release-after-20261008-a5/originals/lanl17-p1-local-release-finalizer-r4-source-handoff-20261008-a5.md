# p1 local release author R4 — native timestamp precision

Selected author: `/private/tmp/lanl17_finalize_p1_normal_release_request_20261008_a5_r4.py`, 18,684 bytes, SHA256 `5f74373dda97c28ae4e3aa2b74923d31bf747fc967d59b626da9fac836a3ac0f`, mode 0600.

Complete R3 derivation: `/private/tmp/lanl17-p1-local-release-finalizer-r4-complete-r3-derivation-20261008-a5.diff`, 4,253 bytes, SHA256 `cf4b8cb467490385eabdbea1a3a5c1d6efcf17417501029d3fa8c91e8836f09a`.

Selected terminal reader: `/private/tmp/lanl17_read_p1_normal_terminal_originals_20261008_a5_r2.py`, 7,926 bytes, SHA256 `6ecee4f1ccd0227527da4cc5831cbc42aeb1120dd1b5f4656660dac92cb08818`.

Use preserved R2 handoff CLI/input instructions, substituting selected author `_r4.py`; retain all R3 native-wrapper/fresh-live obligations. Do not use historical reader R1 or author R3 for actual construction.

Exact changes from R3: selected terminal reader pin, exact reader `stop_within_native_end` helper AST, and one chronology expression. Native wrapper 10,510-byte/00c269 source `socket_lane.sh` line 91 emits `date -u +%Y-%m-%dT%H:%M:%SZ`; line 240 records that timestamp after the child returns. Thus canonical lane end represents a whole-second bin. The author retains original strict ordering where stop end is at or before lane end, and permits stop end after lane end only within the half-open interval `[lane.end, lane.end + 1 second)`, requiring canonical whole-second UTC `Z` lane end. The exact helper is inherited from selected reader R2. No timestamp or receipt bytes are normalized or rewritten.

All other chronology remains strict: dispatch <= stop.start < stop.end; lane.start <= stop.start; native.checked >= max(stop.end, lane.end); native.checked <= terminal.checked <= fresh.parent <= current.now <= valid.until. Explicit parent validity remains positive and at most 300 seconds, rechecked immediately before exclusive output writes.

Historical actual query at `/private/tmp/lanl17-p1-native-release-query-capture-20261008-1449-a5/native-observation-original.json`: 5,403 bytes, SHA256 `73e8d27cb144a73cb48dc7b06cb28337d231adbea29d708fb8633bc682c3fc62`. Metadata reports lane end `2026-10-08T18:48:28Z`, sealed stop end `2026-10-08T18:48:28.810375+00:00`, checked UTC `2026-10-08T18:49:32.183307+00:00`, release_ready true, normal_exit_set_only true, generation 511, four original exits integer zero. This historical observation explains the precision correction; it does not substitute for fresh live admission.

Frozen control compatibility checked read-only:
- Producer32 lines 329-335 consumes original lane hash only and requires release checkedUTC >= exact stop.end.
- B08 lines 253-257 requires original lane hash and release checkedUTC >= exact stop.end.
- Auditor6a lines 1074 and 1212 uses original stop.end <= release <= AFTER chronology and original lane hash, without imposing lane.end >= stop.end.

Request schema, frozen scientific sources, policies, manifest, dispatch, native source/writer descriptors, four original fullstat/byte/hash comparisons, all four zero exits, generation 511, cleanup/source checks, action configuration, budgets and canonical request seals are unchanged. The native wrapper remains omitted only from generic private action source_pins because its actual mode is 0777; local/M2/writer/producer source checks remain. Do not chmod native files. Parent must freshly verify exact native wrapper bytes and physical metadata immediately before release32.

Fresh native generation/no-holder checks are still mandatory before32 and before/after B08, with node0 reserved through AFTER custody. Immutable snapshots do not police subsequent lease reuse. Parent normal-trajectory review remains required; authoring itself does not establish scientific completion.

AST syntax, exact reader-helper AST identity and inverse derivation passed. No imports, tests, SSH, source runtime, staging, controls or finalizer execution occurred. R3 and older sources remain preserved NOTRUN. No finalized request/action outputs were authored.
