# Selected one-thread worksharing order — 2026-10-16 ET

This source-only supplement adds no model fact or loop annotation and changes no frozen packet. It closes a design distinction for review, not an actual runtime or TD proof gate.

The exact selected TDStep uses `schedule(dynamic,1)` in its accelerated worksharing loop; the canonical C stand-in traverses increasing logical chunk indices. One-thread cardinality alone is not a portable OpenMP guarantee of monotonic dynamic chunk assignment. The [OpenMP 5.1 worksharing specification](https://www.openmp.org/spec-html/5.1/openmpsu48.html) defaults an unmodified dynamic schedule to nonmonotonic, permitting arbitrary assignment order. An OMP_SCHEDULE setting cannot override this explicit schedule clause. Thus the sequentialization rule must bind the selected runtime implementation, or prove a separate permutation-independent functional simulation. Neither a sequential printf nor the tiny team observer establishes this order.

The source-backed narrow route is the already declared compiler/runtime TCB for the pinned local Clang/libomp installation. Exact upstream llvmorg-22.1.8 primary sources are retained beside this note with raw byte pins. The installed libomp Homebrew receipt identifies22.1.8, arm64 and bottle installation. This establishes declared version provenance; source-to-bottle reproducibility is not proved here.

| Primary source | Relevant path |
|---|---|
| kmp_runtime.cpp2099–2107 | A one-thread fork enters `__kmp_serial_fork_call`. |
| kmp_runtime.cpp1709–1733,1291–1293 | The serial fork calls the serialized-parallel setup, which sets serialized and nproc=1. |
| kmp_dispatch.cpp1004,1054–1056 | Serialized dispatch uses the current private dispatch buffer. |
| kmp_dispatch.cpp2209–2300 | Serialized next returns either the complete ordered interval once, or consecutive chunks indexed by private count when nomerge is enabled. Both yield increasing logical indices for this positive-stride loop. |
| CGOpenMPRuntime.cpp2613–2658 | The compiler adds nonmonotonic by default for modern OpenMP dynamic schedules and emits the typed dispatch-init interface. |

The active multi-thread dynamic path may map to static stealing; it is not the argument used here. For the qualified one-thread serialized branch, source-level control flow supports increasing traversal despite the general standard permitting a broader schedule. Accepting this route means trusting the selected compiler/runtime implementation and normal source-to-binary correspondence, not inserting monotonicity into ACSL or changing the source schedule. The native profile establishes only installation/team behavior. A counted record must preserve the same runtime/compiler/source and fresh environment; foreign runtime families remain outside this qualification.

Source URLs:

- [runtime fork/setup](https://github.com/llvm/llvm-project/blob/llvmorg-22.1.8/openmp/runtime/src/kmp_runtime.cpp)
- [dispatch](https://github.com/llvm/llvm-project/blob/llvmorg-22.1.8/openmp/runtime/src/kmp_dispatch.cpp)
- [Clang dispatch lowering](https://github.com/llvm/llvm-project/blob/llvmorg-22.1.8/clang/lib/CodeGen/CGOpenMPRuntime.cpp)

No compiler, native observer, formal tool, prover, version/config probe or SSH command was executed for this research. Only primary source downloads, physical receipt reads and passive source analysis occurred. Private storage/lifetime/Graph/device/TD/count acceptance remains separate.
