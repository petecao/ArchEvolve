# 05 — Spike (a): SAW on clang 22 bitcode

Created: 2026-10-13 22:17 ET
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Proof-of-concept plan", A1 row (a); "Verifier lineup and order"; "DX100 proof semantics", encoding bullet; "Further Notes", risk table); decisions: [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md), [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md), [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md), [26](../../formal-verification-2026-10-09/issues/26-proof-records.md), [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md)
**Time estimate:** about 2-3 days, inside the 2-week box

**What to build:** A throwaway test of the plan's first risk: can SAW 1.6, the bounded verifier, read
bitcode from the pinned clang 22.1.8 and keep ghost state? Agent-written stubs and a small fixture,
written for this spike, stand in for a DX100 command. An override for an issue call marks a tile
unready in ghost state. An override for a wait call marks it ready. A read checks the ghost state.
The safe variant must prove, and a seeded bug must be refuted with a counterexample. If SAW cannot
do this, crux-llvm becomes the bounded verifier, and the decision is recorded for 09 — Spike verdict
and every later ticket.

## Acceptance

- [x] SAW 1.6 (installed by 03) loads the fixture's bitcode, compiled by clang++ 22.1.8 with debug
      information, with no parse error. Recorded: SAW version, clang version and flags, solver,
      bitcode sha256. (Debug information matters: the SAW translator maps fields through it, map
      [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) item 3.)
- [x] The ghost state is a fixed-size array indexed by tile, the shape map 16 item 10 needs. Only
      the specs used as `llvm_verify` overrides for the issue and wait calls change it.
- [x] Safe variant (the wait comes before the read): SAW returns proven. Wall time and peak RSS
      recorded.
- [x] Seeded bug (the covering wait removed): SAW refutes it with a counterexample. The check that
      fails is the ghost-state check at the read, not anything else (glossary: negative control).
- [x] Every failed or unexpected run is root-caused and named with a failure class from the
      design's list ("Verifier lineup and order": map
      [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) item 9, extended by map
      26 item 10 and S3: parse error, unsupported construct, timeout, out of memory, solver error,
      tool crash, ghost capacity, ...). None is left unclassified.
- [x] The Answer records the decision in one line: "SAW 1.6 is the bounded verifier" or "crux-llvm
      0.12 is the bounded verifier". It cites the evidence and, for crux-llvm, the failure that
      forced it.
- [ ] Not applicable (SAW passed; fallback not run). Fallback path only: the same fixture and seeded bug run under crux-llvm 0.12 on the C++
      bitcode, with hand stubs as summaries and the ghost state as C globals (map 16 item 10). The
      safe variant proves; the bug is refuted with a counterexample.
- [x] Logs are cited by path and sha256 in the Mac runs folder; specs, stubs and the fixture by
      path and sha256 in the prototype folder. Verifier scratch is deleted when each job ends.

## Notes

- **Not in this ticket:** 03 — New verifiers on the Mac (installs SAW; proves map 07's smoke
  program); 06 — Spike (b): 2 lanes under 15 minutes (real DX100 code at 2 lanes); 09 — Spike verdict
  (the stop rule); 22 — SAW adapter and SAWScript translator (generated specs, the real adapter);
  23 — C-stub translator, fallbacks and check mode (generated stubs, real fallbacks); 27 — Proof
  semantics for the BFS read-offload calls (the real ghost hazard state).
- **Not tested here:** SAW's float mode. Bounded runs on floats use crux-llvm `-f real` until it is
  confirmed (map 11 item 6).
- **Throwaway.** Nothing here becomes A2 code. A2's exit later shows that generated artifacts
  reproduce this verdict (33 — Minimum-bounds script and A2 exit).
- Assumption (not decided in the map): "cannot" means SAW 1.6 fails to parse the bitcode, cannot keep
  ghost state across overrides, or does not get the pair (safe variant proven, seeded bug refuted)
  within this ticket's 2-3 days. Then the fallback runs.
- Assumption (not decided in the map): if 03 already sent SAW to its fallback (SAW did not run at
  all), this ticket skips the SAW runs, runs only the fallback path, and records crux-llvm with 03's
  cause.
- Assumption (not decided in the map): the fixture is C++ written for this spike, not GAPBS or DX100
  code. It uses no standard containers, since SAW bundles no libc++ bitcode (map 11 research).
- Assumption (not decided in the map): the ghost state is an array, not a scalar. A scalar-only
  success would leave map 16 item 10's encoding untested.
- Assumption (not decided in the map): if crux-llvm also fails, this ticket records it and 09 takes
  it to Yan-Ru. Map 11 item 2's later fallbacks (crux-llvm on the C lowering, then CBMC 6.11) are
  not tried here.
- Assumption (not decided in the map): the verdicts go in this ticket's Answer with evidence paths,
  not as `proof` records. That kind arrives with 04 — Proof record tracer, which this ticket does
  not wait for.
