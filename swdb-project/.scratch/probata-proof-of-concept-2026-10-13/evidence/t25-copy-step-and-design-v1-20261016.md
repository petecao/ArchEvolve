# Copy-step conjunction design — 2026-10-16 ET

This is passive source design, not an implementation, retained-task closure, new proof, or admission. The grow38 producer at `37ffe407a10888ff9628c75f37ba770995a3ecd5` reached the original `grow.copy.step` after 27 successful native targets and left ten targets unexecuted. That is the actual open target to bind after root's corrected metadata collector succeeds. No solver-failure cause is inferred from the timeout.

Source/definition pins and the exact original statement are in the adjacent JSON (`3f622222c54bae793eff45037fc449cf1376d54187ef3a676710c107bd381b0f`). The heap theory and complete appended PRELUDE literal are byte-identical between actual source37 and prospective source6216. Source6216 already contains the reviewed, capture-refusing integer-term substitution needed for `k+1`; a new arithmetic language extension is unnecessary.

Let the quantified variables remain exactly `entry,h,r,o,b,bo,s,c,f,cap,k`. Keep the whole antecedent

```text
A = t25v3_copy_inv(entry,h,r,o,b,bo,s,c,f,cap,k) && k < s
H = Heap::copy_int(h,b,bo+4*k,f,4*k)
```

The existing target is `forall variables. A ==> t25v3_copy_inv(entry,H,r,o,b,bo,s,c,f,cap,k+1)`. Expand only its conclusion using the physical source definition of `t25v3_copy_inv`. The proposed fifteen independently required conclusions are:

| Duty | Exact instantiated conclusion |
| --- | --- |
| Entry well-formedness | `Heap::well_formed(entry)` |
| Updated heap well-formedness | `Heap::well_formed(H)` |
| Entry eligibility | `t25v3_eligible(entry,r,o,b,bo,s,c)` |
| Updated eligibility | `t25v3_eligible(H,r,o,b,bo,s,c)` |
| Advanced index and size/capacity bounds | `0 <= (k+1) <= s <= c < cap <= 4611686018427387903` |
| Fresh identity | `f == Heap::fresh_id(entry)` |
| Unissued identity | `!Heap::issued(entry,f)` |
| Receiver separation | `f != r` |
| Old buffer separation | `f != b` |
| Destination write domain | `Heap::typed_writes(H,f,0,4*cap,4)` |
| Destination release domain | `Heap::freeable(H,f,0)` |
| Destination extent | `Heap::bytes(H,f) == 4*cap` |
| Frame preservation | `t25v3_copy_frame(entry,H,f)` |
| Advanced copied prefix | `Heap::copied_prefix(entry,H,b,bo,f,(k+1))` |
| Remaining uninitialized tail | `(forall integer j; (k+1) <= j < cap ==> !Heap::initialized_at(H,f,4*j))` |

Each duty repeats **all of A**, with no new premise and no sibling result imported. Each appearance of H is the exact existing `copy_int` term, not an additional quantified heap or assumed output relation. The full source conjunction remains reference-only; it is never imported as a proved theorem.

The logic rule is pointwise `A => AND(C_i)` iff `AND(A => C_i)`, under the original universal quantifiers. Predicate substitution is simultaneous. The arithmetic replacement `(k+1)` must retain parentheses, especially in inequalities and the tail binder. The physical definition's nested `x,p,j` binders are disjoint from every variable in the substitution arguments. The existing helper refuses capture and unknown grammar; it must not silently rename or weaken scope. Do not add `k>=0`, `k+1<=s`, typed-access, freeability, separation, or prefix facts as new hypotheses: the duties must derive them from the original A where required.

The source assignment and increment are the existing C loop `fresh[k] = this->data[k]; ++k`. Ownership stays with source groups `G5,G6,G9`. Both `grow.copy` and `grow.loop.increment` inventory owners must expand to all fifteen new leaf IDs; unchanged numeric arithmetic duties remain mandatory. `Heap::copy_int` is defined as a uniform `put_integer` of the source `load_int`. Its access/type checks remain separate read/write obligations. Nothing here changes object identities, allocator behavior, escaping raw aliases, stale-alias treatment, arbitrary incoming heaps, or the qualified unary reallocation domain.

Before implementation, the retained printed WP query and each materialized SMT goal must bind to this exact source statement through the actual producer's variable mapping, input SHA, source spans and current definition. Declaration/hypothesis census and support attribution must show that the desired current/future loop result is not an assumption. Materialized tasks are not asserted to be solver submissions. Preserve original open target/raw/source/record and the 27 successful prefix observations without promoting them into a new record.

A subsequent source patch should reuse the reviewed `predicate_conjuncts` mechanism. Preserve every other 37 grow target C payload and every other 43 reserve target C payload byte-for-byte. Add one reference C file for the original whole step. Anticipated target counts become grow52 and reserve58; ctor35/dtor11 remain unchanged. The main caller source without application rows would have115 pending duties; the separately restored three-application caller would have118. These counts are source-planning consequences, not formal goal counts or proof acceptance.

The compiler-free TDD slice should check exact conclusion reconstruction, full-A equality for all fifteen leaves, no dependencies or added premises, correct protected `k+1` and nested binder scopes, tamper refusal, complete event ownership, reference-not-executed membership, and unchanged other payloads/theory/body/contracts. Negative controls should mutate A, replace the copied prefix length with k, capture a binder in an argument, omit a leaf, add a sibling dependency, or alter the whole reference. The current actual failure provides the real solver RED; these source tests cannot establish the mathematical proof.

Only after source-equivalence review and root admission may an actual diagnostic or full public profile run. All new targets must use the ordinary setup/readers with the declared per-goal portfolio/cache/RTE/init/smoke policy. A complete new public model record and independent task/import/foundation/runtime/lifecycle audit remain necessary. Fifteen top-level leaves may still contain difficult nested predicates; this design does not guarantee solver success or authorize further expansion without the next exact task diagnosis. No original-v2, generic caller, C++ equivalence, or ticket25 completion is claimed.
