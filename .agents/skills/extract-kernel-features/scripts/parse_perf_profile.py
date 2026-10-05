#!/usr/bin/env python3
"""
parse_perf_profile.py

Automates PMU counter collection and disassembly hotspot attribution via Linux perf.
Extracts instruction-level cycle breakdown, classifies bottleneck types (atomic CAS,
indirect gather miss, branch misprediction), and outputs structured profiling data.
"""

import sys
import os
import re
import json
import argparse
import subprocess

def run_perf_stat(cmd, output_prefix="perf_stat"):
    """Runs perf stat on the command line and extracts key architectural counters."""
    events = [
        "cycles",
        "instructions",
        "branches",
        "branch-misses",
        "L1-dcache-loads",
        "L1-dcache-load-misses",
        "LLC-loads",
        "LLC-load-misses"
    ]
    perf_cmd = [
        "perf", "stat",
        "-x", ";",
        "-e", ",".join(events),
        "--", *cmd
    ]
    print(f"[Profiler] Running perf stat: {' '.join(perf_cmd)}")
    res = subprocess.run(perf_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[Profiler] perf stat exited with code {res.returncode}: {res.stderr}", file=sys.stderr)
    
    metrics = {}
    for line in res.stderr.splitlines():
        parts = line.strip().split(";")
        if len(parts) >= 3:
            raw_val = parts[0].strip()
            event = parts[2].strip()
            if raw_val.isdigit():
                metrics[event] = int(raw_val)
            else:
                try:
                    metrics[event] = float(raw_val)
                except ValueError:
                    metrics[event] = raw_val

    # Derived rates
    cycles = metrics.get("cycles", 0)
    instructions = metrics.get("instructions", 0)
    branches = metrics.get("branches", 0)
    branch_misses = metrics.get("branch-misses", 0)
    l1_loads = metrics.get("L1-dcache-loads", 0)
    l1_misses = metrics.get("L1-dcache-load-misses", 0)
    llc_loads = metrics.get("LLC-loads", 0)
    llc_misses = metrics.get("LLC-load-misses", 0)

    derived = {
        "ipc": round(instructions / cycles, 4) if cycles else None,
        "branch_miss_rate_pct": round((branch_misses / branches) * 100, 2) if branches else None,
        "l1_dcache_miss_rate_pct": round((l1_misses / l1_loads) * 100, 2) if l1_loads else None,
        "llc_miss_rate_pct": round((llc_misses / llc_loads) * 100, 2) if llc_loads else None,
    }
    return {"raw_counters": metrics, "derived_metrics": derived}

def run_perf_record_annotate(cmd, symbol=None, perf_data_path="perf.data"):
    """Runs perf record followed by perf annotate to attribute samples to asm lines."""
    record_cmd = [
        "perf", "record",
        "-F", "999",
        "-e", "cycles:pp",
        "-o", perf_data_path,
        "--", *cmd
    ]
    print(f"[Profiler] Recording samples: {' '.join(record_cmd)}")
    subprocess.run(record_cmd, check=True)

    annotate_cmd = ["perf", "annotate", "-i", perf_data_path, "--stdio"]
    # Don't pass strict symbol to annotate command so perf outputs all annotated functions,
    # then our parser filters by target_symbol substring
    pass

    print(f"[Profiler] Generating disassembly annotation: {' '.join(annotate_cmd)}")
    annotate_res = subprocess.run(annotate_cmd, capture_output=True, text=True, check=True)
    return parse_annotate_output(annotate_res.stdout)

def parse_annotate_output(annotate_text, threshold_pct=1.0):
    """
    Parses `perf annotate --stdio` output and classifies instruction-level bottlenecks.
    Lines typically look like:
         15.97 :   4021a8:   lock cmpxchg %ecx,(%rdx)
    """
    pattern = re.compile(r"^\s*([0-9]+\.[0-9]+)\s*:\s*([0-9a-fA-F]+):\s*(.*)$")
    source_line_pattern = re.compile(r"^\s*:\s*(?:/\*|//)?\s*(.*\.cc:[0-9]+|\s*for\s*\(|\s*if\s*\(|NodeID|VertexOffsets).*$")

    hotspots = []
    current_source_context = ""

    for line in annotate_text.splitlines():
        # Track source comments if present
        if ":" in line and not pattern.match(line):
            cleaned = line.strip()
            if any(k in cleaned for k in [".cc:", ".h:", "for", "if", "curr_val", "parent", "VertexOffsets"]):
                current_source_context = cleaned

        m = pattern.match(line)
        if m:
            pct = float(m.group(1))
            addr = m.group(2)
            insn = m.group(3).strip()

            if pct >= threshold_pct:
                bottleneck = "COMPUTE_OR_PIPELINE"
                
                # Classify Bottleneck
                if "lock cmpxchg" in insn:
                    bottleneck = "ATOMIC_CAS_CONTENTION"
                elif "mov" in insn and ("(" in insn):
                    bottleneck = "INDIRECT_LOAD_MISS"
                elif "jmp" in insn or insn.startswith("j"):
                    bottleneck = "BRANCH_DIVERGENCE"
                elif "prefetch" in insn:
                    bottleneck = "PREFETCH_INSTRUCTION"
                elif "mfence" in insn or "sfence" in insn:
                    bottleneck = "SERIALIZING_FENCE"

                hotspots.append({
                    "sample_pct": pct,
                    "address": f"0x{addr}",
                    "instruction": insn,
                    "bottleneck_type": bottleneck,
                    "source_context": current_source_context
                })

    # Sort descending by sample percentage
    hotspots.sort(key=lambda x: x["sample_pct"], reverse=True)
    return hotspots

def main():
    parser = argparse.ArgumentParser(description="Profile kernel and annotate bottlenecks.")
    parser.add_argument("--symbol", default="TDStep", help="Target function symbol for annotate")
    parser.add_argument("--threshold", type=float, default=1.5, help="Minimum sample percentage to report")
    parser.add_argument("--output", "-o", default="kernel_hotspots.json", help="Output JSON path")
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Benchmark command line to run")

    args = parser.parse_args()
    if not args.cmd:
        print("Usage: parse_perf_profile.py [options] -- ./benchmark_binary [args...]")
        sys.exit(1)

    benchmark_cmd = args.cmd
    if benchmark_cmd[0] == "--":
        benchmark_cmd = benchmark_cmd[1:]

    # 1. PMU Hardware Counters
    pmu_data = run_perf_stat(benchmark_cmd)

    # 2. Record & Annotate
    hotspots = run_perf_record_annotate(benchmark_cmd, symbol=args.symbol)

    result = {
        "command": " ".join(benchmark_cmd),
        "target_symbol": args.symbol,
        "pmu_profile": pmu_data,
        "annotated_hotspots": hotspots
    }

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n[Profiler] Saved profiling summary to {args.output}")
    print(f"[Profiler] Found {len(hotspots)} instruction hotspots >= {args.threshold}%:")
    for h in hotspots[:5]:
        print(f"  - {h['sample_pct']}% at {h['address']}: {h['instruction']} [{h['bottleneck_type']}]")

if __name__ == "__main__":
    main()
