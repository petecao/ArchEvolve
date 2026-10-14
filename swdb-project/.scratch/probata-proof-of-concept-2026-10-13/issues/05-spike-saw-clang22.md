# 05 — Spike (a): SAW on clang 22 bitcode

Created: 2026-10-13 22:17 ET
**Type:** slice
**Status:** ready-for-agent
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

- [ ] SAW 1.6 (installed by 03) loads the fixture's bitcode, compiled by clang++ 22.1.8 with debug
      information, with no parse error. Recorded: SAW version, clang version and flags, solver,
      bitcode sha256. (Debug information matters: the SAW translator maps fields through it, map
      [16](../../formal-verification-2026-10-09/issues/16-formal-half-language.md) item 3.)
- [ ] The ghost state is a fixed-size array indexed by tile, the shape map 16 item 10 needs. Only
      the specs used as `llvm_verify` overrides for the issue and wait calls change it.
- [ ] Safe variant (the wait comes before the read): SAW returns proven. Wall time and peak RSS
      recorded.
- [ ] Seeded bug (the covering wait removed): SAW refutes it with a counterexample. The check that
      fails is the ghost-state check at the read, not anything else (glossary: negative control).
- [ ] Every failed or unexpected run is root-caused and named with a failure class from the
      design's list ("Verifier lineup and order": map
      [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) item 9, extended by map
      26 item 10 and S3: parse error, unsupported construct, timeout, out of memory, solver error,
      tool crash, ghost capacity, ...). None is left unclassified.
- [ ] The Answer records the decision in one line: "SAW 1.6 is the bounded verifier" or "crux-llvm
      0.12 is the bounded verifier". It cites the evidence and, for crux-llvm, the failure that
      forced it.
- [ ] Fallback path only: the same fixture and seeded bug run under crux-llvm 0.12 on the C++
      bitcode, with hand stubs as summaries and the ghost state as C globals (map 16 item 10). The
      safe variant proves; the bug is refuted with a counterexample.
- [ ] Logs are cited by path and sha256 in the Mac runs folder; specs, stubs and the fixture by
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
