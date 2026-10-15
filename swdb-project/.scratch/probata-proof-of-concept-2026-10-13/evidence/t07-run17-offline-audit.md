# Run 17 offline proof audit — 2026-10-15 ET

Run 17 is unproven: **19/270 open = 2 unit + 17 hint goals**, all classified timeout. It finished at 08:25:15 EDT after 53.48 minutes; no final smoke run was reached (`summary.final == null`). The 251 passed ordinary goals are not a proof of the unit. This audit used existing source/artifacts only: no verifier, provider, or run18 was launched, and no frozen file was edited.

## Evidence and exact source

- Frozen worktree: `/private/tmp/probata-t07-run17`.
- Stand-in base: `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/standin/`.
- Run: `/private/tmp/probata-t07-20261015-run17/counted-17`.
- Best: `best.json`, `dir=attempt-r1f`, 38 hints, 19 open goals; final expanded source is `attempt-r1f/tdstep_standin.c`.
- `meta.json` names guidance `consumed-prefix-cursor-snapshots-v4`; `summary.json` has the final counts/budget boundary; `codex-r1/stdout.jsonl` preserves actual edit/check/revert results.
- All four frozen stand-in hashes match `meta.standin_sha256` on fresh read:

| File | SHA256 |
| --- | --- |
| tdstep_standin.c | d5d599e48c30b9877a3003345dac4077163ffb06359daa24142cf90cbe4540f8 |
| dxc_summaries.h | d708c0ef974e5ede1aaadd2b5e66dd785affa5e1dc6ef37419bf9e72517ae0d2 |
| gapbs_models.h | 401d8ccfa8fdc1ef3734c97563a1c110d003d8847508aaa24ec3f300a33eed3e |
| bfs_unit.h | 1bcbf4dac683d6a46269fcd5f896fefc2571adc49d059b46f93fb25eb0f7b235 |

Source line references below distinguish the original stand-in from the expanded best file.

## Was guidance17 realized?

**It was attempted and then reverted, so it is absent from the final best set.** The guidance in `edit_loop.py:65-86` explicitly asks for clamped original-frontier progress, a pre-issue cursor snapshot, consumed-batch refinement, and the scalar row/edge counterpart.

The provider did try it (`codex-r1/stdout.jsonl`, items43–46):

1. Item43 proposed `td_hit`, `td_cursor_hit`, outer/range/batch/scalar progress, and one comma-separated initialized ghost declaration. Hint checking rejected the declaration: `ghost witness expressions may not call, take addresses, or mutate state`.
2. Item44's combined declaration plus assignment still failed the restricted ghost grammar/ownership check.
3. Item45 split the two declarations and two assignments into four simple ghost hints. **Hint checking passed.** This demonstrates an available syntax for the requested scalar snapshots; the method did not fundamentally prohibit them.
4. Item46 ran the progress proposal. It was **reverted, open goals21→25**. Newly open were chunk-progress preservation, range-progress preservation, batch-progress establishment/preservation, and an assigns-exit obligation. The provider's broad simultaneous induction construction did not establish its own bridges.

The final 38 hints contain **zero ghost hints**, no `td_done`/`td_hit`/progress predicate, and no relation saying which original-frontier edges have actually been consumed. Final hints retain safety (`td_parent_ok`), queue bookkeeping (`td_queue_ok`), row bounds and cursor legality. A legal cursor alone is not a consumption proof. This is more precise than saying the provider ignored the guidance.

## The decisive missing completeness invariant

`td_parent_ok` (best hint r1c23h1) says: previsited parents stay unchanged; a still-negative parent retains its entry value; any newly nonnegative parent is a real frontier neighbor. It does **not** say every processed reachable vertex becomes nonnegative. `td_queue_ok` (r1c29h1) accounts for vertices already discovered, not which vertices must have been discovered. The final chunk/range/i/j/k invariants therefore express safety without completeness.

A concrete counterstate of the **loop abstraction**, not a counterexample execution, shows why `visited_iff_reachable` cannot follow from the final invariants:

