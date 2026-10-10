# 07 — Install the shortlisted verifiers on the Mac

Created: 2026-10-09
**Type:** task
**Status:** ready-for-agent
**Blocked by:** 02
**Map:** `../map.md`

## Question

Install the verifiers shortlisted in 02 on the Mac (Homebrew or prebuilt binaries; nothing that
needs sudo), run a one-assertion smoke check with each, and record versions, install paths and
disk used. Keep at least 50 GB free.

Done when each shortlisted tool runs, or its failure is recorded with the cause.

## Comments

- 2026-10-09: shortlist from 02: ESBMC 8.5 (bounded and k-induction), Frama-C/WP 33.0 with RPP
  0.0.4 (unbounded; C port), crux-llvm 0.12 (optional). VerCors 2.4.0 waits for the concurrency
  phase. Frama-C installs through opam, which can take several GB; check free disk first.
