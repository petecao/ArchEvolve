"""Conservative initialized-input CBMC admission; created 2026-10-15 ET.

This checks the entire retained C++ AST closure before summary substitution. It is a
restricted language, not a diagnosis of undefined behavior: safe heap/aggregate,
late-initialization, reference and address-escaping programs may be refused.
No goto-instrument locals-only result is treated as a memory-initialization proof.
"""

import hashlib
import json
from pathlib import Path

from swdb import bounded_std_initialization as standard


def identity():
    here = Path(__file__)
    # Regeneration and state-draw enumeration are policy dependencies, too. A changed
    # generator must invalidate the frozen method even if the three model files match.
    return {"id": "swdb-bounded-initialization-1", "sha256": hashlib.sha256(
        here.read_bytes() + here.with_name("proof_semantics.py").read_bytes()
        + here.with_name("bounded_std_initialization.py").read_bytes()).hexdigest()}


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _children(node):
    return [n for n in node.get("inner", []) if isinstance(n, dict) and n.get("kind")]


def _walk(node):
    yield node
    for child in _children(node):
        yield from _walk(child)


def _qual(node):
    typ = node.get("type") or {}
    return typ.get("desugaredQualType", typ.get("qualType", ""))


def _type(node, scalars):
    qual = _qual(node).replace("const ", "").replace("volatile ", "").strip()
    if qual in scalars or qual == "void":
        return "scalar"
    if qual.endswith("*") and qual[:-1].strip() in scalars:
        return "pointer"
    return "unsupported"


class _Refusal(Exception):
    def __init__(self, reason, node, function):
        self.reason, self.node, self.function = reason, node, function