- Two vertices, one edge: offsets `[0,1,1]`, neighbors `[1]`.
- Original frontier is queue `[0]`, `shared_out_start=0`, `shared_out_end=shared_in=1`.
- Entry and current parent are `[-1,-1]`; local queue is empty; shared input prefix unchanged; all device pending flags zero.
- Put `begin=1` at chunk-loop exit (or `i=1` at scalar-loop exit).

The parent, queue, buffer, cursor-bound and idle invariants permit this state: no vertex was newly visited, so their implications about new vertices are vacuous. Yet `bfs_reach{Pre}(...,1)` is true and current parent[1] is negative. The actual body should rule it out; the final invariant set forgets that fact at the loop cut. Increasing the solver budget or unfolding queue predicates cannot manufacture this missing relation.

## Exact range contract and the two cursors

Original `dxc_summaries.h:65-72,110-149` defines a lexicographic inclusive continuation cursor `(i,j)`; `j=-1` means before row i. The range call:

- emits valid CSR pairs strictly after the **old** cursor and at/before the **new** cursor (`125-129`);
- orders emitted pairs strictly (`130-132`);
- covers **every** valid pair in that interval (`133-138`);
- ends at `(n,-1)` if output is short, or at the last emitted pair if full (`139-143`);
- preserves legal state and cursor monotonicity (`144-146`).

Original unit `115-120` advances the cursor and may break before the CPU k-loop. Consequently, the post-issue cursor must not describe consumed work until all emitted positions are processed. The attempted item46 snapshot idea was semantically appropriate. At the k-loop head consumption is: prior chunks, pairs at/before the saved pre-issue cursor, and batch positions `<k`. At k==count, range coverage closes the interval and permits advancing the consumed cursor to the returned cursor. A count0 result must be connected to exhaustion through the contract's coverage/exhaustion clauses.

The row-to-original-frontier relationship is already attempted in `td_rows` and `td_emitted_pairs`; these remain unproved. Keep their stages separate: gathered lower/upper rows equal CSR offsets; emitted (row,column) is in that row; row maps to `queue[begin+row]`; neighbor[column] gives the discovered vertex. Bounds alone lose this chain.

## CAS bridge is also missing, even after adding a cursor

Original `gapbs_models.h:48-55,103-110` gives exact CAS, not spurious failure: success iff current value equals old argument; success writes new value, failure preserves the old value. Original unit `143-150` uses a parent value gathered **before the batch** as `hint`, then CAS and enqueue.

The final `td_k_values` only constrains vertices/frontier for the unconsumed suffix; it says nothing about `hints[q]` or their connection to parent history. Another concrete loop-abstraction counterstate is therefore allowed:

- Entry/current parent[v] = -2; hints[k] = -1; u is a valid original-frontier predecessor of v.
- Parent/queue safety invariants hold and the batch vertex/frontier relation holds.
- CAS(parent[v], -1, u) correctly fails; v remains unvisited even after advancing k.

This cannot arise from the actual gather plus monotone parent updates, but that relation has been forgotten by the k-loop abstraction. Do not weaken CAS or assume success. Prove a stable suffix bridge such as negative hints equal the entry-negative parent value, while nonnegative hints imply the corresponding current parent is already nonnegative. Together with `td_parent_ok`'s still-negative equality, exact CAS then yields “this consumed position's vertex is visited” on every path. Repeated vertices require retention of already-discovered visitation. Derive the bridge from gather's old-base postcondition and parent monotonicity; it is not a new input premise.

For the scalar branch, the load is immediate (`original172-174`), but the final j-loop still lacks completed-row/current-edge coverage. The corresponding progress relation must cover rows before i plus current-row edges before j, with all CSR/queue reads tied to Pre.

