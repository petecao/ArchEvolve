# 56 — Verifier lineup on mbit10

Created: 2026-10-13 22:17 ET
Updated: 2026-10-14 01:45 ET (resolved)
**Type:** slice
**Status:** resolved
**Blocked by:** 03
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) ("Verifier lineup and order" (pinned versions), "Providers and machines" (mbit10), "Proof-of-concept plan" (A6)); decisions: [13](../../formal-verification-2026-10-09/issues/13-proof-hint-loop.md) item 13; [27](../../formal-verification-2026-10-09/issues/27-proof-of-concept-stages.md) items 2, 5; [11](../../formal-verification-2026-10-09/issues/11-verifier-choice.md) items 2, 3, 8; [07](../../formal-verification-2026-10-09/issues/07-install-verifiers.md) (smoke programs)
**Time estimate:** about 2 days

**What to build:** The same pinned verifier lineup the Mac uses, installed on mbit10 so A6 can
reproduce every Mac verdict there. SAW, crux-llvm, CBMC, Frama-C/WP with Alt-Ergo, Z3 and CVC5, CIVL
with a JDK, GenMC and Rocq go under `/data1/yanruj/`, without sudo and with nothing under `$HOME`. Each
tool passes its smoke program, and every version is recorded. Builds stay capped on the shared host.
If the ThreadSanitizer box (50) ran, Archer with its instrumented libomp goes there too.

## Acceptance

- [x] **Before installing:** the connection check from the mbit10-runs skill passes; the checkout's
  branch and commit are recorded; `df -h /data1 /data` is recorded with a size budget for the installs
  (LR-06).
