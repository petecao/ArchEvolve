# 34 — proof_hinting role and workspace

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 00:15 ET (review fixes, round 4); 2026-10-13 23:40 ET (review fixes, round 3); 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** claimed
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
