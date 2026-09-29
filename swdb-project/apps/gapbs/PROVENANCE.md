# Provenance of this copy of gapbs

Copied 2026-09-22 (Eastern).

- Upstream: https://github.com/sbeamer/gapbs
- Commit: `2972aeb2703165bafd921222f4ed7196f542d3a8` (committed 2026-07-28, "update ci")
- License: BSD-3-Clause (`LICENSE`)
- What was copied: every file tracked at that commit except `.github/`. Nothing was
  edited. MemAcc's local copy (with its added `pr_push.cc`) was not used.
- How to check: clone upstream, check out the commit, and compare
  `git ls-files | grep -v '^.github' | xargs shasum -a 256` with this folder.

This file is the only addition. The application record `records/applications/gapbs.yaml`
points here through `source.local_path`.
