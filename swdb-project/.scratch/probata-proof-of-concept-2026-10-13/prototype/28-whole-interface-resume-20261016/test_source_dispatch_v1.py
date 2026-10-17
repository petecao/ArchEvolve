"""2026-10-16 ET. Compiler-free source routing and physical identity controls."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest


def no_child(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork")) or event in {"os.system", "ctypes.dlopen"}:
        raise RuntimeError("source dispatch controls forbid " + event)


sys.addaudithook(no_child)
HERE = Path(__file__).resolve().parent


def own(name):
    path = HERE / name
    ns = {"__file__": str(path), "__name__": "inert_source_fixture"}
    exec(compile(ast.parse(path.read_bytes()), str(path), "exec"), ns)
    return ns


SOURCE = own("source_dispatch_v1.py")
API = own("whole_interface_v3.py")
BASE = own("test_whole_interface.py")
BASE["API"] = API
ABI = BASE["ABI"]


def object_row(identity="array", guest=4096, physical=65536, extent=4, dtype=0):
    return {"object_id": identity, "guest_base": guest, "physical_base": physical,
            "extent": extent, "dtype": dtype, "source_pin": "a" * 64}


class Controls(BASE["Controls"]):
    # Inherit source fixtures only. The original six tests also check unchanged
    # source declaration/role derivation and existing refusal controls.
    def test_07_partial_alias_views_reuse_history_cells_in_any_input_order(self):
        middle = object_row("middle", 4104, 65544, 2)
        complete = object_row("complete", extent=6)
        for objects in ([middle, complete], [complete, middle]):
            atlas = SOURCE["prepare_atlas"](objects)
            by_name = {row["object_id"]: row for row in atlas["objects"]}
            self.assertEqual(by_name["middle"]["cell_ids"], [2, 3])
            self.assertEqual(by_name["complete"]["cell_ids"], [0, 1, 2, 3, 4, 5])
            self.assertFalse(atlas["initialization_granted"])
            self.assertEqual(atlas["history_events_added"], 0)
        # Different guest views of the same physical scalar retain one history.
        atlas = SOURCE["prepare_atlas"]([object_row("a"), object_row("b", guest=8192)])
        self.assertEqual(atlas["objects"][0]["cell_ids"], atlas["objects"][1]["cell_ids"])

    def test_08_mixed_views_bad_identity_geometry_and_projection_refuse(self):
        cases = [[object_row(), object_row("wide", dtype=3)],
                 [object_row(), object_row("signed", dtype=1)],
                 [object_row(), object_row("inconsistent", physical=131072)],
                 [object_row(), object_row()], [object_row(dtype=6)], [object_row(extent=0)],
                 [object_row(guest=-1)], [object_row(physical=65537)],
                 [object_row(physical=2**64-4, extent=2)], [dict(object_row(), source_pin="unbound")]]
        for objects in cases:
            with self.assertRaises(SOURCE["Refused"]): SOURCE["prepare_atlas"](objects)

    def test_09_all_source_declarations_have_fixed_typed_routes(self):
        header, contracts = SOURCE["render_routes"](API, self.declarations, ABI)
        self.assertEqual((len(contracts), len({row["name"] for row in contracts})), (132, 26))
        self.assertEqual(len({(row["name"], row["formal_arity"]) for row in contracts}), 27)
        for name in BASE["LITERAL"]:
            self.assertEqual(sum(row["name"] == name for row in contracts), 6)
            self.assertIn("dws_fixed_" + name + "(thread,", header)
        self.assertNotIn("dwi_value_builder", header)
        self.assertNotIn("void *context", header)
        self.assertIn("dws_pack_f32(data)", header)
        self.assertIn("dws_unpack_f64(dwi_get_reg", header)
        self.assertIn("struct dws_pointer dws_get_cacheable_tile_pointer", header)
        self.assertIn("dws_memory_view(data,", header)
        direct = SOURCE["render_direct_families"](API, self.declarations)
        self.assertEqual(direct.count("unsigned command=dwi_prepare_packet("), 11)
        self.assertEqual(direct.count("dxc_bind(command,root)"), 11)
        self.assertNotIn("dwi_atomic_packet", direct)
        self.assertNotIn("dwi_value_builder", direct)
        for family, count in (("dxw_alu", 3), ("dxw_stream", 2), ("dxw_indirect", 5), ("dxw_range", 1)):
            self.assertEqual(direct.count("unsigned root=" + family + "("), count)
        changed = copy.deepcopy(self.declarations);changed[0]["line"] += 1
        with self.assertRaises(SOURCE["Refused"]): SOURCE["render_routes"](API, changed, ABI)

    def test_10_fresh_bind_and_exact_argument_subtree_attribution(self):
        count = 0
        for row in self.declarations:
            for dtype in range(6) if row["template"] else (0,):
                tu, kw = self.fixture(row, dtype)
                binding = API["bind_call"](tu, **kw)
                staged = [{"index": index, "ast_sha256": SOURCE["digest"](node), "identifier": "argument_" + str(index),
                           "model_type": "pointer-descriptor" if "*" in parameter["type"] else "exact-scalar"}
                          for index, (node, parameter) in enumerate(zip(tu["inner"][1]["inner"][0]["inner"][0]["inner"][1:], row["parameters"]))]
                result = SOURCE["bind_dispatch"](API, tu, binding=binding, staged_arguments=staged, thread="owned_thread", **kw)
                self.assertEqual(result["model_expression"], "dws_" + binding["c_name"] + "(" + ", ".join(["owned_thread", *(p["identifier"] for p in staged)]) + ")")
                self.assertFalse(result["public_admission"]);count += 1
        self.assertEqual(count, 132)

    def test_11_changed_stage_type_id_subtree_and_source_refuse(self):
        row = next(row for row in self.declarations if row["name"] == "maa_stream_load")
        tu, kw = self.fixture(row)
        binding = API["bind_call"](tu, **kw)
        nodes = tu["inner"][1]["inner"][0]["inner"][0]["inner"][1:]
        staged = [{"index": i, "ast_sha256": SOURCE["digest"](node), "identifier": "argument_" + str(i),
                   "model_type": "pointer-descriptor" if i == 0 else "exact-scalar"} for i, node in enumerate(nodes)]
        for key, value in (("index", True), ("ast_sha256", "0" * 64), ("identifier", "user();"),
                           ("identifier", "dxm_cover"), ("model_type", "exact-scalar")):
            mutation = copy.deepcopy(staged);mutation[0][key] = value
            with self.assertRaises(SOURCE["Refused"]):
                SOURCE["bind_dispatch"](API, tu, binding=binding, staged_arguments=mutation, thread="thread_id", **kw)
        changed = copy.deepcopy(tu);changed["inner"][1]["inner"][0]["inner"][0]["inner"][1]["value"] = "1"
        with self.assertRaises((SOURCE["Refused"], API["Refused"])):
            SOURCE["bind_dispatch"](API, changed, binding=binding, staged_arguments=staged, thread="thread_id", **kw)

    def test_12_pointer_bridge_cpu_and_device_use_same_cells_and_physical_spans(self):
        atlas = SOURCE["prepare_atlas"]([object_row()])
        header = SOURCE["render_pointer_bridge"](atlas)
        self.assertIn("o->base_cell+(unsigned)(p.offset/bytes)", header)
        self.assertIn("dxc_cpu_read(thread,", header)
        self.assertIn("dxc_cpu_write(thread,", header)
        self.assertIn("physical,physical+bytes", header)
        self.assertIn("m->base_cell=o->base_cell+(unsigned)(p.offset/bytes)", header)
        self.assertIn("m->source_base=o->guest+p.offset", header)
        self.assertNotIn("(uintptr_t)", header)
        self.assertIn("source-one-past-dereference", header)
        self.assertIn("noncacheable-cpu-access-outside-source-policy", header)
        self.assertIn("DXP_VALUE_BOUND*bytes", header)
        for suffix in SOURCE["TYPE_SUFFIX"]:
            self.assertIn("dws_cpu_load_" + suffix, header)
            self.assertIn("dws_cpu_store_" + suffix, header)
        mutation = copy.deepcopy(atlas);mutation["objects"][0]["base_cell"] = 17
        with self.assertRaises(SOURCE["Refused"]): SOURCE["render_pointer_bridge"](mutation)
        for page, line in ((0, 64), (4096, 48), (64, 128), (True, 64)):
            with self.assertRaises(SOURCE["Refused"]): SOURCE["render_pointer_bridge"](atlas, page_bytes=page, line_bytes=line)

    def test_13_defaults_are_pinned_literals_and_other_selector_is_closed(self):
        for row in self.declarations:
            if row["minimum_arity"] == row["formal_arity"]:
                continue
            tu, kw = self.fixture(row, explicit=row["minimum_arity"])
            binding = API["bind_call"](tu, **kw)
            nodes = tu["inner"][1]["inner"][0]["inner"][0]["inner"][1:]
            staged = [{"index": i, "ast_sha256": SOURCE["digest"](node), "identifier": "argument_" + str(i),
                       "model_type": "pointer-descriptor" if "*" in row["parameters"][i]["type"] else "exact-scalar"}
                      for i, node in enumerate(nodes)]
            result = SOURCE["bind_dispatch"](API, tu, binding=binding, staged_arguments=staged, thread="owned_thread", **kw)
            self.assertEqual(result["model_expression"].count("-1"), row["formal_arity"]-row["minimum_arity"])
        row = next(row for row in self.declarations if row["name"] == "get_data_type")
        tu, kw = self.fixture(row)
        # Synthetic metadata consumer control; actual compiler correlation is
        # explicitly outside these fixtures, as in the inherited binder test.
        tu["inner"][0]["inner"][0]["type"] = {"qualType": "unsigned short"}
        binding = API["bind_call"](tu, **kw)
        self.assertEqual(binding["dtype"], 6)
        result = SOURCE["bind_dispatch"](API, tu, binding=binding, staged_arguments=[], thread="owned_thread", **kw)
        self.assertEqual(result["model_expression"], "dws_get_data_type_other(owned_thread)")
        header, _ = SOURCE["render_routes"](API, self.declarations, ABI)
        self.assertIn("dws_get_data_type_other(unsigned thread) {(void)thread;return dwi_get_data_type(6);}", header)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({"date": "2026-10-16 ET", "tests": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skips": len(result.skipped), "inherited_source_bindings": Controls.positive_bindings,
        "source_dispatch_bindings": 132, "source_route_instances": 132, "source_declarations": 27,
        "compiler_native_project_child_execution": False}, sort_keys=True))
    sys.exit(0 if result.wasSuccessful() else 1)
