"""2026-10-16 ET. Pure model composition/refusal controls, no project imports."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
PROJECT = WHOLE.parents[3]
EVENTS = []


def no_child(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "socket.")) or event in {"os.system", "ctypes.dlopen"}:
        EVENTS.append(event)
        raise RuntimeError("pure model controls refuse " + event)


sys.addaudithook(no_child)
MODEL = {"__file__": str(HERE / "whole_model_v1.py"), "__name__": "inert_model_composition"}
exec(compile((HERE / "whole_model_v1.py").read_bytes(), MODEL["__file__"], "exec"), MODEL)
SYNTHETIC = json.loads((WHOLE / "source-dispatch-synthetic-inputs-v2.json").read_bytes())


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = MODEL["assemble"](WHOLE, PROJECT, abi=SYNTHETIC["abi"], objects=SYNTHETIC["objects"])

    def test_01_every_call_executes_fixed_body_with_cited_values(self):
        entry = self.result["entry"]
        self.assertEqual(entry["id"], "semantics.dx100_bfs_0_2")
        self.assertEqual(entry["target"], "dx100-mmio")
        self.assertEqual(entry["contract_form"], MODEL["KIND"])
        self.assertEqual(len(entry["calls"]), 26)
        self.assertEqual(sum(len(row["source_declarations"]) for row in entry["calls"]), 27)
        self.assertEqual(len(self.result["instances"]), 132)
        for row in entry["calls"]:
            self.assertTrue(row["contract"]["normal_return_state_value_relation"])
            self.assertTrue(row["contract"]["source_basis"])
        self.assertEqual(entry["model"]["sha256"], hashlib.sha256(self.result["c_text"].encode()).hexdigest())

    def test_02_flat_composition_preserves_exact_reviewed_bodies(self):
        body = self.result["c_text"]
        last = -1
        for name, sha in MODEL["BACKENDS"]:
            raw = (WHOLE / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), sha)
            at = body.index(raw.decode())
            self.assertGreater(at, last)
            last = at
        for family in ("alu_scalar", "alu_vector", "alu_reduce", "stream_load", "stream_store",
                       "indirect_load", "indirect_store_vector", "indirect_store_scalar",
                       "indirect_rmw_vector", "indirect_rmw_scalar", "range_loop"):
            self.assertIn("dws_fixed_maa_" + family + "(", body)
        self.assertIn("ordinary-mmio-alias-refused", body)
        self.assertIn("dws_cpu_load_u32", body)
        self.assertIn("dws_cpu_store_f64", body)

    def test_03_no_source_admission_or_fresh_state_is_invented(self):
        entry = self.result["entry"]
        self.assertFalse(entry["public_admission"])
        self.assertFalse(entry["current_0_2"])
        self.assertFalse(entry["full_ticket28"])
        self.assertFalse(entry["source_preconditions_assumed"])
        self.assertIn("cannot grant", entry["source_producer_admission"])
        self.assertIn("no fresh zero device", entry["receiver_state_policy"])
        self.assertIn("unsupported contract form", entry["WP"])
        # The fixed backend defines an explicit reset function. The assembler
        # must preserve that definition while never adding an invocation.
        original = sum((WHOLE / name).read_text().count("dxm_reset();") for name, _sha in MODEL["BACKENDS"])
        self.assertEqual(self.result["c_text"].count("dxm_reset();"), original)
        self.assertNotIn("dxm_reset", MODEL["hook_text"](128))

    def test_04_fresh_choice_budget_and_complete_choice_domain(self):
        draw = self.result["entry"]["harness_draws"]
        self.assertEqual(draw, {"object": "dws_choice_table", "scalar_type": "uint32_t", "count": 128,
                               "independent": True, "draw_before_source_unit": True})
        text = MODEL["hook_text"](128)
        self.assertIn("SWDB_CHECK(dws_choice_used<128u", text)
        self.assertIn("SWDB_CHECK(alternatives>0 && alternatives<=256", text)
        self.assertNotIn("__CPROVER_assume", text)
        for count in range(1, 257):
            self.assertEqual({value % count for value in range(count)}, set(range(count)))
        for budget in (True, 0, 257, "128"):
            with self.assertRaises(MODEL["Refused"]): MODEL["hook_text"](budget)

    def test_05_abi_and_physical_alias_controls_reach_real_emitters(self):
        abi = copy.deepcopy(SYNTHETIC["abi"])
        abi["sizes"][0] = 8
        with self.assertRaises(ValueError):
            MODEL["assemble"](WHOLE, PROJECT, abi=abi, objects=SYNTHETIC["objects"])
        for field in ("guest_base", "physical_base"):
            objects = copy.deepcopy(SYNTHETIC["objects"])
            objects[0][field] = 17179869184
            with self.assertRaises(ValueError):
                MODEL["assemble"](WHOLE, PROJECT, abi=SYNTHETIC["abi"], objects=objects)

    def test_06_frozen_pin_and_schema_refusals(self):
        with self.assertRaises(MODEL["Refused"]):
            MODEL["read_pin"](WHOLE / "whole_value_backend_v1.h", "0" * 64)
        self.assertEqual(MODEL["checked_design"](WHOLE / "new-0.2-contract-design-v1.json")[1]["sha256"], MODEL["DESIGN_SHA"])
        binder, _pin = MODEL["owned_module"](WHOLE / "whole_interface_v3.py", MODEL["BINDER_SHA"])
        declarations = binder["inventory"](PROJECT)
        calls = self.result["entry"]["calls"]
        MODEL["check_contract_inventory"](calls, declarations)
        for modified in (calls[:-1], [*calls[:-1], calls[0]]):
            with self.assertRaises(MODEL["Refused"]):
                MODEL["check_contract_inventory"](modified, declarations)
        modified = copy.deepcopy(calls)
        next(row for row in modified if row["call"] == "get_new_reg")["source_declarations"].pop()
        with self.assertRaises(MODEL["Refused"]):
            MODEL["check_contract_inventory"](modified, declarations)
        self.assertEqual(EVENTS, [])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun == 6 and not result.skipped and not EVENTS else 1)
