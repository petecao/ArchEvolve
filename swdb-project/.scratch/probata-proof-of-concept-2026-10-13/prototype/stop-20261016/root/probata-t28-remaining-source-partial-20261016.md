# Ticket 28 remaining source frontier — partial checkpoint

Date: 2026-10-16 ET. Status: **PARTIAL — USER STOP**.

Root relayed USER STOPNOW. Exploration stopped; this note preserves only already read source findings. No implementation, test, compiler, native, formal, SSH, or Git mutation ran. No BC/PR/SSSP held-out function was read.

Inspected integration: `3b1e8277eadebc63f17827c1efd3b1cab6b305c4`; initialized-u32 candidate model read: `e99d09b1699b32525cd4c44cead21ed2fc6f4917`; upstream header identity: `e4fc4afdf894f295442cef3604667a469fab8e62`. Current host state and actual current-pair results were not assessed.

## Completed findings

- The pinned headers expose 26 names / 27 declarations. `get_new_reg(T1)` and `get_new_reg()` are separate declarations (`MAA_gem5.hpp:119-135`).
- **Zero-arity u32/u64 counter allocation is already admitted**, for exact builtin `unsigned int` and `unsigned long long`, by the closed software allocator (`swdb/dx100_allocation_source.py:15-34,63-79`). Missing work is RF initializedness/value/frame composition and other exact type identities, not repeating these arithmetic fixtures.
- The distinct initialized route admits only u32 args1 plus init/get (`dx100_initialized_register_source.py:97-129`). Its args0-unreachable row is a profile boundary. No actual formal result was reviewed.
- Initialized source order is width assert → saved counter → increment → typed store → fence → final counter capacity check/reload → saved ID (`MAA_gem5.hpp:114-126`). Signed-int versus corresponding unsigned-int storage does not justify no-alias; current counter/MMIO disjointness is explicit owned TCB (`dx100_initialized_register_model.py:3-8`).
- Register IDs have **four-byte stride**. Eight-byte accesses occupy two words; source args0 allocation allows odd starts (`MAA_gem5.hpp:108-144`). Typed access alignment/lifetime is separate. Retained RF excerpt/prototype documents odd-u64 alignment UB without inventing a hardware even-ID allocation rule (`checks/rf-source-excerpt.hpp:11-29`; deferred design:185-208).
- Pure selector source admission is u32 only (`dx100_source_selector.py:70-105`). Source datatype dispatch uses exact typedef identities (`MAA_gem5.hpp:164-172`): an unsigned-long-long register storage template does not automatically mean UINT64 command datatype on Linux LP64.
- Typed MMIO get/set cast away volatile; `mfence` has no memory clobber. `maa_const` has no fence (`MAA_gem5.hpp:108-117,146-149`). Each needs its own actual effective-source/emitted-effect binding; no certificate inheritance by similar body.
- One-u32-stream admission is only one isolated metadata observation with explicit RF/input/no-interference/normal-return/event-compression TCB (`dx100_stream_source.py:16-31`). It does not admit all widths or command families.
- Residual families: two tile pointer helpers; general add/clear/alloc mapping applicability; `maa_const`; `print_tile` I/O; other selector/type identities; broader wait/size and command applicability; eleven command wrapper families beyond the isolated admitted stream slice. Retained 0.1 and native prototype support are distinct from whole-interface source qualification.
- `get_tile_ready` is absent from the pinned header inventory. The retained query is logical; real ready-range MMIO is blocking (deferred design:277-305). No source nonblocking call or liveness theorem follows.

## Partial recommendation for resumption

After independent settlement of the current initialized-u32 pair, first compose source-bound u32 args0 allocation → explicit write → read with the initialized overload in a distinct fixed synthetic profile; next qualify paired exact unsigned-long-long register access. This recommendation is **not a finalized or reviewed implementation plan**.

Keep original caller contracts, empty original entry premises and partial-normal-return policy. Capacity and access applicability remain ordinary obligations; do not add desired-result axioms, initialize args0 payloads, hoist the post-store assert, or erase the final counter reload. For u64 retain IDs in four-byte words, two-word frames, width2 capacity0..30 and separate ABI alignment checks; do not impose even IDs on allocation itself. Preserve alias/lifetime/interference/source-correspondence TCB explicitly where unproved. Six-type selector expansion can be a separate stateless source prerequisite, but must bind exact source ABI identities.

Unfinished: complete per-family table, exhaustive spans, final implementation profile, independent design review and any execution. No hardware/current0.2/full-ticket acceptance is claimed.

## Resume pointers

- Ticket: `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/issues/28-proof-semantics-remaining-calls.md`.
- Source policies: `swdb/dx100_{allocation,register,initialized_register,stream,source_selector}*.py`.
- Public source blobs: `/private/tmp/probata-ticket28-interface-upstream-20261015/{MAA.hpp,MAA_gem5.hpp}`.
- Prototype design: `swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/28-proof-semantics/deferred-state-design.md`.
- Companion JSON contains physical SHA-256/size pins for all key source files read. Recheck integration/candidate identity before continuing; current files may move after this checkpoint.
