"""2026-10-16 ET. Inert original-TU/ABI consumer, never a compiler runner.

No project imports. Actual compiler execution/closed runtime/resource/recipe and
source object/CPU expression producers require root admission. All ephemeral
declaration IDs below come from one retained original complete-TU observation.
Filtered ABI roots provide only literal typedef/layout facts; no IDs join TUs.
Original complete JSON tokens are retained after strict streaming whitespace
removal. The DOM parser still refuses above 128 MiB; gzip and minified artifacts
both count against the unchanged 256-MiB retained total.
"""
import copy
import hashlib
import json
from pathlib import Path
import re


ABI_PROBE_SHA = 'c0f4f37ba62992b3de117f6117b134ad0ba663484c172ffa98081952f769bf34'
STAGE_BYTES = 134217728
TOTAL_BYTES = 268435456
TYPE_KEYS = ("uint32_t", "int32_t", "float", "uint64_t", "int64_t", "double")
PRIVATE_PREFIXES = ("dws_", "dwi_", "dxw_", "dxm_", "dxc_", "dxa_", "dxg_", "dxp_", "dxs_", "dxt_", "dxv_", "dxr_", "dxz_")
DIRECT_SOURCE_GLOBALS = {"REG_count", "SPD_count", "SPD_data_cacheable", "SPD_data_noncacheable",
    "SPD_size_noncacheable", "SPD_ready_noncacheable", "REG_noncacheable", "MAA_end_addr", "region_count",
    "INSTR_opcode_datatype_optype_tdst1_tdst2", "INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc", "INSTR_baseaddr"}
ABI_INTS = ("char_bit", "int_bits", "pointer_bits", "little_endian", *(
    family + key for family in ("size_", "align_") for key in TYPE_KEYS),
    "float_radix", "float_mantissa", "double_mantissa", "source_cores", "source_tiles",
    "source_registers", "source_tile_words")


class Refused(ValueError):
    pass


