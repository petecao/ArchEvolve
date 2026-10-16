#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07, method24), throwaway. Created 2026-10-16 ET.
# Small concrete inputs that satisfy TDStep's preconditions (tdstep_standin.c), for the bounded hint
# falsifier. Deterministic: a fixed seed and fixed size bounds give the same instances every run.
# Bounds: num_nodes <= 4, num_edges <= 6, TILE_SIZE <= 3, SWDB_CHUNK_SIZE <= TILE_SIZE, threshold <= 3.
import random

MAX_N, MAX_E, MAX_T = 4, 6, 3


def instance(rng):
    n = rng.randint(1, MAX_N)
    E = rng.randint(0, MAX_E)
    T = rng.randint(1, MAX_T)
    C = rng.randint(1, T)
    AC = rng.random() < 0.75
    cuts = sorted(rng.randint(0, E) for _ in range(n - 1))
    offsets = [0] + cuts + [E]
    neighbors = [rng.randrange(n) for _ in range(E)]
    shared_in = rng.randint(0, n) if rng.random() < 0.3 else rng.randint((n + 1) // 2, n)
    prefix = rng.sample(range(n), shared_in)
    parent = []
    for v in range(n):
        if v in prefix or rng.random() < 0.15:
            parent.append(rng.randrange(n))
        else:
            parent.append(-rng.randint(1, 3))
    oe = rng.randint(0, shared_in)
    os_ = rng.randint(0, oe) if rng.random() < 0.4 else 0
    # Mostly the accelerated path (size >= threshold); sometimes the scalar path.
    size = oe - os_
    TH = rng.randint(1, max(1, size)) if rng.random() < 0.7 else rng.randint(1, 3)
    # Storage past shared_in is arbitrary; real vertex ids there expose hints that read past the window.
    shared = prefix + [rng.randrange(n) if rng.random() < 0.7 else rng.randint(-3, n + 2) for _ in range(n - shared_in)]
    tiles = rng.sample(range(8), 8)
    regs = rng.sample(range(8), 8)
    tile_len = [rng.randint(0, T) for _ in range(8)]
    dep = [rng.randint(0, 1) for _ in range(64)]
    tdata = [rng.randint(-2, 5) for _ in range(8 * T)]
    head = [n, E, T, C, TH, int(AC), os_, oe, shared_in]
    return head + offsets + neighbors + parent + shared + tiles + regs + tile_len + dep + tdata


def instances(count=600, seed=7):
    rng = random.Random(seed)
    return [instance(rng) for _ in range(count)]


def describe(row):
    n, E, T, C, TH, AC, os_, oe, si = row[:9]
    k = 9
    offsets = row[k:k + n + 1]; k += n + 1
    neighbors = row[k:k + E]; k += E
    parent = row[k:k + n]; k += n
    shared = row[k:k + n]
    return (f"num_nodes={n} num_edges={E} TILE_SIZE={T} SWDB_CHUNK_SIZE={C} SWDB_FRONTIER_THRESHOLD={TH} "
            f"swdb_acceleration_enabled={AC} offsets={offsets} out_neighbors={neighbors} parent={parent} "
            f"queue.shared={shared} shared_out_start={os_} shared_out_end={oe} shared_in={si}")