Queue preservation has a separate transient phase: a successful CAS marks a new vertex before `push_back` records it. `td_queue_ok` need hold at loop heads/after push, not as a false assertion immediately after CAS. Use the old-negative witness to prove the new vertex was absent from both old appended/shared and local queues, then use both buffered/flushed behaviors in `gapbs_models.h:202-227`. The final flush bridge must transfer local membership/uniqueness into the appended shared range (`183-194`).

## The other unit goal: parent-gather validity

`typed_TDStep_call___dxc_gather_5_dxc_gather_requires_3` is the final parent gather (`original124`, expanded best160), not the initial offset gathers. Its exact requirement is `dxc_summaries.h:99`: every selected index must yield a valid read from the supplied base. Existing `goal-r1c6/print.log:20943` identifies that instance (source line130 in that earlier printed candidate).

The desired chain is range-column bounds -> neighbor gather output equals neighbor[column] -> each output vertex lies in `[0,num_nodes)` -> valid parent cell. In final best, the large `td_emitted_pairs` assertion is before the neighbor gather and `td_batch_bounds` is **after** the parent gather. The latter cannot discharge the earlier call obligation. A smaller post-neighbor-gather/pre-parent-gather checked bridge would expose this chain, but the frozen stand-in has **no hint anchor between those gathers**: `after_count` precedes all three and `after_gathers` follows them. A comment-only intermediate anchor would therefore require an explicit new source/harness hash in a future method. Under the current anchors, derive the strongest small input/neighbor-index facts at `after_count` and target the exact call formula with controlled contract instantiation. Preserve tile0 length/content across the intervening frontier gather using its frame and distinct tile IDs. Do not add a parent-range assumption.

## Remaining hint goals grouped

| Group | Open hint goals |
| --- | --- |
| Range/data bridges | rows_init; cursor_preserved; rows_preserved; emitted_pairs; tiles_ready; batch_bounds (6) |
| Queue bookkeeping | chunk_queue_preserved; range_queue_established; k_queue_established/preserved; j_queue_preserved; flushed_queue (6) |
| Parent safety | k_parent_established/preserved; j_parent_preserved (3) |
| Other frame/safety | chunk_idle_preserved; k_values_preserved (2) |

Each is a timeout report, not proof of invalidity. Several may become easy after small instantiated bridges replace large nested quantified cuts. Conversely, downstream Valid goals can use unproved hints; the 251 passed goals do not independently validate those hints.

The idle obligation follows a concrete dependency chain: range wait7 covers its paired tile6 plus pending lower/upper/stream dependencies; later wait3 and wait5 cover frontier and parent/vertex writes. The final empty range batch still issues rows/columns and must be covered by wait7. Make these per-tile dependency facts explicit before concluding whole-device idle; no wait should be silently added or dropped.

## Prospective method18 guidance (not implemented or launched)

1. Require the provider to first inspect the range and exact CAS contracts and state a cutpoint induction plan. Give the accepted **simple scalar declaration then separate assignment** syntax as a syntax example; do not inject a solved benchmark hint set.
2. Start with a checked post-neighbor-gather vertex-index bridge, then the batch hint/parent relation. These remove local logical gaps before introducing a global reachability biconditional.
3. Add a fresh pre-issue cursor snapshot with narrow scope; prove its frame obligations. Build consumed-prefix progress bottom-up: scalar j -> scalar i; batch k -> range -> chunk. Use range coverage only after k==count, not immediately after issue.
4. Distinguish safety-only parent/queue invariants from completeness. Split the large conjunctions so a failed prefix, alias/frame or queue-transfer component is visible in one goal. Preserve original source contract, CAS semantics, smoke, frame seeds and final all-goal acceptance.
5. Account for the search rule: run17 reverted a needed induction proposal because total open goals21→25. Merely repeating “use snapshots” will repeat this bottleneck. Under the same monotone rule, ask for smaller independently proved bridges first. Any bounded staging/debt rule that retains a temporarily harder invariant would be a separately named method change, never a relaxed final verdict or an uncounted continuation.
6. Run18 would be fresh uncached evidence with its own method/source/harness hashes and count, not a continuation represented as run17 success. This report authorizes no launch.
