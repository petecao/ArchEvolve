# DX100 v2 contract review

Created: 2026-09-26 (Eastern Time)

This is a narrow implementation review before a prospective model run. It does
not replace the final independent Standards and Spec reviews against
`1bdb7d4037916dea782c40239a6415b61a47f3c1`, and it contains no empirical BFS or
performance acceptance.

The independent `profiling_design` reviewer inspected the witness parser and
its design document after implementation by `identity`. The final inspected
parser SHA-256 was
`70aea578978351d854be33728a0810cff29d104ddc545ace3a2aa6d34267db39`;
the design document SHA-256 was
`099b7db8392f192e5a3cea035f663d47a4e70088b88c397a36b62494568c7eaa`.
No reproducible finding remained in that scope. The reviewer independently ran
69 witness tests, all passing. These are explicit contract fixtures.

The same independent reviewer then inspected the finalized driver
(`371657977d56816a37f4885f19923f37175331d2d15b5d7f6e6049d3fa8c1395`)
and adapter
(`34c37171c79a797af63a172752fdc00ced68349298ca7307c6b00b19935dea90`).
No reproducible issue remained in post-seal activation, chunk accounting,
separate output, process-outcome gating, protected completion ordering, or the
downstream validator call. The implementer reran all 12 public v2 cases against
the stable witness module, including downstream rejection of a stale checker
and deleted witness; all passed in 36.57 s. The independent reviewer had also
run the preceding 12-case adapter snapshot successfully.

The pinned model revision is
`e4fc4afdf894f295442cef3604667a469fab8e62`. The review checked:

- `src/sim/syscall_desc.cc:44–100`: call, return, and retry emission; retry can
  begin before trace activation and execute as a later event.
- `src/base/trace.cc:154–174`: tick, flag, and CPU-object formatting, with each
  message flushed.
- `src/python/pybind11/debug.cc:57–66`: the existing Python trace-output binding.

The root review identified the initial-worker-retry boundary. The parser now
records an initial partial non-exit retry rather than inventing its earlier
call. It still rejects a partial exit witness and requires the complete main
CPU/thread exit call and return. The document distinguishes hardware thread
identity from guest PID, sealed ROI observations from normal termination, and
fixtures from actual model execution.

Root verification passed separately:

- 117 public protocol, aggregation, coverage, and series tests in 284.77 s.
- 78 diagnostic comparison, native freeze, and repeatability tests in 63.49 s.
- 93 witness and series tests in 0.21 s after the retry-boundary fix. The series
  tests overlap the first group; these counts must not be summed as unique tests.
- Local catalog validation: 185 records valid; new held remote metadata was not
  imported or counted.

Historical v1 executions remain unchanged. New v2 requests and their actual
model results require separate bounded execution and evidence review before
correctness acceptance or a frozen comparison can rely on them.
