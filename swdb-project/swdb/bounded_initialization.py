"""Conservative initialized-input CBMC admission; created 2026-10-15 ET.

This checks the entire retained C++ AST closure before summary substitution. It is a
restricted language, not a diagnosis of undefined behavior: safe heap/aggregate,
late-initialization, reference and address-escaping programs may be refused.
No goto-instrument locals-only result is treated as a memory-initialization proof.
"""

import hashlib
import json
from pathlib import Path


def identity():
    return {"id": "swdb-bounded-initialization-1", "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


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


def analyze(nodes, *, scalar_types, source_sha256, text, external_calls=()):
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
    externals = {row["name"] for row in external_calls}
    # clang's separately filtered dumps give the same declaration different IDs.
    # Match retained function name AND canonical signature across those dumps.
    targets = {(node.get("name"), _qual(node)) for node in nodes.values()}
    for function, definition in nodes.items():
        locals_ = {n["id"] for n in _walk(definition) if n.get("kind") in ("VarDecl", "ParmVarDecl")}
        bound = {}

        def refuse(reason, node):
            raise _Refusal(reason, node, function)

        def visit(node):
            kind, children = node.get("kind"), _children(node)
            typ = _type(node, scalar_types)
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
                    visit(argument)
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
                if op == "*" and (not values or values[0] != "pointer" or typ != "scalar"):
                    refuse("dereference has no initialized primitive buffer origin", node)
                return "scalar" if op == "*" else typ
            if kind == "ArraySubscriptExpr":
                values = [visit(child) for child in children]
                if values.count("pointer") != 1 or typ != "scalar":
                    refuse("array access has no initialized primitive buffer origin", node)
                return "scalar"
            if kind in ("BinaryOperator", "CompoundAssignOperator"):
                op = node.get("opcode", "")
                if (op == "=" or kind == "CompoundAssignOperator") and children and _type(children[0], scalar_types) == "pointer":
                    refuse("pointer reassignment needs flow-sensitive initialized-buffer origin tracking", node)
                values = [visit(child) for child in children]
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
    if lowering.allocation:
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
    "c": "ad17837f8dc8aa61de019144f69d6aa6a68b49632caab8a9e48dabd73b6d7b34",
}
DX100_CALLS = {"add_mem_region", "clear_mem_region", "get_cacheable_tile_pointer", "get_new_reg", "get_new_tile",
               "get_tile_size", "maa_alu_scalar", "maa_const", "maa_indirect_load", "maa_indirect_store_vector",
               "maa_range_loop", "maa_stream_load", "swdb_dx_in_footprint", "wait_ready"}


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
            return None
        fresh = proof_semantics.model_for(library, model.entry, defines)
        if fresh != model:
            return None
    except (OSError, KeyError, TypeError, ValueError):
        return None
    return {"id": "dx100-initialized-inputs-1", "entry": model.entry, "entry_sha256": model.sha256,
            "components": actual, "generated_sha256": hashlib.sha256(model.c_text.encode()).hexdigest(),
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
