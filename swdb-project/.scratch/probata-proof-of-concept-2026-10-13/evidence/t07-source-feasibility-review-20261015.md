# Ticket07 source and proof-interface feasibility audit

Date: 2026-10-15 23:23 ET. Read-only audit; no compiler, native, theorem-prover, probe or SSH execution. Frozen source: `ac6bb42ead0beb38da954c3528a1821c6d9f78eb`, physically clean at inspection. Source root: `/private/tmp/probata-resume-t07-method23`.

**Repair the source-summary domains before another counted admission.** The clearest defects are an incorrect unsigned arithmetic summary and an admitted queue-capacity counterstate. Neither identifies the cause of run26's remaining proof timeouts. A guard repair alone does not address either defect or the proof dependency graph.

## Findings and evidence boundaries

| Finding | Classification | Consequence |
|---|---|---|
| `size_t` fetch-and-add promises mathematical, non-wrapping addition without a domain bound | Definite source/summary mismatch on its public admitted states | At `SIZE_MAX, increment=1`, the actual operation returns old maximum and stores zero; the summary promises an unrepresentable result. The wrapper repeats the mismatch. |
| TDStep admits an allocated queue with no room for a newly discovered vertex | Definite source-domain safety defect; full counterstate below | The scalar path's final standard copy writes past allocation. Existing copy abstraction omits the premise that would expose this. |
| Standard-copy and helper contracts omit validity, pointer-range and some alias/overflow premises | Definite incomplete public domains; exact WP behavior not measured here | The contracts can model behavior where actual C++ operations have no defined execution. Correcting these domains creates genuine caller obligations, some not derivable from the current TDStep entry. |
| Search evaluates TDStep/global lemmas while final acceptance evaluates all bodies | Concrete interface asymmetry, not evidence of an actual unclosed helper goal | Header bodies have no hint anchors. Any mandatory unresolved helper obligations cannot be repaired by annotating those bodies through this interface. Audit their no-hint closure before admission. |
| Four nested proof levels connect range issuance to consumption, CAS history and queue membership | Genuine dependency bottleneck; insufficient evidence of mathematical infeasibility | Available vocabulary can express the needed finite relations. No missing recursive predicate, ghost array or extra axiom has been established. |

Only the authorized run26 aggregates were used: baseline103 open; one provider turn with4 hints/102 open; final397 scheduled with58 partial Timeout lines and no complete final-goal report. These aggregates cannot classify an individual failed obligation or establish whether a proposed repair would close it.

## 1. Incorrect unsigned arithmetic is independently actionable

`standin/gapbs_models.h:64–70` gives `__sync_fetch_and_add_size_t` only a valid-pointer requirement, yet promises that the new value is the mathematical sum of the old value and increment. `:112–118` gives its body-bearing wrapper the same promise. `apps/gapbs/src/platform_atomics.h:24–26` forwards to the unsigned compiler builtin. A valid independent `size_t` object containing its maximum and increment1 is in the stated domain; unsigned arithmetic wraps. The C source is defined, but the contract's equality is false. This example does not require an enormous allocation or pointer arithmetic.

Minimum sound alternatives: describe the primitive's actual modular result, then make the wrapper modular too; or explicitly restrict the wrapper to a no-overflow domain and discharge that restriction at every call. The primitive should still describe actual unsigned behavior on its full ordinary domain unless an explicit narrow model domain is recorded. Do not treat wrap as undefined behavior. Do not globally assume all additions are safe.

For a legitimate TDStep call, the initial shared-in bound is at most1,073,741,823 and the local buffer is16,384, so there is ample *arithmetic* room in 64-bit size_t once the buffer-count invariant is proved. This does not establish *allocation* room. Generic helper verification needs its own explicit bound rather than borrowing TDStep's caller facts.

## 2. Full TDStep entry counterstate and executed overflow

This is a static mathematical trace, not a retained actual execution or verifier counterexample. It checks every written TDStep requires clause. Use separately allocated, initialized objects and arrays throughout, including all interface objects. Set:

