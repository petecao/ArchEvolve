# Cleanup follow-up and prospective inactive-process proof

Updated: 2026-10-09 02:16 ET

**The tested correction is ready for review, but remains UNSELECTED and NOTRUN. Original R5 is unchanged.**

| Work | Actual result | Boundary |
|---|---|---|
| User cleanup, 2026-10-09 01:56 ET | `/data` free99822661632B, up63006875648B; RAM125517373440B passes | `/data1` unchanged21979545600B, short569032704B |
| Fresh floor, 2026-10-09 02:12 ET | `/data`99822661632B and RAM125496483840B pass | `/data1`21979545600B remains569032704B below unchanged22548578304B floor; dated resource observation only |
| Same process diagnostic, 2026-10-09 01:56 ET | Same owned PAM S/EACCES, two Z identities/root-owned leaves, absent2332693 unknown | No no-use/readiness exception; source/native controls unchanged |
| Required entrypoint stat check, 2026-10-09 02:05 ET | All16 exact Store/summary/export/control paths present with expected owner/type; four exports match original nine stat fields | No YAML/body/hash/full-catalog continuity or index clearance; route0206 is a label |
| Prospective patchR1 verification | 87/88 isolated cases passed; fdopen constructor failure leaked a leaf FD | Failed original retained, never deployed |
| Corrected patchR2 verification | 96/96 isolated cases pass; all original88 cases plus8 new cleanup failures; all FDs closed | Extracted function/original caller with fake descriptors only; no live `/proc` or full observer |
| Separate Standards / Spec source review | 0 new findings on each axis | SOURCE ONLY; neither review selects a replacement or grants scientific admission |

## Concrete correction

[Review patchR2](originals/lanl17-pre-index-inactive-zombie-proof-prospective-r2-20261009-a5.patch), [96-case result](originals/lanl17-prospective-inactive-proof-isolated-results-r2-20261009-a5.json) and [rationale](originals/lanl17-pre-index-inactive-zombie-proof-r2-rationale-tests-20261009-a5.md) bind prospective body38694B/SHA3698d1a2a34bc6be2585a8e5a9c0029882101268dbf9df5a9a0007823d4ece00, computed in memory without saving a full source copy. Only `inactive_owned_identity` changes; all34 other functions/classes and other top-level AST nodes remain exact against original36052B/be2f68c21a72b4de5deee05f17f48a8cd09342cf3a6e7e17280ff72414dc3fd4.

The proof requires an owned numeric `/proc` directory, stable directory inode/all nine stat fields, truly empty cmdline, exact stable Z/X status, PID/Tgid/PPid/start agreement and four account UIDs. Root-or-account regular kernel leaves use bounded fd-relative O_NOFOLLOW reads with full byte/stat continuity. Foreign ownership, S/other states, malformed metadata, reuse, races, permissions or missing files remain unknown. `closefd=False` plus explicit finally-close owns the leaf descriptor through constructor/read/context failures. No PID/name exception, process action, permission change, native/self/matching-consumer change, sourceR/F6/policy/budget/custody/history change or recoveryR6/PAM waiver is included.

**Approval boundary:** the earlier heartbeat explicitly forbids UID exceptions or immutable guard changes. The replacement cannot be selected without an explicit override of that narrower instruction. It must then receive fresh actual input/source/config approval and a full unchanged source/native/no-consumer/capacity check; isolated tests provide no current host clearance. The `/data1` floor still independently blocks work. Scientific D26/D30/6a and report outcome remain unchanged.

## Outputs still needed

| Remote route (CID p1–p4) | Remaining reader | Retain |
|---|---|---|
| `RAW/campaign-runs/extensa/CID/records/` | 76 → 7a → 32/assembler/6a | Every eligible YAML/YML body; a hash cannot substitute |
| `records/campaign_summaries/CID.summary.yaml` | 76 and32 | Original YAML |
| `RAW/export-CID.stdout` | Original32 selection/trajectory | Original JSON; four files total47907B |
| Original validation quartets, M2/final-export, FINALIZE/control receipts and pinned sources | Pre-index/a2/7a/32/assembly/audit | Physical originals that remaining controls reread/re-hash |
| `RAW/campaign-runs/extensa/CID/site-finder.sqlite` plus existing sidecars | No remaining selected reader | Generated cache can be removed only after actual file hash/size and no-use proof; no deletion here |

`RAW=/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5`; `CID=extensa-gem5-bfs-20261006-p1` throughp4. SQLite fingerprints describe catalog inputs and do not establish file-body SHA. These caches are on `/data`, so removing them does not repair `/data1` headroom. User cleanup and the uncommitted root rule edit remain untouched.

## Compact custody

Four inventories retain19 exact originals/111077B: [actual observations](compact-cleanup-observation-original-inventory.json), [failed/corrected patch and isolated proof](prospective-patch-and-isolated-test-original-inventory.json), [separate source reviews](standards-spec-prospective-source-review-original-inventory.json), [fresh02:12 floor](fresh-floor-0212-original-inventory.json). All bodies match private size/SHA; original nine stat fields are retained separately from copied-file identities. Full private capture streams are retained without repeated publication here. No new full source copy, large report, archive or evaluation output was generated.

Four normal trajectories and original FINALIZE remain complete; actual report unsupported/zero eligible pairs/blind-order unverified/no-switch. Four inventories/indexes, original32 closure, assembly, unchanged6a and final scientific review/acceptance remain pending. Ticket17 stays claimed/all boxes unchecked;14/15 assigned resolved. Heartbeat ACTIVE; formal table/health2026-10-09 02:09 ET, nextby02:39 ET. Remote PRIMARY/originR remains frozen.
