# 56 — Verifier lineup on mbit10

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:40 ET (review fixes, round 3)
**Type:** slice
**Status:** claimed
**Blocked by:** 03
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Verifier lineup and order" (pinned versions), "Providers and machines" (mbit10), "Proof-of-concept plan" (A6)); decisions: [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) item 13; [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) items 2, 5; [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) items 2, 3, 8; [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md) (smoke programs)
**Time estimate:** about 2 days

**What to build:** The same pinned verifier lineup the Mac uses, installed on mbit10 so A6 can
reproduce every Mac verdict there. SAW, crux-llvm, CBMC, Frama-C/WP with Alt-Ergo, Z3 and CVC5, CIVL
with a JDK, GenMC and Rocq go under `/data1/yanruj/`, without sudo and with nothing under `$HOME`. Each
tool passes its smoke program, and every version is recorded. Builds stay capped on the shared host.
If the ThreadSanitizer box (50) ran, Archer with its instrumented libomp goes there too.

## Acceptance

- [ ] **Before installing:** the connection check from the mbit10-runs skill passes; the checkout's
  branch and commit are recorded; `df -h /data1 /data` is recorded with a size budget for the installs
  (LR-06).
- [ ] **Pinned versions.** Each tool is installed at the version the Mac lineup pins: SAW 1.6
  and both its fallbacks (crux-llvm 0.12, CBMC 6.11), Frama-C/WP 33.0 with the same Why3, Alt-Ergo, Z3
  and CVC5 versions (07's record), CIVL 1.23 with a JDK, and GenMC and Rocq at the versions 03 recorded.
- [ ] **No sudo, nothing under `$HOME`.** Everything lives under `/data1/yanruj/`. A listing of
  `$HOME` taken before and after shows no new files or folders from the installs: the opam root, the
  Why3 configuration, the JDK and every build cache point under `/data1/yanruj/`.
- [ ] **Capped builds.** Every build (GenMC from source, opam packages, anything else compiled) runs
  with a capped job count (for example `-j8`), never `-j$(nproc)`. The cap used is recorded.
- [ ] **Smoke programs.** SAW and crux-llvm read bitcode from the pinned clang 22.1.8; GenMC uses the
  LLVM its build pins (see Risks). Each bounded tool (SAW, crux-llvm,
  CBMC, CIVL, GenMC) proves 07's safe smoke program and refutes its seeded bug. WP proves the safe
  program, with Why3 detecting all three solvers, and leaves the seeded bug "not proven", never refuted.
  Rocq checks 03's tiny theorem and rejects its false one.
- [ ] **Archer, only if 50 ran.** If proof-of-concept 50's answer says the ThreadSanitizer baseline
  ran, Archer with the instrumented libomp is installed under `/data1/yanruj/`, at the versions and
  build flags 50 recorded, with a capped build. 50's race fixtures rerun there: Archer reports a race
  on each racy fixture and none on each race-free one. If 50's answer says "not run", nothing is
  installed and this ticket's answer says so.
- [ ] **Versions recorded** the way 03 recorded the Mac lineup: tool, version, install path, release
  archive checksum where there is one, disk used. `df -h /data1 /data` is recorded again at the end.

## Notes

- **Not in this ticket:**
  - 03 — New verifiers on the Mac: the Mac installs and the smoke files reused here.
  - 57 — Proof workers in a socket lane: running proof jobs inside a lane.
  - 58 — Mac verdicts reproduced on mbit10: re-running Mac verdicts through `swdb prove` with the real
    adapters.
  - 50 — ThreadSanitizer one-day box: the Mac box whose outcome decides the Archer criterion;
    evaluation 09 runs the baseline itself.
- Assumption (not decided in the map): 50 does not block this ticket; its one-day A4 box normally
  answers before A6. If it has not answered when the rest is done, this ticket resolves with the
  Archer criterion marked "waiting on 50" in its answer, so 57 is not held up, and the install follows
  50's answer, before evaluation 09 runs the baseline.
- Assumption (not decided in the map): "the pinned lineup" includes the pinned front end, clang 22.1.8,
  because it belongs to every content-hash set (11 item 8). The mbit10-runs skill's host facts
  (2026-09-22) list only clang 18.1.8, so this ticket installs clang 22.1.8 under `/data1/yanruj/` too.
  Check the host first; host facts change.
- Assumption (not decided in the map): if a Mac tool ended on its A0 fallback (SAW to crux-llvm, GenMC
  to CIVL alone, Rocq to the written proof), mbit10 installs the lineup the Mac actually used, so the
  verdicts can reproduce.
- Assumption (not decided in the map): a tool that cannot install without sudo goes to Yan-Ru, not to a
  fallback. A changed lineup would change the method version.
- Assumption (not decided in the map): installs and builds are not measurement jobs, so they take no
  socket lease. They still run capped, and not while either lane runs a timing batch, so they cannot
  disturb one.
- **Risks:** without sudo, a system library an opam package or GenMC needs (for example GMP or zlib
  headers) may be missing; build it from source under `/data1/yanruj/`. GenMC builds only against the
  LLVM versions it supports; use the LLVM version the Mac build used (03's record).
- mbit10 is x86_64 and the Mac is arm64. Smoke verdicts must match; times are never compared across the
  two.
