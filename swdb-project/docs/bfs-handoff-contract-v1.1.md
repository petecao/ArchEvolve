# Functional evaluation-result handoff, format 1.1

Updated: 2026-10-06 ET. This additive extension applies only to evaluations
produced by `swdb.strict-functional-estimate.v1`. Other evaluations and message
kinds retain [the format 1.0 contract](bfs-handoff-contract-v1.md).

The envelope remains `swdb.bfs.handoff.evaluation_result`, with
`format_version: '1.1'`. Its record schema and request versions remain 0.4 and 1.0.
The content adds `estimate` with the immutable estimate ID/hash, estimated basis,
seconds, ratio, verdict, error band, baseline and count/target/protocol/estimator
identities. Required unknowns retain null values; `within_error` remains the
verdict until a valid band exists. Incomplete evaluations carry `estimate: null`.

Correctness adds `scope: functional-target`,
`hardware_correctness_claim: false` and retained certification provenance.
The certificate records the finite strict-functional matrix and kernel check,
its command/source manifest and explicit exact-identity reuse. The performance
timing trial count is zero and `performance_claim` is `none`.

Rendering verifies cached fields against their referenced records and rejects
altered evidence or ratios. Later procedure updates do not invalidate archived
history retrospectively. New evaluations require the current procedure.
See [functional evaluation commands and binding rules](reference/bfs-functional-estimates.md).

The historical example archive includes simulator-linked rewrite dependencies.
Its read-only checker now takes an explicit rendering policy; the default team
policy continues to refuse those dependencies. For example, using an existing
Extensa context:

```sh
python3 scripts/bfs_handoff_examples.py --check --mode extensa --campaign extensa-gem5-bfs-20261004-a7
```

The rendered messages retain their original record provenance and format.
The rendering context creates no evaluation or campaign record.
