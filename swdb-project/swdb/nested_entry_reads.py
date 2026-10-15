"""Checked once-only nested int reads in pure returns (2026-10-15 ET).

Only source sequencing is changed. The ordinary origin checker and WP RTE must
prove the inner read before the captured index can be used by the outer read.
No array-object window or memory initializedness premise is manufactured here.
"""
from dataclasses import dataclass
import json
from pathlib import Path
import re
import tempfile

from swdb import c_lowering, helper_windows as ast, wp_pointer_bounds


class Refused(ValueError):
    """The closed nested-read transformation cannot be certified."""


@dataclass(frozen=True)
class View:
    path: Path
    text: str
    includes: tuple
    certificate: dict
    pins: dict
    assumption: dict


def identity():
    return {"id": "swdb-nested-entry-reads-1", "sha256": ast._hash(Path(__file__).read_bytes())}


def _strip(node):
    while node.get("kind") in {"ParenExpr", "ImplicitCastExpr"}:
        if node.get("kind") == "ImplicitCastExpr" and node.get("castKind") not in {"NoOp", "LValueToRValue"}:
            raise Refused("nested reads require value-preserving plain int conversions")
        node, = ast._children(node)
    return node


def _render(raw, edits):
    for edit in reversed(edits):
        raw = raw[:edit["begin"]] + edit["text"].encode() + raw[edit["end"]:]
    return raw.decode("utf-8")