- num_nodes2, num_edges1; offsets allocation3 with values[0,1,1]; neighbors allocation1 with value[1]; parent allocation2 with values[0,-1].
- queue storage allocation exactly1 with value[0]; shared_out_start0, shared_out_end1, shared_in1, shared_max_size1. All object pointers and graph fields refer to the corresponding allocations. Initialize unused object fields; pvector end pointers are their proper one-past ends.
- TILE_SIZE1, SWDB_CHUNK_SIZE1, SWDB_FRONTIER_THRESHOLD1; acceleration-enabled false.
- The context's tile fields and register fields are each a permutation of0 through7. Allocate8 distinct one-int tile buffers. Set all tile lengths0 and all pending flags0; initialize the remaining ghost/device state.
- Keep the offsets, neighbors, parent, queue storage, global local-buffer storage, four interface-object allocations and8 tile allocations pairwise separate. This is stronger than the written separation clauses.

| Actual entry clause | Why this state satisfies it |
|---|---|
| guard_sizes, knobs |2 and1 are within bounds; all three knob values1 satisfy the ordered limits. |
| g/VertexOffsets/parent/queue validity | Each is its own correctly sized, initialized allocation with required permissions. |
| csr_offsets | The3-element allocation is valid; first0 and last1 equal num_edges; all entries in[0,1] and nondecreasing. |
| csr_neighbors | The single readable edge target1 lies in[0,2). |
| parent_valid | The2-element writable parent range is valid. |
| queue_window | The single-element writable range is valid;0≤1≤1≤1; its sole frontier value0 lies in[0,2). |
| separation | The9 allocation bases named by bfs_distinct_blocks are pairwise different by construction. |
| context | Tile/register IDs are in[0,8), each family pairwise distinct. |
| spd | Every tile's required one-int range is valid; length0 lies in[0,1]; all specified base inequalities hold. |
| dx100_idle | All pending flags are zero. |

The static C context defaults to zero IDs at program initialization. This counterstate is a *function-entry state of the stated unit contract*, consistent with the method's unfiltered-global model and its explicit context precondition; it does not claim that unmodified file-scope initialization alone establishes that precondition. A real system must initialize its contexts before using this interface.

The scalar path processes frontier vertex0 and its one edge to1. Parent[1] is negative, so the exact CAS succeeds, parent[1] becomes0, and local buffer[0] becomes1 with local count1. The final `QueueBuffer_NodeID_flush` obtains copy_start1, increments shared_in to2 without arithmetic overflow, and calls standard copy with source[storage,storage+1) and destination queue.shared+1. Forming that destination is legal one-past formation. Copying one element through it is the out-of-allocation write. The copy result pointer would also be beyond the original one-past limit.

All mem-region registration pointers formed before the scalar loop are legitimate: graph neighbors+1, offset and parent one-past ends, and queue shared+1. Thus the demonstrated failure does not rely on an earlier invalid formation, an accelerated instruction, duplicate frontier values, uninitialized metadata, overlapping allocations or size_t wrap.

**No valid hint can derive the missing capacity from the unchanged entry.** Merely adding capacity≥num_nodes is also insufficient for all currently admitted states: the entry allows an already full queue with duplicate prior entries while another node remains unvisited. A sound caller domain needs a capacity-credit fact justified by the actual queue/visited history, or a stronger uniform reservation established by the actual allocation/caller. Adding a desired postcondition as a premise is not a repair.

The natural GAPBS caller allocates a queue of g.num_nodes() (`apps/gapbs/src/bfs.cc:133`), marks the source visited before insertion(:132–135), and uses successful first-discovery CAS before new insertion. That provides a plausible caller invariant: prior occupied queue entries inject into already visited vertices, while new insertions consume distinct previously unvisited vertices. Preserve this relationship through resets/bitmap transitions before claiming it for the complete caller. The excerpt alone is not a completed caller proof. With it, a mathematically justified occupancy bound can remain fully symbolic. The existing TDStep entry does not state this relationship.

## 3. Correct copy, flush and helper domains without hiding obligations

