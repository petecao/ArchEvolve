# Ownership10 source interpretation for the G621 cold review

2026-10-16 ET. Independent source reasoning by lane_coordination. This is a manual
mathematical interpretation, not an executed verifier result or a public proof
record. Actual retained proof-term/import/support reconciliation remains pending.

The exact source theory is `vector_owned_state.mlw`, SHA-256
`a2c295d2c6720a9c8c522f05e19723c2d2d2a32b63f9b198aab03f195269e4b6`.
The canonical source component is `vector_owned_transfer.py`, SHA-256
`6fa50d3b0ff6610c541bfa787179b37c6c8b50e4155fb2b0605d00e1eaffd085`.
The ten complete canonical statements keep their full antecedents and declare no
sibling dependencies. The original eight move/swap C units are source context;
none is a premise establishing any theorem below.

## Concrete model and consistency boundary

Use the ordinary unbounded integers and total mathematical maps. A state is the
pair `(active: Int -> Bool, backing: Int -> Int)`. Map lookup and functional update
have their standard meanings. The record, empty maps, predicates and transitions
are total definitions. The Owners module adds no axiom, lemma or goal. This gives
a concrete interpretation of the source extension relative to the standard
integer/map theory. It does not establish that every actual imported solver
assertion, driver transformation or native translation is sound.

For `valid(s,f)`, `f` is positive; active receiver identities and their nonnegative
backing identities are below `f`; distinct active owners have distinct nonzero
backings; and a nonzero active backing cannot equal any active receiver identity.
Zero represents no backing. These are registry facts about a source-established
complete owner set. They do not describe every raw pointer or prove a relation to
physical memory.

Empty at frontier 1 is valid. A nonvacuous move premise is frontier 4 with active
receivers 1 and 2, backings 0 and 3, destination 1 and source 2. A nonvacuous swap
or retirement premise is frontier 5 with active receivers 1 and 2 and backings 3
and 4. All other receivers are inactive. Shared-backing rejection has the concrete
antecedent receivers 1 and 2 both active with backing 3. These examples witness
nonempty source premise domains; they do not prove any universal duty.

The normal global `check lemma` route produced zero smoke tasks. There is no
empirical smoke consistency/body reachability observation to accept or invent.

## Independent interpretation of all ten duties

| Duty | Complete source reason | Material condition retained |
| --- | --- | --- |
| `empty.valid` | The active map is constantly false, so every active-owner implication and exclusivity implication is vacuous. | The supplied frontier must be positive. |
| `receiver.fresh` | Identity `f` cannot already be active or be a current backing because each such identity is below `f`. Registering it with backing zero preserves exclusivity and receiver/backing separation; all old bounds remain valid below `f+1`. | The entire incoming state is valid at `f`. Freshness is only relative to the current registry. |
| `buffer.fresh` | A new backing `f` differs from every old active receiver and backing. Updating the selected active owner's zero backing creates no duplicate nonzero backing. Old bounds remain valid and the new backing is below `f+1`. | Incoming validity, selected receiver active, selected backing exactly zero. |
| `move.transfer` | For distinct receivers, the nested stores give the destination the old source backing and then clear the source. Removing one ownership binding and transferring it to the empty destination preserves nonzero uniqueness, bounds and separation from all active receivers. | Both receivers active, distinct, destination backing zero, full incoming validity. |
| `move.frame` | Neither backing-store index is `q`; active is unchanged everywhere. Functional map-update lookup therefore preserves both observations at `q`. | `q` differs from both destination and source. No incoming validity is silently added or removed. |
| `swap.exchange` | Equal receivers take the identity branch. Distinct receivers exchange two old backing values while leaving the active map unchanged; this permutation preserves bounds, exclusivity and receiver/backing separation. | Both receivers active and full incoming validity; self swap stays admitted. |
| `swap.frame` | Equal receivers take the identity branch. Otherwise neither backing-store index equals `q`, and active is unchanged. | `q` differs from both swap receivers. |
| `swap.self` | The explicit equality branch returns the same state. | No incoming validity or active-owner premise is added. |
| `retire.frame` | Clearing one active flag and its backing weakens every validity condition over active owners. Other observations are unchanged. If the removed backing was nonzero and `q` is another active owner, old exclusivity gives distinct backings and old receiver/backing separation gives `q` distinct from that backing. | Full incoming validity, retired receiver active, `q` distinct from it. This transition performs no physical release. |
| `shared_backing.rejected` | The two stated distinct active receivers with equal nonzero backings instantiate the antecedent of exclusivity while contradicting its equality conclusion. | Both active flags, distinct receiver identities, nonzero first backing, equal backing values. It proves rejection, not incoming ownership. |

No theorem needs a previous ownership goal, constructor proof, destructor proof,
private-frame lemma, allocator contract or source-body premise. The cold reader
must verify that the actual twenty task artifacts preserve this property and
that every actual non-goal support assertion is independently attributed. Native
Valid labels and the manually checked source arguments alone do not establish
that retained tasks match these ten formulas.

## What this cannot establish

Registry freshness does not mean a physical allocation identity has never been
issued. Retirement does not implement or prove `Heap.release`, freeability or
automatic lifetime end. The four element instantiations do not exercise element
memory; their original C struct operations still require a complete layout,
read/write/initializedness/padding/effect and automatic temporary rule.

Source registration, a complete owner set, actual address/allocation history,
Heap/Typed correspondence, original requires/ensures/assigns/RTE/init duties,
allocator replacement behavior, callers, default models and public proof records
remain unadmitted. Standard theory/driver/solver soundness, source-to-binary
correspondence, runtime loader behavior and between-check identity remain TCB.
