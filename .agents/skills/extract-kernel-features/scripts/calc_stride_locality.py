#!/usr/bin/env python3
"""
calc_stride_locality.py

Calculates memory distance metrics from a stream of requested indices:
- Mean index jump: |b_{k+1} - b_k|
- Mean byte stride: jump * element_size
- Spatial locality distribution:
  - Cache line proximity (<= 64B / element_size)
  - Virtual page proximity (<= 4096B / element_size)
  - Cross-page jumps (> 4096B / element_size)
"""

import sys
import numpy as np

def calculate_locality(indices, element_size_bytes=4, cacheline_bytes=64, page_bytes=4096):
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
        "mean_index_distance": round(mean_index_jump, 2),
        "mean_byte_stride": round(mean_byte_stride, 2),
        "spatial_locality": {
            "within_same_64B_cacheline_pct": round(same_cacheline, 2),
            "within_same_4KB_page_pct": round(same_page, 2),
            "cross_page_jump_pct": round(cross_page, 2)
        }
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: calc_stride_locality.py <index_trace.txt> [element_size_bytes]")
        sys.exit(1)

    trace_file = sys.argv[1]
    elem_size = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    with open(trace_file) as f:
        vals = [int(line.strip()) for line in f if line.strip().isdigit()]

    stats = calculate_locality(vals, element_size_bytes=elem_size)
    print(f"Calculated Locality for {len(vals)} accesses:")
    print(f"  Mean Element Jump: {stats['mean_index_distance']}")
    print(f"  Mean Byte Stride:  {stats['mean_byte_stride']} B")
    print(f"  Within Cache Line: {stats['spatial_locality']['within_same_64B_cacheline_pct']}%")
    print(f"  Within 4KB Page:   {stats['spatial_locality']['within_same_4KB_page_pct']}%")
    print(f"  Cross Page:        {stats['spatial_locality']['cross_page_jump_pct']}%")
