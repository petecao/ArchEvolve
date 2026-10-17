# No-growth source view: independent SPEC/correctness review

Date: 2026-10-16 ET. Reviewer: independent `prefix10_review` subagent.

**PASS for the isolated source-derived diagnostic view. No blocking SPEC or
correctness finding within that scope. Actual Typed+Var correspondence, parser
admission, body/caller proofs and public routing remain unsupported.** This
review read source/Git and retained control metadata, parsed ASTs and calculated
hashes using the standard library. It ran no project imports, tests, compiler,
native/formal tool, entry, SSH or control replay.

| Final reviewed addition | SHA256 | Bytes |
|---|---|---:|
| `swdb/vector_reallocation_caller_view.py` | `47c286034927b11db471c45ebce061856c4bc73008f0baf2cbdae255a2293413` | 10196 |
| `tests/test_vector_reallocation_caller_view.py` | `b2bec084f1f3f9386b3e81a39c2772473b4ee7560e439143aea99a87c002f3c1` | 5434 |

1. **The view preserves the complete closed caller.** It requires a current
   pending source-bound candidate, exact original/lowered hashes, count request,
   captured-alias observation and the existing exact three-clause contract.
   Recomputed lifetime certification fixes construction, data/alias capture,
   reserve, guarded scalar capture, reachable destructor, scalar return and
   unreachable fallthrough cleanup. Every original call/lowered event span is
   hash-checked. Independent standard-library reconstruction from the retained
   genuine lowering reproduced the exact source-event spans and full inverse;
   source SHA256 is
   `1172e62dbff5076d25471285afcfa17927707dbe6fae121d9570109d39e62b57`
   and original lowering SHA256 is
   `7082d6fc081e23547bf792f8029277695b83d933913545f290f66353ee5841ec`.
   Bytes outside the reserve replacement and explicit ABI/header insertion
   remain unchanged. Model names and all supplied formal clauses are retained.
2. **Reserve inlining adds a duty, never a premise or trusted body theorem.**
   The source model must contain exactly the complete original reserve function
   definition with its sole capacity branch and grow call. Matching just the
   familiar branch is insufficient: an added effect within the function refuses.
   The substituted arguments are the closed automatic receiver and nonvolatile
   integer count, so duplicating their side-effect-free evaluation in the branch
   and call does not strip source effects. The no-growth condition is a named
   ACSL `assert`; construction/fill, capacity, alias validity and cleanup still
   require proof. No summary/body dependency is replaced or admitted and no
   axiom, result theorem, source-local origin or caller premise is introduced.
3. **ABI coordinates are explicit and prospective.** The final version adds
   `_Alignof(int)==4`, `_Alignof(size_t)==8` and `_Alignof(void*)==8` to the existing
   width/size/structure-alignment/field-offset assertions. AST comparison shows
   that only the `LAYOUT_CHECKS` literal changed after green-v3. The metadata
   distinguishes Typed field offsets0/1/2 and extent3 from byte offsets0/8/16 and
   extent24, and int Typed stride1 from byte stride4. It does not identify raw
   addresses with integer IDs. Six prospective selected-source pins include
   MemTyped, MemVar, MemLoader, Ctypes, Cint and Factory. An injective identity
   relation, separate initialization/value relations and actual generated task
   correspondence remain pending; hash equality does not establish them.
4. **Refusal and mutation behavior remains closed for this preparation API.**
   Direct source symlinks/nonfiles refuse. Changed source/lowering/checker,
   unsupported request/observation, altered contract, event spans, reserve
   function effects and changed view/certificate refuse. Existing source and
   lifetime checkers define the accepted closed lowering; this module does not
   reparse the C++ source or authenticate arbitrary forged lowering descriptors.
   That boundary is safe for this diagnostic because `check_launch` always
   raises after rechecking, including when a bridge flag is forged. There is no
   adapter/setup dispatcher hook in these additions. No broader physical-path
   ancestry or malformed-descriptor API guarantee is inferred.
5. **Retained controls support preparation only.** Initial module-absent RED
   reports0passed/4failed. Corrected side-effect RED-v3 reports4passed/1failed,
   preserving the real pytest `Failed: DID NOT RAISE` result; green-v3 reports
   5passed/0failed. Final ABI-only green-v4 again reports5passed/0failed and no
   external/native attempts; its result SHA256 is
   `e6ec6618fb920ac5bc35f230839ab8c403d9ef1a417127af5abada6a59b94c0d`.
   Green-v4's copied module/test bytes equal the exact two reviewed hashes.
   These are bounded retained-parser controls, not fresh parser/runtime/formal
   evidence. The normal test fixture may invoke Clang when separately admitted;
   no such invocation occurred in this review. Original RED, the failed
   intermediate collector and corrected receipts remain historical evidence.

Source preparation may proceed to a separately reviewed generation-only packet.
Actual compilation/runtime collection, ordinary/RTE/init/smoke goals, selected
Typed+Var source/lifetime embedding and current model dependencies must be
admitted independently. No caller127, fullmodel or ticket closure follows.