`std_copy_NodeID`(:89–96) requires an ordered source endpoint pair and source/destination separation, but does not require readable source cells, writable destination cells, or explicitly a common source allocation and legitimate one-past/range formation. Its use of last-first in locations and result also depends on that range domain. A real std::copy contract must cover an actual valid source iterator range and sufficiently large destination, including the legitimate empty-range case. Do not fix this by asserting that every pointer-looking expression denotes an arbitrarily extensible buffer.

`QueueBuffer_NodeID_flush`(:183–199) needs its incoming local-buffer range readable, the incoming shared destination range writable, valid pointer formation, no-overflow for a mathematical occupancy promise, and frame separation sufficient to preserve the local snapshot across the occupancy update. Its present requirements separate copy source from destination and destination from metadata, but do not supply the public range validity or source/metadata independence. The simplest sound queue abstraction should establish its local/shared/object ownership invariant once and preserve it, rather than leaving each helper able to receive arbitrary aliased metadata.

`QueueBuffer_NodeID_push_back`(:202–232) supplies writable local storage and more separation, but does not reserve shared capacity in the flushed case; its public local_size is not fixed to16,384. Its zero/empty/buffer-full cases should each have a valid range domain. The constructor's n≤16,384 summary supplies storage for this specific TDStep instantiation; it does not repair the generic shared destination domain.

The pvector accessor/index bodies(:134–150), queue begin/end/size bodies(:152–162), and destructor(:177–180) likewise have public contracts that do not consistently provide valid/readable self and metadata or legal index/one-past formation. This is a public-domain audit finding, not a measured claim about a particular generated WP goal. End fields used during registration are not constrained by the written TDStep precondition to be valid iterator endpoints; initialization/representation should be part of a faithful object-domain model when they matter to the actual calls.

`wp_run.sh` final/baseline modes use -wp-no-filter-init and smoke tests, but **do not use -wp-rte**; only a separate wp-rte mode contains that flag(:77). Therefore all reported contract goals passing would not independently certify all C pointer/overflow safety checks. No-filter-init is not a substitute for enabling and discharging RTE obligations. This audit does not change the ticket's acceptance criteria or retroactively reclassify earlier runs; it identifies the scientific boundary that an honest throwaway model must state.

The huge finite TDStep queue assigns range(:53) preserves an intended frame but cannot supply allocation validity. Replacing an infinite location set with a finite upper bound does not justify writes to every location in that set.

## 4. What the proof interface can and cannot repair

The source keeps the TDStep names, scalar/accelerated structure and three hazard-read checks, and uses bodyless DX100 contracts. It is deliberately a hand model, not a C++ lowering-equivalence theorem. Fixed buffer allocation, added capacity metadata and eager-at-issue device values are explicit model choices that need their own faithful domains. I found no additional definite mathematical defect in the range-loop lexicographic contract on its stated legal inputs during this read. That is not an independent proof of every summary or of gem5 correspondence.

The accepted vocabulary already supports nonrecursive labelled predicates/functions, universally/existentially quantified invariants/assertions, scalar ghost witnesses, loop frames, integer variants and sound WP tactics. Those can express finite consumed prefixes, queue-buffer transfers and a well-founded cursor measure without a recursive definition or new trusted axiom. I therefore do not recommend relaxing the language ban or supplying concrete hints from an implementing agent.

Two concrete workflow constraints deserve prospective review:

1. Search rounds select only TDStep and global lemmas (`wp_run.sh:24–37`), whereas final replay checks all functions(:38–41). The headers have no annotation anchors. Close and retain no-hint helper obligations independently before counting, or expose any still-mandatory helper problem to an appropriately scoped source-repair stage. Do not drop the helpers from final acceptance.
2. A proposal permits8 operations/6,000 new characters; temporary total debt is bounded and expires in300s with4 repairs (`edit_core.py`, `staged_search.py`). A coherent cross-loop induction can initially add more obligations than it closes. This is a concrete search-policy hypothesis, not an observed explanation of run26 or a recommendation to waive any final proof. Evaluate it with generic controlled policy cases, not prior concrete hints. Formula-level dependencies should guide diagnostics; raw open-count changes are not proof progress by themselves.

