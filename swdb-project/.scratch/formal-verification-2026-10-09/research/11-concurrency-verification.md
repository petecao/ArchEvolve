# Research 11b: Proving the OpenMP BFS step for every thread count

Created: 2026-10-13 00:01 ET
**Ticket:** [11](../issues/11-verifier-choice.md) · **Map:** [../map.md](../map.md) ·
**Companion:** [11-verifier-facts.md](11-verifier-facts.md) (single-thread tool facts; VerCors in its §E)
**Method:** primary sources only: CIVL v1.23.0 source and docs read at the release tag through the
GitHub API, tool READMEs, papers and abstracts, and the DX100 code at ArchEvolve `df077002`. Every
paper citation was checked on Crossref (2026-10-12/13) or, where Crossref has no record, through the
publisher or the doi.org resolver. Nothing was installed, upgraded or run. Scratch files lived in the
session scratchpad and are not kept. "Our reading" marks an inference. "Unconfirmed" marks what could
not be checked.

---

## TL;DR

1. **No tool reads this C++/OpenMP code and proves it for every thread count.** Every family that
   gives thread-count-parametric proofs (reduction, separation logic, rely-guarantee) needs a model
   or a lowering of the OpenMP region first (§1).
2. **Best fit: reduction.** Threads share state at only four points: the `critical` DX100 claim,
   the fallback CAS, the queue fetch-and-add, and one barrier (§0). Everything else is thread-owned
   or read-only. Lipton reduction turns the region into a sequential program indexed by a symbolic
   thread count N. WP can then prove it for all N, reusing the ACSL summaries.
3. **Cross-check: permission-based separation logic in VerCors.** It has `par` blocks over a
   symbolic thread range, barrier contracts, and atomic invariants. But atomics are PVL-only, and
   2.4.0 rejects `omp parallel` blocks, so this needs a hand-written PVL model. The strongest prior
   proofs of CAS-based graph kernels are all separation-logic proofs (§4). We found no mechanized
   proof of a parallel BFS (search-bounded).
4. **Bounded refuter: CIVL 1.23.** It reads C+OpenMP (`parallel`, `for`, `critical`, `barrier`,
   `atomic` read/write/update/capture). It tries every team size from 1 to `omp_thread_max` and
   replays counterexamples.
   - It does not read C++, and the Mac has no JDK 17+.
   - The source's loop-split default is `ROUND_ROBIN`, but the docs say `ALL`, so pass
     `-ompLoopDecomp=ALL`.
   - There is no `atomic compare`, so the CAS must be lowered by hand (§5).
5. **Code finding: the tile path is correct only when team size = `NUM_CORES`.** The value is fixed
   at compile time (`-DNUM_CORES=4`). With fewer threads, frontier chunks are skipped. With more,
   `tiles0[tid]` is indexed out of bounds (`bfs.cc:63-64,79,142-143,195`; our reading, not run).
   So "every thread count" means "every N, built with `NUM_CORES`=N and run with N threads".
6. **Code finding: the fallback path has a data race by the OpenMP rules.** Plain reads and writes
   of `parent[v]` are unordered with other threads' CAS (`bfs.cc:205-210`). OpenMP 5.2 §1.4.1 says
   that makes the result unspecified. Any proof must list "plain `parent` accesses act as relaxed
   atomics" in the assumption set, or the lowering must make them atomic.
7. **Accelerator angle: we found no prior work on several CPU threads driving one shared offload
   engine through their own tiles** (search-bounded). The closest are asyncStar, SCRATCH, the BRiCk
   DMA driver, OMPSan/Arbalest and MC-Checker (§3). New proof obligation: the DX100 store issued
   inside `critical` must be complete and visible to the next thread before the lock is released.
8. **OpenMP race checkers don't fit this code.**
   - LLOV has no `critical`, `atomic` or `barrier` support, and indirect accesses like `a[b[i]]`
     fall outside its model.
   - On DataRaceBench 1.4.0, the best file-level F1 is 0.911 (Coderrect). At line level it drops
     to 0.752 (ThreadSanitizer).
   - Archer/TSan sees only the schedules that actually run, so use it only as a cheap smoke test.

## Ranked recommendation

### A. Method family for proofs that hold for every thread count

1. **Reduction to a thread-indexed sequential program, proved with WP (unbounded).**
   - **Why it fits:** shared-state contact is four small atomic steps (§0). Thread-local and
     read-only steps commute with everything (Lipton both-movers), so every run is equivalent to one
     where whole critical sections and CASes run one at a time, in some order.
   - **What WP proves:** the resulting sequential program (a loop that picks a thread and runs its
     next block) for symbolic N, V and E. It reuses ticket 11's C lowering and ACSL summaries.
   - **Prior art:**
     - Lipton 1975; Flanagan & Qadeer 2003.
     - Civl (Boogie) mechanizes movers and reduction for N threads.
     - Conc2Seq did this for Frama-C, with the thread count as a parameter, but it is archived and
       incompatible with recent Frama-C.
   - **Side obligations (each its own proof or assumption-set entry, ticket 09 item 8):**
     - (a) ownership: tiles, registers and queue buffers per thread; disjoint frontier chunks;
       disjoint queue ranges after fetch-and-add;
     - (b) every thread reaches the barrier and `omp for` the same number of times (uniform control
       flow);
     - (c) the DX100 store is complete before the `critical` exit;
     - (d) the memory-model treatment of the racy `parent` accesses (TL;DR 6).

     The reduction lemma itself is a written proof unless it is mechanized, for example by a Civl
     model.
2. **Permission-based separation logic in VerCors (PVL model): independent cross-check or
   fallback.**
   - **Mapping:** `par (tid = 0 .. N)` for the region, `atomic(inv)` for `critical` and the CAS,
     a barrier contract, ghost sets for the next frontier.
   - **Pro:** it proves race freedom and the unit relation directly for symbolic N.
   - **Cons:**
     - The model is hand-written, so the translation is a trust gap.
     - It adds a third summary format, which works against Q4's "one summary source".
     - Prior art on CAS graph kernels is strong here (§4).
3. **Rely-guarantee / Owicki-Gries on a model** (Civl yield invariants, Armada, Isabelle
   `Hoare_Parallel`). The monotone `parent` protocol fits rely-guarantee naturally: other threads
   only turn a negative entry into a valid frontier neighbor. None of these tools reads C or C++.
4. **Foundational separation logic (Iris/Rocq: BRiCk for C++, VST for C):** the strongest
   guarantees and a real C++ front end (BRiCk), but a manual proof per kernel. Long-term only.
   - **Not recommended:** two-thread abstraction (it covers only race freedom, and its tools are
     GPU-only) and parameterized model checking (abstract models only; undecidable in general).

