# Certification fingerprints for the functional BFS preparation

Updated: 2026-10-06 ET. Agent-decided under Yan-Ru’s autonomous delegation; revisable.

The existing public frozen-manifest test produced eight failures and three passes before this change. The eight stale declarations are candidate 1.3–1.6, native 1.3–1.5 and lowering calibration 1.1. All three library-operation versions already match and keep their existing declarations. Exact before/after hashes are in `09-certification-fingerprint-redeclaration.json`.

A full manifest-source comparison from the frozen baseline `000e85f` to prep base `c109994` finds two relevant changes. Commit `bb7673f` converts attribution tuples to JSON lists before persistence, as the native path already does. It runs after the same attribution computation and preserves the attributed flag, status decisions, checks, matrix, fault plan and verdict. Commit `bb11cb1` delegates the candidate-record YAML read to `access.read_record` and its exact-byte SHA-256 to `access.record_hash`. YAML still uses the same parser, cached reads return fresh data, and the source/artifact binding comparisons are unchanged. Neither refactor changes a certification procedure’s acceptance rule.

No evaluator C++, driver, strict header, legality rule, procedure definition or control-plan source changed. Their unchanged content was inspected across every family. Thus the table and test re-declare only these eight manifest digests under the documented behavior-preserving-refactor policy. No historical certification record, source pin, normative entry or library-operation digest is rewritten.

The fresh functional BFS recipe uses the current candidate default 1.6, including knob spelling and `_Pragma` controls, with both tile sizes 16384 and 1024 and four worker threads in each run. Certification remains pending parent-owned execution on mbit10; these declarations are provenance repair, not new execution evidence.