def analyze(nodes, *, scalar_types, source_sha256, text, external_calls=(), standard_types=None):
    """Generate immutable-origin metadata from clang nodes; never consume candidate certificates.

    Every automatic local is initialized before binding; every admitted pointer
    originates at an initialized harness parameter. Ordinary calls are accepted
    only when their definition is in this same checked closure. Model/summary
    calls remain unsupported until their exact implementations have been audited.
    """
    result = {"check": identity(), "source_sha256": source_sha256,
              "lowering_sha256": hashlib.sha256(text.encode()).hexdigest(), "functions": sorted(nodes),
              "input_domain": "initialized scalar values; each pointer binds a distinct nonnull fully initialized "
                              "primitive buffer of exactly harness_capacity elements (logical sizes do not shorten it)",
              "verdict": "passed", "model_obligations": []}
    standard_types = standard_types or {}
    if standard_types:
        result["standard_policy"] = standard.report(standard_types)
    externals = {row["name"] for row in external_calls}
    # clang's separately filtered dumps give the same declaration different IDs.
    # Match retained function name AND canonical signature across those dumps.
    targets = {(node.get("name"), _qual(node)) for node in nodes.values()}
    for function, definition in nodes.items():
        locals_ = {n["id"] for n in _walk(definition) if n.get("kind") in ("VarDecl", "ParmVarDecl")}
        bound = {}

        def refuse(reason, node):
            raise _Refusal(reason, node, function)

        policy = standard.Policy(standard_types, scalar_types, bound, refuse) if standard_types else None

        def visit(node):
            kind, children = node.get("kind"), _children(node)
            typ = _type(node, scalar_types)
            if policy:
                handled = policy.handle(node, visit, typ)
                if handled is not standard.UNHANDLED:
                    return handled
            if kind.startswith("OMP"):
                refuse("generated OpenMP private/model storage needs a checked initializedness policy", node)
            if kind == "ParmVarDecl":
                if typ == "unsupported":
                    refuse("parameter is not a primitive scalar or one-level primitive buffer pointer", node)
                bound[node["id"]] = typ
                return typ
            if kind == "VarDecl":
                if typ == "unsupported":
                    refuse("automatic arrays, aggregates and reference aliases need a precise initializedness check", node)
                if not children or not node.get("init"):
                    refuse("automatic local has no explicit initializer (late initialization is outside this policy)", node)
                # Bind only AFTER checking the initializer: int x=x must never find itself initialized.
                values = [visit(child) for child in children]
                if typ == "pointer" and standard.is_value(values[-1]) and values[-1].kind == "pointer":
                    bound[node["id"]] = values[-1]
                    return values[-1]
                if typ == "pointer" and values[-1] != "pointer":
                    refuse("pointer initializer has no initialized harness-buffer origin", node)
                bound[node["id"]] = typ
                return typ
            if kind == "DeclRefExpr":
                decl = node.get("referencedDecl") or {}
                if decl.get("kind") in ("FunctionDecl", "CXXMethodDecl", "EnumConstantDecl"):
                    return "scalar"
                if decl.get("id") in locals_:
                    if decl.get("id") not in bound:
                        refuse("local is read before its initializer has been checked", node)
                    return bound[decl["id"]]
                # Source scalar globals are statically initialized; the lowerer separately
                # rejects dynamic/global-dependent initialization. Aggregate/pointer globals
                # would introduce memory roots that the harness does not initialize.
                if decl.get("kind") != "VarDecl" or typ != "scalar":
                    refuse("global or unknown storage has no checked initialized primitive origin", node)
                return "scalar"
            if kind in ("CXXNewExpr", "CXXDeleteExpr", "CXXConstructExpr", "CXXTemporaryObjectExpr",
                        "CXXThisExpr", "MemberExpr", "MaterializeTemporaryExpr", "CXXBindTemporaryExpr",
                        "CXXCtorInitializer"):
                refuse("heap, object lifetime or aggregate storage needs a precise initializedness check", node)
            if kind in ("CallExpr", "CXXMemberCallExpr", "CXXOperatorCallExpr"):
                if not children:
                    refuse("call has no checked target", node)
                # Arguments are ALWAYS checked before the callee exemption, including discarded values.
                for argument in children[1:]:
                    if standard.is_value(visit(argument)):
                        refuse("standard storage cannot escape through an ordinary/model call", argument)
                callee = children[0]
                while callee.get("kind") in ("ImplicitCastExpr", "ParenExpr") and len(_children(callee)) == 1:
                    callee = _children(callee)[0]
                decl = callee.get("referencedDecl") or {}
                if (decl.get("name"), _qual(decl)) not in targets:
                    if decl.get("name") not in externals or typ not in ("scalar", "pointer"):
                        refuse("opaque/model call has no checked initializedness implementation in the retained closure", node)
                    result["model_obligations"].append({"call": decl["name"], "returns": typ})
                    return typ  # provisional root: check() must discharge every exact-content obligation
                if typ != "scalar":
                    refuse("pointer-returning callee has no checked initialized-buffer return policy", node)
                return "scalar"
            if kind == "UnaryOperator":
                op = node.get("opcode")
                if op == "&":
                    refuse("address-taking may expose candidate automatic or untracked storage", node)
                if op in ("++", "--") and children and _type(children[0], scalar_types) == "pointer":
                    refuse("pointer mutation needs flow-sensitive initialized-buffer origin tracking", node)
                values = [visit(child) for child in children]
                if any(standard.is_value(value) for value in values):
                    if policy and op == "*" and typ == "scalar" and len(values) == 1:
                        return policy.read(values[0], 0, node)
                    refuse("standard origin cannot pass through this unary operation", node)
                if op == "*" and (not values or values[0] != "pointer" or typ != "scalar"):
                    refuse("dereference has no initialized primitive buffer origin", node)
                return "scalar" if op == "*" else typ
            if kind == "ArraySubscriptExpr":
                values = [visit(child) for child in children]
                if any(standard.is_value(value) for value in values):
                    if policy and len(values) == 2 and standard.is_value(values[0]) and values[1] == "scalar":
                        return policy.read(values[0], standard.integer(children[1]), node)
                    refuse("raw standard array access has no checked initialized origin", node)
                if values.count("pointer") != 1 or typ != "scalar":
                    refuse("array access has no initialized primitive buffer origin", node)
                return "scalar"
            if kind in ("BinaryOperator", "CompoundAssignOperator"):
                op = node.get("opcode", "")
                if (op == "=" or kind == "CompoundAssignOperator") and children and _type(children[0], scalar_types) == "pointer":
                    refuse("pointer reassignment needs flow-sensitive initialized-buffer origin tracking", node)
                values = [visit(child) for child in children]
                if any(standard.is_value(value) for value in values):
                    refuse("standard origin cannot pass through this binary operation", node)
                if typ == "pointer" and (op not in ("+", "-") or values.count("pointer") != 1):
                    refuse("pointer expression has no unique initialized-buffer origin", node)
                return typ
            allowed = {"CompoundStmt", "DeclStmt", "ReturnStmt", "ForStmt", "WhileStmt", "DoStmt", "IfStmt",
                       "SwitchStmt", "CaseStmt", "DefaultStmt", "BreakStmt", "ContinueStmt", "NullStmt",
                       "LabelStmt", "GotoStmt", "StaticAssertDecl", "EnumDecl", "EnumConstantDecl", "TypedefDecl",
                       "TypeAliasDecl", "IntegerLiteral", "FloatingLiteral", "CXXBoolLiteralExpr", "CharacterLiteral",
                       "StringLiteral", "CXXNullPtrLiteralExpr", "ImplicitCastExpr", "CStyleCastExpr",
                       "CXXStaticCastExpr", "CXXReinterpretCastExpr", "CXXConstCastExpr", "ParenExpr",
                       "ExprWithCleanups", "ConstantExpr", "SubstNonTypeTemplateParmExpr", "CXXDefaultArgExpr",
                       "CXXDefaultInitExpr", "ConditionalOperator", "UnaryExprOrTypeTraitExpr", "CXXScalarValueInitExpr",
                       "ImplicitValueInitExpr", "InitListExpr"}
            if kind not in allowed and not kind.endswith("Attr"):
                refuse(f"AST construct {kind} has no initializedness policy", node)
            if kind in ("CXXDefaultArgExpr", "CXXDefaultInitExpr") and not children:
                refuse("default initializer has not been expanded into checked argument syntax", node)
            values = [visit(child) for child in children]
            if policy:
                handled = policy.wrapper(node, values)
                if handled is not standard.UNHANDLED:
                    return handled
            if kind.endswith("CastExpr") or kind == "ParenExpr":
                if typ == "pointer":
                    if len(values) != 1 or values[0] != "pointer" or _qual(node).replace("const ", "") != _qual(children[0]).replace("const ", ""):
                        refuse("pointer cast has no preserved primitive-buffer origin", node)
                return typ
            if typ == "pointer":
                refuse("pointer-producing expression has no checked initialized-buffer origin", node)
            if kind == "AtomicExpr":
                refuse("atomic model effects need a checked initializedness implementation", node)
            return "scalar"

        try:
            for parameter in (n for n in _children(definition) if n.get("kind") == "ParmVarDecl"):
                visit(parameter)
            for child in _children(definition):
                if child.get("kind") not in ("ParmVarDecl", "TemplateArgument"):
                    visit(child)
        except _Refusal as exc:
            begin = (exc.node.get("range") or {}).get("begin") or exc.node.get("loc") or {}
            result.update(verdict="refused", reason=exc.reason, function=exc.function,
                          source_line=begin.get("_line", begin.get("line")), source_offset=begin.get("offset"))
            break
    result["certificate_sha256"] = _hash(result)
    return result


