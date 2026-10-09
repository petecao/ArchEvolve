#!/usr/bin/env python3
"""
parse_perf_profile.py

Automates PMU counter collection and disassembly hotspot attribution via Linux perf.
Extracts instruction-level cycle breakdown, classifies microarchitectural instruction shapes,
handles typed PMU counter states, and outputs structured profiling data.
"""

import sys
import os
import re
import json
import argparse
import subprocess

def run_perf_stat(cmd, output_prefix="perf_stat"):
    """Runs perf stat on the command line and extracts architectural counters with typed status."""
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
    counter_status = {}
    for line in res.stderr.splitlines():
        parts = line.strip().split(";")
        if len(parts) >= 3:
            raw_val = parts[0].strip()
            event = parts[2].strip()
            if raw_val.isdigit():
                metrics[event] = int(raw_val)
                counter_status[event] = "counted"
            else:
                try:
                    metrics[event] = float(raw_val)
                    counter_status[event] = "counted"
                except ValueError:
                    metrics[event] = None
                    if "<not supported>" in raw_val:
                        counter_status[event] = "unsupported"
                    elif "<not counted>" in raw_val:
                        counter_status[event] = "not_counted"
                    else:
                        counter_status[event] = "unavailable"

    # Helper for safe division without TypeErrors on None or non-numeric types
    def safe_div(num, denom, scale=1.0):
        if isinstance(num, (int, float)) and isinstance(denom, (int, float)) and denom > 0:
            return round((num / denom) * scale, 4)
        return None

    derived = {
        "ipc": safe_div(metrics.get("instructions"), metrics.get("cycles")),
        "branch_miss_rate_pct": safe_div(metrics.get("branch-misses"), metrics.get("branches"), 100.0),
        "l1_dcache_miss_rate_pct": safe_div(metrics.get("L1-dcache-load-misses"), metrics.get("L1-dcache-loads"), 100.0),
        "llc_miss_rate_pct": safe_div(metrics.get("LLC-load-misses"), metrics.get("LLC-loads"), 100.0),
    }
    return {
        "raw_counters": metrics,
        "counter_status": counter_status,
        "derived_metrics": derived
    }

def run_perf_record_annotate(cmd, symbol=None, threshold_pct=1.0, perf_data_path="perf.data"):
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
    print(f"[Profiler] Generating disassembly annotation: {' '.join(annotate_cmd)}")
    annotate_res = subprocess.run(annotate_cmd, capture_output=True, text=True, check=True)
    return parse_annotate_output(annotate_res.stdout, target_symbol=symbol, threshold_pct=threshold_pct)

def parse_annotate_output(annotate_text, target_symbol=None, threshold_pct=1.0):
    """
    Parses `perf annotate --stdio` output, filters by target symbol and threshold,
    and classifies instruction forms cleanly (distinguishing stores from loads, and unconditional jumps from branches).
    """
    pattern = re.compile(r"^\s*([0-9]+\.[0-9]+)\s*:\s*([0-9a-fA-F]+):\s*(.*)$")
    fn_header_pattern = re.compile(r"^\s*(?:Disassembly of (?:function|section)\s+([^\s:]+)|.*<([^>]+)>:)")

    hotspots = []
    current_symbol = None
    current_source_context = ""

    for line in annotate_text.splitlines():
        # Track function/symbol boundaries
        fn_match = fn_header_pattern.match(line)
        if fn_match:
            current_symbol = fn_match.group(1) or fn_match.group(2)
            current_source_context = ""
            continue

        # Track source comments if present
        if ":" in line and not pattern.match(line):
            cleaned = line.strip()
            if any(k in cleaned for k in [".cc:", ".h:", "for", "if", "curr_val", "parent", "VertexOffsets"]):
                current_source_context = cleaned

        m = pattern.match(line)
        if m:
            # If target_symbol is requested, filter out instructions from other symbols
            if target_symbol is not None and current_symbol is not None:
                if target_symbol not in current_symbol:
                    continue

            pct = float(m.group(1))
            addr = m.group(2)
            insn = m.group(3).strip()

            if pct >= threshold_pct:
                # Classify instruction form and candidate bottleneck hypothesis
                form = "COMPUTE"
                bottleneck = "COMPUTE_OR_PIPELINE"

                # AT&T syntax instruction classification
                if "lock cmpxchg" in insn:
                    form = "ATOMIC_CAS"
                    bottleneck = "ATOMIC_CAS_CONTENTION"
                elif "lock " in insn:
                    form = "ATOMIC_RMW"
                    bottleneck = "ATOMIC_BUS_LOCK"
                elif insn.startswith("mov"):
                    # Check if destination is memory (store) or source is memory (load)
                    operands = insn[3:].strip()
                    parts = operands.split(",")
                    if len(parts) >= 2:
                        src, dst = parts[0].strip(), parts[1].strip()
                        if "(" in dst:
                            form = "MEMORY_STORE"
                            bottleneck = "MEMORY_STORE"
                        elif "(" in src:
                            form = "MEMORY_LOAD"
                            bottleneck = "INDIRECT_LOAD_MISS"
                        else:
                            form = "REGISTER_MOV"
                            bottleneck = "REGISTER_TRANSFER"
                    elif "(" in operands:
                        form = "MEMORY_ACCESS"
                        bottleneck = "INDIRECT_LOAD_MISS"
                elif insn.startswith("jmp") or insn == "jmp":
                    form = "UNCONDITIONAL_JUMP"
                    bottleneck = "CONTROL_FLOW_JUMP"
                elif insn.startswith("j"):
                    form = "CONDITIONAL_BRANCH"
                    bottleneck = "BRANCH_DIVERGENCE"
                elif "prefetch" in insn:
                    form = "PREFETCH"
                    bottleneck = "PREFETCH_INSTRUCTION"
                elif any(f in insn for f in ["mfence", "sfence", "lfence"]):
                    form = "MEMORY_FENCE"
                    bottleneck = "SERIALIZING_FENCE"

                hotspots.append({
                    "sample_pct": pct,
                    "address": f"0x{addr}",
                    "instruction": insn,
                    "instruction_form": form,
                    "bottleneck_type": bottleneck,
                    "symbol": current_symbol,
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
    hotspots = run_perf_record_annotate(
        benchmark_cmd,
        symbol=args.symbol,
        threshold_pct=args.threshold
    )

    result = {
        "command": " ".join(benchmark_cmd),
        "target_symbol": args.symbol,
        "sample_threshold_pct": args.threshold,
        "pmu_profile": pmu_data,
        "annotated_hotspots": hotspots
    }

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n[Profiler] Saved profiling summary to {args.output}")
    print(f"[Profiler] Found {len(hotspots)} instruction hotspots >= {args.threshold}% for symbol '{args.symbol}':")
    for h in hotspots[:5]:
        print(f"  - {h['sample_pct']}% at {h['address']}: {h['instruction']} [{h['instruction_form']} -> {h['bottleneck_type']}]")

if __name__ == "__main__":
    main()