class _Plan:
    def __init__(self, source, function, entry_windows, includes, defines):
        self.source = Path(source).resolve()
        self.raw = self.source.read_bytes()
        self.text = self.raw.decode("utf-8")
        if re.search(r'/\*@|//@|\b(?:__(?:FILE|LINE|COUNTER|BASE_FILE|INCLUDE_LEVEL)__|__builtin_(?:FILE|FUNCTION|LINE|COLUMN))\b', self.text):
            raise Refused("nested views cannot transport annotations or location-dependent expressions")
        self.windows = entry_windows or {}
        self.tool = c_lowering.locate()
        if self.tool.missing:
            raise Refused(self.tool.missing)
        self.includes = tuple(dict.fromkeys([self.source.parent, *(Path(p).resolve() for p in includes)]))
        self.defines = tuple(defines)
        self.dependencies = ast._dependencies(self.source, self.tool, self.includes, self.defines)
        self.tree = ast._Tree(self.source, self.tool, self.includes, self.defines)
        self.entry = self.tree.entry(function)
        self.parameters = {n["id"]: n for n in ast._children(self.entry) if n.get("kind") == "ParmVarDecl"}
        # This view certifies the unit, not unrelated retained BFS definitions.
        # Its complete executable/data closure must therefore be visible here:
        # locals/parameters and global bodyless imports only. Header/source bodies,
        # global initializers and omitted default-argument ASTs are not projected.
        body = self.tree.body(self.entry)
        local_ids = set(self.parameters) | {n["id"] for n in ast._walk(body) if n.get("kind") == "VarDecl"}
        imported_ids = set()
        for node in ast._walk(body):
            kind = node.get("kind", "")
            if kind == "CallExpr":
                fn = self.tree.binding(node)
                if self.tree.body(fn) is not None:
                    raise Refused("nested view requires source/header helpers to be checked and expanded first")
                imported_ids.add(ast._unwrap(ast._children(node)[0]).get("referencedDecl", {}).get("id"))
            elif kind.endswith("CallExpr") or kind in {"CXXDefaultArgExpr", "CXXDefaultInitExpr", "CXXConstructExpr", "CXXTemporaryObjectExpr", "SourceLocExpr", "PredefinedExpr"}:
                raise Refused("nested view has an opaque call, initializer or source-location dependency")
            elif kind == "VarDecl" and (node.get("storageClass") or node.get("tls")):
                raise Refused("nested view does not project static or thread-local state")
        for node in ast._walk(body):
            if node.get("kind") == "DeclRefExpr":
                ref = node.get("referencedDecl", {})
                if ref.get("id") not in local_ids | imported_ids:
                    raise Refused("nested view data must bind local variables or entry parameters, not globals")
        reserved = set()
        for path in self.dependencies:
            reserved.update(re.findall(rb'\b[A-Za-z_]\w*\b', Path(path).read_bytes()))
        self.reserved = {s.decode("ascii") for s in reserved}
        self.edits, self.captures, self.targets = [], [], {}
        def scan(node, parent=None):
            if node.get("kind") == "ReturnStmt":
                nested = []
                for outer in ast._walk(node):
                    if outer.get("kind") != "ArraySubscriptExpr":
                        continue
                    children = ast._children(outer)
                    if len(children) != 2:
                        raise Refused("nested subscript has unexpected operands")
                    index = _strip(children[1])
                    if index.get("kind") == "ArraySubscriptExpr":
                        nested.append((outer, index))
                if nested:
                    if not parent or parent.get("kind") != "CompoundStmt":
                        raise Refused("nested read return must be an ordinary statement in braces")
                    self.capture_return(node, nested)
                return
            for child in ast._children(node):
                scan(child, node)
        try:
            scan(self.tree.body(self.entry))
        finally:
            scan = None
        self.edits.sort(key=lambda e: e["begin"])
        if any(a["end"] > b["begin"] for a, b in zip(self.edits, self.edits[1:])):
            raise Refused("nested return replacements overlap")
        self.output = _render(self.raw, self.edits)
        shift = 0
        for edit in self.edits:
            edit["view_begin"] = edit["begin"] + shift
            edit["view_end"] = edit["view_begin"] + len(edit["text"].encode())
            shift += len(edit["text"].encode()) - (edit["end"] - edit["begin"])

    def parameter(self, node):
        node = _strip(node)
        ref = node.get("referencedDecl", {})
        parameter = self.parameters.get(ref.get("id")) if node.get("kind") == "DeclRefExpr" else None
        if not parameter or parameter.get("type", {}).get("qualType") != "int *":
            raise Refused("nested reads need direct plain int pointer entry parameters")
        window = self.windows.get("windows", {}).get(parameter["name"])
        if not window or window.get("element_type") != "int":
            raise Refused("nested read pointer has no explicit plain int entry window")
        return parameter["name"]

    def capture_return(self, statement, nested):
        allowed = {"ReturnStmt", "ParenExpr", "ImplicitCastExpr", "ArraySubscriptExpr", "DeclRefExpr", "IntegerLiteral", "BinaryOperator", "UnaryOperator"}
        for node in ast._walk(statement):
            kind = node.get("kind")
            if kind not in allowed or "volatile" in node.get("type", {}).get("qualType", ""):
                raise Refused("nested return must contain only nonvolatile pure primitive expressions")
            if kind == "BinaryOperator" and node.get("opcode") not in {"+", "-", "*", "/", "%", "&", "|", "^", "==", "!=", "<", ">", "<=", ">="}:
                raise Refused("nested return cannot reorder conditional evaluation or mutation")
            if kind == "UnaryOperator" and node.get("opcode") not in {"+", "-", "!", "~"}:
                raise Refused("nested return cannot transport address, dereference, or mutation operators")
            if kind == "ImplicitCastExpr" and node.get("castKind") not in {"NoOp", "LValueToRValue", "IntegralCast"}:
                raise Refused("nested return contains an unsupported conversion")
            # bool-to-int conversions of comparisons are harmless, but index reads
            # below have the stricter exact plain-int identity policy.
            if kind == "ImplicitCastExpr" and node.get("castKind") == "IntegralCast":
                child, = ast._children(node)
                if child.get("type", {}).get("qualType") != "bool" or node.get("type", {}).get("qualType") != "int":
                    raise Refused("nested return cannot transport narrowing integer conversions")
        begin, end = ast._span(statement, self.source)
        suffix = re.match(rb'\s*;', self.raw[end:])
        if not suffix:
            raise Refused("nested return terminator is not explicit")
        end += suffix.end()
        replacements, rows = [], []
        for outer, inner in nested:
            outer_root = self.parameter(ast._children(outer)[0])
            inner_root = self.parameter(ast._children(inner)[0])
            if inner.get("type", {}).get("qualType") != "int" or outer.get("type", {}).get("qualType") != "int":
                raise Refused("nested reads require exact int elements")
            try:
                wp_pointer_bounds._scalar_math(ast._children(inner)[1])
            except wp_pointer_bounds.Refused as exc:
                raise Refused(str(exc)) from None
            ib, ie = ast._span(inner, self.source)
            if any(a <= ib < b or ib <= a < ie for a, b, _ in replacements):
                raise Refused("more than one nested index level is unsupported")
            serial = len(self.captures)
            name = f"swdb_nested_read_{serial}"
            while name in self.reserved:
                serial += 1
                name = f"swdb_nested_read_{serial}"
            self.reserved.add(name)
            row = {"name": name, "inner_parameter": inner_root, "outer_parameter": outer_root,
                   "source_read": {"begin": ib, "end": ie}, "source_statement": {"begin": begin, "end": end}}
            self.captures.append(row)
            rows.append((inner, row))
            replacements.append((ib, ie, name))
        text = self.raw[begin:end]
        for ib, ie, name in sorted(replacements, reverse=True):
            text = text[:ib-begin] + name.encode() + text[ie-begin:]
        declarations = [f'int {row["name"]} = ' + self.raw[ast._span(inner, self.source)[0]:ast._span(inner, self.source)[1]].decode() + ';' for inner, row in rows]
        replacement = '{ ' + ' '.join(declarations) + ' ' + text.decode() + ' }'
        replacement += "\n" * max(0, self.raw[begin:end].count(b"\n") - replacement.count("\n"))
        self.edits.append({"begin": begin, "end": end, "text": replacement})
        self.targets[statement["id"]] = rows

    def original_offset(self, offset):
        shift = 0
        for edit in self.edits:
            if offset < edit["view_begin"]:
                break
            if offset < edit["view_end"]:
                raise Refused("unexpected source declaration in nested capture block")
            shift += (edit["view_end"] - edit["view_begin"]) - (edit["end"] - edit["begin"])
        return offset - shift

    def verify(self, path):
        if Path(path).read_text() != self.output or re.search(r'/\*@|//@', self.output):
            raise Refused("nested view text or annotations drifted")
        # Independently check unedited byte regions, not just the renderer's
        # digest or the reachable AST. No declaration/attribute/directive outside
        # the designated return statements can be altered by a renderer fault.
        output = self.output.encode()
        original_cursor = view_cursor = 0
        for edit in self.edits:
            if output[view_cursor:edit["view_begin"]] != self.raw[original_cursor:edit["begin"]]:
                raise Refused("nested renderer changed bytes outside its source statements")
            original_cursor, view_cursor = edit["end"], edit["view_end"]
        if output[view_cursor:] != self.raw[original_cursor:]:
            raise Refused("nested renderer changed bytes after its source statements")
        actual = ast._Tree(path, self.tool, self.includes, self.defines)
        headers = lambda deps, source: {p: h for p, h in deps.items() if p != str(source)}
        original_headers = headers(self.dependencies, self.source)
        if headers(ast._dependencies(path, self.tool, self.includes, self.defines), Path(path).resolve()) != original_headers:
            raise Refused("nested view changed header resolution")
        consumed = []
        def match(left, right, captures=None):
            captures = captures or {}
            if left.get("id") in captures:
                target = _strip(right)
                if target.get("kind") != "DeclRefExpr" or target.get("referencedDecl", {}).get("id") != captures[left["id"]]:
                    raise Refused("nested index is not the exact captured read")
                return
            if left.get("id") in self.targets:
                rows = self.targets[left["id"]]
                statements = ast._children(right)
                if right.get("kind") != "CompoundStmt" or len(statements) != len(rows) + 1:
                    raise Refused("nested view added or removed capture operations")
                bindings = {}
                for (inner, row), declaration in zip(rows, statements):
                    decls = ast._children(declaration)
                    if declaration.get("kind") != "DeclStmt" or len(decls) != 1:
                        raise Refused("nested capture is not an ordinary local value initialization")
                    decl = decls[0]
                    if decl.get("kind") != "VarDecl" or decl.get("name") != row["name"] or decl.get("type", {}).get("qualType") != "int" or len(ast._children(decl)) != 1:
                        raise Refused("nested capture type, binding or initializer drifted")
                    init = _strip(ast._children(decl)[0])
                    match(inner, init)
                    bindings[inner["id"]] = decl["id"]
                    consumed.append(row)
                # Bypass target recognition only for this return, retaining all
                # inner read substitutions and all other source operations.
                if ast._signature(left) != ast._signature(statements[-1]):
                    raise Refused("nested view lost its original return")
                for a, b in zip(ast._children(left), ast._children(statements[-1])):
                    match(a, b, bindings)
                if len(ast._children(left)) != len(ast._children(statements[-1])):
                    raise Refused("nested return expression count drifted")
                return
            if ast._signature(left) != ast._signature(right) or len(ast._children(left)) != len(ast._children(right)):
                raise Refused("nested view changed an original executable operation")
            if "referencedDecl" in left and self.tree.declaration_key(left["referencedDecl"]) != actual.declaration_key(right.get("referencedDecl", {}), self.original_offset, self.source):
                raise Refused("nested view changed an original declaration binding")
            for a, b in zip(ast._children(left), ast._children(right)):
                match(a, b, captures)
        try:
            match(self.tree.body(self.entry), actual.body(actual.entry(self.entry["name"])))
            if consumed != self.captures or Path(path).read_text() != self.output or ast._dependencies(self.source, self.tool, self.includes, self.defines) != self.dependencies:
                raise Refused("nested source, dependencies or read coverage drifted")
        finally:
            match = None
        return original_headers

    def certificate(self, headers):
        return {"version": 1, "source_sha256": ast._hash(self.raw), "view_sha256": ast._hash(self.output.encode()),
                "function": self.entry["name"], "captures": self.captures, "entry_windows": self.windows,
                "dependencies": headers, "includes": [str(p) for p in self.includes], "defines": list(self.defines),
                "checker": identity(), "parser_sha256": ast._hash(Path(c_lowering.__file__).read_bytes()),
                "ast_check": ast.identity(), "executable_closure": "entry locals/parameters and bodyless global imports; no global/default/location dependencies"}


