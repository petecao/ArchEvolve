# Spec re-review — 2026-10-15 ET

Scope: uncommitted prototype revision in `/private/tmp/probata-resume-t07`, diff against `418a48d73a187ed725efba5a7089232e3713ecfe`; re-review of both findings in `probata-resume-spec-review.md`. Read-only inspection and retained-output hash verification; no tests, provider calls or real verifiers launched by this reviewer.

**No concrete correctness blocker remains for a prospective counted launch within the explicitly stated trusted-toolchain, sampled/non-atomic boundary.**

1. **RSS omission: fixed.** Active monitoring discovers current ancestry, periodically discovers inherited-marker identities (scheduled every 100 ms), and sums the live PID/birth union once through `_known_rss`. Previously observed reparented descendants remain counted. The new CLI control deliberately creates an orphan allocating 96 MiB and requires the 60 MiB watchdog to fire before timeout and drain its process/lease. This meets the scoped sampled watchdog requirement in `spec.md:50–51`.

2. **Single final-sweep fork/exit race: fixed for the demonstrated interleaving.** Cleanup no longer returns after one empty live check. It requires at least three empty discovery sweeps spanning 50 ms; observed activity resets settlement; failure to settle within five seconds quarantines the lease. The new deterministic CLI control triggers a marked worker's fork/exit during its final inspection and requires its new-session child to die before successful lease release.

**Evidence checked:** all 13 source hashes in `/private/tmp/probata-t07-method20-resource-review-manifest.json` match these worktree bytes. Its retained test-output SHA-256 matches; output records **165 passed in 5.85 s** (164 repository controls plus one independent private CLI control). Runner SHA-256: `0c0cfcd6040637a6df81d47bc65eee588dccd7ca720b6bd324315c8cb7c9151e`; test SHA-256: `faa7c4f4551bf5877ec8e8d249cef61e92ffd8cdecceaf5284a985640b6f62f2`.

**Boundary:** trusted descendants must retain the inherited marker. Discovery/RSS polling and settlement are non-atomic observations, not proof of absence under arbitrary continued fork/exit scheduling, hostile-process containment, or a hard kernel memory quota. The code, recorded summary and METHOD20 document this limitation; no stronger guarantee is approved here.

**Pending before launch:** commit/freeze these exact reviewed bytes, regenerate clean launch/source manifests, and perform live resource/lease/tool preflight. Run20 remains an aborted baseline before provider work, with no proof or negative-control result; fresh counted acceptance remains outstanding. Production eligibility deduplication is outside this prototype fix.
