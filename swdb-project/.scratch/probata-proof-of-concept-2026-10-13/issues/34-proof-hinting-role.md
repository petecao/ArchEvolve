# 34 — proof_hinting role and workspace

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 16:40 ET (Answer); 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** resolved
**Blocked by:** 01, 21
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-hint loop": Workspace; "Loop, modes and guards (changed)": Provider guard and workspaces; "Providers and machines"; "Testing Decisions", seam 4; user stories 27, 28, 77, 80, 85; O3); decisions: [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) (items 1, 6, 10, 13), [18](../../formal-verification-2026-10-09/issues/18-evaluation-claims-and-subjects.md) (item 6, the guard), [23](../../formal-verification-2026-10-09/issues/23-evaluation-baselines-and-metrics.md) (item 7, the Codex pin)
**Time estimate:** about 2 days

**What to build:** A new agent role, `proof_hinting`, launched through the provider launcher like
the existing roles. It gets one proof unit's failing WP goals in a guarded workspace, runs the
proof-hint agent (Codex by default) and returns a hint set as structured output. The provider kind
is recorded on every hint set. The agent sees only what it needs to write hints, never edits code
and builds nothing. It may run WP and the proof hint check, but only through a frozen wrapper.
`workspace.json` hashes every visible file. Hint records never reach a rewriting workspace. Done
when a scripted provider runs the role end to end through the provider workspace and guard seam,
and every hidden-material control is refused.

## Acceptance

- [ ] **Launch.** `proof_hinting` runs through the provider launcher. Default provider Codex at its
      pin (`gpt-5.6-sol`, effort `xhigh`). A scripted provider runs it end to end. The returned hint
      set records the provider kind.
- [ ] **Visible set, exactly.** The workspace holds: the read-only C lowering with its anchors; the
      candidate artifact's C++ proof unit; the contract's formal halves and unit postcondition;
      summaries as ACSL; the failing goals, each with its kind and failure class; earlier rejected
      hints, each with its rejection rule, and blamed hints (map 13 item 6); seeds. A test compares
      the visible tree with `workspace.json`: every visible file has a sha256 there, and nothing
      else is visible.
- [ ] **Hidden material refused.** One negative control each: evaluator code, a workload input, a
      test, a negative control, another candidate artifact, a counterexample (a counterexample goes
      to counterexample-guided repair, never to the proof-hint agent; map 13 item 10). Each makes the
      role refuse to start and name the file.
- [ ] **Narrow guard exception.** The authors' code is visible only when it is the candidate
      artifact. The rule keys on the candidate artifact, not on one name; the test case is
      `TDStepMAA` as the candidate artifact (before the freeze, the only authors' code that is ever
      the candidate artifact). Controls: it is refused when the candidate artifact is other code; a
      second authors' function next to it (for example `DOBFSMAA` or `PBFSMAA`) is refused; the
      rewriting workspace still refuses every name ticket 01's guard blocks.
- [ ] **Output is hints only.** The output schema allows only `{anchor, kind, text}` records. It has
      no code, file-edit or verdict field. A scripted provider that returns edited code or a claimed
      verdict fails the output check.
- [ ] **Frozen wrapper.** The wrapper's hash is in `workspace.json`. Inside the round's one provider
      call, it runs WP with the frozen flags and runs the proof hint check. It refuses any extra flag
      (controls: `-wp-cache update`; a downgraded `ghost:bad-use` warning key). Its results reach only
      the agent; no record reads them as a verdict.
- [ ] **No leak to rewriting.** A rewriting workspace, including one for counterexample-guided
      repair, refuses any input that is a hint record or a `proof_hinting` output.
- [ ] **Inputs immutable.** A scripted provider that tries to edit the C lowering or the proof unit
      changes nothing; the guard audit reports the attempt.
- [ ] **Mac confinement (design O3, default until Yan-Ru rules).** On the Mac the role runs in
      Codex's own sandbox with the workspace read-only, and it builds nothing. Controls: a scripted
      provider that starts a build, and one that writes outside the workspace, are each refused,
      and the guard audit records the attempt.
- [ ] **Mac memory rule.** Each wrapper WP run counts as a real verifier job: one at a time, under the
      ~8 GB RSS watchdog. A second wrapper call while a verifier job runs queues behind it (effort
      spec: verifier jobs queue).

## Notes

