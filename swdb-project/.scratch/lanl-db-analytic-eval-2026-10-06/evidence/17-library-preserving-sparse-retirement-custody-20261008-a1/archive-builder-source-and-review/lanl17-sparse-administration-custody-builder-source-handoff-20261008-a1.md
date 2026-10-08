# Sparse-administration custody archive builder — 2026-10-08 ET

SOURCE ONLY / NOT RUN. This is a local archive-only builder for the one parent-selected evidence directory. No source imports, definition compilation/calls, tests, Git operation, main/archive execution, project mutation, staging, SSH or scientific action occurred. Only source text and its AST were read during preparation. Parent will supply a complete final input ledger and review/run once later; the pending ledger cannot be used as an actual input.

Source: `/private/tmp/lanl17_build_sparse_administration_custody_archive_20261008_a1.py`, 17,329 B / SHA256 `7c1e8a15494f47a51102468e9f9d681c8938fe8ae2c650a931b9719b84b9bb33`. Source AST SHA256 `197b390eea5131de8401daade92fccd44276542df0d2dc5c2ec80f3e9c9efbfe`; 20 function definitions. Neither main nor definitions were invoked.

The reviewed pending ledger is `/private/tmp/lanl17-sparse-administration-archive-input-materials-pending-20261008-a1.json`, 44,074 B / `60875eb08c9563e0c9541dc457cbc98ef076de07fe82dcbb540b8a5fdeb528ae`. It names 80 original rows / 54,793,728 B and still declares new controls/copy/reviews pending. These are input-preparation observations, not a created archive or input acceptance. The builder requires `new_selected_control_and_copier_sources_still_pending:false` in the final separately pinned ledger.

## Exact future scope and argv

The worktree is fixed to `/Users/yanrujhou/.codex/worktrees/lanl-ticket17/ArchEvolve`, branch `codex/lanl17-storage-guard-cost`, initial clean HEAD `5e12a9796432654d88def24ecea617d16ca605b2`. The archive prefix must be absent and is exactly:

`swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-library-preserving-sparse-retirement-custody-20261008-a1`

All actual future values below require parent FULL review. No source or final ledger is inferred from filenames:

```sh
python3 -B /private/tmp/lanl17_build_sparse_administration_custody_archive_20261008_a1.py \
  --builder-source-sha256 7c1e8a15494f47a51102468e9f9d681c8938fe8ae2c650a931b9719b84b9bb33 \
  --input-ledger /private/tmp/EXACT_FINAL_LEDGER.json \
  --input-ledger-sha256 EXACT_FINAL_LEDGER_FILE_SHA256
```

The builder supplies no checkout/branch creation, staging, commit, fetch, reset, chmod, cleanup or source/control execution. Root must first establish the exact branch/worktree through its own approved operations. `-B` keeps bytecode creation outside this archive out of the execution. The builder's finite 900-second deadline and read-only Git 60-second bounds are administrative, unmeasured limits; an outer finite parent capture remains a separate selection.

## Ledger contract and bounds

Final ledger format remains `swdb.parent-sparse-administration-archive-input-materials.v1`, original UNSEALED, with exact branch/base/prefix, `archive_builder_or_project_write_performed:false`, pending flag false, exact `original_bytes_total`, and `rows` (1–192). Each row supplies existing `original_path`, `relative_archive_path`, integer `bytes`, 64-hex `sha256`, `scope`, and `execution_or_evidence_boundary`. Extra original identity/canonical-policy/provenance fields are retained verbatim in the manifest's `original_claims`; the builder does not infer or recompute unknown original seals.

Ledger is at most 2 MiB and parsed with duplicate-key/nonfinite refusal. Each original is an explicitly pinned canonical nonsymlink regular single-link file owned by the local executing account under `/private/tmp`, at most 64 MiB. Total unique originals are at most 128 MiB, verified against ledger total. Absolute/parent/backslash/control-containing archive paths, duplicate origins/targets, reserved README/manifest routes and file/directory collisions are refused. Per-component safe basenames and existing owned canonical evidence ancestors are required. All original byte/SHA/full stat checks finish before any archive prefix exists; a second complete source check precedes publication.

Rows >=256 KiB whose relative filenames end in `.json` or `.stdout` are streamed into `<original-relative-path>.gz`; other rows retain exact bytes at their original relative path. Gzip uses empty filename and mtime 0, exclusive 0600 output and fsync. No JSON body is parsed or reserialized. Both the first decode and the final decode compare every decoded chunk against the actual original bytes under their pinned original full stats, with bounded decoded size and complete SHA. Encoded bytes/stat and original bytes/stat are independently reread finally. Compression is a representation change, not an original evidence change. The original row-relative path and encoded representation/pins are explicit in the manifest.

## Authored custody and preservation

Only the absent prefix and new descendants are created (0700 directories, O_EXCL/O_NOFOLLOW 0600 files). Sources are not edited. Existing ancestors are traversed, not chmodded. Partial failures remain for parent custody; no rollback/delete/replay is supplied. The builder checks the exact recursive file inventory equals original archive targets plus README and manifest, rereads authored bytes, and fsyncs every created directory.

The new manifest alone is sealed with explicit `canonical_ensure_ascii:true` and SHA256 of the complete object before adding `identity_sha256`, sorted compact JSON and `allow_nan:false`. Original JSON identity/canonical-policy fields survive byte-exact decoding and, when supplied in the ledger, verbatim metadata propagation. Known and unknown original seal policies are not normalized or recalculated.

README is dated 2026-10-08 ET and distinguishes archival custody, historical creation-time NOT RUN labels, separate genuine execution originals, and absence of retirement/visibility/reserve/scientific admission. Builder and ledger remain separately pinned outside originals unless a parent explicitly includes their exact source bytes as ordinary ledger rows; the manifest never contains a circular claim that it hashes itself.

Read-only Git pins HEAD/branch/tree, scientific-source tree, canonical-records tree and ref inventory before/after. Tracked/cached changes are refused, initial status must be clean, and final untracked additions must be exactly the archive inventory under the sole prefix. Global/system Git configuration and fsmonitor are disabled for these reads; no configuration is written, no config body/URL/auth is returned. Success prints one compact original UNSEALED archive-only receipt containing archive cardinality, manifest pins and preservation facts, never a cleanup/capacity or campaign admission. Bounded failures expose exception class/message digest only and retain partial files.

No actual final ledger, archive result, scientific/source acceptance or administrative-branch delivery is claimed by this packet. Parent FULL source/ledger review and controlled execution remain pending. No synthetic tests are proposed or run; the copy/roundtrip checks are in the builder itself.