### B. Bounded concurrency refuter

1. **CIVL 1.23 on the same C lowering, with the pragmas kept.**
   - **Run it with:** `-input_omp_thread_max=k -ompLoopDecomp=ALL`, plus DX100 stubs in C.
   - **CAS:** lower it to a CIVL `$atomic` block under `#ifdef _CIVL` (our reading, untested).
   - **Covers:** every team size 1..k, `critical`, `barrier`, `omp for` and race checks, with
     replayable traces.
   - **Needs:** a JDK 17+ install (approval needed) and a z3 or cvc5 on `PATH` (both present).
2. **GenMC on a pthreads rewrite of the region.** It reads C/C++ through LLVM 19-22 and checks
   weak-memory effects, so it is the tool that would catch TL;DR 6 in practice. It has no OpenMP,
   and it is built from source.
3. **Dartagnan** (C to LLVM IR; Java 17+): weak-memory BMC, also on a pthreads rewrite.
   - **Smoke test, not a verifier:** Archer (TSan + OMPT) on real runs.
   - **Not recommended:** ESBMC (it timed out single-threaded, ticket 08), LLOV (§2).

**Decisions this hands to the grilling:**
- (i) Restate the thread bound as "N = `NUM_CORES` = team size", or require the rewrite to drop
  the coupling?
- (ii) Should reduction lemma (c) "DX100 store complete before the lock release" go into ticket 12's
  semantics?
- (iii) Assumption-set entry for the racy `parent` accesses, or require atomic accesses in the
  lowering?
- (iv) Is a hand PVL model acceptable as a cross-check, given Q4's one-summary-source rule?

---

## 0. What the code asks of a verifier

The DX100 top-down step `TDStepMAA` (`apps/dx100/benchmarks/gapbs/src/bfs.cc:66-225`), called from
`DOBFSMAA` (`:419-422`):

| Object | Who touches it, and how | Lines |
|---|---|---|
| `tiles*`, `regs*` arrays (size `NUM_CORES`) | Written once per thread in the setup region under `omp critical`, then read by `tid` | `:63-64`, `:377-398`, `:79-92` |
| DX100 tiles and registers | Thread-owned after setup (strict-layer assert; [research 05](05-accelerator-interface-verification.md) lemma item 4, `:278-279`) | `:94-98`, `:144-179` |
| Frontier window `queue.shared[out_start, out_end)` | Read-only; thread `tid` reads chunk `[idx + tid*ts, +ts)` | `:99-101`, `:142-147`, `:163`, `:202` |
| Graph arrays | Read-only | `:149-151`, `:161`, `:203-204` |
| `parent` (tile path) | DX100 load, compare, conditional indirect store, `wait_ready(tile3)`, all inside `omp critical` | `:170-187` |
| `parent` (fallback path) | Plain read, `__sync_bool_compare_and_swap`, then a plain write of the same value | `:205-210`; `platform_atomics.h:30-31` |
| Queue tail `shared_in` | `fetch_and_add` reserves a range, then `std::copy` into it | `sliding_queue.h:114-118` |
| Control | `idx` and `len` come from the shared queue, so every thread computes the same `tile_size` sequence and reaches `barrier` and `omp for` the same number of times (our reading) | `:99-139`, `:197`, `:200` |

**Thread-count coupling (our reading, not run):**
- The tile path assumes team size = `NUM_CORES`:
  - the tile arrays are sized by it (`:63-64`);
  - the guard `current_len_size > NUM_CORES * tile_size` (`:104-135`) and the stride
    `idx += NUM_CORES * tile_size` (`:195`) both use it.
- **With T < `NUM_CORES` threads,** chunks `tid = T..NUM_CORES-1` are skipped, and their vertices
  are never expanded.
- **With T > `NUM_CORES` threads,** `tiles0[tid]` is out of bounds (`:79`, `:382`).
- **The build and the run:** the build fixes `-DNUM_CORES=4` (`apps/dx100/benchmarks/gapbs/Makefile:58`;
  `records/candidates/bfs-author-maa-compile-20260925-a1.candidate.yaml:709`). The run names
  `OMP_NUM_THREADS` (`:715`); its value was not checked (unconfirmed).

**Memory-model status (our reading):** in the fallback path, the plain read `parent[v]` (`:205`)
and the plain write `parent[v] = u` (`:210`) are unordered with other threads' CAS. OpenMP 5.2
§1.4.1:
- a read and a write to the same memory unit without synchronization form a data race "if the read
  and write are unordered";
- "If a data race occurs then the result of the program is unspecified."

The upstream-style `TDStep` has the same pair (`:243-248`). `TDStep2` has only the racy read
(`:270-272`).

**Accelerator obligation:**
- The `critical` section protects `parent` only if the DX100 store issued inside it is complete,
  and visible to the next thread's DX100 load, before the lock is released.
- On gem5, `wait_ready(tile3)` returns only after that store finished
  ([research 14](14-dx100-wait-rule.md) `:152-153`).
- Visibility to other cores, and the missing `"memory"` clobber on `wait_ready`'s `mfence`
  (research 14 `:170-173`), are not covered (our reading).

---

## 1. Method families for arbitrary thread counts

