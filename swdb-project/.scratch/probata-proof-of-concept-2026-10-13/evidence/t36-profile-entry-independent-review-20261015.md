# Ticket 36 profile entry independent review

2026-10-15 ET. **PASS for the exact collection/context gate below**, subject to root's live source/runtime/lane admission. No entry body, collection, compiler, parser, solver, SSH or evaluation was executed in this review. Only inert source/JSON inspection and Python AST parsing were performed.

| File | Reviewed SHA-256 |
|---|---|
| `/private/tmp/probata-t36-profile-entry-20261015.py` | `09717006a0d1e078532cf9c68a64d05efb3a50cb50bbf71882df6b7d3a72df93` |
| `/private/tmp/probata-t36-setup-cwd-v3-command-20261015.json` | `97956996cd0d3b458f1e866f307721c5bad2ed98bfa7907d3c65fb46b50579b7` |
| `/private/tmp/probata-t36-facts-cwd-v3-command-20261015.json` | `b7a78461a76485a6d5b6c6377188b4f1db50fba8637f3e3d0f9b65e3811f6e96` |
| `/private/tmp/probata-t36-production-cwd-v3-command-20261015.json` | `362a3cd633aac0d50c7eac9402739e99e70fb34d84c1a4b162e0306d928ca2a2` |

All three JSON command arrays embed the exact entry source. Their `python -c` argv binds project, external output, expected selected count and original executable/pytest arguments at the correct positions. Every selected node is an absolute `{SOURCE}/swdb-project/tests/...` path. Expected counts are128 setup,13 facts and5 production; they are prospective expectations until the admitted collection runs.

The entry changes into project cwd before collection and fingerprinting. Its hook observes `len(session.items)` after ordinary selection/deselection, and rejects a nonzero collection result or any count mismatch before tests. Collection stdout/stderr go to a newly created external `collection.log`; `collection.json` records cwd, expected/selected count and exit. Final JUnit output is omitted from collect-only argv, preserving the subsequent real test result. The two JSON writers append actual newline characters, not literal backslash-n text.

Collection may itself discover real Frama-C versions; it is inside the same explicitly admitted lane and RSS/time guards, not mislabeled pure or run outside a lease. `project-runtime-provenance.json` records the exact project-cwd lowering/runtime context separately from the inherited monorepo-cwd bootstrap snapshot. The final `execv` preserves the selected interpreter, cwd, environment, guard process ancestry and full test argv. Variant fake/optional-parser fixtures retain their own exact context rather than pretending to equal the normal project snapshot.

External cache, temporary directory, JUnit and raw paths remain under the root-selected output folder. Root must still confirm actual non-skipped case results, source-after integrity, runtime/method/checker closure, resources and natural lease release. Passing collection is dispatch evidence, not proof acceptance. Earlier command versions and initial no-test raw folders remain immutable.