def check(lowering, cap, *, library=None, model=None):
    """Validate generated metadata and actual input-domain capacity; return a checked admission report."""
    report = dict(getattr(lowering, "bounded_initialization", {}) or {})
    digest = report.pop("certificate_sha256", None)
    if (not report or digest != _hash(report) or report.get("check") != identity()
            or report.get("source_sha256") != lowering.source_sha256
            or report.get("lowering_sha256") != hashlib.sha256(lowering.text.encode()).hexdigest()):
        raise ValueError("bounded initializedness metadata is absent, stale or differs from its generated lowering")
    report["certificate_sha256"] = digest
    report["harness_capacity"] = cap
    standard_ok = standard.valid_report(report.get("standard_policy"), lowering)
    if lowering.std_models and not standard_ok:
        report.update(verdict="refused", reason="standard model lacks an audited exact-content initializedness policy",
                      function=lowering.function, source_line=1)
    if lowering.allocation and not standard_ok:
        report.update(verdict="refused", reason="generated heap allocation needs a precise initializedness check",
                      function=report.get("function", lowering.function), source_line=report.get("source_line", 1))
    if report["verdict"] == "passed" and (report["model_obligations"] or model is not None):
        policy = _dx100_policy(library, model, lowering.defines)
        if policy is None or any(row["call"] not in policy["calls"] or
                row["returns"] == "pointer" and row["call"] != "get_cacheable_tile_pointer"
                for row in report["model_obligations"]):
            report.update(verdict="refused", reason="model call lacks an audited exact-content initializedness policy",
                          function=lowering.function, source_line=1)
        else:
            report["model_policy"] = policy
    if cap == 0 and any(pointer for _name, _typ, pointer in lowering.parameters):
        report.update(verdict="refused", reason="zero-capacity pointer harness has no initialized buffer cells",
                      function=lowering.function, source_line=1)
    return report


