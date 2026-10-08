# Detached E archive date correction R1 — source-only handoff

The selected R1 changes one authored README literal to Eastern Time prose. The original machine custody time remains explicit: the inspection ran on **2026-10-07 at 23:11 ET**, with original machine custody **03:11:16–17 UTC on 2026-10-08**. This corrects presentation only; it changes no original stream, observation, archived original, policy, source pin, mode, selected path, or admission.

The original author source remains unchanged. The complete one-hunk diff reverses byte-for-byte to that original. AST comparison finds one string Constant value change inside `main`; all other definitions, top-level nodes, FIXED entries, guards, loops and archive rules are exact. `main` itself differs only in the authored README string. No target source import, definition compilation or call, main, test, SSH, Git, project/worktree mutation, archive action or staging occurred. R1 is **NOT RUN** and is preparation for parent full review and separate authorization only. The comparison JSON is unsealed source metadata, not an execution receipt.

Exact pins:

- `/private/tmp/lanl_archive_failed_detached_E_and_reviewed_source_custody_20261008_a1.py` — 27573 B; SHA256 `1240ff7633da19dc680938456b4bad5c8664978d5496ece7b7df4a52366c205f`.
- `/private/tmp/lanl_archive_failed_detached_E_and_reviewed_source_custody_20261008_a1_r1.py` — 27623 B; SHA256 `688fce08a5a3e12c86d6b8ab0706b863175ea53e51d422bf781e38d5821dd427`.
- `/private/tmp/lanl-detached-E-failure-archive-date-r1-complete-a1-derivation-20261008.diff` — 2535 B; SHA256 `e646bef12843aeb9e693ff240e076e44d243e7b79dbc2ceed254a290dfdd7480`.
- `/private/tmp/lanl-detached-E-failure-archive-date-r1-source-comparison-20261008.json` — 4509 B; SHA256 `fc0e4eb371f3e51bd56abaa3a42a8afe2e4378925f58b3eb349b9d08782da586`.

Unchanged definition ASTs: 10; changed AST value path: `module.body[20].body[33].body[10].value.value`.
