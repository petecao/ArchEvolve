"""Checked contextual views for transparent helpers (2026-10-15 ET).

This is a trusted source transformation, not a helper-contract assumption.  A
second Clang AST is compared recursively with the original unit and each expanded
helper body.  The normal pointer-origin checker still has to certify every call
in the resulting unit.  No helper entry window or ACSL premise is synthesized.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import tempfile

from swdb import c_lowering


class Refused(ValueError):
    """The closed helper transformation could not be certified."""


@dataclass(frozen=True)
class View:
    path: Path
    text: str
    includes: tuple
    certificate: dict
    pins: dict
    assumption: dict


def _hash(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def identity():
    return {"id": "swdb-helper-windows-1", "sha256": _hash(Path(__file__).read_bytes())}


def _children(node):
    return node.get("inner", [])


def _walk(node):
    yield node
    for child in _children(node):
        yield from _walk(child)


def _unwrap(node):
    while node.get("kind") == "ImplicitCastExpr":
        if node.get("castKind") not in {"LValueToRValue", "FunctionToPointerDecay"}:
            raise Refused("helper operand has a nonidentity implicit conversion")
        node, = _children(node)
    return node


def _span(node, path):
    limits = node.get("range", {})
    begin, end = limits.get("begin", {}), limits.get("end", {})
    if any("offset" not in loc or "expansionLoc" in loc or "spellingLoc" in loc
           or Path(loc.get("_file", "")).resolve() != path for loc in (begin, end)):
        raise Refused("helper source position is missing, imported, or macro-expanded")
    return begin["offset"], end["offset"] + end.get("tokLen", 0)


def _dependencies(path, tool, includes, defines):
    """Clang's complete preprocessor dependency set, including macro-only headers."""
    command = [*tool.command, "-x", "c++", f"-std={c_lowering.STD}", "-fopenmp",
               "-M", "-MT", "swdb_helper_window", f"-I{Path(path).parent}",
               *(f"-I{p}" for p in includes), *(f"-D{d}" for d in defines), str(path)]
    try:
        done = subprocess.run(command, capture_output=True, text=True,
                              timeout=c_lowering.TIMEOUT_SECONDS)
        if done.returncode or not done.stdout.startswith("swdb_helper_window:"):
            raise Refused("Clang could not inventory helper source dependencies")
        names = shlex.split(done.stdout.split(":", 1)[1].replace("\\\n", " "))
        return {str(Path(name).resolve()): _hash(Path(name).read_bytes()) for name in names}
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise Refused(f"helper dependency inventory failed: {exc}") from None


class _Tree:
    def __init__(self, path, tool, includes, defines):
        self.path = Path(path).resolve()
        try:
            trees = c_lowering._dump(tool, self.path, "", includes, defines)
        except c_lowering.LoweringError as exc:
            raise Refused(str(exc)) from None
        self.root, = trees
        self.nodes = {n["id"]: n for n in _walk(self.root) if "id" in n}
        self.functions = {}
        self.global_ids = set()
        # Only actual translation-unit/linkage declarations are global. Namespace,
        # member and template declarations cannot acquire a name-only exemption.
        def globals_in(node):
            for child in _children(node):
                if child.get("kind") == "LinkageSpecDecl":
                    globals_in(child)
                elif child.get("kind") == "FunctionDecl":
                    self.global_ids.add(child["id"])
                    self.functions.setdefault(child.get("name"), []).append(child)
        globals_in(self.root)

    def body(self, fn):
        return next((n for n in _children(fn) if n.get("kind") == "CompoundStmt"), None)

    def binding(self, call):
        if call.get("kind") != "CallExpr" or not _children(call):
            raise Refused("helper body contains an operation other than a direct call")
        ref = _unwrap(_children(call)[0]).get("referencedDecl", {})
        fn = self.nodes.get(ref.get("id"))
        if not fn or fn.get("id") not in self.global_ids:
            raise Refused("helper call is not bound to a global function declaration")
        declarations = self.functions[fn["name"]]
        if any(n.get("type") != fn.get("type") or n.get("mangledName") != fn.get("mangledName")
               for n in declarations):
            raise Refused("overloaded helper/model functions are outside the checked grammar")
        if any(n.get("kind", "").endswith("Attr") for d in declarations for n in _children(d)):
            raise Refused("helper/model declaration attributes are unsupported")
        definitions = [d for d in declarations if self.body(d) is not None]
        if len(definitions) > 1:
            raise Refused("helper definition is ambiguous")
        return definitions[0] if definitions else fn

    def entry(self, function):
        definitions = [d for d in self.functions.get(function, []) if self.body(d) is not None]
        if len(definitions) != 1:
            raise Refused("unit must have one unambiguous global definition")
        return definitions[0]

    def declaration_key(self, ref, offset_map=lambda x: x, source=None):
        node = self.nodes.get(ref.get("id"))
        if node is None:
            raise Refused("referenced declaration is missing from complete AST")
        loc = node.get("loc", {})
        path = Path(loc.get("_file", "")).resolve()
        offset = loc.get("offset")
        if path == self.path:
            path = source or path
            offset = offset_map(offset)
        return (str(path), offset, node.get("kind"), node.get("name"), node.get("type"))