# Audited 2026-10-15 ET. Full state/ghost arrays have static initialization;
# swdb_dx_init initializes all slot/tile/register bookkeeping, and the harness
# explicitly draws EVERY tile element. Every model scalar local has an initializer.
# maa_range_loop's is/js arrays are written together at c before incrementing c;
# only the initialized prefix k<c is read afterwards. Source pointers supplied to
# loads/stores/footprint queries must come from initialized harness buffers (checked
# by analyze); CBMC still checks their bounds. The only model pointer producer is
# get_cacheable_tile_pointer, returning the fully drawn dx_tile_data allocation.
DX100_CONTENT = {
    "ghost": "5fa3f12850eba75ccb254b1c1e8ab5c143488046949fbe0e4c965b55ecdb48e9",
    "state": "b371131b4a3a7ef21ad654b0eaffac94b4c63252d63397ee8b67a6b017610701",
    "c": "88298dbb9176640fd8ec2d0c6e31386dd51849411b08df7cebf7f12eab1d22ce",
}
DX100_CALLS = {"add_mem_region", "clear_mem_region", "get_cacheable_tile_pointer", "get_new_reg", "get_new_tile",
               "get_tile_size", "maa_alu_scalar", "maa_const", "maa_indirect_load", "maa_indirect_store_vector",
               "maa_range_loop", "maa_stream_load", "swdb_dx_in_footprint", "wait_ready"}


# 2026-10-16 ET. Exact synthetic scalar trace only; no hardware/source call exemption.
DX100_TRACE_ENTRY = 'semantics.dx100_memory_trace_fixture_0_2'
DX100_TRACE_ID = 'dx100-synthetic-scalar-memory-trace-1'
DX100_TRACE_COMPONENTS = {'ghost': 'a71409828badd1e0cab4e2a73e2c1053caeaebba1dbd0fdb8a66709226231816', 'state': 'ffddb9894fb78489edc9a97361d2b401c4d3c9a4036af67b115142765dea4bca', 'c': '2fe44f7fea203d1f7914db6077b999d03f64a2e43472bd2884eb8e534e775be8', 'logic': 'cee8b8a666997386cd213c9708ffb78b33e8d521f2859bc3ac853f8bd3db112e'}
DX100_TRACE_CONSTANTS = {'DX_K': 2, 'DX_NT': 4, 'DX_NR': 1, 'DX_NM': 2, 'DX_TS': 1}
DX100_TRACE_QUERIES = {'swdb_t28_claim': 'int swdb_t28_claim(int thread, int tile, int bytes)', 'swdb_t28_cpu_write': 'int swdb_t28_cpu_write(int thread, int cell, int value)', 'swdb_t28_cpu_read': 'int swdb_t28_cpu_read(int thread, int cell)', 'swdb_t28_cpu_cas': 'int swdb_t28_cpu_cas(int thread, int cell, int expected, int desired)', 'swdb_t28_issue': 'int swdb_t28_issue(int thread, int access, int region, int cell, int tile, int bytes, int value)', 'swdb_t28_wait': 'int swdb_t28_wait(int tile)', 'swdb_t28_tile_read': 'int swdb_t28_tile_read(int thread, int tile, int bytes)', 'swdb_t28_pending': 'int swdb_t28_pending(int command)', 'swdb_t28_result': 'int swdb_t28_result(int command)', 'swdb_t28_ready': 'int swdb_t28_ready(int tile)'}
DX100_TRACE_SHAPE_SHA256 = '8c1d71f33cfd1ee2d596a63bf7efec9d5bf75b9bb7830cf933a456c4fb46bdf0'
DX100_TRACE_SCOPE = 'Synthetic scalar event traces use abstract cells and tile masks only, with four independently drawn initialized scalar choice cells and a fatal checked choice budget; all real DX100 calls are unsupported. This fixture supplies no header-body, CPU-access, address-translation, typed-value, hardware-counterexample, interleaving-completeness or current-version refinement certificate.'


