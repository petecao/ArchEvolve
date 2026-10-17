# Constructive swap-header witnesses

Prepared: 2026-10-16 ET. Source preparation only; no verifier run or scientific admission.

The three targets replace only the two integer existential variables in the
original header conclusion with explicit terms. The complete quantified prefix,
original antecedent, case guards, active-owner test, ready test and final header
predicate remain unchanged. The resulting targets are stronger sufficient goals;
the converse is not claimed.

| Original guard | Size witness | Capacity witness |
| --- | --- | --- |
| `observed == l` | `nr` | `cr` |
| `observed == r` | `nl` | `cl` |
| `observed != l && observed != r` | `OwnedEffects::size(h,observed)` | `OwnedEffects::capacity(h,observed)` |

Both equality guards remain active when `l == r`. No separation premise or
caller requirement is added. The two original header predicates in the complete
antecedent describe the same integer cells in that case, so their size/capacity
fields agree by the pinned `Integer` cell constructor and field definitions.
The source swap still copies left to temporary, right to left, temporary to
right, then ends temporary storage. Reconstruction may choose the left case
first for overlapping guards, but all three stronger targets remain pending and
must be proved independently.

For each target, a closed first-order term kernel parses the pinned original
header body, checks source-backed argument/result sorts, substitutes only the
two bound integer variable nodes and rejects captured or unbound names. Its
certificate records capture-free existential introduction. Replacing the exact
instantiated conclusion by the original existential restores the entire old
case statement byte for byte. The predecessor's equality partition then covers
the unchanged original universal formula, including self-swap. These are source
construction checks and a logical sufficient-rule derivation; they do not prove
the stronger header facts.

The seven physical predecessor/kernel containers and nineteen definition slices
are checked before preparation. Full Heap, Owners and OwnedEffects theories,
the original source units, all thirteen original parts, the three old case
targets and twelve unchanged conditional duties remain content-bound. No old
case or successful sibling is imported as a theorem premise. The three generated
targets import only the original theories and keep empty proof-dependency lists.

The public seams are `declaration`, `prepare`, `check` and `check_launch`, as
approved for this preparation. Four retained public checks cover complete
statement inverses, physical kernel mutation, ill-sorted/captured/unbound witness
refusal, all four supported element types, artifact/metadata/membership tampering
and unconditional launch refusal. A bounded audit rejects child processes,
dynamic native loads and network calls. The first three red/green slices and
the final launch slice are retained. The second slice also retains an authoring
path mistake and a failed unchanged-source green attempt; the later passing
attempt is named `green-v2b`.

The original G644 run remains unchanged: all three old existential cases are
unproved, each with Alt-Ergo Failed, CVC5 Unknown and Z3 Timeout. The cause of
Alt-Ergo's failure is unresolved. This preparation does not relabel that run,
increase any bound, establish consistency from absent smokes, or claim a
counterexample. Fresh actual proofs, complete cold interpretation and the
source/lifetime/Heap/Typed correspondence remain required. Source, body, caller,
default-route and public-record admission remain false. `check_launch` refuses.