def _operand(node, tree, substitutions):
    node = _unwrap(node)
    kind = node.get("kind")
    if kind == "IntegerLiteral" and node.get("type", {}).get("qualType") == "int":
        return str(int(node["value"]))
    if kind == "UnaryOperator" and node.get("opcode") == "-":
        child, = _children(node)
        if child.get("kind") == "IntegerLiteral" and child.get("type", {}).get("qualType") == "int":
            return "-" + str(int(child["value"]))
    if kind == "DeclRefExpr":
        ref = node.get("referencedDecl", {})
        if ref.get("id") in substitutions:
            return substitutions[ref["id"]]
        declaration = tree.nodes.get(ref.get("id"), {})
        if substitutions or declaration.get("kind") not in {"ParmVarDecl", "VarDecl"}:
            raise Refused("helper operand is not a formal or stable caller binding")
        if declaration.get("type", {}).get("qualType") not in {"int", "int *"}:
            raise Refused("caller operand is not a plain int or int pointer")
        return declaration["name"]
    raise Refused("helper arguments must be bare bindings or int literals")


def _signature(node):
    # Compare semantic AST shape, independent of Clang's session IDs/locations and
    # used-bit changes caused by removing reachable calls to the original helpers.
    keys = ("kind", "type", "opcode", "castKind", "value", "name", "isPostfix",
            "valueCategory", "isArrow", "storageClass", "isImplicit")
    return {key: node[key] for key in keys if key in node}


