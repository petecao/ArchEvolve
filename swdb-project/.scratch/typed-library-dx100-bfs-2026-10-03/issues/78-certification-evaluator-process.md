# 78 — Certify 1.5 and library-operation command 1.2: record-keeping in a separate evaluator process

Created: 2026-10-05 15:50 ET (scope decided by Yan-Ru 2026-10-05; work started 14:40 ET)
Updated: 2026-10-05 16:10 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** —
**Spec:** `../spec.md` (certification command, "Evaluator process" bullet); [70](70-certification-isolation.md), [75](75-certify-a8-frontier-staging.md), [76](76-attributed-blinded-certification.md), [77](77-library-operation-certification-records.md)

**What to build:** an engineering refactor that moves certification record-keeping out of the
candidate's process into a trusted evaluator process, and a measurement of what that costs.

## Scope (Yan-Ru, 2026-10-05)

- In scope: the process split for every certify path that runs candidate code (DX100 candidate
  artifacts, ticket 75's native-CPU contracts, library operations), the overhead measurement on the
  matrix graphs, and the correctness regression.
- **Out of scope:** OS sandboxing or confinement of the candidate process (syscall filters, seccomp,
  ptrace monitors, filesystem or network restriction), and any adversarial or exploit-style test.
  Neither was designed or written here.
- Gate: prototype on ticket 20's certification first; extend to all paths only if the overhead stays
  under 5x wall time per certification.

## Acceptance

- [x] A trusted evaluator process owns the record writer, the run plan, the fault logic, the
  frontier ledger, the strict model's state and the witness counters; every record is written by it.
- [x] The candidate runs as its child and reaches the evaluator only through the shared arena and
  request slots; it holds no record descriptor and no plan.
- [x] Overhead measured against certify 1.4 on every matrix graph; under 5x.
- [x] Certify 1.5 and library-operation 1.2 are the defaults; 1.3/1.4 and 1.0/1.1 stay selectable.
- [x] Ticket 20, ticket 42, both a7 bests, ticket 75's native contract and the five library
  operations certify under the new versions with every control rejected by its own named check.
- [x] Residuals of tickets 76 and 77 mapped: addressed or remaining.

## Answer

Resolved 2026-10-05 16:10 ET by the agent. Scope decided by Yan-Ru 2026-10-05; design choices
inside it agent-decided under Yan-Ru's delegation, revisable.

**Decision: certify 1.5 (candidate artifacts, DX100 and native-CPU) and library-operation command
1.2 are the defaults.** 1.3/1.4 (`--command-version`) and 1.0/1.1 stay selectable and unchanged
apart from neutral record-file names (below); their records keep their meaning. Code:
`swdb/certification_process.py`, `library/dx100/certification/v1_5/`,
`library/native/certification/v1_5/`, `library/library_operations/certification/v1_2/`,
`swdb/library_operation_blinding.py`.

### Architecture

Two processes per run, one shared memory object (`v1_5/arena.hpp`) mapped at the same virtual
address (0x200000000000, 16 GiB virtual, pages on first touch) in both:

1. **Evaluator (trusted).** Linked from `v1_5/evaluator.cc` + the shared core
   `evaluator_core.inc` + certify 1.4's `record.cc` and `seams.cc`, **byte-unchanged**, + the
   unchanged strict layer. `evaluator_context.hpp` (forced include) redirects only two things:
   `omp_in_parallel/omp_get_thread_num/omp_get_num_threads` read the requesting thread's identity,
   and `std::_Exit` also kills the candidate. The evaluator holds the record descriptor and plan
   (read before `main`), the fault logic, the ledger, the strict model's device tiles, registers,
   operation graph and regions, and the witness counters. It records the source from its own
   arguments and reads the returned vector from the arena at FINISH.
2. **Candidate (child).** The candidate object + `client.cc` only. `client_core.inc` maps the arena
   (descriptor 3, closed after mapping), replaces global `operator new/delete` so the C++ heap is
   in the arena, and forwards every 1.4 seam call and every strict-layer call
   (`v1_5/client/MAA_functional.hpp`) as a request on the thread's slot (spin, then yield, then
   20 µs sleep; about 120 ns per round trip measured). It exits if its evaluator is gone.
   The 1.4 prelude is reused unchanged; 1.5 adds one hook (`__dxc_accelerated_chunk` is counted by
   the evaluator).

Validated: the shared arena is the right route. The strict model reads candidate arrays through
pointers the candidate passes, and every claim is a compare-and-swap on candidate memory; with the
heap in the arena, the evaluator does both on the same addresses. Each tile's CPU-visible buffer is
a window in the arena that the evaluator keeps equal to the model's buffer (rewritten when a tile's
producer, its coverage or the buffer changes; pulled before `set_tile_size`).