After domains are sound, a fresh Codex still has to construct the actual cross-loop invariants. The central dependencies are range-output completeness versus consumed positions, gathered stale parent values versus present CAS state, and buffered versus flushed queue membership. They are already identified generically in the policy; repeating that prose is not evidence the task is solved.58 partial final Timeout lines and a102-open incumbent do not establish a realistic likelihood of complete acceptance on an otherwise identical rerun. A future actual admission needs a concrete, independently reviewed source/interface change with a justified path through these dependencies, while retaining the original60-minute acceptance and all goals.

## Read scope and next action

No prior concrete hints, provider conversations, candidate files, retained negative-control inputs/results, tests, held-out payloads or workload data were read. While reading terminal_plan.py for scheduling, an overbroad source excerpt also displayed its negative_replay implementation. Root was informed immediately. No historical negative payload was opened; the recommendations above do not use that implementation. Some source files were read by selected excerpts; the hashes below bind the whole immutable file, not an assertion that every byte was semantically audited.

Next action: ticket07 should repair the arithmetic/copy/helper domains in a separate source worktree and record the queue-capacity counterstate as a source-domain issue. Root must decide and document a caller-faithful capacity domain, because it cannot be proved from the current TDStep entry. No actual counted readmission is justified by this report alone.

## Exact source hashes

| Source file relative to frozen checkout | SHA-256 |
|---|---|
| `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/standin/tdstep_standin.c` | `b4a820bd20b197eee293616af17da884bbc63ed92f9252e77f261092387024de` |
| `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/standin/bfs_unit.h` | `1bcbf4dac683d6a46269fcd5f896fefc2571adc49d059b46f93fb25eb0f7b235` |
| `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/standin/gapbs_models.h` | `401d8ccfa8fdc1ef3734c97563a1c110d003d8847508aaa24ec3f300a33eed3e` |
| `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/standin/dxc_summaries.h` | `d708c0ef974e5ede1aaadd2b5e66dd785affa5e1dc6ef37419bf9e72517ae0d2` |
| `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/METHOD23.md` | `c70c52bb066462db14527e61f519a69f0ef177af0b3755c59c3756490e65c9c3` |
| `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/wp_run.sh` | `97130fcc3d087961484cddaad7b4ab798f7cf00920eab8b94ecdb64a285f9f1f` |
| `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/hints.py` | `48bafc2eab6caf40bb921e773212dff3efbbbc652aa2d120d87da4704b021bca` |
| `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/edit_loop.py` | `d240f5bbc204035073389def92de23712fbde3ee57afe974391d439443ba81f9` |
| `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/staged_search.py` | `125e2562342e6ba684d1189ca29fb48476b73bee30d0fd368f7f7c6b4c6b2419` |
| `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/focused_probe.py` | `9ad86e2c61530a19f95ebb4d5aff639d489ef5a0788a6a1e00ddbdf0bd7c05db` |
| `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/terminal_plan.py` | `b9de089b800a6d28888fc887d4040c3e0f238d4e14265129e82fdf55126ccc1a` |
| `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/edit_core.py` | `3474b00db4ac40a9ca3eb08a9323902243798eef538552176e07095ab9ab95be` |
| `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/loop.py` | `cb84fdca2b0d8dd0c77b286037513a4642835cd631ad9f87c74f0d736982d350` |
| `swdb-project/library/dx100/bfs_read_offload.inc` | `3c5867a2b8919806f681603836bd0cff448f21634485abf84e49ed71f25515ef` |
| `swdb-project/apps/gapbs/src/sliding_queue.h` | `f8389900181f1a63c0354e274561336191bbc0e4cfb5f34f70da3abc07e4d443` |
| `swdb-project/apps/gapbs/src/platform_atomics.h` | `1183b25883d497c038e70359eaf0ebcffdc7f097c7091e10af58c7415473d2b4` |
| `swdb-project/apps/gapbs/src/bfs.cc` | `7c32c3c8dc43bf7be417fc5c530b4578bfe3697d8eb47a161cdb142487823f73` |
