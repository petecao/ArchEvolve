# Projected-C 630 — complete term and context audit

Date: 2026-10-16 ET. Independent reviewer: `/root/lane_coordination`.

**Decision: the conditional projected-C observations have complete term/context attribution. The original proof remains `not_proven`, and source, body and caller admission remain false.** This review ran no compiler, native helper, verifier or solver. Read-only standard-library parsers operated on mbit10; raw C, AST and SMT files stayed there.

All 314 retained files, 23,681,513 bytes, match the earlier independent manifest and remain unchanged before/after this audit. Fresh physical checks match 333 source/helper pins, all 1,623 consumer files totaling 1,338,043,021 bytes, selected runtime/import/configuration files and 1,983 LLVM headers. This is physical attribution, not a dynamic-loader or submitted-byte attestation.

The 17 ordinary native Valid goals comprise seven materialized query owners and ten internal-Qed goals. Each queried owner has primary and `zilch` files with identical query AST hashes; these 14 files do not count as 14 independent proofs. The ten others have explicit printed `Prove: true` plus native/internal-Qed evidence. Four additional smoke goals retain their operational health status and raw timeout/unknown attempts; their health neither proves the caller theorem nor certifies satisfiable premises.

| Retained query | Meaning and source premise |
| --- | --- |
| Constructor requires | Nonnegative signed32 `n` converts within the modeled maximum. No constructor postcondition is needed. |
| Data requires | Constructor vector validity implies the weaker readable representation. |
| Pointer-field initialization | The constructor representation summary supplies initialized receiver fields. |
| Reserve no growth | Constructor size equals `n`; representation size is at most capacity. |
| Payload initialization | On `n > 0`, constructor initialized-range and earlier assertions cover the first payload cell. |
| Payload read access | On `n > 0`, size/capacity and buffer validity cover one readable cell. |
| Result ensures | Constructor's quantified filled-value summary gives first value 7; the zero branch simplifies internally. |

The constructor's validity, size, filled values and `assigns *this` framing are **modular premises**, not body theorems established by this run. Receiver `memcpy` frame terms and typed memory maps reflect that call summary. The ordinary reader correctly refuses the unadmitted constructor assigns dependency. The four internally trivial caller assigns partitions cannot discharge private allocator writes or the source-to-model frame bridge.

Every nonglobal assertion in all 38 materialized files is attributed: 221 distinct bodies, 4,934 instances, zero opaque bodies. This includes 1,822 instances in the 14 ordinary materializations. The complete recursive import closure contains 32 selected standard/WP modules, with physical/module hashes and declared propositions retained. Additional context is the generated three-cell receiver layout, stack-object metadata, initialized-field framing, chunk domains and source vector predicate definitions. No prior/sibling heap result or scientific desired-result axiom is imported. Standard arithmetic, pointer/memory axioms, generic lemmas, WP translation and Why3 encoding remain explicit tool TCB.

The five Extern allocator/free clauses remain visible assumption entries. The constructor is not added to that whitelist. Successful allocation, freshness/freeability, incoming-memory framing, correct library bodies and release/lifetime correspondence remain trusted or pending as documented. Default allocator spelling and full-TU provenance do not exclude separately linked replacements or interposition.

Pinned `LogicSemantics.ml` SHA `7612c77530d4fe9bb89ec0b28460685f801b10e9b32fc9bfa479548d1b6e9e03`, line 882, routes native allocable/freeable/fresh/dangling predicates to an unsupported `Warning.error` branch. No retained ordinary term proves those lifetime predicates. The projected observer omits actual heap release and automatic scope end; its destructor representation assertion proves neither operation. The native log's skipped unaligned-pointer and valid-function RTE guards also remain recorded.

The original entry refusal and its exit 1 are unchanged. The normal reader remains `not_proven / unclassified_wp_outcome`: `not-Valid property has no classified failing goal: assigns *this;`. No public proof record, current constructor body record, source/Typed bridge, body/caller acceptance, universal setup attestation or ticket closure follows.

The [complete decision and all goal/premise/TCB bindings](t25-projected630-complete-term-context-independent-decision-20261016.json) have SHA-256 `df43dba8bf3eca55649086e6b6addda9de6bbfbde4b46175d4d5d9eeb4e377aa`. The physical/term capture has SHA-256 `9bf81439f36d50b82f91834dd9e39d2afc799d73c13f0facf0e5ae420f7f4b3d`. Required next work remains source-created receiver/buffer identities, constructor/private-frame/lifetime dependency composition, Typed field/value/init/release correspondence, and the complete original observer proof.
