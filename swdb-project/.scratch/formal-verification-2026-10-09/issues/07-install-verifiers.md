# 07 — Install the shortlisted verifiers on the Mac

Created: 2026-10-09
Updated: 2026-10-11 14:55 ET (resolved)
**Type:** task
**Status:** resolved
**Blocked by:** 02
**Map:** `../map.md`

## Question

Install the verifiers shortlisted in 02 on the Mac (Homebrew or prebuilt binaries; nothing that
needs sudo), run a one-assertion smoke check with each, and record versions, install paths and
disk used. Keep at least 50 GB free.

Done when each shortlisted tool runs, or its failure is recorded with the cause.

## Comments

- 2026-10-09: shortlist from 02: ESBMC 8.5 (bounded and k-induction), Frama-C/WP 33.0 with RPP
  0.0.4 (unbounded; C port), crux-llvm 0.12 (optional). VerCors 2.4.0 waits for the concurrency
  phase. Frama-C installs through opam, which can take several GB; check free disk first.

## Answer

2026-10-11 14:55 ET. **All four shortlisted verifiers run on the Mac.** Each one passes a safe
smoke program and does not pass a seeded bug. Smoke files and logs:
[`../prototype/07-smoke/`](../prototype/07-smoke/). Free disk after: 119 GiB.

| Tool | Version | Install path | Safe program | Seeded bug (`-DBUGGY`) | Time | Disk |
|---|---|---|---|---|---|---|
| ESBMC | 8.5.0 (aarch64 macos) | `/opt/homebrew/bin/esbmc` (brew) | `VERIFICATION SUCCESSFUL` | `VERIFICATION FAILED`, `y != 42` | 0.3 s | 27 MB + deps |
| CBMC | 6.11.0 | `/opt/homebrew/bin/cbmc` (brew) | `VERIFICATION SUCCESSFUL` | `VERIFICATION FAILED` | <1 s | 159 MB |
| crux-llvm | 0.12 (Crux 0.9) | `~/opt/verifiers/crux-llvm-0.12/crux-llvm-0.12-macos-15-ARM64/bin/crux-llvm` (release tarball, SHA-256 `01d1b3e4…1f71`) | `Overall status: Valid`, 2/2 goals | `Invalid`, counterexample `x = 41` | 0.05 s / 0.5 s | 232 MB |
| Frama-C/WP | 33.0 Arsenic, Why3 1.8.2, Alt-Ergo 2.6.4 | opam switch `framac-33` (OCaml 5.3.0) in `~/.opam` | 11/11 goals proved (a loop invariant, so unbounded) | 10/11; the false assertion times out | 0.3 s / 10.7 s | `~/.opam` 1.2 GB |
| RPP | 0.0.4 | same switch | relational wrapper check proved | wrapper check times out (not proved) | 10.8 s | in the above |

ESBMC's extra brew dependencies: `llvm@22` 22.1.8 (1.5 GB), boost (380 MB), z3 5.1.0, bitwuzla,
fmt, yaml-cpp. opam added `rsync`, `popt` and `xxhash`; the Frama-C build added `zlib` (brew).

**Facts later tickets depend on:**

- **Activate Frama-C:** `eval $(opam env --switch=framac-33 --set-switch)`. `opam init` ran with
  `--no-setup`, so no shell startup file was changed. `why3 config detect` wrote `~/.why3.conf`
  and found Alt-Ergo 2.6.4, CVC5 1.2.1 and Z3 5.1.0.
- **crux-llvm and clang 22:** crux supports LLVM 3.6–21. Given a `.cpp`, it fails at link time,
  because it ships `libc++` bitcode only for LLVM 3.6.2 and 7.1.0. What works: compile with
  `clang++ -c -emit-llvm -g -I<crux>/c-src/includes`, then run `crux-llvm --no-compile
  --solver=z3 --output-directory=<dir> <abs path>.bc`. It warns about LLVM 22 debug-metadata
  records, but the verdicts were right. C++ that needs `libc++` (for example `std::vector`)
  will need LLVM ≤ 21 or hand-written overrides. Two traps: `-d` is verbosity, not the output
  folder, and a stale `crux-build/` folder is silently reused.
- **WP never says "false" here.** A deductive prover reports the seeded bug as `Timeout`, not as
  refuted. Per ticket 04, "not proved" is never evidence either way. Counterexamples must come
  from the bounded tools.
- **RPP workflow:** `frama-c -rpp f.c -then-last -wp`. With `-then` instead of `-then-last`, WP
  runs on the original project and proves nothing relational, a vacuous pass. RPP needs
  `assigns \result \from <formals>` to accept `\callpure`. The generated
  `Relational_lemma` always times out, because it is over an abstract logic function. The
  wrapper's `check Rpp` is the goal that decides.
- **WP cache:** results are cached in a `.frama-c/` session folder in the working directory.
  The log marks them `(Cached)`. Use `-wp-cache none` for timing runs.

**Side effects on the Mac:**

- Homebrew updated itself from 6.0.10 to 7.0.9, because the old version could not pour the new
  `llvm@22` bottle. Brew also upgraded `z3` (4.16.0 → 5.1.0), `python@3.14` (3.14.6 →
  3.14.8_2; the old keg was kept), `xz`, `openssl@4`, `readline`, `sqlite` and
  `ca-certificates`, and reinstalled `pkgconf`.
- **The z3 upgrade broke the existing `llvm` 22.1.8 keg**, the one `swdb/analytic.py` requires.
  Its `libLLVM.dylib` links `libz3.4.16.dylib`. Repair: copied the retained
  `Cellar/z3/4.16.0/lib/libz3.4.16.dylib` into `Cellar/z3/5.1.0/lib/` (byte-identical, SHA-256
  `227985ce…70d1`, signature valid). `clang++ --version` reports 22.1.8 again, and
  `tests/test_openmp_call_projection.py` passes (10 tests). The repair is lost at the next z3
  upgrade or reinstall. Before any `brew upgrade`, check `/opt/homebrew/opt/llvm/bin/clang
  --version`. Run `brew pin llvm lld` to stop the 22 → 23 upgrade, since the analytic evaluator
  rejects LLVM 23.
- Not installed: SAW, KLEE and VerCors (optional, or deferred to the concurrency phase).
