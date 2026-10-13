# 06 — Library-call service family and indirect-call overhead

Created: 2026-10-12 01:10 ET
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately (01 confirms the call list)
**Spec:** `../spec.md` (C8, C9; seams 1 and 2)
**Code map:** `../notes/calls.md`

**Time estimate:** about a day.

## What to build

- A new calibration family "library call service" for `strlen`, the iostream calls (`ostream`
  put/flush/insert) and `ctype::_M_widen_init`, measured per call with paired receipts, modeled on the
  clock service. Record in the receipt that `flush` cost depends on where stdout goes (measure to a
  file, like the timed run) and that `_M_widen_init` is cached after its first call (the transfer
  rule is inferred; say so).
- `indirect-call`: a receipt for the call overhead only. The existing count proof keeps only
  `cost_accounting == opaque_callee` rows and so counts 0 indirect calls: add a proof that counts
  them, so the callee's work stays where it is defined.
- C9: any call still without a receipt stays `call_cost.<name>` unknown, never 0 s.

## Acceptance

- [x] Seam 2: the runner (test double timing) writes receipts that validate and that the binder admits.
- [x] Seam 1: a fixture with these calls is priced; removing one receipt leaves `call_cost.<name>` unknown.
- [x] Indirect-call count is non-zero on a fixture with indirect calls.

## Answer

Resolved 2026-10-12 01:24 ET on branch `cpud/06-library-calls`. Paths relative to `swdb-project/`.

**Known limitations (added 2026-10-12 ET, code review F2/F3/F4, branch `cpud/review-fixes`)**

- `indirect-call` is priced as call overhead only, at every site with that name. Characterize
  also names inline asm and calls to uncounted callees `indirect-call`, so their real work is
  missing from the estimate. t75 exposure: 1 candidate site (`DOBFS:178`), 0 in g16. Not fixed
  (a Characterize change would change counts); pinned by
  `test_every_indirect_call_site_is_priced_as_call_overhead_only`.
- The `ostream_insert` and `_M_insert<unsigned long>` rates include amortized `write(2)` drains
  (about 4–8 ns, inferred); `ostream_put` does not.
- A native `calibrate` run now refuses fixture caps (< 7 repetitions, < 0.05 s trials) up front.
- Details: `docs/reference/cpu-service-calibration.md`, section "Known limits of the 2026-10-12
  families".

**What exists now**

- Runner: `swdb cpu-service-calibrate --service-group library_call` →
  `swdb/cpu_library_call_calibration.py` (calibrate, count proof, native `validate`).
  Native receipts dispatch to it by `settings.group: library_call_v1` (`swdb/cpu_service_native.py`).
- Native source (shared timed/count body): `swdb/native/CpuLibraryCallWork.h`,
  `CpuLibraryCallTimer.cpp`, `CpuLibraryCallCount.cpp`.
- Seven paired services, each with `scope.event_abi` = the exact t75 name, so the binder's scalar
  path prices them with **no binder or estimator change**:

  | Service id | `event_abi` | Driver |
  |---|---|---|
  | `library.strlen` | `strlen` (16-byte string) | known length |
  | `library.ostream_put` | `_ZNSo3putEc` | no put |
  | `library.ostream_flush` | `_ZNSo5flushEv` (1 pending byte, one `write(2)`) | put only |
  | `library.ostream_insert` | `_ZSt16__ostream_insert…PKS3_l` (16 bytes) | no insert |
  | `library.ostream_insert_unsigned_long` | `_ZNSo9_M_insertImEERSoT_` (7 digits) | no insert |
  | `library.ctype_widen_init` | `_ZNKSt5ctypeIcE13_M_widen_initEv` (uncached) | one virtual `do_widen(range)`, no init |
  | `library.indirect_call` | `indirect-call` (overhead only) | same body inlined |

