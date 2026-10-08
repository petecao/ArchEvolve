# Two-source administrative Git copy R1 — 2026-10-08 ET

SOURCE ONLY / NOT RUN. Parent assigned exactly two strictness fixes to the original copy flow and bootstrap fsmonitor consistency. No source imports, definition compilation/calls, tests, Git operation, SSH, main/copy, project mutation or selected control execution occurred. Originals and their original NOT RUN handoff remain unchanged.

Selected R1 sources:

- `/private/tmp/lanl17_copy_sparse_retirement_sources_from_administrative_git_20261008_a1_r1.py`: 11,828 B / SHA256 `94f5f33bda82c7d64a9c4644c6630aa5fde598fc7d950d94e7ab74e3e60a37a9`.
- `/private/tmp/lanl17_sparse_retirement_copy_native_stdin_bootstrap_20261008_a1_r1.py`: 5,620 B / `fd3c44fdcb7c69e6b6bfbe27221a8508547657b94e7af4b94bec47fc2cd09d8b`.

Exact complete derivations and original UNSEALED static comparison:

- `/private/tmp/lanl17-sparse-two-source-copier-r1-complete-original-derivation-20261008.diff`: 1,725 B / `d741e600a6a286b951ea9395261b8de0596107bfe83a76befe47dcad7267c7c4`.
- `/private/tmp/lanl17-sparse-two-source-bootstrap-r1-complete-original-derivation-20261008.diff`: 1,986 B / `b7ddc3b3d123ee80f88639ed0c72d56c68e8f4543b9b45590ee43b46fea91f3c`.
- `/private/tmp/lanl17-sparse-two-source-git-copy-r1-static-comparison-20261008-a1.json`: 2,844 B / `e5becde5843a654f59a6c3163a4d64b70e636d918759fb746459758415fcd247`.

Both read-only Git helpers now reject nonempty stderr even after native exit 0. Raw warnings remain private; they are not discarded as success or printed in error custody. Both native Git argv vectors include global `--no-replace-objects` before command options, so supplied administrative commit/tree/blob identity does not traverse replace refs. The bootstrap also supplies the same `-c core.fsmonitor=false` already present in the copier. The only changed function definition in each source is `git`; the bootstrap's one `REL` assignment now names the R1 copier. Closed reversal restores every original byte. All other imports/constants/functions, source/copy row count, caps, path/mode rules, signal handling, receipt interfaces and guards are unchanged.

The original full flow handoff remains `/private/tmp/lanl17-sparse-two-source-administrative-git-copy-source-handoff-20261008-a1.md` (6,792 B / `e3c3b9f066397868533e7fb5669729f380b0e6a6019b90de70e4b109ce0e13a7`), with original copier 11,785/`03066928…` and bootstrap 5,546/`828ca407…`. It describes the unexecuted initial packet, not R1 execution. R1 changes only the pins/transport basename and native Git strictness above.

## Exact future argv contract

Every uppercase value remains a required actual parent-reviewed input. This is not an actual populated request, delivery claim or invocation:

```sh
/usr/bin/timeout --signal=TERM --kill-after=60s 600s \
  /usr/bin/python3.12 -B -s - \
  --copier-source-bytes 11828 \
  --copier-source-sha256 94f5f33bda82c7d64a9c4644c6630aa5fde598fc7d950d94e7ab74e3e60a37a9 \
  --administrative40 ADMIN40 \
  --evidence-directory swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-library-preserving-sparse-retirement-custody-20261008-a1 \
  --destination /data1/yanruj/lanl17-sparse-retirement-source-FRESH_ATTEMPT \
  --guard-basename EXACT_GUARD_BASENAME.py --guard-bytes ACTUAL_GUARD_BYTES --guard-sha256 ACTUAL_GUARD_SHA256 \
  --wrapper-basename EXACT_WRAPPER_BASENAME.py --wrapper-bytes ACTUAL_WRAPPER_BYTES --wrapper-sha256 ACTUAL_WRAPPER_SHA256
```

Stdin must be the exact selected R1 bootstrap above. Its exact copier Git route is:

`<same-evidence-prefix>/Git-private-two-source-copy/lanl17_copy_sparse_retirement_sources_from_administrative_git_20261008_a1_r1.py`.

The two selected controls remain at `<same-evidence-prefix>/selected-sparse-control-source/<their exact original basenames>`. No additional source row is copied. Parent must already deliver/fetch the administrative ref while PRIMARY stays on frozen 5e/yanmain/originintegration. The source makes no fetch/checkout/reset/chmod/source-main call.

Original private 0600 transport capture must precede outer GNU/Python startup; parent verifies bootstrap bytes and native executable pins, preserves HOME/CODEX_HOME unread, and clears only child routing overrides. Copier 180-second deadline, per-Git 30 seconds, 16 MiB streams, 512 KiB per control, exclusive 0700/0600 copies/fsyncs, final stat/byte/ref/config/native checks and bounded UNSEALED receipt remain exact. Neither current source nor future receipt grants cleanup, capacity, consumer or scientific admission. Parent FULL source/actual-argv selection is required before one future copy.