- Assumption (not decided in the map): spike code lives in this effort's `prototype/` folder, as the
  map kept its prototypes (map 07, 08). Logs go to a Mac runs folder outside the repo, host `mac`
  (map 26 item 5). The map names no path for it: pick one, and record its path, size budget and
  readers before the first run (LR-06).
- **Risks:**
  - SAW's README says it was tested only up to LLVM 20. Its bitcode parser adds LLVM 21 and 22
    metadata, untested here (map 11 research).
  - crux-llvm supports LLVM 3.6-21. On clang 22 bitcode it warns about debug metadata, but map
    [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md) found its verdicts
    right. Compile to bitcode first and run with `--no-compile`; a stale `crux-build/` folder is
    silently reused.
- **Mac rules:** one real verifier job at a time, under the ~8 GB RSS watchdog. Keep at least 50 GB
  free. After any Homebrew change, check that LLVM 22 still works for the analytic evaluator
  (`clang --version` reports 22.1.8).

## Answer

2026-10-14 01:25 ET. **Decision: SAW 1.6 is the bounded verifier.** On clang++ 22.1.8 bitcode
with debug information, SAW 1.6 proves the safe variant and refutes the seeded bug with a
counterexample at the read's ghost-state check. The fallback (crux-llvm 0.12) was not needed and
not run. Time used: about 20 minutes of the 2-3 day box.

**What ran.** Prototype: [`../prototype/05-saw-ghost/`](../prototype/05-saw-ghost/).
`run_spike.sh` builds both variants, runs SAW three times through
`/tmp/claude/probata-tools/verifier_run.py` (lock, 8 GB cap), deletes each job's scratch folder,
and checks the verdicts (7/7 PASS, exit 0).

| File | sha256 |
|---|---|
| `fixture.cpp` (C++ fixture; three declared-only `dx100::` calls; `-DBUGGY` drops the covering wait) | `1397f33c65201284b2b43383682208ccead2b9721f7d1a0f27ef6e8bd0a32a01` |
| `spike.saw` (issue / wait / read specs as `llvm_unsafe_assume_spec` overrides; kernel spec) | `2afeec2262fdb7e8b38fcebcea87d2295485dba6e73ae5f114f1b3e844ce3b78` |
| `run_spike.sh` (runner and verdict check) | `1098f9c5895d68077948821ed9408836658ee8ff14de6ffb749ca40af91e2591` |

**Recorded setup.** SAW `1.6 (68eed5f release-1.6)`; solver: SAW's bundled Z3 4.8.14 (SBV->Z3,
bundled `bin/` first on PATH); Homebrew clang 22.1.8,
`clang++ -std=c++17 -c -emit-llvm -g -O0 [-DBUGGY] fixture.cpp`. Bitcode sha256: safe
`ab4b526adbb869a7c8457ed34bdb5b29ea9e2ee53c1cd0f558be1af636f5b087`, buggy
`9bb5dbe232683e75607470e232b653c7e4f0cb3d069bb8a14439dcb23e794002`. SAW loaded both with no
parse error and no warning.

**Ghost state.** `pending`, a Cryptol `[8][8]` array (8 tiles, one byte each; nonzero = the tile
has an uncovered writer): map 16 item 10's shape, reduced to one field. Only the issue override
(`update g t 1`) and the wait override (`update g t 0`) change it. The read override leaves it
unchanged and checks `g @ t == 0`. The issue spec reads the `Command` fields by name with
`llvm_field`, so field mapping through debug information is exercised. The fixture keeps tile `a`
unready while it reads tile `b`, so a single "something pending" flag would reject the safe variant;
the per-tile array is needed.

**Results** (logs in `/tmp/claude/probata-runs/t05/`, each with `.summary.json`):

| Run | Verdict | Wall | Peak RSS | Log sha256 |
|---|---|---|---|---|
| `saw_safe.log` | `Proof succeeded! _Z6kerneliij` | 0.47 s | 157.1 MB (getrusage; watchdog sample 175.6 MB incl. wrapper) | `2ee3b5a17af3e13fa61e591583e31235a4a0513238ead40445f65ea11ce814b9` |
| `saw_buggy.log` | `Proof failed.`: the one failed subgoal is at `fixture.cpp:39:43` (the `dx100::read(b, i)` call), `No override specification applies for _ZN5dx1004readEij`; counterexample `a: 6, b: 1` (with `g0`) | 0.47 s | 157.2 MB | `5e7f66eaf94fb4288903e53670ac9b67f1420c4dfbc52951dac3db37edf17e2e` |
| `saw_control.log` (buggy bitcode, ghost check replaced by `True`) | `Proof succeeded!` | 0.48 s | 157.0 MB | `2d6f072f4280bb51cc55b0740ee272a924ecd0a0f9b6f33cb12875d7224f331d` |

