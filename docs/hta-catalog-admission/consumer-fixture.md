# HTA post-lock lookup recheck: compiled interleaving fixture

The primary Flat-HTA description explicitly requires lookup again after acquiring
the software fallback lock (MICRO2019, PDF page6 section4.4/Figure8). This new
C++17 fixture exercises that obligation with two actual host threads and a
condition-variable schedule, rather than replaying the accepted table tests.

Initial state: key39 is in software with value11; the fully occupied synthetic
hardware slot holds key17/value7. Actor A's first hardware lookup of39 falls
through. Before A acquires the software lock, actor B swaps key39/value99 into
hardware, preserves key17/value7 in software and removes software39. Key39 is
continuously present. A lookup that now checks software alone incorrectly returns
absence, which cannot be linearized to an instant when key39 was missing.

The repaired source sequence is Figure8's sequence:

1. Attempt atomic hardware lookup.
2. On unresolved fallback, acquire the relevant software line lock.
3. Reissue hardware lookup while holding that lock.
4. Only if still unresolved, consult software overflow; release the lock.

The fixture reproduces the missing-key result without step3 and gets the new
hardware value with step3. It also tests a returned zero as a valid hit, unchanged
software fallback, fast hardware hit and genuinely absent key. Victim ownership
and absence of a stale software key are checked after both actors finish.

`State` is a bounded normalized one-slot atomic-result abstraction. A host mutex
stands for an indivisible HTA result; it does not execute HTA ISA instructions,
CRC32 or the full line geometry. Thread names are fixture actors, not inferred
gem5 context IDs. The test does not certify a public HTA implementation, all
interleavings, memory ordering or real CPU atomicity. Figure9's update/swap
insertion protocol and the mixed-operation duplicate cleanup remain separate.

Executed once with C++17, `-pthread -O1 -Wall -Wextra -Werror`, UBSan and
`-fno-sanitize-recover=all`; compile/run both returned0. An initial source-receipt
assertion failed because the extracted paper is two-column text; that rejection
is preserved. Binding the exact single-line obligation fixed the receipt without
changing or reapplying the compiled fixture.

Next integration action: Root can add this portable source fixture and obligation
to the latest ArchEvolve implementation notes on a fresh branch after merged
`5ed0ac38`. No capability fields need changing. An actual hardware experiment
still needs authenticated HTA atomic operations, compiler/register packing and
software wrapper source; a mutex-backed fixture cannot substitute for them.
