#!/usr/bin/env python3
"""
calc_stride_locality.py

Calculates memory distance proximity metrics from a sequence of requested indices:
- Mean index jump: |b_{k+1} - b_k|
- Mean byte stride: jump * element_size
- Adjacent-pair distance proximity:
  - Fraction of adjacent pairs with distance <= 64B (|b_{k+1} - b_k| * sizeof(T) <= 64B)
  - Fraction of adjacent pairs with distance <= 4KB (|b_{k+1} - b_k| * sizeof(T) <= 4096B)
  - Fraction of adjacent pairs crossing page distance threshold (> 4096B)

Note on semantics:
These metrics measure adjacent-pair distance proximity across successive accesses in the trace,
NOT cache hit rates, DRAM row buffer hits, or guaranteed same-cacheline/same-page co-residence.
"""

import sys
import numpy as np

def calculate_locality(indices, element_size_bytes=4, cacheline_bytes=64, page_bytes=4096):
    """
    Computes adjacent-pair distance metrics over an index sequence.
    Returns None if fewer than 2 entries are provided.
    """
    if len(indices) < 2:
        return None

    arr = np.array(indices, dtype=np.int64)
    diffs = np.abs(np.diff(arr))

    mean_index_jump = float(np.mean(diffs))
    mean_byte_stride = mean_index_jump * element_size_bytes

    cacheline_threshold = cacheline_bytes // element_size_bytes
    page_threshold = page_bytes // element_size_bytes

    same_cacheline = float(np.sum(diffs <= cacheline_threshold) / len(diffs) * 100.0)
    same_page = float(np.sum(diffs <= page_threshold) / len(diffs) * 100.0)
    cross_page = 100.0 - same_page

    return {
        "entry_count": len(indices),
        "adjacent_pair_count": len(diffs),
        "mean_index_distance": round(mean_index_jump, 2),
        "mean_byte_stride": round(mean_byte_stride, 2),
        "spatial_locality": {
            # Canonical proximity labels preserving backward compatibility
            "within_same_64B_cacheline_pct": round(same_cacheline, 2),
            "within_same_4KB_page_pct": round(same_page, 2),
            "cross_page_jump_pct": round(cross_page, 2),
            # Explicit semantic aliases
            "adjacent_pair_within_64B_proximity_pct": round(same_cacheline, 2),
            "adjacent_pair_within_4KB_proximity_pct": round(same_page, 2)
        },
        "metric_scope": "adjacent_pair_absolute_distance_proximity",
        "measures_cache_hits": False,
        "measures_same_block_membership": False
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: calc_stride_locality.py <index_trace.txt> [element_size_bytes]")
        sys.exit(1)

    trace_file = sys.argv[1]
    elem_size = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    total_lines = 0
    rejected_lines = 0
    vals = []
    try:
        with open(trace_file) as f:
            for line in f:
                total_lines += 1
                s = line.strip()
                if not s:
                    continue
                # Support positive and negative integers
                if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
                    vals.append(int(s))
                else:
                    rejected_lines += 1
    except FileNotFoundError:
        print(f"Error: file '{trace_file}' not found.", file=sys.stderr)
        sys.exit(1)

    stats = calculate_locality(vals, element_size_bytes=elem_size)
    if stats is None:
        print(f"[Locality] Insufficient entries in '{trace_file}': read {total_lines} lines "
              f"({len(vals)} valid integers, {rejected_lines} rejected non-integers). "
              f"At least 2 entries required to compute adjacent-pair statistics.")
        sys.exit(0)

    print(f"Calculated Locality for {len(vals)} accesses ({rejected_lines} non-digit lines ignored out of {total_lines}):")
    print(f"  Mean Element Jump:     {stats['mean_index_distance']}")
    print(f"  Mean Byte Stride:      {stats['mean_byte_stride']} B")
    print(f"  Adjacent Dist <= 64B:  {stats['spatial_locality']['within_same_64B_cacheline_pct']}% (label: within_same_64B_cacheline_pct)")
    print(f"  Adjacent Dist <= 4KB:  {stats['spatial_locality']['within_same_4KB_page_pct']}% (label: within_same_4KB_page_pct)")
    print(f"  Adjacent Dist > 4KB:   {stats['spatial_locality']['cross_page_jump_pct']}%")
    print(f"  Metric Semantics:      Adjacent-pair distance proximity (not cache hits or block co-residence)")

