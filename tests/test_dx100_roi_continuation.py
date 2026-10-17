import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import sys

from archevolve.dx100_validation import analyze_logs

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "docs/designs/dx100-reference-validation/eric-handoff/continue_to_verifier.py"
spec = importlib.util.spec_from_file_location("roi_continuation", WRAPPER)
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)


def event(cause, code=0):
    return SimpleNamespace(getCause=lambda: cause, getCode=lambda: code)


def block(reads=None, ranges=None):
    lines = [wrapper.BEGIN, "simTicks 10"]
    for name, value in zip(wrapper.COUNTERS, (reads, ranges)):
        if value is not None:
            lines.append(name + " " + str(value))
    return "\n".join([*lines, wrapper.END, ""])


class RoiContinuationTests(unittest.TestCase):
    def test_config_wrapper_installs_and_restores_hook_and_records_actual_event_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            (out/"stats.txt").write_text(block())
            original = lambda *args: event("m5_exit instruction encountered")
            simulation = SimpleNamespace(benchCheckpoints=original)
            m5 = SimpleNamespace(options=SimpleNamespace(outdir=temp), curTick=lambda: 10,
                                 simulate=lambda ticks: event(wrapper.NORMAL_EXIT))
            root = SimpleNamespace(resolveStat=lambda name: SimpleNamespace(value=0))
            modules = {"m5": m5, "m5.objects": SimpleNamespace(Root=SimpleNamespace(getInstance=lambda: root)),
                       "common": SimpleNamespace(Simulation=simulation)}
            args = [str(WRAPPER), "--dx100-source-root", temp, "--verify-max-ticks", "100", "--", "--maa"]
            saved_path = list(sys.path)
            try:
                with patch.dict(sys.modules, modules), patch.object(sys, "argv", args), \
                     patch.object(wrapper.runpy, "run_path", side_effect=lambda *a, **kw: simulation.benchCheckpoints(object(), 100, temp)):
                    wrapper.main()
            finally:
                sys.path[:] = saved_path
            self.assertIs(simulation.benchCheckpoints, original)
            receipt = json.loads((out/"exit-events.json").read_text())
            self.assertTrue(receipt["guest_completed"])
            self.assertEqual(len(receipt["events"]), 2)
            self.assertIn("PASS", receipt["verification_status"])

    def test_explicit_registered_zeros_are_projected_without_modifying_raw(self):
        raw = block()
        projection, values = wrapper.freeze_roi(raw, lambda name: 0)
        self.assertNotIn(wrapper.COUNTERS[0], raw)
        self.assertIn(wrapper.COUNTERS[0] + " 0", projection)
        self.assertEqual(list(values.values()), [0, 0])

    def test_positive_counter_dump_is_preserved_exactly(self):
        raw = block(8, 3)
        projection, _ = wrapper.freeze_roi(raw, {wrapper.COUNTERS[0]: 8, wrapper.COUNTERS[1]: 3}.__getitem__)
        self.assertEqual(raw, projection)

    def test_missing_positive_or_unregistered_counter_is_not_replaced_with_zero(self):
        for value in (4, None, float("nan"), -1, .5, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                wrapper.freeze_roi(block(), lambda name: value)

    def test_mismatched_dump_and_live_counter_is_rejected(self):
        with self.assertRaises(ValueError):
            wrapper.freeze_roi(block(8, 3), lambda name: 0)

    def test_multiple_or_incomplete_dumps_do_not_silently_choose_a_window(self):
        for raw in (block()+block(), wrapper.BEGIN, wrapper.END+wrapper.BEGIN):
            with self.assertRaises(ValueError):
                wrapper.freeze_roi(raw, lambda name: 0)

    def run_continuation(self, path, final_cause=wrapper.NORMAL_EXIT, first_cause="m5_exit instruction encountered"):
        events, budgets = [], []
        m5 = SimpleNamespace(curTick=lambda: 10,
            simulate=lambda ticks: (budgets.append(ticks) or event(final_cause)))
        result = wrapper.continue_after_roi(lambda *args: event(first_cause), m5,
            lambda name: 0, path, 200, events, object(), 100, str(path))
        return result, events, budgets

    def test_continuation_obeys_remaining_budget_and_preserves_snapshot_receipts(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp);raw = block();(p/"stats.txt").write_text(raw)
            result, events, budgets = self.run_continuation(p)
            self.assertEqual(result.getCause(), wrapper.NORMAL_EXIT)
            self.assertEqual(budgets, [90])
            self.assertEqual(len(events), 2)
            self.assertEqual((p/"roi.stats.txt").read_text(), raw)
            receipt = json.loads((p/"roi-counter-values.json").read_text())
            self.assertEqual(receipt["raw_roi_sha256"], hashlib.sha256(raw.encode()).hexdigest())

    def test_second_roi_exit_or_timeout_is_not_guest_completion(self):
        for cause in ("m5_exit instruction encountered", "simulate() limit reached"):
            with tempfile.TemporaryDirectory() as temp, self.assertRaises(ValueError):
                p=Path(temp);(p/"stats.txt").write_text(block());self.run_continuation(p, final_cause=cause)

    def test_other_initial_event_is_not_assumed_to_be_the_roi_exit(self):
        with tempfile.TemporaryDirectory() as temp, self.assertRaises(ValueError):
            self.run_continuation(Path(temp), first_cause="simulate() limit reached")

    def test_existing_snapshots_are_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);(p/"stats.txt").write_text(block());(p/"roi.stats.txt").write_text("preserve")
            with self.assertRaises(ValueError):self.run_continuation(p)
            self.assertEqual((p/"roi.stats.txt").read_text(), "preserve")

    def test_collector_accepts_explicit_zero_control_and_rejects_cpu_fallback_candidate(self):
        projection, _ = wrapper.freeze_roi(block(), lambda name: 0)
        for variant, prefix in (("baseline", "TDStep"), ("dx100", "TDStepMAA")):
            stdout = f"ROI started: 1 threads\nStarting {prefix}: 1 elements\nROI End!!!\nVerification: PASS\n"
            result = analyze_logs(stdout, "", "gem5", variant, "completed", 0,
                                  projection, 0, wrapper.COUNTERS)
            self.assertEqual(result["intended_path_observation"],
                "idle_accelerator_observed" if variant == "baseline" else "refuted")


if __name__ == "__main__":
    unittest.main()
