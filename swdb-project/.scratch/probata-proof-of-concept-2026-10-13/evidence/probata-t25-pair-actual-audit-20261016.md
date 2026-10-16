# Pair-only actual acceptance — 2026-10-16 ET

PASS for the six-record pair profile at frozen
`1278f2d9f24015c62b13d5da48a8a7f45600570f`. Ticket 25 remains open.

| Actual subject | Ordinary goals | Smoke | Verdict |
| --- | --- | --- | --- |
| Four original int/int pair bodies | 31 Valid | 4 passed | Four proven records |
| Safe pair-only caller | 24 Valid | 9 passed | proven |
| Wrong-field caller, unchanged postcondition | 23 Valid, one ensures timeout | 9 passed | not_proven |

The original default/value/copy/assignment bodies and contracts retain their
exact text hashes. Both callers pin the same four actual proven records at those
hashes. RTE, initializedness, initialization filtering refusal, fresh reports and
smoke remain enabled. The negative is an ordinary open obligation, not a
refutation or a smoke failure. All six records retain `contract_fixture` and
`method.pair-workflow-fixture`; they do not select a new method.

The Linux project-context composite is
`0c14b3a1ff208deb26c40c2782bd445dda61a29a42a918c9a92bf08e94eb8a47`.
Every record's compiler runtime equals the retained project snapshot, and its
method pins that composite. The Mac composite and bootstrap monorepo context
are separate historical identities. Checker identity is
`76e1a83ace53083ab1f1cb01dde39700ea3bbd59a4783cc997149321413e2eb2`.

The read-only cold audit found no errors across 2,023 declared physical-file
references, 1,005 unique hashed files, 198 source modules and eleven profile
source pins. It independently replayed the pinned pure fresh-report classifier
and matched all six verdicts, failure classes and full goal lists. AST extraction
avoided importing `swdb` or probing tools; only the helper import was replaced
with the separately extracted original helper and independently rebuilt checker
identity. No compiler, verifier, provider or process signal ran during auditing.

The profile passed its one actual test and completed in 279.25 seconds. The
whole guard exited 0 after 282.605 seconds, peak 733,483,008 bytes; the outer guard
exited 0 after 284.695 seconds, peak 784,863,232 bytes. Neither timed out or exceeded
memory. Node 0 generation 586 naturally released at 2026-10-16 00:22:33 ET; the
other socket and legacy leases were also released. Source-after is clean and
unchanged at 1278f2d9.

Three finite same-UID command-line/cwd prefix scans at 00:25:56 ET found no
matching run/source process. Each retained cwd errno 13 denials for `(sd-pam)`
and `sshd`; these are explicit inspection limits. This is not an environment or
token scan, a universal absence claim, or cleanup authorization.

Raw output remains on mbit10 at
`/data/yanruj/EvolveSWDB_runs/probata-reviewed-1278f2d9-t25-pair-public-v1`
(85 files, 1,701,621 bytes) for the coordinator, ticket 25 acceptance and independent
review. Only compact path/hash/result metadata was copied to the Mac.

Full audit JSON: `probata-t25-pair-cold-audit-v3-1278f2d9-20261016.json`, SHA256
`7cfc39a6dd182f89d9d107b82d2d8e47c9b4564e75cdceb458ecafd2bdc29084`.
The companion summary JSON retains exact record IDs, dependency IDs and hashes.
General vector/member-body coverage, wider pair types, heap/lifetime integration
and the eventual combined-method acceptance remain outside this scoped result.