def need(condition, message):
    if not condition: raise Refused(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_decoder():
    def pairs(rows):
        out = {}
        for key, value in rows:
            need(key not in out, "duplicate compiler JSON key")
            out[key] = value
        return out
    def constant(value): raise Refused("nonfinite compiler JSON constant")
    return json.JSONDecoder(object_pairs_hook=pairs, parse_constant=constant)


def parse_json_roots(raw, *, full_tu=False):
    need(type(raw) is bytes and 0 < len(raw) <= STAGE_BYTES, "compiler observation exceeds admitted per-file cap")
    try: text = raw.decode("utf-8")
    except UnicodeError as error: raise Refused("non-UTF8 compiler observation") from error
    decoder = strict_decoder();roots = [];at = 0
    while at < len(text):
        while at < len(text) and text[at].isspace(): at += 1
        if at == len(text): break
        try: node, at = decoder.raw_decode(text, at)
        except (ValueError, RecursionError) as error: raise Refused("malformed compiler JSON stream") from error
        need(isinstance(node, dict), "compiler JSON root must be an object")
        roots.append(node)
    need(roots, "empty compiler observation")
    if full_tu:
        need(len(roots) == 1 and roots[0].get("kind") == "TranslationUnitDecl"
             and isinstance(roots[0].get("inner"), list), "one complete original TU required; filtered dumps cannot join IDs")
    return roots


def resolve_locations(node, source):
    """Same deterministic traversal as c_lowering._resolve_locations.

    Add the normalized coordinates required by the reviewed binder; preserve all
    original fields. This is a compiler-observation parser premise, not a theorem.
    """
    node = copy.deepcopy(node)
    state = {"file": str(Path(source).resolve()), "line": None}
    stack = [node]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            if "offset" in item:
                if "file" in item: state["file"] = item["file"]
                if "line" in item: state["line"] = item["line"]
                item["_file"], item["_line"] = state["file"], state["line"]
                # The binder's source index is line-based; fill only the exact
                # elided line observed by this serialization traversal.
                if "line" not in item and state["line"] is not None: item["line"] = state["line"]
            stack.extend(reversed(list(item.values())))
        elif isinstance(item, list): stack.extend(reversed(item))
    return node


def observed_abi(raw, *, probe_path, api):
    """Read filtered alias/constant roots from the exact retained ABI probe.

    These roots never provide source-call declaration IDs. Every root must be
    exactly one expected global probe declaration at the original probe path.
    """
    need(sha(Path(probe_path).read_bytes()) == ABI_PROBE_SHA, "exact physical ABI probe required")
    roots = parse_json_roots(raw)
    expected = {"dws_probe_" + key for key in (*TYPE_KEYS, *ABI_INTS)}
    selected = {}
    for root in roots:
        root = resolve_locations(root, probe_path)
        name = root.get("name")
        loc = root.get("loc", {})
        need(name in expected and name not in selected and loc.get("_file", loc.get("file")) == str(Path(probe_path).resolve()),
             "unexpected/duplicate/nonlocal ABI probe root")
        selected[name] = root
    need(set(selected) == expected, "complete ABI probe root census required")
    canonical = {}
    for key in TYPE_KEYS:
        root = selected["dws_probe_" + key]
        need(root.get("kind") == "TypeAliasDecl", "exact ABI type-alias root required")
        typ = root.get("type", {})
        value = typ.get("desugaredQualType", typ.get("qualType"))
        need(isinstance(value, str) and re.fullmatch("[a-z]+(?: [a-z]+)*", value), "actual canonical ABI type missing")
        canonical[key] = value
    integers = {}
    for key in ABI_INTS:
        root = selected["dws_probe_" + key]
        need(root.get("kind") == "EnumConstantDecl", "exact ABI enum constant root required")
        constants = [node for node in root.get("inner", []) if node.get("kind") == "ConstantExpr"]
        need(len(constants) == 1 and isinstance(constants[0].get("value"), str)
             and re.fullmatch("[0-9]+", constants[0]["value"]), "one observed integer ConstantExpr required")
        integers[key] = int(constants[0]["value"])
    need(integers["char_bit"] == 8 and integers["little_endian"] == 1, "source byte/endianness domain")
    need([integers[key] for key in ("float_radix", "float_mantissa", "double_mantissa")] == [2, 24, 53],
         "source float representation domain")
    need([integers[key] for key in ("source_cores", "source_tiles", "source_registers", "source_tile_words")] == [4, 32, 32, 16384],
         "actual source geometry differs from pinned backend/MMIO profile")
    abi = {"byte_order": "little", "int_bits": integers["int_bits"], "pointer_bits": integers["pointer_bits"],
        "canonical_types": canonical, "sizes": [integers["size_" + key] for key in TYPE_KEYS],
        "alignments": [integers["align_" + key] for key in TYPE_KEYS]}
    api["validate_abi"](abi)
    return {"abi": abi, "raw_probe_sha256": sha(raw), "root_count": len(roots), "constants": integers,
        "runtime_float_environment_observed": False, "public_admission": False}


def prepare_unit(api, *, full_tu_raw, abi_raw, source_path, source_bytes, probe_path, probe_bytes,
                 declarations, compiler_capture_pin, full_tu_identity, full_tu_compressed_bytes):
    """Prepare all selected original-source calls using one actual TU identity.

    compiler_capture_pin identifies the separately admitted command/input/output
    observation receipt. It is attribution, not a signature or proof that a
    compiler ran. Root must reconcile it with the actual process/raw artifacts.
    Source expression/object/CPU lowering remains mandatory before public use.
    """
    need(isinstance(compiler_capture_pin, str) and re.fullmatch("[0-9a-f]{64}", compiler_capture_pin),
         "root compiler-capture receipt pin required")
    need(type(source_bytes) is bytes and type(probe_bytes) is bytes
         and Path(source_path).read_bytes() == source_bytes and Path(probe_path).read_bytes() == probe_bytes,
         "original source/probe physical inputs changed")
    need(isinstance(full_tu_identity, dict) and set(full_tu_identity) == {
        "schema", "raw_bytes", "raw_sha256", "minified_bytes", "minified_sha256", "raw_limit", "retained_limit",
        "objects", "arrays", "values", "keys", "max_depth", "peak_live_key_charge",
        "complete_JSON_syntax_and_duplicate_key_check", "outside_string_whitespace_only_removed",
        "all_token_spellings_and_key_order_preserved", "AST_nodes_elided", "independent_filtered_parse_join",
        "downstream_complete_TU_consumer_required", "compiler_success_or_source_admission_inferred"},
         "exact complete token identity fields required")
    need(full_tu_identity.get("schema") == "full-tu-token-preserving-identity-1"
         and full_tu_identity.get("raw_limit") == 2147483648 and full_tu_identity.get("retained_limit") == STAGE_BYTES
         and type(full_tu_identity.get("raw_bytes")) is int and 0 < full_tu_identity["raw_bytes"] <= 2147483648
         and isinstance(full_tu_identity.get("raw_sha256"), str) and re.fullmatch("[0-9a-f]{64}", full_tu_identity["raw_sha256"])
         and type(full_tu_raw) is bytes and type(full_tu_identity.get("minified_bytes")) is int
         and 0 < full_tu_identity["minified_bytes"] <= full_tu_identity["raw_bytes"]
         and full_tu_identity.get("minified_bytes") == len(full_tu_raw)
         and full_tu_identity.get("minified_sha256") == sha(full_tu_raw), "exact complete raw/minified identity linkage required")
    for key, bound in {"objects": 20000000, "arrays": 20000000, "values": 20000000,
        "keys": 20000000 * 1024, "max_depth": 256, "peak_live_key_charge": 16777216}.items():
        need(type(full_tu_identity[key]) is int and 0 <= full_tu_identity[key] <= bound, "bounded token census required: " + key)
    need(full_tu_identity["values"] > 0, "nonempty complete token census required")
    for key, value in {"complete_JSON_syntax_and_duplicate_key_check": True,
        "outside_string_whitespace_only_removed": True, "all_token_spellings_and_key_order_preserved": True,
        "AST_nodes_elided": False, "independent_filtered_parse_join": False,
        "downstream_complete_TU_consumer_required": True, "compiler_success_or_source_admission_inferred": False}.items():
        need(type(full_tu_identity.get(key)) is type(value) and full_tu_identity[key] == value, "complete identity profile differs: " + key)
    need(type(full_tu_compressed_bytes) is int and 0 < full_tu_compressed_bytes <= STAGE_BYTES,
         "retained complete original gzip count required")
    need(full_tu_compressed_bytes + len(full_tu_raw) + len(abi_raw) + len(source_bytes) + len(probe_bytes) <= TOTAL_BYTES,
         "retained observations exceed unchanged total output cap")
    source_text = source_bytes.decode("ascii")
    tu = resolve_locations(parse_json_roots(full_tu_raw, full_tu=True)[0], source_path)
    actual_abi = observed_abi(abi_raw, probe_path=probe_path, api=api)
    names = {row["name"] for row in declarations}
    calls = []
    def walk(node, owner=None):
        if node.get("kind") == "FunctionDecl": owner = node
        local_owner = owner and owner.get("loc", {}).get("_file", owner.get("loc", {}).get("file")) == str(Path(source_path).resolve())
        if local_owner:
            name = node.get("name")
            if isinstance(name, str): need(not name.startswith(PRIVATE_PREFIXES), "source declaration collides with private model namespace")
            reference = node.get("referencedDecl", {})
            name = reference.get("name", "")
            need(not name.startswith(PRIVATE_PREFIXES) and name not in DIRECT_SOURCE_GLOBALS,
                 "source bypasses modeled interface through private or direct MMIO state")
        if node.get("kind") == "CallExpr" and owner:
            loc = owner.get("loc", {})
            if loc.get("_file", loc.get("file")) == str(Path(source_path).resolve()):
                children = node.get("inner", [])
                callee = children[0] if children else {}
                while callee.get("kind") in ("ImplicitCastExpr", "ParenExpr") and len(callee.get("inner", [])) == 1:
                    callee = callee["inner"][0]
                reference = callee.get("referencedDecl", {})
                if reference.get("name") in names:
                    need(owner.get("mangledName"), "actual original caller mangled identity required")
                    binding = api["bind_call"](tu, caller=owner["mangledName"], call_range=api["_span"](node),
                        source_path=source_path, source_text=source_text, declarations=declarations, abi=actual_abi["abi"])
                    calls.append(binding)
        for child in node.get("inner", []):
            if isinstance(child, dict): walk(child, owner)
    walk(tu)
    need(calls and len({(row["caller_mangled"], tuple(row["call_range"])) for row in calls}) == len(calls),
         "nonempty distinct source-call census required")
    return {"schema": "whole-interface-original-tu-preparation-2", "calls": calls, "abi_observation": actual_abi,
        "raw_full_tu_sha256": full_tu_identity["raw_sha256"], "parser_full_tu_sha256": sha(full_tu_raw),
        "full_tu_identity": copy.deepcopy(full_tu_identity), "retained_full_tu_archive_bytes": full_tu_compressed_bytes, "normalized_full_tu_sha256": sha(json.dumps(tu, sort_keys=True, separators=(",", ":")).encode()),
        "original_source_sha256": sha(source_bytes), "original_probe_sha256": sha(probe_bytes),
        "compiler_capture_receipt_sha256": compiler_capture_pin, "one_full_tu_for_all_declaration_ids": True,
        "source_expression_and_cpu_pointer_lowering_required": True, "actual_compiler_run_inferred_from_hash": False,
        "original_caller_configuration_gate_required": True, "separate_ABI_probe_proves_caller_macro_scope": False,
        "public_admission": False}


def capture_recipe(*, compiler, project, raw):
    """Prospective four-phase original-buffer Clang-only recipe.

    No version/linker/native/verifier calls. Paths must be bound by root before
    actual use. Root must retain all argv/cwd/input/dependency/stdout/stderr pins,
    bound process-tree/RSS/output resources and exact source/runtime before/after.
    """
    for path in (compiler, project, raw):
        need(isinstance(path, str) and Path(path).is_absolute(), "absolute prospective compiler/project/raw path required")
    base = Path(raw);control = base / "control";out = base / "component"
    include = str(Path(project) / "apps/dx100/benchmarks/API")
    flags = [compiler, "--no-default-config", "-std=c++17", "-fopenmp", "-DNUM_CORES=4", "-DTILE_SIZE=16384", "-I" + include,
             "-I" + str(control / "include")]
    result = []
    for label, source, filtered in (("caller", "source_call_fixture_v2.cpp", False), ("abi", "compiler_abi_probe_v1.cpp", True)):
        original, frozen, dependency = control / source, out / (label + ".ii"), out / (label + ".d")
        result.append({"phase": label + "-preprocess", "argv": [*flags, "-x", "c++", "-E", "-MD", "-MF", str(dependency),
            "-MT", label, str(original), "-o", str(frozen)], "cwd": str(out)})
        ast_flags = ["-Xclang", "-ast-dump-filter=dws_probe_"] if filtered else []
        result.append({"phase": label + "-ast", "argv": [*flags, "-x", "c++", "-fsyntax-only", "-MD", "-MF",
            str(out / (label + ".ast.d")), "-MT", label + "-ast", "-Xclang", "-ast-dump=json", *ast_flags, str(original)], "cwd": str(out),
            "stdout": str(out / (label + ".ast.json")), "source_coordinate_space": "original physical source buffers",
            "same_parse_id_scope": "original caller full TU" if not filtered else "ABI literals only, IDs never joined"})
    return {"commands": result, "budgets": {"whole_seconds": 180, "rss_bytes": 4294967296, "stage_bytes": STAGE_BYTES,
        "total_bytes": TOTAL_BYTES}, "tool_role": "Clang-only source observations; no native/proof run",
        "root_admission_required": True, "actual_launched": False,
        "oversize_policy": "Refuse before accepting; no separate filtered-declaration ID joins or silent cap increases. A streaming/compressed successor requires independent source review and explicit root admission.",
        "dependency_membership_policy": "AST and preprocessing depfiles must have identical independently parsed physical input membership; new/missing/rebound inputs refuse",
        "required_capture_rechecks": ["before each AST: source/probe, used dependencies, compiler/runtime/control pins",
            "after each AST: same physical bytes and dependency membership", "final capture: all source/runtime/control/dependency pins"],
        "dependency_timing_tcb": "First used-header pins only after original preprocessing. AST rereads original source/headers, not frozen .ii; exact original physical coordinates are required, with no invented .ii-to-.cpp mapping. Recheck known input bytes before and after captures, compare both depfiles, and retain frozen preprocessing only as provenance. Between-check transient filesystem changes remain timing TCB."}
