"""Observe profiling-helper behavior using synthetic text and mocked subprocesses.

No perf command or benchmark is executed. This is a diagnostic receipt, not a
profile, correctness certification, or a replacement test suite for Peter's tools.
Run with a Python environment containing numpy to include the locality checks.
"""

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / ".agents/skills/extract-kernel-features/scripts"


def module_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect():
    profiler_path = SCRIPTS / "parse_perf_profile.py"
    locality_path = SCRIPTS / "calc_stride_locality.py"
    profiler = module_from(profiler_path, "audited_perf_helper")
    annotate = """Disassembly of function TDStep:
 : fixture.cc:10
 12.00 : 1000: mov (%rax),%eax
Disassembly of function unrelated_helper:
 : fixture.cc:20
 25.00 : 2000: mov %eax,(%rdx)
 18.00 : 2004: jmp 2010
 22.00 : 2008: lock cmpxchg %ecx,(%rdx)
"""
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        if argv[1] == "stat":
            return SimpleNamespace(returncode=0, stdout="", stderr="100;;cycles;0;100\n100;;instructions;0;100\n")
        if argv[1] == "record":
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if argv[1] == "annotate":
            return SimpleNamespace(returncode=0, stdout=annotate, stderr="")
        raise AssertionError("Unexpected mocked invocation")

    cache = ROOT / ".cache/feature-audit-20261008"
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as directory:
        output = Path(directory) / "synthetic.json"
        argv = ["parse_perf_profile.py", "--symbol", "TDStep", "--threshold", "30",
                "--output", str(output), "--", "SYNTHETIC_NOT_EXECUTED"]
        with patch.object(profiler.sys, "argv", argv), patch.object(profiler.subprocess, "run", fake_run), contextlib.redirect_stdout(io.StringIO()):
            profiler.main()
        emitted = json.loads(output.read_text())

    unsupported = SimpleNamespace(returncode=0, stdout="", stderr="<not supported>;;cycles;0;0\n100;;instructions;0;100\n")
    try:
        with patch.object(profiler.subprocess, "run", return_value=unsupported), contextlib.redirect_stdout(io.StringIO()):
            unsupported_result = profiler.run_perf_stat(["SYNTHETIC_NOT_EXECUTED"])
        unsupported_check = {"outcome": "returned", "result": unsupported_result}
    except Exception as exc:
        unsupported_check = {"outcome": "exception", "type": type(exc).__name__, "message": str(exc)}

    locality_checks = []
    if importlib.util.find_spec("numpy") is not None:
        locality = module_from(locality_path, "audited_locality_helper")
        for indices, block_bytes, key in (([15, 16], 64, "within_same_64B_cacheline_pct"),
                                          ([1023, 1024], 4096, "within_same_4KB_page_pct")):
            result = locality.calculate_locality(indices, element_size_bytes=4)
            addresses = [4 * i for i in indices]  # explicitly aligned base zero
            locality_checks.append({"indices": indices, "element_bytes": 4, "base_address": 0,
                "byte_addresses": addresses, "block_bytes": block_bytes,
                "helper_label": key, "helper_reported_pct": result["spatial_locality"][key],
                "actual_same_block": addresses[0] // block_bytes == addresses[1] // block_bytes,
                "interpretation": "A distance threshold tests proximity, not block membership or cache hits."})
        short_trace = {"zero_values": locality.calculate_locality([]), "one_value": locality.calculate_locality([1])}
    else:
        short_trace = {"status": "not_run_numpy_unavailable"}

    hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in (profiler_path, locality_path)}
    return {"record_kind": "synthetic_helper_diagnostic", "benchmark_executed": False,
        "perf_executed": False, "usable_as_performance_evidence": False, "source_sha256": hashes,
        "symbol_and_threshold": {"requested_symbol": "TDStep", "requested_threshold_pct": 30,
            "emitted_hotspots": emitted["annotated_hotspots"],
            "non_target_addresses_in_output": sorted({h["address"] for h in emitted["annotated_hotspots"]} & {"0x2000", "0x2004", "0x2008"}),
            "below_requested_threshold_in_output": [h["address"] for h in emitted["annotated_hotspots"] if h["sample_pct"] < 30],
            "mocked_perf_subcommands": [c[1] for c in calls]},
        "unsupported_counter": unsupported_check, "locality_counterexamples": locality_checks,
        "short_trace_function_results": short_trace,
        "scope": "Demonstrates current helper output on controlled synthetic inputs only; does not establish how the historical v1.2 reports were collected."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(collect(), indent=2) + "\n")
    print("Wrote synthetic helper observations; no perf or benchmark execution.")
