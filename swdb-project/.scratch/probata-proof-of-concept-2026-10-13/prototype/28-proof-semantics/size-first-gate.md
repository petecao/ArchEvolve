# Stateful size getter first gate

Created: 2026-10-16 ET. Prospective, conditional synthetic-boot domain only.

The unchanged public C++ unit calls the actual pinned header's
`get_tile_size(0)` and returns it. Correct0 and deliberately wrong1 formal halves
use identical source bytes. No original-unit desired-result precondition is
added. This does not admit commands, arbitrary device entry states, ownership,
logical polling, or a production current0.2 version.

| Obligation | Certificate/evidence | Refusal boundary |
|---|---|---|
| Fresh epoch | Explicit fixture-only synthetic SPD-constructor then MMIO-address setup then core0 unit-entry certificate; recorded maintainer-owned environment premise pending Yan-Ru59 | Missing/changed certificate; alloc/init alone never establish freshness |
| Constructor projection | Immutable SPD.cc/SPD.hh and MAA.cc construction pins; exact constructor initialization excerpt produces Finished/status2, size0 and ready-counter0; all modeled read bytes initialized through ordinary C assignments | Source/geometry/projection changes; no desired-size axiom or precondition |
| Guest mapping | Exact pinned alloc_MAA address calculation for32tiles,16384words/tile,4cores, uint32words, uint16 metadata,64-bit guest address; certificate declares this configured mapping at boot epoch | Host pointer coincidence or arbitrary global rebinding does not certify mapping |
| Actual getter | Canonical pinned-header definition, source ABI volatileuint16(int), original-main-TU frozen preprocessing, actual volatile16-bit load from declared size-base plus2*sign-extendedint index and actual mfence; dependency/compiler/runtime closure | Impostor/declaration/macro/include/optimization/body/global/type/fence changes |
| Device action | CpuSidePort core0-only aligneduint16 size-range response calls SPD::getSize; SPD requires Finished and returns starting-tile size | No implicit covering wait, pending-writer support or arbitrary-core support |
| Separate readiness | MAA src/dst counted roles, IF resolved widths and explicit-start dispatch, SPD both-half counters; real ready-range MMIO blocks then1 | No `get_tile_ready` header declaration or unconditional progress theorem |
| Formal model path | Entry projection materializes constructor bytes in private model state; getter relation decodes those bytes; public WP retains normal RTE/init/smoke/fresh-cache checks and complete goal reading | Native/stand-in controls alone do not establish actual proof or body agreement |
| Provenance | Every touched verdict records the boot-epoch premise and source/model certificate with exact pins, owner and pending59 scope | No generalized all-callers freshness or physical-boot proof claim |

Boot premise wording: this synthetic fixture begins on core0 immediately after
one pinned SPD constructor has completed and the pinned MMIO-address setup has
configured its globals, before commands or other accesses modify that instance.
This is an explicit conditional environment/source-model premise owned by the
Probata proof-semantics maintainer, pending Yan-Ru freeze review59. Its existence
for arbitrary programs is not proved. Alloc_MAA/init_MAA are not state resets.

The initialization inserted into the model translates that declared epoch; it
does not execute a new source wait/reset or permit fresh-state initialization
inside arbitrary helper/call boundaries. A closed layout admits only this getter
and the complete26-name/27-declaration refusal inventory. Any future epoch,
command, core or geometry expansion needs its own checked rule and controls.


The first caller domain is deliberately closed to the parameter-free synthetic
`trust_fixture` with one integer local initialized by `get_tile_size(0)` and a
return of that local. The actual compiler AST verifies the declaration, explicit
integer promotion, direct callee, literal0 argument and same-AST local return;
no declaration ID is carried across dumps/processes or persisted. Original body
bytes and frozen preprocessing remain additional evidence, not substitutes for
AST binding. A canonical-body string literal cannot hide a macro-expanded write
inside a call argument. The retained RED demonstrates source-certificate
acceptance before this repair; the independent existing CPU-memory admission
already refused that program with verifier_launched=false, so no unsafe actual
proof or solver launch occurred. Repaired source admission rejects it earlier.

All synthetic constructor arguments/configuration are explicit:32tiles,
16384words per tile and matching4-core address geometry. The source constructors
are parameterized; neither the header defaults nor address setup establish an
arbitrary simulator's runtime parameters. The corresponding epoch/configuration
premise is recorded with maintainer ownership and pending59 review.

The getter's original AST is checked before optimized IR: exactly its local
volatile metadata read, inline fence and return, with no macro-expanded body
nodes. This preserves source RTE obligations that optimization could erase.
A retained countercontrol places a canonical getter string elsewhere and
macro-inserts an unused division by zero after the fence. The earlier source
certificate accepted that altered body and reached an explicitly named exit99
stand-in; no actual Frama-C ran. The repaired AST gate rejects it before model
preparation. Coherently rehashed IR cannot replace the getter fence: final
prelaunch validation rechecks the SSA load/store/fence sequence and MMIO mapping.

The prospective runner is `PROBATA_OUTPUT=/absolute/external/path run_size_acceptance.sh FULL_SOURCE_SHA PROFILE`,
where PROFILE is positive, negative, pair or missing. It requires an enclosing
1,200-second,8GiB one-worker guard (1,320-second outer watchdog), and explicit
`SWDB_DX100_SELECTOR_ACTUAL_LINEUP` four-version JSON before compiler bootstrap.
`SWDB_DX100_SIZE_ACTUAL=1` enables only the new stateful tests. These preparation
and native controls establish no actual verifier outcome; root admission and
complete ordinary/RTE/initialization/smoke evidence remain required.
