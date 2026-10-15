"""The C++ of a proof unit without a C lowering: the unit, its same-file callees and globals, cut from the source.

Created: 2026-10-14 ET (Probata proof of concept ticket 23: crux-llvm on the C++ and check mode). Design:
formal-verification map spec ("Verifier lineup and order": fallbacks; floats as reals). Format:
docs/reference/format-v0.4-stubs-check-mode.md.

The C lowering (swdb.c_lowering) refuses floating-point types, so a real-valued unit has no C lowering. crux-llvm
on the C++ and check mode still need the unit's interface and its code: clang 22.1.8's syntax tree gives both.
`CxxCode` offers the part of `swdb.cbmc_adapter.Code` that the C++ forms use (`functions`, `prototypes`,
`interface`, `cxx_text`, `cxx_defines`), so the CBMC translator's harness, stubs and runtime form work on it.
Accepted: free functions (no template, member or namespace) whose parameters are scalars (integer or floating) or
pointers to them; callees defined in the same file are cut too. Anything else raises `swdb.c_lowering.Unsupported`
(failure class unsupported_construct).
"""

import re
from pathlib import Path

from swdb import c_lowering, cbmc_translator as tr

SCALARS = c_lowering.INTEGER_TYPES | {"float", "double", "long double"}


class CxxCode:
    """The unit, its same-file callees and the globals they use, as C++ text cut from the source."""

    def __init__(self, source, function, defines=()):
        self.source, self.defines = Path(source), tuple(sorted(defines))
        self.tool = c_lowering.locate()
        if self.tool.missing:
            raise c_lowering.LoweringError(self.tool.missing)
        self.data = self.source.read_bytes()
        self.nodes, self.functions, self.prototypes, self.globals = {}, [], {}, []
        self._visit(function, unit=True)

    def _visit(self, name, unit=False):
        node = c_lowering._function(self.tool, self.source, name, (), self.defines, unit=unit)
        self.nodes[name] = node
        self.functions.append(name)
        body = next(c for c in node.get("inner", []) if c.get("kind") == "CompoundStmt")
        begin = node["range"]["begin"]
        if "includedFrom" in begin or "offset" not in begin:
            raise c_lowering.Unsupported(f"function {name} is not defined in {self.source.name} itself")
        self.prototypes[name] = self.data[begin["offset"]:body["range"]["begin"]["offset"]].decode().strip()
        locals_ = set()
        refs = []
        _walk(body, locals_, refs)
        for kind, ref in refs:
            if kind == "FunctionDecl" and ref not in self.functions:
                self._visit(ref)
            elif kind == "VarDecl" and ref not in locals_ and ref not in [g[0] for g in self.globals]:
                self._global(ref)

    def _global(self, name):
        found = [n for n in c_lowering._named(c_lowering._dump(self.tool, self.source, name, (), self.defines), name,
                                              {"VarDecl"})]
        if len(found) != 1:
            raise c_lowering.Unsupported(f"global {name} (found {len(found)} declarations)")
        qual = _scalar(c_lowering._qual(found[0]), allow_array=True)
        text = self._text(found[0])
        self.globals.append((name, None if "[" in qual else qual, text))

    def _text(self, node):
        begin, end = node["range"]["begin"], node["range"]["end"]
        if "includedFrom" in begin or "offset" not in begin or "offset" not in end:
            raise c_lowering.Unsupported(f"{node.get('name')} is not defined in {self.source.name} itself")
        return self.data[begin["offset"]:end["offset"] + end.get("tokLen", 0)].decode()

    def interface(self, function):
        node = self.nodes[function]
        params = []
        for param in [c for c in node.get("inner", []) if c.get("kind") == "ParmVarDecl"]:
            qual = _scalar(c_lowering._qual(param))
            if not param.get("name"):
                raise c_lowering.Unsupported(f"unnamed parameter of {function}")
            params.append((param["name"], qual, "*" in qual))
        returns = _scalar(c_lowering._return_type(c_lowering._qual(node), None), allow_void=True)
        return tr.Interface(function=function, returns=returns, parameters=tuple(params),
                            globals=tuple((name, ctype) for name, ctype, _text in self.globals))

    def cxx_defines(self):
        return [f"-D{define}" for define in self.defines]

    def cxx_text(self, stubs=None):
        """The cut C++, each summarized callee's definition replaced by its stub."""
        stubs = stubs or {}
        parts = [f"/* C++ of {self.functions[0]} cut from {self.source.name} by swdb.cxx_cut (no C lowering). */",
                 "#include <cstddef>", "#include <cstdint>"]
        parts += [text + ";" for _name, _ctype, text in self.globals]
        parts += [f"{self.prototypes[name]};" for name in self.functions]
        for name in self.functions:
            parts.append(stubs[name].rstrip("\n") if name in stubs else self._text(self.nodes[name]))
        return "\n".join(parts) + "\n"


def _walk(node, locals_, refs):
    if isinstance(node, dict):
        if node.get("kind") == "VarDecl" and node.get("name"):
            locals_.add(node["name"])
        if node.get("kind") == "DeclRefExpr":
            ref = node.get("referencedDecl") or {}
            if ref.get("kind") in ("FunctionDecl", "VarDecl") and ref.get("name"):
                refs.append((ref["kind"], ref["name"]))
        for value in node.values():
            _walk(value, locals_, refs)
    elif isinstance(node, list):
        for value in node:
            _walk(value, locals_, refs)


def _scalar(qual, allow_void=False, allow_array=False):
    """A scalar (integer or floating) type, or a pointer to one; else Unsupported."""
    text = re.sub(r"\bstd::", "", qual).strip()
    if "&" in text or re.search(r"[<>:(){}]", text):
        raise c_lowering.Unsupported(f"type {qual}")
    if allow_array:
        text = re.sub(r"\s*\[\d+\]$", "", text) if re.search(r"\[\d+\]$", text) else text
    base = " ".join(w for w in text.replace("*", " ").split() if w not in ("const", "volatile"))
    if allow_void and base == "void" and "*" not in text:
        return "void"
    if base not in SCALARS or text.count("*") > 1:
        raise c_lowering.Unsupported(f"type {qual}")
    return qual if not allow_array else qual
