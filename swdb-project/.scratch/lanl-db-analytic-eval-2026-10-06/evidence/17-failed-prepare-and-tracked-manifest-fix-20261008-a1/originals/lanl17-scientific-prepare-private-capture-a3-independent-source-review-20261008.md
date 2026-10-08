# Independent source review — 2026-10-08

Conclusion: PASS for the authorized a3 start-metadata correction. No material defect found in this delta. This is a source-only conclusion and does not establish remote execution, preserved live environment, successful prepare, or scientific admission.

Candidate: `/private/tmp/lanl17_capture_reviewed_scientific_prepare_20261008_a3.py`, 29451 bytes, SHA-256 `af41955121ea6db8d5064ee543130b5e5b38a0c057011a2b748be7b6f6b4c93c` (matches expected).
Baseline: `/private/tmp/lanl17_capture_reviewed_scientific_prepare_20261008_a2.py`, 29325 bytes, SHA-256 `bdbfa72feb402d4de9dc09d685e999e0b09be70cf578d3ad1a6654ab3edba3b6`.

The byte diff changes only the start.json metadata dictionary on source line 139:
- HOME_CODEX_HOME_original_token_preserved changes from True to False.
- HOME_CODEX_HOME_preserved is added as True.
- task_marker_restored_to_public_CODEX_HOME is added as True.
- task_marker_value is added as `/data1/yanruj/.codex`.

After removing exactly these four dictionary entries, the complete Python ASTs are identical with location attributes excluded. BOOT, direct_argv, PUBLISHED_OVERRIDES, PRESTARTUP, SSH/public route, and every other AST node remain unchanged. The unchanged PRESTARTUP validates inherited CODEX_HOME, refuses a nonempty mismatched task marker, then exports the task marker to the validated fixed path; it does not rewrite HOME or CODEX_HOME. The revised metadata accurately distinguishes preservation of those environment values from restoration of the task marker. start.json remains marked execution_not_yet_started=True and sealed=False, so these fields describe the intended route rather than a verified successful remote observation.

Method: local source bytes, AST parsing, literal extraction, byte diff, and static shell reasoning only. Neither selected module was imported/executed; no selected shell snippet, tests, SSH, or remote command ran. a2 source and its historical review were preserved. This new review records only the a3 correction.
