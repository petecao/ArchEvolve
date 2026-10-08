# PREPARE capture a3: explicit marker-restoration metadata

2026-10-08 ET. SOURCE ONLY; selected capture and remote PREPARE NOTRUN.

Selected source: `/private/tmp/lanl17_capture_reviewed_scientific_prepare_20261008_a3.py`,
29,451 bytes, SHA256 `af41955121ea6db8d5064ee543130b5e5b38a0c057011a2b748be7b6f6b4c93c`,
exclusively created, owned by the current user, mode0600, link count1.

The parent reported that the new SSH login retained public CODEX_HOME route
`/data1/yanruj/.codex` but lacked the task marker. The unchanged a2 PRESTARTUP checks
existing CODEX_HOME against that route, refuses every nonempty mismatched marker,
and exports only the task marker to this checked route. No HOME or CODEX_HOME
assignment occurs; auth/config bodies are neither read nor changed.

Root source review rejected the unchanged legacy combined start-metadata key in
a2 because True could imply the marker preexisted. a3 corrects the new original
start metadata directly:

- HOME_CODEX_HOME_original_token_preserved: false.
- HOME_CODEX_HOME_preserved: true.
- task_marker_restored_to_public_CODEX_HOME: true.
- task_marker_value: /data1/yanruj/.codex.

The start original is preregistration before SSH execution. The restoration field
records the selected prestartup recipe, not successful launch or remote completion;
its surrounding execution_not_yet_started and scientific-admission-unassessed
fields remain unchanged. A later transport/bootstrap result must still be assessed.

The combined legacy True claim in a2 is not selected or explained away. R1 and a2
remain byte-exact source-only history. The root correction is this distinct a3.
Only the four metadata keys above change relative to a2. The complete AST matches
a2 after projecting those four dictionary keys; BOOT, direct_argv,
PUBLISHED_OVERRIDES, PRESTARTUP and all remaining structure are identical.
No reviewed source was imported, compiled, lifted or called; no tests, shell, SSH,
selected helper, provider, source staging or scientific action occurred.

Complete diff: `/private/tmp/lanl17-scientific-prepare-private-capture-a3-a2-derivation-20261008.diff`,
2,625 bytes, SHA256 `1ffb1530ca9fcd8c9f1b5bf23b87d9358705902f4deaff87fdeb72e720e32e68`.
Preparation: `/private/tmp/lanl17-scientific-prepare-private-capture-a3-source-preparation-20261008.json`.
Parent must select the a3 source hash, review real admission/retirement/host/native
pins, and later assess original PREPARE results. This source packet supplies none
of those actual runtime outcomes.