def _dx100_trace_policy(library, model, defines):
    """Exact initialized scalar trace closure; no parameterized/arbitrary model admission."""
    if library is None or model is None or model.entry != DX100_TRACE_ENTRY:
        return None
    from swdb import artifacts, proof_semantics
    try:
        entry = library.get(model.entry) or {}
        if (_hash(entry) != DX100_TRACE_SHAPE_SHA256
                or proof_semantics._constants(entry, defines) != DX100_TRACE_CONSTANTS
                or any(type(value) is not int for value in entry['constants'].values())
                or set(entry['model']) != {'state', 'c', 'logic'}
                or entry['ghost'].get('capacity') != {'commands': 2}):
            return None
        references = {'ghost': entry['ghost']['acsl'], **entry['model']}
        for reference in references.values():
            library._pin(reference)
        actual = {key: hashlib.sha256(library.resolve(ref).read_bytes()).hexdigest()
                  for key, ref in references.items()}
        if (actual != DX100_TRACE_COMPONENTS
                or artifacts.file_hash(library.files[model.entry]) != model.sha256
                or proof_semantics.model_for(library, model.entry, defines) != model
                or set(model.queries) != set(DX100_TRACE_QUERIES)
                or not set(model.queries) <= set(model.functions)
                or set(model.calls) & set(model.functions)):
            return None
    except (OSError, KeyError, TypeError, ValueError, AttributeError):
        return None
    return {'id': DX100_TRACE_ID, 'entry': model.entry, 'entry_sha256': model.sha256,
            'components': actual, 'generated_sha256': hashlib.sha256(model.c_text.encode()).hexdigest(),
            'tile_objects': [{'name': name, 'elements': extent} for name, extent in model.tile_objects],
            'calls': sorted(DX100_TRACE_QUERIES), 'scope': DX100_TRACE_SCOPE}


def _dx100_policy(library, model, defines):
    if library is None or model is None:
        return None
    from swdb import artifacts, proof_semantics
    entry = library.get(model.entry) or {}
    references = {"ghost": (entry.get("ghost") or {}).get("acsl"),
                  **{key: (entry.get("model") or {}).get(key) for key in ("state", "c")}}
    try:
        actual = {key: hashlib.sha256(library.resolve(ref).read_bytes()).hexdigest()
                  for key, ref in references.items()}
        if actual != DX100_CONTENT or artifacts.file_hash(library.files[model.entry]) != model.sha256:
            return _dx100_trace_policy(library, model, defines)
        fresh = proof_semantics.model_for(library, model.entry, defines)
        if fresh != model:
            return None
    except (OSError, KeyError, TypeError, ValueError):
        return None
    return {"id": "dx100-initialized-inputs-1", "entry": model.entry, "entry_sha256": model.sha256,
            "components": actual, "generated_sha256": hashlib.sha256(model.c_text.encode()).hexdigest(),
            "tile_objects": [{"name": name, "elements": extent} for name, extent in model.tile_objects],
            "calls": sorted((set(model.calls) | set(model.queries)) & set(model.functions) & DX100_CALLS)}


def check_model_input(report, model, library, defines, text):
    """Independent last-boundary check of every required generated state draw."""
    if model is None:
        return
    from swdb import proof_semantics
    if _dx100_policy(library, model, defines) != report.get("model_policy"):
        raise ValueError("model initializedness policy changed after planning")
    if "  swdb_dx_init();" not in text or model.c_text not in text:
        raise ValueError("initialized model setup or exact model body is missing from CBMC input")
    if "  swdb_dx_check_exit();" not in text:
        raise ValueError("checked model poststate boundary is missing from CBMC input")
    for draw in proof_semantics.state_draws(library, model.entry, defines):
        if f"  {draw} = (int) swdb_next();" not in text:
            raise ValueError(f"initialized model input draw is missing: {draw}")