class _Plan:
    def __init__(self, source, function, includes, defines, imported_calls):
        self.source = Path(source).resolve()
        self.raw = self.source.read_bytes()
        try:
            self.text = self.raw.decode("utf-8")
        except UnicodeDecodeError:
            raise Refused("helper view requires UTF-8 source") from None
        if re.search(r'/\*@|//@|\b(?:__(?:FILE|LINE|COUNTER|BASE_FILE|INCLUDE_LEVEL)__|__builtin_(?:FILE|FUNCTION|LINE|COLUMN))\b', self.text):
            raise Refused("helper views do not transport annotations or location-dependent builtins")
        self.tool = c_lowering.locate()
        if self.tool.missing:
            raise Refused(self.tool.missing)
        self.includes = tuple(dict.fromkeys([self.source.parent, *(Path(p).resolve() for p in includes)]))
        self.defines = tuple(defines)
        self.dependencies = _dependencies(self.source, self.tool, self.includes, self.defines)
        if self.dependencies.get(str(self.source)) != _hash(self.raw):
            raise Refused("source changed while collecting helper dependencies")
        self.imports = dict(imported_calls)
        self.tree = _Tree(self.source, self.tool, self.includes, self.defines)
        self.entry = self.tree.entry(function)
        if any(self.tree.body(fn) is not None for name in self.imports for fn in self.tree.functions.get(name, [])):
            raise Refused("an imported model name has a source definition")
        if any(n.get("kind") == "SourceLocExpr" for n in _walk(self.tree.body(self.entry))):
            raise Refused("location-dependent source expressions cannot move into a helper view")
        self.contexts, self.models, self.edits = [], [], []
        self.reserved = set(re.findall(r'\b[A-Za-z_]\w*\b', self.text))
        self.helpers = set()
        body = self.tree.body(self.entry)
        # Scan every root call, including calls nested in expressions. Only complete
        # compound-statement children may be replaced; no header/argument evaluation
        # order is changed by silently moving an expression into a new block.
        def scan(node, parent=None):
            if node.get("kind") == "CallExpr":
                fn = self.tree.binding(node)
                if self.tree.body(fn) is not None:
                    if not parent or parent.get("kind") != "CompoundStmt":
                        raise Refused("helper call must be a standalone statement in braces")
                    start, end = _span(node, self.source)
                    suffix = re.match(rb'\s*;', self.raw[end:])
                    if not suffix:
                        raise Refused("helper statement terminator is not explicit")
                    end += suffix.end()
                    replacement = self.expand(node, {}, ())
                    replacement += "\n" * self.raw[start:end].count(b"\n")
                    self.edits.append({"begin": start, "end": end, "text": replacement})
                    return
            for child in _children(node):
                scan(child, node)
        scan(body)
        self.edits.sort(key=lambda e: e["begin"])
        if any(a["end"] > b["begin"] for a, b in zip(self.edits, self.edits[1:])):
            raise Refused("overlapping helper contexts")
        # Clang ranges are byte offsets, including when comments or identifiers
        # contain UTF-8. Preserve all unedited bytes and measure replacement
        # lengths in the same coordinate system as the independent AST checker.
        output = self.raw
        for edit in reversed(self.edits):
            output = output[:edit["begin"]] + edit["text"].encode("utf-8") + output[edit["end"]:]
        self.output = output.decode("utf-8")
        shift = 0
        for edit in self.edits:
            edit["view_begin"] = edit["begin"] + shift
            size = len(edit["text"].encode("utf-8"))
            edit["view_end"] = edit["view_begin"] + size
            shift += size - (edit["end"] - edit["begin"])

    def expand(self, call, substitutions, stack):
        fn = self.tree.binding(call)
        if fn["id"] in stack:
            raise Refused("recursive helper graph")
        if fn.get("type", {}).get("qualType", "").split(" (")[0] != "void":
            raise Refused("only void primitive helpers can be expanded")
        start, end = _span(fn, self.source)
        self.helpers.add(fn["name"])
        params = [n for n in _children(fn) if n.get("kind") == "ParmVarDecl"]
        arguments = _children(call)[1:]
        if fn.get("variadic") or len(params) != len(arguments):
            raise Refused("helper formal/actual arity mismatch")
        if any(p.get("type", {}).get("qualType") not in {"int", "int *"} for p in params):
            raise Refused("helper formals must be plain int or int pointer")
        plain_type = "void (" + ", ".join(p["type"]["qualType"] for p in params) + ")"
        if fn.get("type", {}).get("qualType") != plain_type:
            raise Refused("helper exception specifications and calling conventions are unsupported")
        # No macros may hide executable operations, declarations, or annotation
        # placement. Every helper node is explicitly located in the original file.
        for node in _walk(fn):
            if node.get("range"):
                _span(node, self.source)
        context = {"helper": fn["name"], "helper_begin": start, "helper_end": end,
                   "formal_names": [], "arguments": [], "depth": len(stack)}
        serial = len(self.contexts)
        self.contexts.append(context)
        env, pieces = {}, []
        for index, (param, arg) in enumerate(zip(params, arguments)):
            name = f"swdb_hw_{serial}_arg_{index}"
            while name in self.reserved:
                name += "_"
            self.reserved.add(name)
            actual = _operand(arg, self.tree, substitutions)
            if _unwrap(arg).get("type") != param.get("type"):
                raise Refused("helper parameter capture would convert the actual value")
            env[param["id"]] = name
            context["formal_names"].append(name)
            context["arguments"].append(actual)
            pieces.append(f'{param["type"]["qualType"]} {name} = {actual};')
        body = self.tree.body(fn)
        if body is None:
            raise Refused("missing helper body")
        for statement in _children(body):
            callee = self.tree.binding(statement)
            if self.tree.body(callee) is not None:
                pieces.append(self.expand(statement, env, (*stack, fn["id"])))
            else:
                pin = self.imports.get(callee["name"])
                if not isinstance(pin, dict) or not isinstance(pin.get("id"), str) or not re.fullmatch(r'[0-9a-f]{64}', str(pin.get("sha256"))):
                    raise Refused("helper external call has no exact imported model pin")
                args = [_operand(a, self.tree, env) for a in _children(statement)[1:]]
                self.models.append({"callee": callee["name"], "type": callee["type"],
                                    "mangled_name": callee.get("mangledName"), "pin": pin,
                                    "context": serial, "arguments": args})
                pieces.append(f'::{callee["name"]}({", ".join(args)});')
        return "{ " + " ".join(pieces) + " }"

    def original_offset(self, offset):
        if offset is None:
            return None
        shift = 0
        for edit in self.edits:
            if offset < edit["view_begin"]:
                break
            if offset < edit["view_end"]:
                raise Refused("unmapped generated declaration outside a checked clone")
            shift += (edit["view_end"] - edit["view_begin"]) - (edit["end"] - edit["begin"])
        return offset - shift

    def verify(self, path):
        """Independent output AST matching against original bodies and bindings."""
        if Path(path).read_text() != self.output:
            raise Refused("generated helper text changed before AST certification")
        if _dependencies(self.source, self.tool, self.includes, self.defines) != self.dependencies:
            raise Refused("source dependency changed before AST certification")
        view_dependencies = _dependencies(path, self.tool, self.includes, self.defines)
        original_headers = {p: h for p, h in self.dependencies.items() if p != str(self.source)}
        view_headers = {p: h for p, h in view_dependencies.items() if p != str(Path(path).resolve())}
        if view_headers != original_headers:
            raise Refused("generated source changed include resolution")
        actual = _Tree(path, self.tool, self.includes, self.defines)
        contexts = iter(self.contexts)
        consumed = []
        def match(left, right, env=None):
            env = env or {}
            if left.get("kind") == "CallExpr":
                fn = self.tree.binding(left)
                if self.tree.body(fn) is not None:
                    clone(left, right, env)
                    return
            if _signature(left) != _signature(right) or len(_children(left)) != len(_children(right)):
                raise Refused("generated AST changed an original executable operation")
            if "referencedDecl" in left:
                lr, rr = left["referencedDecl"], right.get("referencedDecl", {})
                if lr.get("id") in env:
                    if rr.get("id") != env[lr["id"]]:
                        raise Refused("generated argument uses a different captured formal")
                elif self.tree.declaration_key(lr) != actual.declaration_key(rr, self.original_offset, self.source):
                    raise Refused("generated view changed a source declaration binding")
            for a, b in zip(_children(left), _children(right)):
                match(a, b, env)
        def clone(call, block, outer):
            fn = self.tree.binding(call)
            context = next(contexts, None)
            if not context or context["helper"] != fn["name"] or block.get("kind") != "CompoundStmt":
                raise Refused("missing or reordered helper clone")
            consumed.append(context)
            params = [n for n in _children(fn) if n.get("kind") == "ParmVarDecl"]
            statements = _children(block)
            source_statements = _children(self.tree.body(fn))
            if len(statements) != len(params) + len(source_statements):
                raise Refused("clone added or removed executable operations")
            env = {}
            for param, arg, name, statement in zip(params, _children(call)[1:], context["formal_names"], statements):
                declarations = _children(statement)
                if statement.get("kind") != "DeclStmt" or len(declarations) != 1:
                    raise Refused("clone formal is not one ordinary value capture")
                declaration, = declarations
                if declaration.get("kind") != "VarDecl" or declaration.get("name") != name or declaration.get("type") != param.get("type") or len(_children(declaration)) != 1:
                    raise Refused("clone formal type, name, or initialization drifted")
                match(arg, _children(declaration)[0], outer)
                env[param["id"]] = declaration["id"]
            for original, generated in zip(source_statements, statements[len(params):]):
                match(original, generated, env)
        try:
            match(self.tree.body(self.entry), actual.body(actual.entry(self.entry["name"])))
            if next(contexts, None) is not None or len(consumed) != len(self.contexts):
                raise Refused("not every source helper context was checked")
            for node in _walk(actual.body(actual.entry(self.entry["name"]))):
                if node.get("kind") == "CallExpr" and actual.body(actual.binding(node)) is not None:
                    raise Refused("reachable source helper remains after contextual expansion")
            if Path(path).read_text() != self.output or _dependencies(self.source, self.tool, self.includes, self.defines) != self.dependencies:
                raise Refused("source/view changed during independent AST certification")
            return original_headers
        finally:
            # The mutually recursive closures otherwise retain both full TU
            # trees until cyclic GC, overlapping the next source replay/verifier.
            match = clone = None

    def certificate(self, dependencies):
        return {"version": 1, "source_sha256": _hash(self.raw), "view_sha256": _hash(self.output.encode()),
                "function": self.entry["name"], "contexts": self.contexts,
                "context_count": len(self.contexts), "model_calls": self.models,
                "model_call_count": len(self.models), "dependencies": dependencies,
                "includes": [str(p) for p in self.includes], "defines": list(self.defines),
                "clang": {"command": list(self.tool.command), "version": self.tool.version},
                "checker": identity(), "parser_sha256": _hash(Path(c_lowering.__file__).read_bytes())}