- [x] **Pinned versions.** Each tool is installed at the version the Mac lineup pins: SAW 1.6
  and both its fallbacks (crux-llvm 0.12, CBMC 6.11), Frama-C/WP 33.0 with the same Why3, Alt-Ergo, Z3
  and CVC5 versions (07's record), CIVL 1.23 with a JDK, and GenMC and Rocq at the versions 03 recorded.
- [x] **No sudo, nothing under `$HOME`.** Everything lives under `/data1/yanruj/`. A listing of
  `$HOME` taken before and after shows no new files or folders from the installs: the opam root, the
  Why3 configuration, the JDK and every build cache point under `/data1/yanruj/`.
- [x] **Capped builds.** Every build (GenMC from source, opam packages, anything else compiled) runs
  with a capped job count (for example `-j8`), never `-j$(nproc)`. The cap used is recorded.
- [x] **Smoke programs.** SAW and crux-llvm read bitcode from the pinned clang 22.1.8; GenMC uses the
  LLVM its build pins (see Risks). Each bounded tool (SAW, crux-llvm,
  CBMC, CIVL, GenMC) proves 07's safe smoke program and refutes its seeded bug. WP proves the safe
  program, with Why3 detecting all three solvers, and leaves the seeded bug "not proven", never refuted.
  Rocq checks 03's tiny theorem and rejects its false one.
- [ ] **Archer, only if 50 ran.** (waiting on 50, see Answer) If proof-of-concept 50's answer says the ThreadSanitizer baseline
  ran, Archer with the instrumented libomp is installed under `/data1/yanruj/`, at the versions and
  build flags 50 recorded, with a capped build. 50's race fixtures rerun there: Archer reports a race
  on each racy fixture and none on each race-free one. If 50's answer says "not run", nothing is
  installed and this ticket's answer says so.
- [x] **Versions recorded** the way 03 recorded the Mac lineup: tool, version, install path, release
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

## Answer

2026-10-14 01:45 ET. **The Mac lineup is installed on mbit10 at the same versions, and all 23 smoke
checks give the Mac's verdicts.** Every tool lives under `/data1/yanruj/probata-verifiers/` (4.3 GB). No
sudo was used, and `$HOME` is unchanged. Archer waits on 50.

**Before installing** (2026-10-14 01:07–01:10 ET): the connection check passed (load 0.06; all three
leases `released`: node0, node1 and the legacy `mbit10-evaluation`). The ArchEvolve checkout was
`yanrujhou_main` `680298a3` and was not moved; the smoke sources came from `git archive` of
`probata-poc/integration` `c38fd273` after a `git fetch`. `df -h`: `/data1` 22 G free, `/data` 97 G,
`/` 3.5 G. Budget (LR-06): at most 6 GB of kept toolchain on `/data1`; downloads and the LLVM build tree
stay transient (deleted); smoke output under 1 MB. Readers: 57, 58, the evaluation.

| Tool | Version on mbit10 | Install path (under `/data1/yanruj/probata-verifiers/`) | Download sha256 / source | Safe program | Seeded bug | Disk |
|---|---|---|---|---|---|---|
| clang (front end) | 22.1.8 (`ca7933e4`) | `/data1/yanruj/toolchains/LLVM-22.1.8-Linux-X64` (already there) | release tarball | — | — | 12 GB (pre-existing) |
| SAW | 1.6 (68eed5f), bundled z3 4.8.14 | `saw-1.6/saw-1.6-ubuntu-24.04-X64-with-solvers/bin/saw` | `0b25c8b3…38f7` (= GitHub digest) | `Proof succeeded! smoke` | `Proof failed.`, exit 2, `x: 41` | 644 MB |
| crux-llvm | 0.12 (Crux 0.9, 31cc4ad4) | `crux-llvm-0.12/crux-llvm-0.12-ubuntu-24.04-X64/bin/crux-llvm` | `51d04fa0…e429` | `Overall status: Valid` | `Invalid`, 1 disproved | 152 MB |
| CBMC | 6.11.0 | `cbmc-6.11.0/usr/bin/cbmc` (.deb unpacked with `dpkg-deb -x`) | `b3721aa5…1ac8` | `VERIFICATION SUCCESSFUL` | `VERIFICATION FAILED`, exit 10 | 212 MB |
| Z3 / CVC5 | 5.1.0 / 1.2.1 | `z3-5.1.0/…/bin/z3`, `cvc5-1.2.1/cvc5-Linux-x86_64-static/bin/cvc5` | `f47be8d2…284a` / `6d44abc2…de56` | — | — | 157 + 110 MB |
| Frama-C/WP | 33.0 Arsenic, Why3 1.8.2, Alt-Ergo 2.6.4 (+ RPP 0.0.4), OCaml 5.3.0 | opam switch `framac-33`, `OPAMROOT=opam/` (opam 2.6.1 binary, `b533d393…be3d`) | opam; package set identical to the Mac's (94 packages) | 11 / 11 proved | 10 / 11, the false assertion `Timeout` (not proven, never refuted) | opam root 2.4 GB (both switches) |
| Why3 provers | Alt-Ergo 2.6.4, CVC5 1.2.1, Z3 5.1.0 detected | `home/.why3.conf` | — | — | — | — |
| CIVL | 1.23 | `civl-1.23/civl-1.23/lib/civl-complete.jar` | `8ab3c6c8…c880` (same file as the Mac) | `All errors marked with '+' are absent` (both programs) | `The program MAY NOT be correct` (both) | 89 MB |
| JDK | OpenJDK 21.0.12.1 (Ubuntu build) | system `/usr/lib/jvm/java-21-openjdk-amd64` | — | — | — | 0 |
| GenMC | 0.19.0 (9f6c4c07), built with clang 22.1.8 against LLVM 22.1.8 | `genmc-0.19.0/build/bin/genmc` (sha256 `824b5b5a…7a82`) | archive `d1a2bf4c…fb9c` (= Mac) | `No errors were detected.` (3 programs) | exit 42: `Safety violation!`, `Non-atomic race!`, RC11 violation with `--disable-mm-detector` | 215 MB |
| LLVM for GenMC | 22.1.8, llvm only, X86, RTTI on, libLLVM.so | `llvm-22.1.8-rtti/` | `llvm-project-22.1.8.src.tar.xz` `922f1817…5888` | — | — | 351 MB |
| Rocq | 9.3.0 (core/runtime), stdlib 9.2.0, OCaml 5.3.0 | opam switch `rocq-9` | opam; Mac set + Linux-only `conf-linux-libc-dev` | true theorems accepted, `Closed under the global context` | `Error:`, exit 1 | in opam root |

Verdict table: `/data1/yanruj/EvolveSWDB_runs/probata-t56-20261014/smoke/verdicts.tsv` (sha256
`0fe206e6…eca1`, 23 PASS, 0 FAIL), from `smoke.log` (`c9bbbaf9…0c6d`). Each case ran once in a fresh
folder with a 600 s timeout. Exact commands, environment and quirks: `/tmp/claude/probata-poc-notes/verifiers-mbit10.md`.

**No sudo, nothing under `$HOME`.** `env.sh` sets `HOME` to `probata-verifiers/home`, `OPAMROOT`,
`WHY3CONFIG`, `TMPDIR` and the XDG folders, so opam, Why3, SARL and Java write under `/data1`. A listing of
`/home/yanruj` before and after (37,024 entries each, `records/home-{before,after}.txt`) is identical,
and `find -newer` the start marker finds nothing.

**Capped builds, lane used.** opam (`framac-33`, `rocq-9`), LLVM and GenMC built at `-j8`, each as its own
job in lane **node 1** through `/data1/yanruj/Memacc-evolveswdb-lane/AgenticRefiner/scripts/host/socket_lane.sh`
(that checkout is at Memacc `origin/yanrujhou_main` `76cca359`; the script matches it). Lease generations
573–579, no gapbs batch running. Wall times: Frama-C 5.6 min, Rocq 6.0 min, LLVM 10.6 min, GenMC 1 min. The
smoke runs also ran in lane node 1. Lane records: `records/lane-*.json`, `smoke/lane-smoke.json`.

**After** (2026-10-14 01:42 ET): `/data1` 18 G free, `/data` 97 G, `/` 3.5 G.

**Archer: waiting on 50.** Ticket 50 is still `claimed` with no answer, so nothing is installed. Per this
ticket's assumption, the install follows 50's answer, before evaluation 09 runs the baseline.

**Side findings:**

- **The LLVM 22.1.8 toolchain on mbit10 has no RTTI and no `libLLVM.so`** (`llvm-config --has-rtti` =
  NO). GenMC uses `dynamic_cast` and links `-lLLVM`, so it fails to link against it (logs
  `records/build-genmc-attempt{1,2}.log`). Fix: a private LLVM 22.1.8 built with Homebrew's configuration
  (RTTI on, EH off, libLLVM shared), so the GenMC source stays the pinned commit, unpatched.
- **clang++ 22 cannot find libstdc++ headers on mbit10**: it selects gcc 14's folder, which has none. Pass
  `--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`. C compiles are unaffected. Ticket 58 and the
  analytic evaluator's C++ builds will hit this.
- `/data1/yanruj/Memacc` has no `socket_lane.sh` at its HEAD and holds someone's staged edits; use
  `Memacc-evolveswdb-lane` instead. Neither was changed.
- **`/data1` is now under the 20 GB rule (18 G free).** New raw run output belongs on
  `/data/yanruj/EvolveSWDB_runs/` until space is freed.

Assumption: the system OpenJDK 21.0.12.1 is used rather than a copy under `/data1`. It is the same
version as the Mac's, nothing new is installed, and it is not under `$HOME`. An Ubuntu upgrade could
change it, so 58 should check `java -version` before it runs.
Assumption: the LLVM built for GenMC has only the X86 target; GenMC interprets IR and needs no other
backend. Its clang is the pinned 22.1.8 binary (a symlink).
Assumption (deviation from this ticket's note): builds ran inside a socket lane, not lease-free.
`.claude/rules/remote_server.md` forbids running a multi-threaded job unconfined, and a `-j8` build is
one. Both lanes were idle, so this cost nothing.
Assumption: no 30-minute heartbeat was scheduled (LR-07). The longest single job was 11 minutes, and the
whole session took about 40 minutes.
