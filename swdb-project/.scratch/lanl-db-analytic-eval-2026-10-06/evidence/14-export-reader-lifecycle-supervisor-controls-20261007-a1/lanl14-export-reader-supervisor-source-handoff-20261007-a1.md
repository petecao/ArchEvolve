# Ticket 14 exporter/reader administrative supervisor

2026-10-07 18:57 ET. Source preparation only. No target import, target main, fixture, test, native application, SSH, staging, Git mutation, source copy, export, reader admission, or cleanup execution occurred. No harness has been prepared.

## What this addresses

The unchanged selected exporter and reader can return early after an internal 120-second Git failure. Killing Git's immediate process does not establish that every transport/helper descendant is gone. The source finding is conditional; no survivor was observed. This one administrative supervisor owns the selected Python child and runs cleanup after an early return as well as timeout or TERM/INT/HUP.

Selected source: `/private/tmp/lanl14_export_reader_administrative_supervisor_20261007_a1.py`, 14,471 bytes, SHA-256 `8cad3bc1986de0ae160535d71fbea580deddaf400658753ffe1dfdee76374837`.

Complete direct fa703 derivation: `/private/tmp/lanl14-export-reader-supervisor-complete-derivation-20261007-a1.diff`, 18,702 bytes, SHA-256 `e2d98fbe1101ea2604d03f318f6edd81aae1af75c869bbcbb9356e41fbb93e0e`. The entire diff is retained, with no omitted hunk or numeric normalization.

## Exact inherited sources

| Role | Original SHA-256 |
| --- | --- |
| fa703 supervisor, `/private/tmp/lanl17_metadata_supervisor_cleanup60_a4.py` | `fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0` |
| Original 31e cleanup, `/private/tmp/lanl17_parent_helpers.py` | `31e1d71bc6e9ef4a5a5f1d5fbff136ceef249935f8f00601edf45277fce249ec` |
| Frozen `swdb/processes.py` | `bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289` |
| Selected exporter 928 | `928af82facd9f36dfdbca6595d2c2e9d1091dd0064c9fe53fc41c163879e026e` |
| Selected reader 690 | `6909c422990a071b1a8d08c634c1c086f0218c5851d38996b6f4798759499570` |
| 03 descendant-boundary source review | `f33980054c708030f8ce22eafb76f0085de6e2be8c9682815f7ce418cdceccaa` |

The 185-module F6 digest is `f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3`, from frozen C `f893fed400347ed23d92e917d8bde21b75e5375d`. This supervisor verifies the exact module bytes; it makes no Git ancestry, clean-checkout, full-catalog validation, final-R, or scientific admission claim. Those existing parent and selected-control gates remain separate.

## Deliberate changes from fa703

1. Production modes are only `exporter` and `reader`, each bound to its exact selected source SHA. Original helper modes, providers, scientific execution, codec, validation, reports, canonical IDs, and domain source bytes are untouched. The caller supplies the original selected control's argument tail without rewriting it.
2. Cleanup loads original 31e and frozen `stop_group` separately from the selected child. Both functions are called from those pinned files, with byte and bundle checks before launch and again after cleanup. The original cleanup implementations are neither copied nor modified.
3. The actual future native Python executable/path/SHA is required explicitly. It must be a non-symlink Linux x86_64 ELF owned by root or UID114316761 and not writable by another account. The supervisor must itself run under that same resolved executable. Child argv is exactly `[native_python, '-B', selected_source, *original_tail]`; no shell, eval, helper mode insertion, environment replacement, or retry is added. Native paths and hashes remain future parent-supplied facts.
4. Exact runtime account is Linux `mbit10`, real/effective non-root UID114316761. All source/private input path components reject symlinks. Selected/cleanup/supervisor/process file pins, own-source pin, F6, and administrative read bounds are checked. Cwd is an explicit owned directory, not a guessed host path.
5. Output is one explicitly selected fresh `lanl14-export-reader-control-<suffix>` directory, strictly below `/data/yanruj/EvolveSWDB_runs` or `/data1/yanruj/EvolveSWDB_runs`. Its existing parent must be owned/private0700 and non-symlink. The new directory is0700; each original stream/JSON is exclusive0600. It must not overlap the supplied project or cwd or contain a code path. No parent directory is invented or created by the supervisor. Parent must also review disjointness from the actual scientific raw folder and export checkout because those are in the opaque original child tail.
6. The core handlers/wait/finally structure remains direct fa703 derivation. Subreaper is enabled **before** child creation; child starts a new session. Finally ignores repeated TERM/INT/HUP, then calls `stop_group(child, grace_seconds=15)` followed by original `cleanup_owned()` (TERM15/KILL5). It checks survivors, cleanup exceptions, subreaper result, and immutable source bytes. An early child7 remains supervisor exit7 when cleanup succeeds; child0 with cleanup failure is nonzero. Original returned child status, final child status, timeout/signal/error and cleanup are retained separately.
7. One private `cleanup.json` preserves the complete returned cleanup structure with exact file SHA/size. The compact sealed `receipt.json` is at most16,384 bytes and includes cleanup counts/pin, hashes, source identities, status and raw-stream sizes/modes. Original stdout/stderr remain private remote files; their bodies, full argv, environment and auth are omitted. No diagnostic truncation, application-result parsing, or scientific-output limit is introduced. Raw stream SHA checks, capacity and any transfer are parent work; the supervisor does not re-read those stream bodies.
8. Internal `supervise(..., fixture=False)` is retained for a future expressly reviewed lifecycle test. There is no CLI fixture flag or arbitrary production source selection. It still checks selected/cleanup/C/F6/native bytes and fixed administrative mode cap; a fixture receipt is visibly `fixture:true`. No fixture/harness or runtime proof exists for this derivative yet.