| Family | Strongest prior work | Proof for every thread count? | Reads C / C++ / OpenMP? | Maturity | Counterexamples? |
|---|---|---|---|---|---|
| (a) Reduction / atomicity | Lipton 1975; Flanagan & Qadeer 2003 (atomicity types); QED (Elmas et al. 2009); **Civl** (Hawblitzel et al. 2015; Kragl & Qadeer 2018, 2021; Kragl et al. 2020 ×2); Anchor (Flanagan & Freund 2020); Armada (Lorch et al. 2020); Gangamreddypalli et al. 2026 | Yes (Civl: linear thread ids, barrier example over N threads) | Civl: Boogie only; Anchor: own language (unconfirmed which); Armada: "C-like" language. None reads C, C++ or OpenMP | Civl active (Boogie pushed 2026-10-12); Anchor, Armada research prototypes | Boogie reports failed obligations, not interleavings (our reading) |
| (b) Two-thread abstraction / symmetry | **GPUVerify** (Betts et al. 2012, 2015); PUG (Li & Gopalakrishnan 2010); GKLEE (Li et al. 2012); barrier invariants (Chong et al. 2013); atomics (Bardsley & Donaldson 2014); Faial (Cogumbreiro et al. 2021); thread-modular model checking (Flanagan & Qadeer 2003); dynamic cutoffs (Kaiser et al. 2010) | Yes, for race freedom and barrier divergence ("reduction to an arbitrary pair of threads") | OpenCL/CUDA kernels only. **No OpenMP analog found** | GPUVerify mature but GPU-only | GPUVerify: yes, a race between two threads (our reading) |
| (c) Permission-based separation logic | **VerCors** (Blom et al. 2015, 2017; Darabi et al. 2017; Amighi et al. 2014); VeriFast (Jacobs et al. 2011); Viper (Müller et al. 2016); Iris (Jung et al. 2018); FCSL (Sergey et al. 2015); RefinedC (Sammler et al. 2021); BRiCk (C++); VCC (Cohen et al. 2009) | Yes (VerCors `par` over symbolic `size`; Iris/FCSL fork and recursion) | VerCors: C subset and basic C++, OpenMP `parallel for` only; VeriFast: multithreaded C; BRiCk: C++ through Clang; VST: C; VCC: C | VerCors 2.4.0 (2026-04); VeriFast active; BRiCk active (SkyLabsAI); VCC archived | No traces; failed assertions only (our reading) |
| (d) Rely-guarantee / Owicki-Gries | Owicki & Gries 1976; Jones 1983; Isabelle `Hoare_Parallel` (Nipkow & Nieto 1999; Nieto 2003); COMPLX (Amani et al. 2017); Civl yield invariants ("a compositional extension of Owicki-Gries") | Yes: `Hoare_Parallel` verifies a collector "parameterized in the number of mutators" | Toy or own languages; none reads C/C++/OpenMP | Isabelle library maintained; COMPLX research | No |
| (e) Parameterized model checking | Apt & Kozen 1986 (undecidable in general); Bloem et al. 2015 (survey); Cubicle (Conchon et al. 2012); MCMT (Ghilardi & Ranise 2010); proof spaces (Farzan et al. 2015); view abstraction (Abdulla et al. 2016); thread modularity (Hoenicke et al. 2017) | Yes, for the abstract model | Transition systems, not C | Cubicle and MCMT stable research tools | Yes, abstract traces (our reading) |
| (f) Bounded interleaving model checking | **CIVL** (Siegel et al. 2015); ESBMC (Cordeiro & Fischer 2011); CBMC (Alglave et al. 2013); Dartagnan (Gavrilenko et al. 2019); GenMC (Kokologiannakis & Vafeiadis 2021); Lazy-CSeq (Inverso et al. 2014); Deagle (He et al. 2021) | **No:** a fixed thread count, or all counts up to k (CIVL) | CIVL: C + OpenMP/MPI/CUDA, no C++; ESBMC: C/C++ + pthreads; GenMC: C/C++ through LLVM; Dartagnan: C through LLVM IR; Lazy-CSeq: C + pthreads | CIVL 1.23.0 (2026-05-26); Dartagnan 4.4.1 (2026-05-22); GenMC LLVM 19-22 | **Yes** (CIVL `replay`; BMC traces) |

**Per-family notes (with sources):**

- **(a) Reduction.**
  - **Civl:** "built on top of Boogie" and adds `async`, `par` and `yield`. It uses linear thread-id
    permissions, and one documented invariant says the barrier count equals "N, the total number of
    threads" (Kragl & Qadeer 2021, §III). Its garbage-collector case study "supports more than one
    mutator" (§V).
  - **Gangamreddypalli, Enea & Qadeer** (arXiv 2601.13341, listed as accepted to ESOP 2026) add
    reduction for atomic sections that contain calls, and soundly replace parallel composition with
    sequential composition. Implemented in Civl.
  - **Conc2Seq** turns concurrent C into a sequential simulation:
    - local variables become arrays indexed by thread id;
    - "the number of threads remains constant, given by a specific parameter of each execution"
      (Blanchard et al., arXiv 1708.07226).
    - It assumes sequential consistency, "which must be verified independently".
    - Status (frama-c.com plug-in page): "Archived: no maintenance or support, incompatible with
      recent Frama-C versions."
  - **Blelloch et al. 2012, Theorem 1 (proof sketch):** if all logically parallel operations
    "commute and are linearizable", then P is internally deterministic.
- **(b) Two-thread abstraction.** Race freedom and barrier divergence "are pairwise properties,
  allowing a reduction to an arbitrary pair of threads", sound with the adversarial or equality
  abstraction (Betts et al. 2015, §1). For our code, this covers only obligation (a). We found no
  OpenMP tool built on it (searched 2026-10-12).
- **(c) Separation logic.**
  - **VerCors 2.4.0** (companion §E): it parses many OpenMP pragmas but rejects
    `#pragma omp parallel { … }` and verifies single `parallel for` loops through iteration
    contracts.
  - **PVL features** (VerCors wiki):
    - `par threads (int tid = 0 .. size)` with per-thread contracts and barrier contracts (wiki
      "Parallel Blocks"; note its warning that one barrier syntax is not checked);
    - `invariant name(…) { … }` with `atomic(name) { … }`, "only … in PVL" (wiki "Atomics and Locks").
  - **Darabi et al.'s PPL** encodes deterministic OpenMP: `omp for` with `schedule(static)` and
    `nowait`, `sections`, `parallel for`, simd, reductions (Huisman, LOPSTR 2017 slides). Our
    `critical`, CAS and `schedule(dynamic)` are outside that deterministic fragment (our reading).
  - **Others:** BRiCk's code generator reads C++ through Clang (LLVM ≥ 16; README). VST has gained
    Iris features for fine-grained concurrency in C (Mansky, arXiv 2207.06574).
- **(d) Rely-guarantee / Owicki-Gries:** the Isabelle `Hoare_Parallel` documentation lists "two
  garbage-collection algorithms, the second one parameterized in the number of mutators"
  (`src/HOL/Hoare_Parallel/document/root.tex`).
- **(e) Parameterized model checking:** Apt & Kozen 1986 show the general problem is undecidable,
  so tools work on restricted models (array-based systems in Cubicle and MCMT). Our reading: useful
  only for an abstract "claim protocol" model of `parent`, not for the C code.
- **(f) Bounded model checking:** Dartagnan takes "LLVM programs (.ll) generated from C code" and
  answers `UNKNOWN` when loops are not fully unrolled (README). GenMC is "a stateless model checker
  for C/C++ and Rust programs that works on the level of LLVM" (README). Neither README mentions
  OpenMP.

---

## 2. OpenMP-specific verifiers and race detectors

