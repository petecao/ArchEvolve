# ONE early-exit7 dispatcher R2 — source-only stat correction

Prepared 2026-10-07 ET. NOT RUN. No dispatcher, fixture or helper import/main, SSH, test, staging, native probe, Store or science occurred. Only source-byte editing, closed literal reversal and structural AST parsing/comparison ran. Originals dc4c and R1 4eee, their handoffs/diffs/preparations remain byte-exact.

Parent identified a read-induced false refusal: full `stat_result` equality includes atime, so a first read under relatime can legitimately change the metadata being checked. The fresh/released lease read and the retained empty lock read both used that predicate.

R2 replaces exactly those TWO predicates with explicit tuples of `(st_dev, st_ino, st_mode, st_nlink, st_uid, st_gid, st_size, st_mtime_ns, st_ctime_ns)`. Atime is deliberately excluded. Each after-read `stat()` is captured once by a local assignment expression; no helper function is introduced. Read bytes/length/SHA and all other checks stay exact. Identity, ownership, link count, mode, size and both content-change timestamps must still agree.

Only decoded remote `read_json` and `source_state` differ at these two predicates. Every other remote AST node, local dispatcher AST, field/control/argv/environment/cap remains exact. Complete literal reversal restores R1 byte-for-byte. AST parsing proves source shape only, not runtime stability, host visibility, fixture pass or scientific admission.

Selected R2: `/private/tmp/lanl14-dispatch-reviewed-early-nonzero-linux-fixture-20261007-a1-r2.py`, 28967 bytes, SHA `cbaaef6a8f7f324502357daacc1ffa27b3245c0e23ebbaa9f827bdebdf7dc9b1`. Full unchanged argv/env are in original handoff111868; retained-lock semantics are in R1 handoff583467.

Source-review chronology supplied by the parent is retained honestly: the parent's earlier readonly checker initially guessed an AST index and failed before any body/runtime execution; corrected structural AST inspection passed. That was a source-checker setup event, not a native/fixture test. No runtime has occurred.

Future parent-selected invocation after full R2/source/readiness review:

```sh
/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3 \
  /private/tmp/lanl14-dispatch-reviewed-early-nonzero-linux-fixture-20261007-a1-r2.py \
  --delivered-revision <exact-parent-selected-delivered-40hex> \
  --dispatcher-sha256 cbaaef6a8f7f324502357daacc1ffa27b3245c0e23ebbaa9f827bdebdf7dc9b1 \
  --output-directory /private/tmp/lanl14-reviewed-early-nonzero-dispatch-actual-20261007-a1
```

The placeholder is intentionally unknown here; no new delivered revision is invented. Output must remain fresh, and prior partials are retained. This is the same ONE fixture plan, without a retry, new guard family, changed native/scientific bound or additional runtime permission.
