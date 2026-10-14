# The proof_hinting role and its workspace

Created: 2026-10-14 (Eastern Time), Probata proof of concept ticket 34.
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/34-proof-hinting-role.md`; design:
`.scratch/formal-verification-2026-10-09/spec.md` ("Proof-hint loop": workspace; "Provider guard and
workspaces"; O3); glossary: proof hint, proof-hint agent, hint set, proof hint check.

**In one line:** one provider call shows the proof-hint agent one proof unit's failing WP goals in a
read-only workspace and returns a hint set of `{anchor, kind, text}` records; the agent can read the
workspace and run the proof hint check and WP only through a frozen wrapper.

Code: `swdb/proof_hinting.py` (role, workspace, confinement, audit), `swdb/proof_hint_wrapper.py` (the
frozen wrapper). Ticket 37 (the loop) calls it; ticket 35 supplies the real proof hint check.

## Calling it

```python
from swdb import provider_roles, proof_hinting
plan = proof_hinting.wrapper_plan(base=wp_input_without_hints, method_flags=lineup_flags,
                                  seconds_per_solver=30, check=(check_path, "check"))
files = proof_hinting.workspace_files(function=..., lowering=..., anchors=..., proof_unit_path=...,
    proof_unit_text=..., formal_halves=..., unit_postcondition=..., summaries={...}, goals=[...],
    rejected=[...], blamed=[...], seeds=[...])
candidate = proof_hinting.Candidate(id=..., files={path: sha256}, authors_function=None)
hint_set, metadata = provider_roles.run("proof_hinting", proof_hinting.Inputs(files, candidate, plan),
                                        None, proof_hinting.default_config(), call_folder)
```

- `default_config()` is Codex at its pin (`provider_adapters.PINS["codex"]`: `gpt-5.6-sol`, `xhigh`).
- The prompt is fixed (`proof_hinting.PROMPT`, hashed in `workspace.json`); `run` refuses an added prompt.
- Every refusal raises `Failure` before any provider call opens, naming the file.

## Workspace layout (all read-only)

| Path | Content |
|---|---|
| `lowering/<f>.c`, `lowering/<f>.anchors.json` | the C lowering with its `/* swdb-anchor <id> */` lines and anchor list |
| `proof_unit/<path>` | the candidate artifact's C++ proof unit; its sha256 must equal `Candidate.files[path]` |
| `contract/formal_halves.acsl`, `contract/unit_postcondition.acsl` | what is proven |
| `summaries/<name>.acsl` | summaries as ACSL (zero or more) |
| `context/goals.json` | failing goals, each with `kind` and `failure_class` |
| `context/rejected_hints.json` | `{hint, rule[, detail]}` per earlier rejected hint |
| `context/blamed_hints.json` | `{hint, reason}` per earlier blamed hint |
| `context/seeds.json` | seed hints `{anchor, kind, text, source}` |

Nothing else is accepted. Refused by path, each naming its category: evaluator code, a workload input,
a test, a negative control, another candidate artifact (also: a proof unit whose bytes are not the
candidate's), other hidden SWDB folders, agent instruction files. A counterexample anywhere is refused
(map 13 item 10). The authors' accelerated functions (`provider_roles.FORBIDDEN_SOURCE`) are refused
everywhere, except the proof unit's own function when `Candidate.authors_function` names it (map 18
item 6); a second authors' function is still refused.

## `workspace.json`

`format` (`swdb.proof-hinting-workspace.v1`), `role`, `candidate`, `function`, `proof_unit`,
`authors_code_exception`, `root`, `home`, `read_only`, `visible_files` (path to sha256, exactly the
visible tree), `visible_files_sha256`, `wrapper` (`path`, `sha256`, `server`, `tools`, `plan` path and
sha256, `wp_flags`, `proof_hint_check` path, function and sha256), `prompt_sha256`,
`output_schema_sha256`, `confinement`, `login_copy_deleted`.

## Output

The provider returns `{"hints": [{anchor, kind, text}]}` and nothing else
(`provider_roles.HINT_OUTPUT_SCHEMA`; extra fields such as code or a verdict fail the output check). The
role returns a hint set: `format` (`swdb.proof-hint-set.v1`), `role`, `candidate`, `function`, `hints`
(each with `provenance: {by: proof_hinting_agent, provider_kind}`), `provider` (`kind`,
`resolved_kind`, `model`, `effort`, `classification`, `cli_version`), `workspace_sha256`. Ticket 35 owns
the hint record's final shape.

## The frozen wrapper

An MCP stdio server: `python -I swdb/proof_hint_wrapper.py --state <call>/wrapper`. Any other argument
exits 2. Tools take exactly the arguments named; any other argument (a flag included) is refused.

| Tool | Does |
|---|---|
| `list_workspace {}` | lists the visible files |
| `read_workspace_file {path}` | one visible file, only while its sha256 matches |
| `check_hints {hints}` | the plan's proof hint check: `check(base, anchors, hints) -> {passed, rejections, merged}` |
| `prove_hints {hints}` | the check, then Frama-C/WP on `merged` with the plan's frozen flags |

- Frozen flags: the method version's WP flags (must hold `-wp-cache none` and `-wp-model +real`; no
  warning-key change, no session, cache-env, prover, timeout, parallelism, machdep, `-then`, `-load` or
  `-save`), then `-machdep x86_64 -wp-prover alt-ergo,z3,cvc5 -wp-timeout <s> -wp-par 1`.
- Each WP run is one real verifier job: `verifier_lock.hold` on the plan's lock (a second job queues),
  `rss_watchdog.run` at the plan's cap (8 GiB, `SWDB_VERIFIER_RSS_CAP_BYTES`), scratch deleted after.
- Each call appends to `<call>/wrapper/calls.jsonl`; every answer says it is feedback only, never a
  verdict. The role's metadata names that log in `wrapper_calls` (count, path, sha256); no record reads it.

## Confinement and audit

- Fixture (`external_fixture`): unconfined on a fixture host; the Codex argv is still built and confined.
- Real Codex on the Mac (O3, ADR 0006 scoped exception): `--sandbox read-only` replaces the guard's
  bypass flag, `--disable shell_tool`, the wrapper is the only MCP server, the session login copy is
  taken directly (no Landlock). Real Codex on Linux and Claude refuse to start (not built).
- `audit.json` (`swdb.provider-audit.v1`, `role: proof_hinting`) fails the call on: `build` (a compiler
  or verifier command), `shell_command`, `immutable_input` (an edit attempt or a changed input),
  `external_write` (a write outside the workspace or a new file beside it), `new_file` (in the
  workspace), `forbidden_tool` (anything but the wrapper's tools), `outbound_connection`, and event-log
  problems.

## Rewriting workspaces refuse hint records

`provider_workspace.refuse_hint_records` (in `context_documents`, so also in counterexample-guided
repair, and in the prompt-only route of `rewrite.call`) refuses any shown file or repair input with a
proof_hinting format name, a record holding `anchor`, `kind` and `text`, or a `hint_set` /
`proof_hints` key.