- Count proof (`swdb.cpu-library-call-count-proof.v1`): it accepts `indirect-call` rows (the clock
  proof's `opaque_callee` filter would count 0). Count driver runs op k for (k+1)·n iterations,
  n ∈ {3, 5}. For each op: exactly one site with (k+1)·n in the service run and 0 in the driver run.
  Every other uncovered call must have equal counts by name in both runs. Native admission
  requires the exact libstdc++ ABI list above.
- C9: unchanged estimator behavior, now tested: a call with no receipt stays `call_cost.<name>`.

**Tests** (`tests/test_cpu_library_call_calibration.py`, 4 tests, plus targeted
`test_cpu_service_calibration.py`, `test_cpu_service_binding.py`, `test_analytic_cpu_service.py`,
`test_cpu_openmp_calibration.py`): runner → receipt → import → bind (seam 2, LLVM 22);
bind → estimate prices all 7 t75 calls (7 994 ns hand total) and dropping the flush receipt leaves
exactly `call_cost._ZNSo5flushEv` (seam 1); synthetic native receipt admitted, and refused on a
libc++ ABI, a zero coefficient or an unpaired other call.

**Decisions and assumptions (inline, pre-approved autonomy)**

- **The t75 indirect call is the virtual `ctype<char>::do_widen` after the first `_M_widen_init`,
  not the `std::endl` pointer** (inferred from counts). `widen(c)` calls `do_widen` virtually only on
  the uncached path. In t75 the indirect count (1) matches widen_init (1), and DOBFS has 7 `endl`
  (put/flush ×7) with 0 indirect calls. So the widen_init driver subtracts one virtual dispatch,
  and `indirect-call` prices it once.
- **Finding:** `Characterize.cpp` reports inline asm as `indirect-call` (`getCalledFunction()` is
  null for `InlineAsm`). The library-call source therefore uses volatile globals, never `asm`.
  Other constructed sources (clock etc.) use `asm volatile`; their proofs filter `opaque_callee`
  so they are unaffected, but any characterization with inline asm will show `indirect-call`.
- `flush` and the stream calls go to `std::cout` (sync_with_stdio) with stdout reopened onto a
  regular file (`sink.out`), like the timed run's redirect. The sink is flushed and truncated
  between untimed 1 024-event batches, so buffered bytes from put/insert drain outside the window.
  Transfer to the app's buffer state is inferred (recorded in `scope.stream`).
- `_M_widen_init` is timed uncached (cache flag cleared each iteration). The app calls it once,
  on first use; warm-cache versus first-call state is labeled inferred in `scope.facet_state`.
- String lengths (16 B) and the 7-digit integer are constructed; application lengths stay
  unmeasured (`length_transfer: inferred`). Scalar selectors ignore `unknown_lengths`.
- The scalar `indirect-call` selector prices every executed indirect site in allowlisted counts
  (acceptable for T1 serial, per `notes/calls.md`).
- On the Mac (libc++) the fixture records the observed libc++ names, and op 5 uses
  `std::locale::classic()` as a stand-in. Only the native validator pins the libstdc++ names.
  The libstdc++ path was compiled and run with `g++-16` locally (timer runs; widen_init about 18 ns uncached).
- Red/green note: seam-1 tests passed on first run because binder and estimator already handled
  scalar ABIs (as `notes/calls.md` predicted); they now guard C9.

**Ticket-07 command (mbit10, one lane, after count admission)** — from a clean pushed checkout's
`swdb-project/`, with `LIBCALL_RAW` a new `/data/yanruj/EvolveSWDB_runs/` root holding a copied
`records/` store, entered through `socket_lane.sh`:

```sh
export OMP_NUM_THREADS=1 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export LD_LIBRARY_PATH=/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/lib/x86_64-unknown-linux-gnu
python3 -m swdb cpu-service-calibrate --service-group library_call --records "$LIBCALL_RAW/records" --output "$LIBCALL_RAW/count" --count-only --machine mbit10 --lane mbit10-evaluation-node0 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --max-wall-s 900 --format json
python3 -m swdb cpu-service-calibrate --service-group library_call --records "$LIBCALL_RAW/records" --output "$LIBCALL_RAW/elapsed" --machine mbit10 --lane mbit10-evaluation-node0 --llvm-bin /data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64/bin --toolchain-flag=--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 --repetitions 7 --min-trial-s .05 --max-wall-s 900 --format json
python3 -m swdb import-cpu-service-calibration --records "$LIBCALL_RAW/records" --receipt "$LIBCALL_RAW/elapsed/receipt.json" --id mbit10.cpu.lanl20261006.service.library-call.a1 --format json
```

Expect 7 services × (pilot + 7 trials) at ≥ 0.05 s each: about 1–2 min of lane time. The count
proof is 4 characterize runs. Any nonpositive paired rate stays null (unknown), never 0.
Then pass `--calibration mbit10.cpu.lanl20261006.service.library-call.a1` to the ticket-08 bind.
