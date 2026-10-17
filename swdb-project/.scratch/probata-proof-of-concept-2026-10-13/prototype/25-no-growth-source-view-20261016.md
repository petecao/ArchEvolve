# Source-derived no-growth caller view — 2026-10-16 ET

**Preparation only. The actual caller bridge and public admission remain unsupported.**

The new `swdb/vector_reallocation_caller_view.py` prepares and independently
reconstructs a diagnostic C view from the existing closed no-growth caller. It
rechecks physical original/lowered source hashes, current caller checker,
original contract tokens, all source-call spans and the complete actual cleanup
order. It inlines the entire unchanged original reserve body on the exact pure
arguments and adds a named assertion that the request is within capacity. This
assertion remains a proof duty. The entire original lowering is recovered by the
inverse transformation; construction/fill, captured alias, guarded scalar
capture, both reachable and unreachable cleanup, return and original model
dependencies remain present. No reserve summary or historical proof is imported.

The view adds target ABI static assertions and records two distinct coordinate
systems: receiver fields are Typed logical cells 0/1/2, extent 3, versus byte
positions 0/8/16, extent 24. An int buffer advances one Typed cell or four bytes.
These numbers are requirements, not a proven source-memory relation. The
selected default is Typed+Var+Machine. A real bridge must cover MemVar's
SSA/record values and initialization state as well as MemTyped's distinct int,
pointer, allocation and initialization chunks. Six exact prospective source pins
identify MemTyped, MemVar, MemLoader, Ctypes, Cint and Factory. A hash is not a
proof of any operation correspondence.

The pure `prepare/check/check_launch` seam first gave four genuine missing-module
RED controls, then four GREEN controls using retained real no-growth lowerer
output. A new model-effect control then caught an inliner that matched only the
familiar branch: four passes/one failure. Requiring the whole exact reserve
definition gives five passes. The first capture of that failure exposed the
harness's missing handler for pytest's `BaseException`; its corrected collector
replayed unchanged production bytes and retained the genuine failure. No project
compiler, formal tool or native child ran. The normal test fixture separately
uses the selected real lowerer and skips when it is unavailable.

`check_launch` always refuses until the actual source/runtime/lifetime bridge is
implemented. No adapter/setup dispatch changed. The next observation gate is
generation of actual Typed+Var tasks from the **unchanged original** no-growth
lowering with its three original clauses; that separate diagnostic does not use
this inlined view. Its task terms must guide a checked relation for local
identities, values and initialization, constructor fill, alias capture,
destruction, scalar retention and the final incoming frame. Current body-record
admission and fresh complete public ordinary/smoke results remain required.

[Preparation receipt](../evidence/t25-no-growth-source-view-preparation-20261016.json).
