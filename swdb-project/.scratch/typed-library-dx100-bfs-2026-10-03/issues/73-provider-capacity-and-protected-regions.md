# 73 — Provider capacity is an uncounted pause; the rewrite workspace names the protected verifier

Created: 2026-10-05 02:50 ET (from campaign `extensa-native-bfs-20261004-a7`, ticket 56 addendum)
Updated: 2026-10-05 17:20 ET (tracker hygiene, code review: Blocked by line); 2026-10-05 03:15 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`; [design decisions](../extensa-design-2026-10-03.md) D7; [56](56-native-campaign-target.md), [72](72-native-upstream-two-level-trials.md)

**What to build:** two harness fixes, agent-decided under Yan-Ru's delegation (revisable), requested by the
coordinating agent on 2026-10-05.

## Findings (campaign a7)

1. **Capacity counted as a failed rewrite.** Calls 4 and 5 (iterations 3 and 4) ended after about 3.5 s with
   Codex's `{"type":"error","message":"Selected model is at capacity. Please try a different model."}` and exit
   code 1. `provider_adapters.check_usage` matched only usage limits, so the call became a counted `failed`
   outcome and the iteration's feedback `provider_output_invalid`. D7 counts only real attempts; provider-side
   unavailability is not one.
2. **The rewrite edited the protected verifier.** Iteration 1's patch changed `BFSVerifier` in `bfs.cc` and was
   rejected (`protected evaluator/ROI input changed ... (verifier)`). Root cause: REGIONS.json names
   `dx100-bfs-scalar/TDStep:240-241`, line numbers of the registered full fork source (revision `e4fc4af`).
   The workspace copy is the scalar-only snapshot, where TDStep is at lines 64-96 and lines 222-268 are
   `BFSVerifier`. Nothing in the prompt or workspace said that the verifier is off-limits.

## Acceptance

- [x] Transient provider unavailability (model at capacity, overloaded, 502/503/504/529, service unavailable,
  bad gateway, gateway timeout, stream disconnected) read from error events and stderr raises
  `ProviderCapacity`; usage limits stay usage limits; quoted text in a normal message is ignored.
- [x] A campaign records such a call as `provider_capacity`, uncounted (D7), backs off (60, 120, 300, 600, 600,
  600, 600 s; at most 3600 s in total) and retries the same iteration. If capacity persists, the campaign stops
  with `infrastructure_failure`. It is never `provider_output_invalid`. A synthesis call at capacity pauses,
  uncounted.
- [x] The raw a7 call 4 and call 5 streams (byte copies, sha256 checked) classify as `ProviderCapacity`.
- [x] The rewrite workspace has `PROTECTED.json`: each protected evaluator input, with the verifier region's
  lines and function (`BFSVerifier`) in the workspace copy. REGIONS.json adds each region's `workspace`
  function and line span. The prompt says plainly that protected regions must never be edited and that
  `source.lines` number the registered full-source revision.
- [x] A refused patch's feedback names the protected region (path, workspace lines, function).

## Answer

Resolved 2026-10-05 03:15 ET by the agent (worktree branch, not pushed).

- `swdb/provider_adapters.py`: `CAPACITY` pattern and `ProviderCapacity(ProviderUnavailable)`, raised by
  `check_usage` after the usage-limit check.
- `swdb/extensa/search.py`: `CallOutcome.PROVIDER_CAPACITY` (SWDB addition), uncounted.
- `swdb/campaign.py`: `_call` retries `_call_once` after each backoff (`CAPACITY_BACKOFF_S`, bounded by
  `CAPACITY_WAIT_S` = 3600 s; `SWDB_CAPACITY_BACKOFF_S` overrides the schedule for tests) and stops
  `infrastructure_failure` past the bound. Each uncounted row records its `backoff_s`. An iteration interrupted
  by a stop is kept in the summary as `interrupted_iteration`. `rewrite_prompt` names `PROTECTED.json`.
- `swdb/campaign_targets.py`: `function_span`, `enclosing_function`, `protected_regions()` and
  `workspace_region_lines()`; the protected-region refusal names the region.
- Tests: `tests/test_provider_capacity.py` (a7 raw streams, transient messages, usage limit unchanged, campaign
  retry uncounted, persistent capacity stops `infrastructure_failure`) and
  `tests/test_extensa_targets.py::test_native_workspace_names_the_protected_verifier_and_region_lines`.
  Fixtures: `tests/fixtures/provider_capacity/`.
- The a7 records are unedited; ticket 56's a7 addendum carries the erratum.