The read override has two preconditions: `t < 8` and the ghost check. The counterexample has
`b = 1`, so `t < 8` holds. The control run removes only the ghost check, and the buggy bitcode then
proves. So the ghost-state check at the read is the only check that fails (negative control).
SAW's message does not name the failed precondition, so this attribution rests on the control
run, not on the message text.

**Failed and unexpected runs, root-caused** (logs `exp_*.log` in the same folder; experiment
scratch deleted):

1. **`llvm_field` on a struct inside a namespace** (first fixture had `dx100::Command`):
   `Unable to resolve struct field name: kind ... Could not resolve setup value debug information
   into a struct type`. Cause: SAW 1.6 does not map the LLVM name `struct.dx100::Command` to the
   debug type `Command` in namespace `dx100`. The same struct at global scope resolves (`exp_A`).
   With `llvm_elem` (field index, no debug information) the namespaced fixture proves (`exp_ns_elem`).
   Without `-g`, `llvm_field` fails the same way (`exp_nodebug_field`), so field names really
   come from debug information. **Class: unsupported construct.** Handler: ticket 22's translator
   reads field indices from debug information itself and emits `llvm_elem` for namespaced
   types (or keeps `llvm_field` only for global-scope types). The fixture's `Command` now sits
   at global scope. Logs: `exp_ns_field` `f84a8b6d…f63f`, `exp_ns_elem` `a6868b8f…29d5`,
   `exp_nodebug_field` `637a75f8…1798`, `exp_A_global_struct` `0a14a462…9eca`.
2. **Kernel spec without `llvm_return`** (`exp_A`): `Missing return value specification for
   function with non-void return type`. Cause: SAW requires a return spec for a non-void
   function under verification; the spike's spec omitted it. A fresh post-state variable
   (`ret`) fixes it. **Class: unsupported construct** (spec side). Handler: the translator
   always emits a return spec.
3. **False refutation of the safe variant** (`exp_B_verbose`, `exp_C_scalar_mask`): the read
   spec wrote `llvm_precond {{ g @ t == 0 }}` **after** `llvm_ghost_value pending g`. SAW 1.6
   then left `g` unbound when it checked the precondition. Evidence: the counterexample names
   the read override's own variable (`read_g`), not the kernel's start state `g0`. Changing the
   ghost to a scalar bitmask fails the same way (`exp_C`), so arrays are not the cause. Replacing
   the check by `True` proves (`exp_D_array_nocheck`). Writing the precondition **before** the
   ghost line proves the safe variant (`exp_E_precond_first`) and still refutes the bug with a
   counterexample over `g0` (`exp_E_precond_first_buggy`). **Class: unsupported construct**
   (SAW 1.6 does not bind a ghost-matched variable for a precondition written after the ghost
   line). Handler: ticket 22's translator emits every precondition that names a ghost-bound
   variable before its `llvm_ghost_value` line, plus a regression test. Logs: `exp_B_verbose`
   `aeb42959…c130`, `exp_C_scalar_mask` `166457ed…a2eb`, `exp_D_array_nocheck`
   `6c9ab3ba…36bf5`, `exp_E_precond_first` `f8d07292…d344f`, `exp_E_precond_first_buggy`
   `bfe99dc9…1417`.
4. `/usr/bin/time -l` (used to measure peak RSS) exits 1 in the Claude sandbox
   (`sysctl kern.clockrate: Operation not permitted`) after SAW finished. **Class: tool crash**
   (of the measuring wrapper, not SAW). Handler: `run_spike.sh` measures peak RSS with
   `getrusage(RUSAGE_CHILDREN)` instead.

**Why item 3 matters.** A spec-encoding defect produced a refutation with a counterexample
on a correct program, not a "not proven". Map 11 trusts a bounded refutation and sends it to
counterexample-guided repair (ticket 13). A translator bug of this kind would send correct
candidates to repair. The design's failure-class list has no class for "the tool or spec
encoding produced a spurious refutation"; I used "unsupported construct".

Runs folder (LR-06): `/tmp/claude/probata-runs/t05/` on host `mac`, budget 50 MB, used 128 KB.
Readers: this ticket and 09. `README.txt` there records this.

Assumption: the ghost tracks one field per tile (uncovered writer). Map 16 item 10's full record
(owner, writer, readers bitmask; per-register and per-thread tables) is ticket 27's work. One
array field already tests what this spike asks: an array ghost kept across overrides.
Assumption: the issue override does not require the destination tile to be ready. The device
stalls rather than fails (map 16 item 10, `IF.cc:193-212`), so a stall is not a ghost-check
failure here.
Assumption: the kernel spec does not constrain the final ghost state. If it did, the seeded bug
would fail a second check (tile `b` still unready at exit), and the negative control would no
longer isolate the read check.
Assumption: "proven" means SAW's `Proof succeeded!` at exit 0 for all 32-bit `a`, `b`, `base` with
`a, b < 8`, `a != b` and any start ghost state; the read loop has 4 iterations, so no unwinding
bound is involved.
