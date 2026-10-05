# Final code review, tickets 38–65

Created: 2026-10-04 ET
Updated: 2026-10-04 21:10 ET (forged-frontier P3 fixed in `ab98aeb`)

**Range:** `58aff85..24da1d2` on `yanrujhou_main`, limited to `swdb-project/`. The fixes are
on the review branch (worktree `agent-ae1e0bf9afef585df`), `2738a26..HEAD`. Nothing was pushed.

**Method:** five parallel review passes, one per area:

1. kernel plug-in seam and BC;
2. certification, library index and site finder;
3. Extensa port, campaign and speed rule;
4. provider login, session lock and audit;
5. native evaluator v2 and compiled verifier.

Each finding was reproduced with a scratch test or a run before it was fixed. Every fix has a
regression test. The review changed no frozen protocol, no committed evaluation record, and no
normative content of a library entry.

## Findings

| Sev | File:line (at HEAD) | Issue | Fix |
|---|---|---|---|
| P1 | `swdb/campaign.py:910` | A repaired patch skipped the leakage scan. Repro: a patch saying "2x speedup" became a certified candidate and a `best/` input. | `d895705` |
| P1 | `swdb/campaign.py:988` | The iteration's evaluation ignored `approval.gem5_other_socket` (ticket 64). An approved native campaign passed its pilot, then stopped at its first block. | `f304e5c` |
| P2 | `swdb/campaign_targets.py:418` | `certify` rebuilt the outcome from named failures only. A `failed` certificate with an empty matrix or no controls came back `certified`. | `f304e5c` |
| P2 | `swdb/certification.py:607` (old 553–561) | A control that expects named checks counted as rejected on any semantic failure. Repro: `index_wrap` "rejected" by a plain verifier FAIL. | `8040609` |
| P2 | `swdb/certification.py:629` | A clause's `negative_control.check` was never compared with what the control's runs observed (ticket 43 review). | `8040609`: `clause_controls`; an enforceable mismatch fails the verdict |
| P2 | `swdb/kernels/bc.py:31` | No control touched L4's successor bit, edge index or path-count source. | `8040609`: three token-matched controls. All 24 BC control runs are rejected. |
| P2 | `swdb/provider_login.py:87,206` | The write-back copied any well-formed login back to the source. A session could plant another account, login mode or API key. | `d78fe83`: only a token refresh of the same identity is written back |
| P2 | `swdb/provider_login.py:60`, `provider_workspace.py:72`, `provider_guard.py:761` | A deeply nested JSON copy raised `RecursionError` out of cleanup. The copy and its hard links stayed, and no audit was written. | `d78fe83` |
| P2 | `swdb/provider_roles.py:48` | The synthesis role's free-form `entry` object fails strict structured output (ticket 57 note). | `4e2a68b`: fixed shape, `strict_problems()` and a test over every role |
| P3 | `swdb/campaign.py:945` | A usage-limit or login failure during synthesis was counted and marked done (D7 says uncounted, then pause). | `d895705` |
| P3 | `swdb/library_operations.py:251` | Pinned body, reference, templates and mutations were checked only before the run. | `8f371fd` |
| P3 | `swdb/certification.py:256` | A snapshot record's `source_derivation.script` named code that was executed. | `0e52ca6`: only `scripts/prepare_*_snapshot.py` |
| P3 | `swdb/certification.py:320,708`, `library_operations.py:263` | Hard-coded `/private/tmp` (sandbox-denied; absent on Linux). | `63e6534`: `tempfile.gettempdir()` |
| P3 | `tools/bfs_native/driver_scalable.cc.in:128` | The v2 driver casts `DOBFS`'s parents to `int32_t`. A candidate returning wider values could have out-of-range parents truncated into valid ones. | **Not fixed.** The template hash is pinned in frozen native protocols (`instrumentation.template_sha256`). This needs a new evaluator version: add a `static_assert` on the element type. |
| P3 | `swdb/certification_faults.py:41` | The forged frontier counts are fixed to the source-0 oracle. | **Partly fixed** by `8040609`: the control now needs `duplicate_frontier`, so a non-zero source can no longer "reject" it through the forged print alone. With more than three levels, the read past the array end remained. **Fixed** 2026-10-04 21:10 ET in `ab98aeb`: the table holds the control run's own oracle counts and is bounded; regression tests on 7- and 8-level graphs; ticket 20 still certifies 10/10 with 16/16 controls rejected by their named checks. |
| P3 | `swdb/annotation.py:21` | The profiling role uses `minLength`, `minItems` and `minimum`. Some strict-mode checkers refuse these. | **Not fixed** (not verified against the API). `strict_problems` checks object shape only. |

