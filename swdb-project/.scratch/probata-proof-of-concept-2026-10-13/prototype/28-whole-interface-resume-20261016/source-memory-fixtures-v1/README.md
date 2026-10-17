# Three original-API same-thread rule fixtures

2026-10-16 ET. This is a new synthetic source set, not an extension or relabeling of the fixed79/80 source or accepted abstract25 traces. No compiler, native program, verifier or public proof has run for it.

One source file contains three independent no-argument scalar caller roots. A future single complete original TU can bind all three with the same compiler parse and header declaration identities. There are no new source globals, helper functions, atomics, second-thread claims or readiness queries.

| Caller | Expected actual result | Required public verdict | Distinguishing rule |
| --- | --- | --- | --- |
| `whole_same_thread_read_during_store` | 7 | refuted | `store-footprint-cpu-access` |
| `whole_same_thread_write_during_gather` | 9 | refuted | `same-thread-read-footprint-write` |
| `whole_same_thread_read_during_gather` | 7 | proven | unfinished read/read overlap is allowed |

Each fixture registers one ordinary uint32 array. The store writes the same value already held, and the write/gather fixture's result9 agrees with ordinary value execution. Their negative properties therefore do not invent a deliberately wrong result: the required refutation is the exact CPU/unfinished-command hazard. A later covering wait cannot protect an earlier conflicting CPU access. The positive read/read fixture completes the gather before its source array leaves scope, so a lifetime check is not mistaken for the overlap rule.

The array contains16 uint32 elements, initialized by the original explicit `{7, 11}` aggregate list with its ordinary zero tail. The separately owned physical/object mapping must place this64-byte allocation on a64-byte physical boundary. That alignment is a proposed context requirement, not a fact inferred from a source declaration whose natural alignment is4 bytes. No context/runtime/mapping receipt is generated or granted by this packet. The future producer must derive real declaration IDs, source/ABI/allocation/lifetime/CPU certificates and bind the separately admitted owner receipts. The region covers the complete array; commands access one logical element. Existing store-line physical hazards remain active.

`source_memory_profiles_v1.prepare(original_project, source_path)` only emits exact pinned compiler requests, anticipated source ranges, predicted contracts/rules and a mapping request. Its tiny lexical function-range grammar is closed by the exact whole-file hash and is never an AST/source certificate. The original physical project/header paths remain explicit. `prospective-local-request-v1.json` records local preparation only, with every compiler/source/context grant false; remote preparation must bind the actual selected original project again. The selected function/mangled name, entire source file, two exact headers and full27-declaration inventory must all match a future complete original TU. There is no filtered dump or cross-parse declaration-ID join.

Integration remains explicit. A new exact source-policy profile must select these three names and this one file hash while preserving the old first profile and its mutation controls. Its C++ counterpart may project every included body, or use a separately reviewed AST-selected function-root extraction with complete dependency/source closure; leaving two raw-pointer bodies beside the replacement API wrappers is insufficient. Native/source-model/draw/runtime/owner identity, no-skips collection, exact new0.2 hash/assumption records, actual CBMC reachability and exact source-preserving C++ replay of both hazard properties are mandatory. Frontend refusal, capacity/unwind failure, another failed property, or mere source preparation does not satisfy the predicted verdicts. Only root admits actual jobs.

Three no-child preparation controls pass. They check one shared exact source, precise issue/CPU-access/wait order, unchanged negative result semantics, false observation/context grants, physical mutation/alias refusal and the explicit owned alignment request. These controls do not compile C++ or prove a memory rule.
