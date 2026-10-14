# 24 — C++ subset widening

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes)
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 21
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Formal-half language and the C++ subset": the subset by construct and kept names; "Verifier lineup and order": failure classes; "Records and levels": method-version file contents; "Testing Decisions", seam 1; choice S1); decisions: [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) items 3, 9; [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) item 2; [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) items 3, 6
**Time estimate:** about 4 days

**What to build:** The C lowering tool grows from 21's core (functions, arrays, loops) to the declared C++ subset, construct by construct, so GAPBS-style candidate artifacts can reach WP. Accepted: C plus references; classes without inheritance or virtual functions; member functions and operators; constructors and destructors as explicit calls; instantiated templates; `new[]` and `delete[]`; `enum class`, `constexpr`, `static_assert`; `std::min`, `std::max`, `std::copy`, `std::swap` through C models proven once; the OpenMP constructs (`parallel`, `for` with static, dynamic and `nowait`, `critical`, `atomic`, `barrier`, `reduction`); `__sync_*` and `__atomic_*`; `__dxc_*` and `maa_*` calls through summaries. The C lowering keeps C++ names: a class becomes a struct with the same name and fields, references become pointers, operators become named functions. So formal halves type-check unchanged. Anything outside the subset gives failure class "unsupported construct", never a crash or a partial C lowering. The naming rules are versioned and belong to the content-hash set.

## Acceptance

- [ ] One fixture per construct group lowers deterministically (twice, identical C and anchors). Its ACSL type-checks over the kept names. `swdb prove` with the real WP adapter proves the safe version, and a seeded bug reads not proven.
- [ ] Kept names: a class fixture's formal half, written over the class's field names, type-checks against the C lowering with no renaming. A reference parameter becomes a pointer; an operator and a member function become named functions under the naming rules; constructors and destructors appear as explicit calls.
- [ ] Templates: a template instantiated at two types lowers to two C functions, named by the naming rules. `enum class` lowers to `int`.
- [ ] `new[]` and `delete[]`: a fixture that indexes out of range, or reads after `delete[]`, reads not proven; the in-range fixture proves.
- [ ] Each of `std::min`, `std::max`, `std::copy`, `std::swap` lowers to a call of its C model. Each model's ACSL contract is proven once (one proof record each, subject: a library entry's summary). A unit that uses a model pins that record.
- [ ] An OpenMP fixture (`parallel for` with a `reduction`, a `critical` section, an `atomic`, a `barrier`) and an atomics fixture (`__sync_*`, `__atomic_*`) lower and prove at threads = 1.
- [ ] A fixture with a `__dxc_*` call and one with a `maa_*` call keep each as a call whose contract comes from a fixture summary. The record lists the summary used.
- [ ] Unsupported constructs: inheritance, a virtual function, an exception, a lambda, RTTI, another standard container (such as `std::map`) and a stream each read not proven, "unsupported construct", naming the construct and its source location.
- [ ] Naming rules carry a version. Every proof record pins it in its content-hash set, and bumping the version gives a different pin.
- [ ] Each diagnosed failure joins 21's regression corpus. Fixtures use no BC, PR or SSSP code. Tests that need Frama-C or LLVM 22 skip cleanly.

## Notes

- **Not in this ticket:**
  - 25 — std::vector and std::pair models: `std::vector<T>`, `std::pair`, and the "allocation succeeds" entry (which then covers `new[]` too).
  - 45 — Per-thread lowering: the program for one symbolic thread of N, sharing classes, uniform control, and the memory-model meaning of atomics for symbolic N (history reads, a CAS as a sequentially consistent read-modify-write).
  - 44 — Shared-action kinds and commutativity lemmas: the closed list of kinds and their lemmas.
  - 46 — CIVL adapter: the history-read encoding CIVL needs. 47 — GenMC adapter and agreement: the pthreads harness GenMC runs.
  - 27 — Proof semantics for the BFS read-offload calls; 28 — Proof semantics for the remaining maa_* calls: the contracts behind `maa_*` calls and the hazard check at each tile-pointer read.
  - 30 — Reference definitions, per-call summaries and new intrinsic versions: the real per-call summaries for `__dxc_*`.
  - 22 — SAW adapter and SAWScript translator: the C++-versus-C-lowering agreement check.
  - 11 — Method-version file and failure classes: the method-version file that lists the subset and naming rules.
  - 16 — Post-campaign WP phase and budgets: the loop's skip reason "outside the C++ subset" (a candidate artifact outside it reaches at most proven within bounds).
- Assumption (not decided in the map): OpenMP constructs and atomics get their single-thread meaning here (a parallel region runs as one thread; a CAS is a read, a compare and a write). Their meaning for symbolic N comes with 45 — Per-thread lowering (history reads; a CAS as a sequentially consistent read-modify-write), not 44. CIVL's history-read encoding is delivered with 46 — CIVL adapter, and GenMC's pthreads harness with 47 — GenMC adapter and agreement.
- Assumption (not decided in the map): 24 does not wait for 22, so until 22's agreement check runs on these fixtures, nothing checks that each construct's C lowering is faithful. WP proves the C lowering, not the C++. Once 22 lands, the agreement check should run on every fixture here; a disagreement reopens this ticket.
- Assumption (not decided in the map): a `__dxc_*` or `maa_*` call with no summary available reads "unsupported construct" until 27, 28 and 30 supply summaries.
- Measuring subset coverage on Extensa-campaign candidate artifacts (13 item 2) is not part of this ticket.
- Why `std::copy` and `std::swap`: GAPBS's `QueueBuffer` and `pvector` use them (13 item 2).
- Held-out kernels (BC, PR, SSSP) are never used before the freeze (59 — Method-version review and freeze).
- Mac: one real verifier job at a time through 21's lock, under the ~8 GB RSS watchdog; keep at least 50 GB free. If the C lowering tool uses LLVM 22, the analytic evaluator must keep working.
- WP runs fail inside the Bash sandbox (the Why3 socket is blocked); run WP jobs outside it.