| Tool | Kind | `critical` | `barrier` | `omp for schedule(dynamic)` | Atomics / CAS | Evidence |
|---|---|---|---|---|---|---|
| **LLOV** (Bora et al. 2020) | Static, polyhedral; proves race freedom on affine code only | ✗ | ✗ (false positives with barriers and locks) | `for` ✓; schedule type collected, effect not described | ✗ | Table 1 §4.1.2, §4.4: no "constructs for synchronization, device offloading, and tasking"; "irregular accesses (like a[b[i]]) fall outside the purview"; `nowait` can give false negatives |
| LLOV-MHP (Bora et al. 2021) | Static, phase-interval MHP | not stated | ✓ ("presence or absence of explicit barriers") | not stated | not stated | arXiv 2111.04259 abstract |
| **ompVerify** (Basupalli et al. 2011) | Static, polyhedral | ✗ (our reading) | ✗ (our reading) | affine `parallel for` loops only | ✗ (our reading) | HAL hal-00752626 abstract (via search snippet): "OpenMP parallel loop programs", affine control loops |
| Chatarasi et al. 2016 ("PolyOMP": name unconfirmed) | Static, extended polyhedral model for SPMD | unconfirmed | SPMD regions (from the title); details unconfirmed | unconfirmed | unconfirmed | LCPC 2016 title only |
| Ye et al. 2018 | Static, polyhedral | – | – | affine loop nests | – | "can classify 40%" of DRB 1.2.0 (SC18 workshop page, via search snippet) |
| **OMPRacer / Coderrect** (Swain et al. 2020) | Static, Clang/LLVM | ✓ (our reading: happens-before graph) | ✓ (our reading) | unconfirmed | unconfirmed | DRB 1.4.0 C/C++: F1 0.911 file level, 0.712 line level |
| Saillard et al. 2014 | Static barrier/worksharing matching | – | ✓ | ✓ (matching) | – | IWOMP 2014 title: "Static Validation of Barriers and Worksharing Constructs" (relevant to obligation (b)) |
| **Archer** (Atzeni et al. 2016) | Dynamic, TSan + OMPT | ✓ (`mutex_acquired/released`) | ✓ (`sync_region` barrier kinds) | only the executed schedule | TSan treats `__sync` as atomic (our reading) | `openmp/tools/archer/ompt-tsan.cpp:710-716,1192-1204` (LLVM main); README: "automatically loaded" with `-fsanitize=thread` |
| ThreadSanitizer (Serebryany & Iskhodzhanov 2009) | Dynamic | ✓ (with Archer) | ✓ (with Archer) | executed only | ✓ | DRB 1.4.0 C/C++: F1 0.873 file level, **0.752** line level (best) |
| Intel Inspector | Dynamic | ✓ | ✓ | executed only | ✓ | DRB 1.4.0: F1 0.873 / 0.744 |
| ROMP (Gu & Mellor-Crummey 2018) | Dynamic | ✓ (our reading) | ✓ (our reading) | executed only | – | DRB 1.4.0: F1 0.810 / 0.508 |
| SWORD (Atzeni et al. 2018) | Dynamic, bounded memory | – | – | – | – | IPDPS 2018 title |
| Ma et al. 2013 | Symbolic (SMT) analysis of OpenMP | unconfirmed | unconfirmed | unconfirmed | unconfirmed | ICPP 2013 title only |
| **CIVL 1.23** | Bounded model checking | ✓ (named and unnamed) | ✓ | parsed; loop split set by `-ompLoopDecomp`, not by `schedule` (our reading) | `atomic` read/write/update/capture; **no `compare`** | §5 |
| Deductive: VerCors, Darabi et al. PPL | Separation logic | ✗ in OpenMP mode | ✗ in OpenMP mode | `schedule(static)` only (PPL) | ✗ in OpenMP mode | companion §E; LOPSTR 2017 slides |
| Du, Sharma, Li & Mansky 2026 | CompCert-based semantics of C + OpenMP | unconfirmed | unconfirmed | unconfirmed | unconfirmed | arXiv 2605.26527: "any successful execution is guaranteed to be free of data races". A semantics, not yet a verifier (our reading) |

**DataRaceBench 1.4.0** (Lin & Liao 2021, Tables III, V and VI; DRB v1.4.1 released 2023-08-23):
- tools tested: Intel Inspector, ROMP and TSan (dynamic); Coderrect and LLOV (static);
- C/C++ adjusted F1 at file level: 0.873, 0.810, 0.873, **0.911**, 0.748;
- at line level: 0.744, 0.508, **0.752**, 0.712, 0.367.

CIVL ships DRB 1.3.2 as a test suite (`examples/omp/dataracebench-1.3.2`, `OmpDataracebenchTest.java`).
We found no published CIVL score on DRB.

---

## 3. Offload from several threads to an accelerator or DMA engine

| Work | Setting | What it proves or finds | Fit to DX100 |
|---|---|---|---|
| **asyncStar** (Botinčan et al. 2011) | Cell multicore DMA; separation logic | A thread "loses these permissions until it issues a corresponding synchronisation operation" ([research 05](05-accelerator-interface-verification.md) `:203-207`) | Closest in spirit: per-thread ownership of in-flight transfers |
| **SCRATCH** (Donaldson et al. 2010; FMSD 2011, vol. 39, pp. 83-113) | One SPE's DMA `get`/`put` + `wait(tag)`; CBMC + k-induction | Overlap of pending DMAs; unbounded over loops (research 05 `:193-202`) | Single-thread analog of our tile hazards |
| BRiCk ZynqMP DMA driver (Stewart & Malecha 2025, talk) | C++ driver in Iris; device modeled as a thread | Driver and device "run concurrently. Treat each as a thread" (research 05 `:223-227`) | Device-as-thread model for C++ |
| AccelSync (An et al. 2026, preprint) | AI-accelerator units sharing on-chip buffers | Decidable "barrier sufficiency" across units (research 05 `:208-215`) | Cross-unit, not cross-CPU-thread |
| OMPSan (Barua et al. 2019) | OpenMP `target` data mapping, static | IWOMP 2019 title | Host/device copy consistency |
| Arbalest (Yu et al. 2021) | OpenMP offload mapping, dynamic | IPDPS 2021 title | Same |
| MC-Checker (Chen et al. 2014) | MPI one-sided (asynchronous put/get with epochs) | Memory consistency errors, dynamic | Async remote writes, completion rules |
| HGRD (Nayak et al. 2026, preprint) | Host + GPU code analyzed together | Fewer false race alarms; no soundness claim stated | Host code fixes kernel parameters |

