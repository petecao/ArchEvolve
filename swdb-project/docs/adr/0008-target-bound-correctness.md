# What counts as correct

Date: 2026-10-03 ET
Updated: 2026-10-05 ET (scope line)
Status: proposed

Narrows ADR 0001 and the implementation meaning in ADR 0004; retains ADR 0005 target-bound check bindings.

Code becomes an implementation when the kernel correctness check passes on the hardware target it is written for. A completion witness is part of that check. Preservation obligations belong to rewrite contracts; execution witnesses show path coverage. Functional-model certification is simulated pre-check evidence, never target correctness or performance. Formal halves are parse-checked predicates or resolved reference-semantics pins; their label remains stated until a formal verifier is integrated.

## Scope and authority

Implementation follows the authorized tickets of the [typed-library map](../../.scratch/typed-library-dx100-bfs-2026-10-03/map.md): 01–37 at first, then 38–78 (updated 2026-10-05 ET; the map lists each ticket and its decision). This proposed record does not assert Yan-Ru accepted the ADR or sent the team note. Human review and communication receipts remain separate.
