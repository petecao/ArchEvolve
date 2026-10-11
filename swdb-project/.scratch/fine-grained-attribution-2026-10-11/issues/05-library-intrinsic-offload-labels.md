# 05: Library, intrinsic and offload labels

Created: 2026-10-11 15:14 ET
**Type:** task
**Status:** ready-for-agent
**Blocked by:** 02 — First working version
**Spec:** `../spec.md` (F2; seam 1)
**Time estimate:** about 2–3 hours

**What to build:** Inside a rewrite site, `swdb attribute` labels executed typed-library operations as `library_call`, intrinsics as `intrinsic` and commands bound by the functional observation contract as `offload_command`, with precedence offload_command > intrinsic > library_call > agent_rewritten. libc and C++ standard library calls already in the baseline stay untouched.

## Acceptance

- [ ] Fixture with an offload command and a library call in one site shows the precedence.
- [ ] A baseline standard-library call outside any site stays untouched.
- [ ] Per-origin seconds appear inside the rewritten group.