These were seen and judged below the reporting bar, so they are not fixed:

- `dx100.execute` does not check that the workload's kernel matches the candidate's kernel. It
  still fails safe on a vacuous source.
- `register_bc_workloads.py` drops `source_policy` provenance.
- The no-FMA assumption in `bc_native` is not enforced. A violation could only cause a false
  rejection, never a false pass.

## Requested known issues

1. **Pre-existing failures.** The causes were:
   - `test_typed_gem5_recovery` (20): the tests read live records, where recovery r1 later wrote. Fixed in `0afddc0` with a pinned pre-r1 copy.
   - `test_typed_certification` (2): `/private/tmp`. Fixed in `63e6534`.
   - `test_library_submit` (1): the status is now `evaluated_on_target`. Fixed in `ed166e3` by matching the library's own admitted set.
   - `test_bfs_acceptance_report` (1): later simulated evaluations joined the cell. Fixed in `787f9bd` by deriving the native evidence by protocol.
   - Also fixed: `test_extensa_selection` (1), stale against ticket 64's per-class gate (`f3391a6`), and `test_format_doc` (2), with undocumented ticket 56/64 fields (`7a3139e`).
   - `test_dx100_compile_smoke`, `test_dx100_smoke_cleanup` and `test_bfs_workload_driver` pass in this environment without changes.
2. **Stray `records/*/fixture.*.yaml`.** I could not reproduce them: a full run left the checkout
   clean. `a2616fd` adds an autouse guard. A test that creates, changes or deletes anything under
   the checkout's `records/` or `library/` now fails, its new files are removed, and the guard
   names the test.
3. **Ticket 43 controls.** Done in `8040609` (see above). Each run records its
   `observed_checks`, and each certificate records its `clause_controls`.
   - Both promoted contracts name checks that no run reports: `knob_range` for
     `frontier_threshold` and `schedule_range` for `schedule`. These are recorded as
     `enforceable: false`. Correcting them is a normative contract change for Yan-Ru.
   - The new L4 controls live in the BC plug-in. The promoted contract's L4 still lists only
     `skipped_cas_recheck`.
4. **Synthesis schema.** Fixed in `4e2a68b`.
5. **`map.md` rows 56–65.** Synced in `2738a26`. Rows 61–65 were missing.

## Full suite

**Result (2026-10-04, at `0e52ca6`): 4,044 passed, 36 skipped, 0 failed, 0 errors.**

- **How it ran:** `python3 -m pytest -q -p no:randomly`, on macOS arm64. The test files were split
  into eight disjoint partitions that ran in parallel. Each partition had its own `TMPDIR` and
  `--basetemp`.
- **Skips:** these are the existing environment skips, for example tests that run only on the
  collecting host or need GCC with OpenMP.
- **Checkout:** the records/library guard fired in no test, and the checkout was clean afterwards.
- **Baseline for comparison:** the same partitions before the fixes, at `24da1d2`, gave 30
  failures:
  - `test_typed_gem5_recovery`: 20
  - `test_typed_certification`: 2
  - `test_format_doc`: 2
  - `test_bfs_acceptance_report`: 1
  - `test_library_submit`: 1
  - `test_extensa_selection`: 1
  - `test_library_index`: 1, which passed on rerun (likely a timing race on the index fingerprint)
  - `test_extensa_campaign`: 1, which passed on rerun

  The `test_dx100_compile_smoke`, `test_dx100_smoke_cleanup` and `test_bfs_workload_driver`
  failures listed in the request did not occur in this environment.

## Open

- **For Yan-Ru, contract wording:**
  - The checks named by the `frontier_threshold` and `schedule` clauses do not exist.
  - The L4 part controls could be named in the contract.
- **Native evaluator:** the v2 driver needs an element-type guard on the parents it returns. This
  requires a new evaluator version.
- **Profiling role:** check its schema against the provider's strict mode.