- **Not in this ticket:** 01 — Guard blocks the authors' held-out functions (the guard's name
  list); 21 — C lowering and WP adapter (A2 tracer) (the lowering, anchors and WP adapter);
  35 — Hint records, merger and proof hint check (what a hint record means and the check itself);
  36 — Proof setup check and verdict reading; 37 — The proof-hint loop (when the role is called,
  seeds, rounds, budget, the proof record); 11 — Method-version file and failure classes (the file
  that pins this role's prompt and wrapper); 16 — Post-campaign WP phase and budgets
  (`provider_calls_proof`); 13 — Counterexample-guided repair (counterexamples never reach this
  role).
- **Prompt:** written here. Prompts belong to the method version (map 26 item 3) and freeze at
  59 — Method-version review and freeze.
- Assumption (not decided in the map): "only through the wrapper" is enforced by the existing
  provider guard and audit: any Frama-C, Why3 or solver call that does not go through the wrapper
  fails the audit. If the guard cannot see such calls, ask Yan-Ru before choosing another mechanism.
- Assumption (not decided in the map): hidden material is kept out by refusal before the provider
  call opens, as the existing guard refuses the authors' names (01), rather than by silently
  dropping the file.
- Assumption (not decided in the map): the guard exception keys on the candidate artifact's record
  saying the candidate artifact is the authors' code, not on the file's content.
- Assumption (not decided in the map): ticket 35 may land after this one. Until then, the
  wrapper's hint-check entry is tested against a scripted check; the real check plugs in when 35
  lands.
- **Risk (research 13, setup trap):** Alt-Ergo runs through a Why3 server Unix socket, and every
  prover call failed inside the Claude Code sandbox
  ([research 13](../../formal-verification-2026-10-09/research/13-wp-hint-facts.md)). The provider
  guard's sandbox may hit the same trap. Check this first. If the guard blocks the socket, take it
  to Yan-Ru before loosening the guard. On the Mac, Codex's own sandbox (O3) may also block WP's
  Why3 socket, or its fresh-session folder under the read-only workspace. Check this first too, and
  take it to Yan-Ru before loosening the confinement.
- Machines: proof work on the Mac runs under the scoped ADR 0006 exception recorded at A0 (map 13
  item 13). Frama-C machdep is x86_64.
- **Mac confinement (design O3, default until Yan-Ru rules):** ADR 0006's launcher is Linux-only, so
  on the Mac the role runs in Codex's own sandbox over the frozen workspace, read-only; it builds
  nothing (criterion "Mac confinement"). 03 —
  New verifiers on the Mac records this in the ADR 0006 exception.

## Answer

2026-10-14 16:40 ET. **Resolved.** Every acceptance box is met with a scripted provider (an `external_fixture`
emulating Codex), a stand-in `frama-c` and a scripted proof hint check. No real Codex call or real WP run was
made; none is required by the boxes. Branch `probata-poc/t34`. Interface doc:
[`format-v0.4-proof-hinting.md`](../../../docs/reference/format-v0.4-proof-hinting.md).

**What was built**

| Piece | Where |
|---|---|
| Role `proof_hinting` in `provider_roles.ROLES`, hints-only schema `HINT_OUTPUT_SCHEMA`; `provider_roles.run` dispatches to it | `swdb/provider_roles.py` |
| Workspace (fixed layout, read-only, `workspace.json`), visibility rules, narrow authors' exception, O3 confinement, role audit, hint set | `swdb/proof_hinting.py` |
| Frozen wrapper: MCP stdio server (`list_workspace`, `read_workspace_file`, `check_hints`, `prove_hints`) | `swdb/proof_hint_wrapper.py` |
| Rewriting workspaces refuse hint records (`refuse_hint_records`, in `context_documents` and the prompt-only route) | `swdb/provider_workspace.py`, `swdb/rewrite.py` |
| `rewrite.configuration_from(mapping)` (the default Codex config has no file) | `swdb/rewrite.py` |
| Tests and fixtures (scripted provider, stand-in `frama-c`, scripted check) | `tests/test_proof_hinting.py`, `tests/fixtures/proof_hinting/` |

**Acceptance, box by box**

- Launch: `provider_roles.run("proof_hinting", Inputs(...), None, config, folder)` goes through
  `rewrite.interpret` (pins, output check, retained call folder). `default_config()` is Codex at
  `PINS["codex"]` (`gpt-5.6-sol`, `xhigh`). The hint set records `provider` (kind, resolved kind, model,
  effort, classification, CLI version) and per-hint provenance.
- Visible set: a test compares the tree under `workspace/` with `workspace.json` `visible_files` (path to
  sha256): equal, and exactly the ten layout files.
- Hidden material: one control each (evaluator code, workload input, test, negative control, another
  candidate artifact, counterexample) refuses before the call folder exists and names the file. Also refused:
  a second proof unit, a proof unit whose bytes are not the candidate's, a file outside the layout.
- Narrow exception: `TDStepMAA` is visible when `Candidate.authors_function == "TDStepMAA"` and the proof unit
  is `TDStepMAA`. Controls: refused when the record does not say so; `DOBFSMAA` and `PBFSMAA` beside it are
  refused; a record naming `DOBFSMAA` for a `TDStepMAA` unit is refused; every other role still refuses all six
  guarded names. Ticket 01's rewriting tests (`test_provider_authors_guard.py`, `test_counterexample_repair.py`)
  still pass.
- Output: the schema has only `hints: [{anchor, kind, text}]` and passes the strict check; a provider that
  returns `files` or `verdict` fails the output check.
- Frozen wrapper: inside the one call the scripted provider starts the wrapper from the Codex argv's
  `-c mcp_servers.swdb_proof_hint.*`, reads a file, gets a check rejection by rule, and runs WP; the stand-in
  `frama-c` saw exactly the plan's frozen flags and the merged hint. Wrapper and plan hashes are in
  `workspace.json`. Refused: `-wp-cache update` and `-kernel-warn-key ghost:bad-use=inactive` on the wrapper's
  command line, as tool arguments, and in the plan's method flags. A changed check hash is refused. Answers say
  "never a verdict"; the hint set carries no wrapper result.
- No leak: a rewriting workspace refuses a hint set or hint records in repair evidence (including a
  counterexample repair) and among its files (JSON, YAML, format marker); the prompt-only route refuses one
  before any call. A rewriting workspace without hints is unchanged (provider workspace suite: 656 passed).
- Inputs immutable: files and folders are written read-only; a provider that tries to edit the lowering and
  the proof unit changes nothing, and `audit.json` lists both attempts; the call fails.
- Mac confinement: the Codex argv has `--sandbox read-only`, `--disable shell_tool`, no
  `--dangerously-bypass-approvals-and-sandbox`, the wrapper as the only MCP server (checked on the real Codex
  adapter's argv too). A provider that starts a build (`clang++ ...`, code `build`) and one that writes
  outside the workspace (`external_write`) are refused, each recorded in `audit.json`. Real Codex on Linux and
  Claude refuse to start.
- Mac memory rule: each `prove_hints` WP run holds the machine-wide verifier lock: with another process
  holding it, the wrapper's WP started only after release (wait recorded in `calls.jsonl`). It runs under
  `rss_watchdog` at the plan's cap (8 GiB default); with a 200 MB cap the stand-in's 600 MB job is reported
  `out_of_memory`.

**Tests** (Mac, serial, no xdist, `-m "not whole_store"`; report logs in `/tmp/claude/probata-runs/t34/`):

- `tests/test_proof_hinting.py`: 53 passed (`r1.jsonl`).
- `test_format_doc.py`, `test_provider_role_schemas.py`, `test_provider_authors_guard.py`,
  `test_provider_pins.py`, `test_provider_guard.py`, `test_provider_guard_scope.py`, `test_provider_login.py`,
  `test_provider_outcomes.py`, `test_provider_capacity.py`, `test_estimation_role.py`, `test_rewrite_stream.py`:
  187 passed, 15 skipped (Linux-only guard cases) (`r2.jsonl`).
- `test_counterexample_repair.py`: 47 passed (`r3.jsonl`). `test_provider_workspace.py`: 656 passed (`r4.jsonl`).

**Assumptions** (the ticket's Notes assumptions are implemented as written; these are new):

- Assumption: with the shell off, the agent reads its workspace through the wrapper's `list_workspace` and
  `read_workspace_file` tools (only `workspace.json`'s files, hash-checked), not inline in the prompt (Codex's
  argv prompt limit is 96 KiB; t07c's workspace was about 75 KB).
- Assumption: "only through the wrapper" is enforced by having no shell at all (ticket 07: Codex's macOS
  sandbox does not restrict reads) plus the role's own event audit: any command, file change or other tool
  fails the call. The Landlock audit (`provider_audit`) is not used, because it refuses every MCP tool call.
- Assumption: the Why3 socket risk does not apply: the wrapper is an MCP server Codex starts outside its
  shell sandbox, as in t07c runs 5 and 6, where WP ran through it under `-s read-only`. WP scratch and
  `TMPDIR` live in `<call>/wrapper/scratch-N`, outside the read-only workspace, deleted after each job.
- Assumption: the proof hint check plugs in as `check(base, anchors, hints) -> {passed, rejections, merged}`
  (a file path and function, hash-pinned in `workspace.json`); `base` is the WP input without hints (the
  caller's `WpAdapter._input` output). Tested with a scripted check until 35 lands.
- Assumption: the authors' code exception is `Candidate.authors_function`, which must equal the proof unit's
  function; the caller sets it from the candidate artifact's record.
- Assumption: real Codex on Linux refuses to start for now (its Landlock roots must admit the wrapper's
  verifiers); that belongs with the mbit10 tickets (57/58).
- Assumption: the role drops Codex's `features.code_mode.direct_only_tool_namespaces` override, which might
  hide MCP tools; t07c's working argv did not set it.

**Not done, and why**

- No real Codex call: the confined real argv is unit-tested but not run. First real use (37 or 39) should do one
  low-cost call to confirm Codex 0.153 starts the MCP server with these `-c` options under `--sandbox read-only`
  and the adapter's other flags (`--ephemeral`, `--ignore-user-config`, `sqlite_home`).

**Interface notes**

- 35: provide `check(base, anchors, hints) -> {"passed", "rejections": [{"hint", "rule", "detail"}], "merged"}`;
  pass it as `wrapper_plan(..., check=(path, "check"))`. The hint set's record shape (`provenance`) is 35's to
  finalize.
- 37: build `Inputs(workspace_files(...), Candidate(...), wrapper_plan(...))`, call
  `provider_roles.run("proof_hinting", inputs, None, config, round_folder)` once per round; charge it through
  `Phase.charge_hint`. Do not hold the verifier lock across the call (the wrapper would take the nested lock).
  `metadata["wrapper_calls"]` counts in-call tool uses (not provider calls). A unit file that defines other
  authors' functions is refused: snapshot only the candidate's function.
