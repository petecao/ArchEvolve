"""2026-10-16 ET. Pure synthetic AST/role controls; never invoke a compiler.

The hand-authored compiler metadata tests the closed consumer protocol. It does
not validate Clang's producer output or establish a real source-call admission.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]


def owned(name):
    path = HERE / (name + ".py")
    namespace = {"__file__": str(path), "__name__": "pure_fixture"}
    exec(compile(ast.parse(path.read_bytes()), str(path), "exec"), namespace)
    return namespace


API, WRAPPERS = owned("whole_interface"), owned("wrappers")
ABI = {"byte_order": "little", "int_bits": 32, "pointer_bits": 64,
       "canonical_types": dict(zip(API["TYPE_KEYS"],
         ("unsigned int", "int", "float", "unsigned long long", "long long", "double"))),
       "sizes": [4, 4, 4, 8, 8, 8], "alignments": [4, 4, 4, 8, 8, 8]}
# Literal independently transcribed header map, not generated from inventory.
LITERAL = {
 "maa_alu_scalar": (8, {"src1": "src1_tile", "rsrc1": "src2_reg", "dst1": "dst_tile"}),
 "maa_alu_vector": (9, {"src1": "src1_tile", "src2": "src2_tile", "dst1": "dst_tile"}),
 "maa_alu_reduce": (10, {"src1": "src1_tile", "rdst1": "dst_reg"}),
 "maa_stream_load": (0, {"rsrc1": "min_reg", "rsrc2": "max_reg", "rsrc3": "stride_reg", "dst1": "dst_tile"}),
 "maa_stream_store": (1, {"rsrc1": "min_reg", "rsrc2": "max_reg", "rsrc3": "stride_reg", "src1": "src_tile"}),
 "maa_indirect_load": (2, {"src1": "idx_tile", "dst1": "dst_tile"}),
 "maa_indirect_store_vector": (4, {"src1": "idx_tile", "src2": "src_tile", "dst1": "dst_tile"}),
 "maa_indirect_store_scalar": (3, {"src1": "idx_tile", "rsrc1": "src_reg", "dst1": "dst_tile"}),
 "maa_indirect_rmw_vector": (6, {"src1": "idx_tile", "src2": "src_tile", "dst1": "dst_tile"}),
 "maa_indirect_rmw_scalar": (5, {"src1": "idx_tile", "rsrc1": "src_reg", "dst1": "dst_tile"}),
 "maa_range_loop": (7, {"src1": "min_tile", "src2": "max_tile", "dst1": "dst_i_tile", "dst2": "dst_j_tile",
                       "rdst1": "last_i_reg", "rdst2": "last_j_reg", "rsrc1": "stride_reg"}),
}
IDS = {"src1": 0, "src2": 4, "dst1": 10, "dst2": 14, "condition": 20,
       "rsrc1": 0, "rsrc2": 4, "rsrc3": 8, "rdst1": 12, "rdst2": 16}


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.declarations = API["inventory"](PROJECT)
        cls.temp = tempfile.TemporaryDirectory(prefix="synthetic-", dir=HERE)
        cls.source = Path(cls.temp.name) / "caller.cpp"
        cls.positive_bindings = 0
        cls.refusals = 0

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def refusal(self, function, *args, **kwargs):
        with self.assertRaises((API["Refused"], ValueError)):
            function(*args, **kwargs)
        type(self).refusals += 1

    def fixture(self, row, dtype=0, explicit=None, abi=None):
        abi = ABI if abi is None else abi
        explicit = row["formal_arity"] if explicit is None else explicit
        canonical = abi["canonical_types"][API["TYPE_KEYS"][dtype]] if row["template"] else None
        text = "void synthetic_caller() { " + row["name"] + ("<" + canonical + ">" if canonical else "")
        begin = len("void synthetic_caller() { ")
        text += "(" + ",".join("0" for _ in range(explicit)) + "); }\n"
        end = text.index(";", begin)
        self.source.write_text(text)
        params = [{"kind": "ParmVarDecl", "name": p["name"], "type": {"qualType": p["type"]}} for p in row["parameters"]]
        template = [{"kind": "TemplateArgument", "type": {"qualType": canonical, "desugaredQualType": canonical}}] if canonical else []
        declaration = {"kind": "FunctionDecl", "id": "source-decl", "name": row["name"],
                       "loc": {"_file": row["header_path"], "line": row["line"]},
                       "type": {"qualType": API["signature"](row, canonical)},
                       "range": {"begin": {"offset": row["source_range"][0]},
                                 "end": {"offset": row["source_range"][1] - 1, "tokLen": 1}},
                       "inner": template + params + [{"kind": "CompoundStmt"}]}
        callee = {"kind": "ImplicitCastExpr", "castKind": "FunctionToPointerDecay", "inner": [
                  {"kind": "DeclRefExpr", "referencedDecl": {"id": "source-decl", "name": row["name"]}}]}
        arguments = [{"kind": "IntegerLiteral", "type": {"qualType": "int"}, "value": "0"} for _ in range(explicit)]
        arguments += [{"kind": "CXXDefaultArgExpr", "type": {"qualType": "int"}} for _ in range(row["formal_arity"] - explicit)]
        call = {"kind": "CallExpr", "range": {"begin": {"offset": begin}, "end": {"offset": end - 1, "tokLen": 1}},
                "inner": [callee] + arguments}
        caller = {"kind": "FunctionDecl", "id": "actual-caller", "name": "synthetic_caller", "mangledName": "_Z16synthetic_callerv",
                  "loc": {"_file": str(self.source)}, "inner": [{"kind": "CompoundStmt", "inner": [call]}]}
        tu = {"kind": "TranslationUnitDecl", "inner": [declaration, caller]}
        kwargs = {"caller": caller["mangledName"], "call_range": [begin, end], "source_path": self.source,
                  "source_text": text, "declarations": self.declarations, "abi": abi}
        return tu, kwargs

    def test_01_inventory_and_all_instances(self):
        self.assertEqual((len(self.declarations), len({r["name"] for r in self.declarations}),
                          sum(r["template"] for r in self.declarations)), (27, 26, 21))
        names = set()
        for row in self.declarations:
            for dtype in range(6) if row["template"] else (0,):
                tu, kw = self.fixture(row, dtype)
                binding = API["bind_call"](tu, **kw)
                names.add(binding["c_name"])
                self.assertEqual(binding["formal_arity"], row["formal_arity"])
                if row["name"] == "maa_range_loop":
                    self.assertEqual(binding["effective_dtype"], 1)
                self.assertEqual(API["recheck_binding"](binding, tu, **kw), binding)
                plan = API["dispatch_plan"](binding, self.declarations, ABI)
                self.assertEqual(plan["c_name"], binding["c_name"])
                self.assertEqual(len(plan["source_arguments"]), row["formal_arity"])
                self.assertFalse(plan["public_admission"])
                type(self).positive_bindings += 1
        self.assertEqual(len(names), 132)
        contracts = {r["name"] for r in self.declarations if not API["contract"](r)["public_supported"]}
        self.assertEqual(len(contracts), 26)

    def test_02_defaults_overloads_and_exact_type_identity(self):
        for row in self.declarations:
            if row["minimum_arity"] < row["formal_arity"]:
                tu, kw = self.fixture(row, explicit=row["minimum_arity"])
                self.assertEqual(API["bind_call"](tu, **kw)["explicit_arity"], row["minimum_arity"])
        rows = [r for r in self.declarations if r["name"] == "get_new_reg"]
        names = set()
        for row in rows:
            tu, kw = self.fixture(row)
            names.add(API["bind_call"](tu, **kw)["c_name"])
        self.assertEqual(names,
                         {"get_new_reg_unsigned_int_args0", "get_new_reg_unsigned_int_args1"})
        row = next(r for r in self.declarations if r["name"] == "maa_alu_scalar")
        linux = copy.deepcopy(ABI)
        linux["canonical_types"].update(uint64_t="unsigned long", int64_t="long")
        tu, kw = self.fixture(row, dtype=3, abi=linux)
        self.assertEqual(API["bind_call"](tu, **kw)["dtype"], 3)
        kw["abi"] = ABI
        self.refusal(API["bind_call"], tu, **kw)
        tu, kw = self.fixture(row)
        binding = API["bind_call"](tu, **kw)
        self.refusal(API["dispatch_plan"], binding, self.declarations, linux)
        selector = next(r for r in self.declarations if r["name"] == "get_data_type")
        tu, kw = self.fixture(selector)
        tu["inner"][0]["inner"][0]["type"] = {"qualType": "unsigned short"}
        self.assertEqual(API["bind_call"](tu, **kw)["dtype"], 6)

    def test_03_binding_refusals(self):
        row = next(r for r in self.declarations if r["name"] == "maa_alu_scalar")
        def mutate_target(tu, key):
            d, caller = tu["inner"]
            c = caller["inner"][0]["inner"][0]
            if key == "macro": c["range"]["begin"]["expansionLoc"] = {"offset": 0}
            elif key == "wrong-callee": c["inner"][0]["inner"][0]["referencedDecl"]["id"] = "other"
            elif key == "static": d["storageClass"] = "static"
            elif key == "attribute": d["inner"].append({"kind": "AlwaysInlineAttr"})
            elif key == "namespace": tu["inner"][0] = {"kind": "NamespaceDecl", "name": "forged", "inner": [d]}
            elif key == "header": d["loc"]["_file"] = "/forged/MAA_gem5.hpp"
            elif key == "line": d["loc"]["line"] += 1
            elif key == "body-span": d["range"]["end"]["offset"] -= 1
            elif key == "body-missing": d["inner"] = [x for x in d["inner"] if x["kind"] != "CompoundStmt"]
            elif key == "signature": d["type"]["qualType"] = "void (int)"
            elif key == "arity": c["inner"].pop()
            elif key == "template-arity": d["inner"].append(copy.deepcopy(d["inner"][0]))
            elif key == "unknown-type": d["inner"][0]["type"] = {"qualType": "unsigned short"}
            elif key == "nested-effect": c["inner"][1] = {"kind": "CallExpr", "inner": []}
            elif key == "volatile": c["inner"][1]["type"]["qualType"] = "volatile int"
            elif key == "default-order": c["inner"][1] = {"kind": "CXXDefaultArgExpr"}
            elif key == "not-statement": caller["inner"][0]["kind"] = "ReturnStmt"
            elif key == "duplicate-id": tu["inner"].append({**d, "name": "forged"})
            elif key == "caller-location": caller["loc"]["_file"] = "/forged/caller.cpp"
        for key in ("macro", "wrong-callee", "static", "attribute", "namespace", "header", "line", "body-span",
                    "body-missing", "signature", "arity", "template-arity", "unknown-type", "nested-effect", "volatile",
                    "default-order", "not-statement", "duplicate-id", "caller-location"):
            tu, kw = self.fixture(row)
            mutate_target(tu, key)
            with self.subTest(key=key): self.refusal(API["bind_call"], tu, **kw)
        tu, kw = self.fixture(row)
        binding = API["bind_call"](tu, **kw)
        tu["unrelated_metadata"] = 1
        self.refusal(API["recheck_binding"], binding, tu, **kw)
        tu, kw = self.fixture(row)
        self.source.write_text(kw["source_text"] + "// changed\n")
        self.refusal(API["bind_call"], tu, **kw)
        tu, kw = self.fixture(row)
        kw["declarations"] = copy.deepcopy(self.declarations)
        kw["declarations"][0]["body_sha256"] = "0" * 64
        self.refusal(API["bind_call"], tu, **kw)
        tu, kw = self.fixture(row)
        kw["source_text"] += "// non-ASCII: \u03b1\n"
        self.source.write_text(kw["source_text"])
        self.refusal(API["bind_call"], tu, **kw)
        for key, value in (("byte_order", "big"), ("int_bits", 64), ("pointer_bits", 32),
                           ("sizes", [4] * 6), ("alignments", [4] * 5)):
            self.refusal(API["validate_abi"], {**ABI, key: value})

    def source_arguments(self, row, operation=0):
        _, literal = LITERAL[row["name"]]
        mapping = {**literal, "condition": "cond_tile"}
        arguments = {parameter: IDS[role] for role, parameter in mapping.items()}
        arguments.update(data=4096, op=operation, o_type=operation)
        return arguments

    def test_04_literal_roles_and_all_66_dtype_maps(self):
        for row in self.declarations:
            if "packet" not in row: continue
            opcode, literal = LITERAL[row["name"]]
            literal = {**literal, "condition": "cond_tile"}
            self.assertEqual(row["packet"]["opcode"], opcode)
            self.assertEqual({role: v["parameter"] for role, v in row["packet"]["operands"].items() if v}, literal)
            for dtype in range(6):
                arguments = self.source_arguments(row)
                result = API["project_operands"](row, dtype, arguments, operation=0 if row["packet"]["operation"] else None)
                masks = {name: 0 for name in result["masks"]}
                actual_dtype = 1 if opcode == 7 else dtype
                for role, parameter in literal.items():
                    reg = role.startswith("r")
                    width = 4 if actual_dtype < 3 else 8
                    if role == "condition" or opcode == 7 or role == "src1" and opcode in (2, 3, 4, 5, 6): width = 4
                    if reg and opcode in (0, 1): width = 4
                    directions = ["write"] if role in ("dst1", "dst2", "rdst1", "rdst2") else ["read"]
                    if opcode == 7 and role in ("rdst1", "rdst2"): directions.append("read")
                    prefix = "register" if reg else "tile"
                    value = IDS[role]
                    physical = (3 if width == 8 else 1) << value
                    for direction in directions:
                        masks[prefix + "_explicit_" + direction] |= 1 << value
                        masks[prefix + "_physical_" + direction] |= physical
                    if not reg and role != "condition": masks["ready_roles"] |= physical
                self.assertEqual(result["masks"], masks)

    def test_05_width_counted_and_refused_domains(self):
        rows = {r["name"]: r for r in self.declarations}
        scalar = rows["maa_alu_scalar"]
        args = self.source_arguments(scalar, 11)
        result = API["project_operands"](scalar, 3, args, operation=11)
        self.assertEqual(result["masks"]["tile_physical_write"], 1 << 10)
        self.assertEqual(result["masks"]["ready_roles"], (3 << 0) | (1 << 10))
        self.assertEqual(result["masks"]["tile_physical_read"] & (1 << 20), 1 << 20)
        for dtype, op in ((0, 16), (2, 6), (5, 10)):
            self.refusal(API["project_operands"], scalar, dtype, self.source_arguments(scalar, op), operation=op)
        self.refusal(API["project_operands"], scalar, 0, self.source_arguments(scalar, 1), operation=0)
        for name, op in (("maa_indirect_rmw_scalar", 1), ("maa_alu_reduce", 8)):
            self.refusal(API["project_operands"], rows[name], 0, self.source_arguments(rows[name], op), operation=op)
        for change in ({"src1_tile": 31}, {"dst_tile": 1}, {"cond_tile": 0}, {"src2_reg": 31}, {"src1_tile": -1}):
            args = {**self.source_arguments(scalar), **change}
            self.refusal(API["project_operands"], scalar, 3, args, operation=0)
        optional = rows["maa_indirect_store_vector"]
        args = {**self.source_arguments(optional), "dst_tile": -1, "cond_tile": -1}
        result = API["project_operands"](optional, 3, args)
        self.assertEqual(result["masks"]["tile_physical_write"], 0)
        self.assertEqual(result["masks"]["ready_roles"], (1 << 0) | (3 << 4))
        self.refusal(API["project_operands"], optional, 3, {**args, "dst_tile": -2})

    def test_06_emitted_wrapper_routes_and_pinned_backend(self):
        header = WRAPPERS["render_adapters"](self.declarations)
        self.assertEqual(len(re.findall(r"static unsigned dwi_maa_(?:alu|stream|indirect|range)\w*\(", header)), 11)
        self.assertNotIn("dwi_get_tile_ready", header)
        fields = ("src1", "src2", "dst1", "dst2", "rdst1", "rdst2", "rsrc1", "rsrc2", "rsrc3", "condition")
        for name, (opcode, roles) in LITERAL.items():
            body = header.split("static unsigned dwi_" + name + "(", 1)[1].split("\n}", 1)[0]
            values = {**roles, "condition": "cond_tile"}
            self.assertIn("struct dwi_packet packet={" + ",".join(values.get(f, "-1") for f in fields) + "};", body)
            self.assertIn("return dwi_atomic_packet(thread," + str(opcode) + ",dtype,", body)
        atomic = header.split("static unsigned dwi_atomic_packet(", 1)[1].split("\n}", 1)[0]
        self.assertLess(atomic.index("dwi_prepare_packet("), atomic.index("build(command"))
        self.assertLess(atomic.index("build(command"), atomic.index("dxc_bind(command,root)"))
        folder = HERE.parent / "28-proof-semantics"
        names = ("numeric_values", "deferred_state", "typed_state", "command_state", "action_state",
                 "region_state", "register_state", "tile_image", "size_state", "setup_state")
        pins = {str((folder / (name + ".py")).resolve()): hashlib.sha256((folder / (name + ".py")).read_bytes()).hexdigest() for name in names}
        backend = WRAPPERS["render_backend"](PROJECT, expected_pins=pins)
        for symbol in ("dxt_binary", "dxa_store", "dxr_assign", "dxg_bind_output", "dxp_bind_output", "dxz_bind_size", "dxs_alloc"):
            self.assertIn(" " + symbol + "(", backend)
        self.refusal(WRAPPERS["render_backend"], PROJECT, expected_pins={})
        self.refusal(WRAPPERS["render_backend"], PROJECT, expected_pins=pins, source_cores=16)
        self.refusal(WRAPPERS["render_backend"], PROJECT, expected_pins=pins, value_bound=16385)


if __name__ == "__main__":
    def no_child(event, args):
        if event.startswith(("subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "os.fork")) or event in {"os.system", "ctypes.dlopen"}:
            raise RuntimeError("no-child source controls: " + event)
    sys.addaudithook(no_child)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({"tests": result.testsRun, "synthetic_bindings": Controls.positive_bindings,
                      "literal_packet_dtype_cases": 66, "refusal_cases": Controls.refusals,
                      "failures": len(result.failures), "errors": len(result.errors),
                      "skips": len(result.skipped), "compiler_or_native": False}, sort_keys=True))
    sys.exit(0 if result.wasSuccessful() else 1)
