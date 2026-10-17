# Kernel identity is its correctness check

Date: 2026-09-22

A kernel is identified by what it computes and by its correctness check (a verifier
plus a stated tolerance); any code that passes that check is an implementation of the
kernel. We rejected bitwise-identical output, which would make almost every useful
change a new kernel (gapbs Gauss-Seidel and Jacobi PageRank differ in scores and sweep
counts yet both pass the verifier), and "same purpose in the algorithm", which no test
can check.

## Consequences

Code, loops, access patterns, and semantics belong to implementations, not kernels,
because two implementations of one kernel can touch memory differently (PageRank pull
gathers; push scatter-adds with atomics). The code found in the application is the
baseline implementation.
