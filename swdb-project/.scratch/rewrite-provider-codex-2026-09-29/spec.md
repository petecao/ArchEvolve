# Spec: Codex and Claude rewrite providers working in a guarded workspace

Created: 2026-09-29 17:30 ET
Updated: 2026-09-29 (Eastern Time)
**Type:** spec
**Status:** resolved
**Blocked by:** None
Owner: Yan-Ru Jhou
Decision record: ADR 0006 (rewrite providers work as tool-using agents in a guarded workspace)

## Problem Statement

SWDB turns a rewrite proposal into a candidate artifact by handing it to a rewrite provider.
Today there is exactly one provider kind, Claude, and it works blind: SWDB packs the source,
the profile package, and the proposal into one prompt, gives the provider no tools, and
takes back a patch. Three things go wrong for the operator.

1. Real applications do not fit in one prompt. The provider cannot look around the code the
   way an engineer (or an interactive coding agent) would, so larger rewrites are guesswork.
2. Nobody controls which model did the work. The provider uses whatever model and effort the
   installed CLI defaults to, and the stored records do not say which model produced a
   candidate, so results cannot be attributed or reproduced.
3. The team wants Codex as the default provider, with Claude as an alternative, and SWDB
   cannot run Codex at all.

Giving a provider tools opens a new problem: it could read what it must not see (the
evaluator and verifier, the workload inputs, other candidates, earlier evaluations, or the
DX100 authors' own optimized code) and so produce a result that looks like a rewrite but is
really copying. The CLIs' own sandboxes cannot prevent this on the lab host: both depend on
bubblewrap, which the host's AppArmor policy blocks for unprivileged users.

## Solution

A rewrite provider works like a coding agent inside a **provider workspace** that holds only
what its rewrite proposal needs. There it may read, edit, build, and run code, including
small test inputs it makes itself. It cannot see anything else, and it cannot reach the
internet from the commands it runs. SWDB builds the workspace from the proposal, confines the
provider with its own Landlock guard, audits everything the provider did, and takes the edit
as the difference between the workspace and the starting source snapshot. All existing
protections and the correctness check still apply.

Two provider kinds are supported, with the model and effort fixed in code and written into
every record:

| Kind | Model | Effort | Default |
|---|---|---|---|
| Codex | `gpt-5.6-sol` | `xhigh` | yes |
| Claude | `claude-sonnet-5-5` | `high` | no |

Workspace mode is the default. Today's prompt-only mode stays available on request, so that
recorded configurations can be re-run exactly.

## User Stories

### Choosing and pinning the provider

1. As the SWDB operator, I want Codex to be the rewrite provider when my provider configuration does not name a kind, so that the team's default is used without extra setup.
2. As the SWDB operator, I want to select Claude instead by naming it in the provider configuration, so that I can use the alternative provider when I choose to.
3. As the SWDB operator, I want Codex always to run as `gpt-5.6-sol` at `xhigh` effort, so that every Codex candidate comes from the same model setting.
4. As the SWDB operator, I want Claude always to run as `claude-sonnet-5-5` at `high` effort, so that every Claude candidate comes from the same model setting.
5. As the SWDB operator, I want a provider configuration that tries to change the model or effort to be rejected, so that a pinned setting cannot drift silently.
6. As a reader of results, I want every proposal record to state the provider kind, model, effort, and CLI version actually used, so that I can attribute a candidate to a model.
7. As a reader of results, I want records made before this change to stay valid and show the model as unknown, so that old evidence remains usable without false claims.
8. As the SWDB operator, I want a repair to use the same kind, model, and effort as the proposal's first attempt, so that a pass or failure is attributable to one provider setting.
9. As the SWDB operator, I want a repair that asks for a different kind to be refused, so that mixed-provider results cannot happen by accident.
10. As the SWDB operator, I want `--provider-config` to remain required, so that choosing a provider is always an explicit operator act.

### Working in the provider workspace

11. As the SWDB operator, I want the provider to explore the source itself instead of receiving everything in one prompt, so that rewrites of large applications become feasible.
12. As the SWDB operator, I want the provider's workspace derived automatically from the rewrite proposal (its source snapshot, its regions' files, the profile package, the selected strategy entry, and the headers of its required operations), so that nobody hand-picks files per run.
13. As a proposal author (for example Peter's agent), I want to name an extra file my proposal needs, so that the provider can see it, with the name recorded.
14. As the SWDB operator, I want everything outside the derived set hidden, including evaluator and verifier code, workload inputs, other candidates, earlier evaluations, the records database, and the internet, so that the provider cannot cheat.
15. As the SWDB operator, I want from-scratch proposals on DX100 BFS to start from a scalar-only source snapshot without the authors' accelerator functions, so that the provider cannot copy the answer key that shares a file with the baseline.
16. As a proposal author, I want proposals whose strategy reuses the DX100 authors' code to keep the full source file, so that reuse routes (like T17) still work.
17. As the SWDB operator, I want the provider to build and run code in its workspace, so that it can check its own work before handing it back.
18. As the SWDB operator, I want the provider unable to run the real workload or verifier, so that tuning against the evaluation is impossible.
19. As the SWDB operator, I want the provider's final message to carry only its interpretation and its unresolved requirements, so that the edit itself comes from the workspace, not from hand-written patch text.
20. As the SWDB operator, I want prompt-only mode available on request, so that I can re-run a recorded configuration exactly.

### Taking the edit

21. As the SWDB operator, I want the edit computed as the diff between the workspace and the starting snapshot, so that malformed patches can no longer corrupt a candidate.
22. As the SWDB operator, I want only changes to source files the proposal allows to count, so that out-of-scope edits never reach a candidate.
23. As the SWDB operator, I want build outputs the provider left behind to be dropped, so that the candidate is rebuilt from source by SWDB.
24. As the SWDB operator, I want a new file outside the allowed list to fail the attempt, so that a smuggled binary or helper cannot enter a candidate.
25. As the SWDB operator, I want the existing protections (protected inputs, "an actual code change is required") to keep applying, so that the new mode is at least as strict as the old one.

### Guard and audit

26. As the SWDB operator, I want the whole provider process confined by an SWDB-owned Landlock guard, so that confinement works on the lab host without sudo.
27. As the SWDB operator, I want the provider itself to connect only to port 443 for its model API, and the commands it runs to have no TCP access at all, so that it cannot fetch code from the internet.
28. As the SWDB operator, I want web search, MCP servers, plugins, memories, and similar surfaces turned off in both CLIs, so that the provider has no side channel to outside material.
29. As the SWDB operator, I want each run to use a fresh provider home holding only a copy of the login file, deleted after the run, so that the provider cannot read my real configuration and the copy does not linger.
30. As a reviewer, I want the provider's full event log kept as a raw artifact, so that I can see every command it ran and every file tool it used.
31. As a reviewer, I want the attempt to fail when the log shows a file access outside the workspace, a command touching the login file, or a network command such as `curl`, `wget`, `pip`, or `git clone`, so that cheating attempts are caught even where the guard has gaps.
32. As a reviewer, I want the guard's policy (read and write roots, ports, limits) recorded with each attempt, so that I can check what the provider was allowed.

### Limits and failures

33. As the SWDB operator, I want each provider session limited to 16 threads, 32 GB of memory, 120 s per command, and a 5 GB workspace, so that it fits in one socket lane on the shared host.
34. As the SWDB operator, I want at most 1800 s per provider call (1200 s by default) and 3600 s in total per proposal, so that a tool-using session has room without running unbounded.
35. As the SWDB operator, I want hitting the ChatGPT usage limit recorded as "provider unavailable", not as a failed rewrite, so that it does not use up a repair and can be retried later.
36. As the SWDB operator, I want the dollar budget recorded as not enforced for Codex, so that the record does not claim a cap that does not exist.
37. As the SWDB operator, I want real Codex and Claude runs refused anywhere the guard cannot run, so that no provider ever runs unguarded.
38. As the SWDB operator, I want provider sessions to run inside a socket lane on mbit10, so that they follow the host's two-lane rule like any other multi-threaded job.

### Campaigns and scripts

39. As the SWDB operator, I want real campaigns to accept Codex as well as Claude, so that the default provider can be used in campaigns.
40. As the SWDB operator, I want candidates already made by Claude to stay reusable in campaigns, so that existing evidence does not have to be regenerated.
41. As the SWDB operator, I want the instruction smoke script to use the default provider and accept a kind override, so that I can smoke-test either provider.

### Maintainers

42. As a maintainer, I want to test the whole path on my Mac with a fake provider that behaves like Codex or Claude, so that I can work on SWDB without spending model usage or needing Linux.
43. As a maintainer, I want the same tests to run on mbit10 with the guard on, plus cases that prove forbidden reads, writes, and connections are blocked, so that the guard is verified where it matters.

## Implementation Decisions

### Provider configuration and pins

- Provider kinds: `codex`, `claude`, and the existing `external_fixture`. `kind` is optional and defaults to `codex`.
- The model and effort for each real kind are constants in the provider module. The configuration has no model or effort fields; supplying one is an error.
- The fixture kind gains an `emulates` field (`codex` or `claude`). A fixture that emulates a kind receives that kind's full command line, including the pins, and must speak its output format. It stays classified as a contract fixture, never as a rewrite provider.
- A new `workspace` field (default true) selects workspace mode; `workspace: false` keeps the current prompt-only path unchanged.
- Existing fields keep their meaning. The per-call time cap rises from 900 s to 1800 s (default from 300 s to 1200 s); the total stays capped at 3600 s. `budget_usd` is passed to Claude and recorded as not enforced for Codex.
- `output_format` applies only to Claude's prompt-only mode. In workspace mode, both kinds always capture a full event stream, because the audit needs it.

### Provider command lines

- Codex runs through `codex exec` with the pinned model and effort, its own sandbox off (it cannot start on the lab host; the SWDB guard replaces it), no persisted session, no user configuration, no project instruction files, and web search, multi-agent tools, apps, plugins, memories, hooks, image generation, and image viewing disabled. It emits its JSON event stream, writes its final message to a file, and gets an empty standard input.
- Claude runs in print mode with the pinned model and effort, stream-JSON output, no MCP servers, no session persistence, and a tool list limited to reading, searching, editing, writing, and running shell commands (no web tools). Its shell commands are wrapped by the guard's inner layer through Claude's shell-prefix setting.
- Both get a final-message schema of `interpretation` (string) and `unresolved` (array of strings), with no free-form objects, so it is valid under OpenAI's strict structured output.
- The Codex equivalent of Claude's shell prefix is unverified. If none exists, Codex tool commands keep the outer guard's port-443 access, and the audit fails the attempt on any outbound connection other than the model API.

### Provider workspace

- A workspace module derives the visible set from the rewrite proposal: source snapshot files, the proposal's regions' files, the profile package, the selected strategy entry, the headers of required operations, and any extra files the proposal names. Extra names are recorded in the proposal record.
- It materializes a workspace copy under the run's raw output folder on the lab host, plus a fresh provider home containing only a copy of the provider's login file. The login copy is deleted when the session ends; the rest of the provider home is retained.
- The prompt carries the proposal, the rules, and a map of the workspace instead of the full package contents.
- After the session, the edit is the diff between the workspace and the starting snapshot. Only allowed source files count; build outputs are dropped; any new file outside the allowed list fails the attempt. The resulting candidate then goes through the existing protections and the correctness check unchanged.

### Guard

- An SWDB-owned launcher applies Landlock (ABI 4 on the lab host) to the whole provider process tree: reads limited to the workspace, the toolchain, the provider's install directory, and the per-run provider home; writes limited to the workspace and the per-run home; TCP connections limited to port 443.
- A second entry point applies an inner Landlock layer with no TCP access to each tool command.
- The launcher also applies the resource limits (16 threads, 32 GB of memory, 120 s per tool command, 5 GB of workspace) and records its full policy in the attempt's receipt.
- The launcher runs only on Linux. Real kinds refuse to run where it is unavailable. Fixtures run under it on Linux and without it elsewhere.

### Audit

- An audit step parses the Codex event stream (command executions, file changes) and the Claude stream (tool calls). It fails the attempt, with a stored reason, when it finds a file access outside the visible set, a command that touches the login file, or a network command. When the Codex fallback above applies, it also fails on any outbound connection other than the model API.

### Records

- The proposal's provider block gains: resolved kind, model, effort, CLI version, workspace mode, guard policy, and audit result. The proposal schema already allows free-form provider objects, so no schema version change is needed.
- A new outcome, `provider_unavailable`, covers usage-limit errors; it does not consume a repair.
- Repairs are refused unless their kind, model, and effort match the first attempt's.
- A scalar-only DX100 BFS source snapshot is registered, with a statement of what was removed and why. Proposals choose between it and the full snapshot through their existing source snapshot reference.

### Campaigns and host

- The native campaign runner's provider checks accept both real kinds, and receipts without model or effort remain valid for reuse.
- The instruction smoke script uses the default kind and takes a kind override.
- Real provider sessions run inside a socket lane on mbit10.
- The host setup is already done (see Further Notes).

## Testing Decisions

- **One seam: the public `swdb submit` and `swdb repair` commands.** Tests drive them with a provider configuration pointing at a fake provider program and assert only on what those commands produce: the proposal record (outcome, reason, provider block, audit result), the candidate's diff, and the retained raw artifacts. No test reaches into provider-module internals.
- **The fake provider** is a fixture that emulates Codex or Claude. It records the command line it received (to check the pins and the refusal of overrides), edits files in its working directory (to check the visible set, the named-file rule, the diff, dropped build outputs, and stray-file rejection), and prints scripted events (to check each audit failure reason, the usage-limit outcome, and time limits).
- **Repairs:** a submitted proposal followed by a repair with a different kind must be refused; one with the same kind must proceed.
- **Platforms:** all tests run on the Mac with the fixture unguarded. On mbit10 the same tests run with the guard on, plus Linux-only tests in which the fake provider attempts a forbidden read, a forbidden write, and a TCP connection, and each is blocked and reported.
- **The scalar-only snapshot** is covered by the existing record validation, plus a build and correctness check on mbit10.
- **Not tests:** the real Codex and Claude smoke runs on mbit10 are recorded as evidence, not as part of the test suite.
- **Prior art:** the bounded rewrite tests (`test_bfs_rewrite`), whose fixture provider goes through `swdb submit`; the stream capture tests (`test_rewrite_stream`), whose fake `claude` replays scripted events and records its argv; the whole-file edit tests (`test_rewrite_full_files`); the prompt projection tests (`test_bfs_prompt_projection`); the campaign reuse tests (`test_bfs_campaign_reuse`); and existing Linux-only tests, which use a `sys.platform` skip mark.

## Out of Scope

- Running the same proposal through both kinds to compare them (A/B).
- Asking the lab admins to allow bubblewrap, which would let the CLIs' own sandboxes work on the lab host.
- Real provider runs on the Mac.
- Changing the evaluator, the correctness checks, or the comparison protocols.
- The ArchEvolve handoff work (TDStep annotation, the T17 comparison, the crosswalk), which has its own spec.

## Further Notes

- **Implementation progress on 2026-09-29 ET:** all ten tickets are resolved;
  ticket 07's audit repairs passed final Linux validation; whole-diff review is pending;
  see [map.md](map.md) and
  [guarded provider evidence](../../docs/evidence/guarded-rewrite-providers-20260929-a1.yaml).
  Linux A6 passed 222 guard/pins/workspace cases at `4f5d152`; A7 passed 42
  focused status cases and the retained-log re-audit at `c8a666f`, including the
  expected historical Codex A1 refusal. Fresh public DX100 A2 at the latter
  revision created a Codex candidate with passing original/current audits, guard,
  cleanup and source-0/3/8 native structural checks; `gain_claim=false`.
  Claude A2 retained an OAuth-expired failure with passing original/current
  audits, guard and cleanup, as permitted by ticket 10; no Claude BFS result is
  claimed. The older Codex A1 receipt remains unchanged and audit-refused.
  Linux A10 passed all 443 workspace cases and six retained-log expectations at
  `a7cca27`. The final network-command repair passed 154 local and 114 independent
  cases at audit blob `62fe75f4`; Linux A11 passed 216 selected cases and six
  retained-log expectations at `3a73c6c`. Whole-diff code review is pending.
  The separate T17 recheck has completed.
- **Host setup done on 2026-09-29:**
  - Codex CLI 0.153.0 is installed under the user's npm prefix on `/data1` and logged in with ChatGPT; its home is on `/data1`, mode 700.
  - The user's folders on mbit10 are owner-only, with the old permissions backed up.
  - Landlock ABI 4 works for the user without sudo; bubblewrap fails with "setting up uid map: Permission denied".
- **Accepted residual risks:**
  - Tool commands can read the per-run login copy while the session runs. The audit flags any command that touches it.
  - UDP is not blocked (DNS, HTTP/3). The audit flags network commands.
- **T17 caveat:** T17's strategy reused the DX100 authors' accelerator function, so its roughly 2.8× simulated speedup reproduces the authors' path rather than an optimization the provider found. This spec's scalar-only snapshot keeps future from-scratch proposals from seeing that code.
- **Recorded decisions:** ADR 0006 records the decision and the rejected options (prompt-only, the CLIs' own sandboxes, running on the Mac). The glossary gained Rewrite provider, Provider workspace, and Statement on 2026-09-29.