def prepare(source, function, *, entry_windows, includes=(), defines=(), scratch):
    try:
        plan = _Plan(source, function, entry_windows, includes, defines)
        if not plan.edits:
            return None
        folder = Path(scratch)
        folder.mkdir(parents=True, exist_ok=True)
        path = Path(tempfile.mkdtemp(prefix="nested-read-", dir=folder)) / "source.cc"
        path.write_text(plan.output)
        certificate = plan.certificate(plan.verify(path))
        pins = {"nested_read_check": identity(), "nested_read_certificate":
                {"id": "swdb-nested-read-certificate-1", "sha256": ast._hash(certificate)}}
        assumption = {"kind": "trusted_tool", "text": "The checked nested-read view evaluates each original plain int index read once in an effect-free return, before its outer read; all input-window, validity and initializedness obligations remain checked."}
        return View(path, plan.output, plan.includes, certificate, pins, assumption)
    except (ast.Refused, UnicodeError) as exc:
        raise Refused(str(exc)) from None


def check_view(source, function, view, *, entry_windows, includes=(), defines=()):
    try:
        if not isinstance(view, View) or not view.path.is_file() or view.path.read_text() != view.text:
            raise Refused("nested source view file changed before replay")
        plan = _Plan(source, function, entry_windows, includes, defines)
        if not plan.edits or plan.output != view.text or plan.includes != view.includes:
            raise Refused("nested source/view correspondence changed")
        certificate = plan.certificate(plan.verify(view.path))
        pins = {"nested_read_check": identity(), "nested_read_certificate":
                {"id": "swdb-nested-read-certificate-1", "sha256": ast._hash(certificate)}}
        if certificate != view.certificate or pins != view.pins:
            raise Refused("nested source certificate or checker pins changed")
    except (ast.Refused, UnicodeError) as exc:
        raise Refused(str(exc)) from None
