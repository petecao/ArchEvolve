# Stream runner output isolation repair

2026-10-16 ET. Executable admission successor901b635e preserves every production
module and vocabulary byte from13d782; it changes only the stream runner and
adds no-tool public controls. Prior590e05/13d782 evidence remains immutable.

Independent review found that lexical prefix checks admitted `..`, symlink
aliases into the source, and output ancestors containing the checkout. RED
controls reproduced3failures/1pass: all3bad paths reached the explicit bootstrap
stand-in and wrote fixture directories; the disjoint path behaved as intended.
The source and Git guards in those controls are explicitly simulated, so they
cannot hide the path bug or accidentally invoke a formal tool.

The runner now resolves the source/output and refuses overlap in both directions
before `mkdir` or bootstrap work. The Python stand-in executes the runner's
actual pure path-resolver program, not an oracle replacing it. GREEN controls
pass12/12 with3coordinator-only actual cases skipped in0.99s; guard1.388s/72.9MB,
no OOM/timeout. The3bad outputs create neither marker nor cache/tmp directory;
the valid disjoint path reaches only the named exit99 bootstrap stand-in.

[Exact receipt](t28-stream-runner-output-controls-20261016.json) retains commands,
resources, JUnit, logs, stand-in source and final source hashes. No compiler,
formal/version tool, collection, SSH or remote evaluation ran. The original
40/3 profile stays pinned to13d782: its old runner source pin is deliberately
replaced in901b635e and must be reviewed from the old Git blob, not relabeled as
the new worktree file. Production/source-policy/partial-subject and pending
source refinement/body/liveness boundaries remain unchanged.