Ten complete original definition ASTs remain exact: `Refusal`, `Interruption`, `digest`, `seal`, `sha`, `now`, `bundle_identity`, `require`, `load_module`, `enable_subreaper`. The complete changed original definitions are `load_context`, `supervise`, and `main`. New definitions are private argument handling, checked code/path/private file operations and the immutable check. Only source AST parsing, hash reading and complete diff construction were performed.

## Prospective direct invocation

All angle-bracket values below are **required future actual parent-reviewed inputs**, not known paths, pins, facts, execution or approval. Select exactly one row:

| Mode | Explicit child administrative wait | Single GNU outer TERM deadline | GNU KILL margin |
| --- | ---: | ---: | ---: |
| exporter | 18000s | 18120s | 60s |
| reader | 14400s | 14520s | 60s |

These are finite administrative allowances, not measured bounds or duration guarantees. They do not modify selected controls' 120-second Git calls, 3600-second validation/codec limits, scientific budgets, or admission checks. The nominal two cleanup waits total40 seconds, but enumeration/hashing/publication also consume time. The outer adds120 seconds plus KILL60, without claiming those allowances prove termination under all host conditions.

```text
<PINNED_GNU_TIMEOUT> --signal=TERM --kill-after=60s <18120s_OR_14520s>
  <PINNED_NATIVE_PYTHON> -B <FULLY_DELIVERED_SUPERVISOR_SOURCE>
  --action <exporter_OR_reader> --timeout-s <18000_OR_14400>
  --selected-source <FULLY_DELIVERED_UNCHANGED_928_OR_690>
  --cleanup-helper <FULLY_DELIVERED_ORIGINAL_31E>
  --project <EXPLICIT_FROZEN_F6_SWDB_PROJECT>
  --python <PINNED_NATIVE_PYTHON> --python-sha256 <ACTUAL_NATIVE_SHA256>
  --supervisor-sha256 8cad3bc1986de0ae160535d71fbea580deddaf400658753ffe1dfdee76374837
  --cwd <EXPLICIT_REVIEWED_CHILD_CWD>
  --control-directory <FRESH_PRIVATE_REMOTE_ADMIN_CONTROL_DIRECTORY>
  -- <EXACT_ORIGINAL_SELECTED_CONTROL_ARGV_TAIL>
```

The parent must review the actual executable/argv/cwd/environment/private output paths, full delivery, lifecycle proof and current lane/capacity/14-completion gates before any invocation. This is one GNU outer around one supervisor around one unchanged selected Python control; no recursive wrapper or new source stager. Parent must privately capture the supervisor's own startup/outer stdout/stderr using its existing invocation mechanism; no such actual mechanism, host native path or extra wrapper is supplied here. Account HOME, auth and original environment are inherited unchanged and are not read or printed.

## Receipt and limitations

Receipt format is `swdb.lanl14-export-reader-administrative-supervisor.v1`, canonical JSON SHA-256 with explicit `canonical_ensure_ascii:false`. Original full cleanup JSON is an **unsealed** exact administrative snapshot pinned by bytes/SHA. Supervision success does not mean export/reader scientific admission; every receipt has `scientific_admission:false` and `child_scientific_result_assessed:false`. A nonzero child remains nonzero even if cleanup succeeds, with no retry or success inference.

Failures before launching any child may refuse without a lifecycle receipt. Failures during receipt I/O, SIGKILL, crash or exhausted outer allowance can prevent publication; no guarantee or fabricated receipt is claimed. Original 31e's `/proc` visibility/UID/start-time semantics and `stop_group` semantics are inherited unchanged; they do not establish host-wide exclusion or cleanup of unrelated processes. Parent quiescence and concrete host checks remain necessary. Original child raw stdout/stderr are unbounded private files subject to parent capacity review; this derivative does not alter their semantics with a process-wide file-size limit. The complete original cleanup snapshot is also retained remote without a new arbitrary truncation rule; only compact returned custody has the fixed16KiB limit.

No actual selected-source invocation, cleanup proof, descendant survivor observation, scientific export/admission, fresh14E or actual17 input/campaign is implied. Parent and03 source reviews, any meaningful new early-nonzero Linux cleanup smoke, full actual argv and final14 results are pending.