def prepare(source, function, *, includes=(), defines=(), imported_calls=None, scratch):
    plan = _Plan(source, function, includes, defines, imported_calls or {})
    if not plan.edits:
        return None
    folder = Path(scratch)
    folder.mkdir(parents=True, exist_ok=True)
    private = Path(tempfile.mkdtemp(prefix="helper-window-", dir=folder))
    path = private / "source.cc"
    path.write_text(plan.output)
    certificate = plan.certificate(plan.verify(path))
    pins = {"helper_window_check": identity(),
            "helper_window_certificate": {"id": "swdb-helper-window-certificate-1", "sha256": _hash(certificate)}}
    assumption = {"kind": "trusted_tool", "text": "The checked contextual helper transformation preserves by-value argument captures, original call order and helper body effects; no helper requires or array window is assumed."}
    return View(path, plan.output, plan.includes, certificate, pins, assumption)


def check_view(source, function, view, *, includes=(), defines=(), imported_calls=None):
    if not isinstance(view, View) or not view.path.is_file() or view.path.read_text() != view.text:
        raise Refused("helper view file drifted before fresh source replay")
    plan = _Plan(source, function, includes, defines, imported_calls or {})
    if not plan.edits or plan.output != view.text or plan.includes != view.includes:
        raise Refused("helper source/view correspondence drifted")
    certificate = plan.certificate(plan.verify(view.path))
    expected_pins = {"helper_window_check": identity(), "helper_window_certificate":
                     {"id": "swdb-helper-window-certificate-1", "sha256": _hash(certificate)}}
    if certificate != view.certificate or expected_pins != view.pins:
        raise Refused("helper context certificate or imported provenance drifted")