**Gap (search-bounded, 2026-10-12):** we found nothing that verifies several CPU threads, each with
its own command tiles on one shared engine, writing a shared array under a CPU lock.

The DX100 case splits into (our reading):
- per-thread tile ownership: separation, as in asyncStar;
- a shared target (`parent`) whose lock protects it only once the engine's write has completed: the
  accelerator version of "release after the write is visible";
- cross-thread command ordering inside the engine, which the strict layer leaves unspecified
  (research 05 lemma item 1 covers only one thread's program order).

---

## 4. Proving a nondeterministic parallel graph kernel

| Work | Kernel | Method | Thread count | Mechanized? |
|---|---|---|---|---|
| **FCSL** (Sergey et al. 2015) | In-place spanning tree: `b ← CAS(x->m, 0, 1)` then `span(x->l) ‖ span(x->r)` (PLDI'15 slides) | Subjective concurrent separation logic | Any (parallel recursion) | Yes, Coq |
| **Raad et al. 2016** | Graph copy, speculatively parallel Dijkstra, graph marking, spanning tree | CoLoSL; tracks each thread's "contributions and responsibilities" | "arbitrary recursive thread creation" | Paper proofs (mechanization not stated) |
| **Oortwijn et al. 2020** | Parallel nested DFS (Laarman et al.) | VerCors | Unconfirmed (abstract silent) | Yes, VerCors |
| **Safari et al. 2021** | GPU Bellman-Ford | VerCors; "global invariants" of graph properties | GPU thread range (our reading) | Yes, VerCors |
| Smits 2019 (bachelor thesis) | GPU BFS (Harish et al.) in VerCors | Listed on VerCors wiki "Case Studies" | – | PDF link returns 404: **unconfirmed** |
| **Blelloch et al. 2012** | BFS and others | CAS BFS gives "internal nondeterminism … and external nondeterminism in the resulting BFS tree"; fixed by priority writes (deterministic reservations) | Any | Paper proof sketch (Theorem 1) |
| Moine, Westrick & Tassarotti 2026 | Schedule-independent safety; MiniDet type system | "All results … verified in Rocq using the Iris separation logic framework" | Any (our reading) | Yes; no graph kernel in the abstract |
| Ligra (Shun & Blelloch 2013) | BFS `updateAtomic` = `CAS(&Parents[d], UINT_E_MAX, s)` | – (framework) | – | No (`apps/BFS.C:33-34`) |
| Commutativity line: Rinard & Diniz 1997; Kulkarni et al. 2007 (Galois); Kim & Rinard 2011; Pingali et al. 2011 | Commuting operations as the basis of parallelism | Kim & Rinard verify commutativity conditions | – | Partly |
| Determinism checking: Burnim & Sen 2009; Vechev et al. 2010; DPJ (Bocchino et al. 2009, 2011) | Determinism assertions, structured parallelism, safe nondeterminism | Dynamic, static or type systems | – | – |

**Gap:** we found no mechanized proof of a CPU parallel BFS with CAS parent claiming (searched
2026-10-12; the closest are FCSL's spanning tree and VerCors's Bellman-Ford).

**Mapping to our unit relation (our reading):**
- The needed invariant is monotone: "`parent[v]` ≥ 0 ⇒ it is a frontier neighbor of v, and it never
  changes again in this step". It is stable under every other thread's action. That makes it an
  atomic or resource invariant (separation logic) or a rely condition (rely-guarantee).
- Equality of the next-frontier set needs a ghost set: each claimed v is pushed by the claimant.
  This is the same shape as FCSL's subjective auxiliary state.

---

## 5. CIVL v1.23 facts (Q5)

| Question | Answer | Source |
|---|---|---|
| Version | v1.23.0, published 2026-05-26; one asset `civl-1.23.tgz` (19,388,366 B) | GitHub API, releases of `verified-software-lab/civl` |
| Languages | "primarily C programs, including parallel C programs that use OpenMP or MPI, and CUDA-C"; also Fortran grammars | `README.md`; tree `mods/dev.civl.abc/grammar/{c,fortran,mfortran}` |
| **C++** | **No.** No C++ grammar or front end in the tree; the docs say only subsets of the listed languages are supported | tree at v1.23.0; docs site home page |
| OpenMP constructs parsed | `parallel`, `for`, `parallel for`, `sections`, `section`, `parallel sections`, `single`, `simd`, `master`, `critical (name)`, `ordered`, `atomic` with `read`/`write`/`update`/`capture` and `seq_cst`, `barrier`, `flush`, `threadprivate`; `schedule` kinds `static`/`dynamic`/`guided`/`runtime`/`auto`. No `task`, no `atomic compare`. The grammar's comment: "a bit old … missing some things, e.g., collapse" | `grammar/c/OmpParser.g:45-65,151-161,210-229` |
| Thread count | `$input int _omp_thread_max`; each parallel region gets `1 + $choose_int(_omp_num_threads)` threads, and `$choose_int(n)` returns any integer in [0, n−1] with "all possible choices … enumerated". Docs: "nondeterministically choose an integer between 1 and `omp_thread_max`" | `OpenMP2CIVLWorker2.java:780-830,1020-1033`; `docs/language.md:569-575`; `docs/introduction.md:680-689` |
| `omp for` distribution | `$omp_arrive_loop(…, config.ompLoopDecomp())`; the `schedule` clause is not used (our reading). **Default: `ROUND_ROBIN` in source, `ALL` in docs.** Pass `-ompLoopDecomp=ALL` explicitly | `OpenMP2CIVLWorker2.java:536-555`; `CIVLConstants.java:569-570`; `docs/introduction.md:691-700` |
| Race checking | On by default (`-ompOnlySimplifier`: "rely on the OpenMP simplifier only, i.e. no data-race checking") | `CIVLConstants.java:515-516` |
| CAS | `stdatomic.h` declares `atomic_compare_exchange_*`, but no implementation file was found in `mods/dev.civl.mc` (unconfirmed). Our reading: write the CAS as a CIVL `$atomic { … }` under `#ifdef _CIVL` | `include/stdatomic.h:98-101`; tree search |
| Counterexamples | `civl replay` gives "a step-by-step account" of a violating run | `docs/introduction.md:56-60` |
| Install | Prover(s) on `PATH` (z3, cvc4, cvc5, alt-ergo); "Java 17 or later"; unpack, then `make` (jlink runtime) or `java -Xmx16g -jar civl-complete.jar`; `civl config` writes `~/.sarl`. No macOS-specific notes | `docs/introduction.md:5-48` |
| This Mac (2026-10-13) | z3 and cvc5 on `PATH`; **no Java runtime** (`/usr/bin/java` is the stub: "Unable to locate a Java Runtime") | `command -v`; `java -version` |

---

## Corrections to earlier tickets

1. **[Research 05](05-accelerator-interface-verification.md) source 15 ("volume and pages not
   confirmed"):** Crossref gives *Formal Methods in System Design* 39, pp. 83-113 (2011),
   DOI 10.1007/s10703-011-0124-2.
2. **[Research 02](02-verifier-landscape.md) said CIVL reads "C with OpenMP / MPI / CUDA subsets".**
   That holds at 1.23. Add: it also has Fortran grammars, and it has no C++ (confirmed from the tree,
   not only from the docs).
3. **CIVL's docs and source disagree on the `-ompLoopDecomp` default** (§5). Trust the source, and
   pass the flag explicitly.

## Still unconfirmed

- Whether CIVL executes C11 `atomic_compare_exchange_*` (header only found).
- Anchor's input language; whether Oortwijn et al.'s NDFS proof is stated for any number of workers.
- The PolyOMP name and its construct coverage; Ma et al. 2013's construct coverage.
- The details of the Smits 2019 GPU BFS thesis (dead link).
- The `OMP_NUM_THREADS` value used in certification runs.
- Whether DX100 store results are visible to other cores' DX100 loads at the `critical` exit
  (gem5 completion is shown; cross-core visibility is not).

---

## Sources

**Code and records (ArchEvolve `df077002`):** `swdb-project/apps/dx100/benchmarks/gapbs/src/bfs.cc`
(lines cited inline); `…/src/platform_atomics.h:30-31`; `…/src/sliding_queue.h:91-120`;
`…/gapbs/Makefile:50-86`; `swdb-project/records/candidates/bfs-author-maa-compile-20260925-a1.candidate.yaml:700-725`.

**Tool sources and documents:**
- CIVL v1.23.0: `README.md`, `docs/{introduction,cli,language,libraries}.md`,
  `mods/dev.civl.abc/grammar/c/OmpParser.g`, `mods/dev.civl.abc/src/dev/civl/abc/include/{omp.h,stdatomic.h,civl-omp.cvh}`,
  `mods/dev.civl.mc/src/dev/civl/mc/transform/common/OpenMP2CIVLWorker2.java`,
  `mods/dev.civl.mc/src/dev/civl/mc/config/IF/CIVLConstants.java` —
  https://github.com/verified-software-lab/civl/tree/v1.23.0; docs site https://verified-software-lab.github.io/civl
- DataRaceBench: README and releases — https://github.com/LLNL/dataracebench ; Lin & Liao 2021 PDF —
  https://github.com/LLNL/dataracebench/blob/master/docs/DataRaceBench_Correctness2021.pdf
- Archer: `openmp/tools/archer/README.md` and `ompt-tsan.cpp` — https://github.com/llvm/llvm-project (main, read 2026-10-12)
- GenMC README — https://github.com/MPI-SWS/genmc ; Dartagnan README and releases — https://github.com/hernanponcedeleon/Dat3M
- BRiCk README and `rocq-skylabs-cpp2v/README.md` — https://github.com/SkyLabsAI/BRiCk
- Repository status (GitHub API, 2026-10-12): `microsoft/vcc` archived (last push 2021-01-20);
  `verifast/verifast`, `boogie-org/boogie` active.
- VerCors wiki pages "Parallel Blocks", "Atomics and Locks", "Case Studies" — https://github.com/utwente-fmt/vercors/wiki
- Conc2Seq plug-in page — https://frama-c.com/fc-plugins/conc2seq.html
- Isabelle `Hoare_Parallel` root document — https://isabelle.in.tum.de/repos/isabelle/file/67930/src/HOL/Hoare_Parallel/document/root.tex (lines 122-132 of the rendered page)
- OpenMP API 5.2, §1.4.1 — https://www.openmp.org/spec-html/5.2/openmpsu9.html
- Ligra `apps/BFS.C` — https://github.com/jshun/ligra
- FCSL PLDI 2015 slides — https://software.imdea.org/fcsl/slides/2015-PLDI-Sergey-al.pdf
- Huisman, LOPSTR 2017 slides — https://www.sci.unich.it/lopstr17/slides/huisman-slides.pdf
- Darabi thesis 2018 (U. Twente) — https://ipa.win.tue.nl/?p=1215

**Papers (DOI checked on Crossref unless noted):**

| Short name | Reference | DOI / link |
|---|---|---|
| Lipton 1975 | Reduction: a method of proving properties of parallel programs. CACM 18, 717-721 | 10.1145/361227.361234 |
| Flanagan & Qadeer 2003 | A type and effect system for atomicity. PLDI, 338-349 | 10.1145/781131.781169 |
| Flanagan & Qadeer 2003b | Thread-modular model checking. SPIN, LNCS, 213-224 | 10.1007/3-540-44829-2_14 |
| Elmas et al. 2009 | A calculus of atomic actions (QED). POPL, 2-15 | 10.1145/1480881.1480885 |
| Hawblitzel et al. 2015 | Automated and modular refinement reasoning for concurrent programs (Civl). CAV, 449-465 | 10.1007/978-3-319-21668-3_26 |
| Kragl & Qadeer 2018 | Layered concurrent programs. CAV, 79-102 | 10.1007/978-3-319-96145-3_5 |
| Kragl, Qadeer & Henzinger 2020 | Refinement for structured concurrent programs. CAV, 275-298 | 10.1007/978-3-030-53288-8_14 |
| Kragl et al. 2020 | Inductive sequentialization of asynchronous programs. PLDI, 227-242 | 10.1145/3385412.3385980 |
| Kragl & Qadeer 2021 | The Civl verifier. FMCAD 2021 (TU Wien Academic Press) | 10.34727/2021/isbn.978-3-85448-046-4_23 (not in Crossref; resolves via doi.org to repositum.tuwien.at/handle/20.500.12708/18644) |
| Gangamreddypalli et al. 2026 | Reduction for structured concurrent programs. arXiv 2601.13341 (ESOP 2026 per arXiv) | https://arxiv.org/abs/2601.13341 (preprint) |
| Flanagan & Freund 2020 | The Anchor verifier for blocking and non-blocking concurrent software. PACMPL 4 (OOPSLA) | 10.1145/3428224 |
| Lorch et al. 2020 | Armada: low-effort verification of high-performance concurrent programs. PLDI, 197-210 | 10.1145/3385412.3385971 |
| Cohen et al. 2009 | VCC: a practical system for verifying concurrent C. TPHOLs, LNCS, 23-42 | 10.1007/978-3-642-03359-9_2 |
| Blanchard et al. 2016 | Conc2Seq: a Frama-C plugin for verification of parallel compositions of C programs. SCAM, 67-72 | 10.1109/SCAM.2016.18 |
| Blanchard, Loulergue & Kosmatov 2017 | From concurrent programs to simulating sequential programs: correctness of a transformation | https://arxiv.org/abs/1708.07226 (preprint) |
| Betts et al. 2012 | GPUVerify: a verifier for GPU kernels. OOPSLA, 113-132 | 10.1145/2384616.2384625 |
| Betts et al. 2015 | The design and implementation of a verification technique for GPU kernels. TOPLAS 37, 1-49 | 10.1145/2743017 |
| Li & Gopalakrishnan 2010 | Scalable SMT-based verification of GPU kernel functions (PUG). FSE, 187-196 | 10.1145/1882291.1882320 |
| Li et al. 2012 | GKLEE: concolic verification and test generation for GPUs. PPoPP, 215-224 | 10.1145/2145816.2145844 |
| Chong et al. 2013 | Barrier invariants. OOPSLA, 605-622 | 10.1145/2509136.2509517 |
| Bardsley & Donaldson 2014 | Warps and atomics: beyond barrier synchronization in the verification of GPU kernels. NFM, 230-245 | 10.1007/978-3-319-06200-6_18 |
| Cogumbreiro et al. 2021 | Checking data-race freedom of GPU kernels, compositionally (Faial). CAV, 403-426 | 10.1007/978-3-030-81685-8_19 |
| Leung et al. 2012 | Verifying GPU kernels by test amplification. PLDI, 383-394 | 10.1145/2254064.2254110 |
| Kaiser et al. 2010 | Dynamic cutoff detection in parameterized concurrent programs. CAV, 645-659 | 10.1007/978-3-642-14295-6_55 |
| Blom et al. 2015 | Verification of loop parallelisations. FASE, 202-217 | 10.1007/978-3-662-46675-9_14 |
| Blom et al. 2017 | The VerCors tool set. iFM, 102-110 | 10.1007/978-3-319-66845-1_7 |
| Darabi et al. 2017 | A verification technique for deterministic parallel programs. NFM, 247-264 | 10.1007/978-3-319-57288-8_17 |
| Blom, Huisman & Mihelčić 2014 | Specification and verification of GPGPU programs. SCP 95, 376-388 | 10.1016/j.scico.2014.03.013 |
| Amighi et al. 2014 | Resource protection using atomics. APLAS, 255-274 | 10.1007/978-3-319-12736-1_14 |
| Jacobs et al. 2011 | VeriFast: a powerful, sound, predictable, fast verifier for C and Java. NFM, 41-55 | 10.1007/978-3-642-20398-5_4 |
| Müller et al. 2016 | Viper: a verification infrastructure for permission-based reasoning. VMCAI, 41-62 | 10.1007/978-3-662-49122-5_2 |
| Jung et al. 2018 | Iris from the ground up. JFP 28 | 10.1017/S0956796818000151 |
| Sammler et al. 2021 | RefinedC. PLDI, 158-174 | 10.1145/3453483.3454036 |
| O'Hearn 2007 | Resources, concurrency, and local reasoning. TCS 375, 271-307 | 10.1016/j.tcs.2006.12.035 |
| Boyland 2003 | Checking interference with fractional permissions. SAS, 55-72 | 10.1007/3-540-44898-5_4 |
| Mansky 2022 | Bringing Iris into the Verified Software Toolchain | https://arxiv.org/abs/2207.06574 (preprint; Crossref lookup timed out) |
| Owicki & Gries 1976 | An axiomatic proof technique for parallel programs I. Acta Inf. 6, 319-340 | 10.1007/BF00268134 |
| Jones 1983 | Tentative steps toward a development method for interfering programs. TOPLAS 5, 596-619 | 10.1145/69575.69577 |
| Nipkow & Nieto 1999 | Owicki/Gries in Isabelle/HOL. FASE, 188-203 | 10.1007/978-3-540-49020-3_13 |
| Nieto 2003 | The rely-guarantee method in Isabelle/HOL. ESOP, 348-362 | 10.1007/3-540-36575-3_24 |
| Amani et al. 2017 | COMPLX: a verification framework for concurrent imperative programs. CPP, 138-150 | 10.1145/3018610.3018627 |
| Apt & Kozen 1986 | Limits for automatic verification of finite-state concurrent systems. IPL 22, 307-309 | 10.1016/0020-0190(86)90071-2 |
| Bloem et al. 2015 | Decidability of parameterized verification. Synthesis Lectures | 10.1007/978-3-031-02011-7 |
| Conchon et al. 2012 | Cubicle: a parallel SMT-based model checker for parameterized systems. CAV, 718-724 | 10.1007/978-3-642-31424-7_55 |
| Ghilardi & Ranise 2010 | MCMT: a model checker modulo theories. IJCAR, 22-29 | 10.1007/978-3-642-14203-1_3 |
| Farzan et al. 2015 | Proof spaces for unbounded parallelism. POPL, 407-420 | 10.1145/2676726.2677012 |
| Abdulla et al. 2016 | Parameterized verification through view abstraction. STTT 18, 495-516 | 10.1007/s10009-015-0406-x |
| Hoenicke et al. 2017 | Thread modularity at many levels. POPL, 473-485 | 10.1145/3009837.3009893 |
| Siegel et al. 2015 | CIVL: the concurrency intermediate verification language. SC, 1-12 | 10.1145/2807591.2807635 |
| Cordeiro & Fischer 2011 | Verifying multi-threaded software using SMT-based context-bounded model checking (ESBMC). ICSE, 331-340 | 10.1145/1985793.1985839 |
| Alglave et al. 2013 | Partial orders for efficient bounded model checking of concurrent software (CBMC). CAV, 141-157 | 10.1007/978-3-642-39799-8_9 |
| Gavrilenko et al. 2019 | BMC for weak memory models (Dartagnan). CAV, 355-365 | 10.1007/978-3-030-25540-4_19 |
| Kokologiannakis & Vafeiadis 2021 | GenMC: a model checker for weak memory models. CAV, 427-440 | 10.1007/978-3-030-81685-8_20 |
| Inverso et al. 2014 | Bounded model checking of multi-threaded C programs via lazy sequentialization. CAV, 585-602 | 10.1007/978-3-319-08867-9_39 |
| He et al. 2021 | Satisfiability modulo ordering consistency theory (Deagle). PLDI, 1264-1279 | 10.1145/3453483.3454108 |
| Bora et al. 2020 | LLOV: a fast static data-race checker for OpenMP programs. TACO 17, 1-26 | 10.1145/3418597 (full text: https://arxiv.org/abs/1912.12189) |
| Bora et al. 2021 | OpenMP aware MHP analysis for improved static data-race detection. LLVM-HPC, 1-11 | 10.1109/LLVMHPC54804.2021.00006 |
| Basupalli et al. 2011 | ompVerify: polyhedral analysis for the OpenMP programmer. IWOMP, 37-53 | 10.1007/978-3-642-21487-5_4 |
| Chatarasi et al. 2016 | An extended polyhedral model for SPMD programs and its use in static data race detection. LCPC (LNCS 2017), 106-120 | 10.1007/978-3-319-52709-3_10 |
| Ye et al. 2018 | Using polyhedral analysis to verify OpenMP applications are data race free. Correctness, 42-50 | 10.1109/Correctness.2018.00010 |
| Swain et al. 2020 | OMPRacer. SC, 1-14 | 10.1109/SC41405.2020.00058 |
| Saillard et al. 2014 | Static validation of barriers and worksharing constructs in OpenMP applications. IWOMP, 73-86 | 10.1007/978-3-319-11454-5_6 |
| Atzeni et al. 2016 | ARCHER: effectively spotting data races in large OpenMP applications. IPDPS, 53-62 | 10.1109/IPDPS.2016.68 |
| Atzeni et al. 2018 | SWORD. IPDPS, 845-854 | 10.1109/IPDPS.2018.00094 |
| Serebryany & Iskhodzhanov 2009 | ThreadSanitizer: data race detection in practice. WBIA, 62-71 | 10.1145/1791194.1791203 |
| Gu & Mellor-Crummey 2018 | Dynamic data race detection for OpenMP programs (ROMP). SC, 767-778 | 10.1109/SC.2018.00064 |
| Ma et al. 2013 | Symbolic analysis of concurrency errors in OpenMP programs. ICPP, 510-516 | 10.1109/ICPP.2013.63 |
| Liao et al. 2017 | DataRaceBench. SC, 1-14 | 10.1145/3126908.3126958 |
| Lin & Liao 2021 | High-precision evaluation of both static and dynamic tools using DataRaceBench. Correctness, 1-8 | 10.1109/Correctness54621.2021.00011 |
| Du et al. 2026 | A formal semantics of C with OpenMP parallelism. LNCS, 436-455 (venue not identified) | 10.1007/978-3-032-28079-4_20; arXiv 2605.26527 |
| Donaldson et al. 2010 | Automatic analysis of scratch-pad memory code for heterogeneous multicore processors (SCRATCH). TACAS, 280-295 | 10.1007/978-3-642-12002-2_24 |
| Donaldson et al. 2011 | Automatic analysis of DMA races using model checking and k-induction. FMSD 39, 83-113 | 10.1007/s10703-011-0124-2 |
| Botinčan et al. 2011 | Safe asynchronous multicore memory operations (asyncStar). ASE, 153-162 | 10.1109/ASE.2011.6100049 |
| Barua et al. 2019 | OMPSan: static verification of OpenMP's data mapping constructs. IWOMP, 3-18 | 10.1007/978-3-030-28596-8_1 |
| Yu et al. 2021 | ARBALEST: dynamic detection of data mapping issues in heterogeneous OpenMP applications. IPDPS, 464-474 | 10.1109/IPDPS49936.2021.00055 |
| Chen et al. 2014 | MC-Checker: detecting memory consistency errors in MPI one-sided applications. SC, 499-510 | 10.1109/SC.2014.46 |
| Nayak et al. 2026 | Towards an accurate GPU data race detector (HGRD) | https://arxiv.org/abs/2604.02106 (preprint) |
| Stewart & Malecha 2025; An et al. 2026 | BRiCk ZynqMP DMA talk; AccelSync preprint | as cited in [research 05](05-accelerator-interface-verification.md) sources 20 and AccelSync |
| Sergey et al. 2015 | Mechanized verification of fine-grained concurrent programs (FCSL). PLDI, 77-87 | 10.1145/2737924.2737964 |
| Raad et al. 2016 | Verifying concurrent graph algorithms. APLAS, 314-334 | 10.1007/978-3-319-47958-3_17 |
| Oortwijn et al. 2020 | Automated verification of parallel nested DFS. TACAS, 247-265 | 10.1007/978-3-030-45190-5_14 |
| Safari et al. 2021 | Automated verification of the parallel Bellman-Ford algorithm. SAS, 346-358 | 10.1007/978-3-030-88806-0_17 |
| Blelloch et al. 2012 | Internally deterministic parallel algorithms can be fast. PPoPP, 181-192 | 10.1145/2145816.2145840 (text: https://jshun.csail.mit.edu/determ.pdf, Theorem 1 and §5.3) |
| Shun & Blelloch 2013 | Ligra. PPoPP, 135-146 | 10.1145/2442516.2442530 |
| Moine et al. 2026 | All for one and one for all: program logics for exploiting internal determinism in parallel programs. PACMPL 10 (POPL), 748-776 | 10.1145/3776668 |
| Pingali et al. 2011 | The tao of parallelism in algorithms. PLDI, 12-25 | 10.1145/1993498.1993501 |
| Kulkarni et al. 2007 | Optimistic parallelism requires abstractions. PLDI, 211-222 | 10.1145/1250734.1250759 |
| Rinard & Diniz 1997 | Commutativity analysis. TOPLAS 19, 942-991 | 10.1145/267959.269969 |
| Kim & Rinard 2011 | Verification of semantic commutativity conditions and inverse operations on linked data structures. PLDI, 528-541 | 10.1145/1993498.1993561 |
| Burnim & Sen 2009 | Asserting and checking determinism for multithreaded programs. ESEC/FSE, 3-12 | 10.1145/1595696.1595700 |
| Vechev et al. 2010 | Automatic verification of determinism for structured parallel programs. SAS, 455-471 | 10.1007/978-3-642-15769-1_28 |
| Bocchino et al. 2009 | A type and effect system for Deterministic Parallel Java. OOPSLA, 97-116 | 10.1145/1640089.1640097 |
| Bocchino et al. 2011 | Safe nondeterminism in a deterministic-by-default parallel language. POPL, 535-548 | 10.1145/1926385.1926447 |
