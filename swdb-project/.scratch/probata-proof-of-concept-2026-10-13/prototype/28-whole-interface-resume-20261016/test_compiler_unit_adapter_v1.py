"""2026-10-16 ET. Inert compiler-unit/ABI consumer controls, no compiler."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest


def deny(event, args):
    if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork", "socket.")) or event in {"os.system", "ctypes.dlopen"}:
        raise RuntimeError("compiler adapter source controls refuse " + event)


sys.addaudithook(deny)
HERE = Path(__file__).resolve().parent


def own(name):
    path = HERE / name;ns = {"__file__": str(path), "__name__": "inert_compiler_fixture"}
    exec(compile(ast.parse(path.read_bytes()), str(path), "exec"), ns)
    return ns


ADAPTER = own("compiler_unit_adapter_v1.py")
API = own("whole_interface_v3.py")
BASE = own("test_whole_interface.py");BASE["API"] = API


def abi_roots():
    roots = []
    loc = {"offset": 0, "file": str(HERE / "compiler_abi_probe_v1.cpp"), "line": 1}
    for key in ADAPTER["TYPE_KEYS"]:
        roots.append({"kind": "TypeAliasDecl", "name": "dws_probe_" + key, "loc": loc,
                      "type": {"desugaredQualType": BASE["ABI"]["canonical_types"][key]}})
    values = dict(char_bit=8, int_bits=32, pointer_bits=64, little_endian=1, float_radix=2,
                  float_mantissa=24, double_mantissa=53, source_cores=4, source_tiles=32,
                  source_registers=32, source_tile_words=16384)
    for key, width in zip(ADAPTER["TYPE_KEYS"], (4, 4, 4, 8, 8, 8)):
        values["size_" + key] = width;values["align_" + key] = width
    for key in ADAPTER["ABI_INTS"]:
        roots.append({"kind": "EnumConstantDecl", "name": "dws_probe_" + key, "loc": loc,
                      "inner": [{"kind": "ConstantExpr", "value": str(values[key])}]})
    return roots


def stream(roots):
    return ("\n".join(json.dumps(root) for root in roots) + "\n").encode()


class Controls(BASE["Controls"]):
    def test_07_one_tu_parser_rejects_filtered_id_joins_and_malformed_streams(self):
        accepted = json.dumps({"kind": "TranslationUnitDecl", "inner": []}).encode()
        self.assertEqual(len(ADAPTER["parse_json_roots"](accepted, full_tu=True)), 1)
        for broken in (b"", b"not JSON", b'{"kind":"TranslationUnitDecl","kind":"FunctionDecl","inner":[]}',
                       b'{"kind":"TranslationUnitDecl","inner":[],"x":NaN}',
                       b'{"kind":"FunctionDecl"}\n{"kind":"FunctionDecl"}', accepted + accepted,
                       b'[{},{}]', b'{"kind":"TranslationUnitDecl"}'):
            with self.assertRaises(ADAPTER["Refused"]): ADAPTER["parse_json_roots"](broken, full_tu=True)
        saved = ADAPTER["STAGE_BYTES"]
        try:
            ADAPTER["STAGE_BYTES"] = 8
            with self.assertRaisesRegex(ADAPTER["Refused"], "cap"): ADAPTER["parse_json_roots"](accepted, full_tu=True)
        finally: ADAPTER["STAGE_BYTES"] = saved

    def test_08_exact_probe_alias_layout_geometry_and_refusal_controls(self):
        roots = abi_roots();probe = HERE / "compiler_abi_probe_v1.cpp"
        result = ADAPTER["observed_abi"](stream(roots), probe_path=probe, api=API)
        self.assertEqual(result["abi"], BASE["ABI"])
        self.assertEqual(result["root_count"], 29)
        self.assertFalse(result["runtime_float_environment_observed"])
        for key, value in (("dws_probe_pointer_bits", "32"), ("dws_probe_little_endian", "0"),
                           ("dws_probe_source_tiles", "64"), ("dws_probe_source_cores", "8"),
                           ("dws_probe_size_double", "4"), ("dws_probe_float_mantissa", "11")):
            changed = copy.deepcopy(roots)
            next(row for row in changed if row["name"] == key)["inner"][0]["value"] = value
            with self.assertRaises((ADAPTER["Refused"], API["Refused"])):
                ADAPTER["observed_abi"](stream(changed), probe_path=probe, api=API)
        for changed in (roots[:-1], roots + [roots[0]], [dict(roots[0], name="foreign"), *roots[1:]],
                        [dict(roots[0], loc={"offset": 0, "file": "/foreign.cpp"}), *roots[1:]]):
            with self.assertRaises(ADAPTER["Refused"]): ADAPTER["observed_abi"](stream(changed), probe_path=probe, api=API)

    def test_09_real_tu_protocol_binding_and_physical_source_refusal(self):
        row = next(row for row in self.declarations if row["name"] == "maa_alu_scalar")
        tu, kw = self.fixture(row)
        probe = HERE / "compiler_abi_probe_v1.cpp"
        args = dict(full_tu_raw=json.dumps(tu).encode(), abi_raw=stream(abi_roots()), source_path=self.source,
                    source_bytes=self.source.read_bytes(), probe_path=probe, probe_bytes=probe.read_bytes(),
                    declarations=self.declarations, compiler_capture_pin="a" * 64)
        unit = ADAPTER["prepare_unit"](API, **args)
        self.assertEqual([row["name"] for row in unit["calls"]], ["maa_alu_scalar"])
        self.assertTrue(unit["one_full_tu_for_all_declaration_ids"])
        self.assertFalse(unit["actual_compiler_run_inferred_from_hash"])
        self.assertFalse(unit["public_admission"])
        for key, value in (("source_bytes", b"changed"), ("probe_bytes", b"changed"),
                           ("compiler_capture_pin", "unbound"),
                           ("full_tu_raw", stream(tu["inner"]))):
            changed = dict(args);changed[key] = value
            with self.assertRaises(ADAPTER["Refused"]): ADAPTER["prepare_unit"](API, **changed)

    def test_10_prospective_recipe_has_one_full_tu_and_independent_abi_literals(self):
        recipe = ADAPTER["capture_recipe"](compiler="/inert/compiler", project="/inert/project", raw="/inert/raw")
        self.assertEqual(len(recipe["commands"]), 4)
        caller, abi = recipe["commands"][1], recipe["commands"][3]
        self.assertNotIn("-ast-dump-filter=dws_probe_", caller["argv"])
        self.assertIn("-ast-dump-filter=dws_probe_", abi["argv"])
        self.assertTrue(all("--no-default-config" in row["argv"] for row in recipe["commands"]))
        self.assertEqual(recipe["budgets"], {"whole_seconds": 180, "rss_bytes": 4294967296,
                         "stage_bytes": 134217728, "total_bytes": 268435456})
        self.assertTrue(recipe["root_admission_required"])
        self.assertFalse(recipe["actual_launched"])
        self.assertNotIn("--version", str(recipe))

    def test_11_macro_free_source_observation_fixture_inverse(self):
        delta = json.loads((HERE / "source-call-fixture-v2-inverse-delta.json").read_bytes())
        original = (HERE / "source_call_fixture_v1.cpp").read_text()
        source = (HERE / "source_call_fixture_v2.cpp").read_text()
        inverse = source
        for edit in reversed(delta["edits"]):
            self.assertEqual(inverse.count(edit["new"]), 1)
            inverse = inverse.replace(edit["new"], edit["old"], 1)
        self.assertEqual(inverse, original)
        self.assertEqual(hashlib.sha256(source.encode()).hexdigest(), delta["new_sha256"])
        for line in source.splitlines():
            if line.strip().startswith("assert("):
                self.assertNotIn("get_", line)
                self.assertNotIn("[", line)

    def test_12_source_cannot_name_private_state_or_bypass_public_mmio_calls(self):
        row = next(row for row in self.declarations if row["name"] == "get_new_tile")
        tu, kw = self.fixture(row);probe = HERE / "compiler_abi_probe_v1.cpp"
        for name in ("dxm_count", "dws_object_pointer", "REG_count", "SPD_data_cacheable", "INSTR_baseaddr"):
            changed = copy.deepcopy(tu)
            changed["inner"][1]["inner"][0]["inner"].append({"kind": "DeclRefExpr", "referencedDecl": {"name": name, "kind": "VarDecl"}})
            with self.assertRaisesRegex(ADAPTER["Refused"], "bypasses"):
                ADAPTER["prepare_unit"](API, full_tu_raw=json.dumps(changed).encode(), abi_raw=stream(abi_roots()),
                    source_path=self.source, source_bytes=self.source.read_bytes(), probe_path=probe, probe_bytes=probe.read_bytes(),
                    declarations=self.declarations, compiler_capture_pin="a" * 64)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({"date": "2026-10-16 ET", "tests": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skips": len(result.skipped), "ABI_roots_synthetic_only": 29,
        "compiler_native_project_child_execution": False}, sort_keys=True))
    sys.exit(0 if result.wasSuccessful() else 1)
