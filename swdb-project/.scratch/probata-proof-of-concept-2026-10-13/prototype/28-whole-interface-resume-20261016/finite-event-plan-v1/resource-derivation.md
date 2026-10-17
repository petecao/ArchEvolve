# Static finite-model budget, 2026-10-16 ET

The profile bounds allocation performed by the emitted trace and the exact pinned model bodies, under the separately owned receiver premise `dxm_count=dxm_event_count=dxc_count=dxa_count=0`, no constructing command, no initialized ordinary/register payload, no tile image and all sizes `UINT_MAX`. It does not bound an unimplemented receiver prefix: its exact compatibility and closure remain a future public gate. Entry consistency checks allocate no model nodes and grant no state.

The fixed backend begins with `DXM_TILES=32`, `DXG_REGS=32`, `DXP_VALUE_BOUND=2` and `DXP_TILE_WORDS=16384` (`whole_value_backend_v1.h:8-24`). Its source setup derives the exact seven MMIO boundaries and six region rows (`:1526-1537`). Region first-ID/F2 checks are retained (`:1086-1107`), as are full-line store projection in `whole_adapters.h:43-78`. This preparation uses no enlarged tile geometry.

| Allocation site | Static upper bound | Exact source basis |
|---|---:|---|
| CPU ordinary write/read/CAS | 0 nodes | `whole_value_backend_v1.h:974-993`; writes extend events, not DAG nodes |
| CPU tile write | 1 node | `:1396-1401`, one constant |
| CPU tile read | 2 nodes | `:1349-1363`, missing sentinel plus byte gather; `:1402-1407` covers without node allocation |
| Register write | 1 node | `:1237-1245`, one constant and byte binding |
| Stream common prefix | 33 nodes | `whole_value_builders_v1.h:130-147`; details below |
| Each load lane | width+10 nodes | `:149-155`; width is4 or8 |
| Each store lane | 12 nodes | `:149-159`, with capture<=2 and `whole_value_backend_v1.h:1007-1023` |

The stream prefix is two constants (zero/one), at most six nodes to capture three int32 registers, six for initial min/stride/max guards, six for byte/page limits, two for stride limit, two for the stride guard, three for difference/minus-one/quotient, three for the size expression, and three for the prefix-bound check: `2+6+6+6+2+2+3+3+3=33`. A register capture creates at most one missing sentinel and one byte-gather node (`whole_value_backend_v1.h:1224-1237`).

A load lane creates active-test2, index3, indexed-read1, at most width+1 conditional byte-output nodes, and work-root/join3: width+10. Inactive lanes retain byte-level initializedness and are never eagerly observed. A store lane creates active-test2, index3, tile capture<=2, store action4 and root join1:12. No condition operand is admitted in this slice. A stream load therefore costs at most61 nodes for u32 or69 for u64; a stream store costs at most57.

The first history pair writes three registers and issues two u32 loads, then reads two tile results: `3 + 2*61 + 2*2 = 129`. No node is introduced by assertions, explicit wait, critical markers, lifetime checks, CPU ordinary accesses or receiver consistency checks. The allocation rule selects `max(16, smallest power of two strictly above required nodes + closure)`, hence256 for129; closure0 is explicit. The preparer refuses an allocation above512, rather than truncating source events. The source Plan, cost rows, limits and model C hashes are retained together.

Ordinary cell IDs are unique, nonaliasing, bound to one physical/guest object identity, and must fit64. The profile separately records the exact high-water cell requirement. It supports only two elements per object and at most eight objects. No source or backend capacity is silently assumed. Commands are exactly counted, at most8, with the exact nonzero limit bound into `DXC_COMMANDS`. Every store allocates two actions including an inactive lane, so `DXA_ACTIONS=2*stores` (minimum1).

Every CPU write or possibly successful CAS contributes at most one memory event. Every store contributes at most two device writes, including a conservative inactive-lane upper bound. Thus events<=CPU-writes/CAS+2*stores; this must be<=63. The retained event limit is exactly that bound (minimum1), and each indexed-read history has at most one issue candidate plus that event count. This follows `whole_value_backend_v1.h:479-514,691-710`. The history profile never deletes prior writes or assumes a particular history choice.

Each load has at most two indexed-read choices. Store completion selects an order for two actions with at most one draw (`whole_value_backend_v1.h:1044-1050`), including inactive actions. Thus draw_count=`max(1,2*loads+stores)`, with independent full-u32 table rows and modulo over positive alternatives from the exact `model-entry-v3/whole_model_v3.py::hook_text`. Every choice and capacity failure remains checked. No readiness-query draws are included because that event is absent. Draws for a future receiver or wrapper must be separately bound; these bounds grant no arbitrary bootstrap activity.

These are source upper bounds, subject to independent review and actual admitted controls. They are not a proof of the physical compiler's stack/RSS needs, a test result for C, a hardware refinement, a claim that the prospective receiver receipt establishes an executable prestate, or public same-thread/other-thread acceptance.
