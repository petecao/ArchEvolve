# Closed no-growth caller allocator boundary — 2026-10-16 ET

The closed caller can use the existing allocator/model policy only within its
stated TCB. The current full-TU certificate establishes canonical source/header
bindings and rejects source allocation hooks; it does not attest a linked
program's replacement-free allocator implementation.

The retained genuine no-growth lowering certificate selects libc++22.1.8 and
`-std=c++17` without preprocessor defines. The candidate source checker accepts
only `std::vector<int>` or `std::vector<int,std::allocator<int>>`, a scalar count,
the four exact construction/capture/reserve/return statements, and a scalar
return captured before the destructor. Full-TU `stdlib_provenance` separately
screens canonical declarations and source-defined new/delete/malloc/free hooks,
standard namespace definitions, and new-handler registration. Its physical
header closure and exact source substitutions must be revalidated before an
actual caller launch.

The inspected selected headers show that the default allocator itself still
uses replaceable global allocation operations:

| Selected header | SHA-256 | Observation |
|---|---|---|
| `__memory/allocator.h` | `6076ad6fc5dc3d22eb599028dd016a24080fbc3c2608ea1788a50f0f65ade9f2` | `allocate` delegates to `__libcpp_allocate`; `deallocate` delegates to `__libcpp_deallocate` outside constant evaluation. |
| `__new/allocate.h` | `dfcb409bce1a9bc2ddc2774338119c1e6dc4c59175ba7d398a7547e162563087` | These helpers call `__builtin_operator_new` and `__builtin_operator_delete`. |
| `__vector/vector.h` | `7e2a0317d9ed2be3427b5e5e04f18ea8e8553da397924080855bf191e90aed0e` | Vector allocation/deallocation goes through its allocator traits. |

These hashes are physical reads of the local selected package and match the
retained original-TU certificate. They are not fresh Linux runtime attestation.
[Clang's primary language-extension documentation](https://clang.llvm.org/docs/LanguageExtensions.html#builtin-operator-new-and-builtin-operator-delete)
states that those builtins resolve to replaceable global allocation/deallocation
functions, while permitting allocation elimination/merging. Using the builtins
therefore does not itself establish a replacement-free linked environment.

The existing `std_models.allocator` WP contracts are explicit trusted primitives:
allocation has `assigns \nothing`, a fresh valid result, and allocation metadata;
deallocation has `assigns \nothing`, its freeable/null requirement, and release
metadata. `std_models.assumptions` records the library/model correspondence and
allocation-success policy. The private frame goals do not prove these imported
contracts or erase allocator/library internals. Their incoming-live observation
is conditional on the complete local transition state and this existing TCB.

Before a smaller closed-caller route is admitted, bind the original source and
default allocator substitutions, the exact allocator/model content, the stated
existing trusted assumptions and actual selected Typed+Var terms. If proof scope
includes externally linked replacement functions, their effects require an
explicit modeled contract or source/linked closure rather than an inference
from the TU certificate. No new replacement-free assumption is silently added.
The actual source/Typed bridge and all caller proof records remain pending.
