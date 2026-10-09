# Research 05: How formal verifiers model an accelerator's hardware interface

Created: 2026-10-09 14:18 ET
**Ticket:** [05](../issues/05-accelerator-interface-verification.md)
**Map:** [../map.md](../map.md)
**Method:** narrative literature review using the deep-research lit-review discipline: each
source checked at its primary location, with read scope recorded in [Sources](#sources). Code
line numbers are at ArchEvolve `c9220665` (`yanrujhou_main`).

---

## TL;DR

- **Nobody ships a ready-made "sentinel until covering wait" semantics.** Prior work models a
  device's hardware interface in one of four ways: (1) as instant procedure calls, (2) as
  havocked (nondeterministic) state, (3) as a concurrent device thread, or (4) as ownership
  that a command takes away and a wait gives back. Our functional model is way 1 and our strict
  layer is a deterministic variant of way 2.
- **The functional model alone is unsound for our purpose.** It completes every operation at
  issue, so a formal verifier using it would *prove* the authors' `TDStepMAA` correct. The
  wrong-tile wait is invisible to it.
- **The closest prior work is DMA race checking on the Cell processor** (SCRATCH, asyncStar):
  a command plus a tag plus `wait(tag)`, checked by a formal verifier. Ghost "tracker arrays"
  record pending commands, an assertion fires on any access that conflicts with one, and the
  data a command writes is set to nondeterministic values. A 2026 preprint (AccelSync) does the
  same for AI-accelerator pipelines and reports a 19.2% defect rate in 120 LLM-generated kernels.
- **The strict layer has two gaps a proof would inherit.** (a) DX100 memory reads and writes
  take effect at *issue*, so main memory touched by an uncovered operation is never flagged.
  (b) The sentinel `0xa5a5a5a5` is one fixed value, so a proof could pass by accident on it.
- **The ILA line of work (ILA, ILAng, ILA-MCM, D2A, 3LA, Glenside) is the right long-term
  shape but the wrong first step.** ILA expresses each command as an atomic state update.
  Asynchrony and interleaving are handled "outside of ILAs" (ILA TODAES §3), so we would still
  have to build the wait semantics ourselves.

### Recommended way to turn our two models into verification semantics

**Split every DX100 proof into two obligations, and write one model a formal verifier can read for each:**

1. **Hazard obligation (H), over a "proof edition" of the strict layer.** Re-express the
   174-line strict layer in a C/C++ subset a formal verifier handles: fixed-size arrays, no
   `std::vector`, `std::mutex`, OpenMP or recursion. Keep its rules and asserts. Make three
   changes:
   - **Calls** (`get_tile_size`, `get_reg`, `get_tile_ready`) on an uncovered tile or
     register become an **assertion failure**, not a sentinel.
   - **Tile pointer reads** become **havoc**: issue fills the CPU-side buffer with
     nondeterministic values instead of `0xa5a5a5a5` (the SCRATCH and AWS-CBMC choice).
   - **Add SCRATCH-style tracker entries** for each uncovered operation's main-memory
     footprint, and assert that the CPU does not touch it before a covering wait.
2. **Functional obligation (F), over the functional model's instant-completion semantics.** Prove
   the rewrite contract's postconditions with every `maa_*` call treated as completing at
   issue. This is simpler and closer to what verified lifting and D2A already handle.
3. **Glue, proven once:** a reduction lemma, the analog of "data-race-free programs see
   sequential consistency" (Adve & Hill 1990). It states: *if (H) holds, every behavior under
   asynchronous completion equals the behavior under instant completion.* This is a paper proof
   about the model, done once, which fits ticket 01's "prove once, reuse" headline.

**Cost:** medium. The work is a proof edition of about 170 lines plus differential tests
against the strict layer, and one hand proof of the reduction lemma. The risk sits in the
lemma's side conditions (main-memory footprints, and in-order DX100 execution), which have to
be written down. Detail is in [§3](#3-the-recommended-split-in-detail).

---

## Options at a glance

| # | Option | What it is | Cost | Trust gap | Prior work |
|---|---|---|---|---|---|
| A | **Functional model as is** | Compile the candidate artifact against the authors' `MAA_functional.hpp`; every call completes at issue | Lowest: code exists, but it has OpenMP pragmas, `pthread` and `iostream` | **Blind to asynchrony**: proves `TDStepMAA`, which is a false proof | Horn et al. 2013 ("hardware response is effectively instantaneous" mode); Exo `@instr` bodies |
| B | **Strict layer as is** | Feed the strict layer and the candidate to a formal verifier unchanged | Low to write; **high verifier risk**: `std::vector`, `std::mutex`, OpenMP, recursive `cover()` | Fixed sentinel can mask a bug; main memory unmodeled; strict layer itself unvalidated against hardware | AWS boot code (device models supplied in the harness) |
| C | **Proof edition of the strict layer** (recommended for H) | Rewrite of the strict layer that a formal verifier can read: havoc plus ghost coverage bits, asserts as verification conditions, footprint trackers | **Medium**: rewrite about 170 lines; bounded equivalence or differential tests against B | Must be shown to match B; inherits B's assumed wait rules | SCRATCH tracker arrays; AWS "havoc the device"; asyncStar |
| D | **Nondeterministic asynchronous model** | Each command spawns a device thread, or sits in a pending set that completes in any dependency-respecting order; early reads see old, new or arbitrary values | **High**: needs a concurrency-capable formal verifier; interleavings explode | Closest to real hardware, but the true completion rules are unconfirmed (spec: "assumed, owner Eric") | Horn et al. 2013 (asynchronous threads); BlueRock ZynqMP DMA (device as a thread in Iris); MachCSL 2026; ILA-MCM |
| E | **Ownership or permission encoding** | Ghost token per tile: issue takes it, a covering wait returns it; every read requires it | **Medium to high**: a contract on each of the 5 data operations and on each control call (`maa_const`, `wait_ready`, `get_reg`, `get_tile_size`, tile pointers, memory-region registration), in a deductive formal verifier that reads C++ | Proves hazard freedom unbounded; says nothing about values (needs F) | asyncStar (separation logic with permissions); Rust embedded DMA ownership; BRiCk |
| F | **ILA model of the DX100 hardware interface** | Write DX100 as an ILA in ILAng: commands become instructions with decode and state-update functions | **High**: new tool, a C++ DSL, SMT export; asynchrony still has to be added outside the ILA | Adds a route to check gem5 or RTL against the model, which ticket 01 ruled out of scope | ILA (TODAES), ILAng (TACAS'19), ILA-MCM (FMCAD'18), DAC'18 firmware, D2A, 3LA |
| G | **Verified lifting for F** | Lift the instant-completion `maa_*` sequence and the original kernel into a gather/scatter IR, then prove them equivalent | **High**: new IR and synthesis; strong for unbounded functional proofs | Does not address asynchrony; needs H first | STNG (PLDI'16), Tenspiler (ECOOP'24), D2A CHC proofs |

**Reading the table:** C plus A-style instant semantics for F, joined by the reduction lemma, is
the recommendation. E is the upgrade path to *proven unbounded* hazard freedom. D is the check on
the lemma's assumptions. F and G are later and larger bets.

---

## 1. What our DX100 semantics actually say today

| Artifact | Path | Async behavior | Matters because |
|---|---|---|---|
| Functional model | `apps/dx100/benchmarks/API/MAA_functional.hpp` (775 lines; 11 data operations plus `maa_const`) | None: each op computes at once and sets the ready bit to 1; nothing ever sets it to 0 | A formal verifier on it cannot see wait bugs |
| Strict layer | `library/dx100/strict/MAA_functional.hpp` (174 lines; 5 data ops plus `maa_const` and control calls) | Tiles and registers: CPU sees `0xa5a5a5a5` until a covering wait (`:74`, `:109`, `:114`); `wait_ready` covers the tile's last writer and its dependencies (`:78`, `:117`) | It is the trusted semantics (ticket 01) |
| MMIO lowering | `apps/dx100/benchmarks/API/MAA_gem5.hpp` | `wait_ready` is **one load of the ready flag plus `mfence`** (`:98-100`); blocking happens in the device, not in C | Any software proof against the lowering needs a device model for that load |
| Candidate 1 | `apps/dx100/benchmarks/gapbs/src/bfs.cc:179-190` | Store issued (`:179`), wait on its source `tile3` (`:180`), CPU reads `tile4Ptr`, `tile5Ptr` (`:190`) | The motivating wrong-tile case |

Five observations that shape the options:

1. **Functional model: the bug is invisible.** All ready bits start at 1 and only ever get set to 1,
   so `wait_ready(tile3)` returns at once and `tile5` already holds the store's old values.
2. **Strict layer: main memory is synchronous.** `maa_stream_load` and `maa_indirect_load` read
   memory at issue (`:126`, `:131`). `maa_indirect_store_vector` writes memory with
   `__atomic_store_n` at issue (`:170`). Only tiles and registers get a sentinel. So the strict
   layer never flags:
   - a CPU read of memory that an uncovered DX100 store will write;
   - a CPU write to memory that an uncovered DX100 load still has to read.

   SCRATCH calls both of these DMA races. The three proof-of-concept candidates barely exercise
   this (in candidate 1 only DX100 itself reads `parent` after its store, in program order). It
   will matter for stores, read-modify-write operations, and the concurrency phase.
3. **Strict layer: the sentinel is one value.** `0xa5a5a5a5` is negative as `int32`. In
   candidate 1 it makes both `tile4Ptr[i]` (nonzero) and `tile5Ptr[i] < 0` true, so the bug
   shows up as extra queue pushes. That is luck: a property that happens to hold on
   `0xa5a5a5a5` would pass. SCRATCH states the sound rule: "to achieve soundness, we must set
   the memory locations written to by a DMA operation to nondeterministic values" (TACAS'10 §4).
4. **Strict layer: in-order DX100 execution is assumed.** The spec says "A thread's DX100
   operations take effect in program order" (`.scratch/typed-library-dx100-bfs-2026-10-03/spec.md:476`).
   The reduction lemma needs this, and it should be listed as an assumption.
5. **The wait-coverage rule is assumed, and the functional model's code leans the other way.**
   The spec marks the rules "assumed, owner Eric, until gem5's ready-bit semantics are
   confirmed" (`spec.md:484-485`). The authors' functional model calls
   `set_tile_ready(src_tile, 1)` at the end of `maa_stream_store`, `maa_indirect_store_vector`
   and `maa_indirect_rmw_vector` (`MAA_functional.hpp:570`, `:614`, `:686`; also `:458` for
   reduce). That call only means something if the hardware clears a *source* tile's ready bit at
   issue and sets it when the store finishes. If so, `wait_ready(tile3)` may in fact wait for the
   store. *Reader-inferred*: no gem5 DX100 device source is in this repo to settle it. See
   [§4](#4-findings-that-challenge-ticket-01).

---

## 2. How prior work models an accelerator's hardware interface

### 2.1 The ILA family: commands as instructions

- **ILA** (Huang et al., TODAES 2018). It extends the ISA idea to accelerators: each
  "instruction" is a command at the hardware interface, with a decode condition and
  state-update functions over architectural state. The AES example has a `START_ENCRYPT`
  instruction and a `GET_STATUS` instruction to "poll for completion". Key limit for us:
  "instructions are sequentially composed within an ILA, whereas concurrency and interleaving
  models are handled outside of ILAs" (§3).
- **ILA as the MMIO hardware interface** (Zhang et al., LATTE'21; Huang et al., 3LA, TODAES
  2024). "Each instruction of an accelerator ILA corresponds to a command at the accelerator
  interface, i.e., an MMIO load or store from a host processor" (3LA §2.1). Checking an ILA
  against RTL needs a refinement map with an "instruction completion condition", either a
  commit signal or a cycle bound (LATTE'21 §3.1). That is the hardware-side twin of our
  covering wait.
- **ILAng** (TACAS'19 tool paper). It builds ILAs, synthesizes them from templates, checks
  properties and equivalence, and exports to Verilog and SMT-LIB2.
- **ILA-MCM** (FMCAD'18). This adds asynchrony between agents. Each shared variable gets
  per-agent "facets" that ILA instructions update; memory-consistency axioms order the facet
  events. With a 30-instruction bound under SC it reproduced a known time-of-check/time-of-use
  firmware exploit in 3.5 s. Under TSO it found a new one in 6.5 s with a 32-instruction bound,
  fixed by adding a fence. This is the most rigorous treatment of "when does the CPU see the
  accelerator's write", and it is heavy.
- **Firmware plus ILA** (Huang et al., DAC'18). Firmware and each IP's ILA are merged into one
  thread; several IPs become a multithreaded program for standard software verification
  (abstract only; the PDF did not parse).
- **D2A** (arXiv 2203.00218v1, 2022; revised as 3LA). It compiles PyTorch and MxNet to
  accelerators using ILA semantics and checks "individual matched operations" formally. The
  FlexASR MaxPool case: bounded model checking took 443 s at 2×16 and timed out after 3 h at
  8×64 and 16×64. Constrained Horn clauses with **manually supplied relational invariants**
  verified 16×64 in 5177 s. This is direct evidence for ticket 01's proof-hint approach (bounded
  checking hits a wall; invariants get past it).
- **Glenside** (MAPS'21). A pure tensor IR with access patterns; term rewriting maps program
  fragments to accelerator invocations. It is relevant to F (offload as a rewrite), not to waits.

**Verdict:** ILA gives each DX100 call clean per-instruction semantics, which our functional
model already has in C++. It does not give the wait semantics.

### 2.2 Device and MMIO models inside software formal verifiers

- **AWS boot code in CBMC** (Cook et al., CAV'18). This is the clearest statement of the
  options. "Not handling MMIO or linker scripts results in imprecision (false positives), and not
  modeling device behavior is unsound (false negatives)." The mechanisms:
  - `__CPROVER_allocated_memory` marks MMIO ranges as valid memory.
  - `--remove-function-body` havocs a device API, or the harness supplies a precise model.
  - `__CPROVER_mm_io_r` / `__CPROVER_mm_io_w` hooks catch raw MMIO accesses.

  AWS havocked every device "to make our result as strong as possible".
- **Horn et al., FMCAD'13.** Symbolic co-execution in CBMC of firmware plus an *executable C
  hardware model*, with protocol rules as **runtime assertions inside the model**, the same
  pattern as our strict layer. Two modes:
  - **instant:** "procedure calls into the hardware model … encodes an assumption that hardware
    response is effectively instantaneous", which is our functional model;
  - **asynchronous:** each register write spawns a thread that runs the hardware's response,
    which is option D.

  Cases ran up to 18 threads. They found executable hardware models "essential".
- **Static Driver Verifier** (Ball et al., EuroSys'06) and **DDVerify** (Witkowski et al.,
  ASE'07). Environment models of the OS kernel around a driver, plus API usage rules. They model
  the *software* environment more than the device, but they set the norm: a formal verifier
  always runs against a hand-written environment model, and that model is trusted.
- **SymDrive** (Renzelmann et al., OSDI'12). A symbolic device (via S²E) stands in for the
  hardware: device reads return symbolic values. It is a testing tool, but it is the same havoc
  idea.

### 2.3 Asynchronous commands with waits: the closest match

- **SCRATCH** (Donaldson, Kroening, Rümmer; TACAS'10, FMSD'11). Cell processor
  `get`/`put(…, tag)` plus `wait(tag)`. Each DMA call is rewritten into an assertion plus
  updates to ghost **tracker arrays**:
  - the arrays hold `valid`, `is_get`, local and host address, size and tag;
  - every new DMA asserts that it does not overlap any pending one;
  - `wait(t)` clears the tracked entries with tag `t`.

  Built on CBMC. k-induction gives **unbounded** proofs over loops. Applied to IBM Cell SDK
  programs, it found a previously unknown bug. Its injected bugs, "removing a wait operation,
  changing the tag used to identify a DMA", are exactly our wrong-tile class.
- **asyncStar** (Botinčan, Dodds, Donaldson, Parkinson; ASE'11). Separation logic with
  permissions: issuing a transfer from A to B needs read permission on A and write permission on
  B, and "the thread loses these permissions until it issues a corresponding synchronisation
  operation". This is option E, automated for a C-like core language and checked on Cell SDK
  programs.
- **AccelSync** (An, Wang, Qian; arXiv 2605.07881, May 2026, preprint). AI-accelerator pipelines
  (DMA, vector, matrix and scalar units sharing on-chip buffers) are expressed in a restricted
  concurrent language. "Barrier sufficiency" means every cross-unit write-read pair on a buffer
  is ordered by happens-before; the authors show it is decidable in O(|E|²). Reported results:
  - 3 unknown hazards in 6,292 production kernels;
  - **a 19.2% defect rate in 120 LLM-generated kernels**.

  Own checker, not an existing formal verifier. This matters for ticket 06 positioning too.
- **GPU analogs.** NVIDIA's PTX "proxy" extensions (Lustig, Cooksey, Giroux; ISCA'22) tag memory
  and fence operations so accelerator paths fit the formal memory model. The GPUVerify tutorial
  verifies a kernel that uses OpenCL asynchronous copies. I found no published formal verifier
  for Hopper-style asynchronous copies with barrier waits (search-bounded, 2026-10-09).

### 2.4 Device as a concurrent agent in deductive proofs

- **BlueRock ZynqMP DMA driver** (Stewart and Malecha, seL4 Summit 2025 talk). A **C++** driver
  verified in BRiCk (Iris-based concurrent separation logic). "Device and driver run
  concurrently. Treat each as a thread". The device is a small-step operational model in Rocq,
  embedded through invariants and ghost state; an MMIO write is safe only in device states that
  allow it.
- **MachCSL** (Kaashoek, Zeldovich; arXiv 2609.04043, Sept 2026, preprint). Iris-based logic over
  Sail RISC-V, covering DMA and interrupts; it verifies xv6 (about 6,600 lines of C and assembly)
  and found ten bugs. It shows that deductive device models now scale to a whole OS, at months of
  effort (the abstract reports 93 days).

### 2.5 Hardware operation semantics inside compilers and lifters

- **Exo** (Ikarashi et al., PLDI'22). Each accelerator instruction is an `@instr` procedure whose
  body is its semantics and whose annotation is the C it emits. The paper says: "Exo entrusts
  programmers with the responsibility of verifying the link between the Exo procedure and
  annotation." This is the same trust gap as our lowering against its reference semantics.
  Configuration state is modeled; asynchrony is not.
- **Verified lifting** (STNG, PLDI'16; Tenspiler, ECOOP'24). Synthesize a high-level summary and
  prove it equivalent to the source. Tenspiler synthesizes over small bounded states, then
  verifies with SMT (cvc5) "for all possible program states", with synthesized loop invariants,
  over integers and reals, not floats. The proof covers the lift, not the generated backend code.
  This fits F, after H has removed asynchrony.

---

## 3. The recommended split in detail

```
candidate artifact
  ├─ (H) hazard obligation        → proof edition of the strict layer (option C)
  │      covered reads, footprints, ownership, 32-bit offsets, truncation, memory regions
  ├─ (F) functional obligation    → instant-completion semantics (functional-model style)
  │      rewrite contract's postconditions and preservation obligations
  └─ (L) reduction lemma, once    → (H) ⇒ async behaviors = instant-completion behaviors
```

**Proof edition: what changes relative to the strict layer**

| Strict layer today | Proof edition | Why |
|---|---|---|
| `std::vector`, `std::mutex`, OpenMP thread id, recursive `cover()` | Fixed arrays sized by `NUM_TILES`, `NUM_SCALAR_REGS` and a bounded op log; single thread; iterative cover | Formal verifiers handle these poorly (C++ support is ticket 02's call) |
| `0xa5a5a5a5` on uncovered tile reads | Nondeterministic fill at issue | Sound for every property, not just properties that fail on one value (SCRATCH, AWS) |
| Sentinel from `get_reg` and `get_tile_size` | `assert(covered)` | Reads through calls can be checked exactly |
| Memory read and written at issue | Same data effect, **plus** a tracker entry for each uncovered op's footprint; assert no conflicting CPU access before cover | Closes the main-memory gap (SCRATCH) |
| Asserts call `_Exit(86)` | Asserts become verification conditions | Each strict check becomes a proof goal |

**Evidence that the proof edition equals the strict layer:** run both under the existing
certification inputs and negative controls (differential testing). Optionally add a bounded
equivalence check with a small `TILE_SIZE` (the strict layer already takes it as a macro). Record
`TILE_SIZE` among the bounds of any proven-within-bounds verdict, because chunking changes with it.

**What must be written down for the lemma (L):**
1. DX100 operations of one thread execute in program order (spec `:476`).
2. Every CPU read of a tile or register is covered (H).
3. No CPU access to main memory overlaps an uncovered op's footprint (H, the new trackers).
4. Tiles and registers are thread-owned (an existing strict assert), so in the concurrency phase
   per-thread DX100 state separates and only main memory is shared.

The lemma is the accelerator version of DRF-SC (Adve & Hill 1990). It is a paper proof over the
model, done once, and reused by every candidate artifact.

**How each proof-of-concept candidate lands** (expected, not run):
- **Candidate 1, `TDStepMAA`:** (H) fails at `bfs.cc:190`; the read of `tile5` is uncovered after
  `wait_ready(tile3)`. This holds *only under the strict layer's coverage rule*; see §4.
- **Candidate 2, Peter's read offload:** DX100 issues no stores, so the footprint trackers are
  nearly empty. (H) should be cheap, and the effort goes to (F).
- **Candidate 3, Codex's native frontier staging:** no DX100 calls, so only (F) applies.

---

## 4. Findings that challenge ticket 01

1. **"The strict layer is the trusted semantics" needs a stated scope.** The strict layer is
   strict for tiles and registers but *synchronous for main memory* (§1, observation 2). Trusting
   it as is means trusting that no candidate artifact reads memory an in-flight DX100 store will
   write. Recommendation: either add footprint tracking (option C) or record main-memory
   synchrony as a named assumption on every DX100 proof.
2. **Candidate 1's "must be refuted" holds relative to an assumed rule.** The rule "waiting on a
   store's source tile does not cover the store" is marked assumed (`spec.md:481-485`). The
   functional model sets a store's source tile ready on completion (`:570`, `:614`, `:686`),
   which hints the authors meant that wait to cover the store. If gem5 agrees, the wrong-tile
   finding becomes "the hardware interface is ambiguous" rather than "the expert code is wrong".
   That is still a result, but a different claim. Recommendation for ticket 12: phrase the verdict
   as "refuted under strict semantics S (version …)", and get Josh's `dxc-observer` answer before
   the paper leans on it as motivating evidence.
3. **The functional model must never be the semantics for (H).** Under it, candidate 1 would be
   *proven*. That is a vacuity trap of the kind the map's "Vacuity guard" open item worries about.
   A useful negative control: the formal verifier must refute candidate 1 under the proof edition
   *and* must prove it under instant semantics (if it is otherwise correct). Both outcomes show
   that the semantics are doing the work.

---

## 5. Open questions

- **gem5 ready-bit rules.** Which tiles does each command clear at issue? Does a store's source
  tile stay not-ready until the store's writes land? This decides finding 2 and the wait rule in
  every model above.
- **In-order DX100.** Does the device ever reorder independent commands from one core? If yes, the
  lemma needs device-to-device footprint checks too.
- **Proof edition language.** It must be in whatever C/C++ subset ticket 02's chosen formal
  verifier reads. The ownership-token version (E) needs a deductive verifier with C++ support
  (BRiCk is one; heavy).
- **Main-memory footprint size.** An indirect store's footprint is data-dependent (indices in a
  tile). SCRATCH tracked contiguous ranges; we need per-element or summarized footprints. This is
  a likely source of proof hints.

---

## Sources

Read scope and verification status per source. All URLs and DOIs were found during this review
on 2026-10-09. "Verified" means I read the text at the primary location; "abstract" means only
the abstract or listing was read.

| # | Source | Venue | Link | Read scope |
|---|---|---|---|---|
| 1 | Bo-Yuan Huang, Hongce Zhang, Pramod Subramanyan, Yakir Vizel, Aarti Gupta, Sharad Malik. *Instruction-Level Abstraction (ILA): A Uniform Specification for System-on-Chip (SoC) Verification* | ACM TODAES, Dec 2018 | https://arxiv.org/abs/1801.01114 | Verified: §1, §3 |
| 2 | Bo-Yuan Huang, Hongce Zhang, Aarti Gupta, Sharad Malik. *ILAng: A Modeling and Verification Platform for SoCs Using Instruction-Level Abstractions* | TACAS 2019, LNCS, pp. 351-357 | https://doi.org/10.1007/978-3-030-17462-0_21 | Abstract and listing |
| 3 | Hongce Zhang, Caroline Trippel, Yatin A. Manerkar, Aarti Gupta, Margaret Martonosi, Sharad Malik. *ILA-MCM: Integrating Memory Consistency Models with Instruction-Level Abstractions for Heterogeneous System-on-Chip Verification* | FMCAD 2018 | https://www.cs.princeton.edu/~aartig/papers/fmcad18-ilamcm.pdf | Verified: abstract, facets, case studies |
| 4 | Hongce Zhang, Bo-Yuan Huang, Yue Xing, Aarti Gupta, Sharad Malik. *Hardware-Software Interface Specification for Verification in Accelerator-Rich Platforms* | LATTE '21 workshop | https://capra.cs.cornell.edu/latte21/paper/6.pdf | Verified: full text |
| 5 | Bo-Yuan Huang, Sayak Ray, Aarti Gupta, Jason M. Fung, Sharad Malik. *Formal Security Verification of Concurrent Firmware in SoCs Using Instruction-Level Abstraction for Hardware* | DAC 2018 | https://doi.org/10.1145/3195970.3196055 | Abstract only (PDF corrupt) |
| 6 | Bo-Yuan Huang, Steven Lyubomirsky, Yi Li, Mike He, Thierry Tambe, Gus Henry Smith, Akash Gaonkar, Vishal Canumalla, Gu-Yeon Wei, Aarti Gupta, Zachary Tatlock, Sharad Malik. *Specialized Accelerators and Compiler Flows: Replacing Accelerator APIs with a Formal Software/Hardware Interface* (the **D2A** paper) | arXiv 2203.00218v1, 2022 | https://arxiv.org/abs/2203.00218v1 | Verified: §2.3, §4.4.1, Table 3 |
| 7 | Bo-Yuan Huang, Steven Lyubomirsky, Yi Li, Mike He, Gus Henry Smith, Thierry Tambe, Akash Gaonkar, Vishal Canumalla, Andrew Cheung, Gu-Yeon Wei, Aarti Gupta, Zachary Tatlock, Sharad Malik. *Application-level Validation of Accelerator Designs Using a Formal Software/Hardware Interface* (**3LA**) | ACM TODAES 29(2), 2024 | https://doi.org/10.1145/3639051 | Verified (arXiv v2): §1, §2.1 |
| 8 | Gus Henry Smith, Andrew Liu, Steven Lyubomirsky, Scott Davidson, Joseph McMahan, Michael Taylor, Luis Ceze, Zachary Tatlock. *Pure Tensor Program Rewriting via Access Patterns (Representation Pearl)* (**Glenside**) | MAPS 2021 | https://arxiv.org/abs/2105.09377 | Abstract |
| 9 | Byron Cook, Kareem Khazem, Daniel Kroening, Serdar Tasiran, Michael Tautschnig, Mark R. Tuttle. *Model Checking Boot Code from AWS Data Centers* | CAV 2018, LNCS 10982, pp. 467-486 | https://doi.org/10.1007/978-3-319-96142-2_28 | Verified: §1, §4 |
| 10 | Alex Horn, Michael Tautschnig, Celina Val, Lihao Liang, Tom Melham, Jim Grundy, Daniel Kroening. *Formal Co-Validation of Low-Level Hardware/Software Interfaces* | FMCAD 2013, pp. 121-128 | https://www.cs.utexas.edu/users/hunt/FMCAD/FMCAD13/papers/44-Formal-Covalidation-Low-Level-Interfaces.pdf | Verified: §I-II |
| 11 | Thomas Ball, Ella Bounimova, Byron Cook, Vladimir Levin, Jakob Lichtenberg, Con McGarvey, Bohus Ondrusek, Sriram K. Rajamani, Abdullah Ustuner. *Thorough Static Analysis of Device Drivers* | EuroSys 2006, pp. 73-85 | https://doi.org/10.1145/1217935.1217943 | Abstract |
| 12 | Thomas Witkowski, Nicolas Blanc, Daniel Kroening, Georg Weissenbacher. *Model Checking Concurrent Linux Device Drivers* | ASE 2007, pp. 501-504 | https://doi.org/10.1145/1321631.1321719 | Abstract |
| 13 | Matthew J. Renzelmann, Asim Kadav, Michael M. Swift. *SymDrive: Testing Drivers without Devices* | OSDI 2012, pp. 279-292 | https://www.usenix.org/system/files/conference/osdi12/osdi12-final-4.pdf | Abstract |
| 14 | Alastair F. Donaldson, Daniel Kroening, Philipp Rümmer. *Automatic Analysis of Scratch-Pad Memory Code for Heterogeneous Multicore Processors* (**SCRATCH**) | TACAS 2010, LNCS 6015, pp. 280-295 | https://www.doc.ic.ac.uk/~afd/papers/2010/TACAS.pdf | Verified: §2, §4, §6 |
| 15 | Alastair F. Donaldson, Daniel Kroening, Philipp Rümmer. *Automatic Analysis of DMA Races Using Model Checking and k-Induction* | Formal Methods in System Design, 2011 (volume and pages not confirmed) | https://www.doc.ic.ac.uk/~afd/papers/2011/FMSD.pdf | Listing; PDF downloaded, abstract only |
| 16 | Matko Botinčan, Mike Dodds, Alastair F. Donaldson, Matthew J. Parkinson. *Safe Asynchronous Multicore Memory Operations* (**asyncStar**) | ASE 2011, pp. 153-162 | https://doi.org/10.1109/ASE.2011.6100049 | Verified: abstract, §I-II |
| 17 | Hangcheng An, Rui Wang, Depei Qian. *AccelSync: Verifying Synchronization Coverage in Accelerator Pipeline Programs* | arXiv 2605.07881, 2026; **preprint, not peer reviewed** | https://arxiv.org/abs/2605.07881 | Abstract |
| 18 | Daniel Lustig, Simon Cooksey, Olivier Giroux. *Mixed-Proxy Extensions for the NVIDIA PTX Memory Consistency Model* | ISCA 2022 (industry track) | https://research.nvidia.com/publication/2022-06_mixed-proxy-extensions-nvidia-ptx-memory-consistency-model | Abstract |
| 19 | GPUVerify tutorial (asynchronous-copy example) | Tool documentation | https://fastpl.doc.ic.ac.uk/tools/GPUVerify/docs/tutorial.html | Search snippet only; **unverified detail** |
| 20 | Gordon Stewart, Gregory Malecha. *Verified ZynqMP DMA Driver in Concurrent Separation Logic* | seL4 Summit 2025 talk (slides); gray literature | https://sel4.systems/Summit/2025/slides/verified-zynqmp.pdf | Verified: slides |
| 21 | M. Frans Kaashoek, Nickolai Zeldovich. *Extending Concurrent Separation Logic to the Hardware Level to Verify the xv6 OS Kernel on RISC-V with AI Agents* (**MachCSL**) | arXiv 2609.04043, 2026; **preprint** | https://arxiv.org/abs/2609.04043 | Abstract |
| 22 | Yuka Ikarashi, Gilbert Louis Bernstein, Alex Reinking, Hasan Genc, Jonathan Ragan-Kelley. *Exocompilation for Productive Programming of Hardware Accelerators* | PLDI 2022 | https://doi.org/10.1145/3519939.3523446 | Verified: §2, trust statement |
| 23 | Shoaib Kamil, Alvin Cheung, Shachar Itzhaky, Armando Solar-Lezama. *Verified Lifting of Stencil Computations* (**STNG**) | PLDI 2016 | https://homes.cs.washington.edu/~akcheung/papers/pldi16.html | Abstract |
| 24 | Jie Qiu, Colin Cai, Sahil Bhatia, Niranjan Hasabnis, Sanjit A. Seshia, Alvin Cheung. *Tenspiler: A Verified-Lifting-Based Compiler for Tensor Operations* | ECOOP 2024, LIPIcs 313, 32:1-32:28 | https://doi.org/10.4230/LIPIcs.ECOOP.2024.32 | Verified (arXiv HTML): verification sections |
| 25 | Sarita V. Adve, Mark D. Hill. *Weak Ordering: A New Definition* | ISCA 1990, pp. 2-14 | https://ftp1.cs.wisc.edu/markhill/Papers/isca90_drf0.pdf | Abstract (DOI listings disagree; cite by URL) |
| 26 | Rust Embedded. *The Embedonomicon: Direct Memory Access (DMA)* | Documentation | https://docs.rust-embedded.org/embedonomicon/dma.html | Search snippet only; **unverified detail** |

**Not found (search-bounded, 2026-10-09):** a peer-reviewed formal verifier for code issuing
asynchronous accelerator commands with tile- or tag-based waits *other than* the Cell DMA line
(14-16) and the AccelSync preprint (17). Nothing combines this with LLM-produced rewrites
checked against rewrite contracts, which is ticket 06's question.

*AI disclosure: this review was compiled by an AI agent (Claude) using web search and the
primary sources listed; every quoted sentence was read at its source.*
