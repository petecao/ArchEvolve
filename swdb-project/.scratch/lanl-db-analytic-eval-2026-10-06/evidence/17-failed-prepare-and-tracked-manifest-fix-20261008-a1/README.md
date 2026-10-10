# Failed PREPARE and tracked-source compatibility fix

Created: 2026-10-08 11:29 ET

The actual original a4 PREPARE ran 11:22:18–11:22:26 ET and failed before population freeze, provider calls or application outcomes. The source worktree was created at frozen R. The DX100 hook refused with `alias_already_exists`; helper exit and supervisor exit were 1, with no owned survivors. RAW and binding receipt are absent. Failed control and source state remain until separately guarded recovery.

Frozen R already tracks exactly the original 53-file DX100 artifact (641,928 logical bytes, manifest `d5ac642dfe1a2ba5ef548f86c5c269ef54164b55985badc55872288f41504e9d`). Git ignores do not remove tracked files. The original hook only handled absent paths, and its fixture omitted the tracked application directory.

The compatibility fix verifies the existing clean tracked directory against the complete original manifest, exact file/directory namespace, Git blobs/executable modes and stable full stats. It repeats checks at postflight and emits an exclusive truthful `tracked_checkout_manifest` receipt. It changes no application files. The absent-path symlink behavior remains available. Extra files/directories, mutated or untracked trees, and existing symlinks remain refused.

Focused real-Git tests: 23 passed, 2 skipped in 7.03 s. Skips cover SUID/sticky modes this Mac filesystem cannot preserve; Linux remains able to exercise them. Independent source review found no material defect. New hook SHA256 `f5e02c61ec3a227613cbba3a779d5667c8e1207bad3e145574183d4421a6c41a`.

The a3 capture correctly reports restoration of the missing task marker; the combined preservation flag is false. Original R1/a2 histories remain exact. This administration fix changes neither R/C185/F6 nor 9c/28/fa/proof4/scientific budgets/provider/D30 policies. A fresh a5 preparation, new deployment request and fresh source/native/lease/consumer/capacity admission are required; no failed attempt is relabeled or automatically rerun.

[Manifest](manifest.json) preserves original bounded error/metadata streams and source revisions. Git modes do not reproduce private original inode/mode custody. Four scientific campaigns/report/final review remain pending.
