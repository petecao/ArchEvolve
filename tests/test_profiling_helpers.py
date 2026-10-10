#!/usr/bin/env python3
"""
Unit tests for kernel feature extraction and profiling helper scripts.
Tests parse_perf_profile.py and calc_stride_locality.py against edge cases
identified in the feature handoff audit.
"""

import unittest
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / ".agents/skills/extract-kernel-features/scripts"

def load_module(script_name, module_name):
    path = SCRIPTS_DIR / script_name
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

profiler_mod = load_module("parse_perf_profile.py", "parse_perf_profile")
locality_mod = load_module("calc_stride_locality.py", "calc_stride_locality")

run_perf_stat = profiler_mod.run_perf_stat
parse_annotate_output = profiler_mod.parse_annotate_output
calculate_locality = locality_mod.calculate_locality



class TestPerfProfileParser(unittest.TestCase):
    def test_run_perf_stat_unsupported_counters(self):
        fake_stderr = "<not supported>;;cycles;0;0\n100;;instructions;0;100\n<not counted>;;LLC-loads;0;0\n"
        fake_res = SimpleNamespace(returncode=0, stdout="", stderr=fake_stderr)
        with patch.object(profiler_mod.subprocess, "run", return_value=fake_res):
            res = run_perf_stat(["dummy_cmd"])
        
        self.assertEqual(res["counter_status"]["cycles"], "unsupported")
        self.assertIsNone(res["raw_counters"]["cycles"])
        self.assertEqual(res["counter_status"]["instructions"], "counted")
        self.assertEqual(res["raw_counters"]["instructions"], 100)
        self.assertEqual(res["counter_status"]["LLC-loads"], "not_counted")
        self.assertIsNone(res["derived_metrics"]["ipc"])

    def test_parse_annotate_symbol_filter_and_threshold(self):
        annotate_text = """Disassembly of function TDStep:
 : fixture.cc:10
 12.00 : 1000: mov (%rax),%eax
 35.00 : 1004: mov %eax,(%rdx)
Disassembly of function unrelated_helper:
 : fixture.cc:20
 45.00 : 2000: mov %eax,(%rdx)
 20.00 : 2004: jmp 2010
 22.00 : 2008: lock cmpxchg %ecx,(%rdx)
"""
        # Threshold 30.0 with symbol TDStep -> only instruction at 1004 (35.00%) should survive
        hotspots = parse_annotate_output(annotate_text, target_symbol="TDStep", threshold_pct=30.0)
        self.assertEqual(len(hotspots), 1)
        self.assertEqual(hotspots[0]["address"], "0x1004")
        self.assertEqual(hotspots[0]["symbol"], "TDStep")
        self.assertEqual(hotspots[0]["instruction_form"], "MEMORY_STORE")

        # Threshold 10.0 with symbol TDStep -> both 1000 (12%) and 1004 (35%)
        hotspots_all_td = parse_annotate_output(annotate_text, target_symbol="TDStep", threshold_pct=10.0)
        self.assertEqual(len(hotspots_all_td), 2)
        addrs = [h["address"] for h in hotspots_all_td]
        self.assertIn("0x1000", addrs)
        self.assertIn("0x1004", addrs)

        # None of unrelated_helper instructions should leak
        for h in hotspots_all_td:
            self.assertNotIn(h["address"], ["0x2000", "0x2004", "0x2008"])

    def test_instruction_form_classification(self):
        text = """Disassembly of function test:
 10.00 : 100: mov (%rax),%eax
 10.00 : 104: mov %eax,(%rdx)
 10.00 : 108: lock cmpxchg %ecx,(%rdx)
 10.00 : 10c: jmp 200
 10.00 : 110: jne 200
 10.00 : 114: prefetcht0 (%rax)
 10.00 : 118: mfence
"""
        hotspots = parse_annotate_output(text, threshold_pct=1.0)
        by_addr = {h["address"]: h for h in hotspots}
        self.assertEqual(by_addr["0x100"]["instruction_form"], "MEMORY_LOAD")
        self.assertEqual(by_addr["0x104"]["instruction_form"], "MEMORY_STORE")
        self.assertEqual(by_addr["0x108"]["instruction_form"], "ATOMIC_CAS")
        self.assertEqual(by_addr["0x10c"]["instruction_form"], "UNCONDITIONAL_JUMP")
        self.assertEqual(by_addr["0x110"]["instruction_form"], "CONDITIONAL_BRANCH")
        self.assertEqual(by_addr["0x114"]["instruction_form"], "PREFETCH")
        self.assertEqual(by_addr["0x118"]["instruction_form"], "MEMORY_FENCE")


class TestLocalityHelper(unittest.TestCase):
    def test_short_and_empty_traces(self):
        self.assertIsNone(calculate_locality([]))
        self.assertIsNone(calculate_locality([42]))

    def test_locality_calculation(self):
        res = calculate_locality([0, 4, 8, 12], element_size_bytes=4)
        self.assertIsNotNone(res)
        self.assertEqual(res["mean_index_distance"], 4.0)
        self.assertEqual(res["mean_byte_stride"], 16.0)
        self.assertEqual(res["spatial_locality"]["within_same_64B_cacheline_pct"], 100.0)
        self.assertEqual(res["spatial_locality"]["within_same_4KB_page_pct"], 100.0)
        self.assertFalse(res["measures_cache_hits"])


if __name__ == "__main__":
    unittest.main()
