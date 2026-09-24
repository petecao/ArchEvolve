# ArchEvolve — Software Database

Updated: 2026-09-23

The Software Database is the ArchEvolve component that knows the applications:
what their kernels compute, how their code touches memory, what profiling
measured, which implementations exist, and which optimization strategies can
change them. Glossary only — no implementation detail, no status.

## Language

### Code

**Application**:
A program that contains one or more kernels, taken from one source at one version.
_Avoid_: benchmark (alone), suite

**Kernel**:
A computation inside an application that the database tracks, defined by what it
computes and by its correctness check, not by any one piece of code.
_Avoid_: hot loop, function, hotspot

**Correctness check**:
The test (a verifier plus a stated tolerance) that decides whether a piece of code
computes a given kernel.
_Avoid_: validation, equivalence proof

**Implementation**:
Code that realizes a kernel and passes that kernel's correctness check.
_Avoid_: option, variant, alternative

**Baseline implementation**:
The implementation of a kernel as found in its application's source.
_Avoid_: original, vanilla, reference implementation

**Access pattern**:
One memory-access expression in one implementation: a chain of steps that ends at
the array it reads or updates, plus its update kind and semantics.
_Avoid_: pattern (alone), access

**Step**:
One link in an access pattern's chain: one array and the address shape used to
reach it from the previous step.
_Avoid_: level, hop, edge

**Address shape**:
How a step computes its address: stream, single-valued indirect, ranged indirect,
pointer chase, or data-dependent merge.
_Avoid_: access type, stride pattern

**Update kind**:
What an access pattern does to the final array of its chain: read, write,
add-update, min/max-update, compare-and-swap, arbitrary, or prefetch (a non-binding
early access that returns no data).
_Avoid_: memory type, RMW type

**Pattern class**:
The category of an access pattern: the address shapes of its steps plus its
update kind.
_Avoid_: pattern (alone), access type

### Optimization

**Optimization strategy**:
A reusable technique for changing how code touches memory, identified by its
target (access pattern, loop, or input) and its effect on that target; numbers such as
tile size or prefetch distance are its parameters. It is not code and never runs.
_Avoid_: optimization (alone), transformation, technique, variant

**Strategy effect**:
The typed changes an optimization strategy makes to its target: reshape an address
shape, add an access pattern, add a hint, widen the lanes per access, reorder indices,
or restructure a loop. Together with the target, it is the strategy's identity.
_Avoid_: benefit, speedup

**Intrinsic**:
One ISA instruction wrapper that code can call (for example `_mm512_i32gather_ps`),
with the ISA extension it needs and the memory access it performs.
_Avoid_: builtin, instruction (alone)

### Evidence

**Basis**:
The stated source of a recorded fact: measured on the machine, simulated by a
model of the machine, read from code, reported by a person, inferred, or unknown.
Unknown never means false.
_Avoid_: confidence, provenance (alone)

**Input density**:
How full the data fed to a kernel is (mostly zeros versus full; scattered versus
clustered indices), independent of the storage format.
_Avoid_: sparse format, dense format

**Workload view**:
The record the HW Ensemble Agent reads, generated from database records in the HW
side's workload format.
_Avoid_: workload file, input YAML
