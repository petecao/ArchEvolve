# Local cleanup evidence

Created: 2026-10-08 11:11 ET

Seventeen completed, clean, merged local checkouts were recoverably archived and removed at Yan-Ru's request. Main, integration and ticket 17 remain registered. Implementation/evaluation stays paused.

- `inventory-before.json`: all 20 pre-cleanup checkouts, tips, tracked/untracked status, ignored-file counts and directory footprints.
- `removal-review.json` and `cwd-check.json`: exact 17 candidates, ignored non-cache files, embedded-repository checks and no matching open handles or process working directories.
- `app-archive-record.json`: requested archive operations and 17 confirmed archived attachments. A queued request alone is not the completion check.
- `snapshot-verification.json`: verified directory absence and recoverable snapshot refs for all 17 original tips; Git registration absence was independently checked.
- `ignored-originals-manifest.json` and `originals/`: seven byte-exact ignored originals, source paths, sizes and SHA256 hashes. All were verified before and after archiving.
- `local-branch-deletion.txt` and `local-branch-deletion-retry.txt`: 15 ordinary local branch deletions, then the two upstream-divergence refusals resolved after rechecking exact ancestry and recovery snapshots. All 17 local refs are absent.

These records establish local cleanup and recovery. They do not establish remote retirement, recovered host capacity or scientific acceptance. Snapshot refs remain local; original commit tips and this compact cleanup record are retained in the pushed main history.
