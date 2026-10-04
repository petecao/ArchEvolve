# 62 — Spelling-independent BFS certification controls for campaign rewrites

Created: 2026-10-04 ET (by ticket 57)
Updated: 2026-10-04 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** —
**Spec:** `../spec.md`

**What to build:** `swdb certify` can certify a provider-written BFS read-offload rewrite whose
text differs from ticket 20's patch.

## Finding (ticket 57, 2026-10-04)

The gem5 acceptance campaign `extensa-gem5-bfs-20261004-a5` (summary in
`records/campaign_summaries/extensa-gem5-bfs-20261004-a5.summary.yaml`) produced six contract edits that
applied and passed the session-begin check. `swdb certify` aborted every one with "candidate source lacks
a unique negative-control mutation site: shared_context", before running the matrix. The BFS negative
controls are exact-text mutations of ticket 20's spelling (`swdb/certification.py` `_rewrite_control`,
for example `dxc_context c=swdb_contexts[omp_get_thread_num()];`). Ticket 58 reported the same caveat.
Until this changes, no independently written contract edit can be certified, so an Extensa gem5 campaign
cannot reach gem5 evaluation with a contract edit.

## Options (agent proposal)

1. Controls as source-level probes from the contract's predicates (the ported
   `swdb/extensa/probes.py`, D1), which bind to call operands rather than to text.
2. Controls located by the intrinsic calls the candidate makes (for example the context argument of
   each `__dxc_*` call), with a refusal only when the call itself is absent.
3. Name the required spellings in the contract so a provider can follow them (weakest; leaks the
   control sites to the provider).

The evaluator's pass rule and the control set stay unchanged; only how a control finds its site changes.

## Answer

Resolved 2026-10-04 ET by the agent. Agent-decided under Yan-Ru's 2026-10-04 delegation; revisable.

**Design: controls attach to the library side, not the candidate text.** None of the three
proposed options was taken as is. Option 1 (probes) checks predicates, not a running mutant;
option 2 still searches the candidate; option 3 leaks control sites. Instead:

- Each shared rewrite control is one fault in `library/dx100/faults/dxc_lowering_faults.hpp`.
  `swdb certify` first checks that the candidate ships the byte-identical canonical lowering
  header (unchanged rule). For each control it then appends the fault block to a *private build
  copy* of that header and selects one fault with `-DSWDB_DXC_FAULT_<ID>`. Object-like macros
  rename the seams the contract requires the candidate to call: the `__dxc_*` intrinsics, the
  CPU claim primitive `compare_and_swap` and `QueueBuffer` (clause L4: the CPU keeps the CAS
  and the queue push). The candidate's own bytes are restored after each build, and the
  tree-identity check still runs.
- Faults: `shared_context` (every thread gets the session's first context), `dropped_wait`
  (no wait completes), `read_before_wait` (waits on gather results are skipped),
  `index_wrap` (stream start register wraps to INT32_MAX), `chunk_off_by_one` (a stream that
  fills the tile requests one more element), `dropped_continuation` (after the first range
  loop of a stream, the loop state is forced to its end), `skipped_cas_recheck` (a failing
  CAS succeeds anyway, at most eight per session, inside the graph's spare vertices),
  `forged_frontier` (after an accelerated chunk, one claimed vertex is pushed twice; the
  evaluator-protected frontier print is forged to the oracle counts, as before).
- A control still counts only after a real build and a named runtime rejection; the expected
  named checks (`_CONTROL_EXPECTED`) and the pass rule are unchanged. A fault that never fires
  leaves its control alive, so certification fails. That is how a rewrite that bypasses a seam
  (for example a raw `__sync_bool_compare_and_swap` claim) is refused.
- BC-L1 `stale_depth_hint` has no library seam. It uses a C++ token matcher
  (`swdb/certification_faults.py` `replace_tokens`) that ignores whitespace, line breaks and
  comments. Calibration controls on the authors' pinned source are unchanged.
- Control records gain `fault` (`site`, `macro`, `fault_block_sha256`). The certification
  `command.sources_sha256` now also covers `swdb/certification_faults.py`.

**Session lock.** `swdb/provider_login.py`: every real provider session holds an exclusive
`flock` on `swdb-session.lock` in CODEX_HOME (or CLAUDE_CONFIG_DIR). It takes the lock when
the login copy is made and releases it after write-back, including on failed starts. A
waiting session polls for up to `SWDB_SESSION_LOCK_TIMEOUT_S` (default 3600 s), then fails
before any provider call. Receipts record `session_lock` (waited, wait_s), never values.

**Also fixed (ticket 58 a2 crash).** `provider_audit` refuses a parsed path the OS cannot
stat (an awk program raised ENAMETOOLONG) instead of crashing the driver.

**Verification (Mac, g++-16).**
- `tests/test_certification_controls.py`: ticket 20's patch, a whitespace-reformatted
  copy and a restructured copy (renamed context reference, different chunk clamp, `while`,
  multi-line claim) each certify through `certify()` with 10/10 cells and 16/16 controls
  rejected. A skipped-CAS rewrite fails the matrix (`frontier_size_equality`). A
  raw-builtin claim passes the matrix but is refused because `skipped_cas_recheck` survives.
- `tests/test_bc_certification.py`: the BC forward pass certifies (10/10 cells, 18/18
  controls rejected).
- `tests/test_provider_login.py`: the lock is held from copy until write-back, serializes
  sessions across processes, and is released by failed starts. Also covers the audit
  refusal and the driver's a3 stop.
- `tests/test_typed_certification.py` and `test_bc_certification.py` pass, except two tests
  that write to `/private/tmp`, which this session's sandbox blocks. Those two are
  environment failures, not regressions.