- **Native-CPU (ticket 75's path):** the profile's pinned 1.4 prelude, record writer and seams run
  unchanged (the profile and contract are not edited); `native/certification/v1_5/{client,evaluator}.cc`
  carry the slide seam's queue bounds by value.
- **Library operations 1.2:** `v1_2/evaluator.cc` (from 1.1's driver) + 1.1's `record.cc` read the
  case, place operands and the canary in the arena and keep private input copies. The candidate
  binary is the unit + `runner.cc`: it copies operands into its own heap (sanitized builds keep
  redzones), calls once, copies output and inputs back. Frame check, driver faults and records are
  the evaluator's. The 1.1 judge, attribution and order are unchanged.

**Semantic differences (1.5 only).** A DX100 memory region must lie in the arena heap (else
`memory_region_registration`). A 4-byte claim outside the heap runs locally, unrecorded, and no
fault acts on it. Memory from `malloc` (not `operator new`) is private to the candidate.

**Ticket 75 review items (coordinator, own commit 93a2a94).** (1) Record files are named
`run-<nonce>.record` for DX100 1.4 and all 1.5 runs (native 1.4 already was). (2) Ticket 75's
native rule (only `#pragma omp` authored) would refuse ticket 20, ticket 42 and both a7 bests,
which author knob defaults and a `SWDB_DXC_DIAGNOSTIC` block. The 1.5 DX100 form keeps its intent:
authored `#if/#ifdef/#ifndef/#elif`, `defined`, and `#define/#undef` of a seam macro are refused,
except `#ifndef M`/`#define M`/`#endif` for a contract knob macro and `#ifdef SWDB_DXC_DIAGNOSTIC`.
It refuses a7 `it5.kronecker.a2` and `it6.kronecker.a0` (already scan-refused) and passes the four
regression inputs. 1.4's scan is unchanged.

### Overhead (Mac arm64, g++-16, one run at a time)

Per run: the same certified binaries and graphs, 10 alternating runs per positive cell, median wall
time of the whole run (process start included). Evidence:
[`evaluation/certification-evaluator-process-2026-10-05.json`](../evaluation/certification-evaluator-process-2026-10-05.json).

| Graph | Tile | BFS 1.4 s | BFS 1.5 s | ratio | BC 1.4 s | BC 1.5 s | ratio |
|---|---|---|---|---|---|---|---|
| kronecker-10 | 16384 | 0.012 | 0.034 | 2.92 | 0.012 | 0.035 | 2.92 |
| kronecker-14 | 16384 | 0.032 | 0.053 | 1.66 | 0.042 | 0.087 | 2.09 |
| kronecker-16 | 16384 | 0.099 | 0.117 | 1.18 | 0.131 | 0.238 | 1.82 |
| uniform-14 | 16384 | 0.037 | 0.058 | 1.56 | 0.046 | 0.085 | 1.86 |
| two-level (21k) | 16384 | 0.016 | 0.043 | 2.66 | 0.020 | 0.052 | 2.66 |
| kronecker-10 | 1024 | 0.011 | 0.032 | 2.96 | 0.012 | 0.034 | 2.90 |
| kronecker-14 | 1024 | 0.035 | 0.059 | 1.70 | 0.040 | 0.082 | 2.06 |
| kronecker-16 | 1024 | 0.127 | 0.162 | 1.27 | 0.140 | 0.217 | 1.55 |
| uniform-14 | 1024 | 0.045 | 0.073 | 1.61 | 0.051 | 0.091 | 1.80 |
| two-level (21k) | 1024 | 0.016 | 0.045 | 2.84 | 0.018 | 0.051 | 2.84 |

About 20 ms per run is fixed (arena creation, fork/exec, server threads); the rest grows with
requests. Whole certifications (builds dominate):

| Input | 1.4 (1.1) s | 1.5 (1.2) s | ratio |
|---|---|---|---|
| Ticket 20 | 20.1 | 21.1 | 1.05 |
| Ticket 42 (BC) | 38.2 | 38.3 | 1.00 |
| a7 `it4.kronecker.a2` | 17.6 | 20.5 | 1.16 |
| a7 `it8.uniform_random.a1` | 18.2 | 20.0 | 1.10 |
| Ticket 75 native contract | 13.2 | 15.7 | 1.19 |
| Five library operations | 9.1–13.3 | 11.6–16.0 | 1.20–1.27 |

Every ratio is under the 5x gate (worst per run 2.96x, worst per certification 1.27x), so the split
was extended to all paths.

### Regression (code commit d1f23cb, sources_sha256 7e93615930dc…; Mac, scratch stores, not committed)

| Input | 1.5 / 1.2 certification | Matrix | Controls rejected | Attributed |
|---|---|---|---|---|
| Ticket 20 | `certification.c806e2af25c6472a95aaa44b398a9015` | 10/10 | 20/20 | 16/16 |
| Ticket 42 (BC) | `certification.b77acdac80a942a5bbe7e8a2bfed1436` | 10/10 | 28/28 | 16/16 |
| a7 best kronecker `it4.kronecker.a2` | `certification.a8418ae17aae4783847dffa18ab34bb6` | 10/10 | 20/20 | 16/16 |
| a7 best uniform `it8.uniform_random.a1` | `certification.8bed7a05d27e423f8df92af6ae63c9a1` | 10/10 | 20/20 | 16/16 |
| Ticket 75 native contract | `certification.41063cbaef894c4e8a55c0dc1d001b97` | 22/22 | 8/8 | 8/8 |
| `operation.pack_executor` | `certification.e144dcdd5402409a91784d1fda31d7f9` | 2/2 + probe | 5/5 | 5/5 |
| `operation.update_binning_executor` | `certification.64f7702f260346b68b85c5e58d6a1479` | 2/2 | 5/5 | 5/5 |
| `operation.vertex_relabel_executor` | `certification.8c65dfbfd4cd4184a04a53b9915949e2` | 2/2 | 5/5 | 5/5 |
| `operation.regroup_executor` | `certification.42e34fbd8e6b443aa50f8e66fc7d4aa8` | 2/2 | 5/5 | 5/5 |
| `operation.gather_staging_executor` | `certification.bfaaa895243146e7871c2ab411778b96` | 2/2 | 5/5 | 5/5 |

All `certified`. For each DX100 and native input the set of (control, named checks, attribution
rule) equals 1.4's run on the same tree at the same commit; every library operation's control
outcomes equal 1.1's. One candidate binary and one evaluator binary per tile size or build.

Tests: `tests/test_certification_process.py` (17: directive rule, record names, flag order, ticket 20
and the native contract under 1.5, the candidate binary refusing to run without its evaluator) and a
1.2 test in `tests/test_library_operation_blinding.py`. Suites (Mac): certification (BC, blinding,
controls, feedback, isolation, legality, native, process, typed, kernel plug-ins) 306 passed, 1
failed then fixed (it pinned the default version 1.4); Extensa, library index, submit, typed
library and library-operation suites 242 passed, 11 failed on the first run (10 from the arena
header missing in fixture library copies, fixed in d1f23cb, then 73 passed; 1 index-staleness test
passes alone, likely files edited during the run).

### Residuals of tickets 76 and 77

| Residual | Status under 1.5 / 1.2 |
|---|---|
| 76 R1 / 77 R1: candidate shares the address space with the record writer, plan and seams | **Addressed in part.** The record descriptor, plan, fault state, ledger, strict-model state, witness counters and (library operations) the input copies and frame check now live only in the evaluator; the candidate holds no evaluator descriptor and its environment has no certification variable. **Remains:** the arena is shared and writable by the candidate (heap allocator header, other threads' request slots, tile windows), each request's thread identity is the candidate's own claim, and the candidate process is not confined (it can use any system call and read or write the run folder by path) — confinement is out of scope by decision. |
| 76 R2: same-thread probe then amplify (thread-attributed faults, dropped_continuation) | **Remains.** Faults behave as in 1.4 and are still observable through seam behavior; no data-flow attribution was added. The evaluator now serves every DX100 operation, which is where taint from faulted tiles would have to start, but tile contents are read by the candidate directly from the arena, unobserved. |
| 76 R3: coverage (gather-from-claimed-array met by a probe gather) | **Remains** unchanged. |
| 76 R4: recognition of the finite certification graphs | **Remains**, out of scope (ADR 0008). |
| 76: a7 trees refused by the scan | Unchanged; the 1.5 directive rule also refuses them. |
| 77: transient input writes undone before return | **Remains.** The runner's operand copies are ordinary memory; a write undone before return is unseen. Mapping inputs read-only would close it. |
| 77: probe cell written by trusted probe code in the candidate's process | **Remains** unchanged (the probe cell still runs the 1.0 probe build). |
| 75 (native): the offsets hook inside DOBFS | Unchanged; its seam now runs in the evaluator. |
| Calibration and lowering certification read printed lines | Unchanged (trusted code only, ticket 76). |

New in 1.5: a DX100 region outside the arena heap is refused; a 4-byte claim outside the heap
runs locally, unrecorded and unfaulted; `malloc` memory is invisible to the evaluator.
