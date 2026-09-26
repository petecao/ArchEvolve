# BFS implementation readiness review

Created: 2026-09-26 (Eastern Time)
Updated: 2026-09-26 (Eastern Time)

This is an interim review while actual evaluations continue. The fixed base is
`1bdb7d4037916dea782c40239a6415b61a47f3c1`; the reviewers used
`git diff 1bdb7d4037916dea782c40239a6415b61a47f3c1...HEAD` and the reviewed
working changes through `c2f987b`. They read repository rules, terminology,
ADRs, the BFS spec and ticket contracts. The audits targeted public workflow,
provenance and evidence integrity, alongside the earlier execution-lifecycle
reviews. They were not an exhaustive review of all 539 changed files and do not
replace the final review after empirical acceptance. The full local regression
runs independently at exact `c2f987b`, before these two narrow repairs.

## Standards

**P2, repaired — profile-package identity downgrade.** Removing
`package_version` bypassed content verification. A temporary public `get` probe
accepted changed source text under the unchanged assembly ID and hash. This
violated the retained assembly identity and explicit legacy-fixture contract in
`docs/bfs-profile-packages.md`. The repair limits compatibility to explicitly
unsealed contract fixtures outside the assembly ID namespace. The public package
group passes 49 tests; all 213 records validate and all six existing legacy
fixtures remain retrievable. Independent recheck rejects the original probe
and removal of every seal field. Original failures are retained in the
[T09 repair receipt](../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/profile-package-identity-repair-20260926.json).

No additional actionable smell finding was established in the reviewed scope.

## Spec

**P2, repaired — paired coverage statistics and receipt admission.** Coverage
discarded frozen sampling and recomputed a paired fixture interval of `[1,1]`
as independent samples, producing `[0.353553,2.309401]`. It also admitted a
consistently rehashed failed pair. This violated spec line 262, which requires
freezing repetition and aggregation rules before assessment. Both coverage
readers now use the frozen sampling and reopen the exact pair with the existing
shared validator. Seven paired/reproduction checks and 24 existing coverage
checks pass. Three independent checks confirm consistent intervals, refusal
when raw trial evidence is missing, and refusal of paired metadata in serial
analysis. Original failures remain in the
[T21 repair receipt](../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/paired-coverage-repair-20260926.json).

The checks use contract fixtures and establish no empirical acceptance or gain.
Tickets 13 and 15–21 retain their outstanding experimental obligations.

Standards: one P2 finding, repaired. Spec: one P2 finding, repaired.
