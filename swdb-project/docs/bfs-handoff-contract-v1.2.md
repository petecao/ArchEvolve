# Evaluation-result handoff, format 1.2: the `certification_level` block

Created: 2026-10-14 ET (Probata proof of concept ticket 18). Code: `swdb/handoff_level.py`.

**In one line:** every `evaluation_result` envelope now says, in fixed sentences, what has been proven
about the candidate artifact's correctness, and that this says nothing about its speed.

- **Version.** Every `swdb.bfs.handoff.evaluation_result` envelope is `format_version: '1.2'`: the
  [1.0 content](bfs-handoff-contract-v1.md), plus [1.1's functional additions](bfs-handoff-contract-v1.1.md)
  on functional evaluations, plus `content.certification_level`. The other message kinds stay 1.0.
- **Reported, never ranked.** The block holds no rank or score. It never changes `performance_claim` or
  `result_class`: a proven-unbounded candidate artifact with no gain still claims nothing about speed.

## The block

| Field | Meaning |
|---|---|
| `candidate` | the candidate artifact the evaluation names |
| `level`, `level_words` | the level `swdb candidate-level` reads now ([level rule](reference/format-v0.4-level-rule.md)): `proven_unbounded`, `proven_within_bounds_threads_k`, `proven_within_bounds_threads_1`, `certified`, `uncertified` or `rejected`, and its plain words |
| `proven` | true when the level is a proven level |
| `bounds` | proven only: each bound dimension, thread count first, as `{dimension, value}`; `value` is the bound or `"any"` (unbounded). Otherwise null |
| `assumptions` | proven only: the level's assumption set, one `{kind, reference {id, sha256}, sentence, records}` per assumption; `sentence` comes from the fixed template of its `kind` |
| `highest_level_reached`, `failures` | not proven only: the level reached, and each way the proof attempts ended, `{class, words, records}` (a failure class or skip reason in the words of vocabulary `proof_failure_classes`; `refuted`; `stale`, an earlier proof that stopped counting) |
| `proof_records` | proven: the counting proof records that set the level; not proven: every proof record of the candidate artifact (the attempts) |
| `speed` | always `Says nothing about speed.` |
| `snapshot` | the dated level snapshot: `{level, at (YYYY-MM-DD HH:MM ET), level_rule, records}`; a rendered message keeps it, while `swdb candidate-level` may later read another level |
| `text` | the block as plain sentences, for example: "Proven for every size and every thread count (threads: any; edges: any; vertices: any). Assumes: clang-22.1.8 works correctly (a trusted tool, not checked). Says nothing about speed." |

## Fixed sentences only

- **Level:** "Proven for every size and every thread count (...)." / "Proven within bounds (...)." /
  "Proven within bounds, one thread (...)." / "Not proven. Highest level reached: certified."
- **One template per assumption kind**, filled only with the reference ID: assumed clause ("<the clause's
  own statement in the library> (assumed; owner <its owner>)."), proof semantics, summary, reduction,
  trusted tool, written proof, platform choice. An assumed clause's reference is `<contract>#<clause>`.
- A proof record's own assumption `sentence` (free text) never reaches the block.
- **Rendering stops with an error** (no envelope) when: an assumption kind has no template; an assumed
  clause is not in the library; a reference is not an ID; a failure class has no words; the speed sentence
  is missing; a proven level's proof record IDs do not resolve; the block holds a rank or score.

The block is checked where it is rendered, not by `swdb validate`: the envelope is a message, not a stored
record. The checked-in example check (`scripts/bfs_handoff_examples.py --check`) keeps each archived
snapshot's date and compares the rest.
